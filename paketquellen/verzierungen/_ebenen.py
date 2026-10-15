"""
_ebenen.py – Werkzeug für mehrlagige Teile: Rasterleinwand, Ebenen-Bauteile, Steckstifte, Sockel.

Leinwand
    rechnet Figuren (siehe _kit.Figur) über ein feines Raster zu Flächen. So dürfen sich Formen beliebig
    überlappen. Beim Zurückverwandeln in Konturen werden Stege unter dem Mindeststeg und Schlitze unter
    der Kerf-Breite ausgeglichen – die Teile sind danach immer laserfest.
Ebene
    ein Bauteil mit exakter Außenkontur (Rahmen, mit Steckzapfen) und Durchbrüchen aus der Leinwand.
"""
from __future__ import annotations

import math
import os
import sys
import zlib
from typing import Dict, List, Optional, Sequence, Tuple

import motive as mt
from steckwerk import Assembly, JointFeature, Part, Point, oriented, point_in_polygon, rect, signed_area, \
    slot_feature
from models.motivvorlagen import plate, tidy

_here = os.path.dirname(os.path.abspath(__file__))


def _sub(name: str):
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


K = _sub("_kit")
MIN_LOCH = 3.0          # kleinere Rasterlöcher entfallen (mm²)
Poly = List[Point]


# --------------------------------------------------------------------------------------------------
# Leinwand
# --------------------------------------------------------------------------------------------------

def _and(a: mt.Raster, b: mt.Raster) -> mt.Raster:
    out = mt.Raster(a.w, a.h)
    out.rows = [x & y for x, y in zip(a.rows, b.rows)]
    return out


def _andnot(a: mt.Raster, b: mt.Raster) -> mt.Raster:
    out = mt.Raster(a.w, a.h)
    out.rows = [x & ~y for x, y in zip(a.rows, b.rows)]
    return out


class Leinwand:
    """Raster über das Rechteck box = (x0, y0, x1, y1) in mm mit Pixelgröße px."""

    def __init__(self, box: Tuple[float, float, float, float], px: float = 0.1):
        x0, y0, x1, y1 = box
        self.px = px
        pad = 4 * px
        self.x0, self.y0 = x0 - pad, y0 - pad
        self.w = int(math.ceil((x1 - x0 + 2 * pad) / px)) + 1
        self.h = int(math.ceil((y1 - y0 + 2 * pad) / px)) + 1
        self.y_top = self.y0 + self.h * px

    def leer(self) -> mt.Raster:
        return mt.Raster(self.w, self.h)

    def _pp(self, poly: Sequence[Point]):
        px = self.px
        return [((x - self.x0) / px, (self.y_top - y) / px) for x, y in poly]

    def flaechen(self, polys: Sequence[Sequence[Point]]) -> mt.Raster:
        # einheitlich orientieren, sonst heben sich gegenläufige Flächen bei „nonzero“ gegenseitig auf
        return self.leer().fill([self._pp(p if signed_area(p) >= 0 else p[::-1]) for p in polys if len(p) >= 3],
                                "nonzero")

    def figur(self, fig, base: Optional[mt.Raster] = None) -> mt.Raster:
        """Figur zeichnen: aufeinanderfolgende + und − Flächen werden gebündelt."""
        acc = base or self.leer()
        batch: List[Poly] = []
        sign = None
        for s, poly in fig.ops + [("=", [])]:
            if s != sign and batch:
                r = self.flaechen(batch)
                acc = acc.union(r) if sign == "+" else _andnot(acc, r)
                batch = []
            sign = s
            if s != "=":
                batch.append(poly)
        return acc

    def px_fuer(self, mm: float) -> int:
        return max(0, int(math.ceil(mm / self.px)))

    def konturen(self, r: mt.Raster, tol: float = 0.45) -> List[dict]:
        """Raster → Flächen in mm: [{aussen, loecher}] (aussen CCW, loecher CW)."""
        # wie mt.raster_to_areas, aber Rechteck-Rahmen (4 Ecken) nicht glätten: sonst schneidet das
        # Eckenschleifen große Dreiecke vom Rasterrand ab und Löcher in Bildecken gingen verloren
        outs, holes = [], []
        for lp in r.trace():
            a = mt.area(lp)
            if abs(a) < 4.0:
                continue
            p = mt.simplify(lp, tol)
            if len(p) > 4:
                p = mt.chaikin(p, 1)
                p = mt.simplify(p, tol * 0.25)
            if len(p) < 3:
                continue
            p = [(x, r.h - y) for x, y in p]
            (outs if a > 0 else holes).append(p)
        res = mt.nest(outs, holes)
        px, x0, y0 = self.px, self.x0, self.y_top - self.h * self.px

        def back(p):
            return [(x0 + x * px, y0 + y * px) for x, y in p]
        return [dict(aussen=back(f["aussen"]), loecher=[back(h) for h in f["loecher"]]) for f in res]


