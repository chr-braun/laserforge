"""
Zierschlitten – 3D-Steckschlitten als Tischdeko oder Geschenkhalter.

Zwei Seitenwände mit geschwungenen Schnörkelkufen, Ringen zwischen den Streben und durchbrochenen
Ranken (oder Herzen/Sternen), dazu Boden, Sitzbank und Rückenlehne mit Zierkrone. Alles steckt über
geprüfte Zapfen und Schlitze zusammen; auf Wunsch steht ein Name auf der Lehne.
"""
from __future__ import annotations

import math
import os
import sys
from typing import List, Tuple

from steckwerk import Assembly, Part, inset_polygon, oriented, rect
from pakete import bibliothek, num, sel, txt

_here = os.path.dirname(os.path.abspath(__file__))


def _sub(name: str):
    import importlib.util
    path = os.path.join(_here, name + ".py")
    key = "swpaket_weihnacht_" + name
    mod = sys.modules.get(key)
    if mod is None or getattr(mod, "__file__", None) != path:
        spec = importlib.util.spec_from_file_location(key, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[key] = mod
        spec.loader.exec_module(mod)
    return mod


W = bibliothek("verzierungen").W
E, K = W.E, W.K
Figur = K.Figur

VERZIERUNG = [("ranken", "Ranken und Spiralen"), ("herzen", "Herzen"), ("sterne", "Sterne und Flocken")]

INFO = dict(
    label="Zierschlitten",
    group="Weihnachtsdeko",
    desc="Schlitten zum Zusammenstecken mit Schnörkelkufen und durchbrochenen Seitenwänden – als Tischdeko "
         "oder Geschenkhalter, auf Wunsch mit Namen auf der Lehne.",
    params=[
        num("laenge", "Länge", 220, 140, 360),
        num("breite", "Innenbreite", 100, 50, 220, help="Platz zwischen den Seitenwänden"),
        sel("verzierung", "Seitenwände", VERZIERUNG, "ranken"),
        txt("text", "Name auf der Lehne", "", maxlen=24, help="optional, wird eingraviert",
            section="Schrift und Beschriftung"),
    ],
)

UEBERSETZUNG = {"en": {
    "Zierschlitten": "Decorative sleigh", "Weihnachtsdeko": "Christmas decor",
    "Schlitten zum Zusammenstecken mit Schnörkelkufen und durchbrochenen Seitenwänden – als Tischdeko "
    "oder Geschenkhalter, auf Wunsch mit Namen auf der Lehne.":
        "Slot-together sleigh with scrolled runners and openwork side panels – as table decoration or gift "
        "holder, optionally with a name on the backrest.",
    "Länge": "Length", "Innenbreite": "Inner width", "Platz zwischen den Seitenwänden": "space between the side panels",
    "Seitenwände": "Side panels", "Ranken und Spiralen": "Scrolls and spirals", "Herzen": "Hearts",
    "Sterne und Flocken": "Stars and flakes", "Name auf der Lehne": "Name on the backrest",
    "optional, wird eingraviert": "optional, will be engraved", "Schrift und Beschriftung": "Font and lettering",
    "Zusammenbau: Boden, Sitzbank und Lehne in eine Seitenwand stecken, dann die zweite Seitenwand aufsetzen. "
    "Die Zapfen sitzen bündig; bei Bedarf mit einem Tropfen Leim sichern.":
        "Assembly: push floor, seat and backrest into one side panel, then fit the second panel. The tabs sit "
        "flush; secure with a drop of glue if needed.",
    "Beide Seitenwände sind spiegelbildlich, damit die Gravur außen liegt.":
        "The two side panels are mirror images so the engraving faces outwards.",
    "Tipp: Mit Moos, Tannengrün und kleinen Geschenken füllen – oder als Brotkorb/Plätzchenschale nutzen.":
        "Tip: Fill with moss, fir sprigs and small presents – or use it as a bread or cookie basket.",
}}


# --------------------------------------------------------------------------------------------------
# Hilfen
# --------------------------------------------------------------------------------------------------

def _spirale(c, r0, r1, a0, turns, ccw=True, n=60):
    sg = 1 if ccw else -1
    out = []
    for i in range(n + 1):
        t = i / n
        a = a0 + sg * 2 * math.pi * turns * t
        r = r0 + (r1 - r0) * t
        out.append((c[0] + r * math.cos(a), c[1] + r * math.sin(a)))
    return out


def _quer_y(poly, x):
    ys = []
    n = len(poly)
    for i in range(n):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % n]
        if (x1 <= x < x2) or (x2 <= x < x1):
            ys.append(y1 + (x - x1) * (y2 - y1) / (x2 - x1))
    return (min(ys), max(ys)) if len(ys) >= 2 else None


