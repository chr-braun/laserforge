"""
Ohrhänger – Ohrring-Paare zum Lasern (Sperrholz, Acryl, Leder).

Jedes Motiv ist eine geschlossene Kontur mit Durchbrüchen. Stil „durchbrochen“ schneidet sie aus,
„Rahmen“ lässt nur einen schmalen Rand stehen, „graviert“ graviert die Durchbrüche nur. Durchbrüche,
die zu nah am Rand oder aneinander lägen, entfallen von selbst – so bleibt jeder Steg laserfest.
Oben sitzt eine Öse für den Biegering. Das Paar ist gespiegelt (wichtig beim Flügel).
"""
from __future__ import annotations

import math
from typing import Callable, Dict, List, Sequence, Tuple

from steckwerk import (Assembly, Part, circle, clean, inset_polygon, min_distance, oriented, point_in_polygon,
                       polygon_ok, signed_area)
from models._shapes import drop_close, union_circle
from pakete import flag, num, sel

Point = Tuple[float, float]
Poly = List[Point]
TAU = 2 * math.pi

MOTIVE = [("bluete", "Lotusblüte"), ("fluegel", "Flügel"), ("tropfen", "Tropfen"), ("mond", "Mond"),
          ("sonne", "Sonne"), ("wolke", "Wolke mit Regen"), ("raute", "Raute"), ("waben", "Waben"),
          ("regenbogen", "Regenbogen"), ("faecher", "Fächer")]
STILE = [("durchbrochen", "durchbrochen"), ("rahmen", "nur Rahmen"), ("graviert", "graviert (voll)")]
ZWISCHEN = [("kein", "keins"), ("kreis", "Kreis"), ("stern", "Stern"), ("tropfen", "Tropfen"), ("mond", "Mond")]

INFO = dict(
    label="Ohrhänger",
    group="Schmuck",
    desc="Ohrring-Paare: Lotusblüte, Flügel, Tropfen, Mond, Sonne, Wolke, Raute, Waben, Regenbogen oder Fächer – "
         "durchbrochen, als Rahmen oder graviert, mit Öse für den Biegering.",
    params=[
        sel("motiv", "Motiv", MOTIVE, "bluete"),
        num("groesse", "Länge", 45, 20, 90, help="ohne Öse"),
        sel("stil", "Stil", STILE, "durchbrochen"),
        num("rand", "Rahmenbreite", 2.0, 1.2, 6, when={"stil": ["rahmen"]}),
        sel("zwischen", "Zwischenteil", ZWISCHEN, "kein", help="kleines Teil oben, mit Biegeringen verbunden"),
        num("loch", "Loch für den Biegering", 1.6, 1.4, 3.0),
        flag("paar", "Als Paar (gespiegelt)", True),
    ],
)

UEBERSETZUNG = {"en": {
    "Ohrhänger": "Earrings", "Schmuck": "Jewellery",
    "Ohrring-Paare: Lotusblüte, Flügel, Tropfen, Mond, Sonne, Wolke, Raute, Waben, Regenbogen oder Fächer – "
    "durchbrochen, als Rahmen oder graviert, mit Öse für den Biegering.":
        "Earring pairs: lotus, wing, drop, moon, sun, cloud, rhombus, honeycomb, rainbow or fan – pierced, as a "
        "frame or engraved, with an eyelet for the jump ring.",
    "Motiv": "Motif", "Lotusblüte": "Lotus", "Flügel": "Wing", "Tropfen": "Drop", "Mond": "Moon", "Sonne": "Sun",
    "Wolke mit Regen": "Cloud with rain", "Raute": "Rhombus", "Waben": "Honeycomb", "Regenbogen": "Rainbow",
    "Fächer": "Fan", "Länge": "Length", "ohne Öse": "without eyelet", "Stil": "Style",
    "durchbrochen": "pierced", "nur Rahmen": "frame only", "graviert (voll)": "engraved (solid)",
    "Rahmenbreite": "Frame width", "Zwischenteil": "Connector piece", "keins": "none", "Kreis": "Circle",
    "Stern": "Star", "kleines Teil oben, mit Biegeringen verbunden": "small piece on top, joined with jump rings",
    "Loch für den Biegering": "Hole for the jump ring", "Als Paar (gespiegelt)": "As a pair (mirrored)",
}}


