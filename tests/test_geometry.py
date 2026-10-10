"""Engine: Geometrie-Grundlagen, Kerf-Offset, Kantenprofile, Config, SVG."""
import math

import pytest

from steckwerk import (Config, ConfigError, Part, arched, circle, finger_count, finger_segments,
                        offset_polygon, profile_edge, rect, sheet_to_svg, signed_area, layout,
                        tab_centers, tab_segments, clean, dist)


def test_offset_grows_outline_and_shrinks_hole():
    sq = rect(0, 0, 10, 10)                       # CCW Außenkontur
    out = offset_polygon(sq, 0.1)
    assert math.isclose(abs(signed_area(out)), 10.2 ** 2, rel_tol=1e-9)
    hole = rect(2, 2, 4, 4, ccw=False)            # CW Loch
    inn = offset_polygon(hole, 0.1)
    assert math.isclose(abs(signed_area(inn)), 3.8 ** 2, rel_tol=1e-9)


def test_offset_sharp_corner_is_bevelled():
    tri = [(0, 0), (100, 0), (50, 3)]             # sehr spitze Ecken
    out = offset_polygon(tri, 0.5)
    # Fase statt endloser Gehrung: kein Punkt weiter als 2.5·d (+Toleranz) von der Kontur weg
    from steckwerk import dist_to_boundary
    assert max(dist_to_boundary(p, tri) for p in out) <= 2.5 * 0.5 + 1e-9


def test_finger_count_is_odd_and_wide_enough():
    cfg = Config()
    for L in (20, 33, 65, 120, 300):
        n = finger_count(L, cfg)
        assert n % 2 == 1 and n >= 3
        assert L / n >= cfg.min_tab_width or n == 3


def test_finger_segments_complementary():
    a = finger_segments(60, 5, 3, "notch")
    b = finger_segments(60, 5, 3, "tab")
    for (wa, da), (wb, db) in zip(a, b):
        assert wa == wb
        assert (da == 0) != (db > 0)              # genau eine Seite besetzt die Eckzone


def test_profile_edge_length_mismatch_raises():
    with pytest.raises(ValueError):
        profile_edge((0, 0), (10, 0), [(5, 0), (4, 3)])


def test_tab_segments_sum_to_length():
    cfg = Config()
    c, w = tab_centers(80, cfg, inset=6)
    segs = tab_segments(80, c, w, 3)
    assert math.isclose(sum(s for s, _ in segs), 80)
    assert w >= cfg.min_tab_width


def test_circle_and_arch_are_closed_and_clean():
    c = circle(0, 0, 10)
    assert dist(c[0], c[-1]) > 0                  # nicht doppelt geschlossen
    a = clean(arched(0, 0, 10, 20))
    assert len(a) > 10 and signed_area(a) > 0


@pytest.mark.parametrize("bad", [dict(kerf=2.0), dict(thickness=0), dict(units="in"),
                                 dict(cut_color="black"), dict(openings="laser"),
                                 dict(cut_color="#0000FF")])
def test_config_rejects_bad_values(bad):
    with pytest.raises(ConfigError):
        Config(**bad)


def test_config_yaml_roundtrip(tmp_path):
    p = tmp_path / "c.yaml"
    p.write_text("thickness: 4\nkerf: 0.15  # Diodenlaser\nengrave_color: '#FF0000'\n")
    cfg = Config.load(str(p))
    assert cfg.thickness == 4 and cfg.kerf == 0.15 and cfg.engrave_color == "#FF0000"
    p.write_text("dicke: 4\n")
    with pytest.raises(ConfigError):
        Config.load(str(p))


def test_svg_has_mm_units_and_layers():
    cfg = Config()
    part = Part("t", rect(0, 0, 20, 10))
    part.add_engrave([(2, 2), (8, 2)])
    sheets = layout([part.compensated(cfg.kerf_offset)], cfg)
    svg = sheet_to_svg(sheets[0], cfg, "test")
    assert 'width="400mm"' in svg and 'viewBox="0 0 400 300"' in svg
    assert 'stroke="#000000"' in svg and 'stroke="#0000FF"' in svg
    assert 'inkscape:label="Schnitt"' in svg and 'inkscape:label="Gravur"' in svg
    assert svg.index("layer-gravur") < svg.index("layer-schnitt")


def test_layout_spills_to_second_sheet_and_rotates():
    cfg = Config(sheet_width=120, sheet_height=80)
    parts = [Part(f"p{i}", rect(0, 0, 100, 60)) for i in range(3)]
    sheets = layout(parts, cfg)
    assert len(sheets) == 3
    tall = layout([Part("hoch", rect(0, 0, 60, 100))], cfg)
    w, h = tall[0].parts[0].size()
    assert w > h                                   # wurde gedreht