class Geo:
    """Maße des Schlittens (Seitenansicht: x nach vorn, y nach oben, Einheit mm)."""

    def __init__(self, L: float, B: float, T: float, wm: float):
        self.L, self.B, self.T, self.wm = L, B, T, wm
        u = L
        self.rw = max(0.034 * u, 2.2 * wm, 1.4 * T)                  # Kufenbreite
        self.yb = max(0.10 * u, self.rw + 2.6 * wm + 6)               # Unterkante Wagenkasten
        self.band = T + 2 * (wm + 1.6)                                 # Holme, in denen die Schlitze sitzen
        self.fw = max(0.028 * u, 1.8 * wm)                             # Rahmenbreite
        yb = self.yb
        top = yb + max(0.20 * u, 2 * self.band + 4 * self.fw + 16)        # Oberkante Mitte
        self.body = oriented(K.spline([(-0.40 * u, yb), (0.20 * u, yb), (0.27 * u, yb + 0.03 * u),
                                       (0.30 * u, yb + 0.10 * u), (0.335 * u, top + 0.04 * u),
                                       (0.30 * u, top + 0.045 * u), (0.20 * u, top + 0.0 * u),
                                       (0.04 * u, top - 0.015 * u), (-0.14 * u, top + 0.0 * u),
                                       (-0.26 * u, top + 0.05 * u), (-0.33 * u, top + 0.12 * u),
                                       (-0.40 * u, top + 0.15 * u), (-0.415 * u, top + 0.09 * u),
                                       (-0.405 * u, yb + 0.06 * u)],
                                      closed=True, n=10), True)
        self.top = top
        self.y_floor = yb + (self.band - T) / 2                        # Unterseite Boden
        self.x_post = -0.40 * u + self.fw * 0.3 + self.band / 2        # Mitte der Lehne
        self.x_f0 = self.x_post + T / 2                                # Boden beginnt hinter der Lehne
        self.x_f1 = 0.21 * u                                           # … und endet vorn
        self.y_seat = yb + 0.45 * (top - yb)                           # Unterseite Sitz
        self.x_s1 = -0.12 * u                                          # Sitz-Vorderkante
        self.y_post0 = self.y_floor + T                                # Lehne steht auf dem Boden
        ys = [p[1] for p in self.body if p[0] < -0.36 * u]
        self.y_post1 = max(ys) - self.fw                               # Lehne bis unter die Rolle
        self.tw = max(T + 0.6 + 0.2, min(0.055 * u, 3.2 * T))         # Zapfenbreite

    def boden_x(self):
        n = 3 if self.x_f1 - self.x_f0 > 110 else 2
        Lf = self.x_f1 - self.x_f0
        return [self.x_f0 + Lf * (k + 0.5) / n for k in range(n)]

    def sitz_x(self):
        Ls = self.x_s1 - self.x_f0
        return [self.x_f0 + Ls * f for f in ((0.5,) if Ls < 4 * self.tw else (0.27, 0.73))]

    def lehne_y(self):
        Hp = self.y_post1 - self.y_post0
        return [self.y_post0 + Hp * f for f in (0.22, 0.62)]


