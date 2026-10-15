"""
Zierstück – einzelnes Ornament zum Aufkleben oder Aufhängen (Paket „Verzierungen“).
"""
import importlib.util
import math
import os

from steckwerk import Assembly
from pakete import integer, num, sel

_spec = importlib.util.spec_from_file_location("swpaket_verzierungen__paket_zs",
                                               os.path.join(os.path.dirname(os.path.abspath(__file__)), "_paket.py"))
_m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_m)
Z = _m.bibliothek()

ARTEN = ([("rosette_" + k, "Rosette: " + v) for k, v in Z.ROSETTEN] +
         [("ecke_" + k, "Ecke: " + v) for k, v in Z.ECKEN] +
         [("schleife", "Schleife"), ("zweig_tanne", "Tannenzweig"), ("zweig_blatt", "Blätterzweig"),
          ("zweig_beere", "Zweig mit Beeren")])

UEBERSETZUNG = {"en": {
    "Zierstück": "Appliqué", "Verzierungen": "Ornaments",
    "Einzelnes Ornament zum Aufkleben, Aufhängen oder als Vorlage: Rosette, Eckornament, Schleife oder Zweig.":
        "Single ornament to glue on, hang up or use as a template: rosette, corner piece, bow or sprig.",
    "Ornament": "Ornament", "Größe": "Size", "Blätter / Zacken": "Petals / points", "Anzahl": "Quantity",
    "Aufhängung": "Hanger", "keine": "none", "Öse oben": "eyelet on top",
    "Rosette: Blüte": "Rosette: flower", "Rosette: Mandala": "Rosette: mandala", "Rosette: Stern": "Rosette: star",
    "Rosette: Sonne": "Rosette: sun", "Rosette: Schneestern": "Rosette: snow star", "Ecke: Ranke": "Corner: scroll",
    "Ecke: Fächer": "Corner: fan", "Ecke: Herz mit Kringeln": "Corner: heart with curls",
    "Ecke: Blätterzweig": "Corner: leafy sprig", "Ecke: Schnörkel": "Corner: flourish", "Schleife": "Bow",
    "Tannenzweig": "Fir sprig", "Blätterzweig": "Leafy sprig", "Zweig mit Beeren": "Sprig with berries",
    "Mit Holzleim aufkleben. Feine Stücke vorher in Ruhe aus dem Rest lösen.":
        "Glue on with wood glue. Ease delicate pieces out of the sheet gently.",
}}

INFO = dict(
    label="Zierstück", group="Verzierungen",
    desc="Einzelnes Ornament zum Aufkleben, Aufhängen oder als Vorlage: Rosette, Eckornament, Schleife oder Zweig.",
    params=[
        sel("art", "Ornament", ARTEN, "rosette_mandala"),
        num("groesse", "Größe", 60, 20, 200),
        integer("blaetter", "Blätter / Zacken", 8, 4, 16, when={"art": [k for k, _ in ARTEN if k.startswith("rosette_")]}),
        integer("anzahl", "Anzahl", 1, 1, 8),
        sel("aufhaengung", "Aufhängung", [("keine", "keine"), ("oese", "Öse oben")], "keine"),
    ],
)


def figur(art: str, g: float, blaetter: int, w: float):
    if art.startswith("rosette_"):
        return Z.rosette(g / 2, art[8:], blaetter, w)
    if art.startswith("ecke_"):
        return Z.ecke(g, art[5:], w)
    if art == "schleife":
        return Z.schleife(g, w)
    if art.startswith("zweig_"):
        return Z.zweig(g, art[6:], w)
    raise ValueError(f"Unbekanntes Ornament {art!r}")


def build(cfg, name="zierstueck", art="rosette_mandala", groesse=60.0, blaetter=8, anzahl=1, aufhaengung="keine"):
    g = cfg.s(groesse)
    w = Z.wmin(cfg)
    fig = figur(art, g, int(blaetter), w)
    if aufhaengung == "oese":
        x0, y0, x1, y1 = fig.bbox()
        cx = (x0 + x1) / 2
        r_o = 3.4
        fig.add(Z.K.circle(cx, y1 + r_o * 0.55, r_o + w))
        fig.add(Z.K.rect(cx - w, y1 - g * 0.12, 2 * w, g * 0.12 + r_o))
        fig.cut(Z.K.circle(cx, y1 + r_o * 0.55, 1.9))
    notes = []
    asm = Assembly(name, params=dict(art=art, groesse=g, blaetter=blaetter, anzahl=anzahl))
    teil = Z.figur_teil(cfg, f"{name}_1", fig, notes)
    asm.parts.append(teil)
    for k in range(2, int(anzahl) + 1):
        asm.parts.append(teil.transformed(lambda pts: list(pts)))
        asm.parts[-1].name = f"{name}_{k}"
    asm.notes += notes
    asm.notes.append("Mit Holzleim aufkleben. Feine Stücke vorher in Ruhe aus dem Rest lösen.")
    return asm
