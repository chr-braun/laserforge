#!/usr/bin/env python3
"""
build_macos.py – baut Steckwerk.app und das Installationspaket für den Mac.

  python3 packaging/build_macos.py              → dist/Steckwerk.app + dist/Steckwerk-<version>-macOS.zip
  python3 packaging/build_macos.py --out /tmp   anderer Zielordner

Läuft auf jedem System (auch Linux/Windows), nur Standardbibliothek. Die App enthält den
Steckwerk-Code und ein kleines Startskript; Python 3.8+ kommt vom Mac (Apples Command Line
Tools, python.org oder Homebrew). Im ZIP sind die Ausführrechte gesetzt, damit der Mac die
App nach dem Entpacken direkt starten kann.
"""
from __future__ import annotations

import argparse
import glob
import os
import plistlib
import shutil
import stat
import sys
import time
import zipfile
from typing import List, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAC_DIR = os.path.join(ROOT, "packaging", "macos")
sys.path.insert(0, ROOT)

from steckwerk import __version__  # noqa: E402

APP = "Steckwerk"
BUNDLE_ID = "app.steckwerk.werkbank"
CODE_FILES = ["steckwerk.py", "validator.py", "service.py", "cli.py", "webui.py", "preview.py",
              "steckwerk_app.py", "steckwerk.yaml", "README.md", "PAKETE.md", "pakete.py", "motive.py", "updater.py", "i18n.py", "assistent.py", "bildgen.py",
              "laserforge.py", "README.en.md", "web/index.html",
              "web/icon.png"]


def code_files() -> List[str]:
    files = CODE_FILES + sorted(os.path.relpath(p, ROOT) for p in glob.glob(os.path.join(ROOT, "models", "*.py")))
    files += sorted(os.path.relpath(p, ROOT) for p in glob.glob(os.path.join(ROOT, "motive", "*.json")))
    missing = [f for f in files if not os.path.exists(os.path.join(ROOT, f))]
    if missing:
        raise SystemExit(f"Fehlende Dateien: {missing}")
    return files


def info_plist() -> dict:
    return {
        "CFBundleName": APP,
        "CFBundleDisplayName": APP,
        "CFBundleIdentifier": BUNDLE_ID,
        "CFBundleVersion": __version__,
        "CFBundleShortVersionString": __version__,
        "CFBundleExecutable": APP,
        "CFBundleIconFile": APP,
        "CFBundlePackageType": "APPL",
        "CFBundleInfoDictionaryVersion": "6.0",
        "CFBundleDevelopmentRegion": "de",
        "LSApplicationCategoryType": "public.app-category.graphics-design",
        "LSMinimumSystemVersion": "10.15",
        "LSUIElement": True,               # kein Dock-Symbol: die Oberfläche läuft im Browser
        "NSHighResolutionCapable": True,
        "NSHumanReadableCopyright": "Steckwerk – parametrische, validierte Lasercut-SVGs",
    }


def bundle_entries() -> List[Tuple[str, str, int]]:
    """(Pfad in der App, Quelldatei, Dateimodus) – Grundlage für Ordner und ZIP."""
    c = f"{APP}.app/Contents"
    entries = [(f"{c}/MacOS/{APP}", os.path.join(MAC_DIR, APP), 0o755),
               (f"{c}/Resources/{APP}.icns", os.path.join(MAC_DIR, f"{APP}.icns"), 0o644)]
    for f in code_files():
        entries.append((f"{c}/Resources/steckwerk/{f}", os.path.join(ROOT, f), 0o644))
    return entries


def build_app(out: str) -> str:
    app = os.path.join(out, f"{APP}.app")
    shutil.rmtree(app, ignore_errors=True)
    for rel, src, mode in bundle_entries():
        dst = os.path.join(out, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(src, dst)
        os.chmod(dst, mode)
    with open(os.path.join(app, "Contents", "Info.plist"), "wb") as fh:
        plistlib.dump(info_plist(), fh)
    with open(os.path.join(app, "Contents", "PkgInfo"), "w") as fh:
        fh.write("APPL????")
    return app


def _add(z: zipfile.ZipFile, name: str, data: bytes, mode: int, when) -> None:
    info = zipfile.ZipInfo(name, when)
    info.create_system = 3                                   # Unix: Rechte bleiben erhalten
    info.external_attr = ((stat.S_IFDIR if name.endswith("/") else stat.S_IFREG) | mode) << 16
    if name.endswith("/"):
        info.external_attr |= 0x10                           # MS-DOS-Ordnerflag
        z.writestr(info, b"")
    else:
        info.compress_type = zipfile.ZIP_DEFLATED
        z.writestr(info, data)


def build_zip(out: str) -> str:
    folder = f"{APP}-{__version__}-macOS"
    path = os.path.join(out, folder + ".zip")
    when = time.localtime()[:6]
    files = [(f"{folder}/{rel}", src, mode) for rel, src, mode in bundle_entries()]
    plist = plistlib.dumps(info_plist())
    dirs = set()
    for name, _, _ in files + [(f"{folder}/{APP}.app/Contents/Info.plist", "", 0)]:
        parts = name.split("/")[:-1]
        for i in range(1, len(parts) + 1):
            dirs.add("/".join(parts[:i]) + "/")
    with zipfile.ZipFile(path, "w") as z:
        for d in sorted(dirs):
            _add(z, d, b"", 0o755, when)
        _add(z, f"{folder}/{APP}.app/Contents/Info.plist", plist, 0o644, when)
        _add(z, f"{folder}/{APP}.app/Contents/PkgInfo", b"APPL????", 0o644, when)
        for name, src, mode in files:
            with open(src, "rb") as fh:
                _add(z, name, fh.read(), mode, when)
        with open(os.path.join(MAC_DIR, "LIES MICH.txt"), "rb") as fh:
            _add(z, f"{folder}/LIES MICH.txt", fh.read(), 0o644, when)
    return path


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Steckwerk.app für den Mac bauen")
    ap.add_argument("--out", default=os.path.join(ROOT, "dist"))
    ap.add_argument("--no-app", action="store_true", help="nur das ZIP bauen, keinen App-Ordner")
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    if not a.no_app:
        print("App:", build_app(a.out))
    z = build_zip(a.out)
    print(f"ZIP: {z} ({os.path.getsize(z) / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