# --------------------------------------------------------------------------------------------------
# Seitenwand
# --------------------------------------------------------------------------------------------------

def _kufe(g: Geo) -> Figur:
    u, rw = g.L, g.rw
    f = Figur()
    y0 = rw / 2
    cf = (0.385 * u, g.yb + 0.085 * u)                 # vordere Schnecke
    Rf = 0.075 * u
    start_f = (cf[0] + Rf, cf[1])
    main = K.chain([(-0.455 * u, y0), (0.30 * u, y0)],
                   K.bez3((0.30 * u, y0), (0.43 * u, y0), (cf[0] + Rf + 0.01 * u, cf[1] - 0.06 * u), start_f, 16))
    f.line(main, rw)
    sp = _spirale(cf, Rf, 0.22 * Rf, 0.0, 1.15, ccw=True, n=70)
    f.add(K.stroke(sp, rw, max(0.6 * rw, g.wm * 1.2), "rund"))
    f.add(K.circle(sp[-1][0], sp[-1][1], max(0.55 * rw, g.wm), 20))
    # hintere Schnecke
    Rr = 0.042 * u
    cr = (-0.455 * u, y0 + Rr)
    sp2 = _spirale(cr, Rr, 0.3 * Rr, -math.pi / 2, 1.0, ccw=False, n=50)
    f.add(K.stroke(sp2, rw * 0.95, max(0.6 * rw, g.wm * 1.2), "rund"))
    f.add(K.circle(sp2[-1][0], sp2[-1][1], max(0.5 * rw, g.wm), 20))
    # Streben mit Fuß und Ringe dazwischen
    xs = [-0.34 * u, -0.07 * u, 0.17 * u]
    sw = max(0.75 * rw, 1.4 * g.wm)
    for x in xs:
        f.add(K.stroke([(x, y0), (x, g.yb + 2)], sw))
        f.add([(x - 1.6 * sw, y0), (x + 1.6 * sw, y0), (x + 0.5 * sw, y0 + 2.2 * sw), (x - 0.5 * sw, y0 + 2.2 * sw)])
        f.add([(x - 1.4 * sw, g.yb + 1), (x + 1.4 * sw, g.yb + 1), (x + 0.5 * sw, g.yb - 1.8 * sw),
               (x - 0.5 * sw, g.yb - 1.8 * sw)])
    gap = g.yb - rw
    rr = gap / 2 + 0.2
    for a, b in zip(xs, xs[1:]):
        n = max(1, int((b - a - 2 * sw) / (2.3 * rr)))
        for k in range(n):
            x = a + (b - a) * (k + 0.5) / n
            f.add(K.circle(x, rw + gap / 2, rr, 48))
            f.cut(K.circle(x, rw + gap / 2, rr - max(g.wm * 1.15, 0.12 * gap), 48))
    return f


