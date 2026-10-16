"""
service.py – gemeinsame Ablaufschicht für Kommandozeile, Konfigurator und Weboberfläche.

  MODEL_INFO / CONFIG_INFO   Beschreibung aller Modelle und Parameter (daraus bauen sich
                             Web-Formular und Terminal-Konfigurator automatisch)
  build_assemblies()         Modell + Parameter → Baugruppen
  process()                  ALLES validieren, Layout, SVG erzeugen, SVG erneut prüfen
  write_results()            Dateien schreiben (nur wenn alles OK ist)
  zip_results()              dasselbe als ZIP im Speicher (für den Download)
  generate()                 alles zusammen als JSON-fähiges dict (Web-API)
"""
from __future__ import annotations

import inspect
import io
import os
import time
import zipfile
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from steckwerk import (Assembly, Config, ConfigError, LayoutError, Sheet, __version__, layout,
                        sheet_to_svg, write_text)
from models import (ACCESSORIES, MODELS, _deko as dk, fahrzeug, ornament, schneeflocke, schwibbogen, serie,
                    wichtelhaus)
from validator import Report, validate_assembly, validate_sheets, validate_svg_text
import motive as mt
from models import motivvorlagen as mv


# ---------------------------------------------------------------------------
# Parameter-Beschreibung
# ---------------------------------------------------------------------------

def num(key, label, default, lo, hi, step=1.0, unit="mm", help="", **extra):
    return dict(key=key, label=label, type="number", default=default, min=lo, max=hi, step=step,
                unit=unit, help=help, **extra)


def integer(key, label, default, lo, hi, help="", unit="", **extra):
    return dict(key=key, label=label, type="int", default=default, min=lo, max=hi, step=1, unit=unit, help=help,
                **extra)


def sel(key, label, options, default, help="", **extra):
    return dict(key=key, label=label, type="select", default=default,
                options=[dict(value=v, label=l) for v, l in options], help=help, **extra)


def txt(key, label, default="", help="", maxlen=80, **extra):
    return dict(key=key, label=label, type="text", default=default, maxlength=maxlen, help=help, **extra)


def flag(key, label, default, help="", **extra):
    return dict(key=key, label=label, type="bool", default=default, help=help, **extra)


def motiv(key, label, default, help="", **extra):
    """Ein Motiv aus der Motiv-Bibliothek (ID)."""
    return dict(key=key, label=label, type="motiv", default=default, help=help, **extra)


def motive(key, label, default, help="", max_items=12, **extra):
    """Frei platzierte Motive: Liste von {id, x, y, groesse, drehung, spiegeln, art}."""
    return dict(key=key, label=label, type="motive", default=default, max=max_items, help=help,
                arten=[dict(value=v, label=l) for v, l in mv.ARTEN], **extra)


def _pl(mid, x=0.0, y=0.0, groesse=50.0, art="schnitt", drehung=0.0, spiegeln=False):
    return dict(id=mid, x=x, y=y, groesse=groesse, drehung=drehung, spiegeln=spiegeln, art=art)


SEED = integer("seed", "Zufallsstartwert", 7, 0, 99999, "Gleicher Wert = gleiches Ergebnis")

# Abschnitte („section“) erscheinen im Web-Formular als aufklappbare Gruppen und im Konfigurator
# hinter der Frage „Gestaltung anpassen?“. when = {schlüssel: [werte]} → Feld nur dann sichtbar.
FENSTER, WAND, SCHRIFT = "Fenster und Tür", "Wände, Dach und Garten", "Beschriftung"
SYM = "Symbole: ♥ ★ ❄ 🎄"


def font_params(section=SCHRIFT, **when):
    extra = dict(when=when) if when else {}
    return [sel("schrift", "Schriftstil", dk.FONT_STYLES, "normal", section=section, **extra),
            sel("schreibweise", "Schreibweise", dk.FONT_CASES, "gross", section=section, **extra)]


