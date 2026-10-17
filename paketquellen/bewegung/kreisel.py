"""
Kreisel – Scheibe mit Vierkantloch und eine Spindel aus der Platte (Vierkant T × T mit stumpfer Spitze).
Die Scheibe sitzt tief auf der Spindel, damit der Kreisel lange ruhig läuft.
"""
from __future__ import annotations

import math
import os
import sys
from typing import List

from steckwerk import Assembly, JointFeature, Part, rect
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

MUSTER = [("spirale", "Spirale (dreht hypnotisch)"), ("farbkreis", "Farbkreis zum Ausmalen"),
          ("sterne", "Sterne ausgeschnitten"), ("blume", "Blume"), ("schlicht", "schlicht")]

INFO = dict(
    label="Kreisel",
    group="Bewegung",
    desc="Drehkreisel aus zwei Teilen: bemalbare Scheibe mit Spirale, Farbkreis, Sternen oder Blume und eine "
         "Spindel mit stumpfer Spitze. Optional ein Kreisel-Paar zum Wettdrehen.",
    params=[
        num("durchmesser", "Durchmesser", 55, 35, 90),
        sel("muster", "Muster", MUSTER, "spirale"),
        num("griff", "Grifflänge", 28, 18, 45, help="Spindel über der Scheibe"),
        flag("paar", "Zwei Kreisel (zum Wettdrehen)", False),
    ],
)

UEBERSETZUNG = {"en": {
    "Kreisel": "Spinning top", "Bewegung": "Motion",
    "Drehkreisel aus zwei Teilen: bemalbare Scheibe mit Spirale, Farbkreis, Sternen oder Blume und eine "
    "Spindel mit stumpfer Spitze. Optional ein Kreisel-Paar zum Wettdrehen.":
        "Two-part spinning top: a disc to paint with a spiral, colour wheel, stars or flower, and a spindle "
        "with a blunt tip. Optionally a pair for spinning contests.",
    "Durchmesser": "Diameter", "Muster": "Pattern", "Spirale (dreht hypnotisch)": "Spiral (hypnotic when spinning)",
    "Farbkreis zum Ausmalen": "Colour wheel to paint", "Sterne ausgeschnitten": "Cut-out stars", "Blume": "Flower",
    "schlicht": "plain", "Grifflänge": "Handle length", "Spindel über der Scheibe": "spindle above the disc",
    "Zwei Kreisel (zum Wettdrehen)": "Two tops (for spinning contests)",
}}


def _scheibe(cfg, pname: str, R: float, muster: str, notes: List[str]) -> Part:
    T = cfg.T
    p = Part(pname, K.circle(0, 0, R, max(64, int(R * 3))))
    hole = rect(-T / 2, -T / 2, T, T, ccw=False)
    p.holes.append(hole)
    p.features.append(JointFeature("nabe", "bore_square", T, T, pos=0.0, points=list(hole)))
    r0 = T / math.sqrt(2) + 3.0
    if muster == "sterne":
        n = 5 if R < 40 else 6
        rs = min(0.2 * R, (R - r0) * 0.32)
        rc = (R + r0) / 2 + 0.5
        for k in range(n):
            a = 2 * math.pi * k / n
            p.add_hole(K.star(rc * math.cos(a), rc * math.sin(a), rs, rs * 0.5, 5, a))
        p.add_engrave(K.circle(0, 0, R - 2, 96), closed=True)
    elif muster == "spirale":
        for arm in range(2):
            pts = []
            for k in range(220):
                t = k / 219
                rr = r0 + 1 + t * (R - r0 - 3)
                a = arm * math.pi + t * 3.4 * math.pi
                pts.append((rr * math.cos(a), rr * math.sin(a)))
            p.add_engrave(pts)
    elif muster == "farbkreis":
        n = 6
        for k in range(n):
            a = 2 * math.pi * k / n
            p.add_engrave([(r0 * math.cos(a), r0 * math.sin(a)), ((R - 1.5) * math.cos(a), (R - 1.5) * math.sin(a))])
        p.add_engrave(K.circle(0, 0, r0, 32), closed=True)
        p.add_engrave(K.circle(0, 0, (R + r0) / 2, 64), closed=True)
    elif muster == "blume":
        n = 8
        rp = (R - r0) * 0.5
        for k in range(n):
            a = 2 * math.pi * k / n
            p.add_engrave(K.ellipse((r0 + rp) * math.cos(a), (r0 + rp) * math.sin(a), rp * 0.95, rp * 0.42, rot=a,
                                    n=36), closed=True)
        p.add_engrave(K.circle(0, 0, r0 + 0.5, 32), closed=True)
    return p


def _spindel(cfg, pname: str, unten: float, griff: float) -> Part:
    """Vierkantspindel: Spitze unten (stumpf, Öffnungswinkel ~ 70°), Scheibe bei z = unten … unten + T."""
    T = cfg.T
    spitze = T / 2 / math.tan(math.radians(35))
    Lg = unten + T + griff
    pts = [(-0.35, 0.0), (0.35, 0.0), (T / 2, spitze), (T / 2, Lg - 0.8), (T / 2 - 0.8, Lg), (-T / 2 + 0.8, Lg),
           (-T / 2, Lg - 0.8), (-T / 2, spitze)]
    p = Part(pname, pts)
    p.features.append(JointFeature("scheibe", "shaft", T, T, pos=0.0, span=(unten, unten + T),
                                   points=[(T / 2, unten), (T / 2, unten + T), (-T / 2, unten + T), (-T / 2, unten)]))
    return p


def build(cfg, name: str = "kreisel", durchmesser: float = 55.0, muster: str = "spirale", griff: float = 28.0,
          paar: bool = False):
    from models import _deko as dk
    dk.check_choice("Muster", muster, MUSTER)
    R = cfg.s(durchmesser) / 2
    if not 17.5 <= R <= 45:
        raise ValueError("Kreisel: Durchmesser muss zwischen 35 und 90 mm liegen")
    if not 18 <= griff <= 45:
        raise ValueError("Kreisel: Grifflänge muss zwischen 18 und 45 mm liegen")
    T = cfg.T
    notes: List[str] = []
    asm = Assembly(name, params=dict(durchmesser=2 * R, muster=muster))
    unten = max(6.0, T / 2 / math.tan(math.radians(35)) + 3.0)
    for i in range(2 if paar else 1):
        suf = f"_{i + 1}" if paar else ""
        sch = _scheibe(cfg, f"{name}_scheibe{suf}", R, muster if i == 0 else ("sterne" if muster != "sterne" else "blume"),
                       notes)
        sp = _spindel(cfg, f"{name}_spindel{suf}", unten, griff)
        asm.parts += [sch, sp]
        asm.connect(f"{sp.name}:scheibe", f"{sch.name}:nabe")
    asm.notes += [
        "Die Scheibe von oben auf die Spindel schieben, bis sie über der Spitze sitzt (Pressitz, bei Bedarf ein "
        "Tropfen Leim). Spitze und Kanten mit feinem Schleifpapier leicht runden.",
        "Drehen: Spindel zwischen Daumen und Mittelfinger zwirbeln und loslassen. Auf einem glatten Teller "
        "läuft er am längsten.",
    ]
    return asm