def _vektor(lw: Leinwand, holes: mt.Raster) -> Tuple[List[Poly], int]:
    """Löcher der mit dem Rahmen verbundenen Materialfläche; zweiter Wert = Anzahl loser Inseln."""
    areas = lw.konturen(holes.invert())
    if not areas:
        return [], 0
    main = max(areas, key=lambda f: abs(signed_area(f["aussen"])))
    lost = sum(1 for f in areas if f is not main and abs(signed_area(f["aussen"])) > 12.0)   # nur Nennenswertes melden
    out = [oriented(tidy(h, 0.04, 0.2), False) for h in main["loecher"] if abs(signed_area(h)) >= MIN_LOCH]
    return [h for h in out if len(h) >= 3], lost


def nahe_stellen(holes: Sequence[Poly], d: float) -> List[Point]:
    """Stellen, an denen sich zwei verschiedene Löcher näher als d kommen (Mittelpunkt der engsten Stelle)."""
    from steckwerk import point_seg_dist
    cell = max(d, 1.0)
    grid: Dict[Tuple[int, int], List[Tuple[int, Point, Point]]] = {}
    for i, h in enumerate(holes):
        n = len(h)
        for k in range(n):
            a, b = h[k], h[(k + 1) % n]
            for cx in range(int(math.floor((min(a[0], b[0]) - d) / cell)), int(math.floor((max(a[0], b[0]) + d) / cell)) + 1):
                for cy in range(int(math.floor((min(a[1], b[1]) - d) / cell)), int(math.floor((max(a[1], b[1]) + d) / cell)) + 1):
                    grid.setdefault((cx, cy), []).append((i, a, b))
    found: Dict[Tuple[int, int], Tuple[float, Point]] = {}
    for key, segs in grid.items():
        if len({s[0] for s in segs}) < 2:
            continue
        for x in range(len(segs)):
            i, a, b = segs[x]
            for y in range(x + 1, len(segs)):
                j, c, e = segs[y]
                if i == j:
                    continue
                best = None
                for p, q1, q2 in ((a, c, e), (b, c, e), (c, a, b), (e, a, b)):
                    g = point_seg_dist(p, q1, q2)
                    if best is None or g < best[0]:
                        best = (g, p, q1, q2)
                if best[0] < d:
                    g, p, q1, q2 = best
                    # nächster Punkt auf der Gegenstrecke
                    vx, vy = q2[0] - q1[0], q2[1] - q1[1]
                    L2 = vx * vx + vy * vy or 1.0
                    t = max(0.0, min(1.0, ((p[0] - q1[0]) * vx + (p[1] - q1[1]) * vy) / L2))
                    q = (q1[0] + t * vx, q1[1] + t * vy)
                    pair = (min(i, j), max(i, j))
                    mid = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
                    if pair not in found or g < found[pair][0]:
                        found[pair] = (g, mid)
    return [m for _, m in found.values()]


def kreuzungen(poly: Poly, limit: int = 50) -> List[Point]:
    """Stellen, an denen sich die Kontur selbst schneidet (Rasterindex statt O(n²))."""
    from steckwerk import point_seg_dist, segments_cross
    n = len(poly)
    hits: List[Point] = []
    if n < 4:
        return hits
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    cell = max((max(xs) - min(xs) + max(ys) - min(ys)) / max(8.0, math.sqrt(n) * 2), 1e-3)
    grid: Dict[Tuple[int, int], List[int]] = {}
    for k in range(n):
        a, b = poly[k], poly[(k + 1) % n]
        for cx in range(int(math.floor(min(a[0], b[0]) / cell)), int(math.floor(max(a[0], b[0]) / cell)) + 1):
            for cy in range(int(math.floor(min(a[1], b[1]) / cell)), int(math.floor(max(a[1], b[1]) / cell)) + 1):
                grid.setdefault((cx, cy), []).append(k)
    seen = set()
    for segs in grid.values():
        for x in range(len(segs)):
            i = segs[x]
            for y in range(x + 1, len(segs)):
                j = segs[y]
                if abs(i - j) <= 1 or abs(i - j) == n - 1 or (i, j) in seen:
                    continue
                seen.add((i, j))
                a0, a1, b0, b1 = poly[i], poly[(i + 1) % n], poly[j], poly[(j + 1) % n]
                # auch Berührungen zählen (der Validator verlangt Abstand > 0,0001 mm)
                if segments_cross(a0, a1, b0, b1) or min(point_seg_dist(a0, b0, b1), point_seg_dist(a1, b0, b1),
                                                         point_seg_dist(b0, a0, a1), point_seg_dist(b1, a0, a1)) < 2e-3:
                    hits.append(a0)
                    if len(hits) >= limit:
                        return hits
    return hits


