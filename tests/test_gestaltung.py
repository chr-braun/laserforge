"""Gestaltung und Beschriftung: jede Auswahl jeder Liste muss cut-ready bleiben."""
import pytest

from conftest import assert_cut_ready
from laserforge import Config
from models import _deko as dk
from models import briefkasten, fahrzeug, ornament, schneemann, serie, wichtel, wichtelhaus
from models._font import CASES, STYLES, fit_text, normalize, unsupported
import service
from cli import options_text, parse_args, params_from_args

HOUSE_LISTS = [("fenster", dk.WINDOW_FORMS), ("sprossen", dk.MUNTINS), ("fenster_deko", dk.WINDOW_DECO),
               ("tuer_deko", dk.DOOR_DECO), ("giebel", dk.GABLES), ("wand", dk.WALLS), ("dach", dk.ROOFS),
               ("zierleiste", dk.TRIMS), ("schild_form", dk.SIGNS), ("vorplatz", dk.YARDS)]


# --- Schrift ---------------------------------------------------------------------------

@pytest.mark.parametrize("style", STYLES)
@pytest.mark.parametrize("case", CASES)
def test_font_styles_fit_their_box(style, case):
    strokes, cap = fit_text("Frohe Weihnacht ♥|2026", 0, 0, 60, 20, min_h=2.5, max_cap=8, style=style, case=case)
    xs = [x for s in strokes for x, _ in s]
    ys = [y for s in strokes for _, y in s]
    assert max(xs) - min(xs) <= 60 + 1e-6 and max(ys) - min(ys) <= 20 + 1e-6 and cap >= 2.5


def test_font_lowercase_and_symbols():
    assert normalize("Straße", "gross") == "STRAßE"
    assert normalize("Anna", "normal") == "Anna"
    assert unsupported("Wichtel ♥ ★ ❄ 🎄 äöüß 12:30 & (Ö)!") == []
    assert unsupported("€") == ["€"]


def test_wrap_variants():
    assert dk.wrap_variants("Post") == ["Post"]
    assert dk.wrap_variants("Frohes Fest") == ["Frohes Fest", "Frohes|Fest"]
    assert dk.wrap_variants("Anna|2026") == ["Anna|2026"]
    assert len(dk.wrap_variants("Briefe an den Weihnachtsmann")) == 3


# --- Wichtelhaus ---------------------------------------------------------------------------

@pytest.mark.parametrize("key,value", [(k, v) for k, opts in HOUSE_LISTS for v in dk.values(opts)])
def test_every_house_option(cfg, key, value):
    extra = {"giebel_text": "Anno 1890"} if value == "text" else {}
    if key == "vorplatz":
        extra["matte_text"] = "Hallo"
    assert_cut_ready(wichtelhaus.build(cfg, **{key: value}, schild="Willi", **extra), cfg)


@pytest.mark.parametrize("door", dk.values(dk.DOORS))
@pytest.mark.parametrize("openings", ["cut", "engrave"])
def test_every_door_both_modes(door, openings):
    cfg = Config(openings=openings)
    assert_cut_ready(wichtelhaus.build(cfg, door=door, tuer_deko="girlande", schild="Haus ♥"), cfg)


@pytest.mark.parametrize("style", STYLES)
def test_sign_in_every_font_style(cfg, style):
    assert_cut_ready(wichtelhaus.build(cfg, schild="Familie Huber", schrift=style, schreibweise="normal",
                                       text_hinten="Frohe Weihnacht"), cfg)


@pytest.mark.parametrize("T,kerf", [(2.0, 0.1), (4.0, 0.15), (6.0, 0.3)])
def test_rich_house_any_material(T, kerf):
    cfg = Config(thickness=T, kerf=kerf)
    asm = wichtelhaus.build(cfg, width=100, height=75, fenster="bogen", fenster_deko="beides", tuer_deko="vordach",
                            wand="ziegel", dach="biber", zierleiste="lichterkette", giebel="uhr",
                            schild="Zur Post", schild_form="holz", vorplatz="alles", matte_text="Hallo")
    assert_cut_ready(asm, cfg)


def test_sign_too_long_is_a_clear_error(cfg):
    with pytest.raises(ValueError, match="Schild"):
        wichtelhaus.build(cfg, width=45, schild="Weihnachtsmannswerkstatt Nordpol")


def test_unknown_option_names_the_choices(cfg):
    with pytest.raises(ValueError, match="erlaubt"):
        wichtelhaus.build(cfg, fenster="dreieck")
    with pytest.raises(TypeError):
        wichtelhaus.build(cfg, farbe="rot")


# --- Serie ---------------------------------------------------------------------------------

def test_series_random_style_reproducible_and_varied(cfg):
    a = serie.build(cfg, n=5, seed=11, schild="Anna, Ben, Lea")
    b = serie.build(cfg, n=5, seed=11, schild="Anna, Ben, Lea")
    keys = ("fenster", "wand", "dach", "zierleiste", "fenster_deko")
    assert [{k: x.params.get(k) for k in keys} for x in a] == [{k: x.params.get(k) for k in keys} for x in b]
    assert len({tuple(x.params.get(k) for k in keys) for x in a}) >= 3
    assert [x.params.get("schild") for x in a][:3] == ["Anna", "Ben", "Lea"]
    for x in a:
        assert_cut_ready(x, cfg)