def _ranken(g: Geo, feld, seed: int) -> Figur:
    """Rankenband im Feld: eine Kette aus S-Voluten, die oben und unten am Rahmen anliegen."""
    f = Figur()
    ws = g.wm * 1.15
    xs = [p[0] for p in feld]
    x0, x1 = min(xs) + 1.0, max(xs) - 1.0

    def band(x):
        q = _quer_y(feld, x)
        return q
    qm = band((x0 + x1) / 2)
    Hm = (qm[1] - qm[0]) if qm else 0.0
    x = x0
    while x < x1 and band(x) and band(x)[1] - band(x)[0] > 1.3 * Hm:
        x += 1.0
    if x - x0 > 6 * ws:                                    # hoher Bereich an der Lehne: große Volute
        zx0, zx1 = x0, x
        q0 = band(zx0 + 0.5 * (zx1 - zx0))
        zh = q0[1] - q0[0]
        R = 0.42 * min(zx1 - zx0, zh)
        c = ((zx0 + zx1) / 2, q0[0] + 0.5 * zh)
        sp = _spirale(c, R, 0.25 * R, -math.pi / 2, 1.5, ccw=True, n=90)
        f.add(K.stroke(sp, ws * 1.15, ws * 0.9, "rund"))
        f.add(K.circle(sp[-1][0], sp[-1][1], ws * 0.95, 14))
        f.add(K.stroke([(c[0], q0[0] - 1.0), sp[0]], ws * 1.15, ws * 1.15, "rund"))
    k = 0
    while True:
        q = band(min(max(x, x0), x1))
        if q is None:
            break
        lo, hi = q
        Hf = hi - lo
        d = 0.17 * Hf
        R = 0.33 * Hf + 0.3
        if R < 2.2 * ws:
            break
        cx = x + 1.9 * R
        if cx + 1.9 * R > x1 + 0.3 * R:
            break
        q2 = band(cx)
        if q2 is None:
            break
        lo, hi = q2
        Hf = hi - lo
        d = 0.17 * Hf
        R = 0.33 * Hf + 0.3
        mid = (lo + hi) / 2
        cA = (cx - 0.9 * R, mid + d)
        cB = (cx + 0.9 * R, mid - d)
        qa, qb = band(cA[0]), band(cB[0])
        if qa and qb:                                      # oben und unten am Rahmen anliegen
            cA = (cA[0], min(qa[1] - R + 0.5, mid + 0.45 * Hf))
            cB = (cB[0], qb[0] + R - 0.5)
        spA = _spirale(cA, R, 0.28 * R, 0.0, 1.15, ccw=True, n=60)
        spB = _spirale(cB, R, 0.28 * R, math.pi, 1.15, ccw=True, n=60)
        f.add(K.stroke(spA, ws * 1.1, ws * 0.9, "rund"), K.stroke(spB, ws * 1.1, ws * 0.9, "rund"))
        f.add(K.stroke([spA[0], spB[0]], ws * 1.1, ws * 1.1, "rund"))
        f.add(K.circle(spA[-1][0], spA[-1][1], ws * 0.95, 14), K.circle(spB[-1][0], spB[-1][1], ws * 0.95, 14))
        x = cx + 1.85 * R
        k += 1
    # Rest bis zum Rand mit einer waagrechten Ranke verbinden
    return f