def _versatz_fehler(nom: Poly, comp: Poly, d: float) -> List[Point]:
    """Wie die Kerf-Prüfung des Validators: jede Kante liegt nie näher als d und (wenn lang) genau d
    neben der versetzten Kontur – hier mit Rasterindex, damit es auch bei großen Konturen schnell geht."""
    from steckwerk import point_seg_dist
    eps = 1.5e-3
    cell = max(4 * d, 0.3)
    grid: Dict[Tuple[int, int], List[int]] = {}
    m = len(comp)
    for k in range(m):
        a, b = comp[k], comp[(k + 1) % m]
        for cx in range(int(math.floor(min(a[0], b[0]) / cell)), int(math.floor(max(a[0], b[0]) / cell)) + 1):
            for cy in range(int(math.floor(min(a[1], b[1]) / cell)), int(math.floor(max(a[1], b[1]) / cell)) + 1):
                grid.setdefault((cx, cy), []).append(k)
    n = len(nom)
    bad: List[Point] = []
    for k in range(n):
        a, b = nom[k], nom[(k + 1) % n]
        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        cx, cy = int(math.floor(mid[0] / cell)), int(math.floor(mid[1] / cell))
        best = math.inf
        for gx in (cx - 1, cx, cx + 1):
            for gy in (cy - 1, cy, cy + 1):
                for j in grid.get((gx, gy), ()):
                    best = min(best, point_seg_dist(mid, comp[j], comp[(j + 1) % m]))
        if best < d - eps or (math.hypot(b[0] - a[0], b[1] - a[1]) >= 4 * d and abs(best - d) > eps):
            bad.append(mid)
    return bad


def probleme(h: Poly, d: float) -> Optional[List[Point]]:
    """Stellen, an denen das Loch den Kerf-Versatz nicht übersteht. None = Loch insgesamt zu klein."""
    from steckwerk import offset_polygon
    comp = offset_polygon(oriented(h, False), d)
    if len(comp) < 3 or abs(signed_area(comp)) < 1.3 or signed_area(comp) * signed_area(h) <= 0:
        return None
    x = kreuzungen(comp)
    if x:
        return x
    return _versatz_fehler(h, comp, d)


def durchbrueche(lw: Leinwand, bereich: mt.Raster, material: mt.Raster, web: float, kerf: float,
                 notes: List[str], label: str) -> List[Poly]:
    """Löcher = bereich ohne material, laserfest gemacht:
    – Schlitze schmaler als der Laser bleiben Material, Materialstege unter ~2 × web verschwinden,
    – kommen sich zwei Löcher näher als web, wird an der Stelle Material ergänzt,
    – Löcher, die den Kerf-Versatz nicht überstehen, werden geglättet,
    – lose Inseln (fielen heraus) entfallen."""
    holes = _andnot(bereich, material)
    n_web = lw.px_fuer((web + kerf + 0.15) / 2)
    n_slit = lw.px_fuer((kerf + 0.35) / 2)
    holes = holes.open(n_slit)
    holes = holes.close(n_web)
    holes = _and(holes, bereich)
    lost = 0
    out: List[Poly] = []
    R_mat = web / 2 + kerf + 0.25
    for runde in range(8):
        out, lost = _vektor(lw, holes)
        flecken: List[Poly] = [K.circle(x, y, R_mat, 16) for x, y in nahe_stellen(out, web + 0.05)]
        for h in out:
            pr = probleme(h, kerf / 2)
            if pr is None:
                flecken.append(h)                              # zu kleines Loch: wird Material
            else:
                flecken += [K.circle(x, y, kerf + 0.3 + 0.1 * runde, 12) for x, y in pr]
        if not flecken:
            break
        holes = _andnot(holes, lw.flaechen(flecken))
    else:
        keep = []
        for h in out:
            pr = probleme(h, kerf / 2)
            if pr == [] :
                keep.append(h)
        if len(keep) < len(out):
            notes.append(f"{label}: {len(out) - len(keep)} winzige Durchbrüche wurden weggelassen.")
        out = keep
    if lost:
        notes.append(f"{label}: {lost} kleine Inseln hätten keinen Halt und wurden weggelassen.")
    return out


