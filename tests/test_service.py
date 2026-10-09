"""Steuerschicht, Terminal-Konfigurator und Weboberfläche (HTTP-API)."""
import io
import json
import threading
import urllib.error
import urllib.request
import zipfile

import pytest

import service
from cli import konfigurator, run


def test_schema_is_json_and_complete():
    s = json.loads(json.dumps(service.schema()))
    assert {"wichtelhaus", "ornament", "schneeflocke", "fahrzeug", "alle"} <= set(s["models"])
    for m in s["models"].values():
        assert m["group"] in s["groups"]
        for p in m["params"]:
            assert p["type"] in ("number", "int", "select", "text", "bool")
            if p["type"] == "select":
                assert p["default"] in [o["value"] for o in p["options"]]


def test_coerce_messages():
    info = service.MODEL_INFO["wichtelhaus"]["params"][0]
    assert service.coerce(info, "80,5") == 80.5
    with pytest.raises(ValueError, match="keine Zahl"):
        service.coerce(info, "abc")
    with pytest.raises(ValueError, match="außerhalb"):
        service.coerce(info, 9999)
    with pytest.raises(ValueError):
        service.clean_params("ornament", {"shape": "raute"})


@pytest.mark.parametrize("model", [m for m in service.MODEL_INFO if m != "alle"])
def test_generate_defaults_every_model(model):
    req = {"model": model, "params": {p["key"]: p["default"] for p in service.MODEL_INFO[model]["params"]}}
    d = service.generate(req)
    assert d["ok"], d.get("error") or [a["errors"] for a in d["assemblies"]]
    for a in d["assemblies"]:
        assert a["sheets"] and all(sh["svg"].startswith("<?xml") and sh["checked"] for sh in a["sheets"])


def test_generate_reports_errors_without_files():
    d = service.generate({"model": "wichtelhaus", "config": {"sheet_width": 60, "sheet_height": 60}})
    assert not d["ok"] and d["assemblies"][0]["errors"]
    assert all(not sh["checked"] for a in d["assemblies"] for sh in a["sheets"])
    d = service.generate({"model": "ornament", "params": {"text": "Viel zu langer Text für einen Stern",
                                                         "size": 40}})
    assert not d["ok"] and "Schrifthöhe" in d["error"]


def test_zip_contains_svgs_and_reports(cfg):
    res, _ = service.process(service.build_assemblies("zubehoer", {}, cfg), cfg)
    names = zipfile.ZipFile(io.BytesIO(service.zip_results(res, cfg))).namelist()
    assert "tannenbaum/tannenbaum.svg" in names and "zaun/pruefbericht.txt" in names


def test_konfigurator_scripted(tmp_path):
    # Steckfahrzeug, Fahrzeug 3 = Lok, Rest Standard, Text "Polar"
    nr = str([k for k in service.MODEL_INFO if k != "alle"].index("fahrzeug") + 1)
    answers = iter([nr, "3", "", "", "", "Polar", "", "", "", "", "", str(tmp_path), "n"])
    lines = []
    args = konfigurator(lambda _: next(answers), lines.append)
    assert args[:2] == ["--model", "fahrzeug"] and "--vehicle" in args and "lok" in args
    assert "--length" in args and "150.0" in args and "--text" in args
    assert any("python cli.py" in ln for ln in lines)
    answers = iter([nr, "3", "", "", "", "Polar", "", "", "", "", "", str(tmp_path), "n"])
    assert run(["--konfigurator"], inp=lambda _: next(answers)) == 0
    assert (tmp_path / "lok" / "lok.svg").exists()


@pytest.fixture
def server(tmp_path):
    import webui
    srv = webui.make_server("127.0.0.1", 0, str(tmp_path / "out"), quiet=True)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{srv.server_address[1]}", tmp_path / "out"
    srv.shutdown()
    srv.server_close()


def _post(url, obj):
    req = urllib.request.Request(url, json.dumps(obj).encode(),
                                 {"Content-Type": "application/json", "X-Laserforge": "1"})
    return urllib.request.urlopen(req, timeout=60)


def test_webui_endpoints(server):
    base, out = server
    html = urllib.request.urlopen(base + "/", timeout=10).read().decode()
    assert "<title>Laserforge Werkbank</title>" in html
    schema = json.load(urllib.request.urlopen(base + "/api/schema", timeout=10))
    assert schema["mode"] == "server" and "fahrzeug" in schema["models"]
    d = json.load(_post(base + "/api/generate", {"model": "schneeflocke", "params": {"count": 2}}))
    assert d["ok"] and len(d["assemblies"][0]["sheets"]) == 1
    r = _post(base + "/api/zip", {"model": "fahrzeug", "params": {"vehicle": "schlitten"}})
    assert r.headers["Content-Type"] == "application/zip"
    assert "schlitten/schlitten.svg" in zipfile.ZipFile(io.BytesIO(r.read())).namelist()
    d = json.load(_post(base + "/api/save", {"model": "zaun"}))
    assert d["ok"] and (out / "zaun" / "zaun.svg").exists()


def test_webui_rejects_bad_requests(server):
    base, out = server
    with pytest.raises(urllib.error.HTTPError) as e:
        _post(base + "/api/zip", {"model": "wichtelhaus", "config": {"sheet_width": 60, "sheet_height": 60}})
    assert e.value.code == 400
    with pytest.raises(urllib.error.HTTPError) as e:
        urllib.request.urlopen(base + "/gibtsnicht", timeout=10)
    assert e.value.code == 404
    with pytest.raises(urllib.error.HTTPError) as e:
        _post(base + "/api/save", {"model": "wichtelhaus", "config": {"kerf": 5}})
    assert e.value.code == 400
    assert not out.exists()
