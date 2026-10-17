"""Tests für Steckwerk Desktop: Bildquelle „chatgpt“ in bildgen und das Startskript packaging/swift/bridge_start.py."""
import base64
import json
import os
import subprocess
import sys
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

import bildgen
import webui

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRIDGE = os.path.join(ROOT, "packaging", "swift", "bridge_start.py")
PNG = b"\x89PNG\r\n\x1a\n" + b"\0" * 32


class FakeOpenAI(BaseHTTPRequestHandler):
    last = None

    def log_message(self, *a):
        pass

    def _j(self, obj, code=200):
        b = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_POST(self):
        req = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
        FakeOpenAI.last = (self.path, req, self.headers.get("Authorization"))
        if self.path != "/v1/images/generations":
            return self._j({"error": {"message": "nicht da"}}, 404)
        if self.headers.get("Authorization") != "Bearer test-chatgpt":
            return self._j({"error": {"message": "Incorrect API key"}}, 401)
        if req.get("prompt", "").startswith("Motif: leer"):
            return self._j({"data": []})
        return self._j({"data": [{"b64_json": base64.b64encode(PNG).decode()}]})


@pytest.fixture
def openai(tmp_path, monkeypatch):
    monkeypatch.setenv("STECKWERK_DATEN", str(tmp_path / "daten"))
    srv = ThreadingHTTPServer(("127.0.0.1", 0), FakeOpenAI)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    monkeypatch.setattr(bildgen, "OPENAI", "http://127.0.0.1:%d/v1" % srv.server_address[1])
    FakeOpenAI.last = None
    yield
    srv.shutdown()


# --- bildgen: ChatGPT ------------------------------------------------------------------------------

def test_chatgpt_braucht_eigenen_schluessel(openai):
    bildgen.save_settings(quelle="openrouter", key="test-openrouter")
    with pytest.raises(bildgen.BildFehler, match="ChatGPT fehlt noch der Schlüssel"):
        bildgen.erzeugen("Reh", quelle="chatgpt")
    assert FakeOpenAI.last is None


def test_chatgpt_bild_und_anfrage(openai):
    s = bildgen.save_settings(quelle="chatgpt", key="test-chatgpt")
    assert s["quelle"] == "chatgpt" and s["chatgpt_modell"] == "gpt-image-1"
    assert s["keys"] == {"openrouter": False, "chatgpt": True}
    assert "test-chatgpt" not in json.dumps(s)
    d = bildgen.erzeugen("Reh im Sprung")
    assert d["ok"] and d["quelle"] == "chatgpt" and d["typ"] == "image/png"
    assert base64.b64decode(d["bild"]) == PNG
    path, req, auth = FakeOpenAI.last
    assert path == "/v1/images/generations" and auth == "Bearer test-chatgpt"
    assert req["model"] == "gpt-image-1" and req["n"] == 1 and req["response_format"] == "b64_json"
    assert "Reh im Sprung" in req["prompt"]
    assert d["monat"]["bilder"] == 1


def test_chatgpt_fehler_auf_deutsch(openai):
    bildgen.save_settings(quelle="chatgpt", key="test-falsch")
    with pytest.raises(bildgen.BildFehler, match="OpenAI lehnt den Schlüssel ab"):
        bildgen.erzeugen("Reh")
    bildgen.save_settings(key="test-chatgpt")
    with pytest.raises(bildgen.BildFehler, match="OpenAI hat kein Bild geliefert"):
        bildgen.erzeugen("leer")


def test_chatgpt_monatslimit(openai):
    bildgen.save_settings(quelle="chatgpt", key="test-chatgpt", limit=0.5)
    data = bildgen._read()
    data["kosten"] = {bildgen._monat(): {"kosten": 0.5, "bilder": 3}}
    bildgen._write(data)
    with pytest.raises(bildgen.BildFehler, match="Monatslimit"):
        bildgen.erzeugen("Reh")
    assert FakeOpenAI.last is None


def test_schluessel_getrennt_und_ungueltige_abgelehnt(openai):
    bildgen.save_settings(quelle="openrouter", key="test-openrouter")
    bildgen.save_settings(quelle="chatgpt", key="test-chatgpt")
    assert bildgen.get_key("openrouter") == "test-openrouter"
    assert bildgen.get_key("chatgpt") == "test-chatgpt"
    with pytest.raises(bildgen.BildFehler, match="sieht nicht richtig aus"):
        bildgen.save_settings(quelle="chatgpt", key="mit leerzeichen")
    assert bildgen.get_key("chatgpt") == "test-chatgpt"
    with pytest.raises(bildgen.BildFehler, match="Quelle unbekannt"):
        bildgen.save_settings(quelle="dalle")


