"""Geometrie-Validator: jede Prüfung muss echte Fehler finden und gute Geometrie durchlassen."""
import copy

import pytest

from steckwerk import (Assembly, Config, JointFeature, Part, Sheet, Stroke, circle, layout,
                        profile_edge, rect, slot_feature, finger_segments, finger_feature, clean)
from validator import (Report, check_connection, check_kerf, check_part, check_path,
                       validate_assembly, validate_sheets)


@pytest.fixture
def cfg():
    return Config()


# --- Einzelpfad -----------------------------------------------------------------------

def test_closed_square_ok(cfg):
    assert check_path(rect(0, 0, 10, 10), True, cfg) == []


def test_open_contour_is_error(cfg):
    errs = check_path(rect(0, 0, 10, 10), False, cfg)
    assert any("offene Kontur" in e for e in errs)


def test_double_closed_contour_is_error(cfg):
    pts = rect(0, 0, 10, 10) + [(0, 0)]
    assert any("doppelt" in e or "Doppelknoten" in e for e in check_path(pts, True, cfg))


def test_duplicate_node_is_error(cfg):
    pts = [(0, 0), (10, 0), (10, 0), (10, 10), (0, 10)]
    assert any("Doppelknoten" in e for e in check_path(pts, True, cfg))


def test_self_intersection_is_error(cfg):
    bowtie = [(0, 0), (10, 10), (10, 0), (0, 10)]
    assert any("Selbstüberschneidung" in e for e in check_path(bowtie, True, cfg))


def test_touching_vertex_is_error(cfg):
    # Kontur berührt sich selbst in einem Punkt (Schnitt würde ein Teil abtrennen)
    pts = [(0, 0), (10, 0), (10, 10), (5, 0.0), (0, 10)]
    assert check_path(pts, True, cfg)


def test_spike_is_error(cfg):
    pts = [(0, 0), (10, 0), (15, 0), (10, 0.0000001), (10, 10), (0, 10)]
    errs = check_path(clean(pts), True, cfg)
    assert errs


def test_min_length_and_area(cfg):
    tiny = rect(0, 0, 0.4, 0.4)
    errs = check_path(tiny, True, cfg)
    assert any("zu kurz" in e for e in errs) and any("Fläche" in e for e in errs)


# --- Bauteil --------------------------------------------------------------------------

def test_hole_outside_outline(cfg):
    p = Part("p", rect(0, 0, 20, 20), [rect(15, 5, 10, 5, ccw=False)])
    assert any("außerhalb" in e for e in check_part(p, cfg))


def test_overlapping_holes(cfg):
    p = Part("p", rect(0, 0, 40, 40), [rect(5, 5, 10, 10, ccw=False), rect(10, 10, 10, 10, ccw=False)])
    assert any("überlappende Schnitte" in e for e in check_part(p, cfg))


def test_min_web_between_holes(cfg):
    p = Part("p", rect(0, 0, 40, 40), [rect(5, 5, 10, 10, ccw=False), rect(15.5, 5, 10, 10, ccw=False)])
    assert any("Steg" in e for e in check_part(p, cfg))
    ok = Part("p", rect(0, 0, 40, 40), [rect(5, 5, 10, 10, ccw=False), rect(17, 5, 10, 10, ccw=False)])
    assert check_part(ok, cfg) == []


def test_engrave_outside_and_over_hole(cfg):
    p = Part("p", rect(0, 0, 20, 20), [rect(5, 5, 10, 10, ccw=False)])
    p.engrave.append(Stroke([(1, 1), (25, 1)]))
    p.engrave.append(Stroke([(6, 7), (14, 7)]))
    errs = check_part(p, cfg)
    assert any("ragt über" in e for e in errs)
    assert any("Durchbruch" in e for e in errs)


# --- Kerf -------------------------------------------------------------------------------

def test_kerf_ok_and_detects_missing_compensation(cfg):
    p = Part("p", rect(0, 0, 30, 20), [circle(15, 10, 5, ccw=False)])
    comp = p.compensated(cfg.kerf_offset)
    assert check_kerf(p, comp, cfg) == []
    assert check_kerf(p, p, cfg)                      # unkompensiert → Fehler
    wrong = p.compensated(-cfg.kerf_offset)           # falsche Richtung → Fehler
    errs = check_kerf(p, wrong, cfg)
    assert any("außen" in e for e in errs) and any("innen" in e for e in errs)


