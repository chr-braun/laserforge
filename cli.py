#!/usr/bin/env python3
"""
cli.py – Kommandozeile von Steckwerk.

Ablauf: Config laden → Modelle erzeugen → ALLES validieren → nur wenn alles OK ist,
SVGs (+ Prüfbericht, optional PNG-Vorschau) schreiben. Bei einem FEHLER wird keine
einzige Datei geschrieben (Exit-Code 2).

Beispiele
  python cli.py --model wichtelhaus --out out
  python cli.py --model wichtelhaus --thickness 4 --kerf 0.15 --width 90 --height 75 --pitch 50
  python cli.py --model wichtelhaus --series 5 --seed 42 --out out/serie
  python cli.py --model tannenbaum --height 140 --out out
  python cli.py --model zubehoer --scale 0.8 --out out
  python cli.py --model ornament --shape herz --pattern punkte --text "Anna,Ben,Lea|2026" --out out
  python cli.py --model ornament --shape kugel --pattern filigran --3d --count 4 --out out
  python cli.py --model schneeflocke --count 8 --size 90 --seed 3 --out out
  python cli.py --model fahrzeug --vehicle lok --length 180 --text "Polarexpress" --out out
  python cli.py --model wichtelhaus -O fenster=herz -O wand=fachwerk -O schild="Villa Kunterbunt" --out out
  python cli.py --model fahrzeug --text "Lisa" -O textrahmen=oval -O zierlinie=eiszapfen --out out
  python cli.py --model wichtelhaus --options  (alle Gestaltungsoptionen eines Modells anzeigen)
  python cli.py --motiv-import katze.svg       (eigenes Motiv in die Motiv-Bibliothek, auch PNG)
  python cli.py --model motiv_aufsteller -O motive='[{"id": "stern", "x": 0, "y": 10, "groesse": 60}]' --out out
  python cli.py --model motiv_silhouette -O motiv=katze --height 150 --out out
  python cli.py --konfigurator                 (fragt alles Schritt für Schritt ab)
  python webui.py                              (Weboberfläche im Browser)
  python cli.py --config meine_config.yaml --model alle --preview --out out
"""
from __future__ import annotations

import argparse
import os
import shlex
import sys
import time
from typing import Callable, Dict, List, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from steckwerk import Config, ConfigError, __version__  # noqa: E402
from models import _deko as dk, fahrzeug  # noqa: E402
from models.ornament import PATTERNS  # noqa: E402
from service import (CONFIG_INFO, MODEL_INFO, VEHICLE_DEFAULTS, build_assemblies, coerce,  # noqa: E402
                     process, write_results)
import service  # noqa: E402
from validator import validate_svg_text  # noqa: E402

CHOICES = list(MODEL_INFO)

# Parameter → CLI-Schalter (Zuordnung und Ausgabe des Konfigurators)
FLAGS = {"width": "--width", "height": "--height", "depth": "--depth", "pitch": "--pitch", "n": "--series",
         "seed": "--seed", "shape": "--shape", "size": "--size", "pattern": "--pattern", "text": "--text",
         "hanger": "--hanger", "count": "--count", "vehicle": "--vehicle", "length": "--length",
         "axles": "--axles", "tiers": "--tiers", "door": "--door", "front_windows": "--front-windows",
         "side_windows": "--side-windows"}
BOOL_FLAGS = {("light", False): "--no-light", ("chimney", False): "--no-chimney", ("annex", True): "--annex",
              ("rand", False): "--no-rand", ("three_d", True): "--3d"}
CONFIG_FLAGS = {"thickness": "--thickness", "kerf": "--kerf", "scale": "--scale", "openings": "--openings"}


