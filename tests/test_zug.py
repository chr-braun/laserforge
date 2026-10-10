"""Zug-Set, Bus und Traktor."""
import pytest

from conftest import MATERIALS, assert_cut_ready
from steckwerk import Config
from models import fahrzeug
import service

NEW = ["tender", "personenwagen", "gueterwagen", "bus", "traktor"]


@pytest.mark.parametrize("T,kerf", MATERIALS)
@pytest.mark.parametrize("vehicle", NEW)
def test_new_vehicles(T, kerf, vehicle):
    cfg = Config(thickness=T, kerf=kerf)
    assert_cut_ready(fahrzeug.build(cfg, vehicle=vehicle, text="Max"), cfg)


@pytest.mark.parametrize("vehicle", ["lok", "tender", "personenwagen", "gueterwagen"])
def test_coupling_holes(cfg, vehicle):
    with_c = fahrzeug.build(cfg, vehicle=vehicle, kupplung=True)
    without = fahrzeug.build(cfg, vehicle=vehicle, kupplung=False)
    n = sum(len(p.holes) for p in with_c.parts) - sum(len(p.holes) for p in without.parts)
    assert n == (1 if vehicle == "lok" else 2)


def test_tractor_has_big_rear_wheels(cfg):
    asm = fahrzeug.build(cfg, vehicle="traktor")
    r0 = asm.part("rad_0l").bbox()[2]
    r1 = asm.part("rad_1l").bbox()[2]
    assert r0 > 1.5 * r1


def test_train_set(cfg):
    asms = service.build_assemblies("zug", {"wagen": 3, "text": "Polar,,Post"}, cfg)
    assert [a.params["vehicle"] for a in asms] == ["lok", "tender", "personenwagen", "gueterwagen", "personenwagen"]
    assert asms[2].params["text"] == "Post"
    for a in asms:
        assert_cut_ready(a, cfg)
