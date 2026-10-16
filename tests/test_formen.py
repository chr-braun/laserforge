"""Paket „Formen“: Steckkörper, Wellenfläche, Stapelvase – schnittfertig, Kreuzungen stimmen, Grenzen."""
import math
import os

import pytest

import pakete
from steckwerk import Config
from conftest import assert_cut_ready

QUELLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "paketquellen", "formen")


@pytest.fixture(scope="module")
def mods():
    _, m = pakete.load_folder(QUELLE)
    return m


@pytest.mark.parametrize("T,kerf", [(1.5, 0.12), (3.0, 0.2), (4.0, 0.15)])
def test_standardwerte_cut_ready(mods, T, kerf):
    cfg = Config(thickness=T, kerf=kerf)
    for name, mod in mods.items():
        params = {p["key"]: p["default"] for p in mod.INFO["params"]}
        assert_cut_ready(mod.build(cfg, **params), cfg)


@pytest.mark.parametrize("form", ["kugel", "ei", "linse", "zwiebel", "kreisel", "tanne", "kuppel"])
@pytest.mark.parametrize("rippen", [3, 8])
def test_steckkoerper_formen(mods, form, rippen):
    cfg = Config()
    asm = mods["steckkoerper"].build(cfg, form=form, durchmesser=140, rippen=rippen)
    assert_cut_ready(asm, cfg)
    assert len(asm.parts) == 2 * rippen
    # jede Kreuzung: A von oben, B von unten, beide Hälften treffen sich in derselben Höhe
    parts = {p.name: p for p in asm.parts}
    for c in asm.connections:
        fa = parts[c.a.split(":")[0]].feature(c.a.split(":")[1])
        fb = parts[c.b.split(":")[0]].feature(c.b.split(":")[1])
        assert math.isclose(fa.span[0], fb.span[1], abs_tol=1e-6)


def test_steckkoerper_zu_gross_und_zu_viele_rippen(mods):
    with pytest.raises(ValueError, match="zu groß"):
        mods["steckkoerper"].build(Config(), form="tanne", durchmesser=280)
    with pytest.raises(ValueError, match="Zu viele Rippen"):
        mods["steckkoerper"].build(Config(thickness=6.0), durchmesser=60, rippen=12)


@pytest.mark.parametrize("funktion", ["welle", "sattel", "huegel", "tropfen", "duenen", "zwei_gipfel", "kuppel"])
def test_wellenflaeche(mods, funktion):
    cfg = Config()
    asm = mods["wellenflaeche"].build(cfg, funktion=funktion, rippen_x=6, rippen_y=4)
    assert_cut_ready(asm, cfg)
    assert len(asm.connections) == 24


def test_wellenflaeche_grenzen(mods):
    with pytest.raises(ValueError, match="Sockel"):
        mods["wellenflaeche"].build(Config(thickness=6.0), sockel=8)


@pytest.mark.parametrize("form,verlauf", [("stern", "bauch"), ("bluete", "tulpe"), ("vieleck", "taille"),
                                          ("zahnrad", "kelch"), ("welle", "kegel")])
def test_stapelvase(mods, form, verlauf):
    cfg = Config()
    asm = mods["stapelvase"].build(cfg, form=form, verlauf=verlauf, hoehe=60, drehung=120)
    assert_cut_ready(asm, cfg)
    assert len(asm.parts) == 20
    assert not asm.parts[0].holes and all(p.holes for p in asm.parts[1:])     # eine dichte Bodenlage
    assert all(p.engrave for p in asm.parts)                                  # Nummer (und Marke)


def test_stapelvase_glas_zu_gross(mods):
    with pytest.raises(ValueError, match="Glas höchstens"):
        mods["stapelvase"].build(Config(), durchmesser=80, einsatz=70)
