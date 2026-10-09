"""
_shapes.py – Formbausteine für Anhänger und Steckfiguren.

  union_circle    Aufhänge-Öse (Kreis) an eine Kontur anfügen
  cut_axis_slot   Kreuzschlitz entlang der senkrechten Achse (für 3D-Steckversionen)
  fill_pattern    Muster-Gravuren / Filigran-Durchbrüche innerhalb eines Bereichs
  star            Sternpolygon
"""
from __future__ import annotations

import math
import random
from typing import List, Optional, Sequence, Tuple

from laserforge import (Part, Point, arc_points, circle, clean, clip_segment, dist, dist_to_boundary,
                        inset_polygon, oriented, point_in_polygon, polygon_ok, rect)


def star(cx: float, cy: float, r_out: float, r_in: float, n: int = 5, rot: float = math.pi / 2) -> List[Point]:
    return [(cx + (r_out if k % 2 == 0 else r_in) * math.cos(rot + k * math.pi / n),
             cy + (r_out if k % 2 == 0 else r_in) * math.sin(rot + k * math.pi / n)) for k in range(2 * n)]


def _circle_hits(poly: Sequence[Point], cx: float, cy: float, r: float):
    """Schnittpunkte Kreis/Kontur als (kantenindex, t, punkt), in Laufrichtung sortiert."""
    hits = []
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        dx, dy = b[0] - a[0], b[1] - a[1]
        fx, fy = a[0] - cx, a[1] - cy
        A = dx * dx + dy * dy
        B = 2 * (fx * dx + fy * dy)
        C = fx * fx + fy * fy - r * r
        disc = B * B - 4 * A * C
        if A < 1e-18 or disc < 0:
            continue
        sq = math.sqrt(disc)
        for t in sorted(((-B - sq) / (2 * A), (-B + sq) / (2 * A))):
            if 0.0 <= t < 1.0:
                hits.append((i, t, (a[0] + t * dx, a[1] + t * dy)))
    return hits


