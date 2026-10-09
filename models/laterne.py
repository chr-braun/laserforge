"""
laterne.py – kleine Weihnachtslaterne.

Kasten mit Zinken (gleicher Generator wie das Wichtelhaus), Rundbogenfenster in allen vier
Wänden, Bodenplatte und Deckel mit Slots, Lüftungsloch im Deckel und ein Tragebügel,
der mit zwei Tabs im Deckel steckt.
"""
from __future__ import annotations

import math
from typing import Optional

from laserforge import (Assembly, Config, JointFeature, Part, arc_points, arched, circle, clean,
                        profile_edge, slot_feature)
from models._box import build_box

DEFAULTS = dict(width=50.0, height=70.0)


def _star(cx, cy, r, n=5):
    pts = []
    for k in range(2 * n):
        rr = r if k % 2 == 0 else 0.45 * r
        a = math.pi / 2 + k * math.pi / n
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return pts


def build(cfg: Config, name: str = "laterne", width: Optional[float] = None,
          height: Optional[float] = None, depth: Optional[float] = None,
          openings: Optional[str] = None) -> Assembly:
    T = cfg.T
    W = cfg.s(width or DEFAULTS["width"])
    D = cfg.s(depth) if depth else W
    H = cfg.s(height or DEFAULTS["height"])
    mode = openings or cfg.openings
    asm, info = build_box(name, W, D, H, cfg, top="slots", base_margin=max(T, 3.0),
                          lid_margin=max(T, 3.0))
    tol = cfg.arc_tolerance
    for side, span in (("vorne", W), ("hinten", W), ("links", info.Ds), ("rechts", info.Ds)):
        part = asm.part(info.name(side))
        ww = 0.52 * span - (2 * T if side in ("vorne", "hinten") else 0)
        wh = 0.56 * H
        y0 = 0.17 * H
        shape = arched(span / 2, y0, ww, wh, tol)
        if mode == "cut":
            part.add_hole(shape)
            # Sprosse als Gravur oberhalb nicht nötig – Rahmenlinie um die Öffnung
            fr = clean(arched(span / 2, y0 - 1.5, ww + 3.0, wh + 3.0, tol))
            part.add_engrave(fr, closed=True)
        else:
            part.add_engrave(shape, closed=True)
        sr = min(0.07 * span, 0.4 * (H - (y0 + wh)) - 1.0)
        if sr >= 2.0:
            part.add_engrave(_star(span / 2, y0 + wh + (H - y0 - wh) / 2, sr), closed=True)

    # Deckel: Lüftungsloch + Slots für den Bügel
    lid = asm.part(info.name("deckel"))
    m = info.lid_margin
    cx, cy = m + W / 2, m + D / 2
    R = min(0.34 * W, W / 2 - T - 2.5)              # Bügel-Slots mit Abstand zu den Wand-Slots
    b = max(cfg.min_tab_width + 1.0, 0.1 * W, 5.0)
    rv = R - b - 3.0
    if rv >= 3.0:
        lid.add_hole(circle(cx, cy, rv, tol))
    slots = []
    for k, sx in enumerate((-1, 1)):
        xc = sx * (R - b / 2)
        feat, hole = slot_feature(f"buegel{k}", cx + xc - b / 2, cy - T / 2, b, T, True, xc)
        lid.holes.append(hole)
        lid.features.append(feat)
        slots.append(feat)

    # Bügel: Halbring mit kurzen Beinen, Füße = Tabs
    leg = 4.0
    pts = profile_edge((R - b, 0.0), (R, 0.0), [(b, T)])
    pts += arc_points(0.0, leg, R, 0.0, math.pi, tol)
    pts += profile_edge((-R, 0.0), (-R + b, 0.0), [(b, T)])
    pts += arc_points(0.0, leg, R - b, math.pi, 0.0, tol)
    feats = []
    for k, (x0, xc) in enumerate(((-R, -(R - b / 2)), (R - b, R - b / 2))):
        feats.append(JointFeature(f"fuss{k}", "tab", b, T, pos=xc,
                                  points=[(x0, 0.0), (x0, -T), (x0 + b, -T), (x0 + b, 0.0)]))
    bow = Part(info.name("buegel"), clean(pts), features=feats)
    asm.parts.append(bow)
    asm.connect(f"{bow.name}:fuss0", f"{lid.name}:buegel0")
    asm.connect(f"{bow.name}:fuss1", f"{lid.name}:buegel1")
    # LED-Markierung auf dem Boden
    base = asm.part(info.name("boden"))
    mb = info.base_margin
    rl = min(W, D) / 2 - 2 * T - 4.0
    if rl > 4:
        base.add_engrave(circle(mb + W / 2, mb + D / 2, rl, tol), closed=True)
    asm.notes.append(f"{name}: LED-Teelicht auf die Markierung stellen, Deckel aufstecken, Bügel einstecken.")
    asm.params.update(openings=mode)
    return asm
