"""
updater.py – neue Steckwerk-Versionen und Pakete finden, laden und installieren.

Steckwerk liest einen Update-Kanal: eine Datei feed.json plus die Dateien, auf die sie zeigt
(Mac-App als ZIP, Pakete als .swpaket). Den Kanal baut packaging/update_kanal.py.

  feed.json = {
    "standard": 1,
    "programm": {"version": "1.7.0", "datum": "2026-10-10", "hinweise": ["…"],
                 "mac": {"datei": "Steckwerk-1.7.0-macOS.zip", "sha256": "…", "groesse": 123}},
    "pakete": [{"id": "halloween", "name": "Halloween", "version": "1.0.0", "beschreibung": "…",
                "steckwerk": "1.5.0", "datei": "pakete/halloween-1.0.0.swpaket", "sha256": "…", "groesse": 456}]
  }

Dateipfade gelten relativ zur feed.json. Jede Datei wird vor dem Installieren über sha256 geprüft.

Einstellungen (Kanal-Adresse, Zugangsschlüssel für ein privates GitHub-Repo, automatisch prüfen)
liegen in <Steckwerk-Datenordner>/update.json. Den Schlüssel legt die App auf dem Mac in den
Schlüsselbund, sonst in die Datei (nur für den Benutzer lesbar).
Umgebungsvariablen: STECKWERK_UPDATE_KANAL (Adresse), STECKWERK_DATEN (Datenordner, für Tests).
"""
from __future__ import annotations

import hashlib
import json
import os
import plistlib
import shutil
import ssl
import stat
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from typing import Any, Dict, List, Optional, Tuple

from steckwerk import __version__

STANDARD = 1
KANAL = "https://raw.githubusercontent.com/chr-braun/steckwerk/updates/feed.json"
MAX_FEED = 1024 * 1024
MAX_DATEI = 80 * 1024 * 1024
MAC = sys.platform == "darwin"
KEYCHAIN = "Steckwerk Updates"
GITHUB_HOSTS = {"raw.githubusercontent.com", "api.github.com", "github.com", "objects.githubusercontent.com"}


class UpdateFehler(RuntimeError):
    pass


def ver(v: Any) -> Tuple[int, ...]:
    try:
        return tuple(int(x) for x in str(v).split(".")[:3])
    except ValueError:
        return (0,)


# --- Einstellungen --------------------------------------------------------------------------------

def data_dir() -> str:
    env = os.environ.get("STECKWERK_DATEN")
    if env:
        base = env
    elif MAC:
        base = os.path.expanduser("~/Library/Application Support/Steckwerk")
    elif os.name == "nt":
        base = os.path.join(os.environ.get("APPDATA") or os.path.expanduser("~"), "Steckwerk")
    else:
        base = os.path.join(os.environ.get("XDG_STATE_HOME") or os.path.expanduser("~/.local/state"), "Steckwerk")
    os.makedirs(base, exist_ok=True)
    return base


def _config_path() -> str:
    return os.path.join(data_dir(), "update.json")


