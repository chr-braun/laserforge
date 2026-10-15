"""
_grusel.py – Halloween-Formbausteine (Bibliothek „Verzierungen“, ursprünglich aus dem Paket Halloween).

Alle Formen sind reine Polygone in mm (y nach oben). Silhouetten stehen auf y = 0, Motive
(Fledermaus, Spinne, Geist …) sind um ihren Mittelpunkt gebaut. Die Bausteine:

  op2            Vereinigung/Differenz zweier Konturen, die sich genau zweimal schneiden
  strip          Band entlang einer Linie (Beine, Ranken, Äste) als linke/rechte Kante
  bat, spider, ghost, skull, witch, cat, hat, pumpkin, crow   Motive
  tree           knorriger, verästelter Baum (zufällig, mit festem Startwert)
  mansion, cottage, crypt, tombstone, fence, cauldron         Szenen-Elemente
  web            Spinnennetz: Fäden als Material, Zwischenräume als Löcher
"""
from __future__ import annotations

import math
import random
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from steckwerk import (Point, arc_points, bezier_q, circle, clean, dist, ellipse, oriented, point_in_polygon,
                        point_seg_dist, polygon_ok, rect, rotate, segments_cross, signed_area, translate)

Poly = List[Point]


# --------------------------------------------------------------------------------------------------
# Geometrie-Helfer
# --------------------------------------------------------------------------------------------------

def mirror(right: Sequence[Point]) -> Poly:
    """Rechte Hälfte (von oben Mitte im Uhrzeigersinn nach unten Mitte) spiegeln → ganze Kontur."""
    r = list(right)
    left = [(-x, y) for x, y in reversed(r) if abs(x) > 1e-9]
    pts = [p for p in r if True] + left
    return dedupe(pts)


def dedupe(pts: Sequence[Point], d: float = 0.05, closed: bool = True) -> Poly:
    out: Poly = []
    for p in pts:
        if not out or dist(out[-1], p) >= d:
            out.append(p)
    while closed and len(out) > 3 and dist(out[0], out[-1]) < d:
        out.pop()
    return out


def place(pts: Sequence[Point], cx: float, cy: float, s: float, ang: float = 0.0, flip: bool = False) -> Poly:
    """Einheitsform skalieren, drehen und verschieben."""
    out = []
    ca, sa = math.cos(ang), math.sin(ang)
    for x, y in pts:
        if flip:
            x = -x
        x, y = x * s, y * s
        out.append((cx + x * ca - y * sa, cy + x * sa + y * ca))
    if flip:
        out.reverse()
    return out


def bez(p0: Point, c: Point, p1: Point, n: int = 10) -> Poly:
    return bezier_q(p0, c, p1, n)


def bez3(p0: Point, c1: Point, c2: Point, p1: Point, n: int = 16) -> Poly:
    out = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        out.append((u ** 3 * p0[0] + 3 * u * u * t * c1[0] + 3 * u * t * t * c2[0] + t ** 3 * p1[0],
                    u ** 3 * p0[1] + 3 * u * u * t * c1[1] + 3 * u * t * t * c2[1] + t ** 3 * p1[1]))
    return out


def chain(*parts: Sequence[Point]) -> Poly:
    """Polylinien aneinanderhängen (gemeinsame Endpunkte nur einmal)."""
    out: Poly = []
    for p in parts:
        for q in p:
            if not out or dist(out[-1], q) > 1e-6:
                out.append(q)
    return out


def arc(cx: float, cy: float, r: float, a0: float, a1: float, n: Optional[int] = None) -> Poly:
    n = n or max(4, int(abs(a1 - a0) * max(r, 1) / 1.2) + 2)
    return [(cx + r * math.cos(a0 + (a1 - a0) * i / n), cy + r * math.sin(a0 + (a1 - a0) * i / n))
            for i in range(n + 1)]


def poly_bbox(pts: Sequence[Point]) -> Tuple[float, float, float, float]:
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def min_gap(pts: Sequence[Point], skip: int = 3) -> float:
    """Kleinster Abstand zwischen nicht benachbarten Kanten derselben Kontur (Materialsteg)."""
    n = len(pts)
    es = [(pts[i], pts[(i + 1) % n]) for i in range(n)]
    bbs = [(min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1])) for a, b in es]
    best = math.inf
    for i in range(n):
        a, b = es[i]
        x0, y0, x1, y1 = bbs[i]
        for j in range(i + skip, n):
            if (j - i) % n < skip or (i - j) % n < skip:
                continue
            u0, v0, u1, v1 = bbs[j]
            if u0 > x1 + best or u1 < x0 - best or v0 > y1 + best or v1 < y0 - best:
                continue
            c, d = es[j]
            if segments_cross(a, b, c, d):
                return 0.0
            g = min(point_seg_dist(a, c, d), point_seg_dist(b, c, d), point_seg_dist(c, a, b),
                    point_seg_dist(d, a, b))
            best = min(best, g)
    return best


def hole_ok(h: Sequence[Point], d: float = 0.25) -> bool:
    """Übersteht das Loch die Kerf-Kompensation (Schrumpfen um d) ohne sich zu verknoten?"""
    from laserforge import offset_polygon
    cw = oriented(clean(h), False)
    comp = offset_polygon(cw, d)
    if len(comp) < 3:
        return False
    cc = oriented(comp, True)
    return polygon_ok(cc) and abs(signed_area(comp)) > 0.5 and signed_area(comp) * signed_area(cw) > 0


def _seg_hit(a: Point, b: Point, c: Point, d: Point) -> Optional[Tuple[float, float, Point]]:
    r = (b[0] - a[0], b[1] - a[1])
    s = (d[0] - c[0], d[1] - c[1])
    den = r[0] * s[1] - r[1] * s[0]
    if abs(den) < 1e-14:
        return None
    t = ((c[0] - a[0]) * s[1] - (c[1] - a[1]) * s[0]) / den
    u = ((c[0] - a[0]) * r[1] - (c[1] - a[1]) * r[0]) / den
    if 0 <= t < 1 and 0 <= u < 1:
        return t, u, (a[0] + t * r[0], a[1] + t * r[1])
    return None


