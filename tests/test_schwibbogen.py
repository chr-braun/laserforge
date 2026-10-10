"""Schwibbogen: jede Szene, Kerzenzahl, Zierlinie und Materialstärke muss cut-ready sein."""
import pytest

from conftest import MATERIALS, assert_cut_ready
from steckwerk import Config
from models import _deko as dk
from models import schwibbogen
import service


@pytest.mark.parametrize("szene", dk.values(schwibbogen.SCENES))
@pytest.mark.parametrize("kerzen", [1, 4, 7, 11])
def test_scenes_and_candles(cfg, szene, kerzen):
    asm = schwibbogen.build(cfg, szene=szene, kerzen=kerzen)
    assert_cut_ready(asm, cfg)
    assert len(asm.parts) == 2 and len(asm.connections) == 2


@pytest.mark.parametrize("deko", dk.values(schwibbogen.DECOS))
def test_arch_decorations(cfg, deko):
    assert_cut_ready(schwibbogen.build(cfg, bogen_deko=deko, text="Frohe Weihnacht"), cfg)


@pytest.mark.parametrize("T,kerf", MATERIALS)
@pytest.mark.parametrize("width", [120, 240, 360])
def test_materials_and_sizes(T, kerf, width):
    cfg = Config(thickness=T, kerf=kerf)
    assert_cut_ready(schwibbogen.build(cfg, width=width, szene="kirche", text="Anno|2026"), cfg)


def test_windows_optional(cfg):
    with_w = schwibbogen.build(cfg, fenster=True).parts[0]
    without = schwibbogen.build(cfg, fenster=False).parts[0]
    assert len(with_w.holes) > len(without.holes) == 1


def test_invalid(cfg):
    with pytest.raises(ValueError, match="Szene"):
        schwibbogen.build(cfg, szene="stadt")
    with pytest.raises(ValueError, match="Kerzen"):
        schwibbogen.build(cfg, kerzen=15)


def test_service(cfg):
    asms = service.build_assemblies("schwibbogen", {"szene": "wald", "kerzen": 5}, cfg)
    assert asms[0].params["szene"] == "wald"
