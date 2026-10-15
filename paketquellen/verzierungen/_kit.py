"""
_kit.py – Zeichenbaukasten des Ebenen-Pakets.

Motive werden als „Figur“ gebaut: eine Folge von Flächen, die hinzugefügt (+) oder weggeschnitten (−)
werden. Überlappungen sind erlaubt, gerechnet wird über ein feines Raster (siehe Leinwand). So lassen
sich organische Silhouetten aus vielen Einzelformen zusammensetzen – Körper, Beine, Geweih, Zweige –
ohne heikle Polygon-Booleans.

Koordinaten in mm (bzw. Einheiten vor dem Platzieren), y nach oben.
"""
from __future__ import annotations

import math
import random
import zlib
from typing import Iterable, List, Optional, Sequence, Tuple

Point = Tuple[float, float]
Poly = List[Point]


# --------------------------------------------------------------------------------------------------
# Kurven
# --------------------------------------------------------------------------------------------------

def bez3(p0: Point, c1: Point, c2: Point, p1: Point, n: int = 16) -> Poly:
    out = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        out.append((u ** 3 * p0[0] + 3 * u * u * t * c1[0] + 3 * u * t * t * c2[0] + t ** 3 * p1[0],
                    u ** 3 * p0[1] + 3 * u * u * t * c1[1] + 3 * u * t * t * c2[1] + t ** 3 * p1[1]))
    return out


def bez(p0: Point, c: Point, p1: Point, n: int = 12) -> Poly:
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * c[0] + t * t * p1[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * c[1] + t * t * p1[1]) for t in (i / n for i in range(n + 1))]


def chain(*parts: Sequence[Point]) -> Poly:
    out: Poly = []
    for p in parts:
        for q in p:
            if not out or abs(out[-1][0] - q[0]) + abs(out[-1][1] - q[1]) > 1e-9:
                out.append(q)
    return out


def spline(pts: Sequence[Point], closed: bool = False, n: int = 10, tension: float = 0.5) -> Poly:
    """Catmull-Rom-Kurve durch die Punkte (zum Zeichnen von Hand: Stützpunkte setzen, glatte Linie)."""
    P = list(pts)
    m = len(P)
    if m < 3:
        return P
    out: Poly = []
    rng = range(m) if closed else range(m - 1)
    for i in rng:
        p0 = P[(i - 1) % m] if closed or i > 0 else P[0]
        p1 = P[i]
        p2 = P[(i + 1) % m]
        p3 = P[(i + 2) % m] if closed or i + 2 < m else P[-1]
        c1 = (p1[0] + (p2[0] - p0[0]) * tension / 3, p1[1] + (p2[1] - p0[1]) * tension / 3)
        c2 = (p2[0] - (p3[0] - p1[0]) * tension / 3, p2[1] - (p3[1] - p1[1]) * tension / 3)
        seg = bez3(p1, c1, c2, p2, n)
        out.extend(seg if not out else seg[1:])
    if closed and len(out) > 1:
        out.pop()
    return out


def arc(cx: float, cy: float, r: float, a0: float, a1: float, n: Optional[int] = None) -> Poly:
    n = n or max(6, int(abs(a1 - a0) * 18))
    return [(cx + r * math.cos(a0 + (a1 - a0) * i / n), cy + r * math.sin(a0 + (a1 - a0) * i / n))
            for i in range(n + 1)]


def ellipse(cx: float, cy: float, rx: float, ry: float, rot: float = 0.0, n: int = 48) -> Poly:
    c, s = math.cos(rot), math.sin(rot)
    out = []
    for i in range(n):
        a = 2 * math.pi * i / n
        x, y = rx * math.cos(a), ry * math.sin(a)
        out.append((cx + x * c - y * s, cy + x * s + y * c))
    return out


def circle(cx: float, cy: float, r: float, n: int = 0) -> Poly:
    return ellipse(cx, cy, r, r, 0.0, n or max(16, int(r * 6)))


def rect(x: float, y: float, w: float, h: float) -> Poly:
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]


def star(cx: float, cy: float, r_out: float, r_in: float, k: int = 5, rot: float = math.pi / 2) -> Poly:
    return [(cx + (r_out if i % 2 == 0 else r_in) * math.cos(rot + math.pi * i / k),
             cy + (r_out if i % 2 == 0 else r_in) * math.sin(rot + math.pi * i / k)) for i in range(2 * k)]


def sparkle(cx: float, cy: float, r: float, waist: float = 0.18, k: int = 4, rot: float = math.pi / 2) -> Poly:
    """Funkelstern mit eingezogenen, gebogenen Flanken."""
    out: Poly = []
    for i in range(k):
        a = rot + 2 * math.pi * i / k
        b = a + math.pi / k
        tip = (cx + r * math.cos(a), cy + r * math.sin(a))
        nxt = (cx + r * math.cos(a + 2 * math.pi / k), cy + r * math.sin(a + 2 * math.pi / k))
        mid = (cx + waist * r * math.cos(b), cy + waist * r * math.sin(b))
        out += bez(tip, mid, nxt, 10)[:-1]
    return out


def path_len(p: Sequence[Point]) -> float:
    return sum(math.hypot(p[i + 1][0] - p[i][0], p[i + 1][1] - p[i][1]) for i in range(len(p) - 1))


