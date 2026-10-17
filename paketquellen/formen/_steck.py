"""
Gemeinsame Werkzeuge für Steckskulpturen: Rippen mit Kreuzschlitzen, Beschriftung, Zuschnitt.

Eine Rippe ist ein ebenes Profil in (u, z): u läuft waagerecht in der Rippenebene, z ist die Höhe.
Zwei Rippen aus verschiedenen Scharen kreuzen sich auf einer senkrechten Linie. Die eine bekommt dort
einen Schlitz von oben bis zur Mitte, die andere einen von unten bis zur Mitte (halving-Feature).
"""
from __future__ import annotations

import math
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from steckwerk import JointFeature, Part, clean, dist_to_boundary, oriented, point_in_polygon, signed_area

Point = Tuple[float, float]


def clip_band(poly: Sequence[Point], lo: float, hi: float) -> List[Point]:
    """Polygon auf lo ≤ u ≤ hi beschneiden (Sutherland–Hodgman, zwei Halbebenen)."""
    def cut(pts, keep, edge):
        out: List[Point] = []
        n = len(pts)
        for i in range(n):
            a, b = pts[i - 1], pts[i]
            ia, ib = keep(a), keep(b)
            if ib:
                if not ia:
                    out.append(edge(a, b))
                out.append(b)
            elif ia:
                out.append(edge(a, b))
        return out

    def at(x):
        return lambda a, b: (x, a[1] + (x - a[0]) / (b[0] - a[0]) * (b[1] - a[1]))
    pts = cut(list(poly), lambda p: p[0] >= lo, at(lo))
    pts = cut(pts, lambda p: p[0] <= hi, at(hi))
    return clean(pts)


def _hits(poly: Sequence[Point], x: float) -> List[float]:
    out = []
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        if (a[0] - x) * (b[0] - x) < 0:
            out.append(a[1] + (x - a[0]) / (b[0] - a[0]) * (b[1] - a[1]))
    return sorted(out)


def slit(poly: Sequence[Point], u: float, T: float, z_mid: float, from_top: bool) -> Tuple[List[Point], List[Point]]:
    """Schlitz der Breite T bei u von oben (bzw. unten) bis z_mid. Liefert (Kontur, Schlitzpunkte)."""
    from models._shapes import cut_axis_slot
    moved = [(x - u, y) for x, y in poly]
    out, pts = cut_axis_slot(moved, T, z_mid, from_top)
    return [(x + u, y) for x, y in out], [(x + u, y) for x, y in pts]


def _entlang(poly: Sequence[Point], i: int, s: float, step: int) -> Tuple[Point, int]:
    """Punkt im Abstand s (entlang der Kontur) von Ecke i, Richtung step; dazu der Index davor."""
    n = len(poly)
    rest, k = s, i
    for _ in range(n - 1):
        a, b = poly[k % n], poly[(k + step) % n]
        L = math.dist(a, b)
        if L >= rest:
            t = rest / L
            return (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])), k
        rest -= L
        k += step
    return poly[k % n], k


def stumpf(poly: Sequence[Point], s: float = 0.4, min_winkel: float = 40.0) -> List[Point]:
    """Spitze Ecken (< min_winkel) kappen, damit der Kerf-Versatz dort sauber bleibt."""
    pts = list(poly)
    for _ in range(20):
        n = len(pts)
        found = False
        for i in range(n):
            p0 = pts[i]
            q1, _ = _entlang(pts, i, s, -1)
            q2, _ = _entlang(pts, i, s, 1)
            v1 = (q1[0] - p0[0], q1[1] - p0[1])
            v2 = (q2[0] - p0[0], q2[1] - p0[1])
            l1, l2 = math.hypot(*v1), math.hypot(*v2)
            if l1 < 1e-9 or l2 < 1e-9:
                continue
            c = max(-1.0, min(1.0, (v1[0] * v2[0] + v1[1] * v2[1]) / (l1 * l2)))
            w = math.acos(c)
            if math.degrees(w) >= min_winkel:
                continue
            s2 = min(2.0, max(s, 0.5 / (2 * math.sin(max(w, 0.05) / 2))))
            if s2 > s + 1e-9:
                q1, _ = _entlang(pts, i, s2, -1)
                q2, _ = _entlang(pts, i, s2, 1)
            ss = s2
            # Ecke i samt allen Punkten näher als s entlang der Kontur durch q1, q2 ersetzen
            _, kb = _entlang(pts, i, ss, -1)
            _, kf = _entlang(pts, i, ss, 1)
            drop = set()
            j = i
            while True:
                drop.add(j)
                if j == kb % n:
                    break
                j = (j - 1) % n
            j = i
            while True:
                drop.add(j)
                if j == kf % n:
                    break
                j = (j + 1) % n
            neu: List[Point] = []
            for j in range(n):
                if j == i:
                    neu += [q1, q2]
                elif j not in drop:
                    neu.append(pts[j])
            m = len(neu)                                   # keine Mini-Segmente neben den neuen Punkten
            k = neu.index(q1)
            for nb in ((k - 1) % m, (k + 2) % m):
                if math.dist(neu[nb], q1 if nb == (k - 1) % m else q2) < 0.08:
                    neu[nb] = None
            pts = clean([p for p in neu if p is not None])
            found = True
            break
        if not found:
            break
    return pts


