"""Paket „Schmuck“ (ab 2.8.0): Ohrhänger-Paare."""
import os

import pytest

import pakete
from steckwerk import Config
from conftest import assert_cut_ready

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_, MODS = pakete.load_folder(os.path.join(HERE, "paketquellen", "schmuck"))
OH = MODS["ohrhaenger"]


@pytest.mark.parametrize("motiv", [m for m, _ in OH.MOTIVE])
@pytest.mark.parametrize("stil", [s for s, _ in OH.STILE])
def test_motive_cut_ready(motiv, stil):
    cfg = Config(thickness=3.0)
    asm = OH.build(cfg, motiv=motiv, stil=stil)
    assert [p.name for p in asm.parts] == ["links", "rechts"]
    assert_cut_ready(asm, cfg)
    for p in asm.parts:
        assert p.holes, "Öse fehlt"
    if stil == "graviert":
        assert all(p.engrave for p in asm.parts)


def test_paar_ist_gespiegelt():
    asm = OH.build(Config(thickness=2.0), motiv="fluegel")
    a, b = asm.parts
    xa = sorted(round(x, 3) for x, _ in a.outline)
    xb = sorted(round(-x, 3) for x, _ in b.outline)
    assert xa == xb


@pytest.mark.parametrize("zwischen", ["kreis", "stern", "tropfen", "mond"])
def test_zwischenteil(zwischen):
    cfg = Config(thickness=2.0)
    asm = OH.build(cfg, motiv="tropfen", zwischen=zwischen, paar=False)
    assert [p.name for p in asm.parts] == ["einzeln", "einzeln_oben"]
    assert len(asm.parts[1].holes) == 2
    assert_cut_ready(asm, cfg)


def test_kleine_ohrringe_bleiben_laserfest():
    cfg = Config(thickness=1.5)
    for m, _ in OH.MOTIVE:
        assert_cut_ready(OH.build(cfg, motiv=m, groesse=20, loch=1.4), cfg)


def test_rahmen_zu_breit():
    with pytest.raises(ValueError, match="Rahmen"):
        OH.build(Config(thickness=3.0), motiv="mond", groesse=20, stil="rahmen", rand=6)