def house_style(random: bool = False) -> list:
    """Gestaltungsoptionen des Wichtelhauses; random=True ergänzt „Zufall je Haus“ (Serie)."""
    def choice(key, label, opts, default, section, help="", **kw):
        if random and key in serie.POOLS:
            return sel(key, label, [(serie.RANDOM, "Zufall je Haus")] + list(opts), serie.RANDOM, help,
                       section=section, **kw)
        return sel(key, label, opts, default, help, section=section, **kw)
    st = wichtelhaus.Style()
    out = []
    if not random:
        out.append(sel("door", "Tür", dk.DOORS, "arched", section=FENSTER))
    out += [choice("tuer_deko", "Türschmuck", dk.DOOR_DECO, st.tuer_deko, FENSTER),
            choice("fenster", "Fensterform", dk.WINDOW_FORMS, st.fenster, FENSTER),
            choice("sprossen", "Sprossen", dk.MUNTINS, st.sprossen, FENSTER),
            choice("fenster_deko", "Fensterschmuck", dk.WINDOW_DECO, st.fenster_deko, FENSTER),
            choice("wand", "Wandgravur", dk.WALLS, st.wand, WAND),
            choice("dach", "Dachgravur", dk.ROOFS, st.dach, WAND),
            choice("zierleiste", "Zierleiste unter dem Dach", dk.TRIMS, st.zierleiste, WAND,
                   "Linie entlang der Traufe – auch auf dem Dach"),
            choice("giebel", "Giebelschmuck", dk.GABLES, st.giebel, WAND),
            txt("giebel_text", "Giebeltext", "", "z. B. Baujahr „Anno 1890“ – " + SYM, 24, section=WAND,
                when={"giebel": ["text"]}, symbols=True),
            sel("vorplatz", "Vorplatz", dk.YARDS, st.vorplatz, "Bodenplatte vor der Tür wird verlängert",
                section=WAND),
            txt("matte_text", "Text auf der Fußmatte", "", "z. B. „Willkommen“", 20, section=WAND,
                when={"vorplatz": ["matte", "alles"]}, symbols=True),
            txt("schild", "Schild über der Tür", "",
                ("Komma = je Haus ein Name (Anna, Ben, …); " if random else "") + "| = neue Zeile – " + SYM,
                120 if random else 40, section=SCHRIFT, symbols=True),
            choice("schild_form", "Schildform", dk.SIGNS, st.schild_form, SCHRIFT),
            txt("text_hinten", "Text auf der Rückwand", "", "z. B. Jahreszahl oder Gruß – " + SYM, 40,
                section=SCHRIFT, symbols=True)]
    return out + font_params()


ORNAMENT_PATTERNS = [("sterne", "Sterne"), ("punkte", "Punkte"), ("streifen", "Streifen"), ("flocken", "Flocken"),
                     ("herzen", "Herzen"), ("tannen", "Tannen"), ("karo", "Karo"), ("wellen", "Wellen"),
                     ("filigran", "Filigran (Durchbrüche)"), ("keins", "keins")]

