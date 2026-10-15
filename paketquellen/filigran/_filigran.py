"""
_filigran.py – Spitzenmuster und Schmuckformen für filigranen Weihnachtsschmuck.

Ein Muster besteht nur aus Linien (Stegen). Alles zwischen den Linien wird ausgeschnitten, so entsteht
Spitze wie bei Klöppel- oder Scherenschnittarbeiten. Die Linien werden in einem Keil gezeichnet (Mitte
zeigt nach oben), gespiegelt und n-mal gedreht. Die Leinwand aus _ebenen macht daraus laserfeste Teile:
zu schmale Stege und Schlitze werden ausgeglichen, lose Inseln fallen weg.
"""
from __future__ import annotations

import math
import os
import sys
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from steckwerk import Point, offset_polygon, oriented, signed_area
from pakete import bibliothek

_here = os.path.dirname(os.path.abspath(__file__))


def _sub(name: str):
    import importlib.util
    path = os.path.join(_here, name + ".py")
    key = "swpaket_filigran_" + name
    mod = sys.modules.get(key)
    if mod is None or getattr(mod, "__file__", None) != path:
        spec = importlib.util.spec_from_file_location(key, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[key] = mod
        spec.loader.exec_module(mod)
    return mod


K = bibliothek("verzierungen").K
Poly = List[Point]
TAU = 2 * math.pi


# --------------------------------------------------------------------------------------------------
# Werkzeug
# --------------------------------------------------------------------------------------------------

def P(r: float, t: float) -> Point:
    """Polarpunkt: Winkel t von der +y-Achse im Uhrzeigersinn (Keilmitte zeigt nach oben)."""
    return (r * math.sin(t), r * math.cos(t))


def rot(poly: Sequence[Point], a: float) -> Poly:
    c, s = math.cos(a), math.sin(a)
    return [(x * c - y * s, x * s + y * c) for x, y in poly]


def mir(poly: Sequence[Point]) -> Poly:
    return [(-x, y) for x, y in poly]


def ring(cx: float, cy: float, r: float) -> Poly:
    n = max(16, int(2 * math.pi * r / 0.6))
    p = K.circle(cx, cy, r, n)
    return p + [p[0]]


def closed(pts: Sequence[Point], n: int = 10) -> Poly:
    p = K.spline(list(pts), closed=True, n=n)
    return p + [p[0]]


def spiral(c: Point, start: Point, turns: float, shrink: float = 0.75, cw: bool = True, n: int = 60) -> Poly:
    """Spirale um c, beginnt in start und läuft turns Umdrehungen nach innen (Radius × (1 − shrink))."""
    r0 = math.hypot(start[0] - c[0], start[1] - c[1])
    a0 = math.atan2(start[1] - c[1], start[0] - c[0])
    sg = -1 if cw else 1
    out = []
    for i in range(n + 1):
        u = i / n
        r = r0 * (1 - shrink * u)
        a = a0 + sg * TAU * turns * u
        out.append((c[0] + r * math.cos(a), c[1] + r * math.sin(a)))
    return out


class Muster:
    """Sammelt Stege (Linien gleicher Breite) und gibt sie als Figur zurück."""

    def __init__(self, w: float, n: int, spiegeln: bool = True, wmin: float = 0.0, R: float = 1.0):
        self.w, self.n, self.spiegeln, self.wmin = w, n, spiegeln, wmin
        self.d = R / w                                   # Detailgrad: Musterradius in Stegbreiten
        self.fig = K.Figur()

    def frei(self, path: Sequence[Point], k: float = 1.0) -> None:
        """Steg entlang path: je Abschnitt ein Viereck, an Knicken und Enden ein Kreis.
        (Ein einziger Umriss für die ganze Linie überschneidet sich an spitzen Ecken und ließe Lücken.)"""
        pts = [q for i, q in enumerate(path) if i == 0 or math.hypot(q[0] - path[i - 1][0], q[1] - path[i - 1][1]) > 1e-6]
        if len(pts) < 2:
            return
        h = max(self.w * k, self.wmin) / 2
        polys = []
        for a, b in zip(pts, pts[1:]):
            dx, dy = b[0] - a[0], b[1] - a[1]
            L = math.hypot(dx, dy)
            nx, ny = -dy / L * h, dx / L * h
            polys.append([(a[0] + nx, a[1] + ny), (a[0] - nx, a[1] - ny), (b[0] - nx, b[1] - ny), (b[0] + nx, b[1] + ny)])
        dots = [pts[0], pts[-1]]
        for a, b, c in zip(pts, pts[1:], pts[2:]):
            u = (b[0] - a[0], b[1] - a[1])
            v = (c[0] - b[0], c[1] - b[1])
            cs = (u[0] * v[0] + u[1] * v[1]) / ((math.hypot(*u) * math.hypot(*v)) or 1)
            if cs < 0.97:
                dots.append(b)
        polys += [K.circle(x, y, h, 12) for x, y in dots]
        self.fig.add(*polys)

    def sym(self, path: Sequence[Point], k: float = 1.0, mirror: Optional[bool] = None) -> None:
        """Linie im Keil – gespiegelt und n-mal gedreht."""
        mirror = self.spiegeln if mirror is None else mirror
        for j in range(self.n):
            a = -TAU * j / self.n
            self.frei(rot(path, a), k)
            if mirror:
                self.frei(rot(mir(path), a), k)

    def kreis(self, r: float, k: float = 1.0) -> None:
        self.frei(ring(0, 0, r), k)

    def perle(self, x: float, y: float, r: float) -> None:
        self.fig.add(K.circle(x, y, r, 18))

    def figur(self, dx: float = 0.0, dy: float = 0.0) -> "K.Figur":
        return self.fig.place(dx, dy, 1.0)


# --------------------------------------------------------------------------------------------------
# Muster (R = Musterradius, n = Zähligkeit, alles in mm)
# --------------------------------------------------------------------------------------------------

def _bogenrand(M: Muster, r: float, R: float, m: int) -> None:
    """Äußerer Spitzensaum: m Bögen auf dem Ring r nach außen, Stege zum Rand, Picot in jedem Bogen."""
    a = TAU / m
    hb = min(0.10 * R, (R - r) * 0.75)
    for j in range(m):
        t0, t1, tm = j * a, (j + 1) * a, (j + 0.5) * a
        M.frei(K.bez(P(r, t0), P(r + 2 * hb, tm), P(r, t1), 14))
        M.frei([P(r, t0), P(R * 1.06, t0)])
        rp = hb * 0.32
        if rp > M.w * 0.6:
            M.frei(ring(*P(r + hb * 0.55, tm), rp), 0.8)


def mandala(M: Muster, R: float) -> None:
    n, al = M.n, TAU / M.n
    r0 = 0.14 * R
    M.kreis(r0)
    if M.d > 24:
        M.kreis(0.06 * R, 0.9)
        M.sym([P(0.06 * R, 0), P(r0, 0)], 0.9, mirror=False)
    # große Blütenblätter mit innerem Blatt
    half = [P(r0, 0), P(0.24 * R, 0.30 * al), P(0.40 * R, 0.40 * al), P(0.56 * R, 0.16 * al), P(0.63 * R, 0)]
    M.sym(closed(half + mir(half[1:-1])[::-1]), mirror=False)
    fein = M.d > 24
    if fein:
        inner = [P(0.22 * R, 0), P(0.30 * R, 0.17 * al), P(0.41 * R, 0.19 * al), P(0.49 * R, 0)]
        M.sym(closed(inner + mir(inner[1:-1])[::-1]), 0.9, mirror=False)
        M.sym([P(0.30 * R, 0), P(0.41 * R, 0)], 0.8, mirror=False)
    else:
        M.sym([P(0.20 * R, 0), P(0.50 * R, 0)], 0.9, mirror=False)
    # Perlenkranz zwischen den Blättern
    M.sym(ring(*P(0.47 * R, al / 2), 0.055 * R), 0.85, mirror=False)
    M.sym([P(0.47 * R + 0.055 * R, al / 2), P(0.63 * R, al / 2)], 0.85, mirror=False)
    M.kreis(0.63 * R)
    # Spitzbögen mit Spindel
    arch = [P(0.63 * R, -0.5 * al), P(0.72 * R, -0.30 * al), P(0.80 * R, -0.08 * al), P(0.83 * R, 0)]
    M.sym(K.spline(arch + mir(arch[:-1])[::-1], n=8), mirror=False)
    M.sym([P(0.63 * R, 0), P(0.83 * R, 0)], 0.8, mirror=False)
    if fein:
        M.sym(ring(*P(0.725 * R, 0), 0.035 * R + M.w * 0.6), 0.8, mirror=False)
        inner_arch = [P(0.63 * R, -0.28 * al), P(0.70 * R, -0.12 * al), P(0.74 * R, 0)]
        M.sym(K.spline(inner_arch + mir(inner_arch[:-1])[::-1], n=8), 0.8, mirror=False)
    M.kreis(0.86 * R)
    _bogenrand(M, 0.86 * R, R, 2 * n)


def ranken(M: Muster, R: float) -> None:
    n, al = M.n, TAU / M.n
    r0 = 0.13 * R
    M.kreis(r0)
    for j in range(n):                                     # kleine Rosette in der Mitte
        a = -TAU * j / n
        leaf = [P(0.02 * R, 0), P(0.07 * R, 0.25 * al), P(r0, 0), P(0.07 * R, -0.25 * al)]
        M.frei(rot(closed(leaf), a), 0.8)
    M.kreis(0.90 * R)
    # Mittelrippe und Rippe zwischen den Lyren
    M.sym([P(r0, 0), P(0.90 * R, 0)], 0.9, mirror=False)
    M.sym([P(0.55 * R, 0.5 * al), P(1.05 * R, 0.5 * al)], 0.9, mirror=False)
    # S-Ranke: vom Fuß der Mittelrippe nach außen, unten eingerollt, oben eingerollt
    a = P(0.30 * R, 0.0)
    b = P(0.42 * R, 0.30 * al)
    c = P(0.62 * R, 0.36 * al)
    stem = K.bez3(a, P(0.34 * R, 0.22 * al), P(0.38 * R, 0.32 * al), b, 14)
    c1 = P(0.40 * R, 0.16 * al)
    M.sym(stem + spiral(c1, b, 0.9, 0.7, cw=True)[1:])
    top0 = P(0.55 * R, 0.0)
    stem2 = K.bez3(top0, P(0.62 * R, 0.10 * al), P(0.66 * R, 0.30 * al), c, 14)
    c2 = P(0.72 * R, 0.30 * al)
    M.sym(stem2 + spiral(c2, c, 1.0, 0.72, cw=False)[1:])
    # Blätter am äußeren Bogen
    lf = [P(0.80 * R, 0.02 * al), P(0.83 * R, 0.14 * al), P(0.88 * R, 0.22 * al), P(0.84 * R, 0.10 * al)]
    M.sym(closed(lf), 0.85)
    M.sym(ring(*P(0.80 * R, 0.5 * al), 0.05 * R), 0.85, mirror=False)
    _bogenrand(M, 0.90 * R, R, n * 2)


def spitze(M: Muster, R: float) -> None:
    n = M.n
    rings = [0.15 * R, 0.34 * R, 0.55 * R, 0.78 * R]
    for r in rings:
        M.kreis(r)
    # Stern in der Mitte
    for j in range(n):
        a = -TAU * j / n
        M.frei(rot([P(0, 0), P(rings[0], 0)], a), 0.85)
    # Netz zwischen den Ringen: Zickzack mit wachsender Zahl an Zacken
    for i in range(len(rings) - 1):
        m = n * (i + 1)
        r_in, r_out = rings[i], rings[i + 1]
        pts = []
        for j in range(2 * m + 1):
            t = j * math.pi / m
            pts.append(P(r_in if j % 2 == 0 else r_out, t))
        M.frei(pts, 0.9)
        for j in range(m):                                 # Picots an den äußeren Spitzen
            t = (2 * j + 1) * math.pi / m
            rp = min(0.045 * R, (r_out - r_in) * 0.22)
            if rp > M.w * 0.9:
                M.frei(ring(*P(r_out - rp * 1.6, t), rp), 0.8)
    _bogenrand(M, rings[-1], R, 3 * n)


def kristall(M: Muster, R: float) -> None:
    n, al = M.n, TAU / M.n
    # Hauptäste
    M.sym([P(0, 0), P(0.97 * R, 0)], 1.1, mirror=False)
    M.perle(0, 0, 0.07 * R)
    # Sechseck-Ringe (gerade Stege zwischen den Ästen)
    for rr, k in ((0.24 * R, 0.9), (0.60 * R, 0.85)):
        M.sym([P(rr, 0), P(rr, al)], k, mirror=False)
    # Seitenäste unter 60° mit Zweigen
    for r, L, k in ((0.34 * R, 0.24 * R, 0.95), (0.70 * R, 0.20 * R, 0.9), (0.86 * R, 0.10 * R, 0.85)):
        base = P(r, 0)
        d = (math.sin(math.pi / 3), math.cos(math.pi / 3))
        tip = (base[0] + d[0] * L, base[1] + d[1] * L)
        M.sym([base, tip], k)
        if L > 0.15 * R:
            for f in (0.45, 0.75):
                q = (base[0] + d[0] * L * f, base[1] + d[1] * L * f)
                M.sym([q, (q[0] + 0.0, q[1] + L * 0.30)], 0.8)
    # Raute an der Spitze
    tip = [P(0.80 * R, 0), P(0.88 * R, 0.07 * al * 6 / n), P(0.97 * R, 0), P(0.88 * R, -0.07 * al * 6 / n)]
    M.sym(closed(tip, 4), 0.8, mirror=False)
    M.sym(ring(*P(0.47 * R, 0), 0.05 * R), 0.85, mirror=False)
    M.kreis(0.98 * R, 0.9)


def sterne(M: Muster, R: float) -> None:
    n, al = M.n, TAU / M.n

    def starline(ro: float, ri: float, off: float) -> Poly:
        pts = [P(ro if i % 2 == 0 else ri, off + i * al / 2) for i in range(2 * n + 1)]
        return pts
    M.frei(starline(0.96 * R, 0.58 * R, 0.0))
    M.frei(starline(0.80 * R, 0.50 * R, al / 2), 0.95)
    M.frei(starline(0.46 * R, 0.28 * R, 0.0), 0.9)
    M.kreis(0.18 * R, 0.9)
    M.perle(0, 0, 0.07 * R)
    M.sym([P(0.07 * R, 0), P(0.18 * R, 0)], 0.8, mirror=False)
    M.sym([P(0.28 * R, al / 2), P(0.50 * R, al / 2)], 0.85, mirror=False)
    M.sym([P(0.46 * R, 0), P(0.80 * R, 0)], 0.85, mirror=False)
    # kleine Sterne in den äußeren Taschen
    for j in range(n):
        c = P(0.86 * R, al / 2 + j * al)
        rs = 0.07 * R
        pts = [(c[0] + (rs if i % 2 == 0 else rs * 0.45) * math.sin(i * math.pi / 5),
                c[1] + (rs if i % 2 == 0 else rs * 0.45) * math.cos(i * math.pi / 5)) for i in range(11)]
        M.frei(pts, 0.8)
        M.frei([P(0.80 * R, al / 2 + j * al), c], 0.8)
        M.frei([c, P(1.05 * R, al / 2 + j * al)], 0.8)


MUSTER: Dict[str, Callable[[Muster, float], None]] = dict(mandala=mandala, ranken=ranken, spitze=spitze,
                                                          kristall=kristall, sterne=sterne)
MUSTER_LISTE = [("mandala", "Mandala mit Blüten und Spitzbögen"), ("ranken", "Ranken und Spiralen"),
                ("spitze", "Klöppelspitze (Netz mit Picots)"), ("kristall", "Eiskristall"),
                ("sterne", "Stern im Stern"), ("rezept", "eigenes Rezept aus Bausteinen"),
                ("zufall", "Zufall (jeder Startwert ein neues Muster)")]



# --------------------------------------------------------------------------------------------------
# Rezepte: Muster aus Bausteinen, Ring für Ring von innen nach außen (ab Filigran 1.1.0)
# --------------------------------------------------------------------------------------------------

BAUSTEINE = [("blueten", "Blütenblätter"), ("boegen", "Spitzbögen"), ("speichen", "Speichen"),
             ("zickzack", "Zickzack-Netz"), ("perlen", "Perlenkranz"), ("ranken", "Ranken"),
             ("sterne", "Sternchen"), ("tropfen", "Tropfen"), ("herzen", "Herzen")]
_BAUSTEIN_IDS = [k for k, _ in BAUSTEINE]
_ALIAS = {"blüten": "blueten", "bluete": "blueten", "blüte": "blueten", "blaetter": "blueten", "blätter": "blueten",
          "bogen": "boegen", "bögen": "boegen", "speiche": "speichen", "netz": "zickzack", "perle": "perlen",
          "ranke": "ranken", "spiralen": "ranken", "stern": "sterne", "tropfen": "tropfen", "herz": "herzen"}


def rezept_lesen(text: str) -> List[str]:
    """„blüten, perlen, bögen“ → ['blueten', 'perlen', 'boegen'] (2–5 Bausteine, Unbekanntes → Fehler)."""
    teile = [t.strip().lower() for t in text.replace(";", ",").replace("+", ",").replace("|", ",").split(",")]
    out = []
    for t in teile:
        if not t:
            continue
        t = _ALIAS.get(t, t)
        if t not in _BAUSTEIN_IDS:
            raise ValueError(f"Rezept: Baustein „{t}“ kenne ich nicht – möglich sind "
                             + ", ".join(_BAUSTEIN_IDS))
        out.append(t)
    if not 1 <= len(out) <= 5:
        raise ValueError("Rezept: bitte 1 bis 5 Bausteine, mit Komma getrennt (von innen nach außen)")
    return out


def rezept_zufall(seed: int) -> List[str]:
    import random
    r = random.Random(int(seed) * 7919 + 17)
    k = r.choice((2, 3, 3, 4))
    out: List[str] = []
    while len(out) < k:
        b = r.choice(_BAUSTEIN_IDS)
        if not out or b != out[-1]:
            out.append(b)
    return out


def _baustein(M: Muster, art: str, a: float, b: float, versatz: float) -> None:
    """Ein Baustein im Ring a … b (Radien). versatz: Winkel-Offset (0 oder halbe Teilung)."""
    al = TAU / M.n
    h = b - a
    o = versatz
    if art == "speichen":
        M.sym([P(a, o), P(b, o)], 0.9, mirror=False)
        if M.d > 24:
            M.sym([P(a + h * 0.45, o + al / 2), P(b, o + al / 2)], 0.8, mirror=False)
    elif art == "blueten":
        half = [P(a, o), P(a + h * 0.3, o + 0.32 * al), P(a + h * 0.7, o + 0.30 * al), P(b, o)]
        M.sym(closed(half + [_spiegel_an(q, o) for q in half[1:-1]][::-1]), mirror=False)
        if M.d > 22:
            M.sym([P(a + h * 0.2, o), P(a + h * 0.75, o)], 0.8, mirror=False)
    elif art == "boegen":
        arch = [P(a, o - 0.5 * al), P(a + h * 0.45, o - 0.30 * al), P(a + h * 0.85, o - 0.08 * al), P(b, o)]
        M.sym(K.spline(arch + [_spiegel_an(q, o) for q in arch[:-1]][::-1], n=8), mirror=False)
        M.sym([P(a, o), P(b, o)], 0.8, mirror=False)
    elif art == "zickzack":
        m = max(M.n, int(round(M.n * (a + b) / max(b, 1e-6) * 0.6)))
        pts = [P(a if j % 2 == 0 else b, o + j * math.pi / m) for j in range(2 * m + 1)]
        M.frei(pts, 0.9)
    elif art == "perlen":
        rp = min(h * 0.28, (a + b) / 2 * al * 0.22)
        c = P((a + b) / 2, o + al / 2)
        M.sym(ring(c[0], c[1], rp), 0.85, mirror=False)
        M.sym([P(a, o + al / 2), P((a + b) / 2 - rp, o + al / 2)], 0.8, mirror=False)
        M.sym([P((a + b) / 2 + rp, o + al / 2), P(b, o + al / 2)], 0.8, mirror=False)
        M.sym([P(a, o), P(b, o)], 0.8, mirror=False)
    elif art == "ranken":
        st = P(a, o)
        e = P(a + h * 0.62, o + 0.33 * al)
        stem = K.bez3(st, P(a + h * 0.25, o + 0.05 * al), P(a + h * 0.45, o + 0.32 * al), e, 12)
        c = P(a + h * 0.52, o + 0.20 * al)
        M.sym(stem + spiral(c, e, 0.85, 0.7, cw=True)[1:])
        M.sym([P(a, o), P(b, o)], 0.85, mirror=False)
    elif art in ("sterne", "herzen", "tropfen"):
        cm = P((a + b) / 2, o + al / 2)
        g = min(h * 0.62, (a + b) / 2 * al * 0.55)
        if art == "sterne":
            ta = math.atan2(cm[0], cm[1])
            pts = [(cm[0] + (g / 2 if i % 2 == 0 else g * 0.22) * math.sin(ta + i * math.pi / 5),
                    cm[1] + (g / 2 if i % 2 == 0 else g * 0.22) * math.cos(ta + i * math.pi / 5)) for i in range(11)]
        elif art == "herzen":
            ta = math.atan2(cm[0], cm[1])
            hz = [(x - cm[0], y - cm[1]) for x, y in _herz(cm[0], cm[1], g)]
            pts = [(cm[0] + x * math.cos(-ta) - y * math.sin(-ta), cm[1] + x * math.sin(-ta) + y * math.cos(-ta))
                   for x, y in hz]
            pts = pts + [pts[0]]
        else:
            mid = (a + b) / 2
            wa = g * 0.28 / mid
            pts = closed([P(mid - g * 0.4, o + al / 2), P(mid - g * 0.1, o + al / 2 + wa),
                          P(mid + g * 0.5, o + al / 2), P(mid - g * 0.1, o + al / 2 - wa)])
        M.sym(pts, 0.8, mirror=False)
        M.sym([P(a, o + al / 2), P((a + b) / 2 - g * 0.42, o + al / 2)], 0.8, mirror=False)
        M.sym([P((a + b) / 2 + g * 0.42, o + al / 2), P(b, o + al / 2)], 0.8, mirror=False)
        M.sym([P(a, o), P(b, o)], 0.8, mirror=False)
    else:
        raise ValueError(f"Unbekannter Baustein {art!r}")


def _spiegel_an(q: Point, o: float) -> Point:
    """Punkt an der Strahl-Achse mit Winkel o spiegeln."""
    r = math.hypot(q[0], q[1])
    t = math.atan2(q[0], q[1])
    return P(r, 2 * o - t)


def _herz(cx: float, cy: float, g: float) -> Poly:
    pts = []
    for i in range(40):
        t = TAU * i / 40
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((cx + x / 32 * g, cy + (y + 2.5) / 32 * g))
    return pts


def rezept(M: Muster, R: float, bausteine: Sequence[str]) -> None:
    """Muster aus Bausteinen: Mitte, dann je Baustein ein Ring, außen der Spitzensaum."""
    r0 = 0.13 * R
    M.kreis(r0)
    M.perle(0, 0, 0.06 * R)
    M.sym([P(0.06 * R, 0), P(r0, 0)], 0.85, mirror=False)
    k = len(bausteine)
    grenzen = [r0 + (0.86 * R - r0) * i / k for i in range(k + 1)]
    for i, art in enumerate(bausteine):
        a, b = grenzen[i], grenzen[i + 1]
        _baustein(M, art, a, b, 0.0 if i % 2 == 0 else TAU / M.n / 2)
        M.kreis(b, 0.95)
    _bogenrand(M, 0.86 * R, R, 2 * M.n)

# --------------------------------------------------------------------------------------------------
# Formen: Umriss, Musterfeld, Musterzentrum, Öse
# --------------------------------------------------------------------------------------------------

def _spline_half(half: Sequence[Point], n: int = 10) -> Poly:
    """Halbes Profil (x ≥ 0, von oben nach unten) → geschlossener, symmetrischer Umriss (CCW)."""
    right = K.spline(list(half), n=n)
    full = right + [(-x, y) for x, y in reversed(right[1:-1])]
    return oriented(full, True)


def form(name: str, S: float) -> Tuple[Poly, Point, float]:
    """Umriss (CCW), Ösenpunkt (oberster Punkt der Mitte) und Höhe der Musterbezugsmitte."""
    h = S / 2
    if name == "kugel":
        circ = K.circle(0, 0, h * 0.90, 160)
        return oriented(circ, True), (0.0, h * 0.90), 0.0
    if name == "stern":
        pts = []
        for i in range(10):
            r = h if i % 2 == 0 else h * 0.56
            pts.append(P(r, i * math.pi / 5))
        return oriented(pts[::-1], True), (0.0, h), 0.0
    if name == "herz":
        pts = []
        for i in range(160):
            t = TAU * i / 160
            x = 16 * math.sin(t) ** 3
            y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
            pts.append((x, y))
        ys = [p[1] for p in pts]
        k = S / (max(ys) - min(ys))
        yc = (max(ys) + min(ys)) / 2
        pts = [(x * k, (y - yc) * k) for x, y in pts]
        top = max(p[1] for p in pts if abs(p[0]) < 0.5 * k)
        return oriented(pts, True), (0.0, top), 0.10 * S
    if name == "glocke":
        half = [(0, h), (0.12 * S, 0.47 * S), (0.20 * S, 0.38 * S), (0.23 * S, 0.20 * S), (0.25 * S, 0.0),
                (0.31 * S, -0.22 * S), (0.42 * S, -0.40 * S), (0.45 * S, -0.47 * S), (0.30 * S, -0.44 * S),
                (0, -0.43 * S)]
        return _spline_half(half), (0.0, h), -0.06 * S
    if name == "zwiebel":
        half = [(0, h), (0.05 * S, 0.40 * S), (0.17 * S, 0.24 * S), (0.30 * S, 0.04 * S), (0.31 * S, -0.10 * S),
                (0.24 * S, -0.27 * S), (0.10 * S, -0.42 * S), (0, -h)]
        return _spline_half(half, 12), (0.0, h), 0.0
    raise ValueError(f"unbekannte Form {name!r}")


FORMEN = [("kugel", "Kugel"), ("stern", "Stern"), ("herz", "Herz"), ("glocke", "Glocke"),
          ("zwiebel", "Zwiebel (Tropfen)")]


def feld(umriss: Poly, rand: float) -> Poly:
    """Musterfeld: Umriss um rand nach innen versetzt."""
    return oriented(offset_polygon(oriented(umriss, True), -rand), True)


def deckung(poly: Sequence[Point], cx: float, cy: float) -> float:
    return max(math.hypot(x - cx, y - cy) for x, y in poly)
