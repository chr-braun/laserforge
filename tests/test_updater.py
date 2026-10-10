"""Updater: Update-Kanal bauen, prüfen, Pakete und Mac-App aus dem Kanal installieren."""
import json
import os
import pathlib
import stat
import sys
import threading
import urllib.request
import zipfile

import pytest

import pakete
import service
import updater
from cli import run
from laserforge import __version__

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "packaging"))
import build_macos  # noqa: E402
import update_kanal  # noqa: E402


def _paket(tmp, pid, version, laserforge="1.5.0"):
    folder = pakete.create(pid, str(tmp / f"src-{version}"), name=pid.title())
    mf = os.path.join(folder, "paket.json")
    m = json.load(open(mf, encoding="utf-8"))
    m.update(version=version, laserforge=laserforge, beschreibung=f"{pid} in {version}")
    json.dump(m, open(mf, "w", encoding="utf-8"))
    path = str(tmp / f"{pid}-{version}.lfpaket")
    with zipfile.ZipFile(path, "w") as z:                  # von Hand packen: pack() prüft die Mindestversion
        for f in sorted(os.listdir(folder)):
            if f.endswith((".json", ".py")):
                z.write(os.path.join(folder, f), f"{pid}/{f}")
    return path


@pytest.fixture(scope="module")
def maczip(tmp_path_factory):
    out = tmp_path_factory.mktemp("mac")
    return build_macos.build_zip(str(out))


@pytest.fixture
def env(tmp_path, monkeypatch, maczip):
    monkeypatch.setenv("LASERFORGE_DATEN", str(tmp_path / "daten"))
    monkeypatch.setenv("LASERFORGE_PAKETE", str(tmp_path / "inst"))
    kanal = tmp_path / "kanal"
    update_kanal.build(str(kanal), maczip, [_paket(tmp_path, "spuk", "1.0.0"), _paket(tmp_path, "zukunft", "1.0.0", "9.0.0")],
                       today="2026-10-10")
    monkeypatch.setenv("LASERFORGE_UPDATE_KANAL", (kanal / "feed.json").as_uri())
    yield tmp_path
    monkeypatch.delenv("LASERFORGE_PAKETE")
    service.reload_pakete()


def test_kanal_feed(env, tmp_path):
    feed = json.loads((env / "kanal" / "feed.json").read_text())
    assert feed["standard"] == 1 and feed["programm"]["version"] == __version__
    assert feed["programm"]["mac"]["datei"] == f"Laserforge-{__version__}-macOS.zip"
    assert feed["programm"]["hinweise"], "Hinweise aus CHANGELOG fehlen"
    assert [p["id"] for p in feed["pakete"]] == ["spuk", "zukunft"]
    # neue Paketversion ersetzt die alte, die alte Datei verschwindet
    update_kanal.build(str(env / "kanal"), None, [_paket(tmp_path, "spuk", "1.2.0")])
    feed = json.loads((env / "kanal" / "feed.json").read_text())
    assert feed["pakete"][0]["version"] == "1.2.0"
    assert sorted(os.listdir(env / "kanal" / "pakete")) == ["spuk-1.2.0.lfpaket", "zukunft-1.0.0.lfpaket"]


def test_changelog_notes():
    notes = update_kanal.changelog_notes("1.6.0")
    assert any("Eigene Motive" in n for n in notes) and all("`" not in n for n in notes)
    assert update_kanal.changelog_notes("0.0.1") == []


def test_check_and_install_paket(env, tmp_path):
    d = updater.check()
    assert not d["programm"]["neu"] and not d["programm"]["kann_installieren"]
    st = {p["id"]: p["status"] for p in d["pakete"]}
    assert st == {"spuk": "neu", "zukunft": "zu_neu"}
    m = updater.install_paket("spuk")
    assert m["version"] == "1.0.0" and (tmp_path / "inst" / "spuk" / "paket.json").exists()
    assert {p["id"]: p["status"] for p in updater.check()["pakete"]}["spuk"] == "aktuell"
    update_kanal.build(str(env / "kanal"), None, [_paket(tmp_path, "spuk", "1.1.0")])
    d = updater.check()
    assert d["updates"] == 1 and d["pakete"][0]["status"] == "update" and d["pakete"][0]["installiert"] == "1.0.0"
    assert [m["version"] for m in updater.install_alle_pakete()] == ["1.1.0"]
    with pytest.raises(updater.UpdateFehler, match="braucht Laserforge 9.0.0"):
        updater.install_paket("zukunft")
    with pytest.raises(updater.UpdateFehler, match="gibt es im Update-Kanal nicht"):
        updater.install_paket("gibtsnicht")


def test_checksum_protects(env):
    f = env / "kanal" / "pakete" / "spuk-1.0.0.lfpaket"
    f.write_bytes(f.read_bytes() + b"x")
    with pytest.raises(updater.UpdateFehler, match="Prüfsumme"):
        updater.install_paket("spuk")
    assert not (env / "inst" / "spuk").exists()


def test_feed_errors(env, monkeypatch):
    feed = env / "kanal" / "feed.json"
    monkeypatch.setenv("LASERFORGE_UPDATE_KANAL", (env / "fehlt.json").as_uri())
    with pytest.raises(updater.UpdateFehler):
        updater.check()
    monkeypatch.setenv("LASERFORGE_UPDATE_KANAL", feed.as_uri())
    feed.write_text('{"standard": 7}')
    with pytest.raises(updater.UpdateFehler, match="neuere Laserforge"):
        updater.check()
    feed.write_text("kein json")
    with pytest.raises(updater.UpdateFehler, match="JSON"):
        updater.check()
    feed.write_text(json.dumps({"standard": 1, "pakete": [{"id": "x", "datei": "../../etc/passwd", "sha256": "0"}]}))
    with pytest.raises(updater.UpdateFehler, match="Unzulässiger Pfad"):
        updater.install_paket("x")


