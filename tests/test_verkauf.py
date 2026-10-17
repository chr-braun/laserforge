"""Paket „Verkauf“ (ab 2.8.0): Flaschen-Preisschilder."""
import os

import pytest

import pakete
from steckwerk import Config
from conftest import assert_cut_ready
from models._font import unsupported

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_, MODS = pakete.load_folder(os.path.join(HERE, "paketquellen", "verkauf"))
FS = MODS["flaschenschild"]


def test_preise_formatieren():
    assert FS.euro(12.9) == "12,90 €"
    assert FS.euro(1234.5) == "1.234,50 €"
    assert FS.liter(0.75) == "0,75 l"
    assert FS.liter(1) == "1,0 l"
    assert unsupported("12,90 € · 19 % MwSt.") == []


def test_preisliste_lesen():
    p = FS.produkte("x", 1.0, 0.75, "Grauburgunder 2023; 14,50; 0,75\nSekt; 11,90\nBrand; 1.024,90 €; 500\n\n")
    assert p == [("Grauburgunder 2023", 14.5, 0.75), ("Sekt", 11.9, 0.75), ("Brand", 1024.9, 0.5)]
    with pytest.raises(ValueError, match="Zeile 1"):
        FS.produkte("x", 1.0, 0.75, "Riesling 12,90")
    with pytest.raises(ValueError, match="keine Zahl"):
        FS.produkte("x", 1.0, 0.75, "Riesling; zwölf")


@pytest.mark.parametrize("form", [f for f, _ in FS.FORMEN])
@pytest.mark.parametrize("logo,art", [("motiv", "flaeche"), ("motiv", "umriss"), ("motiv", "schnitt"),
                                      ("text", "flaeche"), ("kein", "flaeche")])
@pytest.mark.parametrize("halterung", ["hals", "kordel"])
def test_schilder_cut_ready(form, logo, art, halterung):
    cfg = Config(thickness=3.0)
    asm = FS.build(cfg, form=form, logo=logo, logo_art=art, halterung=halterung)
    assert_cut_ready(asm, cfg)
    assert asm.parts[0].engrave


def test_preisliste_ergibt_ein_schild_je_produkt():
    cfg = Config(thickness=2.0)
    asm = FS.build(cfg, liste="Grauburgunder 2023; 14,50; 0,75\nWinzersekt brut; 11,90; 0,75\nTresterbrand; 24,90; 0,5")
    assert [p.name for p in asm.parts] == ["grauburgunder_2023", "winzersekt_brut", "tresterbrand"]
    assert_cut_ready(asm, cfg)


def test_halsloch_zu_gross():
    with pytest.raises(ValueError, match="mindestens"):
        FS.build(Config(thickness=3.0), hals=45, breite=50)