def _seitenwand(g: Geo, name: str, verzierung: str, cfg, notes, spiegeln: bool) -> Part:
    u, T = g.L, g.T
    fig = Figur()
    fig.merge(_kufe(g))
    fig.add(g.body)
    # Rolle oben an der Lehne
    top_back = max(g.body, key=lambda p: p[1] - 0.5 * abs(p[0] + 0.40 * u))
    fig.add(K.circle(-0.405 * u, top_back[1] - 0.02 * u, 0.035 * u, 30))
    feld = inset_polygon(g.body, g.fw)
    xs_band = (-0.40 * u, g.x_post + g.band / 2)
    baender = [K.rect(-0.45 * u, g.yb - 1, 0.9 * u, g.band + 1),                     # Bodenholm
               K.rect(xs_band[0] - 2, g.yb, xs_band[1] - xs_band[0] + 2, g.y_post1 - g.yb + g.fw),   # Lehnenpfosten
               K.rect(xs_band[0], g.y_seat - g.band / 2 + T / 2, 0.8 * u, g.band)]  # Sitzholm (Brüstung)
    # Schlitze und Polster
    slots: List[Tuple[str, float, float, float, float, float]] = []
    for k, x in enumerate(g.boden_x()):
        slots.append((f"boden{k}", x, g.y_floor + T / 2, g.tw, 0.0, 100 + k))
    for k, x in enumerate(g.sitz_x()):
        slots.append((f"sitz{k}", x, g.y_seat + T / 2, g.tw, 0.0, 200 + k))
    for k, y in enumerate(g.lehne_y()):
        slots.append((f"lehne{k}", g.x_post, y, g.tw, math.pi / 2, 300 + k))
    pads = [W.schlitz_polster(x, y, l, T, g.wm + 1.0, a) for _, x, y, l, a, _ in slots]
    fl = []
    if len(feld) >= 3:
        if verzierung == "ranken":
            fl = [feld]
        lw_box = None
    x0 = min(p[0] for p in feld) if feld else 0
    # Durchbruch: Feld minus Holme; darin Muster
    xs = [p[0] for p in g.body] + [-0.48 * u, 0.47 * u]
    ys = [p[1] for p in g.body] + [0.0]
    lw = E.Leinwand((min(xs) - 4, -4, max(xs) + 4, max(ys) + 6), W.px_fuer(u))
    mat = lw.figur(fig)
    if len(feld) >= 3:
        offen = E._andnot(lw.flaechen([feld]), lw.flaechen(baender))
        if verzierung == "ranken":
            mat = E._andnot(mat, offen)
            orn = Figur()
            y_lo = g.yb + g.band
            y_s0 = g.y_seat - g.band / 2 + T / 2
            x_l = g.x_post + g.band / 2
            for k, (ya, yb_) in enumerate(((y_lo, y_s0), (y_s0 + g.band, 1e9))):
                seg = _clip_poly(feld, x_l, 1e9, ya, yb_)
                if seg:
                    mat = mat.union(E._and(lw.figur(_ranken(g, seg, cfg.seed + k)), offen))
        else:
            # geschlossene Wand mit Reihen ausgeschnittener Herzen/Sterne in beiden Feldern
            from models._deko import heart
            loecher = []
            y_lo = g.yb + g.band
            y_s0 = g.y_seat - g.band / 2 + T / 2
            x_l = g.x_post + g.band / 2
            gross = max(9.0, 0.06 * u)
            for k, (ya, yb_) in enumerate(((y_lo, y_s0), (y_s0 + g.band, 1e9))):
                zone = _clip_poly(feld, x_l, 1e9, ya, yb_)
                if not zone:
                    continue
                zone_in = inset_polygon(zone, 1.6)
                if not zone_in:
                    continue
                zx0 = min(p[0] for p in zone_in)
                zx1 = max(p[0] for p in zone_in)
                x = zx0
                i = 0
                while x < zx1:
                    q = _quer_y(zone_in, x)
                    if q:
                        lo, hi = q
                        hgt = hi - lo
                        sz = min(gross, 0.8 * hgt)
                        rows = 2 if hgt > 2.3 * gross else 1
                        for r_ in range(rows):
                            cy = lo + hgt * (r_ + 0.5) / rows
                            xx = x + sz * 0.6
                            if verzierung == "herzen":
                                shp = heart(xx, cy, sz * 0.95, sz * 0.85) if (i + r_) % 2 == 0 else \
                                    K.circle(xx, cy, 0.17 * sz + 0.3, 16)
                            else:
                                shp = K.star(xx, cy, sz * 0.5, sz * 0.21, 5) if (i + r_) % 2 == 0 else \
                                    K.sparkle(xx, cy, sz * 0.36, 0.25, 6)
                            if all(_in(zone_in, p) for p in shp):
                                loecher.append(shp)
                        x += sz * 0.62 + max(g.wm + 1.2, 0.3 * sz)
                    else:
                        x += 1.0
                    i += 1
            mat = E._andnot(mat, lw.flaechen(loecher))
    mat = mat.union(lw.flaechen(pads))
    part = E.teil_aus_raster(name, lw, mat, cfg.min_web, cfg.kerf, notes)
    for fid, x, y, l, a, pos in slots:
        W.schlitz(part, fid, x, y, l, T, pos, a)
    # Gravur: Zierlinie auf dem Rahmen, Punkte auf der Kufe
    lines = []
    il = inset_polygon(g.body, g.fw * 0.45)
    if il:
        lines.append((il, True))
    W.gravur(part, lines, rand=0.6)
    if spiegeln:
        part = _spiegel(part)
    return part