def parse_args(argv=None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        prog="steckwerk",
        description="Parametrische, validierte Lasercut-SVGs: Wichtelhäuser, Zubehör, Christbaumschmuck, "
                    "Schneeflocken und Steckfahrzeuge.",
        formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__.split("Beispiele", 1)[1])
    ap.add_argument("--model", "-m", choices=CHOICES, default="wichtelhaus", help="Modell (Default: wichtelhaus)")
    ap.add_argument("--konfigurator", action="store_true", help="interaktiv: Modell und Werte abfragen")
    ap.add_argument("--config", "-c", help="YAML/JSON-Config (CLI-Werte überschreiben sie)")
    g = ap.add_argument_group("Material und Laser")
    g.add_argument("--thickness", "-t", type=float, help="Materialstärke T in mm (Default 3)")
    g.add_argument("--kerf", "-k", type=float, help="Schnittbreite in mm (Default 0.2)")
    g.add_argument("--scale", type=float, help="Maßstab der Modelle (T bleibt gleich)")
    g.add_argument("--openings", choices=["cut", "engrave"], help="Fenster/Türen als Durchbruch oder Gravur")
    g.add_argument("--sheet", help="Blattgröße BxH in mm, z. B. 400x300")
    g.add_argument("--cut-color", help="Farbe Schnitt-Layer (#RRGGBB, Default #000000)")
    g.add_argument("--engrave-color", help="Farbe Gravur-Layer (#RRGGBB, Default #0000FF)")
    g = ap.add_argument_group("Maße")
    g.add_argument("--width", type=float, help="Breite in mm (Haus: Giebelseite; Zaun: Länge; Fahrzeug: Breite)")
    g.add_argument("--height", type=float, help="Höhe in mm (Haus: Traufhöhe; Figuren: Gesamthöhe)")
    g.add_argument("--depth", type=float, help="Tiefe in mm (Haus, Briefkasten)")
    g.add_argument("--length", type=float, help="Länge in mm (Fahrzeug)")
    g.add_argument("--size", type=float, help="Größe in mm (Ornament: Höhe, Schneeflocke: Durchmesser)")
    g.add_argument("--pitch", type=float, help="Dachneigung in Grad (Haus)")
    g = ap.add_argument_group("Wichtelhaus, Serie, Zubehör")
    g.add_argument("--door", choices=dk.values(dk.DOORS), help="Türform")
    g.add_argument("--front-windows", type=int, help="Fenster vorne (0–4)")
    g.add_argument("--side-windows", type=int, help="Fenster je Seite (0–3)")
    g.add_argument("--no-light", action="store_true", help="ohne Licht-Durchbruch hinten")
    g.add_argument("--no-chimney", action="store_true", help="ohne Kamin")
    g.add_argument("--annex", action="store_true", help="mit Anbau")
    g.add_argument("--series", "-n", type=int, help="Anzahl Varianten (mit --model wichtelhaus oder serie)")
    g.add_argument("--seed", type=int, help="Zufallsstartwert (Serie, Schneeflocken) – reproduzierbar")
    g.add_argument("--tiers", type=int, help="Etagen des Tannenbaums (2–8)")
    g = ap.add_argument_group("Christbaumschmuck und Schneeflocken")
    g.add_argument("--shape", help="Form: stern, kugel, herz, glocke, baum, mond, anhaenger, lebkuchen, stiefel, zuckerstange, "
                   "geschenk, kerze, engel, zapfen, schneemann, schneeflocke")
    g.add_argument("--pattern", help="Muster: " + ", ".join(PATTERNS))
    g.add_argument("--text", help="Text/Namen; Komma = je Name ein Teil, | = neue Zeile")
    g.add_argument("--hanger", choices=["oese", "loch"], help="Aufhängung")
    g.add_argument("--no-rand", action="store_true", help="ohne gravierte Randlinie")
    g.add_argument("--3d", dest="three_d", action="store_true", help="3D: zwei Hälften zum Zusammenstecken")
    g.add_argument("--count", type=int, help="Anzahl (Ornamente ohne Text, Schneeflocken)")
    g = ap.add_argument_group("Fahrzeuge")
    g.add_argument("--vehicle", choices=fahrzeug.VEHICLES, help="Fahrzeugtyp")
    g.add_argument("--axles", type=int, choices=[2, 3], help="Achsen (Lkw)")
    g = ap.add_argument_group("Gestaltung und Beschriftung")
    g.add_argument("--option", "-O", action="append", default=[], metavar="NAME=WERT",
                   help="Gestaltungsoption setzen, mehrfach möglich (z. B. -O fenster=herz -O schild=Willi)")
    g.add_argument("--options", action="store_true", help="Gestaltungsoptionen des Modells auflisten")
    g = ap.add_argument_group("Eigene Motive (Vorlagen unter „Eigene Motive“)")
    g.add_argument("--motive", action="store_true", help="Motiv-Bibliothek auflisten")
    g.add_argument("--motiv-import", metavar="DATEI", help="SVG oder PNG als Motiv in die Bibliothek übernehmen")
    g.add_argument("--motiv-name", metavar="NAME", default="", help="Name des importierten Motivs")
    g.add_argument("--motiv-umkehren", action="store_true", help="PNG: helles Motiv auf dunklem Grund")
    g.add_argument("--motiv-entfernen", metavar="ID", help="eigenes Motiv aus der Bibliothek löschen")
    g = ap.add_argument_group("Erweiterungspakete (siehe PAKETE.md)")
    g.add_argument("--pakete", action="store_true", help="installierte Pakete auflisten")
    g.add_argument("--paket-installieren", metavar="DATEI", help="Paket (.swpaket oder Ordner) prüfen und installieren")
    g.add_argument("--paket-entfernen", metavar="ID", help="installiertes Paket entfernen")
    g.add_argument("--paket-neu", metavar="ID", help="neues Paket aus der Vorlage anlegen (im --out-Ordner)")
    g.add_argument("--paket-pruefen", metavar="ORDNER", help="Paketordner prüfen (jedes Modell bauen und validieren)")
    g.add_argument("--paket-packen", metavar="ORDNER", help="Paketordner prüfen und als .swpaket verpacken")
    g = ap.add_argument_group("Updates (Programm und Pakete aus dem Update-Kanal)")
    g.add_argument("--update-pruefen", action="store_true", help="nachsehen, ob es Neues gibt")
    g.add_argument("--update-paket", metavar="ID", help="Paket aus dem Kanal installieren/aktualisieren („alle“ = alle Updates)")
    g.add_argument("--update-schluessel", metavar="TOKEN", help="GitHub-Lese-Schlüssel für ein privates Repo speichern („-“ = löschen)")
    g.add_argument("--update-kanal", metavar="URL", help="andere Kanal-Adresse (feed.json) verwenden („-“ = Standard)")
    g = ap.add_argument_group("Ausgabe")
    g.add_argument("--out", "-o", default="out", help="Ausgabeverzeichnis (Default ./out)")
    g.add_argument("--validate", action="store_true", help="nur prüfen, nichts schreiben")
    g.add_argument("--preview", action="store_true", help="zusätzlich PNG-Vorschau je Blatt")
    g.add_argument("--quiet", "-q", action="store_true", help="nur Zusammenfassung ausgeben")
    g.add_argument("--check-svg", nargs="+", metavar="DATEI", help="vorhandene SVG-Dateien prüfen (nichts erzeugen)")
    ap.add_argument("--version", action="version", version=f"Steckwerk {__version__}")
    return ap.parse_args(argv)