def op2(P: Sequence[Point], Q: Sequence[Point], mode: str = "union") -> Poly:
    """Vereinigung ("union") oder Differenz P−Q ("minus") zweier einfacher Konturen, deren Ränder
    sich genau zweimal schneiden. Ergebnis gegen den Uhrzeigersinn."""
    P = oriented(clean(P), True)
    Q = oriented(clean(Q), True)
    hits = []
    nP, nQ = len(P), len(Q)
    for i in range(nP):
        a, b = P[i], P[(i + 1) % nP]
        for j in range(nQ):
            h = _seg_hit(a, b, Q[j], Q[(j + 1) % nQ])
            if h:
                hits.append((i + h[0], j + h[1], h[2]))
    if len(hits) != 2:
        raise ValueError(f"op2: {len(hits)} Schnittpunkte statt 2")
    hits.sort()
    (pa, qa, A), (pb, qb, B) = hits

    def run(poly, s, e, ps, pe):
        """Kette von ps (Param s) bis pe (Param e) entlang poly vorwärts."""
        n = len(poly)
        out = [ps]
        k = int(math.floor(s)) + 1
        end = e if e > s else e + n
        while k <= end:
            out.append(poly[k % n])
            k += 1
        out.append(pe)
        return out

    p1 = run(P, pa, pb, A, B)            # A → B
    p2 = run(P, pb, pa, B, A)            # B → A
    q_ab = run(Q, qa, qb, A, B) if qa < qb else run(Q, qa, qb, A, B)
    q_ba = run(Q, qb, qa, B, A)

    def sample(ch):
        mids = ch[1:-1] if len(ch) > 2 else [((ch[0][0] + ch[1][0]) / 2, (ch[0][1] + ch[1][1]) / 2)]
        return mids[len(mids) // 2]

    keepP = p1 if not point_in_polygon(sample(p1), Q) else p2
    inside_wanted = mode == "minus"
    # Q-Kette, die vom Ende von keepP zurück zum Anfang läuft
    s, e = keepP[0], keepP[-1]
    cands = []
    for ch in (q_ab, q_ba):
        for c in (ch, list(reversed(ch))):
            if dist(c[0], e) < 1e-9 and dist(c[-1], s) < 1e-9:
                cands.append(c)
    pick = None
    for c in cands:
        if point_in_polygon(sample(c), P) == inside_wanted:
            pick = c
            break
    if pick is None:
        raise ValueError("op2: keine passende Kette")
    out = dedupe(keepP + pick[1:-1], 0.12)
    return oriented(out, True)


def strip(path: Sequence[Point], w0: float, w1: float) -> Tuple[Poly, Poly]:
    """Band entlang path mit Breite w0 → w1. Liefert (rechte Kante, linke Kante), beide in Laufrichtung."""
    n = len(path)
    right, left = [], []
    for i, p in enumerate(path):
        if i == 0:
            d = (path[1][0] - p[0], path[1][1] - p[1])
        elif i == n - 1:
            d = (p[0] - path[i - 1][0], p[1] - path[i - 1][1])
        else:
            d = (path[i + 1][0] - path[i - 1][0], path[i + 1][1] - path[i - 1][1])
        L = math.hypot(*d) or 1.0
        nx, ny = d[1] / L, -d[0] / L                      # rechts der Laufrichtung
        w = (w0 + (w1 - w0) * i / max(1, n - 1)) / 2
        right.append((p[0] + nx * w, p[1] + ny * w))
        left.append((p[0] - nx * w, p[1] - ny * w))
    return right, left


def limb(path: Sequence[Point], w0: float, w1: float, tip: str = "rund") -> Poly:
    """Ausstülpung entlang path (beginnt am Rumpf): rechts hin, Spitze, links zurück."""
    r, l = strip(path, w0, w1)
    e = path[-1]
    d = (path[-1][0] - path[-2][0], path[-1][1] - path[-2][1])
    L = math.hypot(*d) or 1.0
    ux, uy = d[0] / L, d[1] / L
    if tip == "spitz":
        end = [(e[0] + ux * w1 * 0.9, e[1] + uy * w1 * 0.9)]
    else:
        a = math.atan2(uy, ux)
        end = [(e[0] + math.cos(a - math.pi / 2 + math.pi * k / 4) * w1 / 2,
                e[1] + math.sin(a - math.pi / 2 + math.pi * k / 4) * w1 / 2) for k in range(1, 4)]
    return r + end + list(reversed(l))


def smooth(pts: Sequence[Point], rounds: int = 1, closed: bool = True) -> Poly:
    """Chaikin-Glättung."""
    p = list(pts)
    for _ in range(rounds):
        q = []
        n = len(p)
        rng = range(n) if closed else range(n - 1)
        if not closed:
            q.append(p[0])
        for i in rng:
            a, b = p[i], p[(i + 1) % n]
            q.append((0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]))
            q.append((0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1]))
        if not closed:
            q.append(p[-1])
        p = q
    return p


# --------------------------------------------------------------------------------------------------
# Motive (Einheitsgröße, Mittelpunkt 0/0)
# --------------------------------------------------------------------------------------------------

def bat_unit(wing: float = 0.0) -> Poly:
    """Fledermaus, Spannweite 1. wing −1…1 hebt/senkt die Flügel."""
    lift = 0.10 * wing
    tip = (0.50, 0.15 + lift)
    right = chain(
        [(0.0, 0.085)],
        [(0.022, 0.095), (0.042, 0.175), (0.058, 0.085)],                       # Ohr
        bez((0.058, 0.085), (0.075, 0.075), (0.105, 0.075), 4),                  # Schulter
        bez((0.105, 0.075), (0.30, 0.20 + lift * 1.2), tip, 12),                 # Flügel oben
        bez(tip, (0.43, 0.04 + lift * 0.6), (0.40, -0.03 + lift * 0.4), 6),       # Zacken 1
        bez((0.40, -0.03 + lift * 0.4), (0.34, 0.03 + lift * 0.3), (0.28, -0.075 + lift * 0.2), 7),
        bez((0.28, -0.075 + lift * 0.2), (0.21, -0.01 + lift * 0.1), (0.15, -0.085), 7),
        bez((0.15, -0.085), (0.10, -0.03), (0.06, -0.085), 6),                    # zum Körper
        [(0.040, -0.150), (0.0, -0.135)],
    )
    return mirror(right)


def spider_unit(legs: float = 1.0) -> Poly:
    """Spinne von oben gesehen, Größe ~1 (Beinspanne). Faden oben bei (0, 0.15)."""
    body_r, head_r = 0.13, 0.075
    out: Poly = []
    # Hinterleib (unten) + Kopf (oben) als Kontur mit 8 Beinen
    leg_ang = [20, 45, 80, 115]                                   # rechts, von oben nach unten
    pts: Poly = []
    # Start: oben am Kopf, rechts herum (Uhrzeigersinn rechts)
    pts += arc(0, 0.08, head_r, math.pi / 2, math.radians(-10), 10)
    for k, a in enumerate(leg_ang):
        base_ang = math.radians(a)
        cx, cy = (0.0, 0.0)
        bx, by = 0.11 * math.cos(math.radians(90 - a) * 0 + 0) , 0
    # einfacher: Körper als Kreis/Ellipse, Beine als Ausstülpungen
    pts = []
    n = 64
    leg_at = {}
    for side in (1, -1):
        for k, a in enumerate((35, 10, -15, -40)):
            leg_at[(side, k)] = a
    body = []
    for i in range(n):
        t = 2 * math.pi * i / n
        r = 1.0
        x = 0.10 * math.cos(t)
        y = 0.04 + (0.15 if math.sin(t) > 0 else 0.13) * math.sin(t)
        body.append((x, y))
    return body


def _ellipse_pts(cx, cy, rx, ry, a0, a1, n):
    return [(cx + rx * math.cos(a0 + (a1 - a0) * i / n), cy + ry * math.sin(a0 + (a1 - a0) * i / n))
            for i in range(n + 1)]