def _in(poly, p):
    from steckwerk import point_in_polygon
    return point_in_polygon(p, poly)


def _in_box(b, p, m):
    xs = [q[0] for q in b]
    ys = [q[1] for q in b]
    return min(xs) - m <= p[0] <= max(xs) + m and min(ys) - m <= p[1] <= max(ys) + m


def _clip_poly(poly, x0, x1, y0, y1):
    """Polygon auf ein Rechteck beschneiden (Sutherland-Hodgman)."""
    def clip(pts, inside, inter):
        out = []
        n = len(pts)
        for i in range(n):
            a, b = pts[i - 1], pts[i]
            ia, ib = inside(a), inside(b)
            if ib:
                if not ia:
                    out.append(inter(a, b))
                out.append(b)
            elif ia:
                out.append(inter(a, b))
        return out

    def ix(xc):
        return lambda a, b: (xc, a[1] + (b[1] - a[1]) * (xc - a[0]) / ((b[0] - a[0]) or 1e-12))

    def iy(yc):
        return lambda a, b: (a[0] + (b[0] - a[0]) * (yc - a[1]) / ((b[1] - a[1]) or 1e-12), yc)
    pts = list(poly)
    for ins, inter in ((lambda p: p[0] >= x0, ix(x0)), (lambda p: p[0] <= x1, ix(x1)),
                       (lambda p: p[1] >= y0, iy(y0)), (lambda p: p[1] <= y1, iy(y1))):
        if len(pts) < 3:
            return []
        pts = clip(pts, ins, inter)
    return pts if len(pts) >= 3 else []


def _spiegel(p: Part) -> Part:
    from steckwerk import JointFeature
    m = lambda pts: [(-x, y) for x, y in pts]
    q = Part(p.name, oriented(m(p.outline), True))
    for h in p.holes:
        q.holes.append(oriented(m(h), False))
    for e in p.engrave:
        q.add_engrave(m(e.points), e.closed)
    for f in p.features:
        q.features.append(JointFeature(f.id, f.kind, f.length, f.depth, pos=f.pos,
                                       points=oriented(m(f.points), False)))
    return q


# --------------------------------------------------------------------------------------------------
# Querteile
# --------------------------------------------------------------------------------------------------

def _querteil(name: str, laenge: float, B: float, T: float, zapfen_s, prefix: str, pos0: float,
              vorn=None) -> Part:
    """Rechteckige Platte laenge × B mit Zapfen an beiden Längskanten (y = 0 und y = B).
    vorn: optionale Punkte, die die rechte Kante (x = laenge) ersetzen (von unten nach oben)."""
    feats = []
    unten = [(s, tw, f"{prefix}{k}", pos0 + k) for k, (s, tw) in enumerate(zapfen_s)]
    p_unten, f_u = W.kante_mit_zapfen((0.0, 0.0), (laenge, 0.0), unten, T)
    oben = [(laenge - s, tw, f"{prefix}{k}", pos0 + k) for k, (s, tw) in enumerate(zapfen_s)]
    p_oben, f_o = W.kante_mit_zapfen((laenge, B), (0.0, B), oben, T)
    rechts = vorn or []
    pts = p_unten + [(laenge, 0.0)] + rechts + p_oben + [(0.0, B)]
    return pts, f_u, f_o