def test_webui_reicht_chatgpt_modell_durch(openai, tmp_path):
    srv = webui.make_server("127.0.0.1", 0, str(tmp_path / "out"), quiet=True)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        body = json.dumps({"quelle": "chatgpt", "chatgpt_modell": "gpt-image-1-mini", "key": "test-chatgpt"}).encode()
        req = urllib.request.Request("http://127.0.0.1:%d/api/bild-einstellungen" % srv.server_address[1], body,
                                     {"Content-Type": "application/json", "X-Steckwerk": "1"})
        d = json.loads(urllib.request.urlopen(req, timeout=10).read())
        assert d["ok"] and d["bilder"]["chatgpt_modell"] == "gpt-image-1-mini"
        assert d["bilder"]["keys"]["chatgpt"] is True
        assert "test-chatgpt" not in json.dumps(d)
    finally:
        srv.shutdown()
        srv.server_close()


# --- bridge_start.py --------------------------------------------------------------------------------

def _env(tmp_path):
    env = dict(os.environ)
    env.update(HOME=str(tmp_path / "home"), XDG_STATE_HOME=str(tmp_path / "state"),
               STECKWERK_DATEN=str(tmp_path / "daten"), PYTHONDONTWRITEBYTECODE="1")
    os.makedirs(env["HOME"], exist_ok=True)
    return env


def _start(tmp_path, *extra):
    p = subprocess.Popen([sys.executable, "-u", BRIDGE, "--root", ROOT, "--out", str(tmp_path / "out"), *extra],
                         stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=_env(tmp_path))
    line = p.stdout.readline().decode().strip()
    assert line.startswith("STECKWERK_PORT="), (line, p.stderr.read().decode() if p.poll() is not None else "")
    return p, line


def _post(port, path, body=None):
    req = urllib.request.Request("http://127.0.0.1:%d%s" % (port, path), json.dumps(body or {}).encode(),
                                 {"Content-Type": "application/json", "X-Steckwerk": "1"})
    return json.loads(urllib.request.urlopen(req, timeout=10).read())


def _wait(p, seconds):
    end = time.monotonic() + seconds
    while p.poll() is None and time.monotonic() < end:
        time.sleep(0.05)
    return p.poll()


def test_bridge_meldet_port_und_laeuft_im_app_modus(tmp_path):
    p, line = _start(tmp_path, "--no-reuse")
    try:
        port = int(line.split("=", 1)[1])
        assert _post(port, "/api/ping", {"client": "test"})["app"] == "steckwerk"
        assert _post(port, "/api/open-folder")["ok"] is not None      # nur im App-Modus vorhanden
    finally:
        p.stdin.close()
        assert _wait(p, 5) == 0, "Engine muss enden, wenn stdin schließt"


def test_bridge_endet_bei_quit(tmp_path):
    p, line = _start(tmp_path, "--no-reuse")
    port = int(line.split("=", 1)[1])
    _post(port, "/api/quit")
    assert _wait(p, 5) == 0
    p.stdin.close()


def test_bridge_nutzt_laufende_instanz_mit(tmp_path):
    first, line = _start(tmp_path, "--no-reuse")
    try:
        port = int(line.split("=", 1)[1])
        sys.path.insert(0, ROOT)
        env = _env(tmp_path)
        script = ("import json, steckwerk_app; "
                  "json.dump({'port': %d}, open(steckwerk_app.running_path(), 'w'))" % port)
        subprocess.run([sys.executable, "-c", script], cwd=ROOT, env=env, check=True)
        second, line2 = _start(tmp_path)
        assert line2 == "STECKWERK_PORT=%d REUSED" % port
        assert _wait(second, 5) == 0
        second.stdin.close()
    finally:
        first.stdin.close()
        _wait(first, 5)


def test_bridge_fragt_keinen_rechnernamen_ab(monkeypatch, tmp_path):
    """Auf macOS hängt socket.getfqdn() für 127.0.0.1 teils viele Sekunden – der Start darf es nicht brauchen."""
    import http.server
    import importlib.util
    import socket

    spec = importlib.util.spec_from_file_location("bridge_start", BRIDGE)
    bridge = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bridge)
    monkeypatch.setattr(http.server.HTTPServer, "server_bind", http.server.HTTPServer.server_bind)

    def kein_dns(*a, **k):
        raise AssertionError("getfqdn darf beim Start nicht aufgerufen werden")

    monkeypatch.setattr(socket, "getfqdn", kein_dns)
    bridge._schneller_bind()
    srv = webui.make_server("127.0.0.1", 0, str(tmp_path / "out"), quiet=True)
    try:
        assert srv.server_name == "127.0.0.1" and srv.server_port == srv.server_address[1] > 0
    finally:
        srv.server_close()


def test_bridge_ohne_webui(tmp_path):
    r = subprocess.run([sys.executable, BRIDGE, "--root", str(tmp_path)], capture_output=True, text=True,
                       env=_env(tmp_path), timeout=30)
    assert r.returncode == 2 and "webui.py nicht gefunden" in r.stderr
