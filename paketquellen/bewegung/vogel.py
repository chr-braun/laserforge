"""
Balancier-Vogel – flacher Vogel (Draufsicht) mit nach vorne geschwungenen Flügeln. Unter die Flügelspitzen
kommt je eine Münze; Steckwerk rechnet den Schwerpunkt aus Holzfläche, Holzart und Münzen aus und legt die
Schnabelspitze genau darauf. So balanciert der Vogel auf Fingerspitze, Bleistift oder dem Ständer.
"""
from __future__ import annotations

import math
import os
import sys
from typing import List, Tuple

from steckwerk import Assembly, JointFeature, Part, signed_area, slot_feature
from pakete import flag, num, sel

_here = os.path.dirname(os.path.abspath(__file__))


def _sub(name: str):
    import importlib.util
    path = os.path.join(_here, name + ".py")
    key = "swpaket_bewegung_" + name
    mod = sys.modules.get(key)
    if mod is None or getattr(mod, "__file__", None) != path:
        spec = importlib.util.spec_from_file_location(key, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[key] = mod
        spec.loader.exec_module(mod)
    return mod


B = _sub("_bw")
K = B.K
Figur = B.Figur

# Masse (g) und Durchmesser (mm) der Euro-Münzen
MUENZEN = {"1ct": (2.30, 16.25), "2ct": (3.06, 18.75), "5ct": (3.92, 21.25), "10ct": (4.10, 19.75),
           "20ct": (5.74, 22.25), "1eur": (7.50, 23.25)}
MUENZ_AUSWAHL = [("1ct", "1 Cent"), ("2ct", "2 Cent"), ("5ct", "5 Cent"), ("10ct", "10 Cent"),
                 ("20ct", "20 Cent"), ("1eur", "1 Euro")]
HOLZ = [("pappel", "Pappelsperrholz (0,45 g/cm³)"), ("birke", "Birkensperrholz (0,68 g/cm³)"),
        ("mdf", "MDF (0,75 g/cm³)")]
DICHTE = dict(pappel=0.45, birke=0.68, mdf=0.75)

INFO = dict(
    label="Balancier-Vogel",
    group="Bewegung",
    desc="Vogel, der auf der Schnabelspitze balanciert – auf dem Finger, einem Bleistift oder dem mitgelieferten "
         "Ständer. Unter die Flügelspitzen kommen zwei Münzen, den Schwerpunkt rechnet Steckwerk aus.",
    params=[
        num("spannweite", "Spannweite", 130, 90, 180),
        sel("muenze", "Münzen unter den Flügeln", MUENZ_AUSWAHL, "5ct"),
        sel("holz", "Holz", HOLZ, "pappel", help="für die Schwerpunktrechnung"),
        flag("staender", "Ständer mitschneiden", True),
        flag("ausmalen", "Federn gravieren", True),
    ],
)

UEBERSETZUNG = {"en": {
    "Balancier-Vogel": "Balancing bird", "Bewegung": "Motion",
    "Vogel, der auf der Schnabelspitze balanciert – auf dem Finger, einem Bleistift oder dem mitgelieferten "
    "Ständer. Unter die Flügelspitzen kommen zwei Münzen, den Schwerpunkt rechnet Steckwerk aus.":
        "A bird that balances on the tip of its beak – on a finger, a pencil or the included stand. Two coins go "
        "under the wing tips; Steckwerk works out the centre of gravity.",
    "Spannweite": "Wingspan", "Münzen unter den Flügeln": "Coins under the wings", "Holz": "Wood",
    "für die Schwerpunktrechnung": "for the centre-of-gravity calculation",
    "Pappelsperrholz (0,45 g/cm³)": "Poplar plywood (0.45 g/cm³)", "Birkensperrholz (0,68 g/cm³)":
        "Birch plywood (0.68 g/cm³)", "MDF (0,75 g/cm³)": "MDF (0.75 g/cm³)",
    "Ständer mitschneiden": "Include the stand", "Federn gravieren": "Engrave feathers",
}}

YB = 28.0                                   # Schnabelspitze (Einheiten, Spannweite ≈ 100)
C_MIN, C_MAX = 22.0, 42.0                   # Bereich der Münzmitte entlang der Flügelvorderkante


def _muenzpunkt(cy: float) -> Tuple[float, float]:
    return 28.0 + (cy - 22.0) * 0.8, cy


def _vogel(yb: float, cy: float, rm: float) -> Tuple[Figur, list]:
    """Vogel in Einheiten, Schnabelspitze bei (0, yb), Münzmitte bei (±cx, cy), Münzradius rm."""
    cx, cy = _muenzpunkt(cy)
    f, l = Figur(), []
    f.add(K.ellipse(0, -2, 9, 19))                                              # Körper
    f.add(K.spline([(-7, -14), (-13, -34), (-4, -30), (0, -35), (4, -30), (13, -34), (7, -14)], closed=True, n=5))
    if yb - 9 > 4:
        f.line([(0, 4), (0, yb - 9)], 11, 10)                                    # Hals
    f.add(K.circle(0, yb - 9, 8, 40))                                            # Kopf
    f.add([(-4.2, yb - 4.5), (4.2, yb - 4.5), (0.6, yb), (-0.6, yb)])           # Schnabel
    for s in (-1, 1):
        f.add(K.spline([(s * 5, 9), (s * 17, 18), (s * (cx - 9), cy - 3), (s * cx, cy + rm * 0.6),
                        (s * (cx + rm * 0.9), cy), (s * (cx + 1), cy - 15), (s * (cx - 7), cy - 22),
                        (s * 22, -4), (s * 7, -12)], closed=True, n=6))
        f.add(K.circle(s * cx, cy, rm + 2.0, 40))                                # Flügelspitze für die Münze
        l.append((B.kreis(s * cx, cy, rm, 40), True))
        for kk in range(3):                                                      # Schwungfedern
            t = 0.3 + 0.2 * kk
            l.append(([(s * (10 + 16 * t), 2 + 12 * t), (s * (14 + 20 * t), -6 + 20 * t)], False))
        l.append((B.kreis(s * 3.2, yb - 10, 1.3, 12), True))
    l.append(([(0, -16), (0, -30)], False))
    return f, l


def _schwerpunkt(part: Part) -> Tuple[float, float, float]:
    """Fläche (mm²) und Flächenschwerpunkt (x, y) eines Teils mit Löchern."""
    def poly(pts):
        a = cx = cy = 0.0
        n = len(pts)
        for i in range(n):
            x0, y0 = pts[i]
            x1, y1 = pts[(i + 1) % n]
            c = x0 * y1 - x1 * y0
            a += c
            cx += (x0 + x1) * c
            cy += (y0 + y1) * c
        a /= 2
        return a, cx / (6 * a), cy / (6 * a)
    A, X, Y = poly(part.outline)
    A, X, Y = abs(A), X * abs(A), Y * abs(A)
    for h in part.holes:
        ah, hx, hy = poly(h)
        ah = abs(ah)
        A, X, Y = A - ah, X - hx * ah, Y - hy * ah
    return A, X / A, Y / A


def build(cfg, name: str = "vogel", spannweite: float = 130.0, muenze: str = "5ct", holz: str = "pappel",
          staender: bool = True, ausmalen: bool = True):
    from models import _deko as dk
    dk.check_choice("Münze", muenze, MUENZ_AUSWAHL)
    dk.check_choice("Holz", holz, HOLZ)
    Sp = cfg.s(spannweite)
    if not 90 <= Sp <= 180:
        raise ValueError("Balancier-Vogel: Spannweite muss zwischen 90 und 180 mm liegen")
    T = cfg.T
    mm, dm = MUENZEN[muenze]
    rho = DICHTE[holz] / 1000.0                       # g/mm³
    notes: List[str] = []
    asm = Assembly(name, params=dict(spannweite=Sp, muenze=muenze, holz=holz))
    # Einheit so wählen, dass die Flügelspitzen bei weitester Münzlage Sp/2 auseinanderliegen
    k = Sp / 100.0
    for _ in range(4):
        rm_u = (dm / 2 + 0.4) / k
        k = Sp / (2 * (_muenzpunkt(C_MAX)[0] + rm_u + 2.0))
    rm_u = (dm / 2 + 0.4) / k
    if rm_u > 15:
        raise ValueError("Balancier-Vogel: Die Münze ist für diese Spannweite zu groß – größer machen oder kleinere Münze")

    def schwerpunkt(yb, cy, n):
        f, lines = _vogel(yb, cy, rm_u)
        part = B.teil(f"{name}_vogel", f.map(lambda p: (p[0] * k, p[1] * k)), cfg, [])
        A, _, cw = _schwerpunkt(part)
        mw = A * T * rho
        return part, lines, mw, cw

    # Münzen je Flügel (1–4 übereinander) und ihre Lage so wählen, dass der Schwerpunkt im Schnabel liegt
    yb, wahl = YB, None
    for n in range(1, 5):
        cy = 32.0
        for _ in range(8):
            part, lines, mw, cw = schwerpunkt(yb, cy, n)
            neu = (yb * k * (mw + 2 * n * mm) - mw * cw) / (2 * n * mm * k)
            neu = max(C_MIN - 6, min(C_MAX + 6, neu))
            if abs(neu - cy) < 0.05:
                break
            cy = neu
        if cy <= C_MAX + 1e-6:
            wahl = n
            break
    if wahl is None:
        raise ValueError("Balancier-Vogel: Selbst vier Münzen je Flügel reichen nicht – schwerere Münze (z. B. 1 Euro) oder "
                         "kleinere Spannweite wählen")
    if cy < C_MIN:                                     # Münzen zu schwer: Münzen innen, Schnabel nach vorn
        cy = C_MIN
        for _ in range(8):
            part, lines, mw, cw = schwerpunkt(yb, cy, wahl)
            neu = (mw * cw + 2 * wahl * mm * cy * k) / (mw + 2 * wahl * mm) / k
            if abs(neu - yb) < 0.05:
                break
            yb = neu
    part, lines, mw, cw = schwerpunkt(yb, cy, wahl)
    asm.params.update(muenzen_je_fluegel=wahl, gewicht=round(mw + 2 * wahl * mm, 1))
    if ausmalen:
        B.gravur(part, [([(x * k, y * k) for x, y in pts], c) for pts, c in lines], cfg.seed)
    asm.parts.append(part)

    if staender:
        hp = max(80.0, 0.7 * Sp)
        bw = 34.0
        tw = max(cfg.min_tab_width, 8.0)
        tabs = [(-bw / 2 + 4, -bw / 2 + 4 + tw), (bw / 2 - 4 - tw, bw / 2 - 4)]
        pts = [(-bw / 2, 0)]
        for a, b in tabs:
            pts += [(a, 0), (a, -T), (b, -T), (b, 0)]
        pts += [(bw / 2, 0), (3.0, hp - 3), (1.6, hp - 0.6), (0.6, hp), (-0.6, hp), (-1.6, hp - 0.6), (-3.0, hp - 3)]
        post = Part(f"{name}_staender", pts)
        fuss = Part(f"{name}_fuss", K.circle(0, 0, max(32.0, 0.3 * Sp), 72))
        for i, (a, b) in enumerate(tabs):
            post.features.append(JointFeature(f"tab{i}", "tab", tw, T, pos=(a + b) / 2,
                                              points=[(a, 0), (a, -T), (b, -T), (b, 0)]))
            feat, hole = slot_feature(f"slot{i}", a, -T / 2, tw, T, True, (a + b) / 2)
            fuss.holes.append(hole)
            fuss.features.append(feat)
            asm.connect(f"{post.name}:tab{i}", f"{fuss.name}:slot{i}")
        asm.parts += [post, fuss]

    for t in dict.fromkeys(notes):
        asm.notes.append(t)
    name_m = dict(MUENZ_AUSWAHL)[muenze]
    asm.notes += [
        (f"Münzen: Je {'eine ' + name_m + '-Münze' if wahl == 1 else str(wahl) + ' ' + name_m + '-Münzen übereinander'}"
         f" genau in die gravierten Kreise unter die Flügelspitzen kleben (Heißkleber oder Holzleim). "
         f"Ohne Münzen kippt der Vogel nach hinten."),
        "Balancieren: Die Schnabelspitze auf Fingerspitze, Bleistiftradiergummi oder die Spitze des Ständers setzen. "
        "Kippt er doch, die Münzen ein kleines Stück weiter nach vorn oder hinten schieben.",
    ]
    return asm
