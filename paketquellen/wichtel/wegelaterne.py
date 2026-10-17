"""
Wegelaterne – Paket „Wichtel“.

Laternenpfahl für den Wichtelweg aus zwei gleichen Teilen, die über Kreuz ineinandergesteckt werden – so
steht die Laterne frei und sieht von allen Seiten gleich aus. Geschwungener Fuß, Zierringe am Pfahl,
Schnörkel unter dem Laternenkopf, Fenster mit Sprossen, Dach mit Kugel.
"""
import importlib.util
import math
import os

from steckwerk import Assembly, JointFeature, Part
from pakete import num, sel

_spec = importlib.util.spec_from_file_location("swpaket_wichtel__lade_laterne",
                                               os.path.join(os.path.dirname(os.path.abspath(__file__)), "_lade.py"))
_m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_m)
M = _m.markt()
Z, K = M.Z, M.K

KOEPFE = [("klassisch", "klassisch"), ("rund", "rund mit Kuppel")]

UEBERSETZUNG = {"en": {
    "Wegelaterne": "Lantern post",
    "Laternenpfahl aus zwei Teilen über Kreuz gesteckt: geschwungener Fuß, Zierringe, Schnörkel, Fenster mit "
    "Sprossen und Dach mit Kugel.":
        "Lantern post made of two crossed parts: curved foot, decorative rings, scrolls, windows with glazing bars "
        "and a roof with a ball.",
    "Höhe": "Height", "Laternenkopf": "Lantern head", "klassisch": "classic", "rund mit Kuppel": "round with dome",
}}

INFO = dict(
    label="Wegelaterne", group="Wichtel",
    desc="Laternenpfahl aus zwei Teilen über Kreuz gesteckt: geschwungener Fuß, Zierringe, Schnörkel, Fenster mit "
         "Sprossen und Dach mit Kugel.",
    params=[
        num("hoehe", "Höhe", 95, 50, 300),
        sel("kopf", "Laternenkopf", KOEPFE, "klassisch"),
    ],
)
INFO["params"] = M.mit_massstab("wegelaterne", INFO["params"])
UEBERSETZUNG["en"].update(M.EN)