# ---------------------------------------------------------------------------
# Hilfen
# ---------------------------------------------------------------------------

def _ccw(p: Sequence[Point]) -> Poly:
    return oriented(clean(list(p)), True)


def _scale(polys: Sequence[Sequence[Point]], k: float) -> List[Poly]:
    return [[(x * k, y * k) for x, y in p] for p in polys]


def _bbox(pts):
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def _entlang(poly, i, s, step):
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


def stumpf(poly: Sequence[Point], s: float = 0.35, min_winkel: float = 40.0, breite: float = 0.45) -> Poly:
    """Spitze Ecken (< min_winkel) kappen – sonst stimmt der Kerf-Versatz dort nicht."""
    pts = list(poly)
    for _ in range(60):
        n = len(pts)
        if n < 4:
            break
        hit = None
        for i in range(n):
            q1, _ = _entlang(pts, i, s, -1)
            q2, _ = _entlang(pts, i, s, 1)
            v1 = (q1[0] - pts[i][0], q1[1] - pts[i][1])
            v2 = (q2[0] - pts[i][0], q2[1] - pts[i][1])
            l1, l2 = math.hypot(*v1), math.hypot(*v2)
            if l1 < 1e-9 or l2 < 1e-9:
                continue
            w = math.acos(max(-1.0, min(1.0, (v1[0] * v2[0] + v1[1] * v2[1]) / (l1 * l2))))
            if math.degrees(w) < min_winkel:
                hit = (i, w)
                break
        if hit is None:
            break
        i, w = hit
        ss = min(3 * breite + 1.0, max(s, breite / (2 * math.sin(max(w, 0.05) / 2))))
        q1, kb = _entlang(pts, i, ss, -1)
        q2, kf = _entlang(pts, i, ss, 1)
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
        neu = []
        for j in range(n):
            if j == i:
                neu += [q1, q2]
            elif j not in drop:
                neu.append(pts[j])
        pts = drop_close(clean(neu), 0.08, keep=[q1, q2])
    return pts


