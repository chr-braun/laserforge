"""App-Betrieb: Lebenszeichen, Schutz der API, eine Instanz, Mac-Paket und Startskript."""
import json
import os
import plistlib
import shutil
import stat
import subprocess
import sys
import threading
import urllib.error
import urllib.request
import zipfile

import pytest

import steckwerk_app as lfa
import webui
from steckwerk import __version__

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "packaging"))
import build_macos  # noqa: E402


class Clock:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


# ---------------------------------------------------------------------- Session
def test_session_quits_after_last_window_closed():
    c = Clock()
    s = webui.Session(idle_limit=600, grace=10, clock=c)
    s.touch("a"); s.touch("b")
    s.bye("a"); c.t += 30
    assert s.should_quit() is None                     # b ist noch offen
    s.bye("b"); c.t += 5
    assert s.should_quit() is None                     # Gnadenfrist (Neuladen)
    s.touch("b2"); c.t += 30
    assert s.should_quit() is None                     # neu geladen → läuft weiter
    s.bye("b2"); c.t += 11
    assert s.should_quit() == "alle Fenster geschlossen"


def test_session_idle_and_quit_button():
    c = Clock()
    s = webui.Session(idle_limit=600, grace=10, clock=c)
    c.t += 599
    assert s.should_quit() is None
    c.t += 2
    assert "nicht benutzt" in s.should_quit()
    s2 = webui.Session(clock=c)
    s2.request_quit()
    assert "Beenden" in s2.should_quit()


def test_session_forgets_vanished_windows():
    c = Clock()
    s = webui.Session(idle_limit=600, grace=10, clock=c)
    s.touch("weg")                                     # Fenster stürzt ab, kein bye
    c.t += 300; s.touch()                              # andere Anfragen halten die App wach
    c.t += 301; s.touch()
    assert s.should_quit() is None and "weg" not in s.clients


# ---------------------------------------------------------------------- Server im App-Modus
@pytest.fixture
def app_server(tmp_path):
    opened = []
    session = webui.Session(idle_limit=600, grace=10)
    srv = webui.make_server("127.0.0.1", 0, str(tmp_path / "out"), quiet=True, app=True,
                            session=session, open_folder=opened.append)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}", session, opened, tmp_path / "out"
    srv.shutdown()
    srv.server_close()


def _post(url, obj=None, headers=None):
    h = {"Content-Type": "application/json", "X-Steckwerk": "1"}
    h.update(headers or {})
    req = urllib.request.Request(url, json.dumps(obj or {}).encode(), {k: v for k, v in h.items() if v is not None})
    return urllib.request.urlopen(req, timeout=60)


def test_app_endpoints(app_server):
    base, session, opened, out = app_server
    schema = json.load(urllib.request.urlopen(base + "/api/schema", timeout=10))
    assert schema["app"] is True and schema["out_dir"] == str(out)
    ping = json.load(_post(base + "/api/ping", {"client": "fenster1"}))
    assert ping == {"ok": True, "app": "steckwerk", "version": __version__, "pid": os.getpid(),
                    "files": True}
    assert "fenster1" in session.clients
    assert json.load(_post(base + "/api/open-folder"))["ok"] and opened == [str(out)] and out.is_dir()
    _post(base + "/api/bye", {"client": "fenster1"})
    assert not session.clients and session.closed_at is not None
    _post(base + "/api/quit")
    assert session.quit_requested
    icon = urllib.request.urlopen(base + "/favicon.png", timeout=10)
    assert icon.headers["Content-Type"] == "image/png" and icon.read(8) == b"\x89PNG\r\n\x1a\n"


def test_api_needs_header_and_local_host(app_server):
    base = app_server[0]
    with pytest.raises(urllib.error.HTTPError) as e:              # fremde Webseite: kein eigener Header
        _post(base + "/api/quit", headers={"X-Steckwerk": None})
    assert e.value.code == 403 and not app_server[1].quit_requested
    req = urllib.request.Request(base + "/api/schema", headers={"Host": "evil.example:8765"})
    with pytest.raises(urllib.error.HTTPError) as e:              # DNS-Rebinding
        urllib.request.urlopen(req, timeout=10)
    assert e.value.code == 403