# --------------------------------------------------------------------------------------------------
# Grundformen und Ebenen
# --------------------------------------------------------------------------------------------------

FORMEN = [("bogen", "Rundbogen"), ("rechteck", "Rechteck"), ("abgerundet", "Rechteck, abgerundet"),
          ("spitzbogen", "Spitzbogen (gotisch)"), ("oval", "oval")]


def aussen(form: str, W: float, H: float, flach: float) -> Poly:
    return plate(form, W, H, flat_bottom=flach)


def innen(form: str, W: float, H: float, rand: float, flach: float) -> Poly:
    """Sichtfenster: die Grundform um rand nach innen versetzt (unten gerade)."""
    if form in ("oval",):
        p = plate(form, W - 2 * rand, H - 2 * rand, flat_bottom=max(flach - 2 * rand, 0.6 * (W - 2 * rand)))
    else:
        p = plate(form, W - 2 * rand, H - 2 * rand)
    return [(x, y + rand) for x, y in p]


def zapfen_einsetzen(outline: Poly, xs: Sequence[float], tw: float, T: float, oben: Optional[float] = None
                     ) -> Tuple[Poly, List[Tuple[str, float, Poly]]]:
    """Zapfen (Breite tw, Höhe T) an der geraden Unterkante y = 0 bei den x-Mitten xs einsetzen,
    optional auch an einer geraden Oberkante y = oben. Liefert (Kontur, [(seite, x, Punkte)])."""
    P = oriented(outline, True)
    feats: List[Tuple[str, float, Poly]] = []
    out: Poly = []
    n = len(P)
    for i in range(n):
        a, b = P[i], P[(i + 1) % n]
        out.append(a)
        if abs(a[1]) < 1e-6 and abs(b[1]) < 1e-6 and b[0] > a[0]:            # Unterkante, nach rechts
            for x in sorted(xs):
                if a[0] + 1 < x - tw / 2 and x + tw / 2 < b[0] - 1:
                    pts = [(x - tw / 2, 0.0), (x - tw / 2, -T), (x + tw / 2, -T), (x + tw / 2, 0.0)]
                    out += pts
                    feats.append(("unten", x, pts))
        if oben is not None and abs(a[1] - oben) < 1e-6 and abs(b[1] - oben) < 1e-6 and b[0] < a[0]:
            for x in sorted(xs, reverse=True):
                if b[0] + 1 < x - tw / 2 and x + tw / 2 < a[0] - 1:
                    pts = [(x + tw / 2, oben), (x + tw / 2, oben + T), (x - tw / 2, oben + T), (x - tw / 2, oben)]
                    out += pts
                    feats.append(("oben", x, pts))
    return out, feats


def quer_x(poly: Poly, y: float) -> Tuple[float, float]:
    """Linker und rechter Schnittpunkt einer Kontur mit der Waagerechten y."""
    xs = []
    n = len(poly)
    for i in range(n):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % n]
        if (y1 <= y < y2) or (y2 <= y < y1):
            xs.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
    return min(xs), max(xs)


# --------------------------------------------------------------------------------------------------
# Sockel mit Schlitzen
# --------------------------------------------------------------------------------------------------

def sockelplatte(name: str, W: float, reihen: Sequence[float], xs: Sequence[float], tw: float, T: float,
                 rand: float) -> Tuple[Part, List[str]]:
    """Platte mit je einem Schlitz pro (Reihe y, Zapfen x). Liefert (Teil, Feature-IDs in Reihenfolge)."""
    y0 = min(reihen) - T / 2 - rand
    y1 = max(reihen) + T / 2 + rand
    r = min(4.0, (y1 - y0) / 4)
    from models import _deko as dk
    part = Part(name, oriented(dk.rounded_rect(-W / 2, y0, W / 2, y1, r), True))
    ids = []
    for k, y in enumerate(reihen):
        for j, x in enumerate(xs):
            fid = f"s{k}_{j}"
            feat, hole = slot_feature(fid, x - tw / 2, y - T / 2, tw, T, True, k * 100.0 + j)
            part.holes.append(hole)
            part.features.append(feat)
            ids.append(fid)
    return part, ids


