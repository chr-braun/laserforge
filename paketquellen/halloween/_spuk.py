"""
_spuk.py – fein gezeichnete Halloween-Figuren für das Raster-Verfahren (siehe _kit.py und _ebenen.py).

Jede Figur ist eine _kit.Figur in mm: Flächen werden hinzugefügt (+) oder weggeschnitten (−). Aus der
Figur macht teil() ein laserfestes Teil: zu schmale Stege und Schlitze werden ausgeglichen, lose Inseln
entfallen, runde Löcher (Gelenke, Auffädellöcher) werden danach exakt eingesetzt.

  fledermaus   vier Flügelhaltungen, Flügelknochen als feine Schlitze, Ohren, Augen, Füße, Schwanzflughaut
  kuerbis      Rippen-Buckel, Stiel, Blatt mit Adern, Ranke, geschnitztes Gesicht
  gespenst     mit erhobenen Armen, zerfranstem Saum, Augen und heulendem Mund
  spinne       Kreuzspinne mit gegliederten Beinen, Tastern und Rückenzeichnung
  netz         Spinnennetz: Speichen, durchhängende Fangfäden, Nabe, Tautropfen, gerissene Stellen
"""
from __future__ import annotations

import math
import os
import sys
from typing import List, Optional, Sequence, Tuple

from steckwerk import Part, min_distance, oriented, point_in_polygon
from pakete import bibliothek

_here = os.path.dirname(os.path.abspath(__file__))


