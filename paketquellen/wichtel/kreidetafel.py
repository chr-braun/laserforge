"""
Kreidetafel – Paket „Wichtel“.

Aufstelltafel für den Wichtelmarkt: Holzrahmen mit Tafelfläche (zum Schwarzmalen), gravierter Schrift und
einer Kreideablage, auf zwei Beinen, die in einen Fuß gesteckt werden. Oben gerade, im Rundbogen oder als
Giebel mit Herz.
"""
import importlib.util
import math
import os

from steckwerk import Assembly, Part, oriented
from pakete import num, sel, txt

_spec = importlib.util.spec_from_file_location("swpaket_wichtel__lade_tafel",
                                               os.path.join(os.path.dirname(os.path.abspath(__file__)), "_lade.py"))
_m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_m)
M = _m.markt()
Z, K = M.Z, M.K

FORMEN = [("bogen", "Rundbogen"), ("gerade", "gerade"), ("giebel", "Giebel mit Herz")]

UEBERSETZUNG = {"en": {
    "Kreidetafel": "Chalkboard",
    "Aufstelltafel mit Holzrahmen, Tafelfläche zum Schwarzmalen, gravierter Schrift und Kreideablage – steht "
    "auf zwei Beinen in einem Fuß.":
        "Standing sign with wooden frame, board area to paint black, engraved lettering and chalk ledge – stands "
        "on two legs in a foot.",
    "Text": "Text", "| beginnt eine neue Zeile": "| starts a new line", "Höhe": "Height", "Breite": "Width",
    "Form": "Shape", "Rundbogen": "round arch", "gerade": "straight", "Giebel mit Herz": "gable with heart",
}}

INFO = dict(
    label="Kreidetafel", group="Wichtel",
    desc="Aufstelltafel mit Holzrahmen, Tafelfläche zum Schwarzmalen, gravierter Schrift und Kreideablage – steht "
         "auf zwei Beinen in einem Fuß.",
    params=[
        txt("text", "Text", "Heute|frische|Lebkuchen", "| beginnt eine neue Zeile", maxlen=60),
        num("hoehe", "Höhe", 66, 35, 250),
        num("breite", "Breite", 42, 25, 180),
        sel("form", "Form", FORMEN, "bogen"),
    ],
)
INFO["params"] = M.mit_massstab("kreidetafel", INFO["params"])
UEBERSETZUNG["en"].update(M.EN)


def _kontur(form: str, W: float, H: float, y0: float):
    """Außenkontur der Tafel (x −W/2 … W/2, y y0 … H)."""
    if form == "bogen":
        hb = min(W / 2, (H - y0) * 0.35)
        arc = [(W / 2 * math.cos(a), H - hb + hb * math.sin(a)) for a in (math.pi * i / 40 for i in range(41))]
        return [(-W / 2, y0), (W / 2, y0)] + arc + [(-W / 2, H - hb)]
    if form == "giebel":
        hg = min(W * 0.3, (H - y0) * 0.28)
        return Z.abrunden([(-W / 2, y0), (W / 2, y0), (W / 2, H - hg), (0, H), (-W / 2, H - hg)], W * 0.05)
    return Z.abrunden([(-W / 2, y0), (W / 2, y0), (W / 2, H), (-W / 2, H)], W * 0.07)


def build(cfg, name="kreidetafel", text="Heute|frische|Lebkuchen", hoehe=66.0, breite=42.0, form="bogen",
          massstab="wichtel", wichtel=70.0):
    if massstab == "wichtel":
        _m = M.mass("kreidetafel", wichtel, INFO["params"], cfg)
        hoehe, breite = _m["hoehe"], _m["breite"]
    T = cfg.T
    H, W = cfg.s(hoehe), cfg.s(breite)
    w = Z.wmin(cfg)
    notes = []
    asm = Assembly(name, params=dict(hoehe=H, breite=W))
    hl = H * 0.24                                       # Beinhöhe
    bb = max(2.4 * T, W * 0.1)                          # Beinbreite
    xb = W / 2 - bb / 2 - W * 0.04
    rand = max(3.0, W * 0.09)                           # Holzrahmen um die Tafelfläche
    fig = Z.Figur().add(_kontur(form, W, H, hl))
    for sg in (-1, 1):
        fig.add(K.rect(sg * xb - bb / 2, 0, bb, hl + 1.0))
        fig.add(Z.abrunden(K.rect(sg * xb - bb / 2 - 1.6, 0, bb + 3.2, max(2.5, hl * 0.12)), 0.8, 3))
    ab = max(2.0, H * 0.035)                            # Kreideablage
    fig.add(Z.abrunden(K.rect(-W / 2 - ab * 0.6, hl + rand * 0.3, W + ab * 1.2, ab), ab * 0.4, 3))
    if form == "giebel":
        fig.cut(Z.herz(0, H - min(W * 0.3, (H - hl) * 0.28) * 0.45, min(W * 0.16, (H - hl) * 0.12)))
    # Querstrebe zwischen den Beinen
    fig.add(K.rect(-xb, hl * 0.45, 2 * xb, max(w * 1.3, 2.4)))
    tafel = Z.figur_teil(cfg, "tafel", fig, notes, unten_flach=True)
    tw = max(cfg.min_tab_width + 0.6, min(bb - 2.6, cfg.tab_factor * T))
    for k, sg in enumerate((-1, 1)):
        Z.zapfen_unten(tafel, sg * xb, tw, T, f"fuss{k}", 10 + k)
    # Tafelfläche (Innenkontur) und Schrift
    from steckwerk import offset_polygon
    if form == "giebel":                                # Tafelfläche unter dem Giebel (dort sitzt das Herz)
        innen = offset_polygon(oriented(_kontur("gerade", W, H - min(W * 0.3, (H - hl) * 0.28),
                                                hl + rand * 0.3 + ab), True), -rand)
    else:
        innen = offset_polygon(oriented(_kontur(form, W, H, hl + rand * 0.3 + ab), True), -rand)
    lin = [(innen, True)]
    Z.gravur(tafel, lin + [([(sg * xb - bb * 0.15, 1.5), (sg * xb + bb * 0.1, hl - 1)], False) for sg in (-1, 1)],
             rand=0.5)
    if text.strip():
        xs = [p[0] for p in innen]
        ys = [p[1] for p in innen]
        iw, ih = max(xs) - min(xs), max(ys) - min(ys)
        top = max(ys) - (iw * 0.3 if form == "bogen" else 0)
        M.text_gravur(tafel, text, 0.0, (min(ys) + top) / 2, iw * 0.84, (top - min(ys)) * 0.8, ih * 0.22, rand=0.8)
    asm.parts.append(tafel)
    # Fuß
    L = 2 * xb + bb + 2 * max(4.0, T * 1.5)
    Dfuss = max(4 * T + 4, H * 0.22)
    fuss = Part("fuss", oriented(Z.abrunden(K.rect(-L / 2, -Dfuss / 2, L, Dfuss), Dfuss * 0.4, 6), True))
    for k, sg in enumerate((-1, 1)):
        Z.schlitz(fuss, f"bein{k}", sg * xb, 0.0, tw, T, 10 + k)
        asm.connect(f"tafel:fuss{k}", f"fuss:bein{k}")
    asm.parts.append(fuss)
    asm.notes.append("Die Tafel mit beiden Beinen in den Fuß stecken. Die Tafelfläche schwarz, den Rahmen holzfarben "
                     "lassen und die Schrift mit weißem Stift oder Kreidemarker nachziehen.")
    asm.notes += list(dict.fromkeys(notes))
    return asm
