"""
ornamente.py – Ornament-Katalog der Bibliothek „Verzierungen“.

Alle Formen sind Figuren (siehe _kit.Figur): Flächen, die hinzugefügt (+) oder weggeschnitten (−) werden.
Die Leinwand rechnet sie später zu laserfesten Konturen, Überlappungen sind also erlaubt.
Maße in mm, y nach oben. w ist die Linienstärke (Material) – nie dünner als wmin(cfg) wählen.

  rosette(r, art, blaetter)          runde Zierform: bluete, mandala, stern, sonne, schneestern
  ranke(L, h, …)                     waagerechte Ranke mit Kringeln und Blättern (x = 0 … L)
  ecke(g, art)                       Eckornament im Quadranten x, y ∈ [0, g]: ranke, faecher, herz, blatt, schnoerkel
  bordure(L, h, muster)              Zierband (x = 0 … L, y = 0 … h) mit durchgehender Grundleiste
  kante(poly, muster, g)             Verzierung, die außen an eine Kontur gesetzt wird (Bögen, Perlen, Zacken …)
  durchbruch(poly, muster, g)        Muster, das entlang einer Linie aus einem Band ausgeschnitten wird
  schleife(b), zweig(L, art), herz(cx, cy, g), blatt(…), spirale(…)
"""
from __future__ import annotations

import math
import os
import sys
import zlib
from typing import Callable, List, Optional, Sequence, Tuple

_here = os.path.dirname(os.path.abspath(__file__))