def build(cfg, name: str = "zierschlitten", laenge: float = 220.0, breite: float = 100.0,
          verzierung: str = "ranken", text: str = ""):
    from models import _deko as dk
    from models._font import unsupported
    if verzierung not in dict(VERZIERUNG):
        raise ValueError(f"Seitenwände: unbekannte Auswahl {verzierung!r}")
    L, B, T = cfg.s(laenge), cfg.s(breite), cfg.T
    if L < 120:
        raise ValueError("Der Schlitten ist zu kurz – mindestens 140 mm Länge")
    if L > 370:
        raise ValueError("Der Schlitten ist zu lang für die Platte – höchstens 360 mm")
    if B < 8 * T or B < 40:
        raise ValueError("Die Innenbreite ist zu schmal für diese Materialstärke – breiter wählen")
    if B + 2 * T > 280:
        raise ValueError("Die Innenbreite ist zu groß für die Platte – höchstens 220 mm")
    bad = unsupported(text or "")
    if bad:
        raise ValueError(f"Zeichen {''.join(bad)!r} gibt es in der Schrift nicht")
    wm = W.wmin(cfg)
    g = Geo(L, B, T, wm)
    notes: List[str] = []
    asm = Assembly(name, params=dict(laenge=L, breite=B, verzierung=verzierung, text=text))
    links = _seitenwand(g, "seitenwand_links", verzierung, cfg, notes, False)
    rechts = _seitenwand(g, "seitenwand_rechts", verzierung, cfg, notes, True)

    # Boden: Länge x_f0 … x_f1, Zapfen an beiden Längskanten
    Lf = g.x_f1 - g.x_f0
    zs = [(x - g.x_f0, g.tw) for x in g.boden_x()]
    pts, fu, fo = _querteil("boden", Lf, B, T, zs, "", 0)
    boden = Part("boden", oriented(pts, True))
    for k, (f1, f2) in enumerate(zip(fu, fo)):
        f1.id, f2.id = f"links{k}", f"rechts{k}"
        f1.pos = f2.pos = 100 + k
        boden.features += [f1, f2]
    cv = dk.Canvas(boden, margin=1.2)
    step = max(8.0, B / 7)
    y = step
    while y < B - step / 2:                                          # Bretterfugen
        cv.draw([(0.0, y), (Lf, y)])
        y += step
    cv.draw(K.rect(2.5, 2.5, Lf - 5, B - 5), True)

    # Sitzbank: vorn geschwungene Kante
    Ls = g.x_s1 - g.x_f0
    zs = [(x - g.x_f0, g.tw) for x in g.sitz_x()]
    amp = min(0.03 * L, 0.3 * Ls) * 0.5
    nb = max(3, int(B / 18))
    welle = []
    for i in range(1, 6 * nb):
        t = i / (6 * nb)
        welle.append((Ls + amp * (0.5 + 0.5 * math.cos(2 * math.pi * nb * t + math.pi)), B * t))
    pts, fu, fo = _querteil("sitz", Ls, B, T, zs, "", 0, vorn=welle)
    sitz = Part("sitzbank", oriented(pts, True))
    for k, (f1, f2) in enumerate(zip(fu, fo)):
        f1.id, f2.id = f"links{k}", f"rechts{k}"
        f1.pos = f2.pos = 200 + k
        sitz.features += [f1, f2]
    cv = dk.Canvas(sitz, margin=2.0)
    from models._shapes import fill_pattern
    fill_pattern(sitz, K.rect(4, 4, Ls - 6, B - 8), "karo", seed=cfg.seed, scale=max(1.0, B / 60))

    # Rückenlehne: Breite B (x), Höhe ab Bodenoberkante; Zapfen links/rechts; Krone oben
    Hw = g.y_post1 + g.fw - g.y_post0                              # bis Oberkante Seitenwand
    Hc = max(0.14 * L, 0.22 * B)                                   # Krone über der Wand
    lehne_pts, lf = _lehne(B, Hw, Hc, T, g, L)
    lehne = Part("lehne", oriented(lehne_pts, True))
    lehne.features += lf
    # Herz in der Krone
    heart_c = (B / 2, Hw + 0.40 * Hc)
    hh = min(0.42 * Hc, 0.3 * B)
    lehne.add_hole(dk.heart(heart_c[0], heart_c[1], 1.1 * hh, hh))
    cv = dk.Canvas(lehne, margin=1.5, seed=cfg.seed)
    if text.strip():
        box = (0.12 * B, 0.30 * Hw, 0.88 * B, 0.80 * Hw)
        res = dk.sign(cv, text.strip(), "geschweift", [box], "normal", "gross", min_h=3.5,
                      max_cap=min(14.0, 0.2 * Hw), anchor="mitte", tol=cfg.arc_tolerance)
        if res is None:
            raise ValueError(f"Der Name „{text}“ passt nicht auf die Lehne – kürzer fassen oder den Schlitten "
                             f"breiter machen")
    dk.styled_line(cv, [(4.0, Hw * 0.12), (B - 4.0, Hw * 0.12)], "wellen", 2.5, side=1)
    dk.styled_line(cv, [(3.0, Hw - 1.0), (B - 3.0, Hw - 1.0)], "sterne", min(6.0, 0.06 * Hc + 3), side=-1,
                   seed=cfg.seed, gravity=False)

    asm.parts += [links, rechts, boden, sitz, lehne]
    for k in range(len(g.boden_x())):
        asm.connect(f"boden:links{k}", f"seitenwand_links:boden{k}")
        asm.connect(f"boden:rechts{k}", f"seitenwand_rechts:boden{k}")
    for k in range(len(g.sitz_x())):
        asm.connect(f"sitzbank:links{k}", f"seitenwand_links:sitz{k}")
        asm.connect(f"sitzbank:rechts{k}", f"seitenwand_rechts:sitz{k}")
    for k in range(len(g.lehne_y())):
        asm.connect(f"lehne:links{k}", f"seitenwand_links:lehne{k}")
        asm.connect(f"lehne:rechts{k}", f"seitenwand_rechts:lehne{k}")
    for t in dict.fromkeys(notes):
        asm.notes.append(t)
    asm.notes.append("Zusammenbau: Boden, Sitzbank und Lehne in eine Seitenwand stecken, dann die zweite Seitenwand "
                     "aufsetzen. Die Zapfen sitzen bündig; bei Bedarf mit einem Tropfen Leim sichern.")
    asm.notes.append("Beide Seitenwände sind spiegelbildlich, damit die Gravur außen liegt.")
    asm.notes.append("Tipp: Mit Moos, Tannengrün und kleinen Geschenken füllen – oder als Brotkorb/Plätzchenschale "
                     "nutzen.")
    return asm


