"""Modell Wichtelhaus."""
import math

import pytest

from conftest import MATERIALS, assert_cut_ready, check
from steckwerk import Config, signed_area
from models import wichtelhaus


def test_default_is_cut_ready(cfg):
    asm = wichtelhaus.build(cfg)
    rep = assert_cut_ready(asm, cfg)
    names = {p.name.split("_", 1)[1] for p in asm.parts}
    assert {"vorne", "hinten", "links", "rechts", "boden", "dach_links", "dach_rechts", "kamin"} <= names
    # 4 Zinkenkanten, 8 Bodentabs, 4 Giebel-Dach-Tabs, 1 Kamin
    joints = [e for e in rep.entries if e.scope == "Verbindung"]
    assert len(joints) == len(asm.connections) == 4 + 8 + 4 + 1


@pytest.mark.parametrize("T,kerf", MATERIALS)
def test_any_material(T, kerf):
    cfg = Config(thickness=T, kerf=kerf)
    assert_cut_ready(wichtelhaus.build(cfg), cfg)


@pytest.mark.parametrize("kw", [dict(annex=True), dict(chimney=False), dict(openings="engrave"),
                                dict(door="square", front_windows=0), dict(front_windows=1, side_windows=2),
                                dict(pitch=30), dict(pitch=60), dict(light=False),
                                dict(width=120, depth=90, height=90)])
def test_variants(cfg, kw):
    assert_cut_ready(wichtelhaus.build(cfg, **kw), cfg)


def test_dimensions_follow_parameters(cfg):
    asm = wichtelhaus.build(cfg, width=90, height=70, pitch=45)
    front = asm.part("wichtelhaus_vorne")
    x0, y0, x1, y1 = front.bbox()
    assert math.isclose(x1 - x0, 90)                      # Zinken sind Kerben → Außenmaß = W
    # First = Traufhöhe + W/2·tan(45°); Dachtabs stehen max. T darüber, Bodentabs T darunter
    assert y0 == pytest.approx(-3.0)
    assert 70 + 45 <= y1 <= 70 + 45 + 3.0
    side = asm.part("wichtelhaus_links")
    sx0, _, sx1, _ = side.bbox()
    assert math.isclose(sx1 - sx0, 70 - 2 * 3 + 2 * 3)    # (D-2T) + zwei Zinkenreihen


def test_light_hole_toggle(cfg):
    with_light = wichtelhaus.build(cfg).part("wichtelhaus_hinten")
    without = wichtelhaus.build(cfg, light=False).part("wichtelhaus_hinten")
    assert len(with_light.holes) == len(without.holes) + 1
    biggest = max(abs(signed_area(h)) for h in with_light.holes)
    assert biggest > math.pi * 19 ** 2                    # Ø ≈ 40 mm


def test_engrave_mode_has_no_window_holes(cfg):
    asm = wichtelhaus.build(cfg, openings="engrave")
    assert asm.part("wichtelhaus_vorne").holes == []
    assert asm.part("wichtelhaus_links").holes == []
    assert len(asm.part("wichtelhaus_vorne").engrave) > 5


def test_scale_keeps_thickness(cfg):
    big = Config(scale=1.5)
    asm = wichtelhaus.build(big)
    assert_cut_ready(asm, big)
    w = asm.part("wichtelhaus_vorne").size()[0]
    assert math.isclose(w, 120)


def test_narrow_house_drops_front_windows(cfg):
    asm = wichtelhaus.build(cfg, width=30)
    assert_cut_ready(asm, cfg)
    assert len(asm.part("wichtelhaus_vorne").holes) == 1   # nur die Tür passt noch


def test_validator_rejects_too_thin_webs():
    strict = Config(min_web=12.0)                          # z. B. sehr brüchiges Material
    rep = check(wichtelhaus.build(strict), strict)
    assert not rep.passed and any("Steg" in e.message for e in rep.errors)