def make_config(a: argparse.Namespace) -> Config:
    cfg = Config.load(a.config) if a.config else Config()
    over = dict(thickness=a.thickness, kerf=a.kerf, scale=a.scale, openings=a.openings,
                seed=a.seed, cut_color=a.cut_color, engrave_color=a.engrave_color)
    if a.sheet:
        try:
            w, h = (float(v) for v in a.sheet.lower().split("x"))
        except ValueError:
            raise ConfigError("--sheet erwartet BxH, z. B. 400x300")
        over.update(sheet_width=w, sheet_height=h)
    return cfg.updated(**over)


def params_from_args(a: argparse.Namespace) -> Dict:
    p = {k: getattr(a, k, None) for k in FLAGS if k != "n"}
    p.update(n=a.series, light=False if a.no_light else None, chimney=False if a.no_chimney else None,
             annex=True if a.annex else None, rand=False if a.no_rand else None,
             three_d=True if a.three_d else None)
    p = {k: v for k, v in p.items() if v is not None}
    known = {i["key"] for i in MODEL_INFO.get(model_from_args(a), {}).get("params", [])}
    for item in getattr(a, "option", None) or []:
        key, sep, value = item.partition("=")
        key = key.strip()
        if not sep or not key:
            raise ValueError(f"--option erwartet NAME=WERT, nicht {item!r}")
        if key not in known:
            raise ValueError(f"Option {key!r} gibt es bei {model_from_args(a)} nicht – "
                             f"siehe: python cli.py --model {a.model} --options")
        p[key] = value
    return p