def test_series_fixed_style_for_all(cfg):
    for x in serie.build(cfg, n=3, seed=2, fenster="herz", wand="holz"):
        assert x.params.get("fenster") == "herz" and x.params.get("wand") == "holz"


# --- Schmuck ---------------------------------------------------------------------------------

@pytest.mark.parametrize("stil", dk.values(dk.LINE_STYLES))
@pytest.mark.parametrize("shape", ["stern", "kugel", "glocke", "baum"])
def test_ornament_border_styles(cfg, stil, shape):
    assert_cut_ready(ornament.build(cfg, shape=shape, rand_stil=stil, pattern="punkte"), cfg)


@pytest.mark.parametrize("frame", dk.values(dk.SIGNS))
@pytest.mark.parametrize("shape", ["stern", "kugel", "herz", "anhaenger"])
def test_ornament_text_frames(cfg, frame, shape):
    assert_cut_ready(ornament.build(cfg, shape=shape, text="Mia", textrahmen=frame, pattern="herzen"), cfg)


def test_ornament_long_text_wraps_in_frame(cfg):
    asm = ornament.build(cfg, shape="anhaenger", text="Frohes Fest", textrahmen="geschweift")
    assert_cut_ready(asm, cfg)


# --- Fahrzeuge, Briefkasten, Figuren ----------------------------------------------------------

@pytest.mark.parametrize("frame", dk.values(dk.SIGNS))
@pytest.mark.parametrize("vehicle", ["lkw", "lok"])
def test_vehicle_text_frames(cfg, frame, vehicle):
    assert_cut_ready(fahrzeug.build(cfg, vehicle=vehicle, text="Max", textrahmen=frame, schrift="fett"), cfg)


@pytest.mark.parametrize("line", dk.values(dk.TRIMS))
@pytest.mark.parametrize("vehicle", fahrzeug.VEHICLES)
def test_vehicle_trim_lines(cfg, line, vehicle):
    assert_cut_ready(fahrzeug.build(cfg, vehicle=vehicle, zierlinie=line, text="Lisa"), cfg)


@pytest.mark.parametrize("dach", dk.values(dk.ROOFS))
def test_mailbox_roofs_and_name(cfg, dach):
    asm = briefkasten.build(cfg, dach=dach, text="Post", schild_form="rund")
    assert_cut_ready(asm, cfg)
    assert len(asm.part("briefkasten_vorne").engrave) > 3


def test_mailbox_long_name_wraps(cfg):
    assert_cut_ready(briefkasten.build(cfg, width=60, height=45, text="Briefe an den Weihnachtsmann"), cfg)


@pytest.mark.parametrize("mod", [schneemann, wichtel])
@pytest.mark.parametrize("T", [3.0, 6.0])
def test_figure_base_text(mod, T):
    cfg = Config(thickness=T)
    plain = mod.build(cfg)
    named = mod.build(cfg, text="Wichtel Willi ❄", schrift="kursiv")
    assert_cut_ready(named, cfg)
    base = [p for p in named.parts if p.name.endswith("sockel")][0]
    base0 = [p for p in plain.parts if p.name.endswith("sockel")][0]
    assert len(base.engrave) > len(base0.engrave)


# --- Formular, Konfigurator, Kommandozeile -----------------------------------------------------

def test_schema_sections_and_when():
    keys = {p["key"]: p for p in service.MODEL_INFO["wichtelhaus"]["params"]}
    assert keys["fenster"]["section"] == "Fenster und Tür"
    assert keys["giebel_text"]["when"] == {"giebel": ["text"]}
    serie_opts = {p["key"]: p for p in service.MODEL_INFO["serie"]["params"]}
    assert serie_opts["fenster"]["default"] == "zufall"
    for m in service.MODEL_INFO.values():
        for p in m["params"]:
            for k in (p.get("when") or {}):
                assert any(q["key"] == k for q in m["params"]), (p["key"], k)


def test_service_passes_style_options(cfg):
    asms = service.build_assemblies("wichtelhaus", {"fenster": "stern", "schild": "Lea", "door": "rund"}, cfg)
    assert asms[0].params["fenster"] == "stern" and asms[0].params["door"] == "rund"
    with pytest.raises(ValueError, match="nicht erlaubt"):
        service.build_assemblies("wichtelhaus", {"wand": "beton"}, cfg)


def test_cli_option_flags():
    a = parse_args(["--model", "wichtelhaus", "-O", "fenster=herz", "-O", "schild=A=B"])
    assert params_from_args(a) == {"fenster": "herz", "schild": "A=B"}
    with pytest.raises(ValueError, match="gibt es bei"):
        params_from_args(parse_args(["--model", "zaun", "-O", "fenster=herz"]))
    txt = options_text("fahrzeug")
    assert "zierlinie" in txt and "eiszapfen" in txt and "[nur bei vehicle=lkw]" in txt