class Rippe:
    """Profil plus geplante Schlitze; .teil() baut das fertige Part mit allen Features."""

    def __init__(self, name: str, profil: Sequence[Point], label: str = ""):
        self.name = name
        self.profil = oriented(stumpf(clean(profil)), True)
        self.label = label
        self.schlitze: List[Tuple[str, float, float, bool, Tuple[float, float]]] = []

    def schlitz(self, fid: str, u: float, z_mid: float, from_top: bool, span: Tuple[float, float]) -> None:
        self.schlitze.append((fid, u, z_mid, from_top, span))

    def teil(self, T: float, label_h: float = 4.0) -> Part:
        out = self.profil
        feats = []
        for fid, u, z_mid, from_top, span in sorted(self.schlitze, key=lambda s: s[1]):
            out, pts = slit(out, u, T, z_mid, from_top)
            feats.append((fid, span, pts))
        out = stumpf(out)                               # Schlitzwand trifft schräge Außenkante spitz
        feats = [(fid, span, [p if p in out else min(out, key=lambda q, p=p: math.dist(p, q)) for p in pts])
                 for fid, span, pts in feats]
        part = Part(self.name, out, features=[JointFeature(fid, "halving", span[1] - span[0], T, span=span, points=pts)
                                              for fid, span, pts in feats])
        if self.label:
            beschriften(part, self.label, label_h, [s[1] for s in self.schlitze], T)
        return part


def beschriften(part: Part, text: str, h: float, sperr_u: Sequence[float], T: float) -> bool:
    """Kleine Kennung (z. B. „A3“) als Gravur an eine freie Stelle zwischen den Schlitzen."""
    from models._font import fit_text
    poly = part.outline
    xs = sorted([p[0] for p in poly])
    u0, u1 = xs[0], xs[-1]
    stops = sorted([u0] + [u for u in sperr_u] + [u1])
    kand = []
    for a, b in zip(stops, stops[1:]):
        gap = (b - a) - (T if a != u0 else T / 2) - (T if b != u1 else T / 2)
        kand.append((gap, (a + b) / 2))
    kand.sort(reverse=True)
    for gap, cu in kand[:4]:
        hits = _hits(poly, cu)
        if len(hits) < 2:
            continue
        for k in range(0, len(hits) - 1, 2):
            zl, zh = hits[k], hits[k + 1]
            for cap in (h, h * 0.8, h * 0.65):
                w = min(gap - 2.0, cap * len(text) * 1.1)
                if w < cap * len(text) * 0.7:
                    continue
                for cz in ((zl + zh) / 2, zl + cap + 2.5, zh - cap - 2.5):
                    try:
                        strokes, _ = fit_text(text, cu, cz, w, cap * 1.4, min_h=cap * 0.6, max_cap=cap)
                    except ValueError:
                        continue
                    ok = all(point_in_polygon(p, poly) and dist_to_boundary(p, poly) > 1.0
                             for s in strokes for p in s)
                    if ok and strokes:
                        for s in strokes:
                            part.add_engrave(s)
                        return True
    return False


def profil_aus_breite(zs: Sequence[float], halb: Callable[[float], float]) -> Optional[List[Point]]:
    """Symmetrisches Profil aus der halben Breite je Höhe z (nur Bereich mit halb > 0)."""
    rechts = [(halb(z), z) for z in zs]
    pts = [p for p in rechts if p[0] > 1e-6]
    if len(pts) < 3:
        return None
    links = [(-x, z) for x, z in reversed(pts)]
    return pts + links


def bereich(f: Callable[[float], float], lo: float, hi: float, n: int = 400) -> Optional[Tuple[float, float]]:
    """Intervall [a, b] ⊂ [lo, hi], in dem f ≥ 0 (f einmal steigend, einmal fallend). Bisektion an den Rändern."""
    ts = [lo + (hi - lo) * i / n for i in range(n + 1)]
    inn = [t for t in ts if f(t) >= 0]
    if not inn:
        return None

    def bis(a, b):
        fa = f(a)
        for _ in range(50):
            m = (a + b) / 2
            if (f(m) >= 0) == (fa >= 0):
                a, fa = m, f(m)
            else:
                b = m
        return (a + b) / 2
    a, b = inn[0], inn[-1]
    i, j = ts.index(a), ts.index(b)
    if i > 0:
        a = bis(ts[i - 1], a)
    if j < n:
        b = bis(b, ts[j + 1])
    return a, b


def passt(w: float, h: float, cfg) -> bool:
    """Passt ein Teil w × h (mit etwas Luft für den Kerf) auf die Platte, notfalls gedreht?"""
    uw = cfg.sheet_width - 2 * cfg.sheet_margin
    uh = cfg.sheet_height - 2 * cfg.sheet_margin
    w, h = w + 1.0, h + 1.0
    return (w <= uw and h <= uh) or (h <= uw and w <= uh)


def flaeche(pts: Sequence[Point]) -> float:
    return abs(signed_area(pts))
