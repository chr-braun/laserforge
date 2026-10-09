"""
tannenbaum.py – 3D-Steck-Tannenbaum aus zwei Silhouetten mit Kreuzschlitz.

Teil A hat einen Schlitz von oben bis zur halben Höhe, Teil B einen Schlitz von unten bis
zur halben Höhe. Ineinandergesteckt ergibt das einen freistehenden Baum mit vier Flügeln.
Etagen, Breite und Höhe sind parametrisch; Kugeln werden graviert.
"""
from __future__ import annotations

import math
from typing import List, Optional

from laserforge import Assembly, Config, JointFeature, Part, Point, circle, clean

DEFAULTS = dict(height=110.0, width=None, tiers=4)


def _right_profile(Ht: float, Wt: float, th: float, tiers: int) -> List[Point]:
    """Rechte Baumhälfte von der Stammoberkante bis kurz vor die Spitze."""
    h_t = (Ht - th) / (tiers + 0.5)
    w = [Wt / 2 * (1 - 0.72 * i / tiers) for i in range(tiers)]
    pts: List[Point] = []
    for i in range(tiers):
        y = th + i * h_t
        pts.append((w[i], y))
        if i + 1 < tiers:
            pts.append((0.55 * w[i + 1], y + h_t))
    return pts


def _tier_info(Ht, Wt, th, tiers):
    h_t = (Ht - th) / (tiers + 0.5)
    w = [Wt / 2 * (1 - 0.72 * i / tiers) for i in range(tiers)]
    return h_t, w


def build(cfg: Config, name: str = "tannenbaum", height: Optional[float] = None,
          width: Optional[float] = None, tiers: int = 4) -> Assembly:
    T = cfg.T
    Ht = cfg.s(height or DEFAULTS["height"])
    Wt = cfg.s(width) if width else 0.72 * Ht
    if tiers < 2 or tiers > 8:
        raise ValueError("tiers muss zwischen 2 und 8 liegen")
    th = 0.12 * Ht
    tw = max(0.16 * Wt, T + 2 * max(3.0, 3 * cfg.min_web))
    Hm = Ht / 2                                     # Treffpunkt der Kreuzschlitze
    h_t, w = _tier_info(Ht, Wt, th, tiers)
    right = _right_profile(Ht, Wt, th, tiers)
    # Schnittpunkt der letzten Schräge mit x = T/2 (für Teil A)
    xl, yl = w[-1], th + (tiers - 1) * h_t
    y_cut = yl + (xl - T / 2) / xl * (Ht - yl)

    def mirror(pts):
        return [(-x, y) for x, y in reversed(pts)]

    asm = Assembly(name, params={"height": Ht, "width": Wt, "tiers": tiers})

    # Teil A: Schlitz von oben (Spitze entfällt, B trägt die Spitze)
    a_slot = [(T / 2, y_cut), (T / 2, Hm), (-T / 2, Hm), (-T / 2, y_cut)]
    a_pts = [(-tw / 2, 0.0), (tw / 2, 0.0), (tw / 2, th)] + right + a_slot + mirror(right) + [(-tw / 2, th)]
    A = Part(f"{name}_a", clean(a_pts), features=[
        JointFeature("kreuz", "halving", Ht - Hm, T, span=(Hm, Ht), points=a_slot)])
    # Teil B: Schlitz von unten
    b_slot = [(-T / 2, 0.0), (-T / 2, Hm), (T / 2, Hm), (T / 2, 0.0)]
    b_pts = [(-tw / 2, 0.0)] + b_slot + [(tw / 2, 0.0), (tw / 2, th)] + right + [(0.0, Ht)] + \
        mirror(right) + [(-tw / 2, th)]
    B = Part(f"{name}_b", clean(b_pts), features=[
        JointFeature("kreuz", "halving", Hm, T, span=(0.0, Hm), points=b_slot)])

    # Gravur: Kugeln auf jeder Etage, Stammlinie
    r = max(1.4, 0.016 * Ht)
    for part in (A, B):
        for i in range(tiers):
            y = th + i * h_t + 0.35 * h_t
            for sx in (-1, 1):
                x = sx * max(0.5 * w[i], T / 2 + r + 2.0)
                if abs(x) + r + 1.0 < w[i] * 0.85:
                    part.add_engrave(circle(x, y, r, cfg.arc_tolerance), closed=True)
        for sx in (-1, 1):
            x = sx * (T / 2 + (tw / 2 - T / 2) / 2)
            part.add_engrave([(x, 1.5), (x, th - 1.5)])
    # Stern auf der Spitze von B (Gravur)
    sr = min(0.05 * Ht, 0.35 * (Ht - yl))
    cy = Ht - 1.6 * sr
    star = []
    for k in range(10):
        rr = sr if k % 2 == 0 else sr * 0.45
        ang = math.pi / 2 + k * math.pi / 5
        star.append((rr * math.cos(ang), cy + rr * math.sin(ang)))
    # nur gravieren, wenn der Stern sicher innerhalb der Spitze liegt
    half = lambda y: xl * (Ht - y) / (Ht - yl)
    if all(abs(x) < half(y) - 0.6 for x, y in star):
        B.add_engrave(star, closed=True)

    asm.parts += [A, B]
    asm.connect(f"{A.name}:kreuz", f"{B.name}:kreuz")
    asm.notes.append(f"{name}: Teil A (Schlitz oben) von oben auf Teil B (Schlitz unten) schieben.")
    return asm