def _linse(p0: Point, p1: Point, hw: float, n: int = 24) -> Poly:
    """Spitzovale Linse von p0 nach p1 mit halber Breite hw."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    nx, ny = -uy, ux
    right, left = [], []
    for k in range(n + 1):
        t = k / n
        w = hw * math.sin(math.pi * t) ** 0.85
        c = (p0[0] + dx * t, p0[1] + dy * t)
        right.append((c[0] + nx * w, c[1] + ny * w))
        left.append((c[0] - nx * w, c[1] - ny * w))
    return _ccw(right + left[::-1][1:-1])


def _stadion(p0: Point, p1: Point, r: float, n: int = 10) -> Poly:
    """Langloch mit runden Enden."""
    a = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
    pts = [(p1[0] + r * math.cos(a - math.pi / 2 + math.pi * k / n), p1[1] + r * math.sin(a - math.pi / 2 + math.pi * k / n))
           for k in range(n + 1)]
    pts += [(p0[0] + r * math.cos(a + math.pi / 2 + math.pi * k / n), p0[1] + r * math.sin(a + math.pi / 2 + math.pi * k / n))
            for k in range(n + 1)]
    return _ccw(pts)


def _tropfen(cx: float, y0: float, h: float, alpha: float = 28.0, n: int = 72) -> Poly:
    """Tropfen mit Spitze oben: Kreis unten, zwei Tangenten zur Spitze (Spitzenwinkel 2·alpha)."""
    sa = math.sin(math.radians(alpha))
    r = h * sa / (1 + sa)
    c = (cx, y0 + r)
    a0 = math.radians(alpha)                                   # Tangentenpunkte: Winkel ±alpha über der Waagerechten
    pts = [(cx, y0 + h)]
    for k in range(n + 1):
        t = math.pi - a0 + (math.pi + 2 * a0) * k / n         # von links oben über unten nach rechts oben
        pts.append((c[0] + r * math.cos(t), c[1] + r * math.sin(t)))
    return _ccw(pts)


def _polar(center: Point, r: Callable[[float], float], n: int = 360) -> Poly:
    """Sternförmige Kontur um center; φ = 0 zeigt nach oben, positiv nach rechts."""
    return _ccw([(center[0] + r(TAU * k / n - math.pi) * math.sin(TAU * k / n - math.pi),
                  center[1] + r(TAU * k / n - math.pi) * math.cos(TAU * k / n - math.pi)) for k in range(n)])


def _hex(cx: float, cy: float, r: float) -> Poly:
    return [(cx + r * math.sin(TAU * k / 6), cy + r * math.cos(TAU * k / 6)) for k in range(6)]


def _zacken(cx, cy, ro, ri, n, kappe=0.18, rot=0.0) -> Poly:
    """Stern mit kleinen flachen Spitzen."""
    pts = []
    for k in range(n):
        a = rot + TAU * k / n
        d = kappe * math.pi / n
        pts += [(cx + ro * math.sin(a - d), cy + ro * math.cos(a - d)), (cx + ro * math.sin(a + d), cy + ro * math.cos(a + d))]
        b = a + math.pi / n
        pts.append((cx + ri * math.sin(b), cy + ri * math.cos(b)))
    return _ccw(pts)


# ---------------------------------------------------------------------------
# Motive – Einheitsmaß: Höhe 1, Unterkante y = 0, Mitte x = 0. Liefern (Kontur, Durchbrüche, Ösenpunkt)
# ---------------------------------------------------------------------------

def m_bluete():
    petals = [(0.0, 1.0, 0.36), (-0.55, 0.82, 0.36), (0.55, 0.82, 0.36), (-1.08, 0.6, 0.34), (1.08, 0.6, 0.34)]
    r0 = 0.13

    def r(phi):
        best = r0
        for a, L, h in petals:
            d = phi - a
            if abs(d) < h:
                best = max(best, L * math.cos(math.pi / 2 * d / h) ** 0.7)
        return best
    out = _polar((0.0, 0.0), r, 720)
    holes = []
    for a, L, h in petals:
        u = (math.sin(a), math.cos(a))
        holes.append(_linse((u[0] * 0.3 * L, u[1] * 0.3 * L), (u[0] * 0.82 * L, u[1] * 0.82 * L), 0.3 * 0.55 * L * h))
    return out, holes


def m_fluegel():
    # Wurzel oben rechts, Federn hängen nach unten links
    top = [(0.0, 1.0), (0.12, 0.98), (0.2, 0.9)]
    right = [(0.2 - 0.05 * math.sin(math.pi * t) + 0.04 * t, 0.9 - 0.85 * t) for t in [k / 20 for k in range(1, 21)]]
    feathers = 4
    xs = [0.24 - 0.17 * k for k in range(feathers + 1)]        # Federgrenzen von rechts nach links
    ys = [0.05 + 0.1 * k for k in range(feathers + 1)]
    bottom = []
    holes = []
    for k in range(feathers):
        x0, x1 = xs[k], xs[k + 1]
        y0, y1 = ys[k], ys[k + 1]
        cx, cy = (x0 + x1) / 2, min(y0, y1) - 0.06
        rx = (x0 - x1) / 2
        for j in range(1, 13):
            t = math.pi * j / 12
            bottom.append((cx + rx * math.cos(t), cy + (y0 + y1) / 2 - min(y0, y1) + 0.06 - 0.12 * math.sin(t) - (y0 - y1) / 2 * math.cos(t) * -1))
        tip = (cx, cy - 0.03)
        root = (0.08 + 0.02 * k, 0.86 - 0.04 * k)
        holes.append(_linse((tip[0] + (root[0] - tip[0]) * 0.18, tip[1] + (root[1] - tip[1]) * 0.18),
                            (tip[0] + (root[0] - tip[0]) * 0.72, tip[1] + (root[1] - tip[1]) * 0.72), 0.035))
    left = [(xs[-1] + (0.0 - xs[-1]) * t + 0.06 * math.sin(math.pi * t), ys[-1] + (0.98 - ys[-1]) * t)
            for t in [k / 16 for k in range(1, 16)]]
    out = _ccw(top[::-1] + left[::-1] + bottom[::-1] + right[::-1])
    if not polygon_ok(out):
        out = _ccw(top + right + bottom + left)
    return out, holes


def m_tropfen():
    return _tropfen(0.0, 0.0, 1.0), [_tropfen(0.0, 0.1, 0.62), circle(0.0, 0.8, 0.045, 0.003)]


def m_mond():
    R, c = 0.5, (0.0, 0.5)
    r2, c2 = 0.4, (0.24, 0.6)
    pts = []
    # Außenbogen des Mondes links, Innenbogen rechts: Schnittpunkte der Kreise
    d = math.dist(c, c2)
    a = (R * R - r2 * r2 + d * d) / (2 * d)
    h = math.sqrt(max(R * R - a * a, 0))
    ux, uy = (c2[0] - c[0]) / d, (c2[1] - c[1]) / d
    pm = (c[0] + a * ux, c[1] + a * uy)
    s1 = (pm[0] - h * uy, pm[1] + h * ux)
    s2 = (pm[0] + h * uy, pm[1] - h * ux)
    a1 = math.atan2(s1[1] - c[1], s1[0] - c[0])
    a2 = math.atan2(s2[1] - c[1], s2[0] - c[0])
    while a2 < a1:
        a2 += TAU
    for k in range(121):
        t = a1 + (a2 - a1) * k / 120
        pts.append((c[0] + R * math.cos(t), c[1] + R * math.sin(t)))
    b1 = math.atan2(s2[1] - c2[1], s2[0] - c2[0])
    b2 = math.atan2(s1[1] - c2[1], s1[0] - c2[0])
    while b1 < b2:
        b1 += TAU
    for k in range(1, 120):
        t = b1 - (b1 - b2) * k / 120
        pts.append((c2[0] + r2 * math.cos(t), c2[1] + r2 * math.sin(t)))
    out = _ccw(pts)
    holes = [_zacken(-0.27, 0.48, 0.09, 0.04, 5, 0.25), circle(-0.12, 0.2, 0.035, 0.003),
             circle(-0.15, 0.78, 0.03, 0.003)]
    return out, holes


def m_sonne():
    out = _zacken(0.0, 0.5, 0.5, 0.39, 12, 0.22)
    holes = [circle(0.0, 0.5, 0.25, 0.003)]
    for k in range(12):
        a = TAU * k / 12 + math.pi / 12
        holes.append(circle(0.32 * math.sin(a), 0.5 + 0.32 * math.cos(a), 0.022, 0.002))
    return out, holes


def m_wolke():
    cs = [(-0.32, 0.58, 0.2), (0.0, 0.72, 0.24), (0.32, 0.6, 0.19)]
    base, xl, xr = 0.22, -0.5, 0.53

    def top(x):
        v = base + 0.18
        for cx, cy, r in cs:
            if abs(x - cx) < r:
                v = max(v, cy + math.sqrt(r * r - (x - cx) ** 2))
        return v
    xa, xb = -0.3, 0.33                                    # Mitten der Randkreise: dort setzen die runden Enden an
    n = 160
    up = [(xb - (xb - xa) * k / n, top(xb - (xb - xa) * k / n)) for k in range(n + 1)]
    rl = (up[-1][1] - base) / 2
    links = [(xa - rl * math.sin(t), base + rl + rl * math.cos(t)) for t in [math.pi * k / 24 for k in range(1, 24)]]
    rr = (up[0][1] - base) / 2
    rechts = [(xb + rr * math.sin(t), base + rr - rr * math.cos(t)) for t in [math.pi * k / 24 for k in range(1, 24)]]
    out = _ccw(up + links + [(xa, base), (xb, base)] + rechts)
    holes = []
    for x, y in ((-0.25, 0.3), (0.05, 0.36), (0.33, 0.28), (-0.1, 0.56), (0.2, 0.56)):
        holes.append(_tropfen(x, y, 0.15))
    return out, holes


def m_raute():
    out = _ccw([(0.0, 0.0), (0.33, 0.5), (0.0, 1.0), (-0.33, 0.5)])
    k = 0.6
    inner = [(0.0, 0.5 - 0.5 * k), (0.33 * k, 0.5), (0.0, 0.5 + 0.5 * k), (-0.33 * k, 0.5)]
    bar = 0.045
    oben = _ccw([(0.0, 0.5 + 0.5 * k), (-0.33 * k + 0.33 * k * bar / (0.5 * k) * 0.66, 0.5 + bar),
                 (0.33 * k - 0.33 * k * bar / (0.5 * k) * 0.66, 0.5 + bar)])
    unten = _ccw([(0.0, 0.5 - 0.5 * k), (0.33 * k - 0.66 * bar * 0.66, 0.5 - bar),
                  (-0.33 * k + 0.66 * bar * 0.66, 0.5 - bar)])
    klein = _ccw([(0.0, 0.5 - 0.5 * k - 0.16), (0.07, 0.5 - 0.5 * k - 0.06), (0.0, 0.5 - 0.5 * k - 0.0),
                  (-0.07, 0.5 - 0.5 * k - 0.06)])
    return out, [oben, unten]


def m_waben():
    R = 0.5
    out = _ccw(_hex(0.0, 0.5, R))
    holes = []
    r, g = 0.072, 0.034
    w = math.sqrt(3) * r + g
    dz = 1.5 * r + g * 0.866
    for j in range(-5, 6):
        for i in range(-5, 6):
            x = w * (i + 0.5 * (j % 2))
            y = 0.5 + dz * j
            if math.hypot(x, y - 0.5) < R * 0.8 - r:
                holes.append(_hex(x, y, r))
    return out, holes


def m_regenbogen():
    Ro, Ri, n = 0.5, 0.17, 4
    c = (0.0, 0.08)
    pts = [(c[0] + Ro * math.cos(math.pi * k / 120), c[1] + Ro * math.sin(math.pi * k / 120)) for k in range(121)]
    pts += [(c[0] - Ri * math.cos(math.pi * k / 60), c[1] + Ri * math.sin(math.pi * k / 60)) for k in range(61)]
    # Unterkante leicht abgesetzt
    out = _ccw([(c[0] + Ri, c[1] - 0.08), (c[0] + Ro, c[1] - 0.08)] + pts + [(c[0] - Ro, c[1] - 0.08), (c[0] - Ri, c[1] - 0.08)])
    out = _ccw([(Ri, 0.0), (Ro, 0.0)] + [(Ro * math.cos(math.pi * k / 120), 0.08 + Ro * math.sin(math.pi * k / 120)) for k in range(121)]
               + [(-Ro, 0.0), (-Ri, 0.0)] + [(-Ri * math.cos(math.pi * k / 60), 0.08 + Ri * math.sin(math.pi * k / 60)) for k in range(61)][::-1][::-1])
    holes = []
    band = (Ro - Ri) / n
    for i in range(1, n):
        r = Ri + band * i
        w = band * 0.16
        e = 0.12
        pts = [(r + w) * math.cos(math.pi * (e + (1 - 2 * e) * k / 80)) for k in range(81)]
        arc_o = [((r + w) * math.cos(math.pi * (e + (1 - 2 * e) * k / 80)), 0.08 + (r + w) * math.sin(math.pi * (e + (1 - 2 * e) * k / 80))) for k in range(81)]
        arc_i = [((r - w) * math.cos(math.pi * (e + (1 - 2 * e) * k / 80)), 0.08 + (r - w) * math.sin(math.pi * (e + (1 - 2 * e) * k / 80))) for k in range(81)]
        holes.append(_ccw(arc_o + arc_i[::-1]))
    return out, holes


def m_faecher():
    R, a0, a1 = 1.0, math.radians(-50), math.radians(50)
    hub = 0.12
    c = (0.0, 0.0)
    pts = [(c[0] + R * math.sin(a0 + (a1 - a0) * k / 100), c[1] + R * math.cos(a0 + (a1 - a0) * k / 100) - 0.0) for k in range(101)]
    pts = pts[::-1]
    bottom = [(hub * math.sin(a1 + (TAU - (a1 - a0)) * k / 40), hub * math.cos(a1 + (TAU - (a1 - a0)) * k / 40)) for k in range(41)]
    out = _ccw(pts + bottom[::-1][1:-1])
    holes = []
    m = 7
    for k in range(m):
        a = a0 + (a1 - a0) * (k + 0.5) / m
        u = (math.sin(a), math.cos(a))
        holes.append(_linse((u[0] * 0.3, u[1] * 0.3), (u[0] * 0.9, u[1] * 0.9), 0.045))
    return out, holes


MOTIV_F = dict(bluete=m_bluete, fluegel=m_fluegel, tropfen=m_tropfen, mond=m_mond, sonne=m_sonne, wolke=m_wolke,
               raute=m_raute, waben=m_waben, regenbogen=m_regenbogen, faecher=m_faecher)


def _norm(out: Poly, holes: Sequence[Poly], S: float):
    """Auf Höhe S bringen, Unterkante y = 0, Mitte x = 0."""
    x0, y0, x1, y1 = _bbox(out)
    k = S / (y1 - y0)
    cx = (x0 + x1) / 2
    f = lambda p: [((x - cx) * k, (y - y0) * k) for x, y in p]
    return f(out), [f(h) for h in holes]


def _oese(out: Poly, r_loch: float, web: float, tol: float):
    """Öse oben an der höchsten Stelle anfügen: (Kontur, Lochkreis)."""
    top = max(out, key=lambda p: p[1])
    ring = r_loch + max(1.3 * web, 1.2)
    for dy in (0.4, 0.25, 0.55, 0.7, 0.1):
        cx, cy = top[0], top[1] + dy * ring
        try:
            neu = union_circle(out, cx, cy, ring, tol)
        except ValueError:
            continue
        hole = circle(cx, cy, r_loch, tol)
        neu = _ccw(neu)
        if polygon_ok(neu) and all(point_in_polygon(p, neu) for p in hole) and min_distance(hole, neu) >= web:
            return neu, hole
    raise ValueError("Die Öse passt nicht – Loch kleiner oder Ohrhänger größer machen")


def _loch_ok(h: Poly, kerf: float) -> bool:
    from steckwerk import offset_polygon
    if len(h) < 3 or abs(signed_area(h)) < 1.2 or not polygon_ok(_ccw(h)):
        return False
    comp = offset_polygon(oriented(h, False), kerf)
    return len(comp) >= 3 and polygon_ok(_ccw(comp)) and abs(signed_area(comp)) > 0.6


def _durchbrueche(out: Poly, cand: Sequence[Poly], web: float, kerf: float, schon: Sequence[Poly] = ()) -> List[Poly]:
    """Nur Durchbrüche behalten, die mit Steg ≥ web zum Rand und zu den anderen liegen."""
    keep: List[Poly] = []
    for h in sorted(cand, key=lambda p: -abs(signed_area(p))):
        h = stumpf(_ccw(h), min_winkel=50.0, breite=0.9)
        if not _loch_ok(h, kerf):
            continue
        if not all(point_in_polygon(p, out) for p in h):
            continue
        if min_distance(h, out, limit=web * 1.2) < web * 1.15:
            continue
        if any(min_distance(h, o, limit=web * 1.2) < web * 1.15 for o in list(keep) + list(schon)):
            continue
        keep.append(h)
    return keep


def _teil(cfg, name: str, motiv: str, S: float, stil: str, rand: float, loch: float, spiegeln: bool) -> Part:
    T, web, tol = cfg.T, max(cfg.min_web, 0.9), cfg.arc_tolerance
    out, holes = MOTIV_F[motiv]()
    out, holes = _norm(out, holes, S)
    if spiegeln:
        out = _ccw([(-x, y) for x, y in out])
        holes = [_ccw([(-x, y) for x, y in h]) for h in holes]
    out = stumpf(drop_close(_ccw(out), 0.12))
    if not polygon_ok(out):
        raise ValueError(f"Motiv {motiv!r} lässt sich in dieser Größe nicht sauber schneiden – größer machen")
    body = out
    out, ring = _oese(out, loch / 2, web, tol)
    part = Part(name, out)
    part.add_hole(ring)
    if stil == "rahmen":
        r = max(rand, web * 1.3)
        inner = inset_polygon(body, r)
        inner = stumpf(drop_close(inner, 0.12), min_winkel=50.0, breite=0.9) if inner else []
        ok = inner and polygon_ok(_ccw(inner)) and min_distance(inner, ring) >= web * 1.15 \
            and _loch_ok(inner, cfg.kerf_offset)
        if not ok:                                         # Öse ragt hinein: Rahmen unterhalb der Öse
            raise ValueError("Der Rahmen geht sich nicht aus – Rahmen schmaler oder Ohrhänger größer machen")
        part.add_hole(inner)
        return part
    keep = _durchbrueche(out, [_ccw(h) for h in holes], web, cfg.kerf_offset, schon=[ring])
    for h in keep:
        if stil == "graviert":
            part.add_engrave(h + [h[0]])
        else:
            part.add_hole(h)
    return part


def _zwischenteil(cfg, name: str, form: str, loch: float) -> Part:
    web, tol = max(cfg.min_web, 0.9), cfg.arc_tolerance
    r = loch / 2
    L = max(12.0, 6 * r + 4 * web + 4)
    if form == "kreis":
        out = circle(0.0, L / 2, L / 2, tol)
    elif form == "stern":
        out = _zacken(0.0, L / 2, L / 2 * 1.1, L / 2 * 0.62, 5, 0.3)
    elif form == "tropfen":
        out = _tropfen(0.0, 0.0, L)
    else:
        o, _ = m_mond()
        out, _ = _norm(o, [], L)
    out = stumpf(drop_close(_ccw(out), 0.12))
    x0, y0, x1, y1 = _bbox(out)
    part = Part(name, out)

    def passt(cx, cy):
        h = circle(cx, cy, r, tol)
        return h if all(point_in_polygon(p, out) for p in h) and min_distance(h, out) >= web * 1.1 else None
    cands = []                                              # Rasterpunkte, nah an der Mittelachse zuerst
    n = 40
    for i in range(n + 1):
        cy = y0 + (y1 - y0) * i / n
        for j in range(n + 1):
            cx = x0 + (x1 - x0) * j / n
            cands.append((cx, cy))
    mx = (x0 + x1) / 2 if form != "mond" else x0 + (x1 - x0) * 0.3
    oben = unten = None
    for cx, cy in sorted(cands, key=lambda c: -c[1] + 2.5 * abs(c[0] - mx)):
        oben = passt(cx, cy)
        if oben:
            break
    for cx, cy in sorted(cands, key=lambda c: c[1] + 2.5 * abs(c[0] - mx)):
        unten = passt(cx, cy)
        if unten:
            break
    if not oben or not unten or min_distance(oben, unten) < web * 1.1:
        raise ValueError("Das Zwischenteil ist für dieses Loch zu klein – Loch kleiner wählen")
    part.add_hole(oben)
    part.add_hole(unten)
    return part


def build(cfg, name: str = "ohrhaenger", motiv: str = "bluete", groesse: float = 45.0, stil: str = "durchbrochen",
          rand: float = 2.0, zwischen: str = "kein", loch: float = 1.6, paar: bool = True):
    if motiv not in MOTIV_F:
        raise ValueError(f"Unbekanntes Motiv {motiv!r}")
    if stil not in dict(STILE):
        raise ValueError(f"Unbekannter Stil {stil!r}")
    if zwischen not in dict(ZWISCHEN):
        raise ValueError(f"Unbekanntes Zwischenteil {zwischen!r}")
    S = cfg.s(groesse)
    asm = Assembly(name, params=dict(motiv=motiv, groesse=S, stil=stil, zwischen=zwischen, loch=loch, paar=paar))
    seiten = [("links", False), ("rechts", True)] if paar else [("einzeln", False)]
    for nm, sp in seiten:
        asm.parts.append(_teil(cfg, nm, motiv, S, stil, rand, loch, sp))
        if zwischen != "kein":
            asm.parts.append(_zwischenteil(cfg, f"{nm}_oben", zwischen, loch))
    ringe = len(seiten) * (2 if zwischen != "kein" else 1)
    asm.notes.append(f"Dazu brauchst du {len(seiten)} Ohrhaken und {ringe} Biegeringe (Ø {max(4, loch * 2.5):.0f} mm). "
                     "Holz vorher schleifen und mit Klarlack oder Öl versiegeln.")
    if stil == "graviert":
        asm.notes.append("Gravierte Muster lassen sich danach schön mit Farbe oder Blattgold ausmalen.")
    return asm