def _figur(H: float, T: float, w: float, kopf: str):
    mw = T + 2 * max(2.2, w)                        # Mittelsprosse/Pfahl: Platz für den Kreuzschlitz
    bp = mw
    f = Z.Figur()
    # Fuß: geschwungen auslaufend
    fw = H * 0.2
    rechts = K.bez3((fw, 0), (fw * 0.55, H * 0.02), (bp * 0.9, H * 0.04), (bp / 2, H * 0.12), 14)
    fuss = [(-fw, 0)] + rechts + [(-x, y) for x, y in reversed(rechts[1:])]
    f.add(fuss)
    f.add(K.rect(-fw, 0, 2 * fw, max(1.5, H * 0.018)))
    yk = H * 0.66                                   # Unterkante Laternenkopf
    f.add(K.rect(-bp / 2, 0, bp, yk + 1))
    for y in (H * 0.14, H * 0.38, H * 0.6):        # Zierringe
        f.add(Z.abrunden(K.rect(-bp * 0.85, y, bp * 1.7, max(1.6, H * 0.022)), 0.5, 2))
    # Schnörkel unter dem Kopf
    sw = max(w * 1.05, H * 0.014)
    for sg in (-1, 1):
        pfad = K.bez3((sg * bp / 2, yk - H * 0.1), (sg * H * 0.1, yk - H * 0.1), (sg * H * 0.12, yk - H * 0.02),
                      (sg * H * 0.075, yk + 0.6), 14)
        f.add(K.stroke(pfad, sw))
        f.add(K.circle(sg * bp / 2 + sg * 0.3, yk - H * 0.1, sw * 0.6, 12))
    # Kopf
    kb, kt = H * 0.1, H * 0.135                     # halbe Breite unten / oben
    yh = H * 0.86
    f.add(Z.abrunden(K.rect(-kb - H * 0.015, yk, 2 * (kb + H * 0.015), H * 0.03), 0.6, 2))  # Bodenplatte
    f.add([(-kb, yk), (kb, yk), (kt, yh), (-kt, yh)])
    fr = max(w * 1.1, H * 0.014)
    for sg in (-1, 1):                              # zwei Fensterscheiben neben der Mittelsprosse
        y0, y1 = yk + H * 0.03 + fr, yh - fr
        def xr(y):
            return kb + (kt - kb) * (y - yk) / (yh - yk) - fr
        ym = (y0 + y1) / 2                          # Quersprosse
        q = max(w, 1.2) / 2
        f.cut([(sg * mw / 2, y0), (sg * xr(y0), y0), (sg * xr(ym - q), ym - q), (sg * mw / 2, ym - q)])
        f.cut([(sg * mw / 2, ym + q), (sg * xr(ym + q), ym + q), (sg * xr(y1), y1), (sg * mw / 2, y1)])
    # Dach und Kugel
    if kopf == "rund":
        f.add([(-kt - H * 0.03, yh - 0.5), (kt + H * 0.03, yh - 0.5)] +
              [((kt + H * 0.03) * math.cos(a), yh - 0.5 + H * 0.08 * math.sin(a))
               for a in (math.pi * i / 30 for i in range(1, 30))])
        ytop = yh + H * 0.08
    else:
        f.add(Z.abrunden([(-kt - H * 0.035, yh - 0.5), (kt + H * 0.035, yh - 0.5), (kt * 0.25, yh + H * 0.08),
                          (-kt * 0.25, yh + H * 0.08)], H * 0.008, 2))
        ytop = yh + H * 0.08
    rk = max(mw * 0.62, H * 0.03)
    f.add(K.rect(-mw / 2, ytop - 1, mw, H - ytop - rk + 1.5))
    f.add(K.circle(0, H - rk, rk, 32))
    return f, mw


def build(cfg, name="wegelaterne", hoehe=95.0, kopf="klassisch", massstab="wichtel", wichtel=70.0):
    if massstab == "wichtel":
        hoehe = M.mass("wegelaterne", wichtel, INFO["params"], cfg)["hoehe"]
    from models._shapes import cut_axis_slot
    T = cfg.T
    H = cfg.s(hoehe)
    w = Z.wmin(cfg)
    notes = []
    asm = Assembly(name, params=dict(hoehe=H, kopf=kopf))
    fig, mw = _figur(H, T, w, kopf)
    y_mid = H * 0.5
    for suf, von_oben in (("a", True), ("b", False)):
        p = Z.figur_teil(cfg, f"laterne_{suf}", fig, notes, unten_flach=True)
        out, slot = cut_axis_slot(p.outline, T, y_mid, von_oben)
        ys = [q[1] for q in p.outline]
        span = (y_mid, max(ys)) if von_oben else (min(ys), y_mid)
        q = Part(p.name, out, features=[JointFeature("kreuz", "halving", span[1] - span[0], T, span=span,
                                                     points=slot)])
        for h in p.holes:
            q.add_hole(h)
        # Holzmaserung am Pfahl
        Z.gravur(q, [([(mw * 0.42 * (1 if von_oben else -1), H * 0.17), (mw * 0.38 * (1 if von_oben else -1), H * 0.35)],
                       False)], rand=0.4)
        asm.parts.append(q)
    asm.connect("laterne_a:kreuz", "laterne_b:kreuz")
    asm.notes.append("Teil B (Schlitz unten) von oben über Kreuz auf Teil A (Schlitz oben) schieben, bis beide "
                     "Füße auf dem Tisch stehen. Tipp: Transparentpapier hinter die Fenster und ein LED-Teelicht "
                     "daneben.")
    asm.notes += list(dict.fromkeys(notes))
    return asm
