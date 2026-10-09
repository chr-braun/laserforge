"""Serien-Funktion."""
from conftest import assert_cut_ready
from laserforge import Config
from models import serie


def test_series_all_cut_ready(cfg):
    houses = serie.build(cfg, n=5)
    assert len(houses) == 5
    for h in houses:
        assert_cut_ready(h, cfg)


def test_series_varies_architecture(cfg):
    houses = serie.build(cfg, n=5, seed=3)
    pitches = {h.params["pitch_deg"] for h in houses}
    assert len(pitches) == 5                                  # jede Dachneigung anders
    assert any(h.params["annex"] for h in houses)
    assert houses[0].params["chimney"]
    assert len({h.params["W"] for h in houses}) > 1


def test_series_is_reproducible(cfg):
    a = [h.params for h in serie.build(cfg, n=4, seed=11)]
    b = [h.params for h in serie.build(cfg, n=4, seed=11)]
    c = [h.params for h in serie.build(cfg, n=4, seed=12)]
    assert a == b and a != c


def test_series_robust_over_many_seeds():
    for seed in range(15):
        cfg = Config(seed=seed)
        for h in serie.build(cfg, n=3):
            assert_cut_ready(h, cfg)
