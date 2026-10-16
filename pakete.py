"""
pakete.py – Erweiterungspakete für Steckwerk (Standard „Steckwerk-Paket 1“).

Ein Paket ist ein Ordner (oder dieselben Dateien als ZIP mit der Endung .swpaket):

    mein_paket/
      paket.json        Steckbrief (Pflicht)
      <modell>.py       je Modell eine Datei mit INFO und build()
      LIES MICH.md      optional: Anleitung
      vorschau.png      optional: Bild für die Übersicht

paket.json:
    {
      "standard": 1,
      "id": "tuerschild",                 Kleinbuchstaben, Ziffern, _ (eindeutig)
      "name": "Türschild",
      "version": "1.0.0",
      "autor": "Christian",
      "beschreibung": "Hängeschild mit Namen",
      "steckwerk": "1.5.0",              mindestens nötige Steckwerk-Version
      "modelle": ["tuerschild"],          Dateinamen ohne .py
      "benoetigt": {"verzierungen": "1.0.0"},   optional (ab 2.4.0): andere Pakete ab Version
      "bibliothek": "bibliothek"          optional (ab 2.4.0): Modul, das andere Pakete nutzen dürfen
      "ersetzt": ["altes_paket"]          optional (ab 2.5.0): Pakete, die in diesem aufgegangen sind –
                                          sie werden beim Installieren entfernt und sonst ausgeblendet
    }

Gemeinsame Bausteine (ab 2.4.0): Ein Paket mit "bibliothek" stellt allen anderen Paketen Werkzeuge
bereit. Ein Paket, das sie nutzt, trägt es unter "benoetigt" ein und lädt es mit

    from pakete import bibliothek
    Z = bibliothek("verzierungen")

<modell>.py:
    from pakete import num, sel, txt, flag, integer     # Formular-Bausteine
    INFO = dict(label="Türschild", desc="…", params=[num("width", "Breite", 120, 60, 300), …])
    def build(cfg, name="tuerschild", width=120, …):    # liefert Assembly (oder Liste davon)
        …

Jedes Modell darf alles aus steckwerk.py und models/ (z. B. _deko, _font, _shapes) benutzen.
Ein Paket wird nur installiert, wenn jedes Modell mit seinen Standardwerten baut und der
Validator keinen Fehler findet. Achtung: Pakete enthalten Python-Code – nur Pakete aus
vertrauenswürdiger Quelle installieren.

Suchorte (in dieser Reihenfolge): $STECKWERK_PAKETE (mehrere mit ':' getrennt), der Ordner
„pakete“ neben diesem Programm und der Benutzerordner (macOS: ~/Library/Application Support/
Steckwerk/Pakete, sonst ~/.steckwerk/pakete). Installiert wird in den Benutzerordner – so
überstehen Pakete jedes Steckwerk-Update.
"""
from __future__ import annotations

import importlib.util
import io
import json
import os
import re
import shutil
import sys
import tempfile
import zipfile
from typing import Any, Dict, List, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
STANDARD = 1
EXT = ".swpaket"
MAX_ZIP = 20 * 1024 * 1024
ID_RE = re.compile(r"^[a-z][a-z0-9_]{1,39}$")


# --- Formular-Bausteine (gleiches Format wie service.MODEL_INFO) ------------------------------------

def num(key, label, default, lo, hi, step=1.0, unit="mm", help="", **extra):
    return dict(key=key, label=label, type="number", default=default, min=lo, max=hi, step=step,
                unit=unit, help=help, **extra)


def integer(key, label, default, lo, hi, help="", unit="", **extra):
    return dict(key=key, label=label, type="int", default=default, min=lo, max=hi, step=1, unit=unit, help=help,
                **extra)


def sel(key, label, options, default, help="", **extra):
    return dict(key=key, label=label, type="select", default=default,
                options=[dict(value=v, label=l) for v, l in options], help=help, **extra)


def txt(key, label, default="", help="", maxlen=80, **extra):
    return dict(key=key, label=label, type="text", default=default, maxlength=maxlen, help=help, **extra)


def flag(key, label, default, help="", **extra):
    return dict(key=key, label=label, type="bool", default=default, help=help, **extra)


