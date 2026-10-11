"""Assistent (Werte vom Sprachmodell) und Bild-Werkstatt – gegen ein simuliertes Ollama/OpenRouter."""
import base64
import json
import struct
import threading
import urllib.request
import zlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

import assistent
import bildgen
import service
import webui


def _png(w=64, h=64):
    rows = b""
    for y in range(h):
        row = bytearray([0])
        for x in range(w):
            v = 0 if (x - w / 2) ** 2 + (y - h / 2) ** 2 < (w * 0.35) ** 2 else 255
            row += bytes([v, v, v])
        rows += bytes(row)

    def ch(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    return (b"\x89PNG\r\n\x1a\n" + ch(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + ch(b"IDAT", zlib.compress(rows)) + ch(b"IEND", b""))


SVG = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><path d="M5 0L10 10H0Z"/></svg>'


class Fake(BaseHTTPRequestHandler):
    antwort = {}
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

    def do_GET(self):
        if self.path == "/api/tags":
            return self._j({"models": [{"name": "qwen2.5:3b"}, {"name": "x/z-image-turbo:latest"}]})
        if self.path.startswith("/models"):
            return self._j({"data": [
                {"id": "krea/krea-2-medium", "name": "Krea 2", "architecture": {"output_modalities": ["image"]},
                 "pricing": {"prompt": "0", "image_output": "0.000007"}},
                {"id": "black-forest-labs/flux.2-klein-4b", "name": "FLUX.2 Klein",
                 "architecture": {"output_modalities": ["image"]},
                 "pricing": {"prompt": "0", "completion": "0", "image_output": "0.00000341796875"}},
                {"id": "openai/gpt-4o", "architecture": {"output_modalities": ["text"]}, "pricing": {}}]})
        self._j({"error": "nicht da"}, 404)

    def do_POST(self):
        req = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
        Fake.last = (self.path, req, self.headers.get("Authorization"))
        if self.path == "/api/chat":
            if req["model"] == "fehlt":
                return self._j({"error": "model 'fehlt' not found"}, 404)
            return self._j({"message": {"role": "assistant", "content": json.dumps(Fake.antwort)}, "done": True})
        if self.path == "/api/generate":
            if req["model"].startswith("qwen"):
                return self._j({"response": "Hallo", "done": True})
            return self._j({"image": base64.b64encode(_png()).decode(), "done": True})
        if self.path == "/images":
            if self.headers.get("Authorization") != "Bearer sk-or-test":
                return self._j({"error": {"message": "bad key"}}, 401)
            data, typ = (SVG, "image/svg+xml") if "vector" in req["model"] else (_png(), "image/png")
            return self._j({"data": [{"b64_json": base64.b64encode(data).decode(), "media_type": typ}],
                            "usage": {"cost": 0.0123}})
        self._j({"error": "nicht da"}, 404)


@pytest.fixture
def fake(tmp_path, monkeypatch):
    monkeypatch.setenv("STECKWERK_DATEN", str(tmp_path / "daten"))
    monkeypatch.setenv("STECKWERK_MOTIVE", str(tmp_path / "mot"))
    srv = ThreadingHTTPServer(("127.0.0.1", 0), Fake)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    url = "http://127.0.0.1:%d" % srv.server_address[1]
    monkeypatch.setattr(bildgen, "OPENROUTER", url)
    bildgen._cache.clear()
    assistent.save_settings(an=True, url=url, modell="qwen2.5:3b")
    yield url
    srv.shutdown()


# --- Assistent ------------------------------------------------------------------------------------

@pytest.mark.parametrize("url", ["http://127.0.0.1:11434", "http://localhost:11434", "http://192.168.1.5:11434",
                                 "http://mac-mini.local:11434", "http://[::1]:11434", "http://10.0.0.2"])
def test_url_lokal_erlaubt(url):
    assert assistent.check_url(url + "/") == url


@pytest.mark.parametrize("url", ["https://api.example.com", "http://8.8.8.8:11434", "ftp://127.0.0.1", "127.0.0.1:11434"])
def test_url_fremd_abgelehnt(url):
    with pytest.raises(assistent.AssistentFehler):
        assistent.check_url(url)


def test_status_und_einstellungen(fake):
    st = assistent.status()
    assert st["ok"] and "qwen2.5:3b" in st["modelle"] and st["vorhanden"]
    assert assistent.settings()["an"] is True
    with pytest.raises(assistent.AssistentFehler):
        assistent.save_settings(modell="zwei worte")


def test_vorschlag_prueft_werte(fake):
    model = service.MODEL_INFO["wichtelhaus"]
    num = next(p for p in model["params"] if p["type"] == "number")
    sel = next(p for p in model["params"] if p["type"] == "select")
    opt = sel["options"][-1]
    Fake.antwort = {"werte": {num["key"]: num["max"] * 10, sel["key"]: opt["label"], "erfunden": 3},
                    "hinweis": "Größer gemacht"}
    d = assistent.vorschlag(model, "bitte riesig")
    assert d["werte"][num["key"]] == num["max"]                      # eingegrenzt
    assert d["werte"][sel["key"]] == opt["value"]                    # Anzeigename → Wert
    assert "erfunden" not in d["werte"] and d["hinweis"] == "Größer gemacht"
    path, req, _ = Fake.last
    assert path == "/api/chat" and req["format"]["properties"]["werte"]["properties"][num["key"]]["maximum"] == num["max"]


def test_vorschlag_fehler(fake):
    model = service.MODEL_INFO["wichtelhaus"]
    with pytest.raises(assistent.AssistentFehler, match="Beschreibe"):
        assistent.vorschlag(model, "  ")
    with pytest.raises(assistent.AssistentFehler, match="ollama pull"):
        assistent.vorschlag(model, "x", modell="fehlt")
    Fake.antwort = "kein json"
    with pytest.raises(assistent.AssistentFehler, match="Bauplan"):
        assistent.vorschlag(model, "x")


def test_ollama_nicht_erreichbar(tmp_path, monkeypatch):
    monkeypatch.setenv("STECKWERK_DATEN", str(tmp_path))
    with pytest.raises(assistent.AssistentFehler, match="nicht erreichbar"):
        assistent.status("http://127.0.0.1:9")


# --- Bilder ---------------------------------------------------------------------------------------

def test_kosten_schaetzen():
    assert bildgen.schaetzen({"prompt": "0", "completion": "0", "image_output": "0.00000341796875"}) == 0.014
    assert 0.035 < bildgen.schaetzen({"prompt": "0.0000003", "completion": "0.0000025", "image_output": "0.00003"}) < 0.045
    assert bildgen.schaetzen({}) == 0.0


def test_prompt_und_grenzen():
    p = bildgen.prompt("Eule auf einem Ast", "scherenschnitt")
    assert p.startswith("Motif: Eule auf einem Ast.") and "paper-cut" in p and "no text" in p
    with pytest.raises(bildgen.BildFehler):
        bildgen.prompt(" ")
    with pytest.raises(bildgen.BildFehler):
        bildgen.prompt("x" * 700)


def test_ollama_bild(fake):
    assert bildgen.ollama_modelle() == ["x/z-image-turbo:latest"]
    d = bildgen.erzeugen("Eule", quelle="ollama")
    assert d["ok"] and d["typ"] == "image/png" and d["kosten"] == 0
    assert base64.b64decode(d["bild"])[:4] == b"\x89PNG"
    with pytest.raises(bildgen.BildFehler, match="Sprachmodell"):
        bildgen.erzeugen("Eule", quelle="ollama", modell="qwen2.5:3b")


def test_openrouter_schluessel_kosten_limit(fake):
    with pytest.raises(bildgen.BildFehler, match="Schlüssel"):
        bildgen.erzeugen("Hirsch", quelle="openrouter")
    s = bildgen.save_settings(key="sk-or-test", quelle="openrouter")
    assert s["key_gesetzt"] and "key" not in s and "sk-or-test" not in json.dumps(s)
    d = bildgen.erzeugen("Hirsch", modell="recraft/recraft-v4.1-vector")
    assert d["typ"] == "image/svg+xml" and d["kosten"] == 0.0123 and d["monat"] == {"kosten": 0.0123, "bilder": 1}
    assert Fake.last[2] == "Bearer sk-or-test" and Fake.last[1]["model"] == "recraft/recraft-v4.1-vector"
    bildgen.save_settings(limit=0.01)
    with pytest.raises(bildgen.BildFehler, match="Monatslimit"):
        bildgen.erzeugen("Hirsch")
    bildgen.save_settings(limit=0, key="sk-or-falsch")
    with pytest.raises(bildgen.BildFehler, match="lehnt den Schlüssel ab"):
        bildgen.erzeugen("Hirsch")


def test_openrouter_modellliste(fake):
    ms = bildgen.openrouter_modelle()
    assert [m["id"] for m in ms] == ["black-forest-labs/flux.2-klein-4b", "krea/krea-2-medium"]   # Empfehlung zuerst
    assert ms[0]["empfohlen"] and ms[0]["kosten"] == 0.014 and not ms[1]["empfohlen"]


# --- Webserver ------------------------------------------------------------------------------------

def _post(base, path, obj):
    req = urllib.request.Request(base + path, json.dumps(obj).encode(),
                                 {"Content-Type": "application/json", "X-Steckwerk": "1"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


@pytest.fixture
def server(fake, tmp_path):
    srv = webui.make_server("127.0.0.1", 0, str(tmp_path / "out"), quiet=True)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield "http://127.0.0.1:%d" % srv.server_address[1], srv
    srv.shutdown()


def test_webui_routen(server):
    base, srv = server
    with urllib.request.urlopen(base + "/api/schema") as r:
        sch = json.loads(r.read())
    assert sch["assistent"]["an"] and sch["assistent"]["bilder"]["quelle"] == "ollama"
    Fake.antwort = {"werte": {}, "hinweis": "nichts"}
    code, d = _post(base, "/api/assistent", {"model": "wichtelhaus", "beschreibung": "klein"})
    assert code == 200 and d["ok"]
    code, d = _post(base, "/api/assistent", {"model": "gibtsnicht", "beschreibung": "x"})
    assert code == 400
    code, d = _post(base, "/api/bild", {"beschreibung": "Eule", "stil": "silhouette"})
    assert d["ok"] and d["typ"] == "image/png"
    code, d = _post(base, "/api/bild-einstellungen", {"key": "sk-or-test", "openrouter_modell": "recraft/recraft-v4.1"})
    assert d["ok"] and d["bilder"]["key_gesetzt"] and "sk-or" not in json.dumps(d)
    code, d = _post(base, "/api/bild-modelle", {"quelle": "openrouter"})
    assert d["ok"] and d["modelle"][0]["id"] == "black-forest-labs/flux.2-klein-4b"
    srv.RequestHandlerClass.lan = True
    try:
        code, d = _post(base, "/api/bild-einstellungen", {"quelle": "openrouter"})
        assert code == 403
        code, d = _post(base, "/api/bild", {"beschreibung": "Eule", "quelle": "openrouter"})
        assert code == 403
    finally:
        srv.RequestHandlerClass.lan = False