def options_text(model: str) -> str:
    """Übersicht aller Parameter eines Modells (für --options)."""
    info = MODEL_INFO[model]
    lines = [f"{info['label']} – Optionen (als --option NAME=WERT bzw. -O NAME=WERT):"]
    section = None
    for p in info["params"]:
        sec = p.get("section", "Grundlagen")
        if sec != section:
            section = sec
            lines.append(f"\n  {sec}")
        if p["type"] == "motiv":
            lines.append(f"    {p['key']:<14} {p['label']} – Motiv-ID (Standard {p['default']}), Liste: --motive")
        elif p["type"] == "motive":
            lines.append(f"    {p['key']:<14} {p['label']} – JSON-Liste: [{{\"id\": \"stern\", \"x\": 0, \"y\": 0, "
                         f"\"groesse\": 50, \"drehung\": 0, \"art\": \"schnitt|umriss|flaeche\"}}]")
        elif p["type"] == "select":
            vals = ", ".join(o["value"] for o in p["options"])
            lines.append(f"    {p['key']:<14} {p['label']} (Standard {p['default']}): {vals}")
        elif p["type"] == "text":
            lines.append(f"    {p['key']:<14} {p['label']} – Text{', ' + p['help'] if p.get('help') else ''}")
        elif p["type"] == "bool":
            lines.append(f"    {p['key']:<14} {p['label']} – ja/nein (Standard {'ja' if p['default'] else 'nein'})")
        else:
            unit = f" {p['unit']}" if p.get("unit") else ""
            lines.append(f"    {p['key']:<14} {p['label']} – {p['min']:g}–{p['max']:g}{unit} (Standard {p['default']:g})")
        if p.get("when"):
            lines[-1] += "  [nur bei " + ", ".join(f"{k}={'/'.join(str(x) for x in v)}" for k, v in p["when"].items()) + "]"
    return "\n".join(lines)


def model_from_args(a: argparse.Namespace) -> str:
    return "serie" if a.model == "wichtelhaus" and a.series else a.model


# ---------------------------------------------------------------------------
# Konfigurator (interaktiv, aus derselben Parameterbeschreibung wie die Weboberfläche)
# ---------------------------------------------------------------------------