@pytest.mark.parametrize("kerf", [0.05, 0.1, 0.2, 0.3, 0.5])
def test_kerf_works_for_any_value(kerf):
    cfg = Config(kerf=kerf)
    p = Part("p", rect(0, 0, 30, 20), [rect(5, 5, 6, 6, ccw=False)])
    comp = p.compensated(cfg.kerf_offset)
    assert check_kerf(p, comp, cfg) == []
    # Außenmaß wächst um genau kerf, Lochmaß schrumpft um genau kerf
    w, h = comp.size()
    assert abs(w - (30 + kerf)) < 1e-9 and abs(h - (20 + kerf)) < 1e-9
    from steckwerk import bbox
    x0, y0, x1, y1 = bbox(comp.holes[0])
    assert abs((x1 - x0) - (6 - kerf)) < 1e-9


# --- Steckverbindungen -----------------------------------------------------------------

def _tab(w=9.0, h=3.0, pos=10.0):
    return JointFeature("t", "tab", w, h, pos=pos)


def _slot(l=9.0, w=3.0, pos=10.0):
    return JointFeature("s", "slot", l, w, pos=pos)


def test_tab_slot_match(cfg):
    errs, desc = check_connection(_tab(), _slot(), False, cfg)
    assert errs == [] and "1:1" in desc


@pytest.mark.parametrize("tab,slot,needle", [
    (_tab(w=9.0), _slot(l=8.5), "Slotlänge"),
    (_tab(h=4.0), _slot(), "Tabhöhe"),
    (_tab(), _slot(w=2.5), "Slotbreite"),
    (_tab(w=3.0), _slot(l=3.0), "T + Kerf"),
    (_tab(pos=10), _slot(pos=12), "Position"),
])
def test_tab_slot_mismatch(cfg, tab, slot, needle):
    errs, _ = check_connection(tab, slot, False, cfg)
    assert any(needle in e for e in errs), errs


def _fingers(L, n, phase, T=3.0):
    segs = finger_segments(L, n, T, phase)
    return finger_feature("f", (0, 0), (0, L), segs, phase, T)


def test_finger_match_and_flip(cfg):
    a, b = _fingers(63, 7, "notch"), _fingers(63, 7, "tab")
    assert check_connection(a, b, False, cfg)[0] == []
    assert check_connection(a, b, True, cfg)[0] == []


def test_finger_not_complementary(cfg):
    a, b = _fingers(63, 7, "notch"), _fingers(63, 7, "notch")
    assert any("komplementär" in e for e in check_connection(a, b, False, cfg)[0])


def test_finger_count_and_length_mismatch(cfg):
    a, b = _fingers(63, 7, "notch"), _fingers(63, 5, "tab")
    assert any("Zinkenzahl" in e for e in check_connection(a, b, False, cfg)[0])
    a, b = _fingers(63, 7, "notch"), _fingers(60, 7, "tab")
    assert any("Kantenlängen" in e for e in check_connection(a, b, False, cfg)[0])


def test_finger_too_narrow(cfg):
    a, b = _fingers(15, 7, "notch"), _fingers(15, 7, "tab")
    assert any("T + Kerf" in e for e in check_connection(a, b, False, cfg)[0])


def test_halving_must_meet(cfg):
    a = JointFeature("k", "halving", 50, 3.0, span=(50, 100))
    b = JointFeature("k", "halving", 50, 3.0, span=(0, 50))
    assert check_connection(a, b, False, cfg)[0] == []
    c = JointFeature("k", "halving", 45, 3.0, span=(0, 45))
    assert any("treffen" in e for e in check_connection(a, c, False, cfg)[0])


def _mini_assembly(cfg, tab_w=9.0, slot_l=9.0):
    T = cfg.T
    a = (30 - tab_w) / 2
    wall = Part("wand", profile_edge((0, 0), (30, 0), [(a, 0), (tab_w, T), (a, 0)]) + [(30, 0), (30, 20), (0, 20)],
                features=[JointFeature("tab0", "tab", tab_w, T, pos=15.0,
                                       points=[(a, 0), (a, -T), (a + tab_w, -T), (a + tab_w, 0)])])
    base = Part("boden", rect(0, 0, 40, 20))
    f, hole = slot_feature("slot0", 20 - slot_l / 2, 10 - T / 2, slot_l, T, True, 15.0)
    base.holes.append(hole)
    base.features.append(f)
    asm = Assembly("mini", [wall, base])
    asm.connect("wand:tab0", "boden:slot0")
    return asm