def _read() -> Dict[str, Any]:
    try:
        with open(_config_path(), encoding="utf-8") as fh:
            d = json.load(fh)
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def _write(d: Dict[str, Any]) -> None:
    path = _config_path()
    tmp = path + ".tmp"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(d, fh, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def _use_keychain() -> bool:
    return MAC and not os.environ.get("STECKWERK_DATEN") and shutil.which("security") is not None


def get_token() -> str:
    if _use_keychain():
        for service in (KEYCHAIN, "Laserforge Updates"):              # bis 1.7: alter Name
            r = subprocess.run(["security", "find-generic-password", "-s", service, "-a", "github", "-w"],
                               capture_output=True, text=True)
            if r.returncode == 0 and r.stdout.strip():
                return r.stdout.strip()
        return ""
    return str(_read().get("token") or "")


def set_token(token: str) -> None:
    token = token.strip()
    if _use_keychain():
        subprocess.run(["security", "delete-generic-password", "-s", KEYCHAIN, "-a", "github"], capture_output=True)
        if token:
            r = subprocess.run(["security", "add-generic-password", "-s", KEYCHAIN, "-a", "github", "-w", token, "-U"],
                               capture_output=True, text=True)
            if r.returncode != 0:
                raise UpdateFehler("Schlüssel ließ sich nicht im Schlüsselbund speichern: " + r.stderr.strip())
        return
    d = _read()
    if token:
        d["token"] = token
    else:
        d.pop("token", None)
    _write(d)


def settings() -> Dict[str, Any]:
    """Einstellungen für die Oberfläche – den Schlüssel selbst gibt es nie zurück."""
    d = _read()
    return {"kanal": kanal(), "kanal_eigen": bool(d.get("kanal")), "token_gesetzt": bool(get_token()),
            "auto": d.get("auto", True), "zuletzt": d.get("zuletzt")}


def save_settings(kanal_url: Optional[str] = None, token: Optional[str] = None, auto: Optional[bool] = None) -> Dict[str, Any]:
    d = _read()
    if kanal_url is not None:
        kanal_url = kanal_url.strip()
        if kanal_url and not kanal_url.startswith(("https://", "http://127.0.0.1", "http://localhost", "file:")):
            raise UpdateFehler("Die Kanal-Adresse muss mit https:// beginnen")
        if kanal_url and kanal_url != KANAL:
            d["kanal"] = kanal_url
        else:
            d.pop("kanal", None)
    if auto is not None:
        d["auto"] = bool(auto)
    _write(d)
    if token is not None:
        set_token(token)
    return settings()


def kanal() -> str:
    return os.environ.get("STECKWERK_UPDATE_KANAL") or _read().get("kanal") or KANAL


# --- Laden ----------------------------------------------------------------------------------------

def _ssl_context() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    paths = ssl.get_default_verify_paths()
    if not (paths.cafile and os.path.exists(paths.cafile)) and not (paths.capath and os.path.isdir(paths.capath)):
        # python.org-Python auf dem Mac bringt keine Zertifikate mit: certifi oder die Systemdatei nehmen
        try:
            import certifi  # type: ignore
            ctx.load_verify_locations(certifi.where())
        except ImportError:
            for f in ("/etc/ssl/cert.pem", "/private/etc/ssl/cert.pem"):
                if os.path.exists(f):
                    ctx.load_verify_locations(f)
                    break
    return ctx


def fetch(url: str, limit: int = MAX_DATEI, token: Optional[str] = None) -> bytes:
    """Datei laden. Für GitHub-Adressen wird der Zugangsschlüssel mitgeschickt."""
    host = urllib.parse.urlparse(url).hostname or ""
    headers = {"User-Agent": f"Steckwerk/{__version__}", "Cache-Control": "no-cache"}
    tok = get_token() if token is None else token
    if tok and host in GITHUB_HOSTS:
        headers["Authorization"] = "token " + tok
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30, context=_ssl_context() if url.startswith("https") else None) as r:
            data = r.read(limit + 1)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            hint = (" Ist das Repo privat? Dann unter „Updates → Einstellungen“ einen Lese-Schlüssel eintragen."
                    if host in GITHUB_HOSTS and not tok else "")
            raise UpdateFehler(f"Nicht gefunden: {url}.{hint}")
        if e.code in (401, 403):
            raise UpdateFehler("GitHub lehnt den Zugangsschlüssel ab – ist er abgelaufen oder fehlt ihm das Leserecht?")
        raise UpdateFehler(f"Der Update-Server antwortet mit Fehler {e.code}")
    except ssl.SSLError as e:
        raise UpdateFehler(f"Sichere Verbindung fehlgeschlagen ({e.reason or e}).")
    except (urllib.error.URLError, OSError) as e:
        reason = getattr(e, "reason", e)
        if isinstance(reason, FileNotFoundError) or isinstance(e, FileNotFoundError):
            raise UpdateFehler(f"Nicht gefunden: {url}")
        if isinstance(reason, ssl.SSLError):
            raise UpdateFehler(f"Sichere Verbindung fehlgeschlagen ({reason.reason or reason}).")
        raise UpdateFehler(f"Keine Verbindung zum Update-Server ({reason}). Bist du online?")
    if len(data) > limit:
        raise UpdateFehler(f"Datei ist größer als erwartet: {url}")
    return data


def _join(base: str, rel: str) -> str:
    rel = str(rel)
    if rel.startswith(("https://", "http://", "file:")):
        return rel
    if rel.startswith("/") or ".." in rel.split("/"):
        raise UpdateFehler(f"Unzulässiger Pfad im Update-Kanal: {rel}")
    return urllib.parse.urljoin(base, urllib.parse.quote(rel))


def _entry(d: Any, what: str) -> Dict[str, Any]:
    if not isinstance(d, dict) or not d.get("datei") or not d.get("sha256"):
        raise UpdateFehler(f"Update-Kanal ist unvollständig ({what}: datei/sha256 fehlt)")
    return d


def load_feed(url: Optional[str] = None) -> Dict[str, Any]:
    url = url or kanal()
    try:
        feed = json.loads(fetch(url, MAX_FEED).decode("utf-8"))
    except ValueError:
        raise UpdateFehler("Der Update-Kanal liefert kein gültiges JSON")
    if not isinstance(feed, dict) or int(feed.get("standard", 0) or 0) < 1:
        raise UpdateFehler("Das ist kein Steckwerk-Update-Kanal")
    if int(feed["standard"]) > STANDARD:
        raise UpdateFehler("Der Update-Kanal braucht eine neuere Steckwerk – bitte einmal von Hand aktualisieren")
    feed["_url"] = url
    if not isinstance(feed.get("pakete", []), list):
        raise UpdateFehler("Update-Kanal: „pakete“ muss eine Liste sein")
    return feed