def _ask(info: Dict, inp: Callable[[str], str], out: Callable[[str], None], default=None):
    default = info["default"] if default is None else default
    t = info["type"]
    if t == "select":
        out(f"  {info['label']}:")
        for i, o in enumerate(info["options"], 1):
            out(f"    {i}) {o['label']}{'  ← Standard' if o['value'] == default else ''}")
    while True:
        if t == "bool":
            hint = "J/n" if default else "j/N"
        elif t == "select":
            hint = "Nummer"
        elif t in ("number", "int"):
            hint = f"{info['min']:g}–{info['max']:g} {info.get('unit', '')}".rstrip()
        else:
            hint = info.get("help", "") or "Text"
        shown = f" [{default}]" if t not in ("bool", "select") and default not in ("", None) else ""
        raw = inp(f"  {info['label']}{shown} ({hint}): ").strip()
        if raw == "":
            return default
        try:
            if t == "select":
                if not raw.isdigit() or not 1 <= int(raw) <= len(info["options"]):
                    raise ValueError(f"bitte 1–{len(info['options'])}")
                return info["options"][int(raw) - 1]["value"]
            if t == "bool":
                return raw.lower() in ("j", "ja", "y", "yes", "1")
            return coerce(info, raw.replace(",", ".") if t in ("number", "int") else raw)
        except ValueError as e:
            out(f"    → {e}")


def _default(model: str, key: str):
    for i in MODEL_INFO[model]["params"]:
        if i["key"] == key:
            return i["default"]
    return None