def spider(cx: float, cy: float, S: float, w: float, thread_top: Optional[float] = None) -> Poly:
    """Spinne (Beinspanne ~S, Mindest-Beinbreite w), optional mit Faden nach oben bis thread_top.
    Die acht Beine setzen am Kopfbruststück an, darunter der dicke Hinterleib."""
    leg_w = max(w, 0.04 * S)
    hr = max(0.10 * S, 1.6 * leg_w / math.radians(30))
    br = max(0.14 * S, hr * 1.25)
    hy = cy + 0.06 * S
    by = hy - hr - br * 0.75
    tw = max(w, 0.03 * S)
    legs = [  # Ansatzwinkel am Kopf, Knie, Fuß (relativ zu cx/hy, Einheit S)
        (62, (0.24, 0.30), (0.40, 0.16)),
        (30, (0.36, 0.16), (0.52, 0.00)),
        (-2, (0.36, -0.06), (0.48, -0.24)),
        (-34, (0.26, -0.22), (0.32, -0.44)),
    ]
    pts: Poly = []
    a_top = math.acos(min(0.95, (tw / 2) / hr)) if thread_top is not None else math.pi / 2
    if thread_top is not None:
        pts.append((tw / 2, thread_top))
    prev = a_top
    half = math.degrees(leg_w * 0.55 / hr)
    for a, kn, ft in legs:
        a0 = math.radians(a + half)
        a1 = math.radians(a - half)
        pts += _ellipse_pts(0.0, hy, hr, hr, prev, a0, 3)
        base = (hr * 0.9 * math.cos(math.radians(a)), hy + hr * 0.9 * math.sin(math.radians(a)))
        path = bez(base, (kn[0] * S, hy + kn[1] * S), (ft[0] * S, hy + ft[1] * S), 12)
        r, l = strip(path, leg_w * 1.1, leg_w * 0.85)
        r[0] = (hr * math.cos(a1), hy + hr * math.sin(a1))
        l[0] = (hr * math.cos(a0), hy + hr * math.sin(a0))
        d = (path[-1][0] - path[-2][0], path[-1][1] - path[-2][1])
        L = math.hypot(*d) or 1
        tip = (path[-1][0] + d[0] / L * leg_w, path[-1][1] + d[1] / L * leg_w)
        pts += list(l) + [tip] + list(reversed(r))
        prev = a1
    # Übergang zum Hinterleib: Kopfbogen bis in den Hinterleib, dann dessen Rand
    rx_b = br * 0.85
    a = prev
    step = math.radians(2)
    while a > -math.pi / 2:
        q = (hr * math.cos(a), hy + hr * math.sin(a))
        if (q[0] / rx_b) ** 2 + ((q[1] - by) / br) ** 2 < 1.0:
            break
        pts.append(q)
        a -= step
    t = math.atan2((q[1] - by) / br, q[0] / rx_b)
    pts += _ellipse_pts(0.0, by, rx_b, br, t, -math.pi / 2, 12)
    right = [(cx + x, y) for x, y in pts]
    full = right + [(2 * cx - x, y) for x, y in reversed(right) if abs(x) > 1e-9]
    out = dedupe(full, 0.08)
    return oriented(out, True)


def ghost_unit() -> Poly:
    """Gespenst mit ausgebreiteten, flatternden Ärmeln, Höhe 1, Mitte (0, 0)."""
    right = chain(
        [(0.0, 0.50)],
        bez((0.0, 0.50), (0.24, 0.50), (0.25, 0.24), 10),                       # Kopf
        bez((0.25, 0.24), (0.36, 0.26), (0.47, 0.20), 6),                       # Arm
        [(0.49, 0.12), (0.43, 0.135), (0.45, 0.06), (0.38, 0.09)],              # Ärmelzipfel
        bez((0.38, 0.09), (0.31, 0.06), (0.29, 0.0), 5),
        bez((0.29, 0.0), (0.31, -0.25), (0.36, -0.46), 8),                      # Körper
        bez((0.36, -0.46), (0.28, -0.36), (0.22, -0.47), 5),                    # Saum
        bez((0.22, -0.47), (0.15, -0.38), (0.08, -0.47), 5),
        bez((0.08, -0.47), (0.04, -0.40), (0.0, -0.44), 4),
    )
    return mirror(right)


def skull_unit() -> Poly:
    """Totenkopf, Höhe 1 (Mitte 0/0)."""
    right = chain(
        [(0.0, 0.50)],
        bez((0.0, 0.50), (0.40, 0.50), (0.40, 0.08), 12),
        bez((0.40, 0.08), (0.40, -0.06), (0.30, -0.12), 6),                    # Wange
        [(0.26, -0.20)],
        bez((0.26, -0.20), (0.26, -0.40), (0.20, -0.46), 6),                   # Kiefer
        bez((0.20, -0.46), (0.10, -0.50), (0.0, -0.50), 5),
    )
    return mirror(right)


def skull_holes(cx: float, cy: float, h: float) -> List[Poly]:
    """Augen, Nase und Zahnlücken eines Totenkopfs der Höhe h."""
    s = h
    holes = []
    for side in (1, -1):
        eye = [(cx + side * (0.15 + 0.11 * math.cos(t)) * s, cy + (0.06 + 0.10 * math.sin(t)) * s)
               for t in [2 * math.pi * i / 28 for i in range(28)]]
        eye = [(x, y - (0.035 * s if y > cy + 0.10 * s and (x - cx) * side < 0.13 * s else 0.0)) for x, y in eye]
        holes.append(eye)
    holes.append([(cx, cy - 0.04 * s), (cx + 0.06 * s, cy - 0.17 * s), (cx, cy - 0.15 * s),
                  (cx - 0.06 * s, cy - 0.17 * s)])
    for k in range(-2, 3):
        x = cx + k * 0.065 * s
        holes.append(rect(x - 0.012 * s, cy - 0.40 * s, 0.024 * s, 0.13 * s))
    return holes


def witch_unit() -> Poly:
    """Hexe auf dem Besen, nach rechts fliegend, Breite ~1, Mitte 0/0."""
    pts = chain(
        [(-0.50, -0.06)],                                                        # Besenreisig hinten
        [(-0.40, -0.02), (-0.30, -0.035)],
        [(-0.20, -0.02)],                                                        # Bindung
        [(-0.12, -0.04)],                                                        # Bein / Kleid unten
        bez((-0.12, -0.04), (-0.02, -0.16), (0.06, -0.10), 6),                   # Fuß nach vorn
        [(0.10, -0.12), (0.12, -0.08), (0.05, -0.05)],
        [(0.48, -0.02), (0.50, 0.005), (0.47, 0.01)],                            # Besenstiel vorn
        [(0.06, -0.01)],
        bez((0.06, -0.01), (0.12, 0.06), (0.16, 0.12), 5),                       # Arm nach vorn
        [(0.15, 0.14)],
        bez((0.15, 0.14), (0.08, 0.10), (0.04, 0.10), 4),
        bez((0.04, 0.10), (0.06, 0.16), (0.03, 0.21), 5),                        # Kopf / Nase
        [(0.075, 0.215), (0.03, 0.24)],
        [(0.10, 0.27), (0.11, 0.285), (-0.02, 0.28)],                            # Hutkrempe vorn
        bez((-0.02, 0.28), (0.00, 0.37), (-0.10, 0.46), 6),                      # Hutspitze
        bez((-0.10, 0.46), (-0.07, 0.36), (-0.09, 0.28), 6),
        [(-0.17, 0.265), (-0.17, 0.25), (-0.06, 0.25)],                          # Krempe hinten
        bez((-0.06, 0.25), (-0.12, 0.20), (-0.20, 0.16), 5),                     # Haare wehen
        [(-0.16, 0.15)],
        bez((-0.16, 0.15), (-0.22, 0.10), (-0.24, 0.02), 5),                     # Umhang
        [(-0.20, 0.005)],
        [(-0.30, 0.02), (-0.40, 0.04), (-0.50, 0.07), (-0.46, 0.0)],             # Reisig oben
    )
    return dedupe(pts, 0.004)