def resample(p: Sequence[Point], step: float) -> Poly:
    """Polylinie in gleichmäßigen Abständen neu abtasten."""
    L = path_len(p)
    n = max(2, int(L / step) + 1)
    out = [p[0]]
    seg = 0
    acc = 0.0
    for k in range(1, n):
        t = L * k / (n - 1)
        while seg < len(p) - 2 and acc + math.hypot(p[seg + 1][0] - p[seg][0], p[seg + 1][1] - p[seg][1]) < t:
            acc += math.hypot(p[seg + 1][0] - p[seg][0], p[seg + 1][1] - p[seg][1])
            seg += 1
        a, b = p[seg], p[seg + 1]
        sl = math.hypot(b[0] - a[0], b[1] - a[1]) or 1.0
        u = min(1.0, (t - acc) / sl)
        out.append((a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u))
    return out


def stroke(path: Sequence[Point], w0: float, w1: Optional[float] = None, cap: str = "rund",
           widths: Optional[Sequence[float]] = None) -> Poly:
    """Linie mit Breite w0 → w1 (oder je Punkt widths) als Fläche. cap: rund | spitz | flach."""
    path = [q for i, q in enumerate(path) if i == 0 or math.hypot(q[0] - path[i - 1][0], q[1] - path[i - 1][1]) > 1e-9]
    n = len(path)
    if n < 2:
        return []
    w1 = w0 if w1 is None else w1
    L = path_len(path) or 1.0
    right, left = [], []
    acc = 0.0
    for i, p in enumerate(path):
        if i:
            acc += math.hypot(p[0] - path[i - 1][0], p[1] - path[i - 1][1])
        if i == 0:
            d = (path[1][0] - p[0], path[1][1] - p[1])
        elif i == n - 1:
            d = (p[0] - path[i - 1][0], p[1] - path[i - 1][1])
        else:
            d = (path[i + 1][0] - path[i - 1][0], path[i + 1][1] - path[i - 1][1])
        dl = math.hypot(*d) or 1.0
        nx, ny = d[1] / dl, -d[0] / dl
        w = (widths[i] if widths else w0 + (w1 - w0) * acc / L) / 2
        right.append((p[0] + nx * w, p[1] + ny * w))
        left.append((p[0] - nx * w, p[1] - ny * w))

    def cap_at(p, d, w, out_dir):
        a = math.atan2(d[1], d[0])
        if cap == "rund" and w > 0:
            return [(p[0] + math.cos(a - math.pi / 2 + math.pi * k / 6) * w, p[1] + math.sin(a - math.pi / 2 + math.pi * k / 6) * w)
                    for k in range(1, 6)]
        if cap == "spitz":
            return [(p[0] + math.cos(a) * w * 1.6, p[1] + math.sin(a) * w * 1.6)]
        return []

    e = path[-1]
    de = (path[-1][0] - path[-2][0], path[-1][1] - path[-2][1])
    s = path[0]
    ds = (path[0][0] - path[1][0], path[0][1] - path[1][1])
    we = (widths[-1] if widths else w1) / 2
    ws = (widths[0] if widths else w0) / 2
    return right + cap_at(e, de, we, 1) + list(reversed(left)) + cap_at(s, ds, ws, -1)


# --------------------------------------------------------------------------------------------------
# Figur: Folge von + / − Flächen
# --------------------------------------------------------------------------------------------------

class Figur:
    def __init__(self, ops: Optional[List[Tuple[str, Poly]]] = None):
        self.ops: List[Tuple[str, Poly]] = list(ops or [])

    def add(self, *polys: Poly) -> "Figur":
        self.ops += [("+", list(p)) for p in polys if len(p) >= 3]
        return self

    def cut(self, *polys: Poly) -> "Figur":
        self.ops += [("-", list(p)) for p in polys if len(p) >= 3]
        return self

    def line(self, path: Sequence[Point], w0: float, w1: Optional[float] = None, cap: str = "rund") -> "Figur":
        return self.add(stroke(path, w0, w1, cap))

    def merge(self, other: "Figur") -> "Figur":
        self.ops += other.ops
        return self

    def map(self, f) -> "Figur":
        return Figur([(s, [f(p) for p in poly]) for s, poly in self.ops])

    def place(self, x: float, y: float, s: float, ang: float = 0.0, flip: bool = False, sy: Optional[float] = None) -> "Figur":
        """Skalieren (s, optional sy), spiegeln, drehen, verschieben."""
        ca, sa = math.cos(ang), math.sin(ang)
        sy = s if sy is None else sy

        def f(p):
            px, py = p
            if flip:
                px = -px
            px, py = px * s, py * sy
            return (x + px * ca - py * sa, y + px * sa + py * ca)
        return self.map(f)

    def bbox(self) -> Tuple[float, float, float, float]:
        pts = [q for s, p in self.ops if s == "+" for q in p]
        xs = [q[0] for q in pts]
        ys = [q[1] for q in pts]
        return min(xs), min(ys), max(xs), max(ys)


def rng(seed: int, *salt) -> random.Random:
    """Reproduzierbarer Zufall je Startwert und Zusatz (unabhängig von PYTHONHASHSEED)."""
    return random.Random(zlib.crc32(repr((seed,) + tuple(salt)).encode()))


def jitter(r: random.Random, a: float) -> float:
    return (r.random() * 2 - 1) * a