def motiv(key, label, default="stern", help="", **extra):
    """Ein Motiv aus der Motiv-Bibliothek; kommt als ID an, laden mit motive.load(id)."""
    return dict(key=key, label=label, type="motiv", default=default, help=help, **extra)


def motive(key, label, default=(), help="", max_items=12, **extra):
    """Frei platzierbare Motive; kommen als Liste von {id, x, y, groesse, drehung, spiegeln, art} an."""
    from models.motivvorlagen import ARTEN
    return dict(key=key, label=label, type="motive", default=list(default), max=max_items, help=help,
                arten=[dict(value=v, label=l) for v, l in ARTEN], **extra)


# --- Orte -----------------------------------------------------------------------------------------

def user_dir() -> str:
    if sys.platform == "darwin":
        return os.path.expanduser("~/Library/Application Support/Steckwerk/Pakete")
    return os.path.expanduser("~/.steckwerk/pakete")


def search_dirs() -> List[str]:
    env = [d for d in os.environ.get("STECKWERK_PAKETE", "").split(os.pathsep) if d]
    out: List[str] = []
    for d in env + [os.path.join(HERE, "pakete"), user_dir()]:
        d = os.path.abspath(os.path.expanduser(d))
        if d not in out:
            out.append(d)
    return out


def install_dir() -> str:
    env = [d for d in os.environ.get("STECKWERK_PAKETE", "").split(os.pathsep) if d]
    return os.path.abspath(os.path.expanduser(env[0] if env else user_dir()))


# --- Prüfen und Laden -------------------------------------------------------------------------------

class PaketFehler(ValueError):
    pass


def _ver(v: str) -> Tuple[int, ...]:
    try:
        return tuple(int(x) for x in str(v).split(".")[:3])
    except ValueError:
        raise PaketFehler(f"Versionsangabe {v!r} ist ungültig (Form 1.2.3)")


def read_manifest(folder: str) -> Dict[str, Any]:
    from steckwerk import __version__
    path = os.path.join(folder, "paket.json")
    if not os.path.isfile(path):
        raise PaketFehler(f"{os.path.basename(folder)}: paket.json fehlt")
    try:
        with open(path, encoding="utf-8") as fh:
            m = json.load(fh)
    except (OSError, ValueError) as e:
        raise PaketFehler(f"paket.json ist kein gültiges JSON: {e}")
    if not isinstance(m, dict):
        raise PaketFehler("paket.json muss ein Objekt sein")
    for k in ("id", "name", "version", "modelle"):
        if k not in m:
            raise PaketFehler(f"paket.json: Angabe {k!r} fehlt")
    if int(m.get("standard", STANDARD)) > STANDARD:
        raise PaketFehler(f"Paket nutzt Standard {m['standard']} – diese Steckwerk kennt nur {STANDARD}")
    if not ID_RE.match(str(m["id"])):
        raise PaketFehler(f"Paket-id {m['id']!r}: nur Kleinbuchstaben, Ziffern und _ (2–40 Zeichen)")
    _ver(m["version"])
    if "steckwerk" not in m and "laserforge" in m:                     # Pakete aus der Laserforge-Zeit
        m["steckwerk"] = m["laserforge"]
    if _ver(m.get("steckwerk", "0.0.0")) > _ver(__version__):
        raise PaketFehler(f"Paket {m['id']} braucht Steckwerk {m['steckwerk']} – du hast {__version__}")
    dep = m.get("benoetigt", {})
    if not isinstance(dep, dict):
        raise PaketFehler("paket.json: 'benoetigt' muss ein Objekt sein, z. B. {\"verzierungen\": \"1.0.0\"}")
    for pid, v in dep.items():
        if not ID_RE.match(str(pid)) or pid == m["id"]:
            raise PaketFehler(f"paket.json: benötigtes Paket {pid!r} ist ungültig")
        _ver(v)
    ers = m.get("ersetzt", [])
    if not isinstance(ers, list) or any(not ID_RE.match(str(r)) or r == m["id"] for r in ers):
        raise PaketFehler("paket.json: 'ersetzt' muss eine Liste anderer Paket-ids sein")
    bib = m.get("bibliothek")
    if bib is not None and (not ID_RE.match(str(bib).lstrip("_")) or
                            not os.path.isfile(os.path.join(folder, f"{bib}.py"))):
        raise PaketFehler(f"paket.json: Bibliothek {bib!r} – Datei {bib}.py fehlt")
    mods = m["modelle"]
    if not isinstance(mods, list) or not mods:
        raise PaketFehler("paket.json: 'modelle' muss eine Liste mit mindestens einem Modell sein")
    for name in mods:
        if not ID_RE.match(str(name)):
            raise PaketFehler(f"Modellname {name!r}: nur Kleinbuchstaben, Ziffern und _")
        if not os.path.isfile(os.path.join(folder, f"{name}.py")):
            raise PaketFehler(f"Modell {name!r}: Datei {name}.py fehlt")
    return m