def cat_unit() -> Poly:
    """Sitzende Katze im Profil mit hochgebogenem Schwanz, Höhe 1, steht auf y = −0.5."""
    pts = chain(
        [(-0.22, -0.50)],
        bez((-0.22, -0.50), (-0.32, -0.18), (-0.15, 0.05), 10),                  # Rücken
        bez((-0.15, 0.05), (-0.12, 0.12), (-0.14, 0.22), 4),                     # Hals hinten
        [(-0.16, 0.42), (-0.07, 0.31)],                                          # Ohr hinten
        bez((-0.07, 0.31), (-0.01, 0.33), (0.05, 0.31), 4),
        [(0.11, 0.42), (0.11, 0.22)],                                            # Ohr vorn
        bez((0.11, 0.22), (0.12, 0.12), (0.05, 0.08), 5),                        # Kinn
        bez((0.05, 0.08), (0.17, -0.10), (0.13, -0.46), 10),                     # Brust/Vorderpfote
        bez((0.13, -0.46), (0.30, -0.42), (0.38, -0.30), 6),                     # Schwanz innen
        bez((0.38, -0.30), (0.42, -0.14), (0.34, -0.02), 8),                     # nach oben
        bez((0.34, -0.02), (0.29, 0.06), (0.33, 0.11), 5),                       # Spitze
        bez((0.33, 0.11), (0.40, 0.08), (0.42, -0.02), 5),
        bez((0.42, -0.02), (0.52, -0.20), (0.46, -0.38), 8),                     # außen zurück
        bez((0.46, -0.38), (0.42, -0.50), (0.30, -0.53), 6),
    )
    pts = dedupe(pts, 0.004)
    return list(reversed(pts)) if signed_area(pts) < 0 else pts


def hat_unit() -> Poly:
    """Hexenhut, Breite 1, Mitte 0/0 (Krempe unten)."""
    pts = chain(
        bez((-0.50, -0.30), (-0.20, -0.42), (0.0, -0.40), 8),
        bez((0.0, -0.40), (0.25, -0.40), (0.50, -0.28), 8),
        [(0.47, -0.25)],
        bez((0.47, -0.25), (0.30, -0.24), (0.22, -0.22), 4),
        bez((0.22, -0.22), (0.16, 0.05), (0.10, 0.20), 8),
        bez((0.10, 0.20), (0.15, 0.35), (0.32, 0.36), 8),                         # geknickte Spitze
        bez((0.32, 0.36), (0.12, 0.42), (0.02, 0.26), 8),
        bez((0.02, 0.26), (-0.10, 0.05), (-0.22, -0.22), 8),
        bez((-0.22, -0.22), (-0.32, -0.24), (-0.47, -0.25), 4),
    )
    return dedupe(pts, 0.004)


def pumpkin(cx: float, y0: float, w: float, h: float, lobes: int = 5, stem: bool = True) -> Poly:
    """Kürbis mit Rippen-Buckeln und Stiel, steht auf y0."""
    rx, ry = w / 2, h / 2
    cy = y0 + ry
    pts: Poly = []
    n = 120
    for i in range(n):
        t = -math.pi / 2 + 2 * math.pi * i / n
        bump = 1 + 0.035 * abs(math.cos(lobes * (t + math.pi / 2) / 2)) - 0.03
        x = cx + rx * math.cos(t) * bump
        y = cy + ry * math.sin(t) * (0.96 + 0.04 * math.cos(2 * t))
        y = max(y, y0) if i == 0 else y
        pts.append((x, y))
    if stem:
        sw = 0.11 * w
        top = cy + ry * 0.92
        # Stiel als Ausstülpung oben (leicht gebogen)
        k = min(range(n), key=lambda i: abs(pts[i][0] - (cx + sw / 2)) + (0 if pts[i][1] > cy else 1e9))
        j = min(range(n), key=lambda i: abs(pts[i][0] - (cx - sw / 2)) + (0 if pts[i][1] > cy else 1e9))
        stem_pts = [(cx + sw / 2, top), (cx + sw * 0.55, top + 0.18 * h), (cx + sw * 0.9, top + 0.26 * h),
                    (cx + sw * 0.45, top + 0.27 * h), (cx - sw * 0.25, top + 0.16 * h), (cx - sw / 2, top)]
        pts = pts[:k] + stem_pts + pts[j + 1:]
    return dedupe(pts, 0.1)


