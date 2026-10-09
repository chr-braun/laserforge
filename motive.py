"""
motive.py – eigene Motive importieren (SVG, PNG) und als Bibliothek verwalten.

Ein Motiv ist eine normierte Vektorform: die längere Seite ist 1, die Mitte liegt bei (0, 0), y nach oben.

  {"id": "katze-3f2a", "name": "Katze", "quelle": "svg", "w": 0.82, "h": 1.0,
   "flaechen": [{"aussen": [[x, y], …], "loecher": [[[x, y], …], …]}, …],
   "linien": [[[x, y], …], …]}

flaechen  gefüllte Bereiche (Außenkontur gegen den Uhrzeigersinn, Löcher im Uhrzeigersinn)
linien    reine Strichlinien aus SVGs (nur als Gravur nutzbar)

Import:
  SVG  path, rect, circle, ellipse, line, polyline, polygon, use; Transformationen; Füllregel.
       Überlappende Formen werden über ein feines Raster vereinigt.
  PNG  dunkle (bzw. deckende) Pixel werden zum Motiv und nachgezeichnet. JPG geht nicht.

Bibliothek: eingebaute Motive in ./motive, eigene im Benutzerordner
(macOS ~/Library/Application Support/Laserforge/Motive, sonst ~/.laserforge/motive,
oder erster Ordner aus $LASERFORGE_MOTIVE).

Nur Python-Standardbibliothek, lauffähig ab Python 3.8.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import struct
import sys
import unicodedata
import xml.etree.ElementTree as ET
import zlib
from typing import Dict, List, Optional, Sequence, Tuple

Point = Tuple[float, float]
Poly = List[Point]
Matrix = Tuple[float, float, float, float, float, float]          # a b c d e f wie in SVG

HERE = os.path.dirname(os.path.abspath(__file__))
BUILTIN_DIR = os.path.join(HERE, "motive")
MAX_BYTES = 8 * 1024 * 1024
MAX_PIXELS = 3000 * 3000
RASTER = 1200                       # Rasterauflösung (längere Seite) für Vereinigung und PNG


class MotivFehler(ValueError):
    pass


# ==================================================================================================
# Geometrie-Helfer
# ==================================================================================================

def area(p: Sequence[Point]) -> float:
    s = 0.0
    n = len(p)
    for i in range(n):
        x0, y0 = p[i]
        x1, y1 = p[(i + 1) % n]
        s += x0 * y1 - x1 * y0
    return s / 2.0


def bbox(polys: Sequence[Sequence[Point]]) -> Tuple[float, float, float, float]:
    xs = [x for p in polys for x, _ in p]
    ys = [y for p in polys for _, y in p]
    if not xs:
        raise MotivFehler("Die Datei enthält keine Form")
    return min(xs), min(ys), max(xs), max(ys)


def inside(pt: Point, poly: Sequence[Point]) -> bool:
    x, y = pt
    c = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-300) + xi:
            c = not c
        j = i
    return c


def simplify(pts: Sequence[Point], tol: float, closed: bool = True) -> Poly:
    """Douglas-Peucker (iterativ)."""
    pts = list(pts)
    if len(pts) < 4:
        return pts
    if closed:
        # an den zwei am weitesten entfernten Punkten aufteilen, damit die Naht nicht stört
        far = max(range(len(pts)), key=lambda i: (pts[i][0] - pts[0][0]) ** 2 + (pts[i][1] - pts[0][1]) ** 2)
        a = simplify(pts[:far + 1], tol, False)
        b = simplify(pts[far:] + [pts[0]], tol, False)
        return a[:-1] + b[:-1]
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    t2 = tol * tol
    while stack:
        i0, i1 = stack.pop()
        x0, y0 = pts[i0]
        x1, y1 = pts[i1]
        dx, dy = x1 - x0, y1 - y0
        L2 = dx * dx + dy * dy
        best, bi = -1.0, -1
        for i in range(i0 + 1, i1):
            px, py = pts[i]
            if L2 == 0:
                d2 = (px - x0) ** 2 + (py - y0) ** 2
            else:
                t = ((px - x0) * dx + (py - y0) * dy) / L2
                t = 0.0 if t < 0 else 1.0 if t > 1 else t
                d2 = (px - x0 - t * dx) ** 2 + (py - y0 - t * dy) ** 2
            if d2 > best:
                best, bi = d2, i
        if best > t2:
            keep[bi] = True
            stack += [(i0, bi), (bi, i1)]
    return [p for p, k in zip(pts, keep) if k]


def chaikin(pts: Sequence[Point], rounds: int = 1) -> Poly:
    """Ecken weich schleifen (geschlossene Kontur)."""
    p = list(pts)
    for _ in range(rounds):
        q: Poly = []
        n = len(p)
        for i in range(n):
            (x0, y0), (x1, y1) = p[i], p[(i + 1) % n]
            q += [(0.75 * x0 + 0.25 * x1, 0.75 * y0 + 0.25 * y1), (0.25 * x0 + 0.75 * x1, 0.25 * y0 + 0.75 * y1)]
        p = q
    return p


def _segs_cross(a: Point, b: Point, c: Point, d: Point) -> bool:
    def orient(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    o1, o2, o3, o4 = orient(a, b, c), orient(a, b, d), orient(c, d, a), orient(c, d, b)
    return (o1 > 0) != (o2 > 0) and (o3 > 0) != (o4 > 0) and o1 * o2 < 0 and o3 * o4 < 0


def any_crossing(polys: Sequence[Sequence[Point]]) -> bool:
    """Schneiden sich irgendwelche Kanten (auch innerhalb einer Kontur)? Rasterbasiertes Vorsortieren."""
    edges = []
    for pi, p in enumerate(polys):
        n = len(p)
        for i in range(n):
            edges.append((pi, i, n, p[i], p[(i + 1) % n]))
    if not edges:
        return False
    x0, y0, x1, y1 = bbox(polys)
    size = max(x1 - x0, y1 - y0) or 1.0
    cells = max(1, min(256, int(math.sqrt(len(edges)) / 2) + 1))
    cs = size / cells
    grid: Dict[Tuple[int, int], List[int]] = {}
    for k, (_, _, _, a, b) in enumerate(edges):
        for gx in range(int((min(a[0], b[0]) - x0) / cs), int((max(a[0], b[0]) - x0) / cs) + 1):
            for gy in range(int((min(a[1], b[1]) - y0) / cs), int((max(a[1], b[1]) - y0) / cs) + 1):
                grid.setdefault((gx, gy), []).append(k)
    seen = set()
    for lst in grid.values():
        for i in range(len(lst)):
            for j in range(i + 1, len(lst)):
                ki, kj = lst[i], lst[j]
                if (ki, kj) in seen:
                    continue
                seen.add((ki, kj))
                pi, ii, n, a, b = edges[ki]
                pj, ij, _, c, d = edges[kj]
                if pi == pj and (abs(ii - ij) <= 1 or abs(ii - ij) == n - 1):
                    continue
                if _segs_cross(a, b, c, d):
                    return True
    return False


# ==================================================================================================
# Raster: Füllen, Vereinigen, Nachzeichnen (Zeilen als Bitmasken in Python-Ganzzahlen)
# ==================================================================================================

class Raster:
    """Binärbild mit W×H Pixeln; rows[y] ist eine Ganzzahl, Bit x = Pixel (x, y). y = 0 ist oben."""

    def __init__(self, w: int, h: int):
        self.w, self.h = w, h
        self.rows = [0] * h

    def fill(self, polys: Sequence[Sequence[Point]], rule: str = "evenodd") -> "Raster":
        """Polygone (in Pixelkoordinaten, y nach unten) mit Füllregel in ein neues Raster zeichnen."""
        out = Raster(self.w, self.h)
        edges = []
        for p in polys:
            n = len(p)
            for i in range(n):
                (xa, ya), (xb, yb) = p[i], p[(i + 1) % n]
                if ya == yb:
                    continue
                edges.append((min(ya, yb), max(ya, yb), xa, ya, xb, yb, 1 if yb > ya else -1))
        edges.sort()
        active: list = []
        k = 0
        full = (1 << self.w) - 1
        for y in range(self.h):
            yc = y + 0.5
            while k < len(edges) and edges[k][0] <= yc:
                active.append(edges[k])
                k += 1
            active = [e for e in active if e[1] > yc]
            xs = []
            for (_, _, xa, ya, xb, yb, wdir) in active:
                if ya <= yc < yb or yb <= yc < ya:
                    xs.append((xa + (yc - ya) * (xb - xa) / (yb - ya), wdir))
            if not xs:
                continue
            xs.sort()
            row = 0
            wn = 0
            for i, (x, wdir) in enumerate(xs[:-1]):
                wn = (wn + 1) if rule == "evenodd" else wn + wdir
                on = (wn % 2 == 1) if rule == "evenodd" else wn != 0
                if on:
                    a = max(0, int(math.floor(x + 0.5)))
                    b = min(self.w, int(math.floor(xs[i + 1][0] + 0.5)))
                    if b > a:
                        row |= ((1 << (b - a)) - 1) << a
            out.rows[y] = row & full
        return out

    def union(self, other: "Raster") -> "Raster":
        out = Raster(self.w, self.h)
        out.rows = [a | b for a, b in zip(self.rows, other.rows)]
        return out

    def dilate(self, n: int = 1) -> "Raster":
        """Um n Pixel wachsen (abwechselnd Kreuz- und Quadrat-Nachbarschaft ≈ rund)."""
        full = (1 << self.w) - 1
        rows = list(self.rows)
        for k in range(n):
            new = []
            for y in range(self.h):
                r = rows[y]
                up = rows[y - 1] if y > 0 else 0
                dn = rows[y + 1] if y + 1 < self.h else 0
                v = r | (r << 1) | (r >> 1) | up | dn
                if k % 2:
                    v |= (up << 1) | (up >> 1) | (dn << 1) | (dn >> 1)
                new.append(v & full)
            rows = new
        out = Raster(self.w, self.h)
        out.rows = rows
        return out

    def invert(self) -> "Raster":
        full = (1 << self.w) - 1
        out = Raster(self.w, self.h)
        out.rows = [full ^ r for r in self.rows]
        return out

    def erode(self, n: int = 1) -> "Raster":
        return self.invert().dilate(n).invert()

    def close(self, n: int) -> "Raster":
        """Schließen: schmale Kerben und Spalten bis 2n Pixel füllen."""
        return self.dilate(n).erode(n) if n > 0 else self

    def open(self, n: int) -> "Raster":
        """Öffnen: dünne Spitzen und Stege bis 2n Pixel entfernen."""
        return self.erode(n).dilate(n) if n > 0 else self

    def count(self) -> int:
        return sum(bin(r).count("1") for r in self.rows)

    def trace(self) -> List[Poly]:
        """Pixelkanten zu geschlossenen Konturen verketten (Bild-Koordinaten, Vordergrund rechts der Laufrichtung).
        Außenkonturen haben dann positive, Löcher negative Fläche im y-unten-System."""
        nxt: Dict[Tuple[int, int], List[Tuple[int, int]]] = {}

        def edge(a, b):
            nxt.setdefault(a, []).append(b)

        H = self.h
        prev = 0
        for y in range(H + 1):
            cur = self.rows[y] if y < H else 0
            d = prev ^ cur
            while d:
                low = d & -d
                x = low.bit_length() - 1
                d ^= low
                if cur & low:                       # Pixel (x, y) gefüllt, darüber leer → Oberkante
                    edge((x, y), (x + 1, y))
                else:                               # Pixel (x, y-1) gefüllt, darunter leer → Unterkante
                    edge((x + 1, y), (x, y))
            if y < H and cur:
                t = cur ^ (cur << 1)                # Bit x: Pixel x unterscheidet sich von Pixel x-1
                while t:
                    low = t & -t
                    x = low.bit_length() - 1
                    t ^= low
                    if (cur >> x) & 1:                     # links leer, Pixel x gefüllt → linke Kante
                        edge((x, y + 1), (x, y))
                    else:                                            # Pixel x-1 gefüllt → rechte Kante
                        edge((x, y), (x, y + 1))
            prev = cur
        loops: List[Poly] = []
        while nxt:
            start = next(iter(nxt))
            loop = [start]
            cur_pt = start
            came: Optional[Tuple[int, int]] = None
            while True:
                outs = nxt.get(cur_pt)
                if not outs:
                    break
                if len(outs) == 1:
                    nx = outs.pop()
                else:                                # Sattelpunkt: rechts abbiegen (Diagonale trennt)
                    dx0, dy0 = (cur_pt[0] - came[0], cur_pt[1] - came[1]) if came else (1, 0)
                    def turn(o):
                        dx1, dy1 = o[0] - cur_pt[0], o[1] - cur_pt[1]
                        return dx0 * dy1 - dy0 * dx1           # >0 = rechts im y-unten-System
                    nx = max(outs, key=turn)
                    outs.remove(nx)
                if not outs:
                    del nxt[cur_pt]
                came, cur_pt = cur_pt, nx
                if cur_pt == start:
                    break
                loop.append(cur_pt)
            if len(loop) >= 4:
                loops.append([(float(x), float(y)) for x, y in _corners(loop)])
        return loops


def _corners(loop: Sequence[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """Nur die Eckpunkte einer Pixelkontur behalten."""
    out = []
    n = len(loop)
    for i in range(n):
        a, b, c = loop[i - 1], loop[i], loop[(i + 1) % n]
        if (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0]) != 0:
            out.append(b)
    return out


def raster_to_areas(r: Raster, tol: float = 0.7, smooth: int = 1, min_px: float = 6.0) -> List[dict]:
    """Raster → Flächen (Pixelkoordinaten, y nach unten → hier schon nach oben gedreht)."""
    loops = r.trace()
    outs, holes = [], []
    for lp in loops:
        a = area(lp)                                       # y unten: Außen positiv
        if abs(a) < min_px:
            continue
        p = simplify(lp, tol)
        if smooth:
            p = chaikin(p, smooth)
            p = simplify(p, tol * 0.25)
        if len(p) < 3:
            continue
        p = [(x, r.h - y) for x, y in p]                   # y nach oben
        (outs if a > 0 else holes).append(p)
    return nest(outs, holes)


def nest(outs: List[Poly], holes: List[Poly]) -> List[dict]:
    """Löcher der kleinsten umgebenden Außenkontur zuordnen; Orientierung CCW/CW herstellen."""
    outs = [o if area(o) > 0 else o[::-1] for o in outs]
    holes = [h if area(h) < 0 else h[::-1] for h in holes]
    res = [dict(aussen=o, loecher=[]) for o in sorted(outs, key=lambda o: -area(o))]
    for h in holes:
        best, ba = None, math.inf
        for f in res:
            a = area(f["aussen"])
            if a < ba and inside(h[0], f["aussen"]) and inside(h[len(h) // 2], f["aussen"]):
                best, ba = f, a
        if best is not None:
            best["loecher"].append(h)
    return res


def polys_to_areas(polys: List[Poly]) -> List[dict]:
    """Saubere (überschneidungsfreie) Konturen nach Verschachtelungstiefe in Flächen/Löcher teilen (gerade/ungerade)."""
    polys = [p for p in polys if len(p) >= 3 and abs(area(p)) > 0]
    depth = []
    for i, p in enumerate(polys):
        probe = p[0]
        depth.append(sum(1 for j, q in enumerate(polys) if j != i and abs(area(q)) > abs(area(p)) * 0.999999
                         and inside(probe, q)))
    outs = [p for p, d in zip(polys, depth) if d % 2 == 0]
    holes = [p for p, d in zip(polys, depth) if d % 2 == 1]
    return nest(outs, holes)


# ==================================================================================================
# SVG lesen
# ==================================================================================================

_NUM = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")
_CMD = re.compile(r"([MmZzLlHhVvCcSsQqTtAa])")
IDENT: Matrix = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)


def _mul(m: Matrix, n: Matrix) -> Matrix:
    a, b, c, d, e, f = m
    a2, b2, c2, d2, e2, f2 = n
    return (a * a2 + c * b2, b * a2 + d * b2, a * c2 + c * d2, b * c2 + d * d2,
            a * e2 + c * f2 + e, b * e2 + d * f2 + f)


def _apply(m: Matrix, p: Point) -> Point:
    a, b, c, d, e, f = m
    return (a * p[0] + c * p[1] + e, b * p[0] + d * p[1] + f)


def parse_transform(s: str) -> Matrix:
    m = IDENT
    for name, args in re.findall(r"(\w+)\s*\(([^)]*)\)", s or ""):
        v = [float(x) for x in _NUM.findall(args)]
        if name == "matrix" and len(v) == 6:
            t = tuple(v)
        elif name == "translate" and v:
            t = (1, 0, 0, 1, v[0], v[1] if len(v) > 1 else 0.0)
        elif name == "scale" and v:
            t = (v[0], 0, 0, v[1] if len(v) > 1 else v[0], 0, 0)
        elif name == "rotate" and v:
            r = math.radians(v[0])
            cs, sn = math.cos(r), math.sin(r)
            t = (cs, sn, -sn, cs, 0, 0)
            if len(v) >= 3:
                t = _mul(_mul((1, 0, 0, 1, v[1], v[2]), t), (1, 0, 0, 1, -v[1], -v[2]))
        elif name == "skewX" and v:
            t = (1, 0, math.tan(math.radians(v[0])), 1, 0, 0)
        elif name == "skewY" and v:
            t = (1, math.tan(math.radians(v[0])), 0, 1, 0, 0)
        else:
            continue
        m = _mul(m, t)                                    # type: ignore[arg-type]
    return m


def _flags_split(tokens: str) -> List[float]:
    """Zahlen eines Pfads (ohne Bogen-Flags, siehe _arc_numbers)."""
    return [float(x) for x in _NUM.findall(tokens)]


def _arc_numbers(s: str) -> List[float]:
    out: List[float] = []
    i, n = 0, len(s)
    k = 0
    while i < n:
        while i < n and s[i] in " ,\t\r\n":
            i += 1
        if i >= n:
            break
        if k % 7 in (3, 4) and s[i] in "01":
            out.append(float(s[i]))
            i += 1
        else:
            m = _NUM.match(s, i)
            if not m:
                raise MotivFehler("SVG-Pfad nicht lesbar (Bogen)")
            out.append(float(m.group()))
            i = m.end()
        k += 1
    return out


def _arc_to_beziers(p0: Point, rx: float, ry: float, phi: float, fa: bool, fs: bool, p1: Point) -> List[Tuple[Point, Point, Point]]:
    """SVG-Bogen → kubische Bézierkurven (Endpunkt- → Mittelpunktdarstellung nach SVG-Spezifikation)."""
    if p0 == p1:
        return []
    rx, ry = abs(rx), abs(ry)
    if rx == 0 or ry == 0:
        return [(p0, p1, p1)]
    cp, sp = math.cos(phi), math.sin(phi)
    dx, dy = (p0[0] - p1[0]) / 2, (p0[1] - p1[1]) / 2
    x1, y1 = cp * dx + sp * dy, -sp * dx + cp * dy
    lam = (x1 / rx) ** 2 + (y1 / ry) ** 2
    if lam > 1:
        rx, ry = rx * math.sqrt(lam), ry * math.sqrt(lam)
    num = rx * rx * ry * ry - rx * rx * y1 * y1 - ry * ry * x1 * x1
    den = rx * rx * y1 * y1 + ry * ry * x1 * x1
    co = math.sqrt(max(0.0, num / den)) if den else 0.0
    if fa == fs:
        co = -co
    cx1, cy1 = co * rx * y1 / ry, -co * ry * x1 / rx
    cx = cp * cx1 - sp * cy1 + (p0[0] + p1[0]) / 2
    cy = sp * cx1 + cp * cy1 + (p0[1] + p1[1]) / 2

    def ang(ux, uy, vx, vy):
        a = math.atan2(ux * vy - uy * vx, ux * vx + uy * vy)
        return a
    t1 = ang(1, 0, (x1 - cx1) / rx, (y1 - cy1) / ry)
    dt = ang((x1 - cx1) / rx, (y1 - cy1) / ry, (-x1 - cx1) / rx, (-y1 - cy1) / ry)
    if not fs and dt > 0:
        dt -= 2 * math.pi
    elif fs and dt < 0:
        dt += 2 * math.pi
    nseg = max(1, int(math.ceil(abs(dt) / (math.pi / 2) - 1e-9)))
    d = dt / nseg
    k = 4 / 3 * math.tan(d / 4)
    out = []

    def pt(t):
        return (cx + rx * math.cos(t) * cp - ry * math.sin(t) * sp, cy + rx * math.cos(t) * sp + ry * math.sin(t) * cp)

    def dv(t):
        return (-rx * math.sin(t) * cp - ry * math.cos(t) * sp, -rx * math.sin(t) * sp + ry * math.cos(t) * cp)
    t = t1
    for _ in range(nseg):
        a, b = pt(t), pt(t + d)
        da, db = dv(t), dv(t + d)
        out.append(((a[0] + k * da[0], a[1] + k * da[1]), (b[0] - k * db[0], b[1] - k * db[1]), b))
        t += d
    return out


def parse_path(d: str) -> List[Tuple[List[tuple], bool]]:
    """Pfaddaten → Unterpfade aus Segmenten ('L', p) / ('C', c1, c2, p) / ('Q', c, p); (segmente, geschlossen).
    Jedes Unterpfad-Segment beginnt mit ('M', p)."""
    subs: List[Tuple[List[tuple], bool]] = []
    cur: List[tuple] = []
    x = y = 0.0
    sx = sy = 0.0
    last_c: Optional[Point] = None
    last_q: Optional[Point] = None
    prev = ""
    parts = _CMD.split(d or "")
    i = 1
    while i < len(parts):
        cmd, args = parts[i], parts[i + 1] if i + 1 < len(parts) else ""
        i += 2
        rel = cmd.islower()
        C = cmd.upper()
        nums = _arc_numbers(args) if C == "A" else _flags_split(args)
        if C == "Z":
            if cur:
                subs.append((cur, True))
                cur = []
            x, y = sx, sy
            last_c = last_q = None
            prev = "Z"
            continue
        sizes = {"M": 2, "L": 2, "H": 1, "V": 1, "C": 6, "S": 4, "Q": 4, "T": 2, "A": 7}[C]
        if len(nums) < sizes or len(nums) % sizes:
            if len(nums) < sizes:
                raise MotivFehler(f"SVG-Pfad nicht lesbar ({cmd} mit {len(nums)} Zahlen)")
            nums = nums[:len(nums) - len(nums) % sizes]
        for j in range(0, len(nums), sizes):
            v = nums[j:j + sizes]
            ox, oy = (x, y) if rel else (0.0, 0.0)
            if C == "M":
                if j == 0:
                    if cur:
                        subs.append((cur, False))
                    x, y = ox + v[0], oy + v[1]
                    sx, sy = x, y
                    cur = [("M", (x, y))]
                    last_c = last_q = None
                    continue
                C2 = "L"                                         # weitere Paare nach M = Linien
            else:
                C2 = C
            if not cur:
                cur = [("M", (x, y))]
                sx, sy = x, y
            if C2 == "L":
                x, y = ox + v[0], oy + v[1]
                cur.append(("L", (x, y)))
                last_c = last_q = None
            elif C2 == "H":
                x = (x if rel else 0.0) + v[0]
                cur.append(("L", (x, y)))
                last_c = last_q = None
            elif C2 == "V":
                y = (y if rel else 0.0) + v[0]
                cur.append(("L", (x, y)))
                last_c = last_q = None
            elif C2 == "C":
                c1 = (ox + v[0], oy + v[1])
                c2 = (ox + v[2], oy + v[3])
                x, y = ox + v[4], oy + v[5]
                cur.append(("C", c1, c2, (x, y)))
                last_c, last_q = c2, None
            elif C2 == "S":
                c1 = (2 * x - last_c[0], 2 * y - last_c[1]) if last_c and prev in "CScs" else (x, y)
                c2 = (ox + v[0], oy + v[1])
                x, y = ox + v[2], oy + v[3]
                cur.append(("C", c1, c2, (x, y)))
                last_c, last_q = c2, None
            elif C2 == "Q":
                c = (ox + v[0], oy + v[1])
                x, y = ox + v[2], oy + v[3]
                cur.append(("Q", c, (x, y)))
                last_q, last_c = c, None
            elif C2 == "T":
                c = (2 * x - last_q[0], 2 * y - last_q[1]) if last_q and prev in "QTqt" else (x, y)
                x, y = ox + v[0], oy + v[1]
                cur.append(("Q", c, (x, y)))
                last_q, last_c = c, None
            elif C2 == "A":
                p1 = (ox + v[5], oy + v[6])
                for c1, c2, p in _arc_to_beziers((x, y), v[0], v[1], math.radians(v[2]), bool(v[3]), bool(v[4]), p1):
                    cur.append(("C", c1, c2, p))
                x, y = p1
                last_c = last_q = None
            prev = cmd
        prev = cmd
    if cur:
        subs.append((cur, False))
    return subs


def flatten(segs: List[tuple], m: Matrix, tol: float) -> Poly:
    """Segmente transformieren und Kurven in Strecken auflösen (Toleranz in Zielkoordinaten)."""
    pts: Poly = []
    p = None
    for s in segs:
        if s[0] in ("M", "L"):
            p = _apply(m, s[1])
            pts.append(p)
            continue
        ctrl = [p] + [_apply(m, q) for q in s[1:]]
        L = sum(math.hypot(ctrl[k + 1][0] - ctrl[k][0], ctrl[k + 1][1] - ctrl[k][1]) for k in range(len(ctrl) - 1))
        n = max(2, min(200, int(math.sqrt(L / max(tol, 1e-12)) * 0.9) + 2))
        for k in range(1, n + 1):
            t = k / n
            u = 1 - t
            if s[0] == "C":
                x = u ** 3 * ctrl[0][0] + 3 * u * u * t * ctrl[1][0] + 3 * u * t * t * ctrl[2][0] + t ** 3 * ctrl[3][0]
                y = u ** 3 * ctrl[0][1] + 3 * u * u * t * ctrl[1][1] + 3 * u * t * t * ctrl[2][1] + t ** 3 * ctrl[3][1]
            else:
                x = u * u * ctrl[0][0] + 2 * u * t * ctrl[1][0] + t * t * ctrl[2][0]
                y = u * u * ctrl[0][1] + 2 * u * t * ctrl[1][1] + t * t * ctrl[2][1]
            pts.append((x, y))
        p = pts[-1]
    out: Poly = []
    for q in pts:
        if not out or abs(q[0] - out[-1][0]) + abs(q[1] - out[-1][1]) > tol * 1e-3:
            out.append(q)
    return out


def _style(el: ET.Element, inherited: Dict[str, str]) -> Dict[str, str]:
    st = dict(inherited)
    for k in ("fill", "stroke", "stroke-width", "fill-rule", "display", "visibility", "opacity", "fill-opacity"):
        if el.get(k) is not None:
            st[k] = el.get(k).strip()
    for item in (el.get("style") or "").split(";"):
        if ":" in item:
            k, v = item.split(":", 1)
            st[k.strip()] = v.strip()
    return st


def _num(v: Optional[str], default: float = 0.0, ref: float = 0.0) -> float:
    if v is None:
        return default
    v = v.strip()
    m = _NUM.match(v)
    if not m:
        return default
    f = float(m.group())
    if v.endswith("%"):
        return f / 100.0 * ref
    return f


def _tag(el: ET.Element) -> str:
    t = el.tag
    return t.rsplit("}", 1)[-1] if isinstance(t, str) else ""


def _shape_segments(el: ET.Element, tag: str, ref: float) -> List[Tuple[List[tuple], bool]]:
    g = lambda k, d=0.0: _num(el.get(k), d, ref)              # noqa: E731
    if tag == "path":
        return parse_path(el.get("d") or "")
    if tag == "rect":
        x, y, w, h = g("x"), g("y"), g("width"), g("height")
        if w <= 0 or h <= 0:
            return []
        rx, ry = el.get("rx"), el.get("ry")
        rx_ = _num(rx if rx is not None else ry, 0.0, ref)
        ry_ = _num(ry if ry is not None else rx, 0.0, ref)
        rx_, ry_ = min(rx_, w / 2), min(ry_, h / 2)
        if rx_ <= 0 or ry_ <= 0:
            return [([("M", (x, y)), ("L", (x + w, y)), ("L", (x + w, y + h)), ("L", (x, y + h))], True)]
        d = (f"M{x + rx_},{y} H{x + w - rx_} A{rx_},{ry_} 0 0 1 {x + w},{y + ry_} V{y + h - ry_} "
             f"A{rx_},{ry_} 0 0 1 {x + w - rx_},{y + h} H{x + rx_} A{rx_},{ry_} 0 0 1 {x},{y + h - ry_} "
             f"V{y + ry_} A{rx_},{ry_} 0 0 1 {x + rx_},{y} Z")
        return parse_path(d)
    if tag in ("circle", "ellipse"):
        cx, cy = g("cx"), g("cy")
        rx = g("r") if tag == "circle" else g("rx")
        ry = g("r") if tag == "circle" else g("ry")
        if rx <= 0 or ry <= 0:
            return []
        return parse_path(f"M{cx + rx},{cy} A{rx},{ry} 0 1 1 {cx - rx},{cy} A{rx},{ry} 0 1 1 {cx + rx},{cy} Z")
    if tag == "line":
        return [([("M", (g("x1"), g("y1"))), ("L", (g("x2"), g("y2")))], False)]
    if tag in ("polyline", "polygon"):
        v = [float(x) for x in _NUM.findall(el.get("points") or "")]
        pts = [(v[i], v[i + 1]) for i in range(0, len(v) - 1, 2)]
        if len(pts) < 2:
            return []
        return [([("M", pts[0])] + [("L", p) for p in pts[1:]], tag == "polygon")]
    return []


SKIP = {"defs", "clipPath", "mask", "symbol", "marker", "pattern", "title", "desc", "metadata", "style", "script",
        "linearGradient", "radialGradient", "filter", "foreignObject", "namedview"}


def read_svg(data: bytes) -> dict:
    """SVG-Bytes → Rohmotiv {flaechen, linien} in SVG-Koordinaten (y nach unten)."""
    if len(data) > MAX_BYTES:
        raise MotivFehler("Datei zu groß (höchstens 8 MB)")
    head = data[:4096].lower()
    if b"<!entity" in data.lower():
        raise MotivFehler("SVG mit Entity-Definitionen wird aus Sicherheitsgründen nicht gelesen")
    if b"<svg" not in data.lower() and b"<svg" not in head:
        raise MotivFehler("Das ist keine SVG-Datei")
    try:
        root = ET.fromstring(data)
    except ET.ParseError as e:
        raise MotivFehler(f"SVG nicht lesbar: {e}")
    if _tag(root) != "svg":
        raise MotivFehler("Das ist keine SVG-Datei")
    ids = {}
    for el in root.iter():
        if el.get("id"):
            ids[el.get("id")] = el
    vb = [float(x) for x in _NUM.findall(root.get("viewBox") or "")]
    ref = math.hypot(vb[2], vb[3]) / math.sqrt(2) if len(vb) == 4 else 100.0

    shapes: List[Tuple[List[Tuple[List[tuple], bool]], Matrix, Dict[str, str]]] = []
    texts = [0]

    def walk(el: ET.Element, m: Matrix, st: Dict[str, str], depth: int):
        if depth > 40:
            return
        tag = _tag(el)
        if tag in SKIP:
            return
        s = _style(el, st)
        if s.get("display") == "none" or s.get("visibility") == "hidden":
            return
        try:
            if float(_NUM.match(s.get("opacity", "1")).group()) == 0:
                return
        except (AttributeError, ValueError):
            pass
        m2 = _mul(m, parse_transform(el.get("transform") or "")) if el.get("transform") else m
        if tag == "use":
            href = el.get("href") or el.get("{http://www.w3.org/1999/xlink}href") or ""
            target = ids.get(href.lstrip("#"))
            if target is not None and target is not el:
                m3 = _mul(m2, (1, 0, 0, 1, _num(el.get("x")), _num(el.get("y"))))
                if _tag(target) == "symbol":
                    for ch in target:
                        walk(ch, m3, s, depth + 1)
                else:
                    walk(target, m3, s, depth + 1)
            return
        if tag in ("text", "tspan"):
            texts[0] += 1
            return
        segs = _shape_segments(el, tag, ref)
        if segs:
            shapes.append((segs, m2, s))
        for ch in el:
            walk(ch, m2, s, depth + 1)

    walk(root, IDENT, {"fill": "black"}, 0)
    if not shapes:
        if texts[0]:
            raise MotivFehler("Die SVG enthält nur Text – im Grafikprogramm erst in Pfade umwandeln")
        raise MotivFehler("Die SVG enthält keine Formen")
    # Toleranz aus der Gesamtgröße (Kontrollpunkte reichen dafür)
    allp = []
    for segs, m, _ in shapes:
        for sg, _c in segs:
            for s_ in sg:
                for q in s_[1:]:
                    allp.append(_apply(m, q))
    x0, y0, x1, y1 = bbox([allp])
    size = max(x1 - x0, y1 - y0)
    if size <= 0:
        raise MotivFehler("Die Formen in der SVG haben keine Ausdehnung")
    tol = size / 3000.0
    groups: List[Tuple[List[Poly], str, bool]] = []
    lines: List[Poly] = []
    for segs, m, st in shapes:
        fill = (st.get("fill") or "black").lower()
        stroke = (st.get("stroke") or "none").lower()
        filled = fill not in ("none", "transparent") and st.get("fill-opacity", "1") not in ("0", "0.0")
        polys = []
        for sg, closed in segs:
            pts = flatten(sg, m, tol)
            if filled and len(pts) >= 3:
                polys.append(pts)
            elif stroke not in ("none", "transparent") and len(pts) >= 2:
                lines.append(pts + ([pts[0]] if closed else []))
        if polys:
            groups.append((polys, "nonzero" if st.get("fill-rule", "nonzero") == "nonzero" else "evenodd",
                           _is_white(fill)))
    return dict(groups=groups, lines=lines, texts=texts[0])


def _is_white(fill: str) -> bool:
    f = fill.replace(" ", "")
    return f in ("white", "#fff", "#ffffff", "rgb(255,255,255)", "rgb(100%,100%,100%)")


def svg_to_motif(data: bytes) -> dict:
    raw = read_svg(data)
    polys = [p for g, _, _ in raw["groups"] for p in g]
    flaechen: List[dict] = []
    if polys:
        simple = not any(w for _, _, w in raw["groups"]) and all(
            r == "evenodd" or len(g) == 1 or _same_nesting_ok(g) for g, r, _ in raw["groups"])
        if simple and not any_crossing(polys):
            flaechen = polys_to_areas([[(x, -y) for x, y in p] for p in polys])
        else:
            flaechen = _raster_union(raw["groups"])
    lines = [[(x, -y) for x, y in p] for p in raw["lines"]]
    if not flaechen and not lines:
        raise MotivFehler("Die SVG enthält keine verwertbaren Formen")
    return normalize(dict(flaechen=flaechen, linien=lines))


def _same_nesting_ok(polys: List[Poly]) -> bool:
    """Bei Füllregel nonzero ist gerade/ungerade nur richtig, wenn verschachtelte Konturen gegenläufig sind."""
    for i, p in enumerate(polys):
        for j, q in enumerate(polys):
            if i != j and abs(area(q)) > abs(area(p)) and inside(p[0], q) and (area(p) > 0) == (area(q) > 0):
                return False
    return True


def _raster_union(groups: List[Tuple[List[Poly], str, bool]]) -> List[dict]:
    """Formen in Malreihenfolge rastern: dunkle Füllung kommt dazu, weiße Füllung radiert aus."""
    allp = [p for g, _, w in groups for p in g if not w] or [p for g, _, _ in groups for p in g]
    x0, y0, x1, y1 = bbox(allp)
    size = max(x1 - x0, y1 - y0)
    k = (RASTER - 4) / size
    W = int((x1 - x0) * k) + 4
    H = int((y1 - y0) * k) + 4
    acc = Raster(W, H)
    full = (1 << W) - 1
    for polys, rule, white in groups:
        px = [[((x - x0) * k + 2, (y - y0) * k + 2) for x, y in p] for p in polys]
        layer = acc.fill(px, rule)
        if white:
            acc.rows = [a & (full ^ b) for a, b in zip(acc.rows, layer.rows)]
        else:
            acc = acc.union(layer)
    areas = raster_to_areas(acc)
    # zurück in SVG-Koordinaten mit y nach oben (raster_to_areas hat y schon gedreht: y' = H - y_px)
    out = []
    for f in areas:
        conv = lambda p: [((x - 2) / k + x0, (y - H + 2) / k - y0) for x, y in p]     # noqa: E731
        out.append(dict(aussen=conv(f["aussen"]), loecher=[conv(h) for h in f["loecher"]]))
    return out


# ==================================================================================================
# PNG lesen
# ==================================================================================================

def read_png(data: bytes) -> Tuple[int, int, List[bytearray], List[bytearray]]:
    """PNG → (Breite, Höhe, Zeilen als Graustufen 0–255, Alpha-Zeilen oder leer). Nur Standardbibliothek."""
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        if data[:3] == b"\xff\xd8\xff":
            raise MotivFehler("JPG kann Laserforge nicht lesen – bitte als PNG (dunkles Motiv auf hellem Grund) "
                              "oder SVG speichern")
        raise MotivFehler("Das ist keine PNG-Datei")
    pos = 8
    ihdr = None
    plte = b""
    trns = b""
    idat = []
    while pos + 8 <= len(data):
        n, typ = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + n]
        pos += 12 + n
        if typ == b"IHDR":
            ihdr = struct.unpack(">IIBBBBB", body)
        elif typ == b"PLTE":
            plte = body
        elif typ == b"tRNS":
            trns = body
        elif typ == b"IDAT":
            idat.append(body)
        elif typ == b"IEND":
            break
    if not ihdr:
        raise MotivFehler("PNG ohne Kopfdaten")
    w, h, depth, ctype, _, _, interlace = ihdr
    if w * h > MAX_PIXELS:
        raise MotivFehler(f"PNG zu groß ({w}×{h}) – bitte auf höchstens 3000×3000 Pixel verkleinern")
    if interlace:
        raise MotivFehler("PNG mit Zeilensprung (interlaced) – bitte ohne Interlace speichern")
    chans = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(ctype)
    if chans is None:
        raise MotivFehler("PNG-Farbtyp wird nicht unterstützt")
    try:
        raw = zlib.decompress(b"".join(idat))
    except zlib.error:
        raise MotivFehler("PNG-Daten beschädigt")
    bpp_bits = chans * depth
    stride = (w * bpp_bits + 7) // 8
    bpp = max(1, bpp_bits // 8)
    if len(raw) < h * (stride + 1):
        raise MotivFehler("PNG-Daten unvollständig")
    prev = bytearray(stride)
    gray_rows: List[bytearray] = []
    alpha_rows: List[bytearray] = []
    pal = [tuple(plte[i:i + 3]) for i in range(0, len(plte) - 2, 3)]
    pal_a = list(trns) + [255] * (256 - len(trns)) if ctype == 3 else []
    for y in range(h):
        f = raw[y * (stride + 1)]
        line = bytearray(raw[y * (stride + 1) + 1:(y + 1) * (stride + 1)])
        if f == 1:
            for i in range(bpp, stride):
                line[i] = (line[i] + line[i - bpp]) & 255
        elif f == 2:
            line = bytearray((a + b) & 255 for a, b in zip(line, prev))
        elif f == 3:
            for i in range(stride):
                left = line[i - bpp] if i >= bpp else 0
                line[i] = (line[i] + ((left + prev[i]) >> 1)) & 255
        elif f == 4:
            for i in range(stride):
                a = line[i - bpp] if i >= bpp else 0
                b = prev[i]
                c = prev[i - bpp] if i >= bpp else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pr = a if pa <= pb and pa <= pc else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 255
        elif f != 0:
            raise MotivFehler("PNG-Daten beschädigt (Filter)")
        prev = line
        g = bytearray(w)
        al = bytearray(w)
        if depth < 8:
            mx = (1 << depth) - 1
            for x in range(w):
                bit = x * depth
                v = (line[bit >> 3] >> (8 - depth - (bit & 7))) & mx
                if ctype == 3:
                    r, gg, b = pal[v] if v < len(pal) else (0, 0, 0)
                    g[x] = (r * 299 + gg * 587 + b * 114) // 1000
                    al[x] = pal_a[v]
                else:
                    g[x] = v * 255 // mx
                    al[x] = 255
        else:
            step = depth // 8
            for x in range(w):
                o = x * chans * step
                if ctype == 0:
                    g[x] = line[o]
                    al[x] = 255
                elif ctype == 2:
                    g[x] = (line[o] * 299 + line[o + step] * 587 + line[o + 2 * step] * 114) // 1000
                    al[x] = 255
                elif ctype == 3:
                    r, gg, b = pal[line[o]] if line[o] < len(pal) else (0, 0, 0)
                    g[x] = (r * 299 + gg * 587 + b * 114) // 1000
                    al[x] = pal_a[line[o]]
                elif ctype == 4:
                    g[x] = line[o]
                    al[x] = line[o + step]
                else:
                    g[x] = (line[o] * 299 + line[o + step] * 587 + line[o + 2 * step] * 114) // 1000
                    al[x] = line[o + 3 * step]
        gray_rows.append(g)
        alpha_rows.append(al)
    has_alpha = ctype in (4, 6) or (ctype == 3 and bool(trns))
    return w, h, gray_rows, alpha_rows if has_alpha else []


def png_to_motif(data: bytes, invert: bool = False, schwelle: int = 128) -> dict:
    w, h, gray, alpha = read_png(data)
    use_alpha = False
    if alpha:
        transp = sum(row.count(0) for row in alpha)
        use_alpha = transp > 0.05 * w * h
    k = min(1.0, RASTER / max(w, h))
    W, H = max(1, int(w * k)), max(1, int(h * k))
    r = Raster(W + 4, H + 4)
    for yy in range(H):
        sy = min(h - 1, int((yy + 0.5) / k))
        g, al = gray[sy], (alpha[sy] if alpha else None)
        row = 0
        for xx in range(W):
            sx = min(w - 1, int((xx + 0.5) / k))
            if use_alpha:                          # freigestelltes Bild: deckende Pixel sind das Motiv
                on = (al[sx] >= 128) != invert
            else:
                on = (g[sx] < schwelle) != invert
            if on:
                row |= 1 << (xx + 2)
        r.rows[yy + 2] = row
    cnt = r.count()
    if cnt == 0:
        raise MotivFehler("Im Bild ist kein Motiv zu erkennen – dunkles Motiv auf hellem Grund verwenden "
                          "(oder „Farben umkehren“ wählen)")
    if cnt > 0.97 * W * H:
        raise MotivFehler("Das Bild ist fast vollständig dunkel – „Farben umkehren“ wählen")
    areas = raster_to_areas(r, tol=0.8, smooth=1, min_px=max(6.0, (W * H) * 2e-5))
    if not areas:
        raise MotivFehler("Im Bild ist kein Motiv zu erkennen")
    return normalize(dict(flaechen=areas, linien=[]))


# ==================================================================================================
# Normieren, Transformieren
# ==================================================================================================

def _r(p: Sequence[Point]) -> List[List[float]]:
    return [[round(x, 5), round(y, 5)] for x, y in p]


def normalize(m: dict) -> dict:
    polys = [f["aussen"] for f in m["flaechen"]] + list(m["linien"])
    x0, y0, x1, y1 = bbox(polys)
    s = max(x1 - x0, y1 - y0)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    t = lambda p: [((x - cx) / s, (y - cy) / s) for x, y in p]     # noqa: E731
    fl = []
    for f in m["flaechen"]:
        o = simplify(t(f["aussen"]), 2e-4)
        if len(o) < 3 or abs(area(o)) < 1e-6:
            continue
        hs = [simplify(t(h), 2e-4) for h in f["loecher"]]
        fl.append(dict(aussen=_r(o if area(o) > 0 else o[::-1]),
                       loecher=[_r(h if area(h) < 0 else h[::-1]) for h in hs if len(h) >= 3 and abs(area(h)) > 1e-7]))
    li = [_r(simplify(t(p), 2e-4, closed=False)) for p in m["linien"]]
    return dict(w=round((x1 - x0) / s, 5), h=round((y1 - y0) / s, 5), flaechen=fl, linien=li)


def place(pts: Sequence[Sequence[float]], x: float, y: float, size: float, angle: float = 0.0,
          flip: bool = False) -> Poly:
    """Normierte Punkte in mm setzen: Größe = längere Seite, Drehung in Grad gegen den Uhrzeigersinn."""
    a = math.radians(angle)
    ca, sa = math.cos(a), math.sin(a)
    out = []
    for px, py in pts:
        if flip:
            px = -px
        px, py = px * size, py * size
        out.append((x + px * ca - py * sa, y + px * sa + py * ca))
    if flip:
        out.reverse()                                   # Spiegeln dreht die Laufrichtung um
    return out


# ==================================================================================================
# Bibliothek
# ==================================================================================================

def user_dir() -> str:
    env = [d for d in os.environ.get("LASERFORGE_MOTIVE", "").split(os.pathsep) if d]
    if env:
        return os.path.abspath(os.path.expanduser(env[0]))
    if sys.platform == "darwin":
        return os.path.expanduser("~/Library/Application Support/Laserforge/Motive")
    return os.path.expanduser("~/.laserforge/motive")


def slug(name: str) -> str:
    s = unicodedata.normalize("NFKD", name.replace("ß", "ss")).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:30] or "motiv"


_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,40}$")
_CACHE: Dict[str, Tuple[float, dict]] = {}


def _path_for(mid: str) -> Optional[str]:
    if not _ID.match(mid or ""):
        return None
    for d in (user_dir(), BUILTIN_DIR):
        p = os.path.join(d, mid + ".json")
        if os.path.isfile(p):
            return p
    return None


def load(mid: str) -> dict:
    p = _path_for(mid)
    if not p:
        raise MotivFehler(f"Motiv {mid!r} gibt es nicht (mehr) – in der Motiv-Bibliothek neu wählen")
    mt = os.path.getmtime(p)
    hit = _CACHE.get(p)
    if hit and hit[0] == mt:
        return hit[1]
    with open(p, encoding="utf-8") as fh:
        m = json.load(fh)
    m["id"] = mid
    m["eingebaut"] = os.path.dirname(p) == BUILTIN_DIR
    _CACHE[p] = (mt, m)
    return m


def exists(mid: str) -> bool:
    return _path_for(mid) is not None


def library() -> List[dict]:
    """Alle Motive (eingebaute zuerst), ohne doppelte IDs."""
    out, seen = [], set()
    for d, builtin in ((BUILTIN_DIR, True), (user_dir(), False)):
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if not fn.endswith(".json"):
                continue
            mid = fn[:-5]
            if mid in seen or not _ID.match(mid):
                continue
            try:
                m = load(mid)
            except (OSError, ValueError, MotivFehler):
                continue
            seen.add(mid)
            out.append(m)
    out.sort(key=lambda m: (not m.get("eingebaut"), m.get("name", m["id"]).lower()))
    return out


def summary(m: dict) -> dict:
    """Für Formular und Weboberfläche: ID, Name, Maße, Umrisse (für Vorschaubilder)."""
    return dict(id=m["id"], name=m.get("name", m["id"]), quelle=m.get("quelle", ""), w=m["w"], h=m["h"],
                eingebaut=bool(m.get("eingebaut")), flaechen=m["flaechen"], linien=m["linien"],
                nur_linien=not m["flaechen"])


def import_bytes(data: bytes, filename: str, name: str = "", invert: bool = False) -> dict:
    """Datei einlesen, normieren und in der Bibliothek speichern. Liefert das Motiv."""
    if not data:
        raise MotivFehler("Leere Datei")
    if len(data) > MAX_BYTES:
        raise MotivFehler("Datei zu groß (höchstens 8 MB)")
    ext = os.path.splitext(filename or "")[1].lower()
    if ext == ".svg" or (not ext and b"<svg" in data[:4096].lower()):
        m = svg_to_motif(data)
        m["quelle"] = "svg"
    elif ext == ".png" or data[:8] == b"\x89PNG\r\n\x1a\n":
        m = png_to_motif(data, invert=invert)
        m["quelle"] = "png"
    elif ext in (".jpg", ".jpeg"):
        raise MotivFehler("JPG kann Laserforge nicht lesen – bitte als PNG (dunkles Motiv auf hellem Grund) "
                          "oder SVG speichern")
    else:
        raise MotivFehler("Nur SVG- und PNG-Dateien lassen sich als Motiv importieren")
    name = (name or os.path.splitext(os.path.basename(filename or ""))[0] or "Motiv").strip()[:40]
    m["name"] = name
    digest = hashlib.sha1(data).hexdigest()[:6]
    mid = f"{slug(name)}-{digest}"
    d = user_dir()
    os.makedirs(d, exist_ok=True)
    tmp = os.path.join(d, f".{mid}.tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(m, fh, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, os.path.join(d, mid + ".json"))
    return load(mid)


def import_file(path: str, name: str = "", invert: bool = False) -> dict:
    with open(path, "rb") as fh:
        data = fh.read(MAX_BYTES + 1)
    return import_bytes(data, os.path.basename(path), name, invert)


def remove(mid: str) -> None:
    p = _path_for(mid)
    if not p:
        raise MotivFehler(f"Motiv {mid!r} gibt es nicht")
    if os.path.dirname(p) == BUILTIN_DIR:
        raise MotivFehler("Eingebaute Motive lassen sich nicht entfernen")
    os.remove(p)
    _CACHE.pop(p, None)


def save_builtin(mid: str, name: str, m: dict) -> None:
    """Für die Werkzeugkette: ein eingebautes Motiv schreiben (normiert)."""
    m = normalize(m)
    m["name"] = name
    m["quelle"] = "eingebaut"
    os.makedirs(BUILTIN_DIR, exist_ok=True)
    with open(os.path.join(BUILTIN_DIR, mid + ".json"), "w", encoding="utf-8") as fh:
        json.dump(m, fh, ensure_ascii=False, separators=(",", ":"))