def konfigurator(inp: Callable[[str], str] = input, out: Callable[[str], None] = print) -> List[str]:
    """Fragt Modell, Maße und Material ab und liefert die passenden CLI-Argumente."""
    out(f"\nSteckwerk {__version__} – Konfigurator (Enter = Standardwert)\n")
    keys = [k for k in MODEL_INFO if k != "alle"]
    group = None
    for i, k in enumerate(keys, 1):
        if MODEL_INFO[k]["group"] != group:
            group = MODEL_INFO[k]["group"]
            out(f" {group}")
        out(f"   {i:2d}) {MODEL_INFO[k]['label']:<20} {MODEL_INFO[k]['desc']}")
    while True:
        raw = inp("\nWas möchtest du lasern? Nummer: ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(keys):
            model = keys[int(raw) - 1]
            break
        out("  → bitte eine Nummer aus der Liste")
    args = ["--model", model]
    out(f"\n{MODEL_INFO[model]['label']}")
    vehicle = None
    chosen: Dict[str, object] = {}
    design = None                                   # None = noch nicht gefragt
    section = None
    for info in MODEL_INFO[model]["params"]:
        key = info["key"]
        when = info.get("when") or {}
        if any(chosen.get(k, _default(model, k)) not in allowed for k, allowed in when.items()):
            continue
        if info.get("section"):
            if design is None:
                raw = inp("\n  Gestaltung und Beschriftung anpassen? (j/N): ").strip().lower()
                design = raw in ("j", "ja", "y", "yes")
            if not design:
                continue
            if info["section"] != section:
                section = info["section"]
                out(f"\n  – {section} –")
        if info["type"] == "motive":
            out("  Motive: Standard-Platzierung – frei platzieren in der Weboberfläche oder mit -O motive=[…]")
            continue
        if info["type"] == "motiv":
            import motive as _mt
            info = dict(info, type="select", options=[dict(value=m["id"], label=m.get("name", m["id"]))
                                                      for m in _mt.library() if m["flaechen"]])
        dflt = VEHICLE_DEFAULTS[vehicle][key] if (model == "fahrzeug" and vehicle and
                                                   key in ("length", "width")) else None
        v = _ask(info, inp, out, dflt)
        chosen[key] = v
        if key == "vehicle":
            vehicle = v
        if info["type"] == "bool":
            if (key, v) in BOOL_FLAGS:
                args.append(BOOL_FLAGS[(key, v)])
            elif v != info["default"]:
                args += ["--option", f"{key}={'ja' if v else 'nein'}"]
        elif v not in (None, "") and (v != info["default"] or key in ("vehicle", "shape") or dflt is not None):
            if key in FLAGS:
                args += [FLAGS[key], str(v)]
            else:
                args += ["--option", f"{key}={v}"]
    out("\nMaterial und Laser")
    for info in CONFIG_INFO[:4]:
        v = _ask(info, inp, out)
        if v != info["default"]:
            args += [CONFIG_FLAGS[info["key"]], str(v)]
    args += ["--out", inp("  Ausgabeordner [out]: ").strip() or "out"]
    if inp("  PNG-Vorschau mitschreiben? (J/n): ").strip().lower() not in ("n", "nein", "no"):
        args.append("--preview")
    out("\nDasselbe beim nächsten Mal direkt:\n  python cli.py " + " ".join(shlex.quote(x) for x in args) + "\n")
    return args


# ---------------------------------------------------------------------------
# Hauptablauf
# ---------------------------------------------------------------------------

def motiv_command(a) -> Optional[int]:
    """--motive / --motiv-*: Motiv-Bibliothek verwalten. None = kein Motivbefehl."""
    import motive
    try:
        if a.motive:
            for m in motive.library():
                art = "eingebaut" if m.get("eingebaut") else m.get("quelle", "")
                print(f"  {m['id']:<24} {m.get('name', ''):<24} {art}")
            print(f"Eigene Motive liegen in: {motive.user_dir()}")
            return 0
        if a.motiv_import:
            m = motive.import_file(a.motiv_import, a.motiv_name, a.motiv_umkehren)
            fl = len(m["flaechen"])
            print(f"Motiv „{m['name']}“ importiert als {m['id']} – {fl} Fläche(n), {len(m['linien'])} Linie(n)")
            print(f"Verwenden: python3 cli.py --model motiv_silhouette -O motiv={m['id']} --out out")
            return 0
        if a.motiv_entfernen:
            motive.remove(a.motiv_entfernen)
            print(f"Entfernt: {a.motiv_entfernen}")
            return 0
    except (motive.MotivFehler, OSError) as e:
        print(f"FEHLER: {e}", file=sys.stderr)
        return 2
    return None


def update_command(a) -> Optional[int]:
    """--update-*: Update-Kanal abfragen, Pakete laden. None = kein Updatebefehl."""
    import pakete
    import updater
    if not (a.update_pruefen or a.update_paket or a.update_schluessel or a.update_kanal):
        return None
    try:
        if a.update_schluessel or a.update_kanal:
            s = updater.save_settings(None if a.update_kanal is None else ("" if a.update_kanal == "-" else a.update_kanal),
                                      None if a.update_schluessel is None else
                                      ("" if a.update_schluessel == "-" else a.update_schluessel))
            print(f"Kanal: {s['kanal']} · Schlüssel {'gespeichert' if s['token_gesetzt'] else 'keiner'}")
        if a.update_paket:
            if a.update_paket == "alle":
                done = updater.install_alle_pakete()
                print("\n".join(f"Aktualisiert: {m['name']} {m['version']}" for m in done) or "Alle Pakete sind aktuell.")
            else:
                m = updater.install_paket(a.update_paket)
                print(f"Installiert: {m['name']} {m['version']}")
        if a.update_pruefen:
            d = updater.check()
            p = d["programm"]
            print(f"Steckwerk {p['installiert']} – " + (f"neu: {p['version']} vom {p['datum']}" if p["neu"] else "aktuell"))
            for h in p["hinweise"] if p["neu"] else []:
                print(f"  · {h}")
            if p["neu"]:
                print("  Die Mac-App aktualisiert sich unter „Updates“ selbst; sonst neue Version von Hand holen.")
            names = {"update": "Update", "neu": "neu", "zu_neu": "braucht neuere Steckwerk", "aktuell": "aktuell"}
            for x in d["pakete"]:
                inst = f" (installiert {x['installiert']})" if x["status"] == "update" else ""
                print(f"  {x['id']:<20} {x['version']:<8} {names[x['status']]}{inst}")
            if any(x["status"] in ("update", "neu") for x in d["pakete"]):
                print("Installieren: python3 cli.py --update-paket ID   (oder „alle“ für alle Updates)")
        return 0
    except (updater.UpdateFehler, pakete.PaketFehler) as e:
        print(f"FEHLER: {e}", file=sys.stderr)
        return 2


def paket_command(a) -> Optional[int]:
    """--pakete / --paket-*: Pakete verwalten. None = kein Paketbefehl."""
    import pakete
    try:
        if a.pakete:
            print(pakete.status_text(service.PAKETE))
            print(f"Installationsordner: {pakete.install_dir()}")
            return 0
        if a.paket_installieren:
            print("Hinweis: Pakete enthalten Python-Code – nur aus vertrauenswürdiger Quelle installieren.")
            m, lines = pakete.install(a.paket_installieren)
            print(f"Paket „{m['name']}“ {m['version']} geprüft:")
            print("\n".join(lines))
            return 0
        if a.paket_entfernen:
            print(f"Entfernt: {pakete.remove(a.paket_entfernen)}")
            return 0
        if a.paket_neu:
            folder = pakete.create(a.paket_neu, a.out)
            print(f"Neues Paket angelegt: {folder}\nBearbeiten, dann: python3 cli.py --paket-packen {folder}")
            return 0
        if a.paket_pruefen:
            m, lines = pakete.check_folder(a.paket_pruefen)
            print(f"Paket „{m['name']}“ {m['version']}: alles in Ordnung")
            print("\n".join(lines))
            return 0
        if a.paket_packen:
            path, lines = pakete.pack(a.paket_packen, a.out)
            print("\n".join(lines))
            print(f"Gepackt: {path}")
            return 0
    except (pakete.PaketFehler, OSError) as e:
        print(f"FEHLER: {e}", file=sys.stderr)
        return 2
    return None


def run(argv=None, inp: Callable[[str], str] = input) -> int:
    a = parse_args(argv)
    if a.konfigurator:
        try:
            a = parse_args(konfigurator(inp))
        except (EOFError, KeyboardInterrupt):
            print("\nAbgebrochen.")
            return 1
    t0 = time.time()
    if a.options:
        print(options_text(model_from_args(a)))
        return 0
    paket = paket_command(a)
    if paket is not None:
        return paket
    upd = update_command(a)
    if upd is not None:
        return upd
    mot = motiv_command(a)
    if mot is not None:
        return mot
    if a.check_svg:
        cfg = make_config(a)
        ok = True
        for f in a.check_svg:
            with open(f, encoding="utf-8") as fh:
                rep = validate_svg_text(fh.read(), cfg, os.path.basename(f))
            print(rep.text())
            ok &= rep.passed
        return 0 if ok else 2
    try:
        cfg = make_config(a)
        assemblies = build_assemblies(model_from_args(a), params_from_args(a), cfg)
    except (ConfigError, ValueError) as e:
        print(f"FEHLER  [Parameter] {e}", file=sys.stderr)
        return 2

    # 1) alles validieren – Geometrie, Verbindungen, Layout und das fertige SVG selbst
    results, all_ok = process(assemblies, cfg)
    for res in results:
        print(res.report.summary() if a.quiet else res.report.text())
    if not all_ok:
        print("\nValidierung fehlgeschlagen – es wurde KEINE Datei geschrieben.", file=sys.stderr)
        return 2
    if a.validate:
        print(f"\nAlle {len(results)} Modelle cut-ready (nur Prüfung, nichts geschrieben).")
        return 0

    # 2) schreiben
    written, preview_ok = write_results(results, cfg, a.out, a.preview)
    print(f"\n{len(written)} Dateien geschrieben in {os.path.abspath(a.out)} ({time.time() - t0:.1f} s):")
    for w in written:
        print("  " + w)
    if a.preview and preview_ok is False:
        print("Hinweis: keine Vorschau – weder matplotlib noch Pillow installiert.")
    return 0


if __name__ == "__main__":
    from steckwerk import migrate_legacy
    migrate_legacy()
    sys.exit(run())