def test_assembly_logs_connection(cfg):
    rep = validate_assembly(_mini_assembly(cfg), cfg)
    assert rep.passed, rep.text()
    assert any(e.scope == "Verbindung" and "wand.tab0 ⇄ boden.slot0" in e.message for e in rep.entries)


def test_assembly_detects_mismatch(cfg):
    rep = validate_assembly(_mini_assembly(cfg, slot_l=8.0), cfg)
    assert not rep.passed
    assert "FEHLER" in rep.summary() and "keine Datei" in rep.summary()


def test_unconnected_feature(cfg):
    asm = _mini_assembly(cfg)
    asm.connections.clear()
    rep = validate_assembly(asm, cfg)
    assert any("mit nichts verbunden" in e.message for e in rep.errors)


def test_feature_must_match_geometry(cfg):
    asm = _mini_assembly(cfg)
    wall = asm.part("wand")
    wall.features[0].points = [(1, 1), (1, -2), (2, -2), (2, 1)]   # behauptet, Geometrie fehlt
    rep = validate_assembly(asm, cfg)
    assert any("passt nicht zur Kontur" in e.message for e in rep.errors)
    asm = _mini_assembly(cfg)
    asm.part("boden").holes.clear()                                  # Slot-Loch fehlt
    rep = validate_assembly(asm, cfg)
    assert any("kein vorhandener" in e.message for e in rep.errors)


# --- Blatt ----------------------------------------------------------------------------

def test_sheet_overlap_detected(cfg):
    a = Part("a", rect(10, 10, 30, 30))
    b = Part("b", rect(30, 30, 30, 30))
    rep = Report("x")
    validate_sheets([Sheet(1, 400, 300, [a, b])], cfg, rep)
    assert any("überlappen" in e.message for e in rep.errors)
    rep = Report("x")
    validate_sheets(layout([a, b], cfg), cfg, rep)
    assert rep.passed


def test_sheet_bounds(cfg):
    rep = Report("x")
    validate_sheets([Sheet(1, 100, 100, [Part("a", rect(80, 80, 30, 30))])], cfg, rep)
    assert any("außerhalb des Blatts" in e.message for e in rep.errors)


# --- Fertige SVG-Datei ------------------------------------------------------------------

def _house_svg(cfg):
    from models import wichtelhaus
    from steckwerk import sheet_to_svg
    asm = wichtelhaus.build(cfg)
    sheets = layout([p.compensated(cfg.kerf_offset) for p in asm.parts], cfg)
    return sheet_to_svg(sheets[0], cfg, "t")


def test_svg_file_ok(cfg):
    from validator import validate_svg_text
    assert validate_svg_text(_house_svg(cfg), cfg).passed


@pytest.mark.parametrize("mutate,needle", [
    (lambda s: s[:s.index("layer-schnitt")] + s[s.index("layer-schnitt"):].replace(' Z"', '"', 1),
     "offene Kontur"),
    (lambda s: s.replace('width="400mm"', 'width="400"'), "mm"),
    (lambda s: s.replace('stroke="#000000" fill="none" stroke-width="0.1"/>',
                         'stroke="#FF00FF" fill="none" stroke-width="0.1"/>', 1), "Linienfarbe"),
    (lambda s: s.replace('fill="none" stroke-width="0.1"/>', 'fill="#000000" stroke-width="0.1"/>', 1), "gefüllt"),
])
def test_svg_file_errors(cfg, mutate, needle):
    from validator import validate_svg_text
    rep = validate_svg_text(mutate(_house_svg(cfg)), cfg)
    assert any(needle in e.message for e in rep.errors), rep.text()[-500:]


def test_svg_file_overlap_between_parts(cfg):
    from validator import validate_svg_text
    s = _house_svg(cfg)
    i = s.index('<g id="schnitt-')
    j = s.index("</g>", i) + 4
    dup = s[i:j].replace('id="schnitt-', 'id="schnitt-kopie-')   # gleiches Teil doppelt → Überlappung
    rep = validate_svg_text(s[:j] + dup + s[j:], cfg)
    assert any("überlappen" in e.message for e in rep.errors)
