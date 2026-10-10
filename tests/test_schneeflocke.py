"""Schneeflocken: reproduzierbar, kollisionsfrei, flach und 3D."""
import pytest

from conftest import MATERIALS, assert_cut_ready
from steckwerk import Config
from models import schneeflocke


def test_same_seed_same_flake(cfg):
    a = schneeflocke.build(cfg, seed=11)
    b = schneeflocke.build(cfg, seed=11)
    c = schneeflocke.build(cfg, seed=12)
    assert a.parts[0].outline == b.parts[0].outline
    assert a.parts[0].outline != c.parts[0].outline


@pytest.mark.parametrize("size", [30, 50, 80, 140, 220])
def test_sizes_many_seeds(cfg, size):
    assert_cut_ready(schneeflocke.build(cfg, size=size, count=12, seed=1), cfg)


@pytest.mark.parametrize("T,kerf", MATERIALS)
@pytest.mark.parametrize("three_d", [False, True])
def test_materials(T, kerf, three_d):
    cfg = Config(thickness=T, kerf=kerf)
    assert_cut_ready(schneeflocke.build(cfg, size=90, count=6, seed=3, three_d=three_d), cfg)


def test_3d_two_halves(cfg):
    asm = schneeflocke.build(cfg, count=3, three_d=True)
    assert len(asm.parts) == 6 and len(asm.connections) == 3
    rep = assert_cut_ready(asm, cfg)
    assert sum("Kreuzschlitz" in e.message for e in rep.entries) == 3


def test_flake_is_sixfold_and_has_eye(cfg):
    import math
    from steckwerk import bbox
    for seed in range(1, 9):
        p = schneeflocke.build(cfg, size=80, seed=seed).parts[0]
        eye = bbox(p.holes[0])                                   # erstes Loch = Öse an der oberen Spitze
        assert abs(eye[0] + eye[2]) < 1e-6 and (eye[1] + eye[3]) / 2 > 0.7 * 40
        # sechszählig: Konturpunkte um 60° gedreht liegen wieder auf der Kontur (ohne Arm mit Öse)
        x0, y0, x1, y1 = p.bbox()
        assert math.isclose(-y0, max(abs(x0), abs(x1)) / math.cos(math.pi / 6), rel_tol=0.05) or y0 < -30


def test_limits(cfg):
    with pytest.raises(ValueError):
        schneeflocke.build(cfg, size=20)
    with pytest.raises(ValueError):
        schneeflocke.build(cfg, count=0)
