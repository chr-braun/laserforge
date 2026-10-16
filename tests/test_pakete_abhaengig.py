"""Pakete, die andere Pakete brauchen (benoetigt/bibliothek, ab 2.4.0) und die mitgelieferten Paketquellen."""
import json
import os
import sys

import pytest

import pakete
import service
import updater
from steckwerk import Config
from conftest import assert_cut_ready

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "packaging"))
import update_kanal  # noqa: E402
QUELLEN = os.path.join(HERE, "paketquellen")
NEUE = ["verzierungen", "umrandungen", "wichtelmoebel", "wichteltuer", "wichtelzubehoer", "werkstatt"]
WICHTEL = ["wichtelmoebel", "wichteltuer", "wichtelzubehoer"]
UMGESTELLT = ["ebenen", "filigran", "halloween", "weihnacht"]           # nutzen seit 2026-10-15 die Bibliothek


@pytest.fixture
def inst(tmp_path, monkeypatch):
    monkeypatch.setenv("STECKWERK_PAKETE", str(tmp_path / "inst"))
    monkeypatch.setenv("STECKWERK_DATEN", str(tmp_path / "daten"))
    yield tmp_path
    monkeypatch.delenv("STECKWERK_PAKETE")
    service.reload_pakete()


def test_manifeste():
    for pid in NEUE:
        m = pakete.read_manifest(os.path.join(QUELLEN, pid))
        assert m["id"] == pid and m["name_en"] and m["beschreibung_en"]
        if pid != "verzierungen":
            assert m["benoetigt"]["verzierungen"] in ("1.0.0", "1.1.0", "1.2.0")
    for pid in UMGESTELLT:
        m = pakete.read_manifest(os.path.join(QUELLEN, pid))
        assert m["benoetigt"] == {"verzierungen": "1.1.0"}
        assert not [f for f in os.listdir(os.path.join(QUELLEN, pid)) if f in ("_kit.py", "_ebenen.py", "_figuren.py")]
    assert pakete.read_manifest(os.path.join(QUELLEN, "verzierungen"))["bibliothek"] == "bibliothek"


def test_abhaengigkeit_fehlt_und_entfernen(inst):
    with pytest.raises(pakete.PaketFehler, match="braucht zuerst das Paket"):
        pakete.install(os.path.join(QUELLEN, "umrandungen"))
    pakete.install(os.path.join(QUELLEN, "verzierungen"))
    m, _ = pakete.install(os.path.join(QUELLEN, "umrandungen"))
    assert m["id"] == "umrandungen"
    with pytest.raises(pakete.PaketFehler, match="noch gebraucht von: Umrandungen"):
        pakete.remove("verzierungen")
    pakete.remove("umrandungen")
    pakete.remove("verzierungen")


def test_bibliothek_laden(inst):
    pakete.install(os.path.join(QUELLEN, "verzierungen"))
    Z = pakete.bibliothek("verzierungen")
    assert Z.VERSION == "1.2.0" and Z.F and Z.G and Z.WM and pakete.bibliothek("verzierungen") is Z
    cfg = Config()
    fig = Z.Figur().add(Z.kartusche(80, 50, "oval"))
    fig.merge(Z.ausschnitt("herz", 0, 25, 16))
    notes = []
    teil = Z.figur_teil(cfg, "probe", fig, notes)
    assert teil.holes and not notes
    b = Z.brett("brett", 40, 20, cfg.T, links=[(10, 6, "l", 1)], rechts=[(10, 6, "r", 2)])
    assert {f.id for f in b.features} == {"l", "r"}
    with pytest.raises(pakete.PaketFehler):
        pakete.bibliothek("gibtsnicht")


def test_updater_installiert_abhaengigkeit_mit(inst):
    pakete.install(os.path.join(QUELLEN, "verzierungen"))          # zum Prüfen beim Packen
    paths = [pakete.pack(os.path.join(QUELLEN, pid), str(inst / "pk"))[0] for pid in ("verzierungen", "wichtelmoebel")]
    pakete.remove("verzierungen")
    kanal = inst / "kanal"
    update_kanal.build(str(kanal), None, paths, today="2026-10-15")
    feed = json.loads((kanal / "feed.json").read_text())
    assert {p["id"]: p.get("benoetigt") for p in feed["pakete"]}["wichtelmoebel"] == {"verzierungen": "1.2.0"}
    os.environ["STECKWERK_UPDATE_KANAL"] = (kanal / "feed.json").as_uri()
    try:
        m = updater.install_paket("wichtelmoebel")
        assert m["id"] == "wichtelmoebel"
        assert set(updater.installed_pakete()) >= {"verzierungen", "wichtelmoebel"}
    finally:
        del os.environ["STECKWERK_UPDATE_KANAL"]


@pytest.mark.parametrize("pid", NEUE + UMGESTELLT + ["wichtelwelt"])
def test_modelle_cut_ready(inst, pid):
    if pid != "verzierungen":
        pakete.install(os.path.join(QUELLEN, "verzierungen"))
    if pid == "wichtelwelt":
        for dep in WICHTEL:
            pakete.install(os.path.join(QUELLEN, dep))
    m, mods = pakete.load_folder(os.path.join(QUELLEN, pid))
    for cfg in (Config(), Config(thickness=4.0, kerf=0.15)):
        for name, mod in mods.items():
            params = {p["key"]: p["default"] for p in mod.INFO["params"]}
            asm = mod.build(cfg, **params)
            for a in asm if isinstance(asm, list) else [asm]:
                assert_cut_ready(a, cfg)


