"""Steckfahrzeuge: Tab/Slot, drehende Achsen, gespiegelte Seiten."""
import math

import pytest

from conftest import MATERIALS, assert_cut_ready, check
from laserforge import Config, bbox, circle
from models import fahrzeug
from models.fahrzeug import DEFAULTS, MIN_LENGTH, VEHICLES


@pytest.mark.parametrize("vehicle", VEHICLES)
@pytest.mark.parametrize("T,kerf", MATERIALS)
def test_vehicles_materials(vehicle, T, kerf):
    cfg = Config(thickness=T, kerf=kerf)
    assert_cut_ready(fahrzeug.build(cfg, vehicle=vehicle), cfg)


@pytest.mark.parametrize("vehicle", VEHICLES)
@pytest.mark.parametrize("f", [None, 1.3, 2.0])
def test_vehicle_sizes(cfg, vehicle, f):
    L = MIN_LENGTH[vehicle] if f is None else DEFAULTS[vehicle]["length"] * f
    assert_cut_ready(fahrzeug.build(cfg, vehicle=vehicle, length=L, width=0.45 * L, text="Max" if f else ""), cfg)


def test_lkw_three_axles_and_openings_engrave():
    cfg = Config(openings="engrave")
    asm = fahrzeug.build(cfg, vehicle="lkw", axles=3, text="Wichtel-Express")
    assert_cut_ready(asm, cfg)
    assert sum(p.name.startswith("achse_") for p in asm.parts) == 3
    assert sum(p.name.startswith("rad_") for p in asm.parts) == 6


def test_axle_joints_are_checked(cfg):
    asm = fahrzeug.build(cfg, vehicle="auto")
    rep = assert_cut_ready(asm, cfg)
    msgs = [e.message for e in rep.entries]
    assert sum("Achse ⇄ Rad" in m for m in msgs) == 4
    assert sum("Achse ⇄ Lager" in m and "dreht frei" in m for m in msgs) == 4
    # Lagerbohrung zu eng → der Validator muss es merken
    side = asm.part("seite_l")
    f = side.feature("lager0")
    k = side.holes.index(f.points)
    x0, y0, x1, y1 = bbox(f.points)
    small = circle((x0 + x1) / 2, (y0 + y1) / 2, cfg.T * 0.6, 0.02, ccw=False)
    side.holes[k] = small
    f.points, f.length = list(small), cfg.T * 1.2
    rep = check(asm, cfg)
    assert not rep.passed and any("klemmt" in e.message for e in rep.errors)


def test_sides_are_mirrored_text_reads_normally(cfg):
    asm = fahrzeug.build(cfg, vehicle="lkw", text="AB")
    l, r = asm.part("seite_l"), asm.part("seite_r")
    L = asm.params["length"]
    assert sorted(round(L - x, 6) for x, _ in l.outline) == sorted(round(x, 6) for x, _ in r.outline)
    # Buchstabe A (erste Glyphe, 2 Striche) steht auf beiden Seiten links von B
    for p in (l, r):
        strokes = p.engrave[-3:]                    # A: 2 Striche, B: 2 Striche → letzte 3 enthalten B
        xs_a = [q[0] for s in p.engrave[-4:-2] for q in s.points]
        xs_b = [q[0] for s in p.engrave[-2:] for q in s.points]
        assert max(xs_a) < min(xs_b) + 1e-6, strokes


def test_wheels_turn_axle_fits(cfg):
    asm = fahrzeug.build(cfg, vehicle="lok")
    axle = asm.part("achse_0")
    w = asm.part("rad_0l")
    assert math.isclose(axle.size()[1], cfg.T)                  # Vierkant T × T
    x0, y0, x1, y1 = bbox(w.holes[0])
    assert math.isclose(x1 - x0, cfg.T) and math.isclose(y1 - y0, cfg.T)
    assert len(w.holes) > 1                                     # Speichenrad der Lok


def test_errors(cfg):
    with pytest.raises(ValueError):
        fahrzeug.build(cfg, vehicle="ufo")
    with pytest.raises(ValueError):
        fahrzeug.build(cfg, vehicle="auto", length=50)
    with pytest.raises(ValueError):
        fahrzeug.build(cfg, vehicle="auto", width=100)
    with pytest.raises(ValueError, match="passt"):
        fahrzeug.build(cfg, vehicle="auto", text="Ein ganz besonders langer Name")
