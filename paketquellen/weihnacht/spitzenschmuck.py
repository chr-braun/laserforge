"""
Spitzenschmuck – Christbaumschmuck mit durchbrochenen Spitzenmustern.

Kugel, Stern, Herz, Glocke oder Zwiebel, gefüllt mit Mandala, Ranken, Klöppelspitze, Eiskristall oder
Stern im Stern. Alles zwischen den Stegen wird ausgeschnitten. Stege und Schlitze werden für den Laser
geprüft und wo nötig verbreitert; was keinen Halt hätte, entfällt. Auf Wunsch zwei Teile zum Stecken
über Kreuz (3D).
"""
from __future__ import annotations

import math
import os
import sys
from typing import List

from steckwerk import Assembly, JointFeature, Part, oriented, rect
from pakete import bibliothek, flag, integer, num, sel, txt

_here = os.path.dirname(os.path.abspath(__file__))


def _sub(name: str):
    import importlib.util
    path = os.path.join(_here, name + ".py")
    key = "swpaket_filigran_" + name
    mod = sys.modules.get(key)
    if mod is None or getattr(mod, "__file__", None) != path:
        spec = importlib.util.spec_from_file_location(key, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[key] = mod
        spec.loader.exec_module(mod)
    return mod


E = bibliothek("verzierungen").E
FG = _sub("_filigran")
K = E.K

FEINHEIT = [("fein", "fein (für 1,5–2 mm Holz)"), ("mittel", "mittel"), ("kraeftig", "kräftig (für 4 mm)")]
ZAHL = [("6", "6-fach"), ("8", "8-fach"), ("12", "12-fach")]

INFO = dict(
    label="Spitzenschmuck",
    group="Weihnachten",
    desc="Christbaumschmuck mit durchbrochener Spitze: Kugel, Stern, Herz, Glocke oder Zwiebel mit Mandala, "
         "Ranken, Klöppelspitze, Eiskristall oder Stern im Stern – auf Wunsch zum Stecken über Kreuz.",
    params=[
        sel("form", "Form", FG.FORMEN, "kugel"),
        sel("muster", "Muster", FG.MUSTER_LISTE, "mandala"),
        txt("rezept", "Rezept", "blüten, perlen, bögen",
            "Bausteine von innen nach außen, mit Komma: blüten, bögen, speichen, zickzack, perlen, ranken, "
            "sterne, tropfen, herzen", when={"muster": ["rezept"]}),
        integer("startwert", "Startwert", 1, 1, 9999, when={"muster": ["zufall"]}),
        num("groesse", "Höhe", 80, 50, 200),
        sel("zaehlig", "Symmetrie", ZAHL, "8", help="beim Stern immer 5- oder 10-fach"),
        sel("feinheit", "Feinheit", FEINHEIT, "mittel"),
        flag("doppelrand", "Doppelter Rand", True),
        flag("steckbar", "3D: zwei Teile über Kreuz", False),
        integer("anzahl", "Anzahl", 1, 1, 12),
    ],
)

UEBERSETZUNG = {"en": {
    "Spitzenschmuck": "Lace ornament", "Filigran": "Filigree", "Weihnachten": "Christmas",
    "Christbaumschmuck mit durchbrochener Spitze: Kugel, Stern, Herz, Glocke oder Zwiebel mit Mandala, "
    "Ranken, Klöppelspitze, Eiskristall oder Stern im Stern – auf Wunsch zum Stecken über Kreuz.":
        "Tree ornament in open lace: bauble, star, heart, bell or onion filled with mandala, scrolls, bobbin lace, "
        "ice crystal or star-in-star – optionally as two pieces slotted crosswise.",
    "Form": "Shape", "Muster": "Pattern", "Höhe": "Height", "Symmetrie": "Symmetry",
    "beim Stern immer 5- oder 10-fach": "the star is always 5- or 10-fold", "Feinheit": "Fineness",
    "Doppelter Rand": "Double border", "3D: zwei Teile über Kreuz": "3D: two pieces slotted crosswise",
    "Anzahl": "Count", "Kugel": "Bauble", "Stern": "Star", "Herz": "Heart", "Glocke": "Bell",
    "Zwiebel (Tropfen)": "Onion (drop)", "Mandala mit Blüten und Spitzbögen": "Mandala with petals and arches",
    "Ranken und Spiralen": "Scrolls and spirals", "Klöppelspitze (Netz mit Picots)": "Bobbin lace (net with picots)",
    "Eiskristall": "Ice crystal", "Stern im Stern": "Star in star",
    "eigenes Rezept aus Bausteinen": "your own recipe of building blocks",
    "Zufall (jeder Startwert ein neues Muster)": "random (every seed a new pattern)", "Rezept": "Recipe",
    "Startwert": "Seed",
    "Bausteine von innen nach außen, mit Komma: blüten, bögen, speichen, zickzack, perlen, ranken, sterne, tropfen, herzen":
        "building blocks from the inside out, comma-separated (German names): blüten, bögen, speichen, zickzack, "
        "perlen, ranken, sterne, tropfen, herzen", "6-fach": "6-fold", "8-fach": "8-fold",
    "12-fach": "12-fold", "fein (für 1,5–2 mm Holz)": "fine (for 1.5–2 mm wood)", "mittel": "medium",
    "kräftig (für 4 mm)": "bold (for 4 mm)",
}}

_DICKE = dict(fein=0.0, mittel=0.3, kraeftig=0.7)


def _teil(cfg, name: str, form: str, muster: str, S: float, n: int, feinheit: str, doppelrand: bool,
          oese: bool, achse: bool, notes: List[str], bausteine=()) -> Part:
    web, kerf, T = cfg.min_web, cfg.kerf, cfg.T
    wmin = web + kerf + 0.45                              # übersteht das Ausgleichen der Leinwand sicher
    w = wmin + _DICKE[feinheit]
    umriss, (_, top), yc = FG.form(form, S)
    rand = max(2 * web + 0.6, 0.035 * S, w * 1.6)
    fld = FG.feld(umriss, rand)
    R = FG.deckung(fld, 0.0, yc) if form != "kugel" else max(abs(y) for _, y in fld)
    M = FG.Muster(w, n, wmin=wmin, R=R)
    if muster in ("rezept", "zufall"):
        FG.rezept(M, R, bausteine)
    else:
        FG.MUSTER[muster](M, R)
    fig = M.figur(0.0, yc)
    if doppelrand:
        gap = max(kerf + 0.8, 1.3)
        inner = oriented(FG.offset_polygon(fld, -(gap + w / 2)), True)
        fig.line(inner + [inner[0]], w * 0.9)
    extra = []
    ro = max(3.2, 0.04 * S)
    if oese:
        if form == "kugel":                              # Krone der Kugel
            cw, ch = 0.20 * S, 0.06 * S
            extra.append(K.rect(-cw / 2, top - 1.0, cw, ch + 1.0))
            top += ch
        loop_c = (0.0, top + ro - 1.2)
        extra.append(K.circle(loop_c[0], loop_c[1], ro, 40))
    xs = [p[0] for p in umriss]
    ys = [p[1] for p in umriss]
    lw = E.Leinwand((min(xs) - 2, min(ys) - 2, max(xs) + 2, max(max(ys), top + 2 * ro) + 2), 0.08)
    shape = lw.flaechen([umriss] + extra)
    mat = E._andnot(shape, lw.flaechen([fld]))
    mat = mat.union(E._and(lw.figur(fig), shape))
    if achse:                                            # massiver Steg für den Steckschlitz
        bw = T + 2 * (web + kerf + 0.8)
        mat = mat.union(E._and(lw.flaechen([K.rect(-bw / 2, min(ys) - 1, bw, top - min(ys) + 2)]), shape))
    if oese:
        mat = E._andnot(mat, lw.flaechen([K.circle(loop_c[0], loop_c[1], ro - max(web + 0.6, 1.4), 32)]))
    return E.teil_aus_raster(name, lw, mat, web, kerf, notes)


def build(cfg, name: str = "spitzenschmuck", form: str = "kugel", muster: str = "mandala", groesse: float = 80.0,
          zaehlig: str = "8", feinheit: str = "mittel", doppelrand: bool = True, steckbar: bool = False,
          anzahl: int = 1, rezept: str = "blüten, perlen, bögen", startwert: int = 1):
    from models._shapes import cut_axis_slot
    if form not in dict(FG.FORMEN):
        raise ValueError(f"Unbekannte Form {form!r}")
    if muster not in FG.MUSTER and muster not in ("rezept", "zufall"):
        raise ValueError(f"Unbekanntes Muster {muster!r}")
    S = cfg.s(groesse)
    n = int(zaehlig)
    if form == "stern":
        n = 5 if n < 8 else 10
    if muster == "kristall" and form != "stern":
        n = 6
    if S < 12 * (cfg.min_web + cfg.kerf) + 20:
        raise ValueError("Für so feine Spitze ist der Schmuck zu klein – Höhe vergrößern")
    asm = Assembly(name, params=dict(form=form, muster=muster, groesse=S, zaehlig=n, feinheit=feinheit,
                                     doppelrand=doppelrand, steckbar=steckbar, anzahl=anzahl))
    notes: List[str] = []
    T = cfg.T
    namen = dict(FG.BAUSTEINE)
    for i in range(anzahl):
        tag = f"{form}_{muster}" + (f"_{i + 1}" if anzahl > 1 else "")
        bausteine = ()
        if muster == "rezept":
            bausteine = FG.rezept_lesen(rezept)
        elif muster == "zufall":
            bausteine = FG.rezept_zufall(int(startwert) + i)
            asm.notes.append(f"{tag}: Rezept „{', '.join(namen[b] for b in bausteine)}“ (Startwert {int(startwert) + i}).")
        if not steckbar:
            asm.parts.append(_teil(cfg, tag, form, muster, S, n, feinheit, doppelrand, True, False, notes, bausteine))
            continue
        umriss, (_, top), yc = FG.form(form, S)
        y_mid = (min(p[1] for p in umriss) + top) / 2
        for suf, from_top in (("_a", True), ("_b", False)):
            p = _teil(cfg, tag + suf, form, muster, S, n, feinheit, doppelrand, not from_top, True, notes, bausteine)
            out, slot = cut_axis_slot(p.outline, T, y_mid, from_top)
            ys = [q[1] for q in p.outline]
            span = (y_mid, max(ys)) if from_top else (min(ys), y_mid)
            q = Part(p.name, out, features=[JointFeature("kreuz", "halving", span[1] - span[0], T, span=span,
                                                         points=slot)])
            for h in p.holes:
                q.add_hole(h)
            asm.parts.append(q)
        asm.connect(f"{tag}_a:kreuz", f"{tag}_b:kreuz")
    for t in dict.fromkeys(notes):
        asm.notes.append(t)
    if steckbar:
        asm.notes.append("Teil B (Schlitz unten, mit Öse) von oben auf Teil A (Schlitz oben) schieben.")
    asm.notes.append("Aufhängen: Band oder Draht durch die Öse. Feine Spitze vorsichtig aus der Platte lösen – "
                     "lieber mit einem Zahnstocher von hinten drücken als ziehen.")
    if feinheit == "fein" and T > 2.5:
        asm.notes.append(f"Tipp: Feine Spitze wirkt in 1,5–2 mm Holz am schönsten (eingestellt: {T:g} mm).")
    return asm