def _lehne(B, Hw, Hc, T, g: Geo, L):
    """Lehne: Rechteck B × Hw mit Zapfen an den Seiten, oben eine geschwungene Krone mit Voluten."""
    ss = [y - g.y_post0 for y in g.lehne_y()]
    p_r, f_r = W.kante_mit_zapfen((B, 0.0), (B, Hw), [(v, g.tw, f"rechts{k}", 300 + k) for k, v in enumerate(ss)], T)
    p_l, f_l = W.kante_mit_zapfen((0.0, Hw), (0.0, 0.0), [(Hw - v, g.tw, f"links{k}", 300 + k)
                                                         for k, v in enumerate(ss)], T)
    # Krone: von rechts oben (B, Hw) über Voluten zur Spitze und zurück nach (0, Hw)
    crown = []
    n = 40
    for i in range(n + 1):
        t = i / n                                     # 0 … 1 von rechts nach links
        x = B * (1 - t)
        s = math.sin(math.pi * t)
        y = Hw + Hc * (0.18 + 0.82 * s ** 1.6) - 0.10 * Hc * math.sin(3 * math.pi * t) ** 2 * (1 - s)
        crown.append((x, y))
    crown[0] = (B, Hw + 0.18 * Hc)
    crown[-1] = (0.0, Hw + 0.18 * Hc)
    pts = [(0.0, 0.0), (B, 0.0)] + p_r[1:] + [(B, Hw)] + crown + p_l
    return pts, f_r + f_l