def _index() -> Dict[str, Tuple[str, Dict[str, Any]]]:
    """Alle Pakete der Suchorte nach id: (ordner, steckbrief). Nur paket.json lesen, nichts importieren."""
    out: Dict[str, Tuple[str, Dict[str, Any]]] = {}
    for base in search_dirs():
        if not os.path.isdir(base):
            continue
        for entry in sorted(os.listdir(base)):
            path = os.path.join(base, entry, "paket.json")
            try:
                with open(path, encoding="utf-8") as fh:
                    m = json.load(fh)
            except (OSError, ValueError):
                continue
            if isinstance(m, dict) and isinstance(m.get("id"), str) and m["id"] not in out:
                out[m["id"]] = (os.path.join(base, entry), m)
    return out


def fehlende(m: Dict[str, Any]) -> List[str]:
    """Benötigte Pakete, die fehlen oder zu alt sind – als lesbare Liste."""
    idx = _index()
    out = []
    for pid, v in sorted((m.get("benoetigt") or {}).items()):
        hit = idx.get(pid)
        if hit is None:
            out.append(f"„{pid}“ ab {v}")
        else:
            try:
                alt = _ver(hit[1].get("version", "0")) < _ver(v)
            except PaketFehler:
                alt = True
            if alt:
                out.append(f"„{hit[1].get('name', pid)}“ ab {v} (installiert: {hit[1].get('version')})")
    return out


def _abhaengig(m: Dict[str, Any]) -> None:
    miss = fehlende(m)
    if miss:
        raise PaketFehler(f"„{m.get('name', m['id'])}“ braucht zuerst das Paket {', '.join(miss)} – "
                          f"über „Updates“ wird es automatisch mitinstalliert")


