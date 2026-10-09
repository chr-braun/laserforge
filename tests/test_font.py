"""Einstrich-Schrift für Namen und Jahreszahlen."""
import pytest

from models._font import GLYPHS, fit_text, normalize, text_width, unsupported


def test_glyphs_cover_german_names():
    for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÜß0123456789-+.,!?&'/* ":
        assert ch in GLYPHS
    assert normalize("Jörg ẞ") == "JÖRG ß"
    assert unsupported("Anna|2026") == []
    assert unsupported("Zoë") == ["Ë"]


def test_fit_text_respects_box():
    strokes, h = fit_text("Anna|2026", 0, 0, 40, 20, max_cap=12)
    xs = [p[0] for s in strokes for p in s]
    ys = [p[1] for s in strokes for p in s]
    assert 2.5 <= h <= 12
    assert max(xs) - min(xs) <= 40 + 1e-6 and max(ys) - min(ys) <= 20 + 1e-6
    assert abs((max(xs) + min(xs)) / 2) < 1e-6          # horizontal zentriert


def test_fit_text_too_long_raises():
    with pytest.raises(ValueError, match="Schrifthöhe"):
        fit_text("Ein viel zu langer Text", 0, 0, 20, 10, min_h=3)


def test_width_grows_with_length():
    assert text_width("ABC") > text_width("AB") > 0
    assert fit_text("", 0, 0, 10, 10) == ([], 0.0)
