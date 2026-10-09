"""
schneemann.py – Schneemann-Silhouette aus drei Kreisen mit Zylinder, auf ovalem Sockel.

Die Kontur wird exakt aus Kreisbögen zwischen den analytisch berechneten Schnittpunkten
der Kreise zusammengesetzt (keine Bitmap-Vektorisierung).
"""
from __future__ import annotations

import math
from typing import Optional

from laserforge import (Assembly, Config, Part, arc_points, circle, clean, profile_edge)
from models._stand import bottom_tab, stand_base, tab_feature_at

DEFAULTS = dict(height=60.0)


def _meet(c1: float, r1: float, c2: float, r2: float):
    """Schnittpunkt (rechts) zweier Kreise auf der y-Achse (c2 > c1)."""
    y = (r1 * r1 - r2 * r2 + c2 * c2 - c1 * c1) / (2 * (c2 - c1))
    x = math.sqrt(max(r1 * r1 - (y - c1) ** 2, 0.0))
    return x, y


def build(cfg: Config, name: str = "schneemann", height: Optional[float] = None,
          width: Optional[float] = None, text: str = "", schrift: str = "normal",
          schreibweise: str = "gross") -> Assembly:
    """text: Gravur vorne auf dem Sockel (z. B. ein Name)."""
    T = cfg.T
    Hs = cfg.s(height or DEFAULTS["height"])
    # Proportionen in Einheiten, danach auf Hs skaliert
    r1, r2, r3 = 1.0, 0.74, 0.54
    c1 = 0.85 * r1
    c2 = c1 + r1 + 0.45 * r2
    c3 = c2 + r2 + 0.45 * r3
    yb = c3 + 0.5 * r3                      # Hutkrempe
    bh, crown_h = 0.12, 0.62
    brim, crown = 1.3 * r3, 0.82 * r3
    top = yb + bh + crown_h
    k = Hs / top
    if width:
        k = min(k, cfg.s(width) / (2 * r1))
    r1, r2, r3, c1, c2, c3, yb, bh, crown_h, brim, crown = (v * k for v in
                                                           (r1, r2, r3, c1, c2, c3, yb, bh, crown_h, brim, crown))
    tol = cfg.arc_tolerance
    xb = math.sqrt(r1 * r1 - c1 * c1)       # halbe Standfläche
    x12, y12 = _meet(c1, r1, c2, r2)
    x23, y23 = _meet(c2, r2, c3, r3)
    xh = math.sqrt(r3 * r3 - (yb - c3) ** 2)

    a1b, a1t = math.atan2(-c1, xb), math.atan2(y12 - c1, x12)
    a2b, a2t = math.atan2(y12 - c2, x12), math.atan2(y23 - c2, x23)
    a3b, a3t = math.atan2(y23 - c3, x23), math.atan2(yb - c3, xh)

    tw = max(cfg.min_tab_width, min(cfg.tab_factor * T, 1.2 * xb))
    pts = profile_edge((-xb, 0.0), (xb, 0.0), bottom_tab(2 * xb, tw, T))
    pts += arc_points(0, c1, r1, a1b, a1t, tol)
    pts += arc_points(0, c2, r2, a2b, a2t, tol)
    pts += arc_points(0, c3, r3, a3b, a3t, tol)
    yt = yb + bh
    pts += [(brim, yb), (brim, yt), (crown, yt), (crown, yt + crown_h),
            (-crown, yt + crown_h), (-crown, yt), (-brim, yt), (-brim, yb)]
    pts += arc_points(0, c3, r3, math.pi - a3t, math.pi - a3b, tol)
    pts += arc_points(0, c2, r2, math.pi - a2t, math.pi - a2b, tol)
    pts += arc_points(0, c1, r1, math.pi - a1t, math.pi - a1b, tol)
    fig = Part(f"{name}_figur", clean(pts),
               features=[tab_feature_at("sockel", -tw / 2, 0.0, tw, T)])

    # Gravur: Gesicht, Karottennase, Knöpfe, Schal, Hutband
    e = 0.09 * r3
    for sx in (-1, 1):
        fig.add_engrave(circle(sx * 0.33 * r3, c3 + 0.22 * r3, e, tol), closed=True)
    fig.add_engrave([(0.0, c3 + 0.04 * r3), (0.55 * r3, c3 - 0.06 * r3), (0.0, c3 - 0.14 * r3)], closed=True)
    for i in range(5):
        a = math.radians(-60 - i * 15)
        fig.add_engrave(circle(0.45 * r3 * math.cos(a), c3 + 0.45 * r3 * math.sin(a), e * 0.6, tol),
                        closed=True)
    for j in range(3):
        fig.add_engrave(circle(0.0, c2 + 0.4 * r2 - j * 0.38 * r2, 0.08 * r2, tol), closed=True)
    for dy in (-0.9, 1.6):                  # Schal entlang der Halslinie
        y = y23 + dy
        half = max(math.sqrt(max(r * r - (y - c) ** 2, 0)) for r, c in ((r2, c2), (r3, c3)))
        if half > 3:
            fig.add_engrave([(-half + 1.0, y), (half - 1.0, y)])
    fig.add_engrave([(crown - 0.6, yt + 0.25 * crown_h), (-crown + 0.6, yt + 0.25 * crown_h)])

    asm = Assembly(name, params={"height": Hs, **({"text": text} if text else {})})
    asm.parts.append(fig)
    stand_base(asm, fig, "sockel", tw, cfg, rx=1.25 * r1, ry=0.6 * r1, name=f"{name}_sockel",
               text=text, schrift=schrift, schreibweise=schreibweise)
    asm.notes.append(f"{name}: Figur in den Sockel stecken.")
    return asm