# --------------------------------------------------------------------------------------------------
# Steckstifte (Vierkant, Pressitz durch alle Lagen)
# --------------------------------------------------------------------------------------------------

def stift(name: str, lagen: int, T: float, pos: float, ueberstand: float = 0.0) -> Part:
    """Vierkantstift T × T, so lang wie lagen × T (+ Überstand); je Lage ein shaft-Abschnitt."""
    L = lagen * T + ueberstand
    part = Part(name, rect(0, 0, L, T))
    for k in range(lagen):
        z0, z1 = k * T, (k + 1) * T
        part.features.append(JointFeature(f"l{k}", "shaft", T, T, pos=pos, span=(z0, z1),
                                          points=[(z0, 0.0), (z1, 0.0), (z1, T), (z0, T)]))
    return part


def stiftloch(part: Part, fid: str, x: float, y: float, T: float, pos: float) -> None:
    hole = rect(x - T / 2, y - T / 2, T, T, ccw=False)
    part.holes.append(hole)
    part.features.append(JointFeature(fid, "bore_square", T, T, pos=pos, points=list(hole)))


# --------------------------------------------------------------------------------------------------
# Freistehendes Teil aus einer Figur
# --------------------------------------------------------------------------------------------------

def teil_aus_figur(name: str, fig, web: float, kerf: float, notes: List[str], px: float = 0.08,
                   unten_flach: bool = False) -> Part:
    """Figur → laserfestes Einzelteil: Außenkontur aus der größten Fläche, innere Durchbrüche wie bei den
    Ebenen geprüft (Stege ≥ web, auch zum Rand). unten_flach: Punkte nahe y = 0 exakt auf 0 setzen."""
    x0, y0, x1, y1 = fig.bbox()
    lw = Leinwand((x0 - 3, y0 - 3, x1 + 3, y1 + 3), px)
    return teil_aus_raster(name, lw, lw.figur(fig), web, kerf, notes, unten_flach)


def teil_aus_raster(name: str, lw: Leinwand, mat: mt.Raster, web: float, kerf: float, notes: List[str],
                    unten_flach: bool = False) -> Part:
    """Wie teil_aus_figur, aber aus einem fertigen Materialraster."""
    px = lw.px
    mat = mat.close(lw.px_fuer((kerf + 0.35) / 2)).open(lw.px_fuer((web + kerf + 0.15) / 2))
    from steckwerk import offset_polygon
    for runde in range(6):
        areas = lw.konturen(mat)
        if not areas:
            raise ValueError("Motiv ist zu klein für den Laser – größer wählen")
        main = max(areas, key=lambda f: abs(signed_area(f["aussen"])))
        outline = tidy(main["aussen"], 0.04, 0.2)
        if unten_flach:
            outline = [(x, 0.0 if abs(y) < 2.5 * px else y) for x, y in outline]
            outline = [p for i, p in enumerate(outline) if i == 0 or p != outline[i - 1]]
            n = len(outline)
            outline = [p for i, p in enumerate(outline)
                       if not (p[1] == 0.0 and outline[i - 1][1] == 0.0 and outline[(i + 1) % n][1] == 0.0)]
        outline = oriented(outline, True)
        comp = offset_polygon(outline, kerf / 2)
        bad = kreuzungen(comp) or _versatz_fehler(outline, comp, kerf / 2)
        if not bad:
            break
        # enge Kerben in der Außenkontur mit Material füllen
        mat = mat.union(lw.flaechen([K.circle(x, y, kerf + 0.3 + 0.1 * runde, 12) for x, y in bad]))
    lost = sum(1 for f in areas if f is not main and abs(signed_area(f["aussen"])) > 12.0)
    if lost:
        notes.append(f"{name}: {lost} kleine Teile hingen nicht am Motiv und wurden weggelassen.")
    bereich = lw.flaechen([outline]).erode(lw.px_fuer(web + kerf / 2 + 0.1))
    holes = durchbrueche(lw, bereich, mat, web, kerf, notes, name)
    part = Part(name, outline)
    for h in holes:
        part.add_hole(h)
    return part