def download(feed: Dict[str, Any], entry: Dict[str, Any]) -> bytes:
    data = fetch(_join(feed["_url"], entry["datei"]))
    if hashlib.sha256(data).hexdigest() != str(entry["sha256"]).lower():
        raise UpdateFehler(f"{entry['datei']}: Prüfsumme stimmt nicht – Download beschädigt oder verändert, nichts installiert")
    return data


# --- Prüfen ---------------------------------------------------------------------------------------

def installed_pakete() -> Dict[str, str]:
    import pakete
    return {m.get("id"): str(m.get("version", "0")) for _, m, _, err in pakete.discover() if m.get("id")}


def check(bundle: Optional[str] = None, feed: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Was gibt es Neues? bundle = Pfad der laufenden Mac-App (nur dann sind Programm-Updates möglich)."""
    feed = feed or load_feed()
    d = _read()
    d["zuletzt"] = time.strftime("%Y-%m-%d %H:%M")
    try:
        _write(d)
    except OSError:
        pass
    prog = feed.get("programm") or {}
    neu = ver(prog.get("version", "0")) > ver(__version__)
    ok, grund = program_installable(bundle)
    if neu and not prog.get("mac"):
        ok, grund = False, "Für diese Version gibt es kein Mac-Paket im Kanal."
    programm = dict(installiert=__version__, version=str(prog.get("version", "")), neu=neu,
                    datum=prog.get("datum", ""), hinweise=[str(h) for h in prog.get("hinweise", [])][:30],
                    hinweise_en=[str(h) for h in prog.get("hinweise_en", [])][:30],
                    kann_installieren=bool(neu and ok), grund="" if ok else grund,
                    seite=str(prog.get("seite", "")))
    have = installed_pakete()
    pk = []
    for p in feed.get("pakete", []):
        if not isinstance(p, dict) or not p.get("id"):
            continue
        cur = have.get(p["id"])
        need = str(p.get("steckwerk") or p.get("laserforge") or "0")
        alte = [str(r) for r in (p.get("ersetzt") or []) if str(r) in have]
        if ver(need) > ver(__version__):
            status = "zu_neu"
        elif cur is None and alte:                 # löst installierte Pakete ab (ab 2.5.0) → wie ein Update
            status = "update"
        elif cur is None:
            status = "neu"
        elif ver(p.get("version")) > ver(cur):
            status = "update"
        else:
            status = "aktuell"
        pk.append(dict(id=str(p["id"]), name=str(p.get("name", p["id"])), version=str(p.get("version", "")),
                       beschreibung=str(p.get("beschreibung", "")), name_en=str(p.get("name_en", "")),
                       beschreibung_en=str(p.get("beschreibung_en", "")), installiert=cur, steckwerk=need, status=status,
                       benoetigt=sorted(str(k) for k in (p.get("benoetigt") or {})), ersetzt=alte,
                       groesse=int(p.get("groesse", 0) or 0),
                       inhalt=[str(x) for x in p.get("inhalt") or []], inhalt_en=[str(x) for x in p.get("inhalt_en") or []]))
    pk.sort(key=lambda p: (["update", "neu", "zu_neu", "aktuell"].index(p["status"]), p["name"].lower()))
    anzahl = int(programm["neu"]) + sum(p["status"] in ("update", "neu") for p in pk)
    return {"ok": True, "programm": programm, "pakete": pk, "anzahl": anzahl,
            "updates": int(programm["neu"]) + sum(p["status"] == "update" for p in pk), "kanal": feed["_url"]}


# --- Pakete ---------------------------------------------------------------------------------------

def install_paket(pid: str, feed: Optional[Dict[str, Any]] = None, _kette: Tuple[str, ...] = ()) -> Dict[str, Any]:
    """Paket aus dem Kanal installieren – benötigte Pakete (ab 2.4.0) vorher automatisch mit."""
    import pakete
    feed = feed or load_feed()
    entry = next((p for p in feed.get("pakete", []) if isinstance(p, dict) and p.get("id") == pid), None)
    if entry is None:
        raise UpdateFehler(f"Paket {pid!r} gibt es im Update-Kanal nicht")
    entry.setdefault("steckwerk", entry.get("laserforge", "0"))
    if ver(entry["steckwerk"]) > ver(__version__):
        raise UpdateFehler(f"„{entry.get('name', pid)}“ braucht Steckwerk {entry['steckwerk']} – erst das Programm aktualisieren")
    if pid in _kette:
        raise UpdateFehler(f"Pakete benötigen sich gegenseitig: {' → '.join(_kette + (pid,))}")
    have = installed_pakete()
    for dep, need in sorted((entry.get("benoetigt") or {}).items()):
        if have.get(dep) is None or ver(have[dep]) < ver(need):
            install_paket(dep, feed, _kette + (pid,))
    m, _ = pakete.install(data=download(feed, _entry(entry, pid)))
    if m["id"] != pid:
        raise UpdateFehler(f"Das geladene Paket heißt {m['id']!r} statt {pid!r}")
    return m


def install_alle_pakete(feed: Optional[Dict[str, Any]] = None, nur_updates: bool = True) -> List[Dict[str, Any]]:
    feed = feed or load_feed()
    todo = [p["id"] for p in check(feed=feed)["pakete"] if p["status"] == "update" or (not nur_updates and p["status"] == "neu")]
    want = {p["id"]: p["version"] for p in feed.get("pakete", []) if isinstance(p, dict) and p.get("id")}
    done = []
    for pid in todo:
        cur = installed_pakete().get(pid)
        if cur is not None and ver(cur) >= ver(want.get(pid, "0")):     # schon als Abhängigkeit mitgekommen
            continue
        done.append(install_paket(pid, feed))
    return done


# --- Programm (Mac-App) ---------------------------------------------------------------------------

def program_installable(bundle: Optional[str]) -> Tuple[bool, str]:
    if not bundle or not bundle.endswith(".app"):
        return False, "Programm-Updates installiert die Mac-App selbst. Hier bitte von Hand aktualisieren (git pull bzw. neue ZIP)."
    if "/AppTranslocation/" in bundle:
        return False, "Steckwerk läuft noch aus „Downloads“. Erst in den Programme-Ordner installieren."
    parent = os.path.dirname(os.path.realpath(bundle))
    if not os.access(parent, os.W_OK):
        return False, f"Keine Schreibrechte im Ordner {parent}."
    return True, ""


def _extract_app(data: bytes, dest: str) -> str:
    """Mac-ZIP sicher entpacken (Rechte bleiben erhalten) und den Pfad der Steckwerk.app liefern."""
    try:
        zf = zipfile.ZipFile(__import__("io").BytesIO(data))
    except zipfile.BadZipFile:
        raise UpdateFehler("Das Programm-Update ist kein gültiges ZIP")
    app = None
    for info in zf.infolist():
        name = info.filename
        parts = name.replace("\\", "/").split("/")
        if name.startswith("/") or ".." in parts or ":" in name:
            raise UpdateFehler(f"Unzulässiger Pfad im Update: {name}")
        mode = (info.external_attr >> 16) & 0o7777
        if stat.S_ISLNK(info.external_attr >> 16):
            raise UpdateFehler("Das Update enthält Verknüpfungen – nicht erlaubt")
        target = os.path.join(dest, *[p for p in parts if p])
        if name.endswith("/"):
            os.makedirs(target, exist_ok=True)
            continue
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with zf.open(info) as src, open(target, "wb") as out:
            shutil.copyfileobj(src, out)
        os.chmod(target, (mode & 0o755) or 0o644)
        if "Steckwerk.app" in parts and app is None:
            app = os.path.join(dest, *parts[: parts.index("Steckwerk.app") + 1])
    if not app or not os.path.isfile(os.path.join(app, "Contents", "Info.plist")):
        raise UpdateFehler("Im Update fehlt die Steckwerk.app")
    return app


def app_version(app: str) -> str:
    with open(os.path.join(app, "Contents", "Info.plist"), "rb") as fh:
        return str(plistlib.load(fh).get("CFBundleShortVersionString", ""))


def install_program(bundle: str, feed: Optional[Dict[str, Any]] = None) -> Tuple[str, str]:
    """Neue Mac-App laden, prüfen und die laufende App ersetzen. Liefert (neuer Pfad, Version)."""
    ok, grund = program_installable(bundle)
    if not ok:
        raise UpdateFehler(grund)
    feed = feed or load_feed()
    prog = feed.get("programm") or {}
    want = str(prog.get("version", ""))
    if ver(want) <= ver(__version__):
        raise UpdateFehler(f"Steckwerk {__version__} ist schon aktuell")
    data = download(feed, _entry(prog.get("mac"), "programm.mac"))
    tmp = tempfile.mkdtemp(prefix="swupdate_", dir=data_dir())
    try:
        app = _extract_app(data, tmp)
        got = app_version(app)
        if got != want:
            raise UpdateFehler(f"Das Update enthält Version {got} statt {want} – nichts geändert")
        import steckwerk_app
        target = steckwerk_app.install_bundle(app, os.path.dirname(os.path.realpath(bundle)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return target, want


def restart(target: str) -> None:
    """Neue App kurz nach dem Beenden dieser Instanz starten."""
    if MAC:
        subprocess.Popen(["/bin/sh", "-c", 'sleep 1.5; open "$0"', target], start_new_session=True,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL)