def _sub(name: str):
    import importlib.util
    path = os.path.join(_here, name + ".py")
    key = "swpaket_halloween_" + name
    mod = sys.modules.get(key)
    if mod is None or getattr(mod, "__file__", None) != path:
        spec = importlib.util.spec_from_file_location(key, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[key] = mod
        spec.loader.exec_module(mod)
    return mod


K = bibliothek("verzierungen").K
E = bibliothek("verzierungen").E
E.MIN_LOCH = 1.6        # Augen und Zähnchen der Figuren sollen bleiben (kompensiert noch > 1 mm²)
Figur = K.Figur
Point = Tuple[float, float]
Poly = List[Point]
TAU = 2 * math.pi


# --------------------------------------------------------------------------------------------------
# Laser-Grundmaße und Teil aus Figur
# --------------------------------------------------------------------------------------------------

def wmin(cfg) -> float:
    """Schmalster Steg, der das Ausgleichen der Leinwand auch schräg liegend sicher übersteht
    (das Raster rundet achteckig, schräge Stege brauchen etwas mehr als web + kerf + 0.45)."""
    return cfg.min_web + cfg.kerf + 0.75


def smin(cfg) -> float:
    """Schmalster Schlitz, der als Durchbruch erhalten bleibt."""
    return max(cfg.kerf + 0.75, 0.95)


def rot(p: Point, a: float, c: Point = (0.0, 0.0)) -> Point:
    x, y = p[0] - c[0], p[1] - c[1]
    ca, sa = math.cos(a), math.sin(a)
    return (c[0] + x * ca - y * sa, c[1] + x * sa + y * ca)


def lerp(a: Point, b: Point, t: float) -> Point:
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def innen(path: Sequence[Point], poly: Sequence[Point], d: float) -> Poly:
    """Längstes Stück der Linie, das überall mindestens d vom Rand von poly entfernt (und innen) liegt."""
    from steckwerk import point_seg_dist
    n = len(poly)
    best, cur = [], []
    for p in path:
        ok = point_in_polygon(p, poly) and min(point_seg_dist(p, poly[i], poly[(i + 1) % n]) for i in range(n)) >= d
        if ok:
            cur.append(p)
            if len(cur) > len(best):
                best = list(cur)
        else:
            cur = []
    return best


def teil(name: str, fig: Figur, cfg, notes: List[str], loecher: Sequence[Tuple[float, float, float]] = (),
         ring: Optional[float] = None, px: Optional[float] = None, unten_flach: bool = False) -> Part:
    """Figur → laserfestes Teil. loecher = [(x, y, durchmesser)] werden exakt rund geschnitten; um jedes
    Loch bleibt ein Ring aus Material (Breite ring, Standard 1,6 × wmin)."""
    web, kerf = cfg.min_web, cfg.kerf
    ring = ring if ring is not None else max(1.6 * wmin(cfg), 2.2)
    f = Figur(list(fig.ops))
    for x, y, d in loecher:
        f.add(K.circle(x, y, d / 2 + ring, 40))
    x0, y0, x1, y1 = f.bbox()
    if px is None:
        px = max(0.06, min(0.12, max(x1 - x0, y1 - y0) / 1800.0))
    lw = E.Leinwand((x0 - 3, y0 - 3, x1 + 3, y1 + 3), px)
    mat = lw.figur(f)
    if loecher:          # Bereich der runden Löcher frei von Rasterlöchern halten
        mat = mat.union(lw.flaechen([K.circle(x, y, d / 2 + ring * 0.9, 40) for x, y, d in loecher]))
    part = E.teil_aus_raster(name, lw, mat, web, kerf, notes, unten_flach)
    for x, y, d in loecher:
        c = oriented(K.circle(x, y, d / 2, max(24, int(d * 8))), False)
        if not point_in_polygon((x, y), part.outline) or min_distance(c, part.outline, limit=web + 0.3) < web + 0.2:
            raise ValueError(f"{name}: Loch Ø {d:g} mm passt nicht – Teil größer oder Loch kleiner wählen")
        part.holes = [h for h in part.holes
                      if min_distance(h, c, limit=web + 0.3) >= web + 0.2 and not point_in_polygon(h[0], c)
                      and not point_in_polygon((x, y), h)]
        part.add_hole(c)
    return part


def gravur(part: Part, linien: Sequence[Tuple[Sequence[Point], bool]], seed: int = 1, rand: float = 0.9) -> None:
    """Gravurlinien kollisionsfrei setzen (werden an Rand und Durchbrüchen abgeschnitten)."""
    from models import _deko as dk
    cv = dk.Canvas(part, margin=rand, hole_margin=rand, seed=seed)
    for pts, closed in linien:
        if len(pts) >= 2:
            cv.draw(list(pts), closed)


def eingepasst(fig: Figur, groesse: float, cx: float = 0.0, cy: float = 0.0) -> Figur:
    """Figur so skalieren und verschieben, dass ihre größte Abmessung = groesse ist (Mitte cx, cy)."""
    x0, y0, x1, y1 = fig.bbox()
    k = groesse / max(x1 - x0, y1 - y0)
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    return fig.map(lambda p: (cx + (p[0] - mx) * k, cy + (p[1] - my) * k))


# --------------------------------------------------------------------------------------------------
# Fledermaus
# --------------------------------------------------------------------------------------------------

POSEN = [("segeln", "Segeln (Flügel ausgebreitet)"), ("hoch", "Flügel hoch"), ("tief", "Flügel tief"),
         ("kurve", "In der Kurve (ein Flügel hoch)")]

# rechter Flügel ausgebreitet, Einheit = halbe Spannweite
_SH, _EL, _WR = (0.085, 0.045), (0.34, 0.20), (0.58, 0.27)
_TIPS = [(1.00, 0.17), (0.95, -0.08), (0.76, -0.27), (0.48, -0.33)]
_ANK = (0.075, -0.22)


def _fluegel(pose: str) -> Tuple[Point, Point, List[Point], Point, Point]:
    """Ellbogen, Handgelenk, Fingerspitzen, Daumen eines rechten Flügels für eine Haltung."""
    a, fold = {"segeln": (0.0, 0.0), "hoch": (math.radians(40), math.radians(16)),
               "tief": (math.radians(-30), math.radians(-12)), "mitte": (math.radians(14), 0.0)}[pose]
    el, wr = rot(_EL, a, _SH), rot(_WR, a, _SH)
    tips = [rot(rot(t, a, _SH), fold * (0.4 + 0.25 * i), wr) for i, t in enumerate(_TIPS)]
    if pose == "hoch":                       # Hinterkante zieht zur Flanke, letzte Spitze tiefer
        tips[3] = lerp(tips[3], (0.30, -0.10), 0.35)
    thumb = rot((0.615, 0.325), a, _SH)
    return el, wr, tips, thumb, _ANK


def _bogen(a: Point, b: Point, zug: Point, tiefe: float, n: int = 10) -> Poly:
    """Flughaut-Bogen von a nach b, zur Stelle zug hin eingezogen."""
    m = lerp(a, b, 0.5)
    c = lerp(m, zug, tiefe)
    return K.bez(a, c, b, n)


def fledermaus(S: float, pose: str, cfg, augen: bool = True) -> Tuple[Figur, List[Point]]:
    """Fledermaus mit Spannweite ~S (mm), Mitte 0/0. Liefert (Figur, zwei Auffädelpunkte)."""
    s = S / 2
    w, sw = wmin(cfg), smin(cfg)
    f = Figur()
    sides = {"kurve": ("hoch", "mitte")}.get(pose, (pose, pose))
    slits: List[Poly] = []
    lines_k = []
    for side, ps in zip((1, -1), sides):
        el, wr, tips, thumb, ank = _fluegel(ps)
        X = lambda p: (side * p[0] * s, p[1] * s)
        # Vorderkante: Oberarm, Unterarm, langer Finger – leicht gewölbt
        lead = K.spline([_SH, lerp(_SH, el, 0.5), el, lerp(el, wr, 0.5), wr,
                         lerp(wr, tips[0], 0.5), tips[0]], n=6)
        edge = list(lead)
        zug = lerp(wr, _SH, 0.25)
        for i in range(3):
            edge += _bogen(tips[i], tips[i + 1], zug, 0.30 + 0.04 * i, 12)[1:]
        edge += _bogen(tips[3], ank, lerp(_SH, (0.2, 0.0), 0.5), 0.30, 12)[1:]
        edge += [(0.04, -0.12), (0.03, 0.02)]
        f.add([X(p) for p in edge])
        # kräftiger Armknochen an der Vorderkante, Ellbogen- und Handgelenkknöchel
        f.line([X(p) for p in K.spline([_SH, el, wr], n=8)], max(0.045 * s, w))
        f.add(K.circle(*X(el), max(0.03 * s, w * 0.6), 20), K.circle(*X(wr), max(0.032 * s, w * 0.6), 20))
        # Daumenkralle
        f.line([X(wr), X(thumb), X(lerp(thumb, (thumb[0] + 0.03, thumb[1] - 0.01), 1.0))], max(0.022 * s, w), w * 0.7,
               cap="spitz")
        # Fingerknochen als Schlitze (beginnen dort, wo sie weit genug auseinander liegen)
        for i, t in enumerate(tips):
            L = math.hypot(t[0] - wr[0], t[1] - wr[1]) * s
            a0 = max(0.16, (w + sw) * 1.5 / max(L * 0.42, 1e-6))
            if i == 0 or 0.86 - a0 < 0.15:
                continue
            mid = lerp(wr, t, 0.5)
            off = (-(t[1] - wr[1]) * 0.05, (t[0] - wr[0]) * 0.05)
            path = K.bez(lerp(wr, t, a0), (mid[0] + off[0], mid[1] + off[1]), lerp(wr, t, 0.86), 24)
            path = innen([X(p) for p in path], [X(p) for p in edge], w + sw / 2 + 0.6)
            if len(path) >= 2 and K.path_len(path) >= 2.5:
                slits.append(K.stroke(path, sw, sw * 0.9, "rund"))
        # Falten der Flughaut (Gravur)
        for i in range(3):
            m = lerp(tips[i + 1], tips[i], 0.5)
            lines_k.append(([X(lerp(wr, m, 0.35)), X(lerp(lerp(wr, m, 0.6), zug, 0.12)), X(lerp(wr, m, 0.78))], False))
    # Körper mit Fellzipfeln, Kopf, Ohren – Kopf mindestens so groß, dass Augen Platz haben
    rx, ry = max(0.02 * s, 1.05), max(0.013 * s, 0.72)
    ex = rx + w / 2 + 0.25
    hr = max(0.085 * s, (ex + rx + w + 0.1) if augen else 2 * w + 1.2)
    hy = 0.075 * s + hr * 0.35
    body = []
    for i in range(48):
        t = TAU * i / 48
        r = 1.0 + (0.10 if i % 4 == 0 and math.sin(t) < 0.4 else 0.0)
        body.append((max(0.088 * s, hr * 0.72) * math.cos(t) * r, -0.05 * s + 0.165 * s * math.sin(t) * r))
    f.add(body)
    f.add(K.circle(0.0, hy, hr, 40))
    ew = max(0.075 * s, 2.2 * w)                                  # Ohrbreite am Ansatz
    eh = max(0.17 * s, 2.4 * w)                                   # Ohrhöhe über dem Kopf
    for side in (1, -1):
        X = lambda u, v: (side * u, hy + v)
        f.add(K.chain(K.bez(X(0.10 * hr, 0.6 * hr), X(0.18 * hr + 0.2 * ew, hr + 0.3 * eh),
                            X(0.45 * hr + 0.75 * ew, hr + eh), 8),
                      K.bez(X(0.45 * hr + 0.75 * ew, hr + eh), X(0.55 * hr + 0.9 * ew, hr + 0.3 * eh),
                            X(1.0 * hr, 0.45 * hr), 8), [X(0.9 * hr, 0.0)]))
        # Füße mit Krallen
        foot = (side * 0.035 * s, -0.23 * s)
        f.line([(side * 0.03 * s, -0.17 * s), foot], max(0.035 * s, w * 1.1))
        if 0.012 * s >= w * 0.8:
            for k in (-1, 0, 1):
                f.line([foot, (foot[0] + side * (0.014 + 0.014 * k) * s, foot[1] - 0.045 * s)], max(0.012 * s, w),
                       cap="spitz")
    # Schwanzflughaut zwischen den Füßen
    f.add(K.chain([(-0.075 * s, -0.20 * s), (0.075 * s, -0.20 * s)],
                  K.bez((0.075 * s, -0.20 * s), (0.0, -0.27 * s), (-0.075 * s, -0.20 * s), 10)))
    for sl in slits:
        f.cut(sl)
    if augen:
        ey = hy + 0.15 * hr
        if ex + rx + w <= hr:
            for side in (1, -1):
                f.cut(K.ellipse(side * ex, ey, rx, ry, side * math.radians(-22), 24))
            # Mund mit zwei Zähnchen, wenn unter den Augen genug Platz bleibt
            mt = ey - ry - w - 0.3
            mw, mh = max(0.03 * s, 2.2 * sw), max(0.022 * s, 1.6)
            if mt - mh >= hy - hr * 0.9 and mw + w <= hr:
                f.cut([(-mw, mt), (mw, mt), (mw * 0.5, mt - mh), (mw * 0.28, mt - mh * 0.45),
                       (-mw * 0.28, mt - mh * 0.45), (-mw * 0.5, mt - mh)])
        # Innenohr nur, wenn das Ohr breit genug ist
        if ew * 0.6 >= sw + 2 * w:
            for side in (1, -1):
                x0 = side * (hr * 0.15 + ew * 0.55)
                f.cut(K.stroke([(x0, hy + hr * 0.9), (x0 + side * ew * 0.15, hy + hr + 0.07 * s)], sw, sw, "rund"))
    f.gravur = lines_k
    hy_ = {"tief": -0.07}.get(pose, 0.035)
    holes = [(-0.24 * s, hy_ * s), (0.24 * s, hy_ * s)]
    return f, holes


# --------------------------------------------------------------------------------------------------
# Kürbis
# --------------------------------------------------------------------------------------------------

def kuerbis(S: float, cfg, gesicht: str = "klassisch", seed: int = 1) -> Tuple[Figur, List[Point]]:
    """Kürbis, Breite ~S, Mitte 0/0, mit Stiel, Blatt, Ranke und Gesicht."""
    s = S
    w, sw = wmin(cfg), smin(cfg)
    f = Figur()
    lobes = [(0.0, 0.0, 0.25, 0.38), (0.19, -0.01, 0.24, 0.36), (-0.19, -0.01, 0.24, 0.36),
             (0.33, -0.03, 0.16, 0.30), (-0.33, -0.03, 0.16, 0.30)]
    for x, y, rx, ry in lobes:
        f.add(K.ellipse(x * s, y * s, rx * s, ry * s, 0.0, 64))
    # Stiel (gebogen, oben schräg abgeschnitten), Blatt, Ranke
    f.line([(0.0, 0.32 * s), (0.01 * s, 0.42 * s), (0.05 * s, 0.50 * s)], 0.085 * s, 0.065 * s, cap="flach")
    f.add([(0.02 * s, 0.53 * s), (0.085 * s, 0.505 * s), (0.07 * s, 0.47 * s), (0.015 * s, 0.48 * s)])
    mid = K.bez((0.05 * s, 0.40 * s), (0.16 * s, 0.50 * s), (0.31 * s, 0.47 * s), 16)
    lw_ = [max(0.12 * s * math.sin(math.pi * (0.08 + 0.92 * i / 16)) ** 0.8, w) *
           (1 + 0.18 * math.sin(i * 1.9)) for i in range(17)]
    f.add(K.stroke(mid, 0, widths=lw_, cap="spitz"))
    f.line(K.spline([(-0.02 * s, 0.37 * s), (-0.10 * s, 0.43 * s), (-0.17 * s, 0.42 * s), (-0.19 * s, 0.37 * s),
                     (-0.15 * s, 0.345 * s), (-0.125 * s, 0.37 * s)], n=8), max(0.018 * s, w))
    # Blattadern als Schlitze, wenn das Blatt breit genug ist
    if 0.12 * s >= sw + 2 * w + 0.8:
        f.cut(K.stroke(mid[3:13], sw, sw * 0.8))
        if 0.12 * s >= 2 * sw + 3 * w + 2:
            for i in (6, 9):
                q = mid[i]
                f.cut(K.stroke([(q[0] + 0.012 * s, q[1] + 0.006 * s), (q[0] + 0.03 * s, q[1] + 0.035 * s)], sw, sw))
    for side in (1, -1):
        for x0, bend in ((0.27, 0.05),):
            path = K.bez((side * x0 * s, 0.22 * s), (side * (x0 + bend) * s, -0.03 * s), (side * x0 * s, -0.27 * s), 14)
            f.cut(K.stroke(path, sw, sw, "rund"))
    # Gesicht
    if gesicht == "klassisch":
        for side in (1, -1):
            f.cut([(side * 0.05 * s, 0.06 * s), (side * 0.19 * s, 0.07 * s), (side * 0.125 * s, 0.19 * s)])
        f.cut([(-0.035 * s, -0.015 * s), (0.035 * s, -0.015 * s), (0.0, 0.05 * s)])
        top = [(-0.21 * s, -0.07 * s), (-0.13 * s, -0.10 * s), (-0.10 * s, -0.06 * s), (-0.065 * s, -0.11 * s),
               (0.065 * s, -0.11 * s), (0.10 * s, -0.06 * s), (0.13 * s, -0.10 * s), (0.21 * s, -0.07 * s)]
        bot = [(0.16 * s, -0.17 * s), (0.08 * s, -0.215 * s), (0.055 * s, -0.17 * s), (0.02 * s, -0.225 * s),
               (-0.06 * s, -0.22 * s), (-0.085 * s, -0.175 * s), (-0.11 * s, -0.205 * s), (-0.16 * s, -0.17 * s)]
        f.cut(top + bot)
    elif gesicht == "gruselig":             # schräge Augen, Fangzähne
        for side in (1, -1):
            f.cut([(side * 0.04 * s, 0.06 * s), (side * 0.20 * s, 0.15 * s), (side * 0.17 * s, 0.04 * s)])
        f.cut([(0.0, 0.03 * s), (0.03 * s, -0.03 * s), (-0.03 * s, -0.03 * s)])
        f.cut([(-0.22 * s, -0.06 * s), (-0.12 * s, -0.11 * s), (-0.10 * s, -0.19 * s), (-0.07 * s, -0.115 * s),
               (0.07 * s, -0.115 * s), (0.10 * s, -0.19 * s), (0.12 * s, -0.11 * s), (0.22 * s, -0.06 * s),
               (0.15 * s, -0.20 * s), (0.0, -0.25 * s), (-0.15 * s, -0.20 * s)])
    f.gravur = [(K.bez((side * 0.12 * s, 0.30 * s), (side * 0.17 * s, 0.05 * s), (side * 0.13 * s, -0.30 * s), 14),
                 False) for side in (1, -1)]
    holes = [(-0.30 * s, 0.17 * s), (0.30 * s, 0.17 * s)]
    return f, holes


# --------------------------------------------------------------------------------------------------
# Gespenst
# --------------------------------------------------------------------------------------------------

def gespenst(S: float, cfg, seed: int = 1) -> Tuple[Figur, List[Point]]:
    """Gespenst mit erhobenen Armen, Höhe ~S, Mitte 0/0."""
    s = S
    w, sw = wmin(cfg), smin(cfg)
    f = Figur()
    right = [(0.0, 0.50), (0.13, 0.47), (0.205, 0.37), (0.225, 0.25), (0.29, 0.25), (0.36, 0.30), (0.40, 0.37),
             (0.44, 0.40), (0.445, 0.355), (0.47, 0.33), (0.43, 0.29), (0.40, 0.22), (0.33, 0.15), (0.26, 0.10),
             (0.25, -0.05), (0.28, -0.20), (0.34, -0.32), (0.42, -0.40), (0.47, -0.47), (0.36, -0.445),
             (0.28, -0.40), (0.22, -0.47), (0.15, -0.40), (0.08, -0.48), (0.02, -0.41)]
    left = [(-0.05, -0.47), (-0.11, -0.40), (-0.18, -0.46), (-0.24, -0.38), (-0.30, -0.42), (-0.26, -0.25),
            (-0.24, -0.08), (-0.25, 0.08), (-0.32, 0.13), (-0.40, 0.21), (-0.45, 0.30), (-0.47, 0.36),
            (-0.43, 0.345), (-0.42, 0.40), (-0.38, 0.36), (-0.31, 0.29), (-0.225, 0.25), (-0.205, 0.37),
            (-0.13, 0.47)]
    body = K.spline([(x * s, y * s) for x, y in right + left], closed=True, n=6, tension=0.45)
    f.add(body)
    for side in (1, -1):
        f.cut(K.ellipse(side * 0.075 * s, 0.30 * s, 0.045 * s, 0.07 * s, side * math.radians(10), 32))
    f.cut(K.ellipse(0.0, 0.15 * s, 0.045 * s, 0.07 * s, 0.0, 32))
    # Faltenschlitze im Laken
    for path in (K.bez((0.13 * s, 0.02 * s), (0.16 * s, -0.15 * s), (0.22 * s, -0.31 * s), 12),
                 K.bez((-0.12 * s, 0.0), (-0.14 * s, -0.14 * s), (-0.13 * s, -0.30 * s), 12),
                 K.bez((0.02 * s, -0.08 * s), (0.04 * s, -0.20 * s), (0.08 * s, -0.33 * s), 12)):
        f.cut(K.stroke(path, sw, sw * 0.9))
    f.gravur = [(K.bez((-0.30 * s, 0.20 * s), (-0.36 * s, 0.26 * s), (-0.40 * s, 0.31 * s), 8), False),
                (K.bez((0.30 * s, 0.21 * s), (0.36 * s, 0.27 * s), (0.39 * s, 0.33 * s), 8), False)]
    holes = [(-0.17 * s, 0.15 * s), (0.17 * s, 0.15 * s)]
    return f, holes


# --------------------------------------------------------------------------------------------------
# Spinne
# --------------------------------------------------------------------------------------------------

def spinne(S: float, cfg, cx: float = 0.0, cy: float = 0.0, ang: float = 0.0, zeichnung: bool = True) -> Figur:
    """Kreuzspinne von oben, Beinspanne ~S, Kopf zeigt nach oben (ang dreht), Mitte = Kopfbruststück."""
    s = S
    w, sw = wmin(cfg), smin(cfg)
    f = Figur()
    lw0, lw1 = max(0.045 * s, w), max(0.028 * s, w)
    # Beine: Ansatz am Kopfbruststück, Knie, Fersengelenk, Fuß (rechts; links gespiegelt)
    legs = [((0.04, 0.05), (0.17, 0.25), (0.25, 0.36), (0.29, 0.46)),
            ((0.05, 0.02), (0.24, 0.13), (0.38, 0.12), (0.47, 0.06)),
            ((0.05, -0.02), (0.22, -0.02), (0.34, -0.12), (0.42, -0.22)),
            ((0.04, -0.05), (0.15, -0.15), (0.22, -0.30), (0.24, -0.45))]
    for side in (1, -1):
        for base, knee, heel, foot in legs:
            P = [(side * x * s, y * s) for x, y in (base, knee, heel, foot)]
            f.add(K.stroke(P[:2], lw0, lw0 * 0.9, "rund"))
            f.add(K.stroke(P[1:3], lw0 * 0.9, lw1, "rund"))
            f.add(K.stroke(P[2:], lw1, max(w, lw1 * 0.7), "spitz"))
            for q, r in ((P[1], lw0 * 0.62), (P[2], lw1 * 0.62)):
                f.add(K.circle(q[0], q[1], max(r, w * 0.55), 16))
        # Taster
        f.add(K.stroke([(side * 0.025 * s, 0.10 * s), (side * 0.06 * s, 0.155 * s), (side * 0.045 * s, 0.19 * s)],
                       max(0.03 * s, w), max(0.022 * s, w * 0.8)))
    f.add(K.ellipse(0.0, 0.02 * s, 0.075 * s, 0.095 * s, 0.0, 40))                # Kopfbruststück
    f.add(K.ellipse(0.0, -0.085 * s, max(0.05 * s, 1.5 * w), max(0.05 * s, w), 0.0, 24))     # Stiel
    ab = K.spline([(0.0, -0.08 * s), (0.10 * s, -0.10 * s), (0.135 * s, -0.20 * s), (0.11 * s, -0.31 * s),
                   (0.0, -0.37 * s), (-0.11 * s, -0.31 * s), (-0.135 * s, -0.20 * s), (-0.10 * s, -0.10 * s)],
                  closed=True, n=8)
    f.add(ab)
    if zeichnung and 0.031 * s >= w + 0.3 and 0.012 * s >= sw * 0.6:
        # Kreuz aus Punkten und Seitenflecken (nur wenn die Stege dazwischen halten)
        r = 0.012 * s
        for x, y in ((0, -0.15), (0, -0.205), (0, -0.26), (0.055, -0.205), (-0.055, -0.205)):
            f.cut(K.circle(x * s, y * s, r, 16))
        for side in (1, -1):
            f.cut(K.stroke([(side * 0.098 * s, -0.13 * s), (side * 0.112 * s, -0.21 * s), (side * 0.09 * s, -0.29 * s)],
                           max(0.014 * s, sw), max(0.011 * s, sw)))
            f.cut(K.circle(side * 0.025 * s, 0.075 * s, max(0.010 * s, sw * 0.55), 12))      # Augen
    out = f.place(cx, cy, 1.0, ang)
    return out


def spinne_frei(S: float, cfg, cx: float = 0.0, cy: float = 0.0, ang: float = 0.0) -> Figur:
    """Schnittflächen, die das Netz unter dem Spinnenkörper freistellen (vor spinne() anwenden)."""
    g = smin(cfg) + 0.6
    f = Figur()
    f.cut(K.ellipse(0.0, 0.02 * S, 0.075 * S + g, 0.095 * S + g, 0.0, 40))
    f.cut(K.ellipse(0.0, -0.225 * S, 0.135 * S + g, 0.15 * S + g, 0.0, 40))
    return f.place(cx, cy, 1.0, ang)


# --------------------------------------------------------------------------------------------------
# Spinnennetz
# --------------------------------------------------------------------------------------------------

def netz(cx: float, cy: float, R: float, a0: float, a1: float, ringe: int, speichen: int, w: float,
         seed: int = 1, riss: bool = False, tropfen: bool = True, voll: bool = True):
    """Netz als Figur aus Fäden (Material) zwischen den Winkeln a0..a1. voll = geschlossener Kreis.
    Liefert (Figur, Speichen-Endpunkte, Punkte auf dem äußersten Fangfaden zum Anhängen)."""
    r = K.rng(seed, "netz", ringe, speichen)
    n_sp = speichen if voll else speichen + 1
    span = (a1 - a0)
    angs = []
    for i in range(n_sp):
        t = i / (speichen if voll else speichen)
        j = 0.0 if (i == 0 or (not voll and i == n_sp - 1)) else K.jitter(r, 0.18) * span / speichen
        angs.append(a0 + span * t + j)
    hub = max(0.07 * R, 2.2 * w, (w + 3.2) / (span / speichen))
    radii = []
    for k in range(ringe):
        t = (k + 1) / ringe
        radii.append(hub + (R - hub) * t ** 0.92)
    # Radius je Speiche leicht unregelmäßig
    rr = [radii[k] * (1 + K.jitter(r, 0.03)) if (k < ringe - 1 and (voll or 0 < i < n_sp - 1)) else radii[k]
          for k in range(ringe) for i in range(n_sp)]
    RR = lambda k, i: rr[k * n_sp + i]
    P = lambda rad, a: (cx + rad * math.cos(a), cy + rad * math.sin(a))
    f = Figur()
    ends = []
    sag = 0.20
    pairs = list(range(n_sp)) if voll else list(range(n_sp - 1))
    torn = set()
    if riss:
        for _ in range(max(1, ringe * len(pairs) // 26)):
            k = r.randrange(1, ringe - 1) if ringe > 2 else 0
            torn.add((k, r.choice(pairs)))
    outer_pts = []
    for k in range(ringe):
        thick = w * (1.25 if k == ringe - 1 else 1.0)
        for i in pairs:
            j = (i + 1) % n_sp
            pa, pb = P(RR(k, i), angs[i]), P(RR(k, j), angs[j] + (TAU if j < i else 0.0))
            m = lerp(pa, pb, 0.5)
            depth = sag * (1 - 0.35 * (k == ringe - 1))
            c = lerp(m, (cx, cy), depth * math.hypot(pb[0] - pa[0], pb[1] - pa[1]) / max(RR(k, i), 1e-6))
            curve = K.bez(pa, c, pb, 14)
            if (k, i) in torn:
                # gerissener Faden: zwei hängende Enden
                L = len(curve)
                e1 = curve[:L // 3]
                e2 = curve[-L // 4:]
                d1 = [e1[-1], (e1[-1][0], e1[-1][1] - 0.04 * R)]
                f.line(e1 + [d1[1]], w)
                f.line([(e2[0][0], e2[0][1] - 0.025 * R)] + e2, w)
                continue
            f.line(curve, thick)
            if k == ringe - 1:
                outer_pts.append(lerp(pa, pb, 0.5))
            if tropfen and k % 2 == 1 and r.random() < 0.28:
                q = curve[r.randrange(3, 11)]
                f.add(K.circle(q[0], q[1], w * 0.95, 16))
    for i in range(n_sp):
        e = P(RR(ringe - 1, i), angs[i])
        ends.append(e)
        f.line([P(hub * 0.5, angs[i]), e], w)
    # Nabe: volle Scheibe (bzw. Viertel), darauf eine gravierte Spirale
    rh = hub * 0.92
    if voll:
        f.add(K.circle(cx, cy, rh, 48))
    else:
        f.add([(cx, cy)] + K.arc(cx, cy, rh, a0, a1, 24))
    spiral = []
    turns = 3.0 if voll else 0.75
    for j in range(int(60 * turns) + 1):
        t = j / (60 * turns)
        a = a0 + 0.08 + (TAU * turns if voll else (span - 0.16)) * t
        rad = rh * (0.15 + 0.7 * t) if voll else rh * (0.25 + 0.55 * (j % 60 / 60.0 if False else t))
        spiral.append(P(rad, a))
    f.gravur = [(spiral, False)]
    if not voll:
        f.gravur = [(K.arc(cx, cy, rh * q, a0 + 0.1, a1 - 0.1, 20), False) for q in (0.35, 0.55, 0.75)]
    return f, ends, outer_pts, angs, radii