def test_filigran_rezepte(inst):
    pakete.install(os.path.join(QUELLEN, "verzierungen"))
    _, mods = pakete.load_folder(os.path.join(QUELLEN, "filigran"))
    FG = mods["spitzenschmuck"].FG
    assert list(FG.rezept_lesen("Blüten, perlen,BÖGEN")) == ["blueten", "perlen", "boegen"]
    with pytest.raises(ValueError, match="kenne"):
        FG.rezept_lesen("blüten, wolken")
    assert FG.rezept_zufall(7) == FG.rezept_zufall(7)
    cfg = Config()
    mod = mods["spitzenschmuck"]
    asm = mod.build(cfg, muster="rezept", rezept="ranken, herzen, zickzack", form="herz")
    assert_cut_ready(asm, cfg)
    asm = mod.build(cfg, muster="zufall", startwert=3, anzahl=2)
    assert len(asm.parts) == 2 and sum("Startwert" in n for n in asm.notes) == 2
    assert_cut_ready(asm, cfg)


@pytest.mark.parametrize("kerf", [0.1, 0.2])
def test_halloween_spitze_zwickel(inst, kerf):
    """Spukschloss mit Spinne und Kürbis mit Blatt: spitze Zwickel überstehen den Kerf-Versatz."""
    pakete.install(os.path.join(QUELLEN, "verzierungen"))
    _, mods = pakete.load_folder(os.path.join(QUELLEN, "halloween"))
    cfg = Config(thickness=3.0, kerf=kerf)
    assert_cut_ready(mods["spukschloss"].build(
        cfg, width=176.49808971447334, szene="friedhof", himmel="nichts", fledermaeuse=1, kuerbisse=1, spinne=True,
        variante=55, rahmen_deko="keine", text="Happy Halloween", schrift="breit", schreibweise="gross"), cfg)
    cfg = Config(thickness=5.0, kerf=kerf)
    assert_cut_ready(mods["kuerbis"].build(cfg, width=119.59090487445758, gesicht="froehlich", rippen=True, blatt=True,
                                           text="BOO!", schrift="normal", schreibweise="gross"), cfg)


def test_passungstest_werte(inst):
    pakete.install(os.path.join(QUELLEN, "verzierungen"))
    _, mods = pakete.load_folder(os.path.join(QUELLEN, "werkstatt"))
    pt = mods["passungstest"]
    w = pt.werte(0.2, 5, 0.05)
    assert [d for d, _ in w] == [-0.1, -0.05, 0.0, 0.05, 0.1]
    assert [k for _, k in w] == [0.3, 0.25, 0.2, 0.15, 0.1]
    assert all(k >= 0 for _, k in pt.werte(0.05, 7, 0.05))           # kein negativer Kerf
    cfg = Config(thickness=3.0, kerf=0.2)
    asm = pt.build(cfg)
    kamm = asm.parts[0]
    breiten = sorted({round(abs(a[0] - b[0]), 4) for a, b in zip(kamm.outline, kamm.outline[1:])
                      if abs(a[1] - b[1]) < 1e-9 and abs(a[1] - min(p[1] for p in kamm.outline if p[1] > 0)) < 1e-9})
    assert 3.0 in breiten and 3.15 in breiten and 2.85 in breiten


def test_wichtel_massstab(inst):
    pakete.install(os.path.join(QUELLEN, "verzierungen"))
    for dep in WICHTEL:
        pakete.install(os.path.join(QUELLEN, dep))
    WM = pakete.bibliothek("verzierungen").WM
    bank = pakete.bibliothek("wichtelmoebel", "wichtelbank")
    assert bank.INFO["params"][0]["key"] == "massstab"
    assert {p["key"]: p.get("when") for p in bank.INFO["params"]}["sitzhoehe"] == {"massstab": ["frei"]}
    m = WM.wichtelmass("wichtelbank", 70, bank.INFO["params"])
    assert m["laenge"] == 70 and m["sitzhoehe"] == 23.8
    assert WM.wichtelmass("wichtelbank", 300, bank.INFO["params"])["laenge"] == 200     # Parametergrenze
    cfg = Config(thickness=5.0)
    with pytest.raises(ValueError, match="mindestens 70 mm"):
        bank.build(cfg, wichtel=50)
    asm = bank.build(Config(), massstab="frei", laenge=90)                              # eigene Maße bleiben
    assert asm.params["laenge"] == 90


def test_wichtelzimmer(inst):
    pakete.install(os.path.join(QUELLEN, "verzierungen"))
    for dep in WICHTEL:
        pakete.install(os.path.join(QUELLEN, dep))
    _, mods = pakete.load_folder(os.path.join(QUELLEN, "wichtelwelt"))
    cfg = Config()
    out = mods["wichtelzimmer"].build(cfg, wichtel=90, leiter=True, bett=False)
    namen = [a.name for a in out]
    assert namen == ["wichtelfigur", "wichteltuer", "wichtelfenster", "wichtelbank", "wichteltisch",
                     "wichtelleiter"]
    assert out[1].params["hoehe"] == 135.0 and out[3].params["laenge"] == 90.0
    for a in out:
        assert_cut_ready(a, cfg)
    with pytest.raises(ValueError, match="Bank, Tisch und Bett mindestens 75 mm"):
        mods["wichtelzimmer"].build(Config(thickness=5.0), wichtel=40)
