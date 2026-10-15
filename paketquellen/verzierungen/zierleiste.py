"""
Zierleiste – Bordüre als Streifen mit gerader Unterkante (Paket „Verzierungen“).
"""
import importlib.util
import os

from steckwerk import Assembly
from pakete import integer, num, sel

_spec = importlib.util.spec_from_file_location("swpaket_verzierungen__paket_zl",
                                               os.path.join(os.path.dirname(os.path.abspath(__file__)), "_paket.py"))
_m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_m)
Z = _m.bibliothek()

UEBERSETZUNG = {"en": {
    "Zierleiste": "Border strip",
    "Bordüre als Streifen mit gerader Unterkante – für Regalkanten, Dachtraufen, Kisten oder Rahmen.":
        "Decorative border strip with a straight bottom edge – for shelf edges, eaves, boxes or frames.",
    "Muster": "Pattern", "Länge": "Length", "Höhe": "Height", "Anzahl": "Quantity",
    "Ranke": "Scroll", "Wellen": "Waves", "Laufender Kringel": "Running curl", "Bogenkante": "Scallops",
    "Zacken": "Points", "Herzen": "Hearts", "Sterne": "Stars", "Perlen": "Beads", "Blätter": "Leaves",
    "Tannen": "Fir trees", "Mäander": "Greek key",
    "Die gerade Unterkante an die Kante kleben, an der die Leiste sitzen soll.":
        "Glue the straight bottom edge along the edge where the strip should sit.",
}}

INFO = dict(
    label="Zierleiste", group="Verzierungen",
    desc="Bordüre als Streifen mit gerader Unterkante – für Regalkanten, Dachtraufen, Kisten oder Rahmen.",
    params=[
        sel("muster", "Muster", Z.BORDUEREN, "ranke"),
        num("laenge", "Länge", 200, 40, 380),
        num("hoehe", "Höhe", 28, 12, 80),
        integer("anzahl", "Anzahl", 1, 1, 6),
    ],
)


def build(cfg, name="zierleiste", muster="ranke", laenge=200.0, hoehe=28.0, anzahl=1):
    L, h = cfg.s(laenge), cfg.s(hoehe)
    if h < 4 * Z.wmin(cfg):
        raise ValueError(f"Die Leiste ist für {cfg.T:g} mm Material zu niedrig – mindestens {4 * Z.wmin(cfg):.0f} mm Höhe")
    notes = []
    teil = Z.figur_teil(cfg, f"{name}_1", Z.bordure(L, h, muster, Z.wmin(cfg)), notes, unten_flach=True)
    asm = Assembly(name, params=dict(muster=muster, laenge=L, hoehe=h, anzahl=anzahl))
    asm.parts.append(teil)
    for k in range(2, int(anzahl) + 1):
        p = teil.transformed(lambda pts: list(pts))
        p.name = f"{name}_{k}"
        asm.parts.append(p)
    asm.notes += notes
    asm.notes.append("Die gerade Unterkante an die Kante kleben, an der die Leiste sitzen soll.")
    return asm
