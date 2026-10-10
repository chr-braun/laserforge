#!/usr/bin/env python3
"""
steckwerk_app.py – Steckwerk als App: lokaler Server + Browserfenster, ohne Terminal.

Die Mac-App (Steckwerk.app) ruft diese Datei auf; sie läuft aber auf jedem System:

  python3 steckwerk_app.py              starten (läuft es schon, öffnet sich nur das Fenster)
  python3 steckwerk_app.py --self-test  prüfen, ob alles da ist, und beenden

Verhalten:
  - Nur eine Instanz. Ein zweiter Start öffnet bloß ein neues Fenster.
  - Die App beendet sich selbst, wenn alle Steckwerk-Fenster zu sind, nach 20 Minuten ohne
    Benutzung oder über „Beenden“ in der Oberfläche.
  - „In Ordner speichern“ schreibt nach Dokumente/Steckwerk.
  - Mac: Beim Start außerhalb des Programme-Ordners bietet die App an, sich dorthin zu installieren.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import threading
import time
import traceback
import urllib.request
import webbrowser
from typing import List, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from steckwerk import __version__  # noqa: E402
import webui  # noqa: E402

APP_NAME = "Steckwerk"
LEGACY_NAME = "Laserforge"
HEADERS = {"Content-Type": "application/json", "X-Steckwerk": "1", "X-Laserforge": "1"}   # auch alte Instanzen
DEFAULT_PORT = 8765
MAC = sys.platform == "darwin"
WINDOWS = os.name == "nt"


def log(msg: str) -> None:
    print(time.strftime("%Y-%m-%d %H:%M:%S"), msg, flush=True)


# ---------------------------------------------------------------------- Orte
def data_dir() -> str:
    """Ordner für Einstellungen und die Info über die laufende Instanz."""
    if MAC:
        base = os.path.expanduser("~/Library/Application Support")
    elif WINDOWS:
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    else:
        base = os.environ.get("XDG_STATE_HOME") or os.path.expanduser("~/.local/state")
    path = os.path.join(base, APP_NAME)
    os.makedirs(path, exist_ok=True)
    return path


def default_out_dir() -> str:
    docs = os.path.expanduser("~/Documents")
    base = docs if os.path.isdir(docs) else os.path.expanduser("~")
    legacy = os.path.join(base, LEGACY_NAME)                   # bis 1.7: dort weiter speichern
    if os.path.isdir(legacy) and not os.path.exists(os.path.join(base, APP_NAME)):
        return legacy
    return os.path.join(base, APP_NAME)


def _read_json(path: str) -> dict:
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _write_json(path: str, data: dict) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def settings_path(base: Optional[str] = None) -> str:
    return os.path.join(base or data_dir(), "einstellungen.json")


def running_path(base: Optional[str] = None) -> str:
    return os.path.join(base or data_dir(), "laeuft.json")


# ---------------------------------------------------------------------- System
def open_url(url: str) -> None:
    if MAC:
        subprocess.Popen(["open", url])
    else:
        webbrowser.open(url)


def open_folder(path: str) -> None:
    if MAC:
        subprocess.Popen(["open", path])
    elif WINDOWS:
        os.startfile(path)                                      # type: ignore[attr-defined]
    else:
        subprocess.Popen(["xdg-open", path])


def _osa_text(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def dialog(text: str, buttons: List[str], default: str, icon: str = "note") -> Optional[str]:
    """Mac-Dialog; gibt den gedrückten Knopf zurück (None ohne Dialog oder bei Abbruch)."""
    if not MAC:
        return None
    script = (f"display dialog {_osa_text(text)} with title {_osa_text(APP_NAME)} "
              f"buttons {{{', '.join(_osa_text(b) for b in buttons)}}} "
              f"default button {_osa_text(default)} with icon {icon}")
    try:
        r = subprocess.run(["osascript", "-e", "activate", "-e", script],      # activate: Dialog nach vorn
                           capture_output=True, text=True, timeout=600)
    except (OSError, subprocess.SubprocessError):
        return None
    for b in buttons:
        if r.stdout.strip().endswith(":" + b):
            return b
    return None


def notify(text: str) -> None:
    if MAC:
        subprocess.run(["osascript", "-e", f"display notification {_osa_text(text)} with title {_osa_text(APP_NAME)}"],
                       capture_output=True)
    log(text)


# ---------------------------------------------------------------------- Installation (Mac)
def is_translocated(bundle: str) -> bool:
    """macOS startet Apps aus „Downloads“ von einer temporären, schreibgeschützten Kopie."""
    return "/AppTranslocation/" in bundle


def is_installed(bundle: str) -> bool:
    b = os.path.realpath(bundle)
    homes = [os.path.realpath("/Applications"), os.path.realpath(os.path.expanduser("~/Applications"))]
    return any(b.startswith(h + os.sep) for h in homes)


def install_bundle(bundle: str, target_dir: str) -> str:
    """Kopiert die App nach target_dir (ersetzt eine ältere Version) und gibt den neuen Pfad zurück."""
    os.makedirs(target_dir, exist_ok=True)
    target = os.path.join(target_dir, APP_NAME + ".app")
    fresh, old = target + ".neu", target + ".alt"
    for p in (fresh, old):
        shutil.rmtree(p, ignore_errors=True)
    if MAC:
        subprocess.run(["ditto", bundle, fresh], check=True)
        subprocess.run(["xattr", "-dr", "com.apple.quarantine", fresh], capture_output=True)
    else:
        shutil.copytree(bundle, fresh, symlinks=True)
    if os.path.exists(target):
        os.rename(target, old)
    os.rename(fresh, target)
    shutil.rmtree(old, ignore_errors=True)
    legacy = os.path.join(target_dir, LEGACY_NAME + ".app")    # bis 1.7 hieß die App „Laserforge“
    if os.path.isdir(legacy):
        shutil.rmtree(legacy, ignore_errors=True)
    return target


def app_dirs() -> List[str]:
    return ["/Applications", os.path.expanduser("~/Applications")]


def installed_version() -> Optional[Tuple[str, str]]:
    """(Ordner, Version) einer schon installierten Steckwerk.app – oder None."""
    import plistlib
    for d, name in [(d, n) for n in (APP_NAME, LEGACY_NAME) for d in app_dirs()]:
        plist = os.path.join(d, name + ".app", "Contents", "Info.plist")
        if os.path.exists(plist):
            try:
                with open(plist, "rb") as fh:
                    return d, str(plistlib.load(fh).get("CFBundleShortVersionString", "?"))
            except Exception:                              # kaputte Info.plist: trotzdem ersetzen
                return d, "?"
    return None


def maybe_install(bundle: Optional[str]) -> bool:
    """Mac: App aus „Downloads“ in den Programme-Ordner übernehmen bzw. eine ältere installierte Version
    ersetzen. True = installierte Kopie gestartet."""
    if not (MAC and bundle and bundle.endswith(".app")) or is_installed(bundle):
        return False
    sp = settings_path()
    settings = _read_json(sp)
    inst = installed_version()
    upgrade = inst is not None and inst[1] != __version__
    if upgrade:
        if settings.get("update_abgelehnt") == __version__:
            return False
        yes = "Ersetzen"
        answer = dialog(f"Im Programme-Ordner ist Steckwerk {inst[1]} installiert.\n\n"
                        f"Durch die neue Version {__version__} ersetzen? Deine Einstellungen und "
                        "gespeicherten Dateien bleiben erhalten.", ["Nur starten", yes], yes)
    else:
        if settings.get("install_abgelehnt") and not is_translocated(bundle):
            return False
        yes = "Installieren"
        answer = dialog("Steckwerk in den Programme-Ordner installieren?\n\n"
                        "Danach startest du es wie jede andere App über Launchpad, Spotlight oder das Dock. "
                        "Die heruntergeladene Kopie kannst du anschließend löschen.",
                        ["Nur starten", yes], yes)
    if answer != yes:
        if upgrade:
            settings["update_abgelehnt"] = __version__
        else:
            settings["install_abgelehnt"] = True
        _write_json(sp, settings)
        return False
    if inst:
        target_dir = inst[0]
    else:
        target_dir = "/Applications" if os.access("/Applications", os.W_OK) else os.path.expanduser("~/Applications")
    try:
        target = install_bundle(bundle, target_dir)
    except (OSError, subprocess.SubprocessError) as e:
        log(f"Installation fehlgeschlagen: {e}")
        dialog(f"Die Installation hat nicht geklappt:\n{e}\n\nSteckwerk startet jetzt von hier aus.",
               ["OK"], "OK", icon="caution")
        return False
    notify(f"Steckwerk ist installiert ({target_dir}).")
    subprocess.Popen(["open", target])
    return True


# ---------------------------------------------------------------------- Instanzen
def probe(port: int, timeout: float = 1.5) -> Optional[dict]:
    """Antwortet auf dem Port ein Steckwerk? Dann dessen Ping-Antwort, sonst None."""
    req = urllib.request.Request(f"http://127.0.0.1:{port}/api/ping", b"{}",
                                 HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.load(r)
        return data if isinstance(data, dict) and data.get("app") in ("steckwerk", "laserforge") else None
    except (OSError, ValueError):
        return None


def stop_instance(port: int, wait: float = 5.0) -> bool:
    req = urllib.request.Request(f"http://127.0.0.1:{port}/api/quit", b"{}",
                                 HEADERS)
    try:
        urllib.request.urlopen(req, timeout=2).read()
    except OSError:
        pass
    end = time.monotonic() + wait
    while time.monotonic() < end:
        if probe(port, 0.5) is None:
            return True
        time.sleep(0.2)
    return False


def find_running(base: Optional[str] = None) -> Optional[int]:
    """Port einer laufenden Steckwerk-Instanz dieser Version, sonst None (ältere wird beendet)."""
    info = _read_json(running_path(base))
    port = info.get("port")
    if not isinstance(port, int):
        return None
    answer = probe(port)
    if answer is None:
        return None
    if answer.get("version") != __version__:
        log(f"Beende ältere Steckwerk-Version {answer.get('version')} auf Port {port}")
        stop_instance(port)
        return None
    if answer.get("files") is False:
        log(f"Steckwerk auf Port {port} findet seine Dateien nicht mehr – starte neu")
        stop_instance(port)
        return None
    return port


def bind(port: int, out_dir: str, session: webui.Session, tries: int = 10, bundle: Optional[str] = None):
    """Server auf dem Wunschport (oder den nächsten freien) starten. (server, None) oder (None, port_fremd)."""
    for p in range(port, port + tries):
        try:
            srv = webui.make_server("127.0.0.1", p, out_dir, quiet=True, app=True,
                                    session=session, open_folder=open_folder, bundle=bundle)
            return srv, None
        except OSError:
            other = probe(p)
            if other and other.get("version") == __version__:
                return None, p                                # gleichzeitig gestartete Instanz
    raise OSError(f"Kein freier Port zwischen {port} und {port + tries - 1}")


# ---------------------------------------------------------------------- Start
def run(port: int = DEFAULT_PORT, out_dir: Optional[str] = None, browser: bool = True,
        idle_limit: float = 20 * 60, grace: float = 10.0, base: Optional[str] = None,
        ready: Optional[threading.Event] = None, bundle: Optional[str] = None) -> int:
    base = base or data_dir()
    out_dir = out_dir or default_out_dir()
    running = find_running(base)
    if running:
        log(f"Steckwerk läuft schon auf Port {running} – öffne nur das Fenster")
        if browser:
            open_url(f"http://127.0.0.1:{running}/")
        return 0
    session = webui.Session(idle_limit=idle_limit, grace=grace)
    srv, other = bind(port, out_dir, session, bundle=bundle)
    if srv is None:
        if browser:
            open_url(f"http://127.0.0.1:{other}/")
        return 0
    real_port = srv.server_address[1]
    url = f"http://127.0.0.1:{real_port}/"
    _write_json(running_path(base), {"port": real_port, "pid": os.getpid(), "version": __version__})
    log(f"Steckwerk {__version__} läuft: {url} · Speicherordner {out_dir} · Python {sys.version.split()[0]}")

    def watchdog():
        while True:
            time.sleep(0.5)
            reason = session.should_quit()
            if reason:
                log(f"Beende ({reason})")
                srv.shutdown()
                return

    threading.Thread(target=watchdog, daemon=True).start()
    if browser:
        threading.Timer(0.3, open_url, args=(url,)).start()
    if ready:
        ready.port = real_port                                    # type: ignore[attr-defined]
        ready.set()
    try:
        srv.serve_forever(poll_interval=0.25)
    finally:
        srv.server_close()
        if _read_json(running_path(base)).get("pid") == os.getpid():
            try:
                os.remove(running_path(base))
            except OSError:
                pass
    return 0


def self_test() -> int:
    import service
    r = service.generate({"model": "schneeflocke", "params": {"count": 1}})
    assert r["ok"], r
    assert os.path.exists(webui.INDEX), webui.INDEX
    print(f"Steckwerk {__version__} OK · Python {sys.version.split()[0]} · {sys.executable}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="steckwerk_app", description="Steckwerk als App starten")
    ap.add_argument("--bundle", help="Pfad der Mac-App (setzt das Startskript)")
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--out", help="Ordner für „In Ordner speichern“ (Default: Dokumente/Steckwerk)")
    ap.add_argument("--no-browser", action="store_true", help="kein Fenster öffnen")
    ap.add_argument("--idle", type=float, default=20, help="Minuten ohne Benutzung bis zum Beenden")
    ap.add_argument("--self-test", action="store_true", help="nur prüfen, ob alles da ist")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    from steckwerk import migrate_legacy
    for d in migrate_legacy():
        log(f"Daten von Laserforge übernommen: {d}")
    try:
        if a.bundle and hasattr(os, "setsid"):
            try:
                os.setsid()                    # vom Startskript lösen – die App läuft im Hintergrund weiter
            except OSError:
                pass
        if maybe_install(a.bundle):
            return 0
        return run(a.port, a.out, not a.no_browser, idle_limit=a.idle * 60, bundle=a.bundle)
    except Exception as e:                                       # pragma: no cover – letzte Rettung
        traceback.print_exc()
        dialog(f"Steckwerk konnte nicht starten:\n{e}\n\nDetails stehen in ~/Library/Logs/Steckwerk.log",
               ["OK"], "OK", icon="stop")
        return 1


if __name__ == "__main__":
    sys.exit(main())
