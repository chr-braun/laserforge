"""Paket „Bewegung“: Hampelmann, Kurbeltier, Turner, Kreisel, Balancier-Vogel – schnittfertig und plausibel."""
import os

import pytest

import pakete
from steckwerk import Config
from conftest import assert_cut_ready

QUELLEN = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "paketquellen")


@pytest.fixture(scope="module")
def mods(tmp_path_factory):
    alt = {k: os.environ.get(k) for k in ("STECKWERK_PAKETE", "STECKWERK_DATEN")}
    d = tmp_path_factory.mktemp("bewegung")
    os.environ["STECKWERK_PAKETE"] = str(d / "inst")
    os.environ["STECKWERK_DATEN"] = str(d / "daten")
    pakete.install(os.path.join(QUELLEN, "verzierungen"))
    _, m = pakete.load_folder(os.path.join(QUELLEN, "bewegung"))
    yield m
    for k, v in alt.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


@pytest.mark.parametrize("T,kerf", [(3.0, 0.2), (4.0, 0.15)])
def test_standardwerte_cut_ready(mods, T, kerf):
    cfg = Config(thickness=T, kerf=kerf)
    for name, mod in mods.items():
        params = {p["key"]: p["default"] for p in mod.INFO["params"]}
        assert_cut_ready(mod.build(cfg, **params), cfg)


@pytest.mark.parametrize("figur", ["wichtel", "weihnachtsmann", "rentier", "schneemann", "skelett"])
@pytest.mark.parametrize("hoehe", [150, 400])
def test_hampelmann(mods, figur, hoehe):
    cfg = Config(thickness=3.0)
    asm = mods["hampelmann"].build(cfg, figur=figur, hoehe=hoehe, griff="herz")
    assert_cut_ready(asm, cfg)
    namen = [p.name for p in asm.parts]
    assert {"hampelmann_arm_links", "hampelmann_arm_rechts", "hampelmann_bein_links", "hampelmann_bein_rechts",
            "hampelmann_koerper", "hampelmann_griff"} <= set(namen)
    # jedes Glied: Gelenkloch + Fadenloch
    assert all(len(asm.part(n).holes) >= 2 for n in namen if "_arm_" in n or "_bein_" in n)


@pytest.mark.parametrize("bewegung", ["huepfen", "wippen", "doppelt"])
@pytest.mark.parametrize("tier,anzahl", [("hase", 1), ("dino", 2), ("gemischt", 3)])
def test_kurbeltier(mods, bewegung, tier, anzahl):
    cfg = Config(thickness=3.0)
    asm = mods["kurbeltier"].build(cfg, tier=tier, anzahl=anzahl, bewegung=bewegung, breite=210,
                                   aufschrift="Ida")
    rep = assert_cut_ready(asm, cfg)
    mk = asm.params["mechanik"]
    assert mk["rmax"] - mk["rmin"] >= 5
    assert len([p for p in asm.parts if "_nocke_" in p.name]) == anzahl
    assert "Achse ⇄ Lager" in str([e.message for e in rep.entries])


def test_kurbeltier_zu_schmal(mods):
    with pytest.raises(ValueError, match="mindestens"):
        mods["kurbeltier"].build(Config(thickness=3.0), anzahl=3, breite=100)


@pytest.mark.parametrize("figur", ["affe", "baer", "wichtel"])
def test_turner(mods, figur):
    cfg = Config(thickness=3.0)
    assert_cut_ready(mods["turner"].build(cfg, figur=figur, hoehe=60), cfg)


@pytest.mark.parametrize("muster", ["spirale", "farbkreis", "sterne", "blume", "schlicht"])
def test_kreisel(mods, muster):
    cfg = Config(thickness=3.0)
    asm = mods["kreisel"].build(cfg, muster=muster, durchmesser=35, paar=True)
    assert_cut_ready(asm, cfg)
    assert len(asm.parts) == 4


@pytest.mark.parametrize("muenze", ["1ct", "5ct", "1eur"])
@pytest.mark.parametrize("holz", ["pappel", "mdf"])
def test_vogel_balanciert(mods, muenze, holz):
    V = mods["vogel"]
    cfg = Config(thickness=3.0)
    asm = V.build(cfg, spannweite=150, muenze=muenze, holz=holz)
    assert_cut_ready(asm, cfg)
    v = asm.part("vogel_vogel")
    A, cx, cy = V._schwerpunkt(v)
    n = asm.params["muenzen_je_fluegel"]
    mm = V.MUENZEN[muenze][0]
    mw = A * cfg.T * V.DICHTE[holz] / 1000
    # Münzmitten: Mittelpunkte der gravierten Münzkreise
    kreise = [s for s in v.engrave if s.closed and 7 < (max(p[0] for p in s.points) - min(p[0] for p in s.points)) / 2 < 14]
    ym = sum(sum(p[1] for p in s.points) / len(s.points) for s in kreise) / len(kreise)
    y_s = (mw * cy + 2 * n * mm * ym) / (mw + 2 * n * mm)
    spitze = max(y for x, y in v.outline if abs(x) < 1.0)
    assert abs(spitze - y_s) < 1.5


def test_vogel_grenzen(mods):
    with pytest.raises(ValueError, match="zu groß"):
        mods["vogel"].build(Config(thickness=3.0), spannweite=90, muenze="1eur")