def pumpkin_face(kind: str, cx: float, cy: float, w: float, h: float) -> List[Poly]:
    """Geschnitztes Gesicht als Löcher (Mittelpunkt cx/cy, Gesichtsbreite w, -höhe h)."""
    holes: List[Poly] = []
    ex = 0.24 * w
    if kind == "klassisch":
        for s in (1, -1):
            holes.append([(cx + s * ex - 0.12 * w, cy + 0.08 * h), (cx + s * ex + 0.12 * w, cy + 0.08 * h),
                          (cx + s * ex, cy + 0.34 * h)])
        holes.append([(cx - 0.07 * w, cy - 0.06 * h), (cx + 0.07 * w, cy - 0.06 * h), (cx, cy + 0.08 * h)])
        m = [(cx - 0.40 * w, cy - 0.14 * h)]
        top = [(cx - 0.40 * w, cy - 0.14 * h), (cx - 0.22 * w, cy - 0.22 * h), (cx - 0.16 * w, cy - 0.15 * h),
               (cx - 0.10 * w, cy - 0.24 * h), (cx + 0.10 * w, cy - 0.24 * h), (cx + 0.16 * w, cy - 0.15 * h),
               (cx + 0.22 * w, cy - 0.22 * h), (cx + 0.40 * w, cy - 0.14 * h)]
        bot = bez((cx + 0.40 * w, cy - 0.14 * h), (cx + 0.10 * w, cy - 0.56 * h), (cx - 0.06 * w, cy - 0.44 * h), 8)
        bot = bot + [(cx - 0.04 * w, cy - 0.33 * h), (cx - 0.12 * w, cy - 0.40 * h)]
        bot += bez((cx - 0.12 * w, cy - 0.40 * h), (cx - 0.30 * w, cy - 0.36 * h), (cx - 0.40 * w, cy - 0.14 * h), 6)[1:-1]
        holes.append(dedupe(top + bot, 0.1))
    elif kind == "gruselig":
        for s in (1, -1):
            holes.append([(cx + s * 0.08 * w, cy + 0.12 * h), (cx + s * 0.38 * w, cy + 0.30 * h),
                          (cx + s * 0.33 * w, cy + 0.10 * h), (cx + s * 0.18 * w, cy + 0.04 * h)])
        holes.append([(cx, cy + 0.06 * h), (cx + 0.06 * w, cy - 0.08 * h), (cx - 0.06 * w, cy - 0.08 * h)])
        # breites Maul mit Fangzähnen
        top = []
        xs = [-0.44, -0.30, -0.24, -0.16, -0.08, 0.0, 0.08, 0.16, 0.24, 0.30, 0.44]
        for i, x in enumerate(xs):
            y = -0.14 - 0.10 * (1 - (x / 0.44) ** 2) * 0
            top.append((cx + x * w, cy + (y - (0.10 if i in (2, 8) else 0.0) - 0.02 * (1 - abs(x) / 0.44)) * h))
        top = [(cx - 0.44 * w, cy - 0.12 * h), (cx - 0.26 * w, cy - 0.20 * h), (cx - 0.22 * w, cy - 0.34 * h),
               (cx - 0.17 * w, cy - 0.21 * h), (cx + 0.17 * w, cy - 0.21 * h), (cx + 0.22 * w, cy - 0.34 * h),
               (cx + 0.26 * w, cy - 0.20 * h), (cx + 0.44 * w, cy - 0.12 * h)]
        bot = [(cx + 0.36 * w, cy - 0.32 * h), (cx + 0.12 * w, cy - 0.44 * h), (cx + 0.08 * w, cy - 0.32 * h),
               (cx + 0.02 * w, cy - 0.46 * h), (cx - 0.12 * w, cy - 0.46 * h), (cx - 0.16 * w, cy - 0.34 * h),
               (cx - 0.22 * w, cy - 0.44 * h), (cx - 0.36 * w, cy - 0.32 * h)]
        holes.append(top + bot)
    elif kind == "froehlich":
        for s in (1, -1):
            holes.append(_ellipse_pts(cx + s * ex, cy + 0.20 * h, 0.09 * w, 0.12 * h, 0, 2 * math.pi, 28)[:-1])
        holes.append(_ellipse_pts(cx, cy, 0.05 * w, 0.05 * h, 0, 2 * math.pi, 16)[:-1])
        up = bez((cx - 0.38 * w, cy - 0.10 * h), (cx, cy - 0.30 * h), (cx + 0.38 * w, cy - 0.10 * h), 14)
        lo = bez((cx + 0.38 * w, cy - 0.10 * h), (cx, cy - 0.62 * h), (cx - 0.38 * w, cy - 0.10 * h), 14)
        holes.append(dedupe(up + lo[1:-1], 0.1))
    elif kind == "katze":
        for s in (1, -1):
            e = [(cx + s * ex + 0.12 * w * math.cos(t), cy + 0.18 * h + 0.07 * h * math.sin(t) *
                  (1 if math.sin(t) > 0 else 1)) for t in [2 * math.pi * i / 24 for i in range(24)]]
            holes.append([(x, y + (0.04 * h if (x - cx) * s < ex else 0) * math.copysign(1, y - cy - 0.18 * h)
                           * 0) for x, y in e])
        holes.append([(cx - 0.06 * w, cy + 0.02 * h), (cx + 0.06 * w, cy + 0.02 * h), (cx, cy - 0.06 * h)])
        m1 = bez((cx - 0.20 * w, cy - 0.16 * h), (cx - 0.10 * w, cy - 0.30 * h), (cx, cy - 0.12 * h), 8)
        m2 = bez((cx, cy - 0.12 * h), (cx + 0.10 * w, cy - 0.30 * h), (cx + 0.20 * w, cy - 0.16 * h), 8)
        m3 = bez((cx + 0.20 * w, cy - 0.16 * h), (cx + 0.10 * w, cy - 0.38 * h), (cx, cy - 0.20 * h), 8)
        m4 = bez((cx, cy - 0.20 * h), (cx - 0.10 * w, cy - 0.38 * h), (cx - 0.20 * w, cy - 0.16 * h), 8)
        holes.append(dedupe(m1 + m2[1:] + m3[1:] + m4[1:-1], 0.1))
    else:
        raise ValueError(f"Gesicht {kind!r} unbekannt")
    return holes


# --------------------------------------------------------------------------------------------------
# Baum
# --------------------------------------------------------------------------------------------------

def tree(x0: float, h: float, seed: int, lean: float = 0.0, min_w: float = 1.6, spread: float = 1.0,
         depth: int = 6, width: Optional[float] = None, reach: float = 1.0,
         allow: Optional[Callable[[Point], bool]] = None) -> Poly:
    """Knorriger, kahler Baum mit verzweigten Ästen. Steht auf y = 0 bei x0, Höhe ~h.
    Die Äste verdicken sich an jeder Gabel (wie echte Astansätze). Kontur gegen den Uhrzeigersinn."""
    rng = random.Random(seed)
    wt = width or max(0.065 * h, 4 * min_w)

    def branch(base_r: Point, base_l: Point, ang: float, L: float, lvl: int) -> Poly:
        bx, by = (base_r[0] + base_l[0]) / 2, (base_r[1] + base_l[1]) / 2
        wb = dist(base_r, base_l)
        we = wb * rng.uniform(0.70, 0.80)
        bend = rng.uniform(-0.35, 0.35)
        if allow is not None:
            # Ast drehen oder kürzen, bis er (mit Spitze) im erlaubten Bereich bleibt
            def fits(a_, Lf):
                ca, sa = math.cos(a_), math.sin(a_)
                for t in (0.35, 0.6, 0.8, 1.0, 1.0 + 2.6 * wb / max(Lf, 1e-6)):
                    cxp, cyp = bx + Lf * t * ca, by + Lf * t * sa
                    for o in (-0.6 * wb - 0.5, 0.0, 0.6 * wb + 0.5):
                        if not allow((cxp - sa * o, cyp + ca * o)):
                            return False
                return True
            found = None
            for f in (1.0, 0.82, 0.66):
                for da in (0.0, 0.22, -0.22, 0.45, -0.45):
                    a_ = ang + da
                    if math.radians(-20) <= a_ <= math.radians(200) and fits(a_, L * f):
                        found = (a_, f)
                        break
                if found:
                    break
            if found is None:
                for f in (0.5, 0.36, 0.24):
                    if fits(ang, L * f):
                        found = (ang, f)
                        break
            if found is None:
                found = (ang, 0.16)
            ang, f = found
            if f < 1.0:
                L *= f
                lvl = lvl if f >= 0.66 else min(lvl, 1 if f >= 0.36 else 0)
        ex, ey = bx + L * math.cos(ang), by + L * math.sin(ang)
        mx, my = bx + L * 0.5 * math.cos(ang + bend), by + L * 0.5 * math.sin(ang + bend)
        center = bez((bx, by), (mx, my), (ex, ey), max(4, int(L / 3)))
        child_w = we * 0.75
        k = 3 if (lvl >= 3 and rng.random() < 0.3) else 2
        tip_end = lvl == 0 or child_w < min_w
        w_end = we if tip_end else max(we, k * child_w * 0.96)
        r_side, l_side = strip(center, wb, w_end)
        r_side[0], l_side[0] = base_r, base_l
        if tip_end:
            tw = max(min_w, we)
            r_side, l_side = strip(center, wb, tw)
            r_side[0], l_side[0] = base_r, base_l
            d = (ex - center[-2][0], ey - center[-2][1])
            dl = math.hypot(*d) or 1
            tip = (ex + d[0] / dl * tw * 2.2, ey + d[1] / dl * tw * 2.2)
            return r_side + [tip] + list(reversed(l_side))
        R, Lp = r_side[-1], l_side[-1]
        spreads = [-0.62, 0.55] if k == 2 else [-0.75, 0.05, 0.7]
        if rng.random() < 0.5:
            spreads = [v + rng.uniform(-0.2, 0.2) for v in spreads]
        out = list(r_side)
        for i in range(k):
            t0, t1 = i / k, (i + 1) / k
            cr = (R[0] + (Lp[0] - R[0]) * t0, R[1] + (Lp[1] - R[1]) * t0)
            cl = (R[0] + (Lp[0] - R[0]) * t1, R[1] + (Lp[1] - R[1]) * t1)
            a = ang + spread * spreads[i]
            # Äste streben leicht nach außen und oben
            a += 0.12 * (math.pi / 2 - a)
            a = max(math.radians(-15), min(math.radians(195), a))
            sub = branch(cr, cl, a, L * rng.uniform(0.66, 0.80), lvl - 1)
            out += sub[1:] if out and dist(out[-1], sub[0]) < 1e-9 else sub
        out += list(reversed(l_side))[1:]
        return out

    y_root = 0.06 * h
    trunk = branch((x0 + wt / 2, y_root), (x0 - wt / 2, y_root), math.pi / 2 + lean, 0.30 * h * reach, depth)
    root_r = bez((x0 + wt * 1.0, 0.0), (x0 + wt * 0.52, 0.01 * h), (x0 + wt / 2, y_root), 5)
    root_l = bez((x0 - wt / 2, y_root), (x0 - wt * 0.52, 0.01 * h), (x0 - wt * 1.0, 0.0), 5)
    pts = chain(root_r[:-1], trunk, root_l[1:])
    return dedupe(pts, 0.08)


