"""Seit 2.7.0: alte Einzelpakete, die in einem Themenpaket aufgegangen sind, werden nicht mehr geladen."""
import json
import os

import pytest

import pakete
import service


@pytest.fixture
def inst(tmp_path, monkeypatch):
    monkeypatch.setenv("STECKWERK_PAKETE", str(tmp_path / "inst"))
    monkeypatch.setenv("STECKWERK_DATEN", str(tmp_path / "daten"))
    yield tmp_path
    monkeypatch.delenv("STECKWERK_PAKETE")
    service.reload_pakete()


def _alt(inst, pid, **extra):
    folder = pakete.create(pid, str(inst / "alt"))
    if extra:
        p = os.path.join(folder, "paket.json")
        with open(p, encoding="utf-8") as fh:
            m = json.load(fh)
        m.update(extra)
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(m, fh)
    pakete.install(folder)
    return pakete.read_manifest(folder)


def test_altlast_wird_deaktiviert(inst):
    m = _alt(inst, "filigran")
    service.reload_pakete()
    eintrag = {p["id"]: p for p in service.schema()["pakete"]}["filigran"]
    assert eintrag["ersatz"] == "weihnacht"
    assert "Weihnachten" in eintrag["fehler"]
    assert not any(k in service.schema()["models"] for k in m["modelle"])


def test_altlasten_einzeln_entfernbar(inst):
    _alt(inst, "wichtelwelt")
    _alt(inst, "wichtelmoebel", benoetigt={"wichtelwelt": "1.0.0"})
    pakete.remove("wichtelwelt")                     # die alte Abhängigkeit hält nicht mehr fest
    pakete.remove("wichtelmoebel")
    assert not os.listdir(str(inst / "inst"))


def test_normale_pakete_unberuehrt(inst):
    _alt(inst, "meinpaket")
    service.reload_pakete()
    eintrag = {p["id"]: p for p in service.schema()["pakete"]}["meinpaket"]
    assert eintrag["fehler"] is None and eintrag["ersatz"] is None