MODEL_INFO: Dict[str, Dict[str, Any]] = {
    "wichtelhaus": dict(
        label="Wichtelhaus", group="Häuser",
        desc="Haus mit Satteldach, Fenstern, Tür und Kamin; Wände mit Zinken verbunden. "
             "Fenster, Tür, Wand- und Dachgravur, Schilder und Schrift frei gestaltbar.",
        params=[num("width", "Breite (Giebelseite)", 80, 40, 300), num("depth", "Tiefe", 70, 40, 300),
                num("height", "Traufhöhe", 65, 35, 300), num("pitch", "Dachneigung", 45, 25, 60, 1, "°"),
                integer("front_windows", "Fenster vorne", 2, 0, 4),
                integer("side_windows", "Fenster je Seite", 1, 0, 3),
                flag("light", "Lichtloch hinten", True, "Runder Durchbruch für eine LED-Kerze"),
                flag("chimney", "Kamin", True), flag("annex", "Anbau", False)] + house_style()),
    "serie": dict(
        label="Häuser-Serie", group="Häuser",
        desc="Mehrere Wichtelhäuser mit zufälligen, reproduzierbaren Varianten – Gestaltung fest oder je Haus "
             "gewürfelt.",
        params=[integer("n", "Anzahl Häuser", 5, 1, 50), SEED,
                num("width", "Grundbreite", 80, 40, 300), num("depth", "Grundtiefe", 70, 40, 300),
                num("height", "Grundhöhe", 65, 35, 300)] + house_style(random=True)),
    "tannenbaum": dict(label="Tannenbaum", group="Zubehör", desc="Zwei Hälften, über Kreuz gesteckt.",
                       params=[num("height", "Höhe", 110, 50, 400), integer("tiers", "Etagen", 4, 2, 8)]),
    "schneemann": dict(label="Schneemann", group="Zubehör", desc="Figur mit Standsockel – auf Wunsch mit Namen.",
                       params=[num("height", "Höhe", 60, 35, 300),
                               txt("text", "Text auf dem Sockel", "", SYM, 30, section=SCHRIFT, symbols=True)]
                       + font_params()),
    "wichtel": dict(label="Wichtel", group="Zubehör", desc="Wichtelfigur mit Mütze und Standsockel – auf Wunsch "
                    "mit Namen.",
                    params=[num("height", "Höhe", 70, 40, 300),
                            txt("text", "Text auf dem Sockel", "", SYM, 30, section=SCHRIFT, symbols=True)]
                    + font_params()),
    "zaun": dict(label="Zaun", group="Zubehör", desc="Lattenzaun mit Füßen.",
                 params=[num("width", "Länge", 120, 40, 400), num("height", "Höhe", 45, 20, 150)]),
    "laterne": dict(label="Laterne", group="Zubehör", desc="Kleine Laterne mit Fenstern und Bügel.",
                    params=[num("width", "Breite", 50, 35, 200), num("height", "Höhe", 70, 45, 300)]),
    "briefkasten": dict(label="Briefkasten", group="Zubehör", desc="Wichtel-Briefkasten auf Pfosten – mit Namensschild "
                        "und Dachgravur.",
                        params=[num("width", "Breite", 40, 25, 150), num("depth", "Tiefe", 50, 25, 150),
                                num("height", "Höhe Kasten", 32, 20, 150),
                                sel("dach", "Dachgravur", dk.ROOFS, "ziegel", section="Dach"),
                                txt("text", "Namensschild", "", "statt Briefumschlag, z. B. „Post“ – | = neue Zeile – "
                                    + SYM, 40, section=SCHRIFT, symbols=True),
                                sel("schild_form", "Schildform", dk.SIGNS, "rahmen", section=SCHRIFT)]
                        + font_params()),
    "zubehoer": dict(label="Zubehör-Set", group="Zubehör",
                     desc="Tannenbaum, Schneemann, Zaun, Laterne, Briefkasten und Wichtel in Standardgröße.",
                     params=[]),
    "ornament": dict(
        label="Christbaumschmuck", group="Schmuck",
        desc="Anhänger-Konfigurator: Form, Muster, Randstil, Name/Jahr mit Rahmen, Öse – flach oder 3D gesteckt.",
        params=[sel("shape", "Form", [(s, l) for s, l in (
                    ("stern", "Stern"), ("kugel", "Kugel"), ("herz", "Herz"), ("glocke", "Glocke"),
                    ("baum", "Tannenbaum"), ("mond", "Mond"), ("anhaenger", "Anhänger/Schild"),
                    ("lebkuchen", "Lebkuchenmann"), ("stiefel", "Nikolausstiefel"),
                    ("zuckerstange", "Zuckerstange (ohne Text)"), ("geschenk", "Geschenk"), ("kerze", "Kerze"),
                    ("engel", "Engel"), ("zapfen", "Tannenzapfen"), ("schneemann", "Schneemann"),
                    ("schneeflocke", "Schneeflocke"))], "stern"),
                num("size", "Größe (Höhe)", 70, 30, 200),
                sel("pattern", "Muster", ORNAMENT_PATTERNS, "sterne", "Gravur; Filigran = Durchbrüche"),
                txt("text", "Text", "", "Komma = je Name ein Anhänger, | = neue Zeile (z. B. Anna|2026) – " + SYM,
                    symbols=True),
                sel("hanger", "Aufhängung", [("oese", "Öse oben"), ("loch", "Loch")], "oese"),
                flag("rand", "Rand", True),
                sel("rand_stil", "Randstil", dk.LINE_STYLES, "linie", when={"rand": [True]}),
                flag("three_d", "3D gesteckt", False, "Zwei Hälften mit Kreuzschlitz (ohne Text)"),
                integer("count", "Anzahl ohne Text", 1, 1, 30), SEED,
                sel("textrahmen", "Textrahmen", dk.SIGNS, "ohne", "Schild um den Text", section=SCHRIFT)]
               + font_params()),
    "schwibbogen": dict(
        label="Schwibbogen", group="Schmuck",
        desc="Lichterbogen mit Kerzen und Scherenschnitt-Szene (Dorf, Wald, Kirche) – Fenster zum Hinterleuchten.",
        params=[num("width", "Breite", 240, 120, 600),
                sel("szene", "Szene", schwibbogen.SCENES, "dorf"),
                integer("kerzen", "Kerzen", 7, 1, 11),
                flag("fenster", "Fenster ausschneiden", True, "zum Hinterleuchten mit einer Lichterkette"),
                sel("bogen_deko", "Zierlinie auf dem Bogen", schwibbogen.DECOS, "sterne", section="Gestaltung"),
                txt("text", "Text auf der Sockelleiste", "", "z. B. Frohe Weihnacht – " + SYM, 40, section=SCHRIFT,
                    symbols=True)]
               + font_params()),
    "schneeflocke": dict(
        label="Schneeflocken", group="Schmuck",
        desc="Sechszählige Flocken, jede aus ihrem Zufallswert – mit Öse oder 3D gesteckt.",
        params=[num("size", "Durchmesser", 80, 30, 250), integer("count", "Anzahl", 3, 1, 60), SEED,
                flag("three_d", "3D gesteckt", False)]),
    "fahrzeug": dict(
        label="Steckfahrzeug", group="Fahrzeuge",
        desc="Seitenwände + Querteile mit Tabs; Räder drehen auf einer Vierkantachse aus der Platte. "
             "Aufschrift mit Rahmen und Zierlinien.",
        params=[sel("vehicle", "Fahrzeug", [("auto", "Auto"), ("lkw", "Lkw"), ("lok", "Lok"),
                                            ("schlitten", "Schlitten"), ("tender", "Tender (zur Lok)"),
                                            ("personenwagen", "Personenwagen"), ("gueterwagen", "Güterwagen"),
                                            ("bus", "Bus"), ("traktor", "Traktor")], "auto"),
                num("length", "Länge", 120, 80, 400, help="Leer lassen = Standard je Fahrzeug"),
                num("width", "Breite", 60, 30, 250),
                integer("axles", "Achsen", 2, 2, 3, "Lkw mit Tandemachse hinten", when={"vehicle": ["lkw"]}),
                flag("kupplung", "Kupplungslöcher", True, "Lok, Tender und Wagen mit Draht/Schnur verbinden",
                     when={"vehicle": list(fahrzeug.TRAIN)}),
                txt("text", "Aufschrift", "", "Gravur auf beiden Seiten, | = neue Zeile – " + SYM, 40, symbols=True),
                sel("textrahmen", "Textrahmen", dk.SIGNS, "ohne", "Schild um die Aufschrift", section=SCHRIFT),
                ] + font_params() + [
                sel("zierlinie", "Zierlinie", dk.TRIMS, "keine", "Linienstil entlang der Seitenkontur – "
                    "Eiszapfen hängen an den Oberkanten", section="Zierlinien")]),
    "zug": dict(
        label="Zug-Set", group="Fahrzeuge",
        desc="Lok, Tender und Wagen in passender Größe – mit Kupplungslöchern zum Verbinden.",
        params=[num("length", "Länge der Lok", 150, 100, 300, help="Tender und Wagen wachsen mit"),
                num("width", "Breite", 60, 30, 250),
                integer("wagen", "Anzahl Wagen", 2, 0, 6),
                sel("wagentyp", "Wagen", [("gemischt", "abwechselnd"), ("personenwagen", "Personenwagen"),
                                          ("gueterwagen", "Güterwagen")], "gemischt"),
                txt("text", "Aufschriften", "", "mit Komma je Fahrzeug: Lok, Tender, Wagen … – " + SYM, 80,
                    symbols=True),
                sel("textrahmen", "Textrahmen", dk.SIGNS, "ohne", section=SCHRIFT)]
               + font_params() + [
                sel("zierlinie", "Zierlinie", dk.TRIMS, "keine", section="Zierlinien")]),
    "motiv_aufsteller": dict(
        label="Aufsteller", group="Eigene Motive",
        desc="Platte mit Standsockel – Motive aus der Bibliothek frei platzieren: ausschneiden oder gravieren.",
        params=[num("width", "Breite", 120, 40, 400), num("height", "Höhe", 150, 40, 400),
                sel("form", "Form", mv.FORMEN_AUFSTELLER, "bogen"),
                motive("motive", "Motive", [_pl("stern", 0, 8, 62)],
                       "In der Vorschau ziehen; x/y = Abstand zur Mitte in mm"),
                sel("rahmen", "Zierrahmen", dk.TRIMS, "linie", section="Gestaltung"),
                num("schraffur", "Abstand der Flächengravur", 0.3, 0.1, 2.0, 0.05, section="Gestaltung",
                    help="Linienabstand für „flächig gravieren“"),
                txt("text", "Text auf der Platte", "", "unten auf der Platte – " + SYM, 40, section=SCHRIFT,
                    symbols=True),
                txt("sockel_text", "Text auf dem Sockel", "", SYM, 30, section=SCHRIFT, symbols=True)]
               + font_params()),
    "motiv_schild": dict(
        label="Schild", group="Eigene Motive",
        desc="Hängeschild mit Löchern oder Schraublöchern – Motive frei platzieren, Text darunter.",
        params=[num("width", "Breite", 200, 50, 600), num("height", "Höhe", 120, 30, 400),
                sel("form", "Form", mv.FORMEN, "abgerundet"),
                sel("aufhaengung", "Aufhängung", mv.AUFHAENGUNG, "zwei_loecher"),
                motive("motive", "Motive", [_pl("herz", 0, 10, 55)],
                       "In der Vorschau ziehen; x/y = Abstand zur Mitte in mm"),
                sel("rahmen", "Zierrahmen", dk.TRIMS, "doppelt", section="Gestaltung"),
                num("schraffur", "Abstand der Flächengravur", 0.3, 0.1, 2.0, 0.05, section="Gestaltung"),
                txt("text", "Text", "Willkommen", "unten auf dem Schild – | = neue Zeile – " + SYM, 60,
                    section=SCHRIFT, symbols=True)]
               + font_params()),
    "motiv_anhaenger": dict(
        label="Anhänger", group="Eigene Motive",
        desc="Kleiner Anhänger mit Loch – für Geschenke, Schlüssel oder den Baum.",
        params=[num("size", "Größe (Höhe)", 60, 25, 200), sel("form", "Form", mv.FORMEN_ANHAENGER, "rund"),
                motive("motive", "Motive", [_pl("stern", 0, -3, 30)],
                       "In der Vorschau ziehen; x/y = Abstand zur Mitte in mm"),
                sel("rahmen", "Zierrahmen", dk.TRIMS, "linie", section="Gestaltung"),
                num("schraffur", "Abstand der Flächengravur", 0.25, 0.1, 2.0, 0.05, section="Gestaltung"),
                txt("text", "Text", "", "z. B. ein Name – " + SYM, 30, section=SCHRIFT, symbols=True)]
               + font_params()),
    "motiv_untersetzer": dict(
        label="Untersetzer", group="Eigene Motive",
        desc="Untersetzer – Motive standardmäßig flächig graviert.",
        params=[num("size", "Größe", 100, 50, 300), sel("form", "Form", mv.FORMEN_UNTERSETZER, "rund"),
                motive("motive", "Motive", [_pl("herz", 0, 4, 52, "flaeche")],
                       "In der Vorschau ziehen; x/y = Abstand zur Mitte in mm"),
                sel("rahmen", "Zierrahmen", dk.TRIMS, "doppelt", section="Gestaltung"),
                num("schraffur", "Abstand der Flächengravur", 0.3, 0.1, 2.0, 0.05, section="Gestaltung"),
                txt("text", "Text", "", SYM, 30, section=SCHRIFT, symbols=True)]
               + font_params()),
    "motiv_silhouette": dict(
        label="Silhouette", group="Eigene Motive",
        desc="Das Motiv selbst wird zum Teil – als Figur im Sockel, mit Öse zum Aufhängen oder als freie Form.",
        params=[motiv("motiv", "Motiv", "katze"), num("size", "Größe (längere Seite)", 120, 25, 400),
                sel("fuss", "Fuß", mv.FUSS, "sockel"), sel("innen", "Innenformen", mv.INNEN, "schnitt"),
                txt("sockel_text", "Text auf dem Sockel", "", SYM, 30, section=SCHRIFT, symbols=True,
                    when={"fuss": ["sockel"]})]
               + font_params(fuss=["sockel"])),
    "alle": dict(label="Alle Modelle", group="Komplett", desc="Jedes Modell in Standardgröße – gut als Testlauf "
                 "für neue Material- und Kerf-Einstellungen.", params=[]),
}

