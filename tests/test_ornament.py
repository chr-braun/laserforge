"""Christbaumschmuck-Konfigurator."""
import pytest

from conftest import MATERIALS, assert_cut_ready
from laserforge import Config
from models import ornament
from models.ornament import PATTERNS, SHAPES

FLAT = [s for s in SHAPES if s != "schneeflocke"]


@pytest.mark.parametrize("shape", FLAT)
@pytest.mark.parametrize("pattern", PATTERNS)
def test_every_shape_and_pattern(cfg, shape, pattern):
    assert_cut_ready(ornament.build(cfg, shape=shape, pattern=pattern), cfg)


@pytest.mark.parametrize("T,kerf", MATERIALS)
@pytest.mark.parametrize("shape", ["stern", "kugel", "herz", "glocke"])
def test_materials(T, kerf, shape):
    cfg = Config(thickness=T, kerf=kerf)
    assert_cut_ready(ornament.build(cfg, shape=shape, pattern="filigran", text="Lea"), cfg)


def test_names_make_one_part_each(cfg):
    asm = ornament.build(cfg, shape="herz", pattern="punkte", text="Anna, Ben,Jörg|2026")
    assert [p.name for p in asm.parts] == ["herz_anna", "herz_ben", "herz_joerg_2026"]
    rep = assert_cut_ready(asm, cfg)
    assert rep.passed


def test_hanger_and_border_options(cfg):
    a = ornament.build(cfg, shape="kugel", hanger="loch", rand=False, pattern="keins")
    b = ornament.build(cfg, shape="kugel", hanger="oese", rand=True, pattern="keins")
    assert_cut_ready(a, cfg)
    assert_cut_ready(b, cfg)
    assert b.parts[0].bbox()[3] > a.parts[0].bbox()[3]       # Öse ragt über die Kugel
    assert len(b.parts[0].engrave) > len(a.parts[0].engrave)  # Randlinie


@pytest.mark.parametrize("shape", ["stern", "kugel", "herz", "glocke", "baum", "anhaenger"])
def test_3d_halves_are_connected(cfg, shape):
    asm = ornament.build(cfg, shape=shape, pattern="sterne", three_d=True, count=2)
    assert len(asm.parts) == 4 and len(asm.connections) == 2
    rep = assert_cut_ready(asm, cfg)
    assert any("Kreuzschlitz" in e.message for e in rep.entries)


def test_invalid_combinations(cfg):
    with pytest.raises(ValueError):
        ornament.build(cfg, shape="mond", three_d=True)
    with pytest.raises(ValueError):
        ornament.build(cfg, shape="stern", text="Anna", three_d=True)
    with pytest.raises(ValueError):
        ornament.build(cfg, shape="raute")
    with pytest.raises(ValueError):
        ornament.build(cfg, shape="stern", text="Name mit €")
    with pytest.raises(ValueError, match="Schrifthöhe"):
        ornament.build(cfg, shape="stern", size=40, text="Ein sehr langer Name für einen kleinen Stern")


def test_snowflake_shape_delegates(cfg):
    asm = ornament.build(cfg, shape="schneeflocke", count=2)
    assert len(asm.parts) == 2
    assert_cut_ready(asm, cfg)


@pytest.mark.parametrize("T", [1.5, 4.0, 6.0])
@pytest.mark.parametrize("size", [30, 200])
@pytest.mark.parametrize("shape", ["herz", "glocke", "kugel"])
@pytest.mark.parametrize("hanger", ["oese", "loch"])
def test_extreme_sizes(T, size, shape, hanger):
    """Grenzfälle aus dem Großtest: kleines Herz mit Loch, Glocken-Öse, großes Filigran."""
    cfg = Config(thickness=T, kerf=0.2)
    assert_cut_ready(ornament.build(cfg, shape=shape, size=size, pattern="filigran", hanger=hanger), cfg)


NEW_SHAPES = ["lebkuchen", "stiefel", "zuckerstange", "geschenk", "kerze", "engel", "zapfen", "schneemann"]


@pytest.mark.parametrize("shape", [s for s in NEW_SHAPES if s != "zuckerstange"])
@pytest.mark.parametrize("hanger", ["oese", "loch"])
def test_new_shapes_with_text(cfg, shape, hanger):
    asm = ornament.build(cfg, shape=shape, text="Lea|2026", hanger=hanger, pattern="sterne")
    assert_cut_ready(asm, cfg)


@pytest.mark.parametrize("shape", NEW_SHAPES)
@pytest.mark.parametrize("size", [30, 200])
def test_new_shapes_sizes(shape, size):
    cfg = Config(thickness=3.0, kerf=0.2)
    for hanger in ("oese", "loch"):
        assert_cut_ready(ornament.build(cfg, shape=shape, size=size, pattern="filigran", hanger=hanger), cfg)


def test_new_shapes_have_deco(cfg):
    plain = ornament.build(cfg, shape="lebkuchen", pattern="keins", rand=False)
    assert len(plain.parts[0].engrave) >= 5          # Augen, Mund, Knöpfe


@pytest.mark.parametrize("shape", ["lebkuchen", "engel", "zapfen", "schneemann"])
def test_new_shapes_3d(cfg, shape):
    assert_cut_ready(ornament.build(cfg, shape=shape, three_d=True), cfg)


@pytest.mark.parametrize("shape", ["stiefel", "zuckerstange", "kerze", "geschenk"])
def test_new_shapes_without_3d(cfg, shape):
    with pytest.raises(ValueError, match="3D"):
        ornament.build(cfg, shape=shape, three_d=True)


def test_candy_cane_has_no_text(cfg):
    with pytest.raises(ValueError, match="Platz"):
        ornament.build(cfg, shape="zuckerstange", text="Max")
