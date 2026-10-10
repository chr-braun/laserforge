"""
fahrzeug.py – Steckfahrzeuge: Auto, Lkw, Lok und Schlitten.

Aufbau (alle Typen gleich):
  seite_l / seite_r   zwei gespiegelte Seitenwände mit Profil, Fenstern, Gravur
  Querteile           liegende (Boden, Dach, Sitz) und stehende Platten (Front, Heck, Lehne);
                      ihre Tabs stecken in Slots der Seitenwände (Tab/Slot 1:1 vom Validator geprüft)
  achse_N             Vierkantstab T × T aus derselben Platte; dreht in runden Lagerbohrungen
                      der Seitenwände (Ø = Diagonale + Spiel)
  rad_N…              Räder mit Vierkant-Nabe T × T – sitzen fest auf der Achse und halten sie seitlich

Koordinaten: x entlang des Fahrzeugs (0 = Heck, L = Front), y nach oben (0 = Boden/Straße),
z quer (0 … W_in zwischen den Seitenwänden). Die rechte Seitenwand ist gespiegelt (x → L − x),
damit die Gravur nach dem Umdrehen außen liegt; Text wird dabei nicht gespiegelt.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Sequence, Tuple

from steckwerk import (Assembly, Config, JointFeature, Part, Point, arc_points, circle, clean,
                        inset_polygon, min_distance, mirror_x, oriented, point_in_polygon, polygon_ok,
                        profile_edge,
                        rect, slot_feature, tab_centers,
                        tab_features, tab_segments)
from models import _deko as dk
from models._font import CASES, STYLES, fit_text, unsupported
from models._shapes import star

VEHICLES = ["auto", "lkw", "lok", "schlitten", "tender", "personenwagen", "gueterwagen", "bus", "traktor"]
DEFAULTS = {
    "auto": dict(length=120.0, width=60.0),
    "lkw": dict(length=150.0, width=64.0),
    "lok": dict(length=150.0, width=60.0),
    "schlitten": dict(length=140.0, width=64.0),
    "tender": dict(length=95.0, width=60.0),
    "personenwagen": dict(length=140.0, width=60.0),
    "gueterwagen": dict(length=140.0, width=60.0),
    "bus": dict(length=160.0, width=64.0),
    "traktor": dict(length=120.0, width=60.0),
}
MIN_LENGTH = {"auto": 80.0, "lkw": 100.0, "lok": 100.0, "schlitten": 90.0, "tender": 70.0, "personenwagen": 100.0,
              "gueterwagen": 100.0, "bus": 110.0, "traktor": 90.0}
TRAIN = ("lok", "tender", "personenwagen", "gueterwagen")
WHEEL_GAP = 0.8          # Luft zwischen Rad und Seitenwand
AXLE_PLAY = 0.6          # Lagerbohrung = Achsdiagonale + Spiel


# ---------------------------------------------------------------------------
# Geometrie-Helfer
# ---------------------------------------------------------------------------

def fillet(pts: Sequence[Tuple[float, float, float]], tol: float = 0.05) -> List[Point]:
    """Polygon aus (x, y, radius) mit abgerundeten Ecken (Radius wird an kurze Kanten angepasst)."""
    n = len(pts)
    out: List[Point] = []
    for i in range(n):
        ax, ay, _ = pts[i - 1]
        bx, by, r = pts[i]
        cx, cy, _ = pts[(i + 1) % n]
        if r <= 0:
            out.append((bx, by))
            continue
        l1, l2 = math.hypot(ax - bx, ay - by), math.hypot(cx - bx, cy - by)
        u1 = ((ax - bx) / l1, (ay - by) / l1)
        u2 = ((cx - bx) / l2, (cy - by) / l2)
        cosang = max(-1.0, min(1.0, u1[0] * u2[0] + u1[1] * u2[1]))
        ang = math.acos(cosang)
        if ang < 1e-3 or ang > math.pi - 1e-3:
            out.append((bx, by))
            continue
        d = r / math.tan(ang / 2)
        d = min(d, 0.45 * l1, 0.45 * l2)
        r = d * math.tan(ang / 2)
        t1 = (bx + u1[0] * d, by + u1[1] * d)
        t2 = (bx + u2[0] * d, by + u2[1] * d)
        bis = (u1[0] + u2[0], u1[1] + u2[1])
        bl = math.hypot(*bis)
        k = r / math.sin(ang / 2)
        c = (bx + bis[0] / bl * k, by + bis[1] / bl * k)
        a1 = math.atan2(t1[1] - c[1], t1[0] - c[0])
        a2 = math.atan2(t2[1] - c[1], t2[0] - c[0])
        delta = (a2 - a1 + math.pi) % (2 * math.pi) - math.pi
        steps = max(2, int(math.ceil(abs(delta) / (2 * math.acos(max(-1.0, 1 - tol / r))))))
        out += [(c[0] + r * math.cos(a1 + delta * s / steps), c[1] + r * math.sin(a1 + delta * s / steps))
                for s in range(steps + 1)]
    return clean(out)


def clip(poly: Sequence[Point], a: float, b: float, c: float) -> List[Point]:
    """Sutherland–Hodgman: behält den Teil mit a·x + b·y ≤ c."""
    out: List[Point] = []
    n = len(poly)
    for i in range(n):
        p, q = poly[i], poly[(i + 1) % n]
        fp, fq = a * p[0] + b * p[1] - c, a * q[0] + b * q[1] - c
        if fp <= 0:
            out.append(p)
        if fp * fq < 0:
            t = fp / (fp - fq)
            out.append((p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])))
    return clean(out) if len(out) >= 3 else []


def window(outline: Sequence[Point], x0: float, x1: float, y0: float, y1: float, p: float,
           r: float = 1.5) -> List[Point]:
    """Fenster im Rechteck [x0,x1]×[y0,y1], das zusätzlich Abstand p zur Außenkontur hält."""
    if x1 - x0 < 3.0 or y1 - y0 < 3.0:
        return []
    P = list(outline)
    for a, b, c in ((1, 0, x1 + p), (-1, 0, -(x0 - p)), (0, 1, y1 + p), (0, -1, -(y0 - p))):
        P = clip(P, a, b, c)
        if not P:
            return []
    W = inset_polygon(P, p) if p > 0 else P
    if len(W) < 3:
        return []
    return fillet([(x, y, r) for x, y in W]) if r > 0 else W


def top_y(outline: Sequence[Point], x: float) -> float:
    ys = []
    n = len(outline)
    for i in range(n):
        a, b = outline[i], outline[(i + 1) % n]
        if (a[0] - x) * (b[0] - x) <= 0 and a[0] != b[0]:
            ys.append(a[1] + (x - a[0]) / (b[0] - a[0]) * (b[1] - a[1]))
    return max(ys)


def span_at(outline: Sequence[Point], y: float, x_ref: float) -> Tuple[float, float]:
    """Waagrechtes Innenintervall der Kontur auf Höhe y, das x_ref enthält."""
    xs = []
    n = len(outline)
    for i in range(n):
        a, b = outline[i], outline[(i + 1) % n]
        if (a[1] - y) * (b[1] - y) < 0:
            xs.append(a[0] + (y - a[1]) / (b[1] - a[1]) * (b[0] - a[0]))
    xs.sort()
    for l, r in zip(xs[0::2], xs[1::2]):
        if l <= x_ref <= r:
            return l, r
    raise ValueError(f"Höhe {y:.1f} mm liegt bei x = {x_ref:.1f} mm außerhalb der Seitenwand")


# ---------------------------------------------------------------------------
# Bauplan
# ---------------------------------------------------------------------------

@dataclass
class Member:
    """Querteil zwischen den Seitenwänden.
    orient 'h': liegt waagrecht, y = at … at+T, reicht in x von a0 bis a1
    orient 'v': steht senkrecht, x = at−T/2 … at+T/2, reicht in y von a0 bis a1"""
    name: str
    orient: str
    at: float
    a0: float
    a1: float
    count: Optional[int] = None
    deco: Optional[Callable[[Part, float, float], None]] = None   # (teil, länge, W_in)


@dataclass
class Spec:
    kind: str
    L: float
    W_in: float
    outline: List[Point]
    windows: List[List[Point]] = field(default_factory=list)
    engrave: List[Tuple[List[Point], bool]] = field(default_factory=list)
    extras: List[Tuple[List[Point], bool]] = field(default_factory=list)     # weichen der Aufschrift
    text_box: Optional[Tuple[float, float, float, float]] = None     # cx, cy, w, h
    axles: List[float] = field(default_factory=list)
    axle_y: float = 0.0
    rw: float = 0.0
    wheel_style: str = "voll"
    members: List[Member] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    radii: Optional[List[float]] = None             # je Achse eigener Radius (Traktor); Achshöhe = Radius
    couple: List[str] = field(default_factory=list)  # Querteile mit Kupplungsloch (Zug)
    couple_y: float = 0.0

    def axle_at(self, k: int) -> Tuple[float, float]:
        """(Achshöhe, Radradius) der Achse k."""
        r = self.radii[k] if self.radii else self.rw
        return (r if self.radii else self.axle_y), r


class Dims:
    """Gemeinsame Maße eines Fahrzeugs."""

    def __init__(self, cfg: Config, L: float, W: float, rw: float):
        self.T = cfg.T
        self.L, self.W = L, W
        self.W_in = W - 2 * self.T
        self.web = max(cfg.min_web, 2.0, 0.8 * self.T)
        self.rb = (self.T * math.sqrt(2) + AXLE_PLAY) / 2          # Lagerbohrung Radius
        self.rw = rw
        self.ya = rw                                                # Achshöhe
        self.yb = self.ya - self.rb - self.web - 0.5                # Unterkante Seitenwand
        self.yf = self.ya + self.rb + self.web                      # Boden (Unterseite)
        if self.W_in < 4 * self.T + 10:
            raise ValueError(f"Fahrzeug zu schmal: Innenbreite {self.W_in:.1f} mm")
        if self.yb < 1.5:
            raise ValueError("Räder zu klein für die Materialstärke (Bodenfreiheit < 1.5 mm)")


def _h_extent(outline, y, T, x_ref, margin=1.0):
    l1, r1 = span_at(outline, y + 1e-6, x_ref)
    l2, r2 = span_at(outline, y + T - 1e-6, x_ref)
    return max(l1, l2) + margin, min(r1, r2) - margin


def _v_top(outline, x, T, web, margin=1.0):
    return min(top_y(outline, x - T / 2), top_y(outline, x + T / 2)) - web - margin


def _resolve(members: Sequence[Member], T: float) -> None:
    """Stehende Platten enden unter liegenden, die über ihnen durchlaufen; echte Durchdringung = Fehler."""
    for h in members:
        if h.orient != "h":
            continue
        for v in members:
            if v.orient != "v" or not (h.a0 < v.at + T / 2 and h.a1 > v.at - T / 2):
                continue
            if h.at + T <= v.a0 + 1e-6 or h.at >= v.a1 + 0.3 - 1e-6:
                continue
            if h.at >= (v.a0 + v.a1) / 2:
                v.a1 = h.at - 0.3
            else:
                raise ValueError(f"Querteile {h.name} und {v.name} durchdringen sich")


def _ends(d: Dims, xf: float, xr: float) -> Tuple[float, float]:
    """Front-/Heckplatte so weit innen, dass ihr Slot einen Steg zur Außenkante behält."""
    m = d.T / 2 + d.web
    return min(xf, d.L - m), max(xr, m)


def _check_axles(d: Dims, xs: Sequence[float]) -> None:
    for a, b in zip(xs, xs[1:]):
        if b - a < 2 * d.rw + 3:
            raise ValueError("Räder zu groß für den Achsabstand")
    if xs and (xs[0] < d.rw * 0.6 or xs[-1] > d.L - d.rw * 0.6):
        raise ValueError("Räder ragen zu weit über das Fahrzeug hinaus")


# --- Dekor für Querteile (lokal: x = Länge entlang a0→a1, y = quer 0…W_in) -------------------

def _grille(part: Part, length: float, W: float) -> None:
    n = max(2, int(length // 4))
    for i in range(1, n):
        u = length * i / n
        part.add_engrave([(u, W * 0.18), (u, W * 0.82)])


def _plate(part: Part, length: float, W: float) -> None:
    h, w = min(0.5 * length, 8.0), min(0.5 * W, 22.0)
    part.add_engrave(rect(length / 2 - h / 2, W / 2 - w / 2, h, w), closed=True)


def _planks(part: Part, length: float, W: float) -> None:
    n = max(2, int(W // 8))
    for i in range(1, n):
        part.add_engrave([(1.5, W * i / n), (length - 1.5, W * i / n)])


def _smokebox(part: Part, length: float, W: float) -> None:
    r = min(length, W) * 0.36
    part.add_engrave(circle(length * 0.5, W / 2, r, 0.1), closed=True)
    part.add_engrave([(length * 0.5, W / 2 - r * 0.6), (length * 0.5, W / 2 + r * 0.6)])


def _stars(part: Part, length: float, W: float) -> None:
    r = min(length, W) * 0.22
    if r >= 2.5:
        part.add_engrave(star(length / 2, W / 2, r, 0.45 * r, 5, 0.0), closed=True)


# --- Typen ---------------------------------------------------------------------------------

def spec_auto(cfg: Config, L: float, W: float, **_) -> Spec:
    d = Dims(cfg, L, W, max(0.125 * L, 0.0))
    T, web = d.T, d.web
    yh, yr, yt = 0.30 * L, 0.47 * L, 0.29 * L
    out = fillet([(0, d.yb, 4), (L, d.yb, 4), (L, yh - 0.05 * L, 3), (0.93 * L, yh, 6),
                  (0.70 * L, yh + 0.01 * L, 2), (0.58 * L, yr, 6), (0.31 * L, yr, 6),
                  (0.18 * L, yt + 0.02 * L, 2), (0.03 * L, yt, 5), (0, yt - 0.06 * L, 3)])
    sp = Spec("auto", L, d.W_in, out, axles=[0.19 * L, 0.80 * L], axle_y=d.ya, rw=d.rw)
    _check_axles(d, sp.axles)
    roof_at = yr - web - T
    a0, a1 = _h_extent(out, roof_at, T, 0.45 * L)
    xf, xr = _ends(d, 0.955 * L, 0.045 * L)
    sp.members = [
        Member("boden", "h", d.yf, xr + T / 2 + 0.3, xf - T / 2 - 0.3),
        Member("front", "v", xf, d.yb + 1.0, _v_top(out, xf, T, web), 1, _grille),
        Member("heck", "v", xr, d.yb + 1.0, _v_top(out, xr, T, web), 1, _plate),
        Member("dach", "h", roof_at, a0, a1),
    ]
    wy0, wy1 = yh + 0.02 * L + web, roof_at - web
    xm = 0.465 * L
    p = max(2.5, T)
    for x0, x1 in ((0.15 * L, xm - p / 2), (xm + p / 2, 0.75 * L)):
        w = window(out, x0, x1, wy0, wy1, p)
        if w:
            sp.windows.append(w)
    door_bot = d.yf + T + web
    sp.engrave += [([(0.30 * L, door_bot), (0.30 * L, yh), (0.62 * L, yh), (0.64 * L, door_bot)], False),
                   (circle(0.91 * L, yh - 0.04 * L, max(1.5, 0.02 * L), 0.1), True),
                   (rect(0.07 * L, yt - 0.035 * L, 0.025 * L, 0.025 * L), True)]
    sp.extras.append(([(0.53 * L, yh - 1.8), (0.58 * L, yh - 1.8)], False))          # Türgriff
    sp.text_box = (0.46 * L, (door_bot + yh) / 2 - 0.8, 0.28 * L, yh - door_bot - 5.0)
    return sp


def spec_lkw(cfg: Config, L: float, W: float, axles: int = 2, **_) -> Spec:
    d = Dims(cfg, L, W, 0.095 * L if axles < 3 else 0.075 * L)
    T, web = d.T, d.web
    yc, ybox, yfr = 0.36 * L, 0.42 * L, 0.20 * L
    out = fillet([(0, d.yb, 3), (L, d.yb, 3), (L, yfr, 3), (0.975 * L, yc, 6), (0.74 * L, yc, 3),
                  (0.712 * L, yc, 0), (0.712 * L, ybox, 2), (0, ybox, 2)])
    xs = [0.20 * L, 0.84 * L] if axles < 3 else [0.10 * L, 0.28 * L, 0.84 * L]
    sp = Spec("lkw", L, d.W_in, out, axles=xs, axle_y=d.ya, rw=d.rw)
    _check_axles(d, xs)
    cab_roof, box_roof = yc - web - T, ybox - web - T
    xf, xr = _ends(d, 0.96 * L, 0.035 * L)
    sp.members = [
        Member("boden", "h", d.yf, xr + T / 2 + 0.3, xf - T / 2 - 0.3),
        Member("front", "v", xf, d.yb + 1.0, _v_top(out, xf, T, web), 1, _grille),
        Member("heck", "v", xr, d.yb + 1.0, box_roof - 1.0, 1, _planks),
        Member("dach_kabine", "h", cab_roof, 0.712 * L + 1.0, _h_extent(out, cab_roof, T, 0.85 * L)[1]),
        Member("dach_koffer", "h", box_roof, *_h_extent(out, box_roof, T, 0.35 * L)),
    ]
    p = max(2.5, T)
    w = window(out, 0.76 * L, xf - T / 2 - web, yc - 0.13 * L, cab_roof - web, p)
    if w:
        sp.windows.append(w)
    sp.engrave += [([(0.712 * L, d.yf + T + web), (0.712 * L, yc - 1.0)], False),
                   ([(0.80 * L, d.yf + T + web), (0.80 * L, yc - 0.13 * L - 2)], False)]
    sp.text_box = (0.36 * L, (d.yf + T + box_roof) / 2, 0.6 * L, box_roof - d.yf - T - 2 * web - 2)
    return sp


def spec_lok(cfg: Config, L: float, W: float, **_) -> Spec:
    d = Dims(cfg, L, W, 0.085 * L)
    T, web = d.T, d.web
    yfr, ybt, ych, ycr = 0.20 * L, 0.37 * L, 0.50 * L, 0.52 * L
    yfr = max(yfr, d.yf + T + 2 * web + T + 1)
    out = fillet([(0, d.yb, 2), (L, d.yb, 2), (L, yfr, 2), (0.95 * L, yfr, 0), (0.95 * L, ybt, 0.06 * L),
                  (0.87 * L, ybt, 1.5), (0.865 * L, ych - 0.035 * L, 0), (0.89 * L, ych, 1.5),
                  (0.775 * L, ych, 1.5), (0.80 * L, ych - 0.035 * L, 0), (0.795 * L, ybt, 1.5),
                  (0.62 * L, ybt, 2), (0.60 * L, ybt + 0.05 * L, 3), (0.52 * L, ybt + 0.05 * L, 3),
                  (0.50 * L, ybt, 2), (0.30 * L, ybt, 0), (0.30 * L, ycr, 0), (0.32 * L, ycr, 0),
                  (0.32 * L, ycr + 0.035 * L, 1.5), (0, ycr + 0.035 * L, 2)])
    xs = [0.17 * L, 0.42 * L, 0.67 * L]
    sp = Spec("lok", L, d.W_in, out, axles=xs, axle_y=d.ya, rw=d.rw, wheel_style="speichen")
    _check_axles(d, xs)
    cab_roof, boiler = ycr + 0.035 * L - web - T, ybt - web - T
    xf, xr = _ends(d, 0.975 * L, 0.035 * L)
    sp.members = [
        Member("boden", "h", d.yf, xr + T / 2 + 0.3, xf - T / 2 - 0.3),
        Member("puffer", "v", xf, d.yb + 1.0, _v_top(out, xf, T, web), 1, None),
        Member("rauchkammer", "v", 0.925 * L, d.yf + T, boiler - 0.5, 1, _smokebox),
        Member("fuehrerhaus", "v", xr, d.yb + 1.0, cab_roof - 0.5, 1, _plate),
        Member("dach", "h", cab_roof, *_h_extent(out, cab_roof, T, 0.15 * L)),
        Member("kessel", "h", boiler, 0.30 * L + 1.0, _h_extent(out, boiler, T, 0.6 * L)[1]),
    ]
    p = max(2.5, T)
    w = window(out, 0.07 * L, 0.25 * L, ybt - 0.04 * L, cab_roof - web, p)
    if w:
        sp.windows.append(w)
    sp.engrave += [([(0.30 * L, yfr), (0.95 * L, yfr)], False)]
    tb = (0.625 * L, (yfr + boiler) / 2, 0.5 * L, boiler - yfr - 2 * web)
    sp.text_box = tb
    sp.couple, sp.couple_y = ["fuehrerhaus"], d.yf + T + web + 3.0
    sp.engrave += [([(x, yfr + 1.5), (x, boiler - 1.5)], False) for x in (0.36 * L, 0.89 * L)]
    return sp


def spec_schlitten(cfg: Config, L: float, W: float, **_) -> Spec:
    T = cfg.T
    d = Dims(cfg, L, W, 30.0)                   # rw nur Platzhalter – Schlitten hat Kufen
    web = d.web
    rt = max(2 * web, 0.04 * L)                 # Kufenstärke
    Rc = max(0.17 * L, 2.4 * rt)
    C = (0.80 * L, Rc)
    Ri = Rc - rt
    yb, yd, ys, yk = 0.14 * L, 0.36 * L, 0.30 * L, 0.50 * L
    tol = cfg.arc_tolerance
    outer = arc_points(C[0], C[1], Rc, -math.pi / 2, math.radians(70), tol)
    ct = (C[0] + (Rc - rt / 2) * math.cos(math.radians(70)), C[1] + (Rc - rt / 2) * math.sin(math.radians(70)))
    cap = arc_points(ct[0], ct[1], rt / 2, math.radians(70), math.radians(250), tol)[1:-1]
    inner = arc_points(C[0], C[1], Ri, math.radians(70), math.radians(-10), tol)
    pts = [(0.07 * L, 0.0, rt / 2)] + [(x, y, 0) for x, y in outer + cap + inner] + \
          [(0.74 * L, yd, 4), (0.66 * L, ys, 4), (0.25 * L, ys, 4), (0.18 * L, yk, 6), (0.015 * L, yk, 6),
           (0.0, yk - 0.06 * L, 3), (0.025 * L, rt, 2)]
    out = oriented(fillet(pts, tol), True)
    from validator import check_path
    if check_path(out, True, cfg):
        raise ValueError("Schlitten zu klein für diese Materialstärke – länger wählen")
    sp = Spec("schlitten", L, d.W_in, out)
    floor = yb + web
    seat = ys - web - T
    xf = 0.69 * L
    sp.members = [
        Member("boden", "h", floor, _h_extent(out, floor, T, 0.4 * L, 2.0)[0], xf - T / 2 - 0.3, deco=_planks),
        Member("sitz", "h", seat, max(_h_extent(out, seat, T, 0.45 * L)[0], 0.09 * L + T / 2 + 0.5),
               min(_h_extent(out, seat, T, 0.45 * L)[1], xf - T / 2 - 0.5)),
        Member("lehne", "v", 0.09 * L, floor + T, _v_top(out, 0.09 * L, T, web), 1, _stars),
        Member("front", "v", xf, rt + 1.0, _v_top(out, xf, T, web), 1, _stars),
    ]
    if seat - (floor + T) < 2 * web + 2:              # kleiner Schlitten: Boden ist die Sitzfläche
        sp.members = [m for m in sp.members if m.name != "sitz"]
    for x0, x1 in ((0.11 * L, 0.37 * L), (0.43 * L, xf - T / 2 - web - 0.5)):
        w = window(out, x0, x1, rt, yb, 0.0, r=0)
        if w:
            sp.windows.append(fillet([(x, y, 3.0) for x, y in w]))
    sp.text_box = (0.40 * L, (floor + T + seat) / 2, 0.36 * L, seat - floor - T - 2 * web)
    sp.engrave += [(star(0.82 * L, 0.9 * Rc, 0.035 * L, 0.016 * L), True)] if Ri > 0.06 * L else []
    sp.notes.append("Schlitten: Kufen sind Teil der Seitenwände – keine Achsen nötig.")
    return sp


def _train_ends(sp: Spec, d: Dims) -> None:
    sp.couple, sp.couple_y = ["front", "heck"], d.yf + d.T + d.web + 3.0


def _coal(part: Part, length: float, W: float) -> None:
    n = max(3, int(length // 7))
    for i in range(n):
        cx = length * (i + 0.5) / n
        part.add_engrave(circle(cx, W * (0.3 + 0.4 * (i % 2)), min(2.2, length / n * 0.3), 0.1), closed=True)


def spec_tender(cfg: Config, L: float, W: float, **_) -> Spec:
    d = Dims(cfg, L, W, max(0.10 * L, 2 * cfg.T + 1.0))
    T, web = d.T, d.web
    yt = max(0.40 * L, d.yf + 2 * T + 5 * web + 10)
    out = fillet([(0, d.yb, 2), (L, d.yb, 2), (L, yt, 2), (0.80 * L, yt, 0), (0.76 * L, yt + 0.06 * L, 2),
                  (0.24 * L, yt + 0.06 * L, 2), (0.20 * L, yt, 0), (0, yt, 2)])
    xs = [0.24 * L, 0.76 * L]
    sp = Spec("tender", L, d.W_in, out, axles=xs, axle_y=d.ya, rw=d.rw, wheel_style="speichen")
    _check_axles(d, xs)
    xf, xr = _ends(d, 0.96 * L, 0.04 * L)
    top = yt - web - T
    sp.members = [
        Member("boden", "h", d.yf, xr + T / 2 + 0.3, xf - T / 2 - 0.3),
        Member("front", "v", xf, d.yb + 1.0, _v_top(out, xf, T, web), 1, None),
        Member("heck", "v", xr, d.yb + 1.0, _v_top(out, xr, T, web), 1, None),
        Member("kohle", "h", top, *_h_extent(out, top, T, 0.5 * L), deco=_coal),
    ]
    yl = d.yf + T + web
    sp.engrave += [([(0.03 * L, yl), (0.97 * L, yl)], False)]
    sp.text_box = (0.5 * L, (yl + top) / 2, 0.8 * L, top - yl - 2 * web)
    _train_ends(sp, d)
    return sp


def spec_personenwagen(cfg: Config, L: float, W: float, **_) -> Spec:
    d = Dims(cfg, L, W, max(0.075 * L, 2 * cfg.T + 1.0))
    T, web = d.T, d.web
    yw = max(0.37 * L, d.yf + T + 6 * web + 20)
    out = fillet([(0, d.yb, 3), (L, d.yb, 3), (L, yw, 3), (0.96 * L, yw + 0.045 * L, 10),
                  (0.04 * L, yw + 0.045 * L, 10), (0, yw, 3)])
    xs = [0.18 * L, 0.82 * L]
    sp = Spec("personenwagen", L, d.W_in, out, axles=xs, axle_y=d.ya, rw=d.rw, wheel_style="speichen")
    _check_axles(d, xs)
    xf, xr = _ends(d, 0.965 * L, 0.035 * L)
    roof = _h_extent(out, yw - web - T, T, 0.5 * L)
    roof_at = yw - web - T
    sp.members = [
        Member("boden", "h", d.yf, xr + T / 2 + 0.3, xf - T / 2 - 0.3, deco=_planks),
        Member("front", "v", xf, d.yb + 1.0, _v_top(out, xf, T, web), 1, None),
        Member("heck", "v", xr, d.yb + 1.0, _v_top(out, xr, T, web), 1, None),
        Member("dach", "h", roof_at, *roof),
    ]
    p = max(2.5, T)
    wy1 = roof_at - web
    wy0 = wy1 - 0.075 * L
    n = 4
    x0, x1 = max(0.10 * L, xr + T / 2 + web + 0.5), min(0.90 * L, xf - T / 2 - web - 0.5)
    ww = (x1 - x0 - (n - 1) * 0.05 * L) / n
    for i in range(n):
        a = x0 + i * (ww + 0.05 * L)
        w = window(out, a, a + ww, wy0, wy1, p)
        if w:
            sp.windows.append(w)
    yl = d.yf + T + web
    sp.engrave += [([(0.02 * L, wy0 - 2.0), (0.98 * L, wy0 - 2.0)], False)]
    sp.text_box = (0.5 * L, (yl + wy0 - 2.0) / 2, 0.7 * L, wy0 - 2.0 - yl - 2 * web)
    _train_ends(sp, d)
    return sp


def spec_gueterwagen(cfg: Config, L: float, W: float, **_) -> Spec:
    d = Dims(cfg, L, W, max(0.075 * L, 2 * cfg.T + 1.0))
    T, web = d.T, d.web
    yw = max(0.34 * L, d.yf + T + 6 * web + 14)
    out = fillet([(0, d.yb, 2), (L, d.yb, 2), (L, yw, 2), (0.5 * L, yw + 0.03 * L, 0), (0, yw, 2)])
    xs = [0.18 * L, 0.82 * L]
    sp = Spec("gueterwagen", L, d.W_in, out, axles=xs, axle_y=d.ya, rw=d.rw)
    _check_axles(d, xs)
    xf, xr = _ends(d, 0.965 * L, 0.035 * L)
    roof_at = yw - web - T
    sp.members = [
        Member("boden", "h", d.yf, xr + T / 2 + 0.3, xf - T / 2 - 0.3),
        Member("front", "v", xf, d.yb + 1.0, _v_top(out, xf, T, web), 1, _planks),
        Member("heck", "v", xr, d.yb + 1.0, _v_top(out, xr, T, web), 1, _planks),
        Member("dach", "h", roof_at, *_h_extent(out, roof_at, T, 0.5 * L)),
    ]
    yl, yt = d.yf + T + web, roof_at - web
    a, b = 0.58 * L, 0.88 * L
    sp.engrave += [(rect(a, yl, b - a, yt - yl), True), ([(a, yl), (b, yt)], False), ([(a, yt), (b, yl)], False),
                   ([(a - 0.03 * L, yt + 1.2), (b + 0.03 * L, yt + 1.2)], False)]
    sp.text_box = (0.30 * L, (yl + yt) / 2, 0.44 * L, yt - yl - 2 * web)
    _train_ends(sp, d)
    return sp


def spec_bus(cfg: Config, L: float, W: float, **_) -> Spec:
    d = Dims(cfg, L, W, 0.08 * L)
    T, web = d.T, d.web
    yt = max(0.36 * L, d.yf + 2 * T + 7 * web + 13 + 0.10 * L)
    out = fillet([(0, d.yb, 4), (L, d.yb, 4), (L, 0.75 * yt, 4), (0.985 * L, yt, 8), (0, yt, 6)])
    xs = [0.18 * L, 0.78 * L]
    sp = Spec("bus", L, d.W_in, out, axles=xs, axle_y=d.ya, rw=d.rw)
    _check_axles(d, xs)
    xf, xr = _ends(d, 0.97 * L, 0.03 * L)
    roof_at = yt - web - T
    sp.members = [
        Member("boden", "h", d.yf, xr + T / 2 + 0.3, xf - T / 2 - 0.3),
        Member("front", "v", xf, d.yb + 1.0, _v_top(out, xf, T, web), 1, _grille),
        Member("heck", "v", xr, d.yb + 1.0, _v_top(out, xr, T, web), 1, _plate),
        Member("dach", "h", roof_at, *_h_extent(out, roof_at, T, 0.5 * L)),
    ]
    p = max(2.5, T)
    wy1 = roof_at - web
    wy0 = wy1 - 0.10 * L
    n = 5
    x0, x1 = max(0.05 * L, xr + T / 2 + web + 0.5), 0.80 * L
    gap = max(p, 0.02 * L)
    ww = (x1 - x0 - (n - 1) * gap) / n
    for i in range(n):
        a = x0 + i * (ww + gap)
        w = window(out, a, a + ww, wy0, wy1, p)
        if w:
            sp.windows.append(w)
    w = window(out, 0.86 * L, xf - T / 2 - web, wy0, wy1, p)
    if w:
        sp.windows.append(w)
    yl = d.yf + T + web
    sp.engrave += [(rect(0.81 * L, yl, 0.045 * L, wy1 - yl), True),
                   ([(0.02 * L, wy0 - 2.0), (0.80 * L, wy0 - 2.0)], False)]
    sp.text_box = (0.42 * L, (yl + wy0 - 2.0) / 2, 0.7 * L, wy0 - 2.0 - yl - 2 * web)
    return sp


def spec_traktor(cfg: Config, L: float, W: float, **_) -> Spec:
    R, r = 0.24 * L, 0.14 * L                          # Hinter- und Vorderrad
    d = Dims(cfg, L, W, r)
    T, web = d.T, d.web
    xa = [0.26 * L, 0.80 * L]
    yh = max(0.33 * L, R + d.rb + web + 2, d.yf + 2 * T + 5 * web + 10)
    yc = max(0.66 * L, yh + 0.2 * L)
    out = fillet([(0, d.yb, 3), (L, d.yb, 3), (L, yh - 0.03 * L, 4), (0.97 * L, yh, 3), (0.72 * L, yh, 0),
                  (0.72 * L, yh + 0.13 * L, 1), (0.68 * L, yh + 0.13 * L, 1), (0.68 * L, yh, 0),
                  (0.50 * L, yh, 2), (0.48 * L, yc, 3), (0.06 * L, yc, 3), (0.04 * L, 0.42 * L, 2),
                  (0, 0.40 * L, 2)])
    sp = Spec("traktor", L, d.W_in, out, axles=xa, axle_y=d.ya, rw=r, radii=[R, r])
    if xa[1] - xa[0] < R + r + 3 or xa[0] < 0.6 * R:
        raise ValueError("Räder zu groß für den Traktor")
    for k, x in enumerate(xa):                        # Lagerbohrung braucht Fleisch ringsum
        y = sp.axle_at(k)[0]
        if not (d.yb + d.rb + web <= y and top_y(out, x) - d.rb - web >= y):
            raise ValueError("Traktor zu klein für diese Materialstärke")
    xf, xr = _ends(d, 0.97 * L, 0.05 * L)
    roof_at = yc - web - T
    hood_at = yh - web - T
    sp.members = [
        Member("boden", "h", d.yf, max(xr + T / 2 + 0.3, xa[0] + d.rb + web + 0.5), xf - T / 2 - 0.3),
        Member("front", "v", xf, d.yb + 1.0, _v_top(out, xf, T, web), 1, _grille),
        Member("heck", "v", xr, d.yb + 1.0, _v_top(out, xr, T, web), 1, _plate),
        Member("haube", "h", hood_at, 0.50 * L + 1.0, _h_extent(out, hood_at, T, 0.85 * L)[1]),
        Member("dach", "h", roof_at, *_h_extent(out, roof_at, T, 0.27 * L)),
    ]
    if hood_at < d.yf + T + 2 * web:                 # kleiner Traktor: Haube trägt sich selbst
        sp.members = [m for m in sp.members if m.name != "haube"]
    p = max(2.5, T)
    w = window(out, 0.12 * L, 0.44 * L, R + d.rb + web + 2 * p, roof_at - web, p)
    if w:
        sp.windows.append(w)
    sp.engrave += [([(x, yh - 0.04 * L), (x, yh - 0.14 * L)], False) for x in (0.60 * L, 0.64 * L, 0.88 * L)]
    sp.text_box = (0.74 * L, (d.yf + T + hood_at) / 2, 0.32 * L, hood_at - d.yf - T - 2 * web)
    sp.notes.append("Traktor: große Räder hinten, kleine vorne – Achsen passend einstecken.")
    return sp


SPECS = {"auto": spec_auto, "lkw": spec_lkw, "lok": spec_lok, "schlitten": spec_schlitten, "tender": spec_tender,
         "personenwagen": spec_personenwagen, "gueterwagen": spec_gueterwagen, "bus": spec_bus,
         "traktor": spec_traktor}


# ---------------------------------------------------------------------------
# Bauteile erzeugen
# ---------------------------------------------------------------------------

def _member_part(cfg: Config, m: Member, W_in: float) -> Tuple[Part, List[float], float]:
    T = cfg.T
    length = m.a1 - m.a0
    if length < cfg.min_tab_width + 3.0:
        raise ValueError(f"Querteil {m.name} zu kurz ({length:.1f} mm)")
    count = m.count or (1 if length < 50 else (2 if length < 130 else 3))
    centers, tw = tab_centers(length, cfg, count, inset=min(4.0, length * 0.1))
    tw = min(tw, length / count - 2.0)
    if tw < cfg.min_tab_width:
        raise ValueError(f"Querteil {m.name}: zu wenig Platz für Tabs")
    segs = tab_segments(length, centers, tw, T)
    rev = [length - c for c in centers]
    segs_top = tab_segments(length, sorted(rev), tw, T)
    p0, p1, p2, p3 = (0.0, 0.0), (length, 0.0), (length, W_in), (0.0, W_in)
    outline = profile_edge(p0, p1, segs) + [p1] + profile_edge(p2, p3, segs_top)
    outline = clean(outline[:1] + outline[1:] + [p3])
    feats = tab_features("l", p0, p1, centers, tw, T, lambda t: m.a0 + t)
    top = tab_features("r", p2, p3, rev, tw, T, lambda t: m.a0 + length - t)
    part = Part(m.name, outline, features=feats + top)
    if m.deco:
        m.deco(part, length, W_in)
    return part, [m.a0 + c for c in centers], tw


def _side(cfg: Config, sp: Spec, name: str, mirror: bool, text: str,
          slots: List[Tuple[str, Member, float, float]], look: Optional[dict] = None) -> Part:
    look = look or {}
    T = cfg.T
    L = sp.L
    fx = (lambda pts: mirror_x(pts, L / 2)) if mirror else (lambda pts: list(pts))
    part = Part(name, fx(sp.outline))
    for w in sp.windows:
        if cfg.openings == "cut":
            part.add_hole(fx(w))
        else:
            part.add_engrave(fx(w), closed=True)
    for fid, m, c, tw in slots:
        if m.orient == "h":
            x, y, w, h, along = c - tw / 2, m.at, tw, T, True
        else:
            x, y, w, h, along = m.at - T / 2, c - tw / 2, T, tw, False
        if mirror:
            x = L - x - w
        feat, hole = slot_feature(fid, x, y, w, h, along, c)
        part.holes.append(hole)
        part.features.append(feat)
    for k, xa in enumerate(sp.axles):
        cx = L - xa if mirror else xa
        rb = (T * math.sqrt(2) + AXLE_PLAY) / 2
        hole = circle(cx, sp.axle_at(k)[0], rb, cfg.arc_tolerance / 2, ccw=False)
        part.holes.append(hole)
        part.features.append(JointFeature(f"lager{k}", "bore_round", 2 * rb, T, pos=xa, points=list(hole)))
    for pts, closed in sp.engrave:                    # Zierlinien nur, wo sie frei liegen
        if _clear(fx(pts), closed, part, 0.6):
            part.add_engrave(fx(pts), closed)
    if text and sp.text_box:
        _side_text(cfg, sp, part, text, mirror, look)
    for pts, closed in sp.extras:
        q = fx(pts)
        if _clear(q, closed, part, 0.6) and all(min_distance(q, e.points, 0.6, closed, e.closed) >= 0.6
                                                for e in part.engrave):
            part.add_engrave(q, closed)
    if look.get("zierlinie", "keine") != "keine":
        size = max(2.2, min(3.5, 0.03 * L))
        ins = inset_polygon(part.outline, max(1.4, 0.012 * L))
        if polygon_ok(ins):
            cv = dk.Canvas(part, margin=0.6, hole_margin=1.0, seed=7)
            cv.block_strokes(part.engrave, 0.9)
            paths = dk.top_runs(ins) if look["zierlinie"] == "eiszapfen" else [ins + [ins[0]]]
            for k, path in enumerate(paths):
                dk.styled_line(cv, path, look["zierlinie"], size, side=+1, seed=7 + k)
    return part


def _side_text(cfg: Config, sp: Spec, part: Part, text: str, mirror: bool, look: dict) -> None:
    """Aufschrift (optional mit Schild-Rahmen) in die Textfläche der Seitenwand."""
    L = sp.L
    cx, cy, w, h = sp.text_box
    cx = L - cx if mirror else cx
    style, case, form = look.get("schrift", "normal"), look.get("schreibweise", "gross"), look.get("textrahmen", "ohne")
    if form != "ohne":
        cv = dk.Canvas(part, margin=1.0, seed=3)
        cv.block_strokes(part.engrave, 0.6)
        cands = dk.free_rects(cv, cx, cy, [g * h for g in (2.0, 1.6, 1.3, 1.0, 0.8)],
                              [0.0, 0.12 * h, -0.12 * h, 0.25 * h, -0.25 * h], max_w=1.25 * w)
        cands.append((cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2))
        if dk.sign(cv, text, form, cands, style, case, min_h=2.5, max_cap=0.12 * L, anchor="mitte",
                   tol=cfg.arc_tolerance) is None:
            raise ValueError(f"Aufschrift {text!r} passt mit Rahmen „{form}“ nicht auf die Seitenwand – "
                             f"kürzer fassen, ohne Rahmen oder Fahrzeug größer machen")
        return
    for f in (1.0, 0.9, 0.8, 0.7, 0.6, 0.5):
        try:
            strokes, _ = fit_text(text, cx, cy, w * f, h * f, min_h=2.5, max_cap=0.12 * L, style=style, case=case)
        except ValueError:
            break
        if all(_clear(st, False, part, 0.8) and
               all(min_distance(st, e.points, 0.5, False, e.closed) >= 0.5 for e in part.engrave)
               for st in strokes):
            for st in strokes:
                part.add_engrave(st)
            return
    raise ValueError(f"Aufschrift {text!r} passt nicht auf die Seitenwand (min. 2.5 mm Schrifthöhe) – "
                     f"kürzer fassen oder Fahrzeug größer machen")


def _clear(pts: Sequence[Point], closed: bool, part: Part, margin: float) -> bool:
    """Gravur liegt ganz in der Kontur und hält Abstand zu Rand und Durchbrüchen."""
    if not all(point_in_polygon(p, part.outline) for p in pts):
        return False
    if min_distance(pts, part.outline, margin, closed, True) < margin:
        return False
    for h in part.holes:
        if point_in_polygon(pts[0], h) or min_distance(pts, h, margin, closed, True) < margin:
            return False
    return True


def _wheel(cfg: Config, name: str, rw: float, xa: float, style: str) -> Part:
    T = cfg.T
    tol = cfg.arc_tolerance
    part = Part(name, circle(0.0, 0.0, rw, tol))
    hole = rect(-T / 2, -T / 2, T, T, ccw=False)
    part.holes.append(hole)
    part.features.append(JointFeature("nabe", "bore_square", T, T, pos=xa, points=list(hole)))
    web = max(cfg.min_web, 2.0, 0.8 * T)
    r_hub = T / math.sqrt(2) + web + 1.0
    tire = max(2.2, 0.16 * rw)
    r_rim = rw - tire
    if style == "speichen" and r_rim - r_hub >= 3.0:
        s = web
        n = 6
        for k in range(n):
            a = 2 * math.pi * k / n + math.pi / 2
            b = a + 2 * math.pi / n
            ao, ai = math.asin(s / 2 / r_rim), math.asin(s / 2 / r_hub)
            if (b - ai) - (a + ai) < 0.15:
                break
            pts = arc_points(0, 0, r_rim, a + ao, b - ao, tol) + arc_points(0, 0, r_hub, b - ai, a + ai, tol)
            part.add_hole(pts)
        part.add_engrave(circle(0, 0, rw - tire / 2, 0.1), closed=True)
    else:
        part.add_engrave(circle(0, 0, r_rim, 0.1), closed=True)
        if r_rim - r_hub > 2.0:
            part.add_engrave(circle(0, 0, r_hub, 0.1), closed=True)
            rr = (r_hub + r_rim) / 2
            for k in range(5):
                a = 2 * math.pi * k / 5
                part.add_engrave(circle(rr * math.cos(a), rr * math.sin(a), 0.6, 0.05), closed=True)
    return part


def _axle(cfg: Config, k: int, xa: float, W_in: float) -> Part:
    T = cfg.T
    ov, g = 0.5, WHEEL_GAP
    La = 4 * T + 2 * g + W_in + 2 * ov
    part = Part(f"achse_{k}", rect(0, 0, La, T))
    z = [ov, ov + T, ov + T + g, ov + 2 * T + g]
    zr = [La - z[3], La - z[2], La - z[1], La - z[0]]

    def shaft(fid, z0, z1):
        return JointFeature(fid, "shaft", T, T, pos=xa, span=(z0, z1),
                            points=[(z0, 0.0), (z1, 0.0), (z1, T), (z0, T)])
    part.features += [shaft("rad_l", z[0], z[1]), shaft("lager_l", z[2], z[3]),
                      shaft("lager_r", zr[0], zr[1]), shaft("rad_r", zr[2], zr[3])]
    return part


def build(cfg: Config, name: Optional[str] = None, vehicle: str = "auto", length: Optional[float] = None,
          width: Optional[float] = None, height: Optional[float] = None, depth: Optional[float] = None,
          axles: int = 2, text: str = "", schrift: str = "normal", schreibweise: str = "gross",
          textrahmen: str = "ohne", zierlinie: str = "keine", kupplung: bool = True) -> Assembly:
    """Steckfahrzeug. length = Gesamtlänge, width = Gesamtbreite der Karosserie (ohne Räder).
    Gestaltung: schrift/schreibweise der Aufschrift, textrahmen (Schildform oder „ohne“),
    zierlinie (Linienstil entlang der Seitenkontur oder „keine“)."""
    if vehicle not in SPECS:
        raise ValueError(f"Unbekanntes Fahrzeug {vehicle!r} – wähle {', '.join(VEHICLES)}")
    if schrift not in STYLES:
        raise ValueError(f"Schrift {schrift!r} unbekannt – erlaubt: {', '.join(STYLES)}")
    if schreibweise not in CASES:
        raise ValueError(f"Schreibweise {schreibweise!r} unbekannt – erlaubt: {', '.join(CASES)}")
    dk.check_choice("Textrahmen", textrahmen, dk.SIGNS)
    dk.check_choice("Zierlinie", zierlinie, dk.TRIMS)
    bad = unsupported(text)
    if bad:
        raise ValueError(f"Aufschrift: Zeichen {''.join(bad)!r} gibt es in der Gravurschrift nicht")
    look = dict(schrift=schrift, schreibweise=schreibweise, textrahmen=textrahmen, zierlinie=zierlinie)
    dflt = DEFAULTS[vehicle]
    L = cfg.s(length or dflt["length"])
    W = cfg.s(width or depth or dflt["width"])
    if L < MIN_LENGTH[vehicle]:
        raise ValueError(f"{vehicle} zu klein: min. {MIN_LENGTH[vehicle]:.0f} mm Länge")
    if W > 0.8 * L:
        raise ValueError("Fahrzeug breiter als 80 % der Länge – bitte schmaler wählen")
    sp = SPECS[vehicle](cfg, L, W, axles=axles)
    _resolve(sp.members, cfg.T)
    asm = Assembly(name or vehicle, params=dict(vehicle=vehicle, length=L, width=W, axles=len(sp.axles),
                                                text=text))
    asm.params.update({k: v for k, v in look.items()
                       if v != dict(schrift="normal", schreibweise="gross", textrahmen="ohne", zierlinie="keine")[k]})
    slots: List[Tuple[str, Member, float, float]] = []
    for m in sp.members:
        if m.a1 - m.a0 <= 0:
            raise ValueError(f"Querteil {m.name}: kein Platz")
        part, centers, tw = _member_part(cfg, m, sp.W_in)
        if kupplung and m.name in sp.couple:
            u = sp.couple_y - m.a0
            rc = max(1.75, 0.6 * cfg.T)
            if not (rc + 2.0 <= u <= m.a1 - m.a0 - rc - 2.0):
                raise ValueError(f"{vehicle}: kein Platz für das Kupplungsloch")
            part.add_hole(circle(u, sp.W_in / 2, rc, cfg.arc_tolerance / 2, ccw=False))
        asm.parts.append(part)
        for i, c in enumerate(centers):
            slots.append((f"{m.name}_{i}", m, c, tw))
            asm.connect(f"{m.name}:l{i}", f"seite_l:{m.name}_{i}")
            asm.connect(f"{m.name}:r{i}", f"seite_r:{m.name}_{i}")
    asm.parts.insert(0, _side(cfg, sp, "seite_r", True, text, slots, look))
    asm.parts.insert(0, _side(cfg, sp, "seite_l", False, text, slots, look))
    for k, xa in enumerate(sp.axles):
        asm.parts.append(_axle(cfg, k, xa, sp.W_in))
        for side in ("l", "r"):
            asm.parts.append(_wheel(cfg, f"rad_{k}{side}", sp.axle_at(k)[1], xa, sp.wheel_style))
            asm.connect(f"achse_{k}:rad_{side}", f"rad_{k}{side}:nabe")
            asm.connect(f"achse_{k}:lager_{side}", f"seite_{side}:lager{k}")
    asm.notes += sp.notes
    if kupplung and sp.couple:
        asm.notes.append(f"{vehicle.capitalize()}: Kupplungslöcher in Front/Heck – Wagen mit einer Draht- oder "
                         "Schnurschlaufe verbinden (z. B. aufgebogene Büroklammer).")
    asm.notes.append(f"{vehicle.capitalize()}: Querteile in die linke Seitenwand stecken, rechte Seitenwand aufsetzen.")
    if sp.axles:
        asm.notes.append("Achsen durch die Lagerbohrungen schieben, Räder auf den Vierkant pressen "
                         f"(≈{WHEEL_GAP} mm Luft zur Seitenwand lassen, bei Bedarf einen Tropfen Leim).")
    return asm