VEHICLE_DEFAULTS = {k: dict(length=v["length"], width=v["width"]) for k, v in fahrzeug.DEFAULTS.items()}

CONFIG_INFO = [
    num("thickness", "Materialstärke T", 3.0, 0.5, 20, 0.1),
    num("kerf", "Kerf (Schnittbreite)", 0.2, 0.0, 1.0, 0.01, help="CO2 meist 0.1–0.2, Diode 0.15–0.3"),
    num("scale", "Maßstab", 1.0, 0.2, 5, 0.05, ""),
    sel("openings", "Fenster/Türen", [("cut", "ausschneiden"), ("engrave", "gravieren")], "cut"),
    num("sheet_width", "Platte Breite", 400, 50, 2000, 1),
    num("sheet_height", "Platte Höhe", 300, 50, 2000, 1),
    txt("cut_color", "Farbe Schnitt", "#000000", "LightBurn-Layer 00"),
    txt("engrave_color", "Farbe Gravur", "#0000FF", "LightBurn-Layer 01"),
]


def coerce(info: Dict[str, Any], value: Any) -> Any:
    """Wert gegen die Parameterbeschreibung prüfen und umwandeln (None = Standard)."""
    if value is None or value == "":
        return None
    t, label = info["type"], info["label"]
    if t == "motiv":
        v = str(value)
        if not mt.exists(v):
            raise ValueError(f"{label}: Motiv {v!r} gibt es nicht – in der Motiv-Bibliothek wählen")
        return v
    if t == "motive":
        return coerce_motive(info, value)
    if t == "bool":
        if isinstance(value, str):
            return value.strip().lower() in ("1", "true", "ja", "yes", "on", "j", "y")
        return bool(value)
    if t == "select":
        v = str(value)
        if v not in [o["value"] for o in info["options"]]:
            raise ValueError(f"{label}: {v!r} nicht erlaubt – wähle {', '.join(o['value'] for o in info['options'])}")
        return v
    if t == "text":
        v = str(value)
        if len(v) > info.get("maxlength", 200):
            raise ValueError(f"{label}: höchstens {info['maxlength']} Zeichen")
        return v
    try:
        f = float(str(value).replace(",", ".")) if isinstance(value, str) else float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{label}: {value!r} ist keine Zahl")
    if f != f or f in (float("inf"), float("-inf")):
        raise ValueError(f"{label}: {value!r} ist keine Zahl")
    if t == "int":
        if f != int(f):
            raise ValueError(f"{label}: bitte eine ganze Zahl")
        v = int(f)
    else:
        v = f
    if v < info["min"] or v > info["max"]:
        raise ValueError(f"{label}: {v:g} liegt außerhalb {info['min']:g}–{info['max']:g} {info.get('unit', '')}".rstrip())
    return v