def bibliothek(pid: str, modul: str = ""):
    """Gemeinsame Bausteine eines anderen Pakets laden (siehe "bibliothek" in paket.json).

        Z = bibliothek("verzierungen")
        fig = Z.rosette(30, blaetter=8)
    """
    hit = _index().get(pid)
    if hit is None:
        raise PaketFehler(f"Das Paket „{pid}“ fehlt – bitte zuerst installieren (Einstellungen → Pakete "
                          f"oder Updates)")
    folder, m = hit
    name = modul or m.get("bibliothek") or "bibliothek"
    path = os.path.join(folder, f"{name}.py")
    if not re.match(r"^_?[a-z][a-z0-9_]{0,39}$", name) or not os.path.isfile(path):
        raise PaketFehler(f"Paket „{pid}“ hat keine Bibliothek {name!r}")
    key = f"swbib_{pid}_{name}"
    mod = sys.modules.get(key)
    if mod is None or getattr(mod, "__file__", None) != path:
        spec = importlib.util.spec_from_file_location(key, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[key] = mod
        try:
            spec.loader.exec_module(mod)
        except Exception as e:
            sys.modules.pop(key, None)
            raise PaketFehler(f"Bibliothek von „{pid}“ lässt sich nicht laden: {type(e).__name__}: {e}")
    return mod


def _import(folder: str, pid: str, model: str):
    path = os.path.join(folder, f"{model}.py")
    modname = f"swpaket_{pid}_{model}"
    spec = importlib.util.spec_from_file_location(modname, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[modname] = mod
    try:
        spec.loader.exec_module(mod)
    except Exception as e:
        sys.modules.pop(modname, None)
        raise PaketFehler(f"Modell {model!r} lässt sich nicht laden: {type(e).__name__}: {e}")
    if not callable(getattr(mod, "build", None)):
        raise PaketFehler(f"Modell {model!r}: Funktion build(cfg, …) fehlt")
    info = getattr(mod, "INFO", None)
    if not isinstance(info, dict) or not isinstance(info.get("params", []), list):
        raise PaketFehler(f"Modell {model!r}: INFO = dict(label=…, params=[…]) fehlt")
    for p in info.get("params", []):
        if not isinstance(p, dict) or "key" not in p or "type" not in p:
            raise PaketFehler(f"Modell {model!r}: Parameter ohne key/type – nimm num(), sel(), txt() …")
    return mod


def load_folder(folder: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Liest ein Paket (Steckbrief + Module). Liefert (manifest, {modell: modul})."""
    m = read_manifest(folder)
    _abhaengig(m)
    return m, {name: _import(folder, m["id"], name) for name in m["modelle"]}


def check_folder(folder: str) -> Tuple[Dict[str, Any], List[str]]:
    """Wie load_folder, baut aber zusätzlich jedes Modell mit Standardwerten und prüft es."""
    from steckwerk import Config, layout
    from validator import validate_assembly, validate_sheets
    m, mods = load_folder(folder)
    lines = []
    for name, mod in mods.items():
        cfg = Config()
        params = {p["key"]: p.get("default") for p in mod.INFO.get("params", []) if p.get("default") is not None}
        try:
            res = mod.build(cfg, **params)
        except Exception as e:
            raise PaketFehler(f"Modell {name!r} baut mit Standardwerten nicht: {type(e).__name__}: {e}")
        asms = res if isinstance(res, list) else [res]
        for a in asms:
            rep = validate_assembly(a, cfg)
            validate_sheets(layout([p.compensated(cfg.kerf_offset) for p in a.parts], cfg), cfg, rep)
            if not rep.passed:
                errs = "; ".join(e.line() for e in rep.errors)[:400]
                raise PaketFehler(f"Modell {name!r}: Validator meldet Fehler – {errs}")
        lines.append(f"  ✓ {name}: {sum(len(a.parts) for a in asms)} Teile, cut-ready")
    return m, lines


def ersetzte() -> Dict[str, str]:
    """Pakete, die in einem anderen vorhandenen Paket aufgegangen sind: {alte id: neue id} (ab 2.5.0)."""
    out: Dict[str, str] = {}
    for pid, (_, m) in _index().items():
        for r in m.get("ersetzt") or []:
            if isinstance(r, str) and r != pid:
                out.setdefault(r, pid)
    return out


def discover() -> List[Tuple[str, Dict[str, Any], Dict[str, Any], Optional[str]]]:
    """Alle Pakete der Suchorte: (ordner, manifest, module, fehler). Doppelte ids: erstes gewinnt.
    Pakete, die ein anderes vorhandenes Paket ersetzt, werden übersprungen."""
    seen = set(ersetzte())
    out = []
    for base in search_dirs():
        if not os.path.isdir(base):
            continue
        for entry in sorted(os.listdir(base)):
            folder = os.path.join(base, entry)
            if not os.path.isfile(os.path.join(folder, "paket.json")):
                continue
            try:
                m, mods = load_folder(folder)
            except PaketFehler as e:
                out.append((folder, {"id": entry}, {}, str(e)))
                continue
            if m["id"] in seen:
                continue
            seen.add(m["id"])
            out.append((folder, m, mods, None))
    return out


def register(model_info: Dict[str, Any], models: Dict[str, Any]) -> List[Tuple[str, Dict[str, Any], Optional[str]]]:
    """Lädt alle Pakete und trägt ihre Modelle ein. Liefert (ordner, manifest, fehler) je Paket."""
    for k in [k for k, v in model_info.items() if v.get("paket")]:     # neu laden: alte Einträge weg
        model_info.pop(k, None)
        models.pop(k, None)
    status = []
    for folder, m, mods, err in discover():
        if err is None:
            for name, mod in mods.items():
                key = name if name not in model_info else f"{m['id']}_{name}"
                if key in model_info:
                    err = f"Modellname {name!r} ist schon vergeben"
                    continue
                info = dict(label=name, group="Pakete", desc="", params=[])
                info.update(mod.INFO)
                info["paket"] = dict(id=m["id"], name=m["name"], version=m["version"], autor=m.get("autor", ""))
                model_info[key] = info
                models[key] = mod
                if isinstance(getattr(mod, "UEBERSETZUNG", None), dict):
                    import i18n
                    for lang, table in mod.UEBERSETZUNG.items():
                        i18n.add(lang, table)
        status.append((folder, m, err))
    return status


# --- Installieren, Entfernen, Erstellen, Packen ----------------------------------------------------

def _unzip(data: bytes, dest: str) -> str:
    if len(data) > MAX_ZIP:
        raise PaketFehler("Paket ist größer als 20 MB")
    try:
        zf = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile:
        raise PaketFehler("Datei ist kein Steckwerk-Paket (kein ZIP)")
    total = 0
    for info in zf.infolist():
        name = info.filename
        if name.startswith("/") or ".." in name.replace("\\", "/").split("/") or ":" in name:
            raise PaketFehler(f"Unzulässiger Pfad im Paket: {name}")
        total += info.file_size
        if total > 5 * MAX_ZIP:
            raise PaketFehler("Paket ist entpackt zu groß")
    zf.extractall(dest)
    if os.path.isfile(os.path.join(dest, "paket.json")):
        return dest
    subs = [os.path.join(dest, d) for d in os.listdir(dest) if os.path.isfile(os.path.join(dest, d, "paket.json"))]
    if len(subs) != 1:
        raise PaketFehler("Im Paket fehlt paket.json")
    return subs[0]


def install(source: str = "", data: Optional[bytes] = None) -> Tuple[Dict[str, Any], List[str]]:
    """Paket aus Ordner, .swpaket-Datei oder Bytes prüfen und in den Benutzerordner kopieren."""
    tmp = tempfile.mkdtemp(prefix="swpaket_")
    try:
        if data is not None:
            folder = _unzip(data, tmp)
        elif os.path.isdir(source):
            folder = source
        elif os.path.isfile(source):
            with open(source, "rb") as fh:
                folder = _unzip(fh.read(), tmp)
        else:
            raise PaketFehler(f"{source}: nicht gefunden")
        m, lines = check_folder(folder)
        dest = os.path.join(install_dir(), m["id"])
        os.makedirs(install_dir(), exist_ok=True)
        if os.path.abspath(dest) != os.path.abspath(folder):
            if os.path.exists(dest):
                shutil.rmtree(dest)
            shutil.copytree(folder, dest, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        lines = lines + [f"Installiert nach {dest}"]
        for alt in m.get("ersetzt") or []:                 # aufgegangene Pakete aufräumen (ab 2.5.0)
            alt_dir = os.path.join(install_dir(), alt)
            if os.path.isfile(os.path.join(alt_dir, "paket.json")):
                shutil.rmtree(alt_dir, ignore_errors=True)
                lines.append(f"Entfernt: {alt} (steckt jetzt in „{m['name']}“)")
        return m, lines
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def remove(pid: str) -> str:
    if not ID_RE.match(pid):
        raise PaketFehler(f"Paket-id {pid!r} ungültig")
    dest = os.path.join(install_dir(), pid)
    if not os.path.isfile(os.path.join(dest, "paket.json")):
        raise PaketFehler(f"Paket {pid!r} ist nicht im Benutzerordner installiert")
    nutzer = sorted(m.get("name", k) for k, (_, m) in _index().items() if pid in (m.get("benoetigt") or {}))
    if nutzer:
        raise PaketFehler(f"„{pid}“ wird noch gebraucht von: {', '.join(nutzer)} – diese zuerst entfernen")
    shutil.rmtree(dest)
    return dest


def pack(folder: str, out_dir: str = ".") -> Tuple[str, List[str]]:
    """Paketordner prüfen und als <id>-<version>.swpaket verpacken."""
    m, lines = check_folder(folder)
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{m['id']}-{m['version']}{EXT}")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(folder):
            dirs[:] = [d for d in dirs if d != "__pycache__" and not d.startswith(".")]
            for f in sorted(files):
                if f.endswith(".pyc") or f.startswith("."):
                    continue
                full = os.path.join(root, f)
                zf.write(full, os.path.join(m["id"], os.path.relpath(full, folder)))
    return path, lines


TEMPLATE_MODEL = '''"""
{label} – Modell aus dem Paket „{name}“.

Koordinaten in mm, y nach oben. Außenkontur gegen den Uhrzeigersinn, Löcher im Uhrzeigersinn
(add_hole dreht automatisch richtig). Gravuren über add_engrave oder – kollisionsfrei – über
models._deko (Canvas, sign, styled_line …).
"""
from steckwerk import Assembly, Part, circle, rect
from models import _deko as dk
from pakete import num, sel, txt

INFO = dict(
    label="{label}",
    group="Pakete",
    desc="Hängeschild mit Text, Rahmen und zwei Löchern zum Aufhängen.",
    params=[
        num("width", "Breite", 120, 60, 300),
        num("height", "Höhe", 60, 30, 200),
        txt("text", "Text", "Willkommen", "| = neue Zeile"),
        sel("rahmen", "Rahmen", dk.SIGNS, "holz"),
    ],
)


def build(cfg, name="{model}", width=120.0, height=60.0, text="Willkommen", rahmen="holz"):
    W, H = cfg.s(width), cfg.s(height)
    r = min(6.0, H * 0.15)
    outline = rect(-W / 2, 0, W, H)
    part = Part(name, outline)
    for x in (-W / 2 + 8, W / 2 - 8):                       # Aufhängelöcher
        part.add_hole(circle(x, H - 8, 2.0, cfg.arc_tolerance))
    if text.strip():
        cv = dk.Canvas(part, margin=2.0, seed=cfg.seed)
        cands = [(-W / 2 + 14, 4, W / 2 - 14, H - 14), (-W / 2 + 6, 4, W / 2 - 6, H - 14)]
        if dk.sign(cv, text, rahmen, cands, "normal", "gross", min_h=3.0, max_cap=0.3 * H,
                   anchor="mitte", tol=cfg.arc_tolerance) is None:
            raise ValueError(f"Text {{text!r}} passt nicht aufs Schild – kürzer fassen oder größer machen")
    asm = Assembly(name, params=dict(width=W, height=H, text=text, rahmen=rahmen))
    asm.parts.append(part)
    asm.notes.append("Schild an einer Kordel durch die beiden Löcher aufhängen.")
    return asm
'''


def create(pid: str, out_dir: str = ".", name: str = "", autor: str = "") -> str:
    """Neues Paket aus der Vorlage anlegen (ein lauffähiges Beispielmodell)."""
    from steckwerk import __version__
    if not ID_RE.match(pid):
        raise PaketFehler(f"Paket-id {pid!r}: nur Kleinbuchstaben, Ziffern und _ (2–40 Zeichen)")
    folder = os.path.join(out_dir, pid)
    if os.path.exists(folder):
        raise PaketFehler(f"{folder} gibt es schon")
    os.makedirs(folder)
    name = name or pid.replace("_", " ").title()
    manifest = dict(standard=STANDARD, id=pid, name=name, version="1.0.0", autor=autor,
                    beschreibung="Beschreibe hier dein Paket.", steckwerk=__version__, modelle=[pid])
    with open(os.path.join(folder, "paket.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    with open(os.path.join(folder, f"{pid}.py"), "w", encoding="utf-8") as fh:
        fh.write(TEMPLATE_MODEL.format(label=name, name=name, model=pid))
    with open(os.path.join(folder, "LIES MICH.md"), "w", encoding="utf-8") as fh:
        fh.write(f"# {name}\n\nPaket für Steckwerk (Standard {STANDARD}).\n\n"
                 f"- Testen:  python3 cli.py --paket-pruefen {folder}\n"
                 f"- Packen:  python3 cli.py --paket-packen {folder}\n"
                 f"- Laden:   python3 cli.py --paket-installieren {pid}-1.0.0{EXT}\n")
    return folder


def status_text(status) -> str:
    if not status:
        return f"Keine Pakete installiert. Suchorte: {', '.join(search_dirs())}"
    lines = []
    for folder, m, err in status:
        if err:
            lines.append(f"✗ {m.get('id')} ({folder}): {err}")
        else:
            lines.append(f"✓ {m['name']} {m['version']} [{m['id']}] – Modelle: {', '.join(m['modelle'])}"
                         + (f" – von {m['autor']}" if m.get("autor") else ""))
    return "\n".join(lines)