def tree_ok(pts: Sequence[Point], web: float) -> bool:
    return polygon_ok(oriented(pts, True)) and min_gap(pts, 4) >= web


def good_tree(x0: float, h: float, seed: int, web: float, box: Callable[[Point], bool], **kw) -> Poly:
    """Ersten Baum (Startwerte seed, seed+1 …), der sich nicht selbst berührt und in 'box' passt.
    Passt keiner, wird der Baum schrittweise kleiner und schmaler."""
    for f, sp in ((1.0, 1.0), (0.92, 0.9), (0.84, 0.85), (0.76, 0.8), (0.68, 0.75), (0.6, 0.7), (0.5, 0.65)):
        for k in range(14):
            t = tree(x0, h * f, seed + 97 * k, **dict(kw, spread=sp, allow=box))
            if all(box(p) for p in t) and tree_ok(t, web):
                return t
    raise ValueError("Baum passt nicht – Szene größer wählen")


# --------------------------------------------------------------------------------------------------
# Szenen-Elemente: (Kontur auf y=0 von links nach rechts, Löcher, Gravur-Hinweise)
# Einheit: mm, x relativ zur Elementmitte
# --------------------------------------------------------------------------------------------------

Element = Dict[str, object]


def _window_holes(kind: str, cx: float, y: float, w: float, h: float) -> Poly:
    if kind == "spitz":
        hh = h - w * 0.75
        pts = [(cx - w / 2, y), (cx + w / 2, y), (cx + w / 2, y + hh)]
        pts += bez((cx + w / 2, y + hh), (cx + w / 2, y + h * 0.92), (cx, y + h), 6)[1:]
        pts += bez((cx, y + h), (cx - w / 2, y + h * 0.92), (cx - w / 2, y + hh), 6)[1:]
        return dedupe(pts, 0.1)
    if kind == "rund":
        return [(cx + w / 2 * math.cos(t), y + h / 2 + w / 2 * math.sin(t)) for t in
                [2 * math.pi * i / 28 for i in range(28)]]
    return rect(cx - w / 2, y, w, h)


def mansion(w: float, h: float, seed: int, min_w: float) -> Element:
    """Spukhaus: links ein Rundturm mit schiefem Kegeldach, in der Mitte das Haupthaus mit steilem
    Giebel und Schornstein, rechts ein hoher Wehrturm mit Zinnen und Spitzhelm.
    Liefert die Silhouette als Linie von links unten nach rechts unten (Mitte x = 0)."""
    u = w
    L0, L1 = -0.50 * u, -0.27 * u           # linker Turm
    H0, H1 = L1, 0.22 * u                   # Haupthaus
    T0, T1 = H1, 0.50 * u                   # rechter Turm
    lt_wall, lt_tip = 0.56 * h, 0.90 * h
    eave, ridge_y = 0.44 * h, 0.80 * h
    ridge_x = (H0 + H1) / 2
    tt_wall = 0.78 * h

    def roof_y(x):
        return eave + (ridge_y - eave) * (1 - abs(x - ridge_x) / ((H1 - H0) / 2))

    pts: Poly = [(L0, 0.0), (L0, lt_wall), (L0 - 0.035 * u, lt_wall - 0.01 * h)]
    tip = (L0 + 0.06 * u, lt_tip)                                   # schief nach links
    pts += bez((L0 - 0.035 * u, lt_wall - 0.01 * h), (L0 + 0.05 * u, lt_wall + 0.12 * h), tip, 6)[1:]
    pts += bez(tip, (L1 - 0.02 * u, lt_wall + 0.10 * h), (L1 + 0.035 * u, lt_wall - 0.01 * h), 6)[1:]
    pts += [(L1, lt_wall + 0.012 * h), (L1, roof_y(L1 + 1e-6))]
    # Schornstein auf der linken Dachseite
    c0, c1 = H0 + 0.16 * (H1 - H0), H0 + 0.26 * (H1 - H0)
    pts += [(c0, roof_y(c0)), (c0, 0.80 * h), (c0 - 0.012 * u, 0.80 * h), (c0 - 0.012 * u, 0.835 * h),
            (c1 + 0.012 * u, 0.835 * h), (c1 + 0.012 * u, 0.80 * h), (c1, 0.80 * h), (c1, roof_y(c1))]
    pts += [(ridge_x, ridge_y), (H1, roof_y(H1 - 1e-6))]
    # rechter Turm: Wand, Konsole, Zinnenkranz mit Spitzhelm in der Mitte
    pts += [(T0, tt_wall), (T0 - 0.02 * u, tt_wall + 0.02 * h)]
    zy = tt_wall + 0.02 * h
    zt = zy + 0.06 * h
    n = 5
    xs = [T0 - 0.02 * u + (T1 - T0 + 0.04 * u) * k / (2 * n - 1) for k in range(2 * n)]
    s0, s1 = (T0 + T1) / 2 - 0.07 * u, (T0 + T1) / 2 + 0.07 * u
    spire_done = False
    for k in range(2 * n - 1):
        xa, xb = xs[k], xs[k + 1]
        up = k % 2 == 0
        if xb > s0 and xa < s1:
            if not spire_done:
                pts += [(max(xa, s0 - 0.01 * u), zt if up else zy)] if xa < s0 else []
                pts += [(s0, zt), ((T0 + T1) / 2, h), (s1, zt)]
                spire_done = True
            continue
        y = zt if up else zy
        if pts and abs(pts[-1][1] - y) > 1e-9:
            pts.append((xa, y))
        else:
            pts.append((xa, y))
        pts.append((xb, y))
    pts += [(T1 + 0.02 * u, zy), (T1 + 0.02 * u, zy)] [:1]
    pts += [(T1, tt_wall), (T1, 0.0)]
    pts = dedupe(pts, 0.1, closed=False)
    # orthogonale Zinnen-Treppen sauber machen (keine doppelten Richtungswechsel)
    clean_pts: Poly = []
    for p in pts:
        if len(clean_pts) >= 2:
            a, b = clean_pts[-2], clean_pts[-1]
            if abs((b[0] - a[0]) * (p[1] - b[1]) - (b[1] - a[1]) * (p[0] - b[0])) < 1e-9 and \
                    (b[0] - a[0]) * (p[0] - b[0]) + (b[1] - a[1]) * (p[1] - b[1]) > 0:
                clean_pts[-1] = p
                continue
        clean_pts.append(p)
    pts = clean_pts

    holes: List[Poly] = []
    ww = max(0.055 * u, 3.0 + 2 * min_w)
    for k in range(3):
        x = H0 + (k + 0.5) * (H1 - H0) / 3
        if k != 1:
            holes.append(_window_holes("spitz", x, 0.07 * h, ww, 0.14 * h))
        holes.append(_window_holes("spitz", x, 0.26 * h, ww, 0.12 * h))
    holes.append(_window_holes("spitz", ridge_x, 0.02 * h + min_w * 1.5, 0.10 * u, 0.20 * h))     # Tür
    holes.append(_window_holes("rund", ridge_x, 0.53 * h, 0.075 * u, 0.075 * u))
    for y in (0.16 * h, 0.38 * h, 0.58 * h):
        holes.append(_window_holes("spitz", (T0 + T1) / 2, y, ww, 0.12 * h))
    for y in (0.22 * h, 0.40 * h):
        holes.append(_window_holes("spitz", (L0 + L1) / 2, y, ww * 0.8, 0.10 * h))
    return dict(poly=pts, holes=holes,
                walls=[(H0, 0.0, H1, eave), (T0, 0.0, T1, tt_wall), (L0, 0.0, L1, lt_wall)],
                roofs=[(H0, eave, H1, ridge_y), (L0, lt_wall, L1, lt_tip)])