def test_program_update(env, tmp_path, monkeypatch):
    apps = tmp_path / "Programme"
    old = apps / "Laserforge.app" / "Contents"
    old.mkdir(parents=True)
    (old / "alt.txt").write_text("alt")
    bundle = str(apps / "Laserforge.app")
    monkeypatch.setattr(updater, "__version__", "1.0.0")
    d = updater.check(bundle)
    assert d["programm"]["neu"] and d["programm"]["kann_installieren"] and d["programm"]["hinweise"]
    assert not updater.check(None)["programm"]["kann_installieren"]
    assert "Downloads" in updater.program_installable("/private/var/folders/x/AppTranslocation/y/Laserforge.app")[1]
    target, version = updater.install_program(bundle)
    assert target == bundle and version == __version__
    assert updater.app_version(bundle) == __version__ and not (old / "alt.txt").exists()
    exe = pathlib.Path(bundle, "Contents", "MacOS", "Laserforge")
    assert exe.stat().st_mode & stat.S_IXUSR
    assert (pathlib.Path(bundle) / "Contents" / "Resources" / "laserforge" / "updater.py").exists()
    assert not [p for p in os.listdir(updater.data_dir()) if p.startswith("lfupdate_")]
    monkeypatch.setattr(updater, "__version__", __version__)
    with pytest.raises(updater.UpdateFehler, match="schon aktuell"):
        updater.install_program(bundle)


def test_program_update_wrong_version(env, tmp_path, monkeypatch):
    feed = env / "kanal" / "feed.json"
    f = json.loads(feed.read_text())
    f["programm"]["version"] = "99.0.0"
    feed.write_text(json.dumps(f))
    (tmp_path / "A" / "Laserforge.app").mkdir(parents=True)
    with pytest.raises(updater.UpdateFehler, match="enthält Version"):
        updater.install_program(str(tmp_path / "A" / "Laserforge.app"))


def test_settings_and_token(env, monkeypatch):
    s = updater.save_settings("https://example.org/kanal/feed.json", "geheim123", False)
    assert s["token_gesetzt"] and "geheim123" not in json.dumps(s) and s["auto"] is False
    path = os.path.join(updater.data_dir(), "update.json")
    assert stat.S_IMODE(os.stat(path).st_mode) == 0o600
    monkeypatch.delenv("LASERFORGE_UPDATE_KANAL")
    assert updater.kanal() == "https://example.org/kanal/feed.json"
    assert updater.save_settings("", "")["kanal"] == updater.KANAL and not updater.get_token()
    with pytest.raises(updater.UpdateFehler, match="https"):
        updater.save_settings("ftp://x")

    seen = []

    class R:
        def __init__(self, req, **kw):
            seen.append(req)

        def read(self, n):
            return b"{}"

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(updater.urllib.request, "urlopen", R)
    updater.set_token("tok")
    updater.fetch("https://raw.githubusercontent.com/a/b/updates/feed.json")
    updater.fetch("https://example.org/feed.json")
    assert seen[0].get_header("Authorization") == "token tok" and seen[1].get_header("Authorization") is None


def test_cli(env, capsys):
    assert run(["--update-pruefen"]) == 0
    out = capsys.readouterr().out
    assert "aktuell" in out and "spuk" in out and "braucht neuere" in out
    assert run(["--update-paket", "spuk"]) == 0 and "Installiert: Spuk 1.0.0" in capsys.readouterr().out
    assert run(["--update-paket", "zukunft"]) == 2
    assert run(["--update-schluessel", "abc"]) == 0 and "Schlüssel gespeichert" in capsys.readouterr().out
    assert run(["--update-schluessel", "-"]) == 0 and "Schlüssel keiner" in capsys.readouterr().out


def _post(base, path, obj):
    req = urllib.request.Request(base + path, json.dumps(obj).encode(),
                                 {"Content-Type": "application/json", "X-Laserforge": "1"})
    try:
        return json.load(urllib.request.urlopen(req, timeout=60))
    except urllib.error.HTTPError as e:
        return json.load(e)


def test_webui(env, tmp_path):
    import webui
    srv = webui.make_server("127.0.0.1", 0, str(tmp_path / "out"), quiet=True)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        base = f"http://127.0.0.1:{srv.server_address[1]}"
        schema = json.load(urllib.request.urlopen(base + "/api/schema", timeout=10))
        assert schema["updates"]["auto"] is True and schema["bundle"] is False
        d = _post(base, "/api/update-check", {})
        assert d["ok"] and d["anzahl"] == 1 and d["einstellungen"]["token_gesetzt"] is False
        d = _post(base, "/api/update-paket", {"id": "spuk"})
        assert d["ok"] and "spuk" in d["schema"]["models"]
        assert _post(base, "/api/update-paket", {"alle": True})["message"] == "Alle Pakete sind aktuell"
        d = _post(base, "/api/update-einstellungen", {"token": "xyz", "auto": False})
        assert d["ok"] and d["einstellungen"]["token_gesetzt"] and "xyz" not in json.dumps(d)
        assert _post(base, "/api/update-programm", {}).get("error") == "nicht gefunden"     # nur in der App
        os.remove(env / "kanal" / "feed.json")
        d = _post(base, "/api/update-check", {})
        assert not d["ok"] and "Nicht gefunden" in d["error"] and "einstellungen" in d
    finally:
        srv.shutdown()
        srv.server_close()