def union_circle(poly: Sequence[Point], cx: float, cy: float, r: float, tol: float = 0.05) -> List[Point]:
    """Vereinigung einer CCW-Kontur mit einem Kreis, der sie genau zweimal schneidet."""
    poly = oriented(poly, True)
    hits = _circle_hits(poly, cx, cy, r)
    if len(hits) != 2:
        raise ValueError(f"Öse schneidet die Kontur {len(hits)}× statt 2×")
    (i1, _, p1), (i2, _, p2) = hits
    n = len(poly)
    # Kette p1 → p2 (Laufrichtung) und Kette p2 → p1
    chain_a = [p1] + [poly[(k) % n] for k in range(i1 + 1, i2 + 1)] + [p2]
    chain_b = [p2] + [poly[k % n] for k in range(i2 + 1, i1 + n + 1)] + [p1]

    def outside(chain):
        mids = chain[1:-1] or [((chain[0][0] + chain[-1][0]) / 2, (chain[0][1] + chain[-1][1]) / 2)]
        return sum(1 for p in mids if math.hypot(p[0] - cx, p[1] - cy) > r) >= len(mids) / 2

    keep = chain_a if outside(chain_a) else chain_b
    s, e = keep[0], keep[-1]                                   # Bogen von e zurück nach s
    a_e = math.atan2(e[1] - cy, e[0] - cx)
    a_s = math.atan2(s[1] - cy, s[0] - cx)
    while a_s <= a_e:
        a_s += 2 * math.pi
    arc = arc_points(cx, cy, r, a_e, a_s, tol)                 # gegen den Uhrzeigersinn
    mid = arc[len(arc) // 2]
    if point_in_polygon(mid, poly):                            # falsche Seite → andersherum
        arc = arc_points(cx, cy, r, a_e, a_s - 2 * math.pi, tol)
    return drop_close(clean(keep + arc[1:-1]), 0.15)


def drop_close(pts: Sequence[Point], d: float, keep: Sequence[Point] = ()) -> List[Point]:
    """Entfernt Knoten, die näher als d am vorigen liegen (z. B. Schnittpunkt dicht neben einem
    Eckpunkt) – sonst entstehen nach der Kerf-Kompensation Mini-Segmente. 'keep' bleibt erhalten."""
    prot = {(round(p[0], 9), round(p[1], 9)) for p in keep}
    is_p = lambda p: (round(p[0], 9), round(p[1], 9)) in prot
    out: List[Point] = []
    for p in pts:
        if out and dist(out[-1], p) < d:
            if is_p(p) and not is_p(out[-1]):
                out[-1] = p
            continue
        out.append(p)
    while len(out) > 3 and dist(out[-1], out[0]) < d:
        if is_p(out[-1]) and not is_p(out[0]):
            out[0] = out[-1]
        out.pop()
    return out


def _vertical_hits(poly: Sequence[Point], x: float):
    out = []
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        if (a[0] - x) * (b[0] - x) < 0 or (a[0] == x and b[0] != x):
            t = (x - a[0]) / (b[0] - a[0])
            out.append((i, (x, a[1] + t * (b[1] - a[1]))))
    return out


def cut_axis_slot(poly: Sequence[Point], width: float, y_mid: float, from_top: bool) -> Tuple[List[Point], List[Point]]:
    """Schneidet einen Schlitz der Breite 'width' entlang x = 0 von oben (oder unten) bis y_mid.
    Liefert (neue CCW-Kontur, Schlitz-Eckpunkte für das halving-Feature)."""
    poly = oriented(clean(poly), True)
    hw = width / 2
    hr, hl = _vertical_hits(poly, hw), _vertical_hits(poly, -hw)
    if not hr or not hl:
        raise ValueError("Schlitz trifft die Kontur nicht")
    pick = max if from_top else min
    ir, pr = pick(hr, key=lambda h: h[1][1])
    il, pl = pick(hl, key=lambda h: h[1][1])
    n = len(poly)
    if from_top:
        # behalten: pl → (links runter, unten, rechts hoch) → pr
        chain = [pl] + [poly[k % n] for k in range(il + 1, (ir if ir > il else ir + n) + 1)] + [pr]
        slot = [pr, (hw, y_mid), (-hw, y_mid), pl]
        new = chain + slot[1:3]
    else:
        chain = [pr] + [poly[k % n] for k in range(ir + 1, (il if il > ir else il + n) + 1)] + [pl]
        slot = [pl, (-hw, y_mid), (hw, y_mid), pr]
        new = chain + slot[1:3]
    return drop_close(clean(new), 0.15, keep=slot), slot


def fill_pattern(part: Part, region: Sequence[Point], kind: str, avoid: Sequence[Sequence[Point]] = (),
                 seed: int = 1, scale: float = 1.0, cut_web: float = 1.6) -> int:
    """Füllt 'region' mit einem Muster. Gravur: punkte, streifen, sterne, flocken, herzen, tannen,
    karo, wellen. Schnitt: filigran.
    'avoid' sind Sperrflächen (Text, Öse, Schlitz). Liefert die Anzahl der Elemente."""
    if kind in ("keins", "rand", None) or len(region) < 3 or not polygon_ok(oriented(region, True)):
        return 0
    region = oriented(region, True)
    rng = random.Random(seed)
    xs = [p[0] for p in region]
    ys = [p[1] for p in region]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    count = 0

    def free(pts, margin):
        for p in pts:
            if not point_in_polygon(p, region) or dist_to_boundary(p, region) < margin:
                return False
            for av in avoid:
                if point_in_polygon(p, av) or dist_to_boundary(p, av) < margin:
                    return False
        return True

    if kind == "streifen":
        step = 4.5 * scale
        c = x0 - (y1 - y0)
        while c < x1:
            for a, b in clip_segment((c, y0 - 1), (c + (y1 - y0) + 2, y1 + 1), region, avoid):
                if dist(a, b) > 1.0:
                    part.add_engrave([a, b])
                    count += 1
            c += step
        return count
    if kind in ("karo", "wellen"):
        step = (5.0 if kind == "karo" else 4.2) * scale
        lines = []
        if kind == "karo":
            span = (x1 - x0) + (y1 - y0)
            c = -span
            while c < span:
                lines.append([(x0 + c, y0 - 1), (x0 + c + (y1 - y0) + 2, y1 + 1)])
                lines.append([(x1 - c, y0 - 1), (x1 - c - (y1 - y0) - 2, y1 + 1)])
                c += step
        else:
            y = y0 + step / 2
            while y < y1:
                n = max(8, int((x1 - x0) / 0.6))
                lines.append([(x0 - 1 + (x1 - x0 + 2) * i / n,
                               y + 0.28 * step * math.sin(2 * math.pi * (x0 + (x1 - x0) * i / n) / (2.2 * step)))
                              for i in range(n + 1)])
                y += step
        for ln in lines:
            run: List[Point] = []
            for a, b in zip(ln, ln[1:]):
                for s, e in clip_segment(a, b, region, avoid):
                    if run and dist(run[-1], s) < 1e-7:
                        run.append(e)
                    else:
                        if len(run) >= 2 and dist(run[0], run[-1]) > 1.0:
                            part.add_engrave(run)
                            count += 1
                        run = [s, e]
            if len(run) >= 2 and dist(run[0], run[-1]) > 1.0:
                part.add_engrave(run)
                count += 1
        return count
    grid = {"punkte": 5.0, "sterne": 8.0, "flocken": 9.0, "filigran": 7.0, "herzen": 8.0,
            "tannen": 9.0}.get(kind)
    if grid is None:
        raise ValueError(f"Unbekanntes Muster {kind!r}")
    g = grid * scale
    placed: List[Tuple[float, float, float]] = []      # (x, y, Umkreisradius) gesetzter Durchbrüche
    centers: List[Point] = []                          # Mittelpunkte gesetzter Gravur-Symbole

    def symbol(cx: float, cy: float) -> bool:
        """Ein graviertes Symbol setzen, falls frei."""
        if kind == "punkte":
            items = [(circle(cx, cy, 0.7 * scale), True)]
        elif kind == "sterne":
            r = rng.uniform(1.6, 2.4) * scale
            items = [(star(cx, cy, r, 0.45 * r, 5, math.pi / 2 + rng.uniform(-0.3, 0.3)), True)]
        elif kind == "flocken":
            r = rng.uniform(2.0, 2.8) * scale
            items = []
            for k in range(3):
                a = math.pi / 2 + k * math.pi / 3
                items.append(([(cx - r * math.cos(a), cy - r * math.sin(a)),
                               (cx + r * math.cos(a), cy + r * math.sin(a))], False))
        elif kind == "herzen":
            from models._deko import heart
            r = rng.uniform(1.6, 2.3) * scale
            items = [(heart(cx, cy, 2.0 * r, 1.8 * r, 32), True)]
        else:                                                   # tannen
            r = rng.uniform(1.6, 2.3) * scale
            h, w = 2.4 * r, 1.6 * r
            items = [([(cx, cy + h / 2), (cx + 0.32 * w, cy + 0.12 * h), (cx + 0.18 * w, cy + 0.12 * h),
                       (cx + 0.5 * w, cy - 0.3 * h), (cx + 0.08 * w, cy - 0.3 * h), (cx + 0.08 * w, cy - h / 2),
                       (cx - 0.08 * w, cy - h / 2), (cx - 0.08 * w, cy - 0.3 * h), (cx - 0.5 * w, cy - 0.3 * h),
                       (cx - 0.18 * w, cy + 0.12 * h), (cx - 0.32 * w, cy + 0.12 * h)], True)]
        if not free([q for pts, _ in items for q in pts], 0.6):
            return False
        for pts, closed in items:
            part.add_engrave(pts, closed=closed)
        centers.append((cx, cy))
        return True

    row = 0
    y = y0 + g / 2
    while y < y1:
        x = x0 + g / 2 + (g / 2 if row % 2 else 0)
        while x < x1:
            jx, jy = (rng.uniform(-0.18, 0.18) * g, rng.uniform(-0.18, 0.18) * g) if kind != "punkte" else (0, 0)
            cx, cy = x + jx, y + jy
            if kind in ("punkte", "sterne", "flocken", "herzen", "tannen"):
                count += symbol(cx, cy)
            elif kind == "filigran":
                r = 0.28 * g
                is_star = (row + int(x)) % 3 == 0
                shape = star(cx, cy, r, 0.5 * r, 5) if is_star else circle(cx, cy, 0.62 * r)
                rc = r if is_star else 0.62 * r
                if free(shape, cut_web) and all(math.hypot(cx - px, cy - py) >= rc + pr + cut_web
                                                for px, py, pr in placed):
                    part.add_hole(shape)
                    placed.append((cx, cy, rc))
                    count += 1
            x += g
        y += g * 0.87
        row += 1
    if kind in ("sterne", "flocken", "herzen", "tannen"):
        # Lücken neben Text, Öse & Co. auffüllen – nur wo kein Nachbar näher als ~ein Raster liegt
        step = g / 3
        yy = y0 + step / 2
        while yy < y1:
            xx = x0 + step / 2
            while xx < x1:
                if all(math.hypot(xx - px, yy - py) >= 0.92 * g for px, py in centers):
                    count += symbol(xx, yy)
                xx += step
            yy += step
    return count


def border(part: Part, outline: Sequence[Point], d: float, avoid: Sequence[Sequence[Point]] = ()) -> bool:
    """Gravierte Randlinie im Abstand d (Lücken an Sperrflächen wie der Öse)."""
    ins = inset_polygon(outline, d)
    if not polygon_ok(ins):
        return False
    if not avoid:
        part.add_engrave(ins, closed=True)
        return True
    pts = ins + [ins[0]]
    run: List[Point] = []
    for a, b in zip(pts, pts[1:]):
        for s, e in clip_segment(a, b, rect(-1e5, -1e5, 2e5, 2e5), avoid):
            if run and dist(run[-1], s) < 1e-6:
                run.append(e)
            else:
                if len(run) >= 2:
                    part.add_engrave(run)
                run = [s, e]
    if len(run) >= 2:
        part.add_engrave(run)
    return True


def keepout_circle(cx: float, cy: float, r: float) -> List[Point]:
    return circle(cx, cy, r, 0.2)


def keepout_rect(cx: float, cy: float, w: float, h: float) -> List[Point]:
    return rect(cx - w / 2, cy - h / 2, w, h)
