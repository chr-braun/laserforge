"""
_bw.py – gemeinsame Helfer für das Paket „Bewegung“: Figur → laserfestes Teil mit exakten runden
Gelenk- und Fadenlöchern, kollisionsfreie Gravur.
"""
from __future__ import annotations

import math
from typing import List, Optional, Sequence, Tuple

from steckwerk import Part, min_distance, oriented, point_in_polygon
from pakete import bibliothek

K = bibliothek("verzierungen").K
E = bibliothek("verzierungen").E
Figur = K.Figur
Point = Tuple[float, float]
Linien = List[Tuple[List[Point], bool]]


def wmin(cfg) -> float:
    return cfg.min_web + cfg.kerf + 0.75


def ring(cfg) -> float:
    return max(1.6 * wmin(cfg), 2.2)


def teil(name: str, fig: Figur, cfg, notes: List[str], loecher: Sequence[Tuple[float, float, float]] = (),
         unten_flach: bool = False) -> Part:
    """Figur → Teil. loecher = [(x, y, durchmesser)] werden exakt rund geschnitten, mit Materialring."""
    web, kerf = cfg.min_web, cfg.kerf
    rg = ring(cfg)
    f = Figur(list(fig.ops))
    for x, y, d in loecher:
        f.add(K.circle(x, y, d / 2 + rg, 40))
    x0, y0, x1, y1 = f.bbox()
    px = max(0.06, min(0.12, max(x1 - x0, y1 - y0) / 1800.0))
    lw = E.Leinwand((x0 - 3, y0 - 3, x1 + 3, y1 + 3), px)
    mat = lw.figur(f)
    if loecher:
        mat = mat.union(lw.flaechen([K.circle(x, y, d / 2 + rg * 0.9, 40) for x, y, d in loecher]))
    part = E.teil_aus_raster(name, lw, mat, web, kerf, notes, unten_flach)
    for x, y, d in loecher:
        c = oriented(K.circle(x, y, d / 2, max(24, int(d * 8))), False)
        if not point_in_polygon((x, y), part.outline) or min_distance(c, part.outline, limit=web + 0.3) < web + 0.2:
            raise ValueError(f"{name}: Loch Ø {d:g} mm passt nicht – Figur größer oder Loch kleiner wählen")
        part.holes = [h for h in part.holes
                      if min_distance(h, c, limit=web + 0.3) >= web + 0.2 and not point_in_polygon(h[0], c)
                      and not point_in_polygon((x, y), h)]
        part.add_hole(c)
    return part


def gravur(part: Part, linien: Sequence[Tuple[Sequence[Point], bool]], seed: int = 1, rand: float = 0.8) -> None:
    from models import _deko as dk
    cv = dk.Canvas(part, margin=rand, hole_margin=rand, seed=seed)
    for pts, closed in linien:
        if len(pts) >= 2:
            cv.draw(list(pts), closed, min_len=0.3)


def spiegel(pts: Sequence[Point]) -> List[Point]:
    return [(-x, y) for x, y in pts]


def skaliert(pts: Sequence[Point], u: float, dx: float = 0.0, dy: float = 0.0) -> List[Point]:
    return [(dx + x * u, dy + y * u) for x, y in pts]


def kreis(cx: float, cy: float, r: float, n: int = 28) -> List[Point]:
    return [(cx + r * math.cos(2 * math.pi * k / n), cy + r * math.sin(2 * math.pi * k / n)) for k in range(n)]