def test_quit_and_folder_only_in_app_mode(tmp_path):
    srv = webui.make_server("127.0.0.1", 0, str(tmp_path), quiet=True)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        base = f"http://127.0.0.1:{srv.server_address[1]}"
        for path in ("/api/quit", "/api/open-folder"):
            with pytest.raises(urllib.error.HTTPError) as e:
                _post(base + path)
            assert e.value.code == 404
        assert json.load(urllib.request.urlopen(base + "/api/schema", timeout=10))["app"] is False
    finally:
        srv.shutdown(); srv.server_close()


# ---------------------------------------------------------------------- Start, eine Instanz, Ende
def test_run_single_instance_and_shutdown(tmp_path, monkeypatch):
    opened = []
    monkeypatch.setattr(lfa, "open_url", opened.append)
    ready = threading.Event()
    t = threading.Thread(target=lfa.run, kwargs=dict(port=0, out_dir=str(tmp_path / "out"), browser=True,
                                                     grace=0.5, base=str(tmp_path), ready=ready), daemon=True)
    t.start()
    assert ready.wait(10)
    port = ready.port
    info = json.loads((tmp_path / "laeuft.json").read_text())
    assert info == {"port": port, "pid": os.getpid(), "version": __version__}
    assert lfa.find_running(str(tmp_path)) == port
    assert lfa.run(port=0, base=str(tmp_path)) == 0                # zweiter Start öffnet nur das Fenster
    t0 = threading.Event(); t0.wait(0.5)
    assert opened == [f"http://127.0.0.1:{port}/"] * 2
    base = f"http://127.0.0.1:{port}"
    _post(base + "/api/ping", {"client": "x"})
    _post(base + "/api/bye", {"client": "x"})
    t.join(10)
    assert not t.is_alive()                                       # Fenster zu → beendet
    assert not (tmp_path / "laeuft.json").exists()
    assert lfa.find_running(str(tmp_path)) is None


def test_stale_state_file_is_ignored(tmp_path):
    (tmp_path / "laeuft.json").write_text(json.dumps({"port": 1, "pid": 1, "version": __version__}))
    assert lfa.find_running(str(tmp_path)) is None


def test_install_bundle_replaces_old_version(tmp_path):
    src = tmp_path / "Downloads" / "Steckwerk.app"
    (src / "Contents").mkdir(parents=True)
    (src / "Contents" / "neu.txt").write_text("1.1")
    apps = tmp_path / "Applications"
    (apps / "Steckwerk.app" / "Contents").mkdir(parents=True)
    (apps / "Steckwerk.app" / "Contents" / "alt.txt").write_text("1.0")
    target = lfa.install_bundle(str(src), str(apps))
    assert target == str(apps / "Steckwerk.app")
    assert sorted(os.listdir(apps)) == ["Steckwerk.app"]
    assert os.listdir(os.path.join(target, "Contents")) == ["neu.txt"]


def test_maybe_install_flow(tmp_path, monkeypatch):
    monkeypatch.setattr(lfa, "MAC", True)
    monkeypatch.setattr(lfa, "data_dir", lambda: str(tmp_path))
    monkeypatch.setattr(lfa, "notify", lambda text: None)
    bundle = tmp_path / "Downloads" / "Steckwerk.app"
    bundle.mkdir(parents=True)
    answers, installed, launched = ["Nur starten"], [], []
    monkeypatch.setattr(lfa, "dialog", lambda *a, **k: answers.pop(0))
    monkeypatch.setattr(lfa, "install_bundle", lambda b, d: installed.append((b, d)) or d + "/Steckwerk.app")
    monkeypatch.setattr(lfa.subprocess, "Popen", lambda args: launched.append(args))
    assert lfa.maybe_install(str(bundle)) is False                  # „Nur starten“ …
    assert lfa.maybe_install(str(bundle)) is False                  # … wird gemerkt, keine zweite Frage
    assert not installed
    os.remove(lfa.settings_path(str(tmp_path)))
    answers.append("Installieren")
    assert lfa.maybe_install(str(bundle)) is True
    assert installed and launched == [["open", installed[0][1] + "/Steckwerk.app"]]
    assert lfa.maybe_install(None) is False


