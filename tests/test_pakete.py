"""Erweiterungspakete: anlegen, prüfen, packen, installieren, laden, entfernen."""
import base64
import json
import os
import zipfile

import pytest

import pakete
import service
from cli import run
from laserforge import Config
from conftest import assert_cut_ready

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture
def paketordner(tmp_path, monkeypatch):
    inst = tmp_path / "inst"
    monkeypatch.setenv("LASERFORGE_PAKETE", str(inst))
    yield tmp_path
    monkeypatch.delenv("LASERFORGE_PAKETE")
    service.reload_pakete()


def test_create_pack_install_use_remove(paketordner):
    folder = pakete.create("testschild", str(paketordner), name="Testschild")
    path, lines = pakete.pack(folder, str(paketordner))
    assert path.endswith("testschild-1.0.0.lfpaket") and "cut-ready" in lines[0]
    m, _ = pakete.install(path)
    assert m["id"] == "testschild"
    service.reload_pakete()
    assert service.MODEL_INFO["testschild"]["paket"]["version"] == "1.0.0"
    cfg = Config()
    asms = service.build_assemblies("testschild", {"text": "Anna", "rahmen": "oval"}, cfg)
    assert_cut_ready(asms[0], cfg)
    assert any(p["id"] == "testschild" for p in service.schema()["pakete"])
    pakete.remove("testschild")
    service.reload_pakete()
    assert "testschild" not in service.MODEL_INFO


def test_example_package_installs(paketordner):
    m, _ = pakete.install(os.path.join(HERE, "beispiel-pakete", "tuerschild-1.0.0.lfpaket"))
    assert m["name"] == "Türschild"


def test_cli_commands(paketordner, capsys):
    out = str(paketordner)
    assert run(["--paket-neu", "cli_schild", "--out", out]) == 0
    assert run(["--paket-packen", os.path.join(out, "cli_schild"), "--out", out]) == 0
    assert run(["--paket-installieren", os.path.join(out, "cli_schild-1.0.0.lfpaket")]) == 0
    assert run(["--pakete"]) == 0
    assert "cli_schild" in capsys.readouterr().out
    assert run(["--paket-entfernen", "cli_schild"]) == 0
    assert run(["--paket-entfernen", "cli_schild"]) == 2


def _zip(files):
    import io
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for n, t in files.items():
            zf.writestr(n, t)
    return buf.getvalue()


@pytest.mark.parametrize("files,msg", [
    ({"x/readme.txt": "?"}, "paket.json"),
    ({"x/paket.json": "{kaputt"}, "JSON"),
    ({"x/paket.json": json.dumps(dict(id="Bad Id", name="a", version="1.0.0", modelle=["a"]))}, "Paket-id"),
    ({"x/paket.json": json.dumps(dict(id="ok", name="a", version="1.0.0", modelle=["fehlt"]))}, "fehlt"),
    ({"x/paket.json": json.dumps(dict(id="ok", name="a", version="1.0.0", modelle=["mm"], laserforge="99.0.0"))},
     "braucht"),
    ({"x/paket.json": json.dumps(dict(id="ok", name="a", version="1.0.0", modelle=["mm"])), "x/mm.py": "x = 1"},
     "build"),
    ({"x/paket.json": json.dumps(dict(id="ok", name="a", version="1.0.0", modelle=["mm"])),
      "x/mm.py": "INFO = dict(params=[])\ndef build(cfg):\n    raise ValueError('kaputt')"}, "Standardwerten"),
    ({"../boese/paket.json": "{}"}, "Unzulässiger"),
])
def test_bad_packages_are_rejected(paketordner, files, msg):
    with pytest.raises(pakete.PaketFehler, match=msg):
        pakete.install(data=_zip(files))
    assert not os.path.exists(os.path.join(str(paketordner), "inst", "ok"))


def test_webui_install(paketordner):
    import threading
    import urllib.request
    import webui
    srv = webui.make_server("127.0.0.1", 0, str(paketordner / "out"), quiet=True)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        url = f"http://127.0.0.1:{srv.server_address[1]}"
        with open(os.path.join(HERE, "beispiel-pakete", "tuerschild-1.0.0.lfpaket"), "rb") as fh:
            body = json.dumps({"data": base64.b64encode(fh.read()).decode()}).encode()
        req = urllib.request.Request(url + "/api/paket-installieren", body,
                                     {"Content-Type": "application/json", "X-Laserforge": "1"})
        d = json.loads(urllib.request.urlopen(req).read())
        assert d["ok"] and "tuerschild" in d["schema"]["models"]
    finally:
        srv.shutdown()
        srv.server_close()
