"""
wichtel.py – Wichtel-Figur (Zipfelmütze, Bart, Füße) auf ovalem Sockel.

Kontur aus Geraden, Kreisbögen (Füße) und quadratischen Bezierkurven (Mütze).
Gesicht und Bart werden graviert.
"""
from __future__ import annotations

import math
from typing import Optional

from laserforge import (Assembly, Config, Part, arc_points, bezier_q, circle, clean, profile_edge)
from models._stand import bottom_tab, stand_base, tab_feature_at

DEFAULTS = dict(height=70.0)


def build(cfg: Config, name: str = "wichtel", height: Optional[float] = None,
          width: Optional[float] = None, text: str = "", schrift: str = "normal",
          schreibweise: str = "gross") -> Assembly:
    """text: Gravur vorne auf dem Sockel (z. B. ein Name)."""
    T = cfg.T
    H = cfg.s(height or DEFAULTS["height"])
    f = 0.08 * H                 # Fußhöhe
    fw = 0.30 * H                # halbe Fußbreite (außen)
    bw = 0.25 * H                # halbe Gewandbreite unten
    nw = 0.20 * H                # halbe Breite unter der Krempe
    yb = 0.44 * H                # Krempe unten
    brim_h = 0.05 * H
    brim = 0.26 * H
    if width:
        s = min(1.0, cfg.s(width) / (2 * max(fw + f / 2, brim)))
        fw, bw, nw, brim = fw * s, bw * s, nw * s, brim * s
    tol = cfg.arc_tolerance
    tw = max(cfg.min_tab_width, min(cfg.tab_factor * T, 0.5 * fw))

    tip = (0.06 * H, H)
    hb = 0.80 * brim             # Mützenansatz über der Krempe
    pts = profile_edge((-fw, 0.0), (fw, 0.0), bottom_tab(2 * fw, tw, T))
    pts += arc_points(fw, f / 2, f / 2, -math.pi / 2, math.pi / 2, tol)          # rechter Fuß
    pts += [(bw, f), (nw, yb), (brim, yb), (brim, yb + brim_h), (hb, yb + brim_h)]
    pts += bezier_q((hb, yb + brim_h), (0.19 * H, 0.77 * H), tip, 28)[1:]
    pts += bezier_q(tip, (-0.13 * H, 0.77 * H), (-hb, yb + brim_h), 28)[1:]
    pts += [(-brim, yb + brim_h), (-brim, yb), (-nw, yb), (-bw, f)]
    pts += arc_points(-fw, f / 2, f / 2, math.pi / 2, 3 * math.pi / 2, tol)      # linker Fuß
    fig = Part(f"{name}_figur", clean(pts),
               features=[tab_feature_at("sockel", -tw / 2, 0.0, tw, T)])

    # Gravur: Nase, Bart (Wellenlinie), Fußtrennung, Krempe, Bommel-Andeutung
    ny = yb - 0.07 * H
    fig.add_engrave(circle(0.0, ny, 0.055 * H, tol), closed=True)
    beard = []
    n = 9
    for i in range(n + 1):
        t = i / n
        x = -0.17 * H + t * 0.34 * H
        depth = 0.30 * H * math.sin(math.pi * t) ** 0.8
        y = yb - 0.015 * H - depth + (0.012 * H if i % 2 else 0.0)
        beard.append((x, y))
    fig.add_engrave(beard)
    fig.add_engrave([(0.0, 0.6), (0.0, f + 0.02 * H)])
    fig.add_engrave([(-brim + 1.0, yb + brim_h / 2), (brim - 1.0, yb + brim_h / 2)])
    for sx in (-1, 1):                    # Hände
        fig.add_engrave(circle(sx * 0.18 * H, 0.2 * H, 0.03 * H, tol), closed=True)

    asm = Assembly(name, params={"height": H, **({"text": text} if text else {})})
    asm.parts.append(fig)
    stand_base(asm, fig, "sockel", tw, cfg, rx=fw + 4.0, ry=max(0.16 * H, 8.0), name=f"{name}_sockel",
               text=text, schrift=schrift, schreibweise=schreibweise)
    asm.notes.append(f"{name}: Figur in den Sockel stecken.")
    return asm