def coerce_motive(info: Dict[str, Any], value: Any) -> List[Dict[str, Any]]:
    """Platzierungsliste prüfen (auch als JSON-Text von der Kommandozeile)."""
    import json
    label = info["label"]
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except ValueError:
            raise ValueError(f"{label}: erwartet eine Liste wie "
                             '[{"id": "stern", "x": 0, "y": 0, "groesse": 50, "art": "schnitt"}]')
    if isinstance(value, dict):
        value = [value]
    if not isinstance(value, list):
        raise ValueError(f"{label}: erwartet eine Liste von Motiven")
    if len(value) > info.get("max", 12):
        raise ValueError(f"{label}: höchstens {info.get('max', 12)} Motive")
    out = []
    for i, it in enumerate(value, 1):
        if not isinstance(it, dict):
            raise ValueError(f"{label} {i}: ungültiger Eintrag")
        mid = str(it.get("id", ""))
        if not mt.exists(mid):
            raise ValueError(f"Motiv {i}: {mid!r} gibt es nicht (mehr) – in der Motiv-Bibliothek neu wählen")

        def f(k, d, lo, hi):
            v = it.get(k, d)
            try:
                v = float(str(v).replace(",", ".")) if isinstance(v, str) else float(v)
            except (TypeError, ValueError):
                raise ValueError(f"Motiv {i}: {k}={it.get(k)!r} ist keine Zahl")
            if v != v or not lo <= v <= hi:
                raise ValueError(f"Motiv {i}: {k} muss zwischen {lo:g} und {hi:g} liegen")
            return v
        art = str(it.get("art", "schnitt"))
        if art not in mv.ART_KEYS:
            raise ValueError(f"Motiv {i}: Art {art!r} unbekannt – erlaubt: {', '.join(mv.ART_KEYS)}")
        sp = it.get("spiegeln", False)
        out.append(dict(id=mid, x=f("x", 0, -2000, 2000), y=f("y", 0, -2000, 2000), groesse=f("groesse", 50, 3, 2000),
                        drehung=f("drehung", 0, -360, 360),
                        spiegeln=sp if isinstance(sp, bool) else str(sp).lower() in ("1", "true", "ja"), art=art))
    return out