def test_maybe_install_replaces_older_version(tmp_path, monkeypatch):
    monkeypatch.setattr(lfa, "MAC", True)
    monkeypatch.setattr(lfa, "data_dir", lambda: str(tmp_path))
    monkeypatch.setattr(lfa, "notify", lambda text: None)
    apps = tmp_path / "Programme"
    (apps / "Steckwerk.app" / "Contents").mkdir(parents=True)
    import plistlib
    with open(apps / "Steckwerk.app" / "Contents" / "Info.plist", "wb") as fh:
        plistlib.dump({"CFBundleShortVersionString": "1.1.0"}, fh)
    monkeypatch.setattr(lfa, "app_dirs", lambda: [str(apps)])
    assert lfa.installed_version() == (str(apps), "1.1.0")
    _write = lfa._write_json
    lfa._write_json(lfa.settings_path(str(tmp_path)), {"install_abgelehnt": True})   # früher abgelehnt
    bundle = tmp_path / "Downloads" / "Steckwerk.app"
    bundle.mkdir(parents=True)
    texts, answers, installed = [], ["Nur starten", "Ersetzen"], []
    monkeypatch.setattr(lfa, "dialog", lambda text, *a, **k: texts.append(text) or answers.pop(0))
    monkeypatch.setattr(lfa, "install_bundle", lambda b, d: installed.append(d) or d + "/Steckwerk.app")
    monkeypatch.setattr(lfa.subprocess, "Popen", lambda args: None)
    assert lfa.maybe_install(str(bundle)) is False and "1.1.0" in texts[0]     # Update trotzdem angeboten
    assert lfa.maybe_install(str(bundle)) is False and len(texts) == 1         # pro Version nur einmal
    s = lfa._read_json(lfa.settings_path(str(tmp_path)))
    s.pop("update_abgelehnt")
    _write(lfa.settings_path(str(tmp_path)), s)
    assert lfa.maybe_install(str(bundle)) is True and installed == [str(apps)]


def test_self_test(capsys):
    assert lfa.self_test() == 0
    assert f"Steckwerk {__version__} OK" in capsys.readouterr().out


# ---------------------------------------------------------------------- Mac-Paket
def test_build_macos_bundle_and_zip(tmp_path):
    assert build_macos.main(["--out", str(tmp_path)]) == 0
    app = tmp_path / "Steckwerk.app" / "Contents"
    info = plistlib.loads((app / "Info.plist").read_bytes())
    assert info["CFBundleExecutable"] == "Steckwerk" and info["CFBundleShortVersionString"] == __version__
    assert info["LSUIElement"] is True
    assert (app / "Resources" / "Steckwerk.icns").read_bytes()[:4] == b"icns"
    assert (app / "Resources" / "steckwerk" / "models" / "fahrzeug.py").exists()
    assert not list((app / "Resources" / "steckwerk").glob("tests"))
    z = zipfile.ZipFile(tmp_path / f"Steckwerk-{__version__}-macOS.zip")
    exe = z.getinfo(f"Steckwerk-{__version__}-macOS/Steckwerk.app/Contents/MacOS/Steckwerk")
    assert exe.create_system == 3 and stat.S_IMODE(exe.external_attr >> 16) == 0o755
    assert f"Steckwerk-{__version__}-macOS/LIES MICH.txt" in z.namelist()
    names = z.namelist()
    assert all(not n.endswith(".pyc") and "__pycache__" not in n for n in names)


