#!/usr/bin/env python3
"""
update_kanal.py – Update-Kanal für Steckwerk bauen bzw. auffrischen.

  python3 packaging/update_kanal.py KANAL [--mac Steckwerk-1.7.0-macOS.zip] [--paket datei.swpaket ...]

KANAL ist ein Ordner (z. B. ein Checkout des Branches „updates“). Neue Dateien werden hineinkopiert,
danach wird feed.json aus dem Inhalt neu geschrieben: die neueste Mac-App und je Paket die neueste
Version. Ältere Dateien werden entfernt, damit der Kanal klein bleibt. Die Hinweise zur Programmversion
kommen aus dem passenden Abschnitt der CHANGELOG.md.

Danach den Ordner veröffentlichen (Branch „updates“ pushen); Steckwerk findet die Neuerungen
unter „Updates“.
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import plistlib
import re
import shutil
import sys
import time
import zipfile
from typing import Any, Dict, List, Optional

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from updater import STANDARD, ver  # noqa: E402

MAC_RE = re.compile(r"^Steckwerk-(\d+\.\d+\.\d+)-macOS\.zip$")


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def changelog_notes(version: str, path: str = os.path.join(ROOT, "CHANGELOG.md")) -> List[str]:
    """Stichpunkte des Abschnitts „## <version> …“ als Liste (Folgezeilen zusammengefügt)."""
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return []
    m = re.search(rf"^## {re.escape(version)}\b.*?$(.*?)(?=^## |\Z)", text, re.M | re.S)
    if not m:
        return []
    notes: List[str] = []
    for line in m.group(1).splitlines():
        if line.startswith("- "):
            notes.append(line[2:].strip())
        elif line.startswith("  ") and notes:
            notes[-1] += " " + line.strip()
    skip = ("Kommandozeile", "Für Herausgeber", "Tests", "Command line", "For publishers")          # nur für Entwickler interessant
    return [n.replace("`", "").replace("**", "") for n in notes if not n.startswith(skip)]


def mac_version(path: str) -> str:
    with zipfile.ZipFile(path) as z:
        name = next((n for n in z.namelist() if n.endswith("Steckwerk.app/Contents/Info.plist")), None)
        if not name:
            raise SystemExit(f"{path}: keine Steckwerk.app darin")
        return str(plistlib.loads(z.read(name)).get("CFBundleShortVersionString"))


def paket_manifest(path: str) -> Dict[str, Any]:
    with zipfile.ZipFile(path) as z:
        name = next((n for n in z.namelist() if n.rstrip("/").split("/")[-1] == "paket.json" and n.count("/") <= 1), None)
        if not name:
            raise SystemExit(f"{path}: kein Steckwerk-Paket (paket.json fehlt)")
        return json.loads(z.read(name).decode("utf-8"))


def build(kanal: str, mac: Optional[str] = None, pakete: List[str] = (), notes: Optional[List[str]] = None,
          seite: str = "", today: Optional[str] = None) -> Dict[str, Any]:
    os.makedirs(os.path.join(kanal, "pakete"), exist_ok=True)
    if mac:
        v = mac_version(mac)
        shutil.copyfile(mac, os.path.join(kanal, f"Steckwerk-{v}-macOS.zip"))
    for p in pakete:
        m = paket_manifest(p)
        shutil.copyfile(p, os.path.join(kanal, "pakete", f"{m['id']}-{m['version']}.swpaket"))

    old = {}
    try:
        with open(os.path.join(kanal, "feed.json"), encoding="utf-8") as fh:
            old = json.load(fh)
    except (OSError, ValueError):
        pass

    macs = sorted((f for f in os.listdir(kanal) if MAC_RE.match(f)), key=lambda f: ver(MAC_RE.match(f).group(1)))
    for f in macs[:-1]:
        os.remove(os.path.join(kanal, f))
    programm: Dict[str, Any] = dict(old.get("programm") or {})
    if macs:
        f = macs[-1]
        v = MAC_RE.match(f).group(1)
        if programm.get("version") != v:
            programm = {"version": v, "datum": today or time.strftime("%Y-%m-%d")}
        programm["hinweise"] = notes if notes is not None else (changelog_notes(v) or programm.get("hinweise", []))
        en = changelog_notes(v, os.path.join(ROOT, "CHANGELOG.en.md"))
        if en:
            programm["hinweise_en"] = en
        programm["mac"] = {"datei": f, "sha256": sha256(os.path.join(kanal, f)),
                           "groesse": os.path.getsize(os.path.join(kanal, f))}
        if seite:
            programm["seite"] = seite

    newest: Dict[str, tuple] = {}
    for path in glob.glob(os.path.join(kanal, "pakete", "*.swpaket")):
        m = paket_manifest(path)
        if m["id"] not in newest or ver(m["version"]) > ver(newest[m["id"]][0]["version"]):
            if m["id"] in newest:
                os.remove(newest[m["id"]][1])
            newest[m["id"]] = (m, path)
        else:
            os.remove(path)
    eintraege = []
    for pid, (m, path) in sorted(newest.items()):
        eintraege.append({"id": pid, "name": m.get("name", pid), "version": m["version"],
                          "beschreibung": m.get("beschreibung", ""), "autor": m.get("autor", ""),
                          **{k: m[k] for k in ("name_en", "beschreibung_en", "benoetigt") if m.get(k)},
                          "steckwerk": m.get("steckwerk") or m.get("laserforge") or "1.5.0",
                          "datei": "pakete/" + os.path.basename(path), "sha256": sha256(path),
                          "groesse": os.path.getsize(path)})
    feed = {"standard": STANDARD, "erstellt": today or time.strftime("%Y-%m-%d"), "programm": programm,
            "pakete": eintraege}
    with open(os.path.join(kanal, "feed.json"), "w", encoding="utf-8") as fh:
        json.dump(feed, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    return feed


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Steckwerk-Update-Kanal bauen")
    ap.add_argument("kanal", help="Ordner des Update-Kanals")
    ap.add_argument("--mac", help="Mac-App als ZIP (aus packaging/build_macos.py)")
    ap.add_argument("--paket", action="append", default=[], help=".swpaket-Datei (mehrfach möglich)")
    ap.add_argument("--seite", default="", help="Webseite mit Download für Nicht-Mac-Nutzer")
    a = ap.parse_args(argv)
    feed = build(a.kanal, a.mac, a.paket, seite=a.seite)
    prog = feed["programm"]
    print(f"Kanal {a.kanal}: Programm {prog.get('version', '–')}, "
          f"{len(feed['pakete'])} Paket(e): " + ", ".join(f"{p['id']} {p['version']}" for p in feed["pakete"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