def make_config(values: Optional[Dict[str, Any]] = None, base: Optional[Config] = None) -> Config:
    cfg = base or Config()
    over = {}
    for info in CONFIG_INFO:
        v = coerce(info, (values or {}).get(info["key"]))
        if v is not None:
            over[info["key"]] = v
    return cfg.updated(**over)


def clean_params(model: str, params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if model not in MODEL_INFO:
        raise ValueError(f"Unbekanntes Modell {model!r} – erlaubt: {', '.join(MODEL_INFO)}")
    out = {}
    for info in MODEL_INFO[model]["params"]:
        v = coerce(info, (params or {}).get(info["key"]))
        if v is not None:
            out[info["key"]] = v
    return out


# ---------------------------------------------------------------------------
# Modelle bauen
# ---------------------------------------------------------------------------

def call_build(module, cfg: Config, **kw):
    """Nur die Parameter übergeben, die das Modell kennt (bei **style auch dessen STYLE_KEYS)."""
    sig = inspect.signature(module.build).parameters
    extra = set(getattr(module, "STYLE_KEYS", ())) if any(
        p.kind is inspect.Parameter.VAR_KEYWORD for p in sig.values()) else set()
    return module.build(cfg, **{k: v for k, v in kw.items() if (k in sig or k in extra) and v is not None})


def call_fn(fn, cfg: Config, **kw):
    sig = inspect.signature(fn).parameters
    return fn(cfg, **{k: v for k, v in kw.items() if k in sig and v is not None})


VORLAGEN = {"motiv_aufsteller": mv.build_aufsteller, "motiv_schild": mv.build_schild,
            "motiv_anhaenger": mv.build_anhaenger, "motiv_untersetzer": mv.build_untersetzer,
            "motiv_silhouette": mv.build_silhouette}


def design(req: Dict[str, Any]) -> Dict[str, Any]:
    """Grundform eines Vorlagen-Modells ohne Motive (für den Platzierungs-Editor der Weboberfläche).
    Koordinaten wie im Modell; (cx, cy) ist der Bezugspunkt der Motive (Mitte der Grundform)."""
    model = str(req.get("model", ""))
    if model not in VORLAGEN or model == "motiv_silhouette":
        return dict(ok=False, error="Kein Vorlagen-Modell")
    cfg = make_config(req.get("config"))
    p = clean_params(model, req.get("params"))
    p["motive"] = []
    asm = call_fn(VORLAGEN[model], cfg, **p)
    part = asm.parts[0]
    ys = [y for _, y in part.outline]
    xs = [x for x, _ in part.outline]
    top = max(ys)
    h_ref = {"motiv_aufsteller": p.get("height", 150.0), "motiv_schild": p.get("height", 120.0),
             "motiv_untersetzer": p.get("size", 100.0)}.get(model)
    if h_ref is None:                                            # Anhänger: Höhe = size
        h_ref = p.get("size", 60.0)
    r = lambda pts: [[round(x, 2), round(y, 2)] for x, y in pts]     # noqa: E731
    return dict(ok=True, cx=0.0, cy=cfg.s(h_ref) / 2, outline=r(part.outline), holes=[r(h) for h in part.holes],
                engrave=[dict(pts=r(s.points), closed=s.closed) for s in part.engrave],
                bbox=[min(xs), min(ys), max(xs), top])


def zug(cfg: Config, length: Optional[float] = None, width: Optional[float] = None, wagen: int = 2,
        wagentyp: str = "gemischt", text: str = "", **look) -> List[Assembly]:
    """Lok + Tender + Wagen, alle im Maßstab der Lok, mit Kupplungslöchern."""
    k = (length or 150.0) / 150.0
    W = width or 60.0
    kinds = ["lok", "tender"] + [("personenwagen", "gueterwagen")[i % 2] if wagentyp == "gemischt" else wagentyp
                                 for i in range(int(wagen))]
    names = [t.strip() for t in text.split(",")] if text else []
    out = []
    for i, v in enumerate(kinds):
        L = fahrzeug.DEFAULTS[v]["length"] * k
        out.append(call_build(fahrzeug, cfg, name=f"zug_{i + 1:02d}_{v}", vehicle=v, length=L,
                              width=min(W, 0.8 * L), text=names[i] if i < len(names) else "", kupplung=True,
                              **look))
    return out


def build_assemblies(model: str, params: Optional[Dict[str, Any]], cfg: Config) -> List[Assembly]:
    p = clean_params(model, params)
    if model == "serie":
        return serie.build(cfg, n=p.pop("n", 5), seed=p.pop("seed", None), **p)
    if model == "fahrzeug":
        v = p.get("vehicle", "auto")
        if p.get("length") is None and p.get("width") is None:
            p.update(VEHICLE_DEFAULTS[v])
        return [call_build(fahrzeug, cfg, name=v, **p)]
    if model == "zug":
        return zug(cfg, **p)
    if model == "schneeflocke":
        return [call_build(schneeflocke, cfg, **p)]
    if model == "ornament":
        return [call_build(ornament, cfg, **p)]
    if model in MODELS:
        res = call_build(MODELS[model], cfg, **p)
        return list(res) if isinstance(res, (list, tuple)) else [res]
    if model in VORLAGEN:
        for info in MODEL_INFO[model]["params"]:              # Motiv-Standardwerte auch ohne Formular
            if info["type"] in ("motiv", "motive") and info["key"] not in p:
                p[info["key"]] = info["default"]
        return [call_fn(VORLAGEN[model], cfg, **p)]
    if model == "zubehoer":
        return [call_build(MODELS[x], cfg) for x in ACCESSORIES]
    if model == "alle":
        return ([call_build(MODELS["wichtelhaus"], cfg)] + [call_build(MODELS[x], cfg) for x in ACCESSORIES] +
                serie.build(cfg, n=3) + [ornament.build(cfg), schneeflocke.build(cfg, count=3)] +
                [fahrzeug.build(cfg, name=v, vehicle=v) for v in fahrzeug.VEHICLES])
    raise ValueError(f"Unbekanntes Modell {model!r}")


# ---------------------------------------------------------------------------
# Prüfen, Layout, SVG
# ---------------------------------------------------------------------------

@dataclass
class Result:
    asm: Assembly
    report: Report
    sheets: List[Sheet] = field(default_factory=list)
    svgs: List[Tuple[Sheet, str, str]] = field(default_factory=list)      # (blatt, dateiname, svg)
    preview: List[Tuple[Sheet, str, str]] = field(default_factory=list)   # ungeprüfte Ansicht bei Fehlern

    @property
    def ok(self) -> bool:
        return self.report.passed


def process(assemblies: List[Assembly], cfg: Config, preview_on_error: bool = False) -> Tuple[List[Result], bool]:
    """Geometrie, Verbindungen, Layout und das fertige SVG prüfen. Dateien entstehen hier keine."""
    results = []
    all_ok = True
    for asm in assemblies:
        rep = Report(asm.name)
        validate_assembly(asm, cfg, rep)
        res = Result(asm, rep)
        try:
            res.sheets = layout([p.compensated(cfg.kerf_offset) for p in asm.parts], cfg)
            validate_sheets(res.sheets, cfg, rep)
        except LayoutError as e:
            rep.error("Layout", str(e))
        for sh in res.sheets:
            suffix = "" if len(res.sheets) == 1 else f"_blatt{sh.index}"
            fname = f"{asm.name}{suffix}.svg"
            if rep.passed:
                meta = {"model": asm.name, "params": asm.params, "sheet": f"{sh.index}/{len(res.sheets)}",
                        "validation": "OK"}
                text = sheet_to_svg(sh, cfg, f"Steckwerk – {asm.name}{suffix}", meta)
                validate_svg_text(text, cfg, fname, rep)
                res.svgs.append((sh, fname, text))
            elif preview_on_error:
                res.preview.append((sh, fname, sheet_to_svg(sh, cfg, f"UNGEPRÜFT – {asm.name}{suffix}")))
        if not rep.passed:
            res.svgs = []
        all_ok &= rep.passed
        results.append(res)
    return results, all_ok


def report_text(res: Result, cfg: Config) -> str:
    notes = "\n".join(f"- {n}" for n in res.asm.notes)
    return (f"Steckwerk {__version__} – {res.asm.name}\nParameter: {res.asm.params}\n"
            f"Config: {cfg.to_dict()}\n\n{res.report.text()}\nMontage:\n{notes}\n")


def write_results(results: List[Result], cfg: Config, out: str, preview: bool = False) -> Tuple[List[str], Optional[bool]]:
    if not all(r.ok for r in results):
        raise RuntimeError("Validierung fehlgeschlagen – es wird keine Datei geschrieben")
    written: List[str] = []
    preview_ok = None
    for res in results:
        d = os.path.join(out, res.asm.name)
        os.makedirs(d, exist_ok=True)
        for sh, fname, text in res.svgs:
            path = os.path.join(d, fname)
            write_text(path, text)
            written.append(path)
            if preview:
                from preview import render_sheet
                png = render_sheet(sh, cfg, path[:-4] + ".png",
                                   f"{fname[:-4]} – T={cfg.T} mm, Kerf={cfg.kerf} mm – validiert OK")
                preview_ok = bool(png)
                if png:
                    written.append(png)
        write_text(os.path.join(d, "pruefbericht.txt"), report_text(res, cfg))
        written.append(os.path.join(d, "pruefbericht.txt"))
    return written, preview_ok


def zip_results(results: List[Result], cfg: Config) -> bytes:
    if not all(r.ok for r in results):
        raise RuntimeError("Validierung fehlgeschlagen – kein Download")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for res in results:
            for _, fname, text in res.svgs:
                z.writestr(f"{res.asm.name}/{fname}", text)
            z.writestr(f"{res.asm.name}/pruefbericht.txt", report_text(res, cfg))
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Web-API
# ---------------------------------------------------------------------------

def schema() -> Dict[str, Any]:
    groups: List[str] = []
    for m in MODEL_INFO.values():
        if m["group"] not in groups:
            groups.append(m["group"])
    paks = [dict(id=m.get("id"), name=m.get("name", m.get("id")), version=m.get("version", ""),
                 autor=m.get("autor", ""), modelle=m.get("modelle", []), fehler=err, ersatz=m.get("_ersatz"),
                 name_en=m.get("name_en", ""), beschreibung=m.get("beschreibung", ""),
                 beschreibung_en=m.get("beschreibung_en", ""),
                 schluessel=[k for k, i in MODEL_INFO.items() if (i.get("paket") or {}).get("id") == m.get("id")])
            for _, m, err in PAKETE]
    return dict(version=__version__, groups=groups, models=MODEL_INFO, config=CONFIG_INFO,
                motive=[mt.summary(m) for m in mt.library()], motive_ordner=mt.user_dir(),
                vehicle_defaults=VEHICLE_DEFAULTS, pakete=paks, pakete_ordner=pakete.install_dir())


def run_request(req: Dict[str, Any], preview_on_error: bool = True) -> Tuple[List[Result], Config]:
    cfg = make_config(req.get("config"))
    assemblies = build_assemblies(str(req.get("model", "wichtelhaus")), req.get("params"), cfg)
    results, _ = process(assemblies, cfg, preview_on_error=preview_on_error)
    return results, cfg


def generate(req: Dict[str, Any]) -> Dict[str, Any]:
    """Anfrage {model, params, config} → Ergebnis mit Prüfbericht und SVGs (nur wenn OK)."""
    t0 = time.time()
    try:
        results, cfg = run_request(req)
    except (ConfigError, ValueError) as e:
        return dict(ok=False, error=str(e), assemblies=[], elapsed=round(time.time() - t0, 2))
    out = []
    for res in results:
        sheets = res.svgs if res.ok else res.preview
        out.append(dict(
            name=res.asm.name, ok=res.ok, summary=res.report.summary(), report=res.report.text(),
            notes=list(res.asm.notes), params={k: v for k, v in res.asm.params.items()},
            parts=len(res.asm.parts), joints=len(res.asm.connections),
            errors=[e.line() for e in res.report.errors][:50],
            sheets=[dict(file=f, svg=t, width=sh.width, height=sh.height, parts=len(sh.parts), checked=res.ok)
                    for sh, f, t in sheets]))
    return dict(ok=all(r.ok for r in results), assemblies=out, elapsed=round(time.time() - t0, 2),
                config=cfg.to_dict())


# --- Erweiterungspakete ---------------------------------------------------------------------------
import pakete  # noqa: E402

PAKETE = pakete.register(MODEL_INFO, MODELS)


def reload_pakete():
    """Pakete neu einlesen (nach Installieren/Entfernen)."""
    global PAKETE
    PAKETE = pakete.register(MODEL_INFO, MODELS)
    return PAKETE