def tombstone(kind: str, w: float, h: float) -> Poly:
    """Grabstein-Kontur auf y = 0 (Mitte x = 0)."""
    if kind == "rund":
        r = w / 2
        return dedupe([(-r, 0.0), (r, 0.0)] + arc(0, h - r, r, 0, math.pi, 16), 0.1)
    if kind == "gotisch":
        hh = h - w * 0.8
        pts = [(-w / 2, 0.0), (w / 2, 0.0), (w / 2, hh)]
        pts += bez((w / 2, hh), (w * 0.48, h * 0.86), (0, h), 8)[1:]
        pts += bez((0, h), (-w * 0.48, h * 0.86), (-w / 2, hh), 8)[1:]
        return dedupe(pts, 0.1)
    if kind == "kreuz":
        b = w * 0.32
        arm = h * 0.62
        return [(-b / 2, 0.0), (b / 2, 0.0), (b / 2, arm), (w / 2, arm), (w / 2, arm + b), (b / 2, arm + b),
                (b / 2, h), (-b / 2, h), (-b / 2, arm + b), (-w / 2, arm + b), (-w / 2, arm), (-b / 2, arm)]
    if kind == "schief":
        return dedupe([(-w / 2, 0.0), (w / 2, 0.0), (w / 2, h * 0.70)] +
                      bez((w / 2, h * 0.70), (w * 0.35, h * 1.0), (-w * 0.05, h * 0.93), 8)[1:] +
                      [(-w * 0.12, h * 0.80), (-w * 0.22, h * 0.86)] +
                      bez((-w * 0.22, h * 0.86), (-w * 0.45, h * 0.80), (-w / 2, h * 0.62), 6)[1:], 0.1)
    raise ValueError(kind)


def fence(x0: float, x1: float, h: float, bar: float, gap: float) -> Poly:
    """Schmiedeeiserner Zaun mit Lanzenspitzen zwischen x0 und x1 (Kontur ohne Unterkante)."""
    n = max(2, int((x1 - x0 + gap) / (bar + gap)))
    step = (x1 - x0 - bar) / (n - 1)
    o = max(0.0, min(bar * 0.6, (step - bar) / 2 - 0.8))       # Überstand der Spitzen, ohne dass sie sich berühren
    pts: Poly = [(x0, 0.0)]
    for i in range(n):
        a = x0 + i * step
        b = a + bar
        if i == 0:
            pts += [(a, h * 0.82), ((a + b) / 2, h), (b + o, h * 0.82), (b, h * 0.82)]
        elif i == n - 1:
            pts += [(a, h * 0.82), (a - o, h * 0.82), ((a + b) / 2, h), (b, h * 0.82)]
        else:
            pts += [(a, h * 0.82), (a - o, h * 0.82), ((a + b) / 2, h), (b + o, h * 0.82), (b, h * 0.82)]
        if i < n - 1:
            na = x0 + (i + 1) * step
            pts += [(b, 0.64 * h), (na, 0.64 * h)]
    pts += [(x1, 0.0)]
    return dedupe(pts, 0.05, False)


def fence_holes(x0: float, x1: float, h: float, bar: float, gap: float) -> List[Poly]:
    """Zwischenräume unter dem oberen Riegel (über dem unteren Riegel)."""
    n = max(2, int((x1 - x0 + gap) / (bar + gap)))
    step = (x1 - x0 - bar) / (n - 1)
    out = []
    lo, hi = 0.14 * h, 0.64 * h - bar
    for i in range(n - 1):
        a = x0 + i * step + bar
        b = x0 + (i + 1) * step
        if b - a > 1.0 and hi - lo > 2.0:
            out.append(rect(a, lo, b - a, hi - lo))
    return out


def web(cx: float, cy: float, R: float, a0: float, a1: float, rings: int, spokes: int, thread: float
        ) -> Tuple[Poly, List[Poly]]:
    """Spinnennetz als Fächer um (cx, cy) von Winkel a0 bis a1 (Bogenmaß).
    Die Ringfäden hängen zwischen den Speichen zur Mitte hin durch. Liefert (Außenkontur des
    Netzes, Löcher zwischen den Fäden); zwischen allen Löchern bleibt mindestens 'thread' Material."""
    angs = [a0 + (a1 - a0) * i / spokes for i in range(spokes + 1)]
    radii = [R * (0.20 + 0.80 * (k / rings) ** 0.9) for k in range(1, rings + 1)]
    sag = 0.13
    t = thread * 1.12

    def r_eff(r, a):
        i = min(spokes - 1, max(0, int((a - a0) / (a1 - a0) * spokes)))
        u = (a - angs[i]) / (angs[i + 1] - angs[i])
        return r * (1 - 0.22 * (angs[1] - angs[0]) * math.sin(math.pi * max(0.0, min(1.0, u))))

    def P(r, a):
        return (cx + r * math.cos(a), cy + r * math.sin(a))

    def ring_full(r, off, n=24):
        """ganzer Ringfaden (alle Speichen), um 'off' entlang der Normalen versetzt (+ = außen).
        Liefert Liste von (Winkel, Punkt)."""
        pts = []
        for i in range(spokes):
            for j in range(n + (1 if i == spokes - 1 else 0)):
                a = angs[i] + (angs[i + 1] - angs[i]) * j / n
                pts.append(P(r_eff(r, a), a))
        rgt, lft = strip(pts, 2 * abs(off), 2 * abs(off))      # Laufrichtung = gegen Uhrzeigersinn
        side = rgt if off > 0 else lft                         # rechts der Laufrichtung = außen
        return [(math.atan2(q[1] - cy, q[0] - cx), q) for q in side]

    def ring(r, aa, ab, off):
        mid = (aa + ab) / 2
        seg = []
        for a, q in ring_full(r, off):
            a += 2 * math.pi * round((mid - a) / (2 * math.pi))
            if aa <= a <= ab:
                seg.append((a, q))
        return [q for a, q in sorted(seg)]

    outer: Poly = [(cx, cy)] + [q for a, q in ring_full(radii[-1], thread / 2)]
    holes: List[Poly] = []
    for k in range(rings):
        r_in = radii[k - 1] if k > 0 else 0.0
        r_out = radii[k]
        for i in range(spokes):
            aa, ab = angs[i], angs[i + 1]
            rr = max(r_in * (1 - 0.22 * (angs[1] - angs[0])), t)
            da = (t / 2) / rr * 1.05
            ia = aa + da * (2.0 if i == 0 else 1.0)
            ib = ab - da * (2.0 if i == spokes - 1 else 1.0)
            if ib - ia < 0.03:
                continue
            out_seg = ring(r_out, ia, ib, -t / 2)
            if k == 0:
                rc = (t / 2) / math.sin((ab - aa) / 2) * 1.05
                inner = [P(rc, (aa + ab) / 2)]
            else:
                inner = list(reversed(ring(r_in, ia, ib, t / 2)))
            if len(out_seg) < 2 or (k > 0 and len(inner) < 2):
                continue
            cell = dedupe(out_seg + inner, 0.08)
            # Ecken am Speichenfaden: Abstand zur Speiche prüfen
            if len(cell) >= 3 and abs(signed_area(cell)) > 2.0 and polygon_ok(oriented(cell, True)) \
                    and hole_ok(cell, 0.3):
                holes.append(cell)
    return dedupe(outer, 0.08), holes


