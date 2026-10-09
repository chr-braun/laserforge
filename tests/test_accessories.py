"""Zubehör-Modelle: je ein Testblock pro Modell."""
import math

import pytest

from conftest import MATERIALS, assert_cut_ready
from laserforge import Config
from models import briefkasten, laterne, schneemann, tannenbaum, wichtel, zaun


# --- Tannenbaum --------------------------------------------------------------------
@pytest.mark.parametrize("T,kerf", MATERIALS)
def test_tannenbaum_materials(T, kerf):
    cfg = Config(thickness=T, kerf=kerf)
    assert_cut_ready(tannenbaum.build(cfg), cfg)


@pytest.mark.parametrize("tiers,height", [(2, 60), (3, 90), (5, 160), (6, 200)])
def test_tannenbaum_shapes(cfg, tiers, height):
    asm = tannenbaum.build(cfg, height=height, tiers=tiers)
    rep = assert_cut_ready(asm, cfg)
    a, b = asm.part("tannenbaum_a"), asm.part("tannenbaum_b")
    assert math.isclose(b.bbox()[3], height)               # B trägt die Spitze
    assert a.bbox()[3] < height                             # A ist oben geschlitzt
    assert any("Kreuzschlitz" in e.message for e in rep.entries)


# --- Schneemann ----------------------------------------------------------------------
@pytest.mark.parametrize("T,kerf", MATERIALS)
def test_schneemann_materials(T, kerf):
    cfg = Config(thickness=T, kerf=kerf)
    assert_cut_ready(schneemann.build(cfg), cfg)


def test_schneemann_height(cfg):
    asm = schneemann.build(cfg, height=80)
    fig = asm.part("schneemann_figur")
    assert math.isclose(fig.bbox()[3], 80, abs_tol=1e-6)
    assert math.isclose(fig.bbox()[1], -cfg.T)             # Tab unten


# --- Zaun ------------------------------------------------------------------------------
@pytest.mark.parametrize("T,kerf", MATERIALS)
def test_zaun_materials(T, kerf):
    cfg = Config(thickness=T, kerf=kerf)
    assert_cut_ready(zaun.build(cfg), cfg)


@pytest.mark.parametrize("width", [40, 120, 250])
def test_zaun_lengths(cfg, width):
    asm = zaun.build(cfg, width=width)
    assert_cut_ready(asm, cfg)
    assert asm.params["width"] <= width
    assert len(asm.part("zaun_feld").holes) == asm.params["pickets"] - 1


# --- Laterne -----------------------------------------------------------------------------
@pytest.mark.parametrize("T,kerf", MATERIALS)
def test_laterne_materials(T, kerf):
    cfg = Config(thickness=T, kerf=kerf)
    assert_cut_ready(laterne.build(cfg), cfg)


def test_laterne_engrave_and_bow(cfg):
    asm = laterne.build(cfg, openings="engrave", width=60, height=90)
    assert_cut_ready(asm, cfg)
    assert asm.part("laterne_vorne").holes == []
    assert any(c.a.startswith("laterne_buegel") for c in asm.connections)


# --- Briefkasten ---------------------------------------------------------------------------
@pytest.mark.parametrize("T,kerf", [m for m in MATERIALS if m[0] < 6])
def test_briefkasten_materials(T, kerf):
    cfg = Config(thickness=T, kerf=kerf)
    assert_cut_ready(briefkasten.build(cfg), cfg)


def test_briefkasten_too_small_for_thick_material():
    cfg = Config(thickness=6.0)
    with pytest.raises(ValueError, match="zu klein"):
        briefkasten.build(cfg)
    assert_cut_ready(briefkasten.build(cfg, height=45), cfg)


def test_briefkasten_post_is_rectangular(cfg):
    asm = briefkasten.build(cfg, post=70)
    post = asm.part("briefkasten_pfosten")
    x0, y0, x1, y1 = post.bbox()
    assert math.isclose(y1 - y0, 70 + 2 * cfg.T)
    assert (x1, 0.0) in post.outline and (0.0, 70.0) in post.outline


# --- Wichtel ----------------------------------------------------------------------------------
@pytest.mark.parametrize("T,kerf", MATERIALS)
def test_wichtel_materials(T, kerf):
    cfg = Config(thickness=T, kerf=kerf)
    assert_cut_ready(wichtel.build(cfg), cfg)


@pytest.mark.parametrize("height", [40, 70, 120])
def test_wichtel_sizes(cfg, height):
    asm = wichtel.build(cfg, height=height)
    assert_cut_ready(asm, cfg)
    assert math.isclose(asm.part("wichtel_figur").bbox()[3], height)