def _lade(name: str):
    import importlib.util
    path = os.path.join(_here, name + ".py")
    key = "swbib_verzierungen_%s_%08x" % (name, zlib.crc32(path.encode()))
    mod = sys.modules.get(key)
    if mod is None or getattr(mod, "__file__", None) != path:
        spec = importlib.util.spec_from_file_location(key, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[key] = mod
        spec.loader.exec_module(mod)
    return mod


K = _lade("_kit")
Figur = K.Figur
Point = Tuple[float, float]
Poly = List[Point]
TAU = 2 * math.pi

ROSETTEN = [("bluete", "Blüte"), ("mandala", "Mandala"), ("stern", "Stern"), ("sonne", "Sonne"),
            ("schneestern", "Schneestern")]
ECKEN = [("ranke", "Ranke"), ("faecher", "Fächer"), ("herz", "Herz mit Kringeln"), ("blatt", "Blätterzweig"),
         ("schnoerkel", "Schnörkel")]
BORDUEREN = [("ranke", "Ranke"), ("wellen", "Wellen"), ("kringel", "Laufender Kringel"), ("bogen", "Bogenkante"),
             ("zacken", "Zacken"), ("herzen", "Herzen"), ("sterne", "Sterne"), ("perlen", "Perlen"),
             ("blaetter", "Blätter"), ("tannen", "Tannen"), ("maeander", "Mäander")]
KANTEN = [("bogen", "Bögen"), ("perlen", "Perlen"), ("zacken", "Zacken"), ("wellen", "Wellen"),
          ("herzen", "Herzen"), ("sterne", "Sterne"), ("blaetter", "Blätter")]
DURCHBRUECHE = [("punkte", "Punkte"), ("herzen", "Herzen"), ("sterne", "Sterne"), ("tropfen", "Tropfen"),
                ("rauten", "Rauten"), ("blueten", "Blüten"), ("ranke", "Ranke")]


# --------------------------------------------------------------------------------------------------
# Grundformen
# --------------------------------------------------------------------------------------------------

def _rot(p: Point, a: float, o: Point = (0.0, 0.0)) -> Point:
    c, s = math.cos(a), math.sin(a)
    x, y = p[0] - o[0], p[1] - o[1]
    return (o[0] + x * c - y * s, o[1] + x * s + y * c)


def spirale(cx: float, cy: float, r0: float, r1: float, dreh: float, a0: float = 0.0, sinn: int = 1,
            n: int = 0) -> Poly:
    """Archimedische Spirale um (cx, cy) von Radius r0 nach r1, dreh = Umdrehungen, sinn ±1."""
    n = n or max(12, int(dreh * 40))
    return [(cx + (r0 + (r1 - r0) * i / n) * math.cos(a0 + sinn * TAU * dreh * i / n),
             cy + (r0 + (r1 - r0) * i / n) * math.sin(a0 + sinn * TAU * dreh * i / n)) for i in range(n + 1)]


def kringel(start: Point, richtung: float, r: float, sinn: int = 1, dreh: float = 1.15) -> Poly:
    """Ein Kringel, der bei start in Richtung richtung beginnt und sich nach innen einrollt."""
    # Mittelpunkt liegt links (sinn = 1) bzw. rechts der Startrichtung
    cx = start[0] + r * math.cos(richtung + sinn * math.pi / 2)
    cy = start[1] + r * math.sin(richtung + sinn * math.pi / 2)
    a0 = math.atan2(start[1] - cy, start[0] - cx)
    return spirale(cx, cy, r, r * 0.22, dreh, a0, sinn)


def blatt(basis: Point, winkel: float, L: float, B: float, spitze: float = 0.0) -> Poly:
    """Mandelförmiges Blatt: Stiel bei basis, Spitze in Richtung winkel, Länge L, Breite B."""
    ux, uy = math.cos(winkel), math.sin(winkel)
    nx, ny = -uy, ux
    tip = (basis[0] + ux * L, basis[1] + uy * L)
    c1 = (basis[0] + ux * L * 0.45 + nx * B * (1 + spitze), basis[1] + uy * L * 0.45 + ny * B * (1 + spitze))
    c2 = (basis[0] + ux * L * 0.45 - nx * B * (1 - spitze), basis[1] + uy * L * 0.45 - ny * B * (1 - spitze))
    return K.chain(K.bez(basis, c1, tip, 14), K.bez(tip, c2, basis, 14)[1:-1])


def herz(cx: float, cy: float, g: float, rot: float = 0.0) -> Poly:
    """Herz der Höhe ≈ g, Mitte (cx, cy)."""
    pts = []
    for i in range(64):
        t = TAU * i / 64
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((x / 32 * g, (y + 2.5) / 32 * g))
    if rot:
        pts = [_rot(p, rot) for p in pts]
    return [(cx + x, cy + y) for x, y in pts]


def tropfen(cx: float, cy: float, L: float, B: float, winkel: float) -> Poly:
    """Tropfen: rund bei (cx, cy), spitz in Richtung winkel."""
    ux, uy = math.cos(winkel), math.sin(winkel)
    tip = (cx + ux * L, cy + uy * L)
    r = B / 2
    a = winkel + math.pi / 2
    side1 = (cx + math.cos(a) * r, cy + math.sin(a) * r)
    side2 = (cx - math.cos(a) * r, cy - math.sin(a) * r)
    back = K.arc(cx, cy, r, a, a + math.pi, 12)
    return K.chain(back, K.bez(side2, (cx + ux * L * 0.55 - math.cos(a) * r * 0.9,
                                        cy + uy * L * 0.55 - math.sin(a) * r * 0.9), tip, 10),
                   K.bez(tip, (cx + ux * L * 0.55 + math.cos(a) * r * 0.9,
                               cy + uy * L * 0.55 + math.sin(a) * r * 0.9), side1, 10)[1:-1])


def raute(cx: float, cy: float, b: float, h: float) -> Poly:
    return [(cx, cy - h / 2), (cx + b / 2, cy), (cx, cy + h / 2), (cx - b / 2, cy)]


# --------------------------------------------------------------------------------------------------
# Rosetten
# --------------------------------------------------------------------------------------------------

def rosette(r: float, art: str = "bluete", blaetter: int = 8, w: Optional[float] = None) -> Figur:
    """Runde Zierform mit Radius r um (0, 0)."""
    n = max(4, min(24, int(blaetter)))
    w = w or max(0.9, r * 0.06)
    f = Figur()
    if art == "bluete":
        for k in range(n):
            a = TAU * k / n + math.pi / 2
            f.add(blatt((0, 0), a, r, r * 0.42 * 8 / max(n, 6)))
        f.add(K.circle(0, 0, r * 0.34))
        for k in range(n):                                     # Blattinneres ausschneiden
            a = TAU * k / n + math.pi / 2
            b = (math.cos(a) * r * 0.42, math.sin(a) * r * 0.42)
            f.cut(blatt(b, a, r * 0.43, r * 0.17 * 8 / max(n, 6)))
        for k in range(n):                                     # Punktkranz um die Mitte
            a = TAU * (k + 0.5) / n + math.pi / 2
            f.cut(K.circle(math.cos(a) * r * 0.22, math.sin(a) * r * 0.22, max(w * 0.55, r * 0.035)))
        f.cut(K.star(0, 0, r * 0.11, r * 0.05, max(5, n // 2 if n > 9 else n)))
    elif art == "mandala":
        bumps = n * 2
        rim = []
        for i in range(bumps * 12):
            a = TAU * i / (bumps * 12)
            rr = r * (0.93 + 0.07 * abs(math.cos(a * bumps / 2)))
            rim.append((math.cos(a) * rr, math.sin(a) * rr))
        f.add(rim)
        for k in range(n):                                     # äußerer Ring: Tropfen
            a = TAU * k / n + math.pi / 2
            f.cut(tropfen(math.cos(a) * r * 0.58, math.sin(a) * r * 0.58, r * 0.26, r * 0.17, a))
        for k in range(2 * n):                                 # Perlenkranz
            a = TAU * (k + 0.5) / (2 * n) + math.pi / 2
            f.cut(K.circle(math.cos(a) * r * 0.84, math.sin(a) * r * 0.84, r * 0.045 + 0.1))
        for k in range(n):                                     # innerer Ring: Rauten
            a = TAU * (k + 0.5) / n + math.pi / 2
            p = [_rot(q, a - math.pi / 2) for q in raute(0, r * 0.38, r * 0.11, r * 0.2)]
            f.cut(p)
        f.cut(K.star(0, 0, r * 0.22, r * 0.11, max(5, n // 2 if n >= 10 else n)))
    elif art == "stern":
        f.add(K.star(0, 0, r, r * 0.5, n))
        for k in range(n):                                     # je Zacke ein schlanker Durchbruch
            a = TAU * k / n + math.pi / 2
            f.cut(tropfen(math.cos(a) * r * 0.42, math.sin(a) * r * 0.42, r * 0.3, r * 0.1 * 8 / max(n, 6), a))
        f.cut(K.sparkle(0, 0, r * 0.22, 0.25, 4))
    elif art == "sonne":
        for k in range(2 * n):
            a = TAU * k / (2 * n) + math.pi / 2
            L = r if k % 2 == 0 else r * 0.75
            path = [(math.cos(a + 0.18 * math.sin(t * math.pi)) * (r * 0.4 + (L - r * 0.4) * t),
                     math.sin(a + 0.18 * math.sin(t * math.pi)) * (r * 0.4 + (L - r * 0.4) * t))
                    for t in (i / 12 for i in range(13))]
            f.line(path, max(w * 1.6, r * 0.09), w, "spitz")
        f.add(K.circle(0, 0, r * 0.48))
        for k in range(n):
            a = TAU * k / n + math.pi / 2
            f.cut(tropfen(math.cos(a) * r * 0.14, math.sin(a) * r * 0.14, r * 0.2, r * 0.085, a))
        for k in range(2 * n):
            a = TAU * (k + 0.5) / (2 * n) + math.pi / 2
            f.cut(K.circle(math.cos(a) * r * 0.39, math.sin(a) * r * 0.39, max(w * 0.55, r * 0.03)))
    elif art == "schneestern":
        n = 6 if n < 6 else (8 if n < 8 else n)
        for k in range(n):
            a = TAU * k / n + math.pi / 2
            ux, uy = math.cos(a), math.sin(a)
            f.line([(0, 0), (ux * r, uy * r)], max(w * 1.4, r * 0.08), w * 1.1)
            for t, L in ((0.45, 0.32), (0.72, 0.22)):
                b = (ux * r * t, uy * r * t)
                for s in (-1, 1):
                    aa = a + s * 0.85
                    f.line([b, (b[0] + math.cos(aa) * r * L, b[1] + math.sin(aa) * r * L)], w * 1.2, w, "rund")
            f.add(K.circle(ux * r, uy * r, max(w, r * 0.05)))
        f.add(K.circle(0, 0, r * 0.2))
        f.cut(K.star(0, 0, r * 0.13, r * 0.06, n))
    else:
        raise ValueError(f"Unbekannte Rosette {art!r}")
    return f


# --------------------------------------------------------------------------------------------------
# Ranke
# --------------------------------------------------------------------------------------------------

def ranke(L: float, h: float, blaetter: bool = True, kringel_an: bool = True, w: Optional[float] = None,
          phase: int = 0) -> Figur:
    """Wellenranke von x = 0 bis L im Band y = 0 … h: Wellenstiel, in jeder Bucht ein eingerollter Trieb,
    außen an jedem Bogen ein Blatt."""
    w = w or max(0.9, h * 0.07)
    n = max(1, int(round(L / (h * 1.9))))
    lam = L / n
    A = h * 0.26
    mid = h / 2
    ph = phase * math.pi

    def y_at(x):
        return mid + A * math.sin(TAU * x / lam + ph)

    stem = [(x, y_at(x)) for x in (L * i / (n * 32) for i in range(n * 32 + 1))]
    f = Figur().line(stem, w * 1.3, w * 1.3, "rund")
    r = min(lam * 0.17, h * 0.24)
    for k in range(2 * n):
        xk = (k + 0.5 - phase * 0.5) * lam / 2                  # Wellenberg / Wellental
        if not (0 <= xk <= L):
            continue
        sgn = 1 if math.sin(TAU * xk / lam + ph) > 0 else -1
        if kringel_an:
            xs = xk - lam * 0.06
            start = (xs, y_at(xs))
            c = (xk + lam * 0.1, mid + sgn * A * 0.05)
            d = math.hypot(start[0] - c[0], start[1] - c[1])
            th0 = math.atan2(start[1] - c[1], start[0] - c[0])
            sense = -sgn                                       # Berg: im Uhrzeigersinn einrollen
            m = 60
            path = [(c[0] + (d + (r * 0.22 - d) * (i / m) ** 0.8) * math.cos(th0 + sense * TAU * 1.15 * i / m),
                     c[1] + (d + (r * 0.22 - d) * (i / m) ** 0.8) * math.sin(th0 + sense * TAU * 1.15 * i / m))
                    for i in range(m + 1)]
            f.line(path, w * 1.15, w * 0.9, "rund")
            f.add(K.circle(path[-1][0], path[-1][1], w * 0.85))
        if blaetter:
            xb = xk + lam * 0.02
            base = (xb, y_at(xb) + sgn * w * 0.3)
            ang = sgn * (math.pi / 2 - 0.55)
            Lb = h * 0.36
            f.add(blatt(base, ang, Lb, Lb * 0.34))
            xb2 = xk - lam * 0.16
            base2 = (xb2, y_at(xb2) + sgn * w * 0.3)
            f.add(blatt(base2, sgn * (math.pi / 2 + 0.75), Lb * 0.75, Lb * 0.26))
    return f


# --------------------------------------------------------------------------------------------------
# Ecken
# --------------------------------------------------------------------------------------------------

def ecke(g: float, art: str = "ranke", w: Optional[float] = None) -> Figur:
    """Eckornament für die linke untere Ecke: liegt im Quadrat x, y ∈ [0, g].
    Für andere Ecken mit Figur.place(…, flip=True) bzw. Drehung um 90°/180° setzen."""
    w = w or max(0.9, g * 0.05)
    f = Figur()
    if art == "ranke":
        b = g * 0.24                                       # Bandbreite entlang der Kanten
        for spiegel in (False, True):
            arm = ranke(g * 0.95, b * 1.6, True, True, w)
            if spiegel:
                arm = arm.map(lambda p: (p[1], p[0]))
            f.merge(arm)
        f.add(K.circle(b * 0.8, b * 0.8, b * 0.62))
        f.cut(K.circle(b * 0.8, b * 0.8, b * 0.62 - 1.6 * w))
        f.add(K.circle(b * 0.8, b * 0.8, b * 0.22))
        for k in range(5):
            a = math.pi / 4 + (k - 2) * 0.42
            f.add(blatt((b * 0.8 + math.cos(a) * b * 0.55, b * 0.8 + math.sin(a) * b * 0.55), a, b * 0.75, b * 0.24))
    elif art == "faecher":
        R = g * 0.95
        rays = 5
        bumps = rays * 2
        rim = [(0, 0)] + [(math.cos(a) * R * (0.93 + 0.07 * abs(math.sin(a * bumps))),
                           math.sin(a) * R * (0.93 + 0.07 * abs(math.sin(a * bumps))))
                          for a in (math.pi / 2 * i / 120 for i in range(121))]
        f.add(rim)
        for k in range(rays):
            am = math.pi / 2 * (k + 0.5) / rays
            f.cut(tropfen(math.cos(am) * R * 0.72, math.sin(am) * R * 0.72, R * 0.4, R * 0.15, am + math.pi))
        for k in range(bumps):
            am = math.pi / 2 * (k + 0.5) / bumps
            f.cut(K.circle(math.cos(am) * R * 0.86, math.sin(am) * R * 0.86, max(w * 0.6, R * 0.03)))
        f.cut(K.arc(0, 0, R * 0.2, 0.25, math.pi / 2 - 0.25, 12) + [(R * 0.06, R * 0.06)])
    elif art == "herz":
        hz = g * 0.42
        cx = cy = g * 0.42
        f.add(herz(cx, cy, hz, rot=-math.pi / 4))
        f.cut(herz(cx, cy, hz * 0.62, rot=-math.pi / 4))
        f.add(herz(cx, cy, hz * 0.3, rot=-math.pi / 4))
        for spiegel in (False, True):
            path = K.chain([(cx - hz * 0.25, cy - hz * 0.42)], K.bez((cx - hz * 0.25, cy - hz * 0.42), (g * 0.45, w), (g * 0.82, g * 0.09), 16)[1:])
            curl = kringel(path[-1], 0.25, g * 0.08, 1)
            path = K.chain(path, curl)
            if spiegel:
                path = [(p[1], p[0]) for p in path]
            f.line(path, w * 1.4, w * 0.9)
        f.line([(w, w), (cx - hz * 0.25, cy - hz * 0.25)], w * 1.5, w * 1.2)
    elif art == "blatt":
        for k, (a, L) in enumerate(((math.pi / 4, 0.95), (math.pi / 4 + 0.42, 0.72), (math.pi / 4 - 0.42, 0.72),
                                    (math.pi / 4 + 0.78, 0.5), (math.pi / 4 - 0.78, 0.5))):
            base = (math.cos(a) * g * 0.12, math.sin(a) * g * 0.12)
            tip_len = g * L * 0.8
            f.line([(0, 0), base], w * 1.6, w * 1.4)
            f.add(blatt(base, a, tip_len, tip_len * 0.28))
            f.cut(K.stroke([(base[0] + math.cos(a) * tip_len * 0.18, base[1] + math.sin(a) * tip_len * 0.18),
                            (base[0] + math.cos(a) * tip_len * 0.78, base[1] + math.sin(a) * tip_len * 0.78)],
                           max(0.5, tip_len * 0.035), max(0.5, tip_len * 0.02)))
        f.add(K.circle(0, 0, g * 0.1))
    elif art == "schnoerkel":
        for spiegel in (False, True):
            p0 = (g * 0.12, g * 0.12)
            s = K.chain(K.bez(p0, (g * 0.55, g * 0.02), (g * 0.86, g * 0.16), 18))
            s = K.chain(s, kringel(s[-1], 1.2, g * 0.09, 1, 1.3))
            s2 = K.chain(K.bez((g * 0.4, g * 0.08), (g * 0.5, g * 0.3), (g * 0.38, g * 0.38), 12))
            s2 = K.chain(s2, kringel(s2[-1], 2.4, g * 0.06, 1, 1.2))
            for path, wa, wb in ((s, w * 1.6, w * 0.9), (s2, w * 1.2, w * 0.8)):
                if spiegel:
                    path = [(p[1], p[0]) for p in path]
                f.line(path, wa, wb)
        f.add(K.circle(g * 0.12, g * 0.12, g * 0.1))
        f.cut(K.circle(g * 0.12, g * 0.12, g * 0.1 - 1.5 * w))
        f.add(K.sparkle(g * 0.12, g * 0.12, g * 0.07, 0.3, 4, math.pi / 4))
    else:
        raise ValueError(f"Unbekannte Ecke {art!r}")
    return f


def vier_ecken(x0: float, y0: float, x1: float, y1: float, g: float, art: str = "ranke",
               w: Optional[float] = None) -> Figur:
    """Dasselbe Eckornament in alle vier Ecken des Rechtecks (gespiegelt)."""
    base = ecke(g, art, w)
    f = Figur()
    f.merge(base.map(lambda p: (x0 + p[0], y0 + p[1])))
    f.merge(base.map(lambda p: (x1 - p[0], y0 + p[1])))
    f.merge(base.map(lambda p: (x0 + p[0], y1 - p[1])))
    f.merge(base.map(lambda p: (x1 - p[0], y1 - p[1])))
    return f


# --------------------------------------------------------------------------------------------------
# Bordüren (gerades Zierband)
# --------------------------------------------------------------------------------------------------

def bordure(L: float, h: float, muster: str = "ranke", w: Optional[float] = None, leiste: Optional[float] = None
            ) -> Figur:
    """Zierband x = 0 … L, y = 0 … h. Unten läuft immer eine Grundleiste (Höhe leiste) durch, so hält
    alles zusammen und die Unterkante ist gerade (zum Aufkleben oder Einstecken)."""
    w = w or max(0.9, h * 0.07)
    lb = leiste if leiste is not None else max(w * 1.6, h * 0.16)
    f = Figur().add(K.rect(0, 0, L, lb))
    top = h
    if muster == "ranke":
        f.merge(ranke(L, h - lb * 0.5, True, True, w).map(lambda p: (p[0], p[1] + lb * 0.5)))
        f.add(K.rect(0, 0, w * 1.5, h * 0.7))
        f.add(K.rect(L - w * 1.5, 0, w * 1.5, h * 0.7))
    elif muster == "wellen":
        n = max(1, int(round(L / (h * 1.2))))
        lam = L / n
        for k, (amp, y) in enumerate(((0.28, 0.5), (0.2, 0.82))):
            path = [(x, lb + (h - lb) * (y - 0.15) + (h - lb) * amp * 0.5 * math.sin(TAU * x / lam + k * math.pi))
                    for x in (L * i / (n * 24) for i in range(n * 24 + 1))]
            f.line(path, w * 1.3, w * 1.3, "flach")
        for k in range(n + 1):
            f.add(K.rect(min(max(k * lam - w * 0.7, 0), L - w * 1.4), 0, w * 1.4, h * 0.62))
    elif muster == "kringel":
        n = max(1, int(round(L / (h * 1.1))))
        lam = L / n
        r = (h - lb) * 0.36
        for k in range(n):
            cx = (k + 0.5) * lam
            cy = lb + r * 1.05
            path = K.chain(K.bez((k * lam, lb + w * 0.3), (cx - r * 1.2, cy + r * 1.6), (cx + r * 0.2, cy + r * 1.05), 14),
                           spirale(cx, cy, r * 1.0, r * 0.2, 1.05, math.pi / 2 - 0.2, -1)[1:])
            f.line(path, w * 1.3, w * 0.9)
    elif muster == "bogen":
        n = max(1, int(round(L / (h * 1.0))))
        lam = L / n
        r = lam / 2
        for k in range(n):
            cx = (k + 0.5) * lam
            arc = [(cx + r * math.cos(a), lb + (h - lb) * math.sin(a)) for a in (math.pi * i / 24 for i in range(25))]
            f.add(arc + [(cx - r, lb * 0.5), (cx + r, lb * 0.5)])
            f.cut(K.ellipse(cx, lb + (h - lb) * 0.42, r * 0.42, (h - lb) * 0.3))
        top = h
    elif muster == "zacken":
        n = max(1, int(round(L / (h * 0.8))))
        lam = L / n
        for k in range(n):
            x0 = k * lam
            f.add([(x0, lb * 0.5), (x0 + lam, lb * 0.5), (x0 + lam / 2, h)])
            f.cut([(x0 + lam * 0.33, lb + w), (x0 + lam * 0.67, lb + w), (x0 + lam / 2, lb + (h - lb) * 0.62)])
    elif muster == "herzen":
        n = max(1, int(round(L / (h * 0.95))))
        lam = L / n
        g = min(lam * 0.92, (h - lb) * 1.05)
        for k in range(n):
            cx = (k + 0.5) * lam
            f.add(herz(cx, lb + g * 0.38, g))
            f.add(K.rect(cx - w, lb * 0.5, 2 * w, g * 0.4))
            f.cut(herz(cx, lb + g * 0.42, g * 0.48))
    elif muster == "sterne":
        n = max(1, int(round(L / (h * 0.95))))
        lam = L / n
        rr = min(lam * 0.5, (h - lb) * 0.55)
        for k in range(n):
            cx = (k + 0.5) * lam
            f.add(K.star(cx, h - rr, rr, rr * 0.45, 5))
            f.cut(K.star(cx, h - rr, rr * 0.5, rr * 0.22, 5))
            f.add(K.rect(cx - w * 0.75, 0, w * 1.5, h - rr))
    elif muster == "perlen":
        n = max(1, int(round(L / ((h - lb) * 0.9))))
        lam = L / n
        rr = min(lam * 0.56, (h - lb) * 0.5)
        for k in range(n):
            cx = (k + 0.5) * lam
            f.add(K.circle(cx, lb + rr * 0.92, rr))
            f.cut(K.circle(cx, lb + rr * 0.92, rr * 0.45))
    elif muster == "blaetter":
        # Lorbeerband: schräge Blätter in eine Richtung, jedes mit Mittelrippe
        n = max(1, int(round(L / (h * 0.62))))
        lam = L / n
        Lb = (h - lb * 0.5) * 1.12
        for k in range(n):
            x = k * lam + lam * 0.25
            a = 0.78 if k % 2 == 0 else 1.05
            f.add(blatt((x, lb * 0.5), a, Lb, Lb * 0.27))
            f.cut(K.stroke([(x + math.cos(a) * Lb * 0.25, lb * 0.5 + math.sin(a) * Lb * 0.25),
                            (x + math.cos(a) * Lb * 0.7, lb * 0.5 + math.sin(a) * Lb * 0.7)],
                           max(0.45, Lb * 0.04), max(0.45, Lb * 0.025)))
        f.cut(K.rect(L, 0, h * 2, h * 2))                         # Überstand rechts abschneiden
    elif muster == "tannen":
        n = max(1, int(round(L / (h * 0.75))))
        lam = L / n
        for k in range(n):
            cx = (k + 0.5) * lam
            hh = (h - lb) * (0.82 + 0.18 * ((k * 37) % 3) / 2)
            bw = lam * 0.48
            pts = [(cx - w * 0.8, lb * 0.5)]
            for t in range(3):
                y0 = lb + hh * (0.08 + 0.3 * t)
                y1 = lb + hh * (0.42 + 0.3 * t)
                bb = bw * (1 - 0.28 * t)
                pts += [(cx - bb, y0), (cx - bb * 0.35, y1 - hh * 0.02)]
            pts.append((cx, lb + hh))
            pts += [(2 * cx - x, y) for x, y in reversed(pts[1:-1])]
            pts.append((cx + w * 0.8, lb * 0.5))
            f.add(pts)
    elif muster == "maeander":
        n = max(1, int(round(L / (h * 1.0))))
        lam = L / n
        ww = max(w * 1.3, (h - lb) * 0.16)
        y0, y1 = lb, h - ww * 0.5
        for k in range(n):
            x = k * lam
            u = lam / 4
            path = [(x, y0 + ww * 0.5), (x + u * 3, y0 + ww * 0.5), (x + u * 3, y1), (x + u * 0.5, y1),
                    (x + u * 0.5, y0 + (y1 - y0) * 0.55), (x + u * 2, y0 + (y1 - y0) * 0.55),
                    (x + u * 2, y0 + ww * 0.5 + (y1 - y0) * 0.22)]
            f.line(path, ww, ww, "flach")
            f.add(K.rect(x + u * 3 - ww * 0.5, y0, lam - u * 3 + ww * 0.5, ww))
        f.add(K.rect(0, h - ww, L, ww))
    else:
        raise ValueError(f"Unbekanntes Bordürenmuster {muster!r}")
    return f


# --------------------------------------------------------------------------------------------------
# Verzierungen entlang einer Kontur
# --------------------------------------------------------------------------------------------------

def _entlang(poly: Sequence[Point], step: float, closed: bool = True) -> List[Tuple[Point, Point]]:
    pts = list(poly) + ([poly[0]] if closed else [])
    L = K.path_len(pts)
    n = max(3, int(round(L / step)))
    rs = K.resample(pts, L / n)
    out = []
    for i in range(n if closed else len(rs)):
        a = rs[(i - 1) % n] if closed else rs[max(i - 1, 0)]
        b = rs[(i + 1) % n] if closed else rs[min(i + 1, len(rs) - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        dl = math.hypot(dx, dy) or 1.0
        out.append((rs[i], (dx / dl, dy / dl)))
    return out


def kante(poly: Sequence[Point], muster: str, g: float, w: Optional[float] = None,
          ausser: Optional[Callable[[Point], bool]] = None) -> Figur:
    """Verzierung außen an einer geschlossenen Kontur (CCW): Bögen, Perlen, Zacken … der Größe g.
    Die Figur überlappt die Kontur, also mit add() auf das Teil legen. ausser(p) → True lässt Stellen aus
    (z. B. eine gerade Standfläche)."""
    w = w or max(0.9, g * 0.1)
    f = Figur()
    step = {"bogen": g * 1.5, "perlen": g * 1.05, "zacken": g * 1.1, "wellen": g * 1.6, "herzen": g * 1.3,
            "sterne": g * 1.4, "blaetter": g * 0.9}.get(muster)
    if step is None:
        raise ValueError(f"Unbekannte Kantenverzierung {muster!r}")
    for (x, y), (tx, ty) in _entlang(poly, step):
        if ausser and ausser((x, y)):
            continue
        nx, ny = ty, -tx                                         # außen (Kontur gegen den Uhrzeigersinn)
        a = math.atan2(ny, nx)
        if muster == "bogen":
            r = step / 2
            f.add([(x + tx * r * math.cos(t) + nx * r * 0.75 * math.sin(t) - nx * r * 0.15,
                    y + ty * r * math.cos(t) + ny * r * 0.75 * math.sin(t) - ny * r * 0.15)
                   for t in (math.pi * i / 20 for i in range(21))])
            f.cut(K.circle(x + nx * r * 0.3, y + ny * r * 0.3, max(w * 0.6, r * 0.2)))
        elif muster == "perlen":
            f.add(K.circle(x + nx * g * 0.25, y + ny * g * 0.25, g * 0.55))
        elif muster == "zacken":
            h = g * 0.8
            f.add([(x - tx * step / 2 - nx * g * 0.2, y - ty * step / 2 - ny * g * 0.2),
                   (x + tx * step / 2 - nx * g * 0.2, y + ty * step / 2 - ny * g * 0.2),
                   (x + nx * h, y + ny * h)][::1])
        elif muster == "wellen":
            r = step / 4
            f.add(K.circle(x + nx * r * 0.2, y + ny * r * 0.2, r * 1.15))
        elif muster == "herzen":
            f.add(herz(x + nx * g * 0.3, y + ny * g * 0.3, g, rot=a - math.pi / 2))
        elif muster == "sterne":
            f.add(K.star(x + nx * g * 0.35, y + ny * g * 0.35, g * 0.6, g * 0.27, 5, a))
        elif muster == "blaetter":
            f.add(blatt((x - nx * g * 0.2, y - ny * g * 0.2), a + 0.5, g * 1.1, g * 0.34))
    return f


def durchbruch(poly: Sequence[Point], muster: str, g: float, closed: bool = True,
               ausser: Optional[Callable[[Point], bool]] = None) -> Figur:
    """Ausschnitte (−) entlang einer Linie, z. B. in der Mitte eines Rahmenbands: Punkte, Herzen, Sterne …
    g = Größe eines Motivs. Mit Figur.merge() hinter die Materialflächen setzen."""
    f = Figur()
    step = {"punkte": g * 1.7, "herzen": g * 1.6, "sterne": g * 1.6, "tropfen": g * 1.35, "rauten": g * 1.25,
            "blueten": g * 1.9, "ranke": g * 3.0}.get(muster)
    if step is None:
        raise ValueError(f"Unbekannter Durchbruch {muster!r}")
    for i, ((x, y), (tx, ty)) in enumerate(_entlang(poly, step, closed)):
        if ausser and ausser((x, y)):
            continue
        a = math.atan2(ty, tx)
        if muster == "punkte":
            f.cut(K.circle(x, y, g * 0.42 if i % 2 == 0 else g * 0.28))
        elif muster == "herzen":
            f.cut(herz(x, y - g * 0.05, g * 0.85, rot=a))
        elif muster == "sterne":
            f.cut(K.star(x, y, g * 0.52, g * 0.22, 5, a + math.pi / 2))
        elif muster == "tropfen":
            s = 1 if i % 2 == 0 else -1
            f.cut(tropfen(x - ty * s * g * 0.2, y + tx * s * g * 0.2, g * 0.7, g * 0.36, a + math.pi / 2 * s))
        elif muster == "rauten":
            f.cut([_rot(p, a, (x, y)) for p in raute(x, y, g * 0.8, g * 0.5)])
        elif muster == "blueten":
            for k in range(5):
                b = a + TAU * k / 5
                f.cut(tropfen(x + math.cos(b) * g * 0.16, y + math.sin(b) * g * 0.16, g * 0.42, g * 0.22, b))
        elif muster == "ranke":
            s = 1 if i % 2 == 0 else -1
            p = (x - tx * g * 0.9, y - ty * g * 0.9)
            curl = kringel((x + tx * g * 0.2, y + ty * g * 0.2), a - s * 0.4, g * 0.42, sinn=s, dreh=0.9)
            f.cut(K.stroke(K.chain([p], curl), g * 0.32, g * 0.18, "rund"))
    return f


# --------------------------------------------------------------------------------------------------
# Einzelstücke
# --------------------------------------------------------------------------------------------------

def schleife(b: float, w: Optional[float] = None) -> Figur:
    """Schleife der Breite b, Mitte (0, 0)."""
    w = w or max(0.9, b * 0.04)
    f = Figur()
    for s in (-1, 1):
        loop = K.chain(K.bez3((0, 0), (s * b * 0.25, b * 0.32), (s * b * 0.52, b * 0.3), (s * b * 0.5, b * 0.02), 18),
                       K.bez3((s * b * 0.5, b * 0.02), (s * b * 0.48, -b * 0.2), (s * b * 0.2, -b * 0.1), (0, 0), 18)[1:-1])
        f.add(loop)
        f.cut(K.chain(K.bez3((s * b * 0.1, b * 0.03), (s * b * 0.25, b * 0.2), (s * b * 0.42, b * 0.18),
                             (s * b * 0.41, b * 0.03), 14),
                      K.bez3((s * b * 0.41, b * 0.03), (s * b * 0.38, -b * 0.08), (s * b * 0.2, -b * 0.04),
                             (s * b * 0.1, b * 0.03), 14)[1:-1]))
        tail = [(s * b * 0.04, -b * 0.02), (s * b * 0.3, -b * 0.42), (s * b * 0.22, -b * 0.36), (s * b * 0.17, -b * 0.47),
                (-s * b * 0.04, -b * 0.05)]
        f.add(tail)
    f.add(K.ellipse(0, 0, b * 0.09, b * 0.11))
    return f


def zweig(L: float, art: str = "tanne", w: Optional[float] = None, seed: int = 1) -> Figur:
    """Zweig von (0, 0) nach (L, 0): tanne (Nadeln), blatt (Blätter) oder beere (Blätter und Beeren)."""
    w = w or max(0.9, L * 0.03)
    r = K.rng(seed, "zweig", art)
    stem = [(x, L * 0.04 * math.sin(x / L * math.pi)) for x in (L * i / 20 for i in range(21))]
    f = Figur().line(stem, w * 1.8, w * 1.1, "rund")
    if art == "tanne":
        n = max(4, int(L / (w * 2.2)))
        for i in range(n):
            t = 0.08 + 0.9 * i / n
            x = L * t
            y = L * 0.04 * math.sin(t * math.pi)
            for s in (-1, 1):
                ln = L * (0.2 - 0.12 * t) * (0.85 + 0.3 * r.random())
                a = s * (0.95 - 0.3 * t)
                f.line([(x, y), (x + math.cos(a) * ln, y + math.sin(a) * ln)], w * 1.2, w * 0.7, "spitz")
    else:
        n = max(3, int(L / (L * 0.14)))
        for i in range(n):
            t = 0.12 + 0.8 * i / n
            x = L * t
            y = L * 0.04 * math.sin(t * math.pi)
            s = 1 if i % 2 == 0 else -1
            Lb = L * (0.26 - 0.08 * t)
            f.add(blatt((x, y), s * 0.8, Lb, Lb * 0.32))
            if art == "beere" and i % 2 == 1:
                f.add(K.circle(x + L * 0.04, y - s * L * 0.1, L * 0.045))
                f.add(K.circle(x + L * 0.1, y - s * L * 0.07, L * 0.04))
        f.add(blatt((L * 0.95, 0), 0.0, L * 0.18, L * 0.06))
    return f


def kartusche(W: float, H: float, form: str = "rechteck") -> Poly:
    """Rahmenform um (0, H/2), Breite W, Höhe H: rechteck, abgerundet, oval, bogen, wappen, achteck, kartusche."""
    if form == "rechteck":
        return [(-W / 2, 0), (W / 2, 0), (W / 2, H), (-W / 2, H)]
    if form == "abgerundet":
        r = min(W, H) * 0.12
        out: Poly = []
        for cx, cy, a0 in ((W / 2 - r, r, -math.pi / 2), (W / 2 - r, H - r, 0), (-W / 2 + r, H - r, math.pi / 2),
                           (-W / 2 + r, r, math.pi)):
            out += K.arc(cx, cy, r, a0, a0 + math.pi / 2, 10)
        return out
    if form == "oval":
        return K.ellipse(0, H / 2, W / 2, H / 2, 0, 120)
    if form == "bogen":
        r = W / 2
        hs = max(0.0, H - r)
        return [(-W / 2, 0), (W / 2, 0), (W / 2, hs)] + K.arc(0, hs, r, 0, math.pi, 48)[1:-1] + [(-W / 2, hs)]
    if form == "wappen":
        return K.chain([(-W / 2, H), (-W / 2, H * 0.45)], K.bez((-W / 2, H * 0.45), (-W / 2, H * 0.08), (0, 0), 20)[1:],
                       K.bez((0, 0), (W / 2, H * 0.08), (W / 2, H * 0.45), 20)[1:], [(W / 2, H)])
    if form == "achteck":
        c = min(W, H) * 0.25
        return [(-W / 2 + c, 0), (W / 2 - c, 0), (W / 2, c), (W / 2, H - c), (W / 2 - c, H), (-W / 2 + c, H),
                (-W / 2, H - c), (-W / 2, c)]
    if form == "kartusche":
        # barocke Kartusche: eingezogene Ecken mit Viertelkreisen, oben und unten leicht geschweift
        r = min(W, H) * 0.16
        out = []
        for cx, cy, a0 in ((W / 2, 0, math.pi), (W / 2, H, -math.pi / 2), (-W / 2, H, 0), (-W / 2, 0, math.pi / 2)):
            out += K.arc(cx, cy, r, a0, a0 - math.pi / 2, 10)
            if cy == 0 and cx > 0:
                pass
        # geschweifte Kanten zwischen den Ecken einfügen
        res: Poly = []
        corners = [out[i * 11:(i + 1) * 11] for i in range(4)]
        for i in range(4):
            res += corners[i]
            a, b = corners[i][-1], corners[(i + 1) % 4][0]
            mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
            dx, dy = b[0] - a[0], b[1] - a[1]
            dl = math.hypot(dx, dy) or 1.0
            nx, ny = dy / dl, -dx / dl                         # außen
            bulge = min(W, H) * 0.06
            res += K.bez(a, (mx + nx * bulge * 2, my + ny * bulge * 2), b, 16)[1:-1]
        return res
    raise ValueError(f"Unbekannte Form {form!r}")


FORMEN = [("rechteck", "Rechteck"), ("abgerundet", "Rechteck, abgerundet"), ("oval", "Oval"), ("bogen", "Rundbogen"),
          ("wappen", "Wappen"), ("achteck", "Achteck"), ("kartusche", "Kartusche (barock)")]


# --------------------------------------------------------------------------------------------------
# Ausschnittmotive: einfache Formen, die als Loch aus einer Fläche geschnitten werden
# --------------------------------------------------------------------------------------------------

AUSSCHNITTE = [("herz", "Herz"), ("stern", "Stern"), ("tanne", "Tanne"), ("blume", "Blume"), ("mond", "Mond"),
               ("pilz", "Pilz"), ("kreis", "Kreis"), ("raute", "Raute")]


def ausschnitt(art: str, cx: float, cy: float, g: float) -> Figur:
    """Motiv der Größe ≈ g (Höhe) um (cx, cy) als Loch (mit merge() auf eine Fläche legen)."""
    f = Figur()
    if art == "herz":
        f.cut(herz(cx, cy, g))
    elif art == "stern":
        f.cut(K.star(cx, cy - g * 0.04, g * 0.52, g * 0.22, 5))
    elif art == "tanne":
        for k, (b, y0) in enumerate(((0.9, -0.3), (0.7, -0.05), (0.5, 0.18))):
            h = g * 0.38
            f.cut([(cx - g * b / 2, cy + g * y0), (cx + g * b / 2, cy + g * y0), (cx, cy + g * y0 + h)])
        f.cut(K.rect(cx - g * 0.08, cy - g * 0.5, g * 0.16, g * 0.22))
    elif art == "blume":
        for k in range(5):
            a = TAU * k / 5 + math.pi / 2
            f.cut(tropfen(cx + math.cos(a) * g * 0.16, cy + math.sin(a) * g * 0.16, g * 0.33, g * 0.24, a))
        f.cut(K.circle(cx, cy, g * 0.17))
    elif art == "mond":
        f.cut(K.circle(cx, cy, g * 0.5))
        f.add(K.circle(cx + g * 0.24, cy + g * 0.14, g * 0.44))
    elif art == "pilz":
        f.cut(K.chain(K.arc(cx, cy, g * 0.5, 0, math.pi, 24), [(cx - g * 0.5, cy - g * 0.04), (cx + g * 0.5, cy - g * 0.04)]))
        f.cut(K.rect(cx - g * 0.13, cy - g * 0.5, g * 0.26, g * 0.5))
    elif art == "kreis":
        f.cut(K.circle(cx, cy, g * 0.5))
    elif art == "raute":
        f.cut(raute(cx, cy, g * 0.62, g))
    elif art != "keine":
        raise ValueError(f"Unbekanntes Ausschnittmotiv {art!r}")
    return f