# Englische Texte für die Sprachwahl (ab Steckwerk 2.0.0; ältere Versionen ignorieren sie)
EN = {
    "Blatt und Ranke": "Leaf and tendril",
    "Efeuranke": "Ivy tendril",
    "Fledermaus, Gespenst, Totenkopf, Katze, Hexenhut, Kürbis, Spinnennetz – filigran, mit Öse.": "Bat, ghost, skull, cat, witch hat, pumpkin, spider web – filigree, with a hanging loop.",
    "Fledermaus-Silhouette": "Bat silhouette",
    "Fledermäuse": "Bats",
    "Fledermäuse vor dem Mond": "Bats against the moon",
    "Friedhof": "Graveyard",
    "Geschnitzter Kürbis mit Stiel, Blatt und Ranke – Gesicht oder Silhouette leuchtet mit Teelicht.": "Carved pumpkin with stem, leaf and tendril – the face or silhouette glows with a tea light.",
    "Gesicht": "Face",
    "Gespenst schaut hervor": "Ghost peeking out",
    "Gotischer Bogen mit Scherenschnitt-Szene, Mond, Fledermäusen, Spinnennetz und leuchtenden Fenstern.": "Gothic arch with a paper-cut scene, moon, bats, spider web and glowing windows.",
    "Grabspruch": "Epitaph",
    "Grabstein": "Gravestone",
    "Grabstein mit Grabspruch, Ornament, Rissen und Efeu – auf Wunsch mit Gespenst dahinter.": "Gravestone with epitaph, ornament, cracks and ivy – optionally with a ghost behind it.",
    "Halloween-Anhänger": "Halloween pendants",
    "Hexe und Fledermäuse": "Witch and bats",
    "Hexenhaus": "Witch's house",
    "Höhe ≈ 1,3 × Breite": "Height ≈ 1.3 × width",
    "Katzengesicht": "Cat face",
    "Kürbis-Leuchte": "Pumpkin lantern",
    "Leuchtende Kürbisse": "Glowing pumpkins",
    "Name (Gespenst, Kürbis, Hut)": "Name (ghost, pumpkin, hat)",
    "Ornament": "Ornament",
    "Rippen gravieren": "Engrave ribs",
    "Schrift": "Font",
    "Schrift und Beschriftung": "Font and lettering",
    "Spinnennetz": "Spider web",
    "Spinnennetz und Spinne": "Spider web and spider",
    "Spukhaus": "Haunted house",
    "Spukschloss-Fensterbild": "Haunted castle window picture",
    "Variante (Baum, Fledermäuse)": "Variant (tree, bats)",
    "Vor dem Mond": "Against the moon",
    "alle sieben (Set)": "all seven (set)",
    "andere Zahl = anders gewachsener Baum": "other number = differently grown tree",
    "fröhlich": "cheerful",
    "gotisch (Spitzbogen)": "gothic (pointed arch)",
    "gruselig mit Fangzähnen": "creepy with fangs",
    "größte Abmessung in mm": "largest dimension in mm",
    "klassisch (Dreiecke)": "classic (triangles)",
    "leer = ohne": "empty = none",
    "leer = ohne Text": "empty = no text",
    "nur der Mond": "just the moon",
    "schatten": "shadow",
    "schief abgebrochen": "broken off at an angle",
    "| = neue Zeile": "| = new line",
    "Hexe auf dem Besen": "Witch on a broom",
    "Text auf dem Sockel": "Text on the stand",
    "Kürbis": "Pumpkin",
    "Spukschloss": "Haunted castle",
    "Anhänger": "Pendant",
    "Anhänger an einem Faden durch die Öse aufhängen. Tipp: schwarz lasiert vor einem hellen Fenster wirken sie wie Scherenschnitte.": "Hang the pendants on a thread through the loop. Tip: stained black in front of a bright window they look like paper cuts.",
    "Stein in den Erdhügel stecken. Tipp: Stein mit grauer Lasur, Gravur dunkel auslegen – dann wirkt er wie verwittert.": "Plug the stone into the mound. Tip: grey stain on the stone and a dark-filled engraving make it look weathered.",
    "Kürbis in den Sockel stecken, LED-Teelicht dahinter stellen. Tipp: Rückseite mit orangem Transparentpapier bekleben, dann leuchtet das Gesicht warm.": "Plug the pumpkin into the stand and put an LED tea light behind it. Tip: glue orange tracing paper to the back and the face glows warmly.",
    "Bogen mit beiden Zapfen in die Bodenplatte stecken (bei Bedarf leimen). Eine LED-Lichterkette oder ein Teelicht im Glas dahinter lässt Fenster, Kürbisse, Fledermäuse und Hexe leuchten. Tipp: Rückseite mit orangem Transparentpapier bekleben.": "Plug the arch into the base plate with both tenons (glue if needed). An LED string or a tea light in a jar behind it makes windows, pumpkins, bats and witch glow. Tip: glue orange tracing paper to the back.",
    "Baum passt nicht – Szene größer wählen": "Tree does not fit – choose a larger scene",
    "Öse passt nicht – Anhänger größer wählen": "Loop does not fit – choose a larger pendant",
    "Gesicht passt nicht – Kürbis größer wählen": "Face does not fit – choose a larger pumpkin",
    "Szene passt nicht in den Bogen – größere Breite wählen": "Scene does not fit into the arch – choose a larger width",
    "Szene passt nicht unter den Bogen – größere Breite wählen": "Scene does not fit under the arch – choose a larger width",
    "Schrift oder Schreibweise unbekannt": "Unknown font or letter case"
}