@pytest.mark.skipif(shutil.which("sh") is None, reason="braucht sh")
def test_launcher_script(tmp_path):
    """Das Mac-Startskript unter sh: Selbsttest mit gefundenem Python, Hinweis ohne Python."""
    build_macos.build_app(str(tmp_path))
    script = str(tmp_path / "Steckwerk.app" / "Contents" / "MacOS" / "Steckwerk")
    home = tmp_path / "home"
    home.mkdir()
    env = dict(os.environ, HOME=str(home), STECKWERK_PYTHON=sys.executable, STECKWERK_SELFTEST="1")
    r = subprocess.run(["sh", script], env=env, capture_output=True, text=True, timeout=120)
    assert r.returncode == 0 and f"Steckwerk {__version__} OK" in r.stdout, r.stderr
    # ohne Python: Dialog (osascript) und Angebot, die Command Line Tools zu installieren
    stub = tmp_path / "stub"
    stub.mkdir()
    log = tmp_path / "stub.log"
    for name, body in (("xcode-select", 'echo "xcode-select $*" >> "$STUBLOG"; [ "$1" = "-p" ] && exit 2; exit 0'),
                       ("osascript", 'echo "osascript" >> "$STUBLOG"; echo "button returned:Installieren"')):
        (stub / name).write_text("#!/bin/sh\n" + body + "\n")
        (stub / name).chmod(0o755)
    env = dict(os.environ, HOME=str(home), STECKWERK_PYTHON="", STUBLOG=str(log), PATH=f"{stub}:/usr/bin:/bin")
    for cand in ("/opt/homebrew/bin/python3", "/usr/local/bin/python3",
                 "/Library/Frameworks/Python.framework/Versions/Current/bin/python3", "/opt/local/bin/python3"):
        if os.path.exists(cand):
            pytest.skip("auf diesem Rechner liegt ein Python an einem Mac-Standardort")
    r = subprocess.run(["sh", script], env=env, capture_output=True, text=True, timeout=60)
    assert r.returncode == 1
    assert log.read_text().splitlines() == ["xcode-select -p", "osascript", "xcode-select --install"]
    assert "kein Python" in (home / "Library" / "Logs" / "Steckwerk.log").read_text()


def test_instance_without_files_is_restarted(tmp_path, monkeypatch):
    """Hat macOS die temporäre App-Kopie entfernt, wird die verwaiste Instanz beendet statt benutzt."""
    monkeypatch.setattr(lfa, "open_url", lambda url: None)
    ready = threading.Event()
    t = threading.Thread(target=lfa.run, kwargs=dict(port=0, out_dir=str(tmp_path / "out"), browser=False,
                                                     base=str(tmp_path), ready=ready), daemon=True)
    t.start()
    assert ready.wait(10)
    assert lfa.find_running(str(tmp_path)) == ready.port
    monkeypatch.setattr(lfa.webui, "INDEX", str(tmp_path / "weg" / "index.html"))
    assert lfa.find_running(str(tmp_path)) is None
    t.join(10)
    assert not t.is_alive()


def test_translocated_app_offers_install_again(tmp_path, monkeypatch):
    monkeypatch.setattr(lfa, "MAC", True)
    monkeypatch.setattr(lfa, "data_dir", lambda: str(tmp_path))
    monkeypatch.setattr(lfa, "app_dirs", lambda: [str(tmp_path / "Programme")])
    lfa._write_json(lfa.settings_path(str(tmp_path)), {"install_abgelehnt": True})
    texts = []
    monkeypatch.setattr(lfa, "dialog", lambda text, *a, **k: texts.append(text) or "Nur starten")
    normal = tmp_path / "Downloads" / "Steckwerk.app"
    moved = tmp_path / "AppTranslocation" / "ABC" / "d" / "Steckwerk.app"
    for b in (normal, moved):
        b.mkdir(parents=True)
    assert lfa.maybe_install(str(normal)) is False and texts == []
    assert lfa.maybe_install(str(moved)) is False and len(texts) == 1


def test_launcher_runs_in_foreground_when_translocated(tmp_path):
    root = tmp_path / "AppTranslocation" / "ABC" / "d"
    build_macos.build_app(str(root))
    script = str(root / "Steckwerk.app" / "Contents" / "MacOS" / "Steckwerk")
    home = tmp_path / "home"
    home.mkdir()
    env = dict(os.environ, HOME=str(home), STECKWERK_PYTHON=sys.executable)
    r = subprocess.run(["sh", script, "--self-test"], env=env, capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr
    # im Vordergrund: Python ist fertig, wenn das Skript endet
    assert f"Steckwerk {__version__} OK" in (home / "Library" / "Logs" / "Steckwerk.log").read_text()


def test_bundle_has_every_module():
    sys.path.insert(0, os.path.join(ROOT, "packaging"))
    import build_macos
    files = set(build_macos.code_files())
    missing = [f for f in os.listdir(ROOT) if f.endswith(".py") and f not in files]
    assert not missing, missing
