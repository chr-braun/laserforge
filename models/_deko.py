"""
_deko.py – Gestaltungsbaukasten für Gravuren und Fenster.

  Canvas        „Leinwand“ eines Bauteils: Linien werden an der Kontur (mit Randabstand), an
                Durchbrüchen und an bereits belegten Flächen (Fenster, Schild, Text) abgeschnitten;
                geschlossene Ornamente (Sterne, Lampen, Blüten) werden nur ganz gesetzt.
                So kann keine Gravur über einen Schnitt laufen oder aus dem Teil ragen.
  styled_line   Zierlinien: Linie, Doppellinie, gestrichelt, Punkte, Wellen, Zickzack, Zuckerguss,
                Eiszapfen, Lichterkette, Girlande, Sterne, Herzen
  window_*      Fensterformen (Rechteck, rund, Rundbogen, Spitzbogen, Raute, Herz, Stern) mit
                Sprossen und Schmuck (Rahmen, Läden, Herzläden, Blumenkasten, Schneehaube)
  door_*        Türformen und Türschmuck (Rahmen, Vordach, Laternen, Girlande, Kranz)
  gable_deco    Giebelschmuck (Rundfenster, Herz, Stern, Uhr, Heuluke, Text)
  sign          Schild mit Beschriftung (Rahmen, abgerundet, oval, Banner, Holzbrett, geschweift)
  wall_pattern  Wandgravur (Holz, Ziegel, Bruchstein, Fachwerk, Schindeln, Rauputz, Sterne, Herzen)
  roof_pattern  Dachgravur (Ziegel, Biberschwanz, Holzschindeln, Reet, Schneekante, Sternenhimmel)
  yard          Vorplatz auf der Bodenplatte (Steinweg, Fußmatte mit Text, Tannen)
"""
from __future__ import annotations

import bisect
import math
import random
from typing import List, Optional, Sequence, Tuple

from steckwerk import (Part, Point, arc_points, arched, bbox, circle, clean, dist, ellipse,
                        inset_polygon, offset_polygon, oriented, point_in_polygon, polygon_ok, rect,
                        remove_loops, signed_area)
from models._font import fit_text
from models._shapes import drop_close, star

Box = Tuple[float, float, float, float]          # x0, y0, x1, y1

# ---------------------------------------------------------------------------
# Auswahllisten (Wert, Beschriftung) – daraus baut service.py die Formulare
# ---------------------------------------------------------------------------
LINE_STYLES = [("linie", "Linie"), ("doppelt", "Doppellinie"), ("gestrichelt", "gestrichelt"),
               ("punkte", "Punkte"), ("wellen", "Wellen"), ("zickzack", "Zickzack"),
               ("zuckerguss", "Zuckerguss"), ("eiszapfen", "Eiszapfen"), ("lichterkette", "Lichterkette"),
               ("girlande", "Girlande"), ("sterne", "Sterne"), ("herzen", "Herzen")]
WINDOW_FORMS = [("rechteck", "Rechteck"), ("rund", "rund"), ("bogen", "Rundbogen"),
                ("spitzbogen", "Spitzbogen"), ("raute", "Raute"), ("herz", "Herz"), ("stern", "Stern")]
MUNTINS = [("kreuz", "Kreuz"), ("senkrecht", "senkrecht"), ("waagrecht", "waagrecht"), ("keine", "keine")]
WINDOW_DECO = [("rahmen", "Rahmen und Sims"), ("laeden", "Fensterläden"), ("herzlaeden", "Läden mit Herz"),
               ("blumen", "Blumenkasten"), ("beides", "Läden und Blumen"), ("schnee", "Schneehaube"),
               ("keine", "nichts")]
DOORS = [("arched", "Rundbogen"), ("rect", "Rechteckig"), ("spitzbogen", "Spitzbogen"),
         ("rund", "rund (Hobbit)"), ("none", "keine")]
DOOR_DECO = [("rahmen", "Rahmen"), ("vordach", "Vordach"), ("laternen", "Laternen"),
             ("girlande", "Girlande"), ("kranz", "Türkranz"), ("keine", "nichts")]
GABLES = [("rundfenster", "Rundfenster"), ("herz", "Herz"), ("stern", "Stern"), ("uhr", "Uhr"),
          ("luke", "Heuluke"), ("text", "Text"), ("keins", "nichts")]
WALLS = [("keine", "glatt"), ("holz", "Holzbretter"), ("ziegel", "Ziegel"), ("stein", "Bruchstein"),
         ("fachwerk", "Fachwerk"), ("schuppen", "Rundschindeln"), ("putz", "Rauputz"),
         ("sterne", "Sterne"), ("herzen", "Herzen")]
ROOFS = [("ziegel", "Ziegel"), ("biber", "Biberschwanz"), ("schindel", "Holzschindeln"), ("reet", "Reet"),
         ("schnee", "Schneekante"), ("sterne", "Sternenhimmel"), ("keine", "glatt")]
TRIMS = [("keine", "keine")] + LINE_STYLES
SIGNS = [("rahmen", "Rahmen"), ("rund", "abgerundet"), ("oval", "oval"), ("banner", "Banner"),
         ("holz", "Holzbrett"), ("geschweift", "geschweift"), ("ohne", "nur Text")]
FONT_STYLES = [("normal", "normal"), ("fett", "fett"), ("kursiv", "kursiv"), ("schmal", "schmal"),
               ("breit", "breit"), ("schatten", "mit Schatten")]
FONT_CASES = [("gross", "GROSSBUCHSTABEN"), ("normal", "wie eingegeben (groß/klein)")]
YARDS = [("keiner", "keiner"), ("weg", "Steinweg"), ("matte", "Fußmatte"), ("garten", "Tannen und Schnee"),
         ("alles", "alles zusammen")]

values = lambda opts: [v for v, _ in opts]          # noqa: E731


def check_choice(label: str, value: str, opts) -> str:
    if value not in values(opts):
        raise ValueError(f"{label}: {value!r} unbekannt – erlaubt: {', '.join(values(opts))}")
    return value


# ---------------------------------------------------------------------------
# Leinwand
# ---------------------------------------------------------------------------

class _Poly:
    __slots__ = ("pts", "bb", "edges")

    def __init__(self, pts: Sequence[Point]):
        self.pts = list(pts)
        self.bb = bbox(self.pts) if self.pts else (0.0, 0.0, -1.0, -1.0)
        n = len(self.pts)
        self.edges = []
        for i in range(n):
            a, b = self.pts[i], self.pts[(i + 1) % n]
            self.edges.append((a, b, min(a[0], b[0]), max(a[0], b[0]), min(a[1], b[1]), max(a[1], b[1])))

    def overlaps(self, bb: Box) -> bool:
        return not (bb[2] < self.bb[0] or bb[0] > self.bb[2] or bb[3] < self.bb[1] or bb[1] > self.bb[3])

    def contains(self, p: Point) -> bool:
        if not self.pts or p[0] < self.bb[0] or p[0] > self.bb[2] or p[1] < self.bb[1] or p[1] > self.bb[3]:
            return False
        return point_in_polygon(p, self.pts)

    def crossings(self, p0: Point, p1: Point, sbb: Box, out: List[float]) -> None:
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        for a, b, ex0, ex1, ey0, ey1 in self.edges:
            if ex1 < sbb[0] or ex0 > sbb[2] or ey1 < sbb[1] or ey0 > sbb[3]:
                continue
            ex, ey = b[0] - a[0], b[1] - a[1]
            den = dx * ey - dy * ex
            if abs(den) < 1e-12:
                continue
            t = ((a[0] - p0[0]) * ey - (a[1] - p0[1]) * ex) / den
            u = ((a[0] - p0[0]) * dy - (a[1] - p0[1]) * dx) / den
            if 0.0 < t < 1.0 and -1e-12 <= u <= 1.0 + 1e-12:
                out.append(t)


def grow(poly: Sequence[Point], d: float) -> List[Point]:
    """Fläche um d vergrößern (Sperrzone). Bei Problemen: umschließendes Rechteck."""
    pts = oriented(clean(poly), True)
    if d <= 0:
        return pts
    g = remove_loops(offset_polygon(pts, d, miter_limit=2.0))
    if len(g) < 3 or signed_area(g) <= 0 or not polygon_ok(g):
        x0, y0, x1, y1 = bbox(pts)
        g = rect(x0 - d, y0 - d, x1 - x0 + 2 * d, y1 - y0 + 2 * d)
    return g


class Canvas:
    """Zeichenfläche eines Bauteils (siehe Moduldoku)."""

    def __init__(self, part: Part, margin: float = 1.0, area: Optional[Sequence[Point]] = None,
                 hole_margin: Optional[float] = None, seed: int = 1):
        self.part = part
        self.margin = margin
        self.hole_margin = margin if hole_margin is None else hole_margin
        ins = inset_polygon(part.outline, margin) if margin > 0 else oriented(part.outline, True)
        self.ok = len(ins) >= 3
        self.inside = [_Poly(ins)]
        if area is not None:
            self.inside.append(_Poly(oriented(clean(area), True)))
        self.blocks: List[_Poly] = []
        for h in part.holes:
            self.block(h, self.hole_margin)
        self.rng = random.Random(seed)

    # --- Sperrflächen ---------------------------------------------------------
    def block(self, poly: Sequence[Point], margin: float = 0.0) -> None:
        if len(poly) >= 3:
            self.blocks.append(_Poly(grow(poly, margin)))
            if margin > 0:                                    # Sicherheitsnetz: Fläche selbst
                self.blocks.append(_Poly(oriented(clean(poly), True)))

    def block_box(self, b: Box, margin: float = 0.0) -> None:
        x0, y0, x1, y1 = b
        self.blocks.append(_Poly(rect(x0 - margin, y0 - margin, x1 - x0 + 2 * margin, y1 - y0 + 2 * margin)))

    def block_strokes(self, strokes, margin: float = 0.6, solid: bool = False) -> None:
        """Vorhandene Gravuren als Sperrflächen: Linien als schmale Bänder, geschlossene Linien
        mit solid=True als ganze Fläche."""
        for st in strokes:
            pts, closed = (st.points, st.closed) if hasattr(st, "points") else st
            pts = list(pts)
            if closed and len(pts) >= 3:
                if solid:
                    self.block(pts, margin)
                    continue
                pts = pts + [pts[0]]
            for a, b in zip(pts, pts[1:]):
                L = dist(a, b)
                if L < 1e-9:
                    continue
                ux, uy = (b[0] - a[0]) / L * margin, (b[1] - a[1]) / L * margin
                self.blocks.append(_Poly(oriented([(a[0] - ux + uy, a[1] - uy - ux), (b[0] + ux + uy, b[1] + uy - ux),
                                                   (b[0] + ux - uy, b[1] + uy + ux), (a[0] - ux - uy, a[1] - uy + ux)],
                                                  True)))

    def add_hole(self, poly: Sequence[Point]) -> None:
        self.part.add_hole(poly)
        self.block(poly, self.hole_margin)

    # --- Abschneiden ------------------------------------------------------------
    def free(self, p: Point) -> bool:
        return self.ok and all(P.contains(p) for P in self.inside) and not any(B.contains(p) for B in self.blocks)

    def _seg(self, a: Point, b: Point) -> List[Tuple[Point, Point]]:
        if not self.ok:
            return []
        sbb = (min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1]))
        ts = [0.0, 1.0]
        for P in self.inside:
            P.crossings(a, b, sbb, ts)
        blk = [B for B in self.blocks if B.overlaps(sbb)]
        for B in blk:
            B.crossings(a, b, sbb, ts)
        ts.sort()
        dx, dy = b[0] - a[0], b[1] - a[1]
        keep: List[Tuple[float, float]] = []
        for t0, t1 in zip(ts, ts[1:]):
            if t1 - t0 < 1e-9:
                continue
            tm = (t0 + t1) / 2
            m = (a[0] + dx * tm, a[1] + dy * tm)
            if all(P.contains(m) for P in self.inside) and not any(B.contains(m) for B in blk):
                if keep and abs(keep[-1][1] - t0) < 1e-9:
                    keep[-1] = (keep[-1][0], t1)
                else:
                    keep.append((t0, t1))
        return [((a[0] + dx * t0, a[1] + dy * t0), (a[0] + dx * t1, a[1] + dy * t1)) for t0, t1 in keep]

    def clip(self, pts: Sequence[Point], closed: bool = False) -> List[List[Point]]:
        pts = list(pts)
        if closed:
            pts = pts + [pts[0]]
        runs: List[List[Point]] = []
        cur: List[Point] = []
        for a, b in zip(pts, pts[1:]):
            if dist(a, b) < 1e-9:
                continue
            for s, e in self._seg(a, b):
                if cur and dist(cur[-1], s) < 1e-7:
                    cur.append(e)
                else:
                    if len(cur) >= 2:
                        runs.append(cur)
                    cur = [s, e]
        if len(cur) >= 2:
            runs.append(cur)
        if closed and len(runs) >= 2 and dist(runs[0][0], runs[-1][-1]) < 1e-7:
            runs[0] = runs.pop() + runs[0][1:]                  # Anfang/Ende verbinden
        return runs

    def fits(self, pts: Sequence[Point], closed: bool = True, solid: bool = False) -> bool:
        """Liegt die Linie vollständig auf freier Fläche? solid: auch keine Sperrinsel im Inneren."""
        if not self.ok or not all(self.free(p) for p in pts):
            return False
        if solid and closed and len(pts) >= 3:
            bb = bbox(pts)
            if any(B.pts and B.overlaps(bb) and point_in_polygon(B.pts[0], pts) for B in self.blocks):
                return False
        seq = list(pts) + ([pts[0]] if closed else [])
        for a, b in zip(seq, seq[1:]):
            if dist(a, b) < 1e-9:
                continue
            s = self._seg(a, b)
            if len(s) != 1 or dist(s[0][0], a) > 1e-7 or dist(s[0][1], b) > 1e-7:
                return False
        return True

    def draw(self, pts: Sequence[Point], closed: bool = False, min_len: float = 0.35) -> float:
        """Linie gravieren, abgeschnitten an allem Belegten. Liefert die gezeichnete Länge."""
        if len(pts) < 2:
            return 0.0
        runs = self.clip(pts, closed)
        total = sum(dist(a, b) for a, b in zip(list(pts) + ([pts[0]] if closed else []), list(pts)[1:] +
                                                   ([pts[0]] if closed else [])))
        done = 0.0
        if closed and len(runs) == 1 and abs(_plen(runs[0]) - total) < 1e-6:
            self.part.add_engrave(pts, closed=True)
            return total
        for r in runs:
            L = _plen(r)
            if L >= min_len:
                self.part.add_engrave(r)
                done += L
        return done

    def put(self, pts: Sequence[Point], closed: bool = True, reserve: Optional[float] = None) -> bool:
        """Ornament nur ganz setzen (oder gar nicht)."""
        if len(pts) < 2 or not self.fits(pts, closed):
            return False
        self.part.add_engrave(pts, closed=closed)
        if reserve is not None and closed:
            self.block(pts, reserve)
        return True

    def put_all(self, items: Sequence[Tuple[Sequence[Point], bool]], reserve: Optional[float] = None,
                outline: Optional[Sequence[Point]] = None) -> bool:
        """Mehrteiliges Ornament: nur setzen, wenn alle Teile passen."""
        if not items or not all(self.fits(p, c) for p, c in items):
            return False
        for p, c in items:
            self.part.add_engrave(p, closed=c)
        if reserve is not None:
            if outline is not None:
                self.block(outline, reserve)
            else:
                xs = [q[0] for p, _ in items for q in p]
                ys = [q[1] for p, _ in items for q in p]
                self.block_box((min(xs), min(ys), max(xs), max(ys)), reserve)
        return True


def _plen(pts: Sequence[Point]) -> float:
    return sum(dist(a, b) for a, b in zip(pts, pts[1:]))


# ---------------------------------------------------------------------------
# Pfade
# ---------------------------------------------------------------------------

class _Path:
    def __init__(self, pts: Sequence[Point]):
        self.pts: List[Point] = []
        for p in pts:
            if not self.pts or dist(p, self.pts[-1]) > 1e-9:
                self.pts.append(p)
        self.cum = [0.0]
        for a, b in zip(self.pts, self.pts[1:]):
            self.cum.append(self.cum[-1] + dist(a, b))
        self.length = self.cum[-1]

    def at(self, s: float) -> Tuple[Point, Point]:
        """Punkt und Einheits-Tangente bei Bogenlänge s."""
        if len(self.pts) < 2:
            return (self.pts[0] if self.pts else (0.0, 0.0)), (1.0, 0.0)
        s = min(max(s, 0.0), self.length)
        i = min(max(bisect.bisect_right(self.cum, s) - 1, 0), len(self.pts) - 2)
        a, b = self.pts[i], self.pts[i + 1]
        L = self.cum[i + 1] - self.cum[i]
        t = (s - self.cum[i]) / L if L > 0 else 0.0
        return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t), ((b[0] - a[0]) / L, (b[1] - a[1]) / L)

    def sub(self, s0: float, s1: float) -> List[Point]:
        out = [self.at(s0)[0]]
        for i, c in enumerate(self.cum):
            if s0 < c < s1:
                out.append(self.pts[i])
        out.append(self.at(s1)[0])
        return out


def offset_path(pts: Sequence[Point], d: float) -> List[Point]:
    """Offene Polylinie um d nach links (d < 0: rechts) versetzen, Ecken auf Gehrung."""
    P = _Path(pts).pts
    n = len(P)
    if n < 2 or abs(d) < 1e-12:
        return list(P)
    nrm = []
    for a, b in zip(P, P[1:]):
        L = dist(a, b)
        nrm.append((-(b[1] - a[1]) / L, (b[0] - a[0]) / L))
    out = [(P[0][0] + nrm[0][0] * d, P[0][1] + nrm[0][1] * d)]
    for i in range(1, n - 1):
        n1, n2 = nrm[i - 1], nrm[i]
        k = 1.0 + n1[0] * n2[0] + n1[1] * n2[1]
        if k < 0.25:                                     # sehr spitz: zwei Punkte
            out += [(P[i][0] + n1[0] * d, P[i][1] + n1[1] * d), (P[i][0] + n2[0] * d, P[i][1] + n2[1] * d)]
        else:
            out.append((P[i][0] + (n1[0] + n2[0]) * d / k, P[i][1] + (n1[1] + n2[1]) * d / k))
    out.append((P[-1][0] + nrm[-1][0] * d, P[-1][1] + nrm[-1][1] * d))
    return out


def _bez(p0: Point, c: Point, p1: Point, n: int = 12) -> List[Point]:
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * c[0] + t * t * p1[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * c[1] + t * t * p1[1])
            for t in (i / n for i in range(n + 1))]


# ---------------------------------------------------------------------------
# Kleine Formen
# ---------------------------------------------------------------------------

def heart(cx: float, cy: float, w: float, h: float, n: int = 56) -> List[Point]:
    """Herz in der Box w × h: auf die Spitze gestelltes Quadrat + zwei Halbkreise.
    Die Kerbe oben ist ein sauberer 90°-Knick – robust für Kerf-Versatz und Sperrzonen."""
    a = 1.0
    q = a / math.sqrt(2)
    r = a / 2
    tol = max(0.0015, 0.05 / max(w, h, 1.0))
    rc = (q / 2, 1.5 * q)
    ang = math.atan2(q - rc[1], q - rc[0])
    pts = [(0.0, 0.0), (q, q)]
    pts += arc_points(rc[0], rc[1], r, ang, ang + math.pi, tol)[1:]
    lc = (-q / 2, 1.5 * q)
    ang2 = math.atan2(2 * q - lc[1], 0.0 - lc[0])
    pts += arc_points(lc[0], lc[1], r, ang2, ang2 + math.pi, tol)[1:-1]
    x0, y0, x1, y1 = bbox(pts)
    sx, sy = w / (x1 - x0), h / (y1 - y0)
    return oriented(clean([(cx + (x - (x0 + x1) / 2) * sx, cy + (y - (y0 + y1) / 2) * sy) for x, y in pts]), True)


def rounded_rect(x0: float, y0: float, x1: float, y1: float, r: float, tol: float = 0.05) -> List[Point]:
    r = max(0.0, min(r, (x1 - x0) / 2 - 1e-6, (y1 - y0) / 2 - 1e-6))
    if r < 0.05:
        return rect(x0, y0, x1 - x0, y1 - y0)
    pts = arc_points(x1 - r, y0 + r, r, -math.pi / 2, 0, tol)
    pts += arc_points(x1 - r, y1 - r, r, 0, math.pi / 2, tol)
    pts += arc_points(x0 + r, y1 - r, r, math.pi / 2, math.pi, tol)
    pts += arc_points(x0 + r, y0 + r, r, math.pi, 1.5 * math.pi, tol)
    return clean(pts)


def scalloped_rect(x0: float, y0: float, x1: float, y1: float, r: float, tol: float = 0.05) -> List[Point]:
    """Rechteck mit nach innen gewölbten Ecken (geschweiftes Schild)."""
    r = max(0.3, min(r, (x1 - x0) / 3, (y1 - y0) / 3))
    pts = arc_points(x1, y0, r, math.pi, math.pi / 2, tol)
    pts += arc_points(x1, y1, r, -math.pi / 2, -math.pi, tol)
    pts += arc_points(x0, y1, r, 0, -math.pi / 2, tol)
    pts += arc_points(x0, y0, r, math.pi / 2, 0, tol)
    return oriented(clean(pts), True)


def _rot(pts: Sequence[Point], c: Point, ux: float, uy: float) -> List[Point]:
    """Lokale Form (x nach rechts, y nach oben) so drehen, dass ihr 'unten' (0,-1) in (ux,uy) zeigt."""
    ey = (-ux, -uy)
    ex = (ey[1], -ey[0])
    return [(c[0] + x * ex[0] + y * ey[0], c[1] + x * ex[1] + y * ey[1]) for x, y in pts]


# ---------------------------------------------------------------------------
# Zierlinien
# ---------------------------------------------------------------------------

def styled_line(cv: Canvas, path: Sequence[Point], style: str, size: float, side: int = -1,
                seed: int = 0, gravity: bool = True) -> None:
    """Zierlinie entlang 'path'. Das Band reicht 'size' mm zur Seite 'side' (-1 rechts der
    Laufrichtung, +1 links). Hängende Elemente (Eiszapfen, Lampen, Kugeln) zeigen bei
    gravity=True senkrecht nach unten, sofern das Band nach unten zeigt."""
    P = _Path(path)
    if P.length < 1.5 * size or style in ("keine", "", None):
        return
    rng = random.Random(seed)

    def hang(t):
        return (-t[1] * side, t[0] * side)

    def down(t):
        h = hang(t)
        return (0.0, -1.0) if gravity and h[1] < -0.3 else h

    def off(p, v, d):
        return (p[0] + v[0] * d, p[1] + v[1] * d)

    def stations(step, pad=0.0):
        n = max(1, int((P.length - 2 * pad) / step))
        st = (P.length - 2 * pad) / n
        return [pad + st * (i + 0.5) for i in range(n)], st

    s = size
    if style == "linie":
        cv.draw(P.pts)
    elif style == "doppelt":
        cv.draw(P.pts)
        cv.draw(offset_path(P.pts, side * 0.38 * s))
    elif style == "gestrichelt":
        dash, gap = 0.9 * s, 0.55 * s
        x = 0.0
        while x < P.length - 0.3:
            cv.draw(P.sub(x, min(x + dash, P.length)))
            x += dash + gap
    elif style == "punkte":
        for x in stations(0.85 * s)[0]:
            p, t = P.at(x)
            cv.put(circle(*off(p, hang(t), 0.3 * s), 0.16 * s, 0.03))
    elif style == "wellen":
        c = _Path(offset_path(P.pts, side * 0.32 * s))
        lam, a = 1.4 * s, 0.22 * s
        n = max(8, int(c.length / (lam / 14)))
        pts = []
        for i in range(n + 1):
            x = c.length * i / n
            p, t = c.at(x)
            pts.append(off(p, hang(t), a * math.sin(2 * math.pi * x / lam)))
        cv.draw(pts)
    elif style == "zickzack":
        per = 1.1 * s
        n = max(2, int(P.length / (per / 2)))
        pts = []
        for i in range(n + 1):
            x = P.length * i / n
            p, t = P.at(x)
            pts.append(off(p, hang(t), (0.05 if i % 2 == 0 else 0.55) * s))
        cv.draw(pts)
    elif style == "zuckerguss":
        cv.draw(P.pts)
        w = 0.7 * s
        n = max(1, int(P.length / w))
        w = P.length / n
        pts = []
        for k in range(n):
            for j in range(9):
                x = (k + j / 8) * w
                p, t = P.at(x)
                pts.append(off(p, hang(t), 0.32 * s * math.sin(math.pi * j / 8)))
        cv.draw(pts)
        for k in range(n):
            if (k + seed) % 2 == 0:
                p, t = P.at((k + 0.5) * w)
                cv.put(circle(*off(p, down(t), 0.6 * s), 0.11 * s, 0.03))
    elif style == "eiszapfen":
        cv.draw(P.pts)
        xs, st = stations(0.42 * s)
        for x in xs:
            p, t = P.at(x)
            d = down(t)
            L = s * (0.35 + 0.6 * rng.random())
            bw = 0.14 * s
            cv.put([off(p, t, -bw), off(p, d, L), off(p, t, bw)], closed=False)
    elif style in ("lichterkette", "girlande"):
        step = (2.2 if style == "lichterkette" else 2.6) * s
        n = max(1, int(P.length / step))
        step = P.length / n
        anchors = [P.at(i * step) for i in range(n + 1)]
        for (pa, ta), (pb, tb) in zip(anchors, anchors[1:]):
            mid = ((pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2)
            dm = down(ta)
            if style == "lichterkette":
                cv.draw(_bez(pa, off(mid, dm, 0.7 * s), pb, 14))
                low = off(mid, dm, 0.35 * s)
                ux, uy = dm
                bulb = [(0.12 * s * math.cos(a), -0.22 * s - 0.2 * s * math.sin(a))
                        for a in (2 * math.pi * i / 20 for i in range(20))]
                socket = [(-0.07 * s, -0.02 * s), (-0.07 * s, -0.12 * s), (0.07 * s, -0.12 * s), (0.07 * s, -0.02 * s)]
                cv.put_all([(_rot(bulb, low, ux, uy), True), (_rot(socket, low, ux, uy), False)])
            else:
                cv.draw(_bez(pa, off(mid, dm, 0.9 * s), pb, 14))
                cv.draw(_bez(pa, off(mid, dm, 0.62 * s), pb, 14))
        if style == "girlande":
            for i, (p, t) in enumerate(anchors[1:-1], 1):
                d = down(t)
                ball = off(p, d, 0.62 * s)
                cv.put_all([([p, off(p, d, 0.48 * s)], False), (circle(*ball, 0.14 * s, 0.03), True)])
    elif style in ("sterne", "herzen"):
        for i, x in enumerate(stations(1.0 * s)[0]):
            p, t = P.at(x)
            c = off(p, hang(t), 0.42 * s)
            r = (0.3 if i % 2 == 0 else 0.22) * s
            shape = star(c[0], c[1], r, 0.45 * r) if style == "sterne" else heart(c[0], c[1], 1.7 * r, 1.5 * r, 32)
            cv.put(shape)
    else:
        raise ValueError(f"Zierlinie {style!r} unbekannt – erlaubt: {', '.join(values(LINE_STYLES))}")


# ---------------------------------------------------------------------------
# Fenster
# ---------------------------------------------------------------------------

CONVEX = {"rechteck", "rund", "bogen", "spitzbogen", "raute"}


def pointed_arch(cx: float, y0: float, w: float, h: float, tol: float = 0.05) -> List[Point]:
    """Spitzbogen in der Box w × h (Unterkante y0)."""
    a = min(0.85 * w, h)
    if a <= w / 2 + 0.05:
        return arched(cx, y0, w, h, tol)
    ys = y0 + h - a
    R = (w * w / 4 + a * a) / w
    phi = math.atan2(a, R - w / 2)
    pts = [(cx - w / 2, y0), (cx + w / 2, y0)]
    if ys > y0 + 1e-6:
        pts.append((cx + w / 2, ys))
    pts += arc_points(cx + w / 2 - R, ys, R, 0.0, phi, tol)[1:]
    pts += arc_points(cx - w / 2 + R, ys, R, math.pi - phi, math.pi, tol)[1:]
    return clean(pts)


def spring_y(form: str, cy: float, w: float, h: float) -> float:
    """Höhe der waagrechten Sprosse (bei Bögen der Bogenansatz)."""
    y0 = cy - h / 2
    if form == "bogen":
        return y0 + max(h - w / 2, h * 0.5)
    if form == "spitzbogen":
        a = min(0.85 * w, h)
        return y0 + max(h - a, h * 0.45)
    return cy


def window_shape(form: str, cx: float, cy: float, w: float, h: float, tol: float = 0.05) -> List[Point]:
    x0, y0 = cx - w / 2, cy - h / 2
    if form == "rechteck":
        return rect(x0, y0, w, h)
    if form == "rund":
        return circle(cx, cy, min(w, h) / 2, tol)
    if form == "bogen":
        return arched(cx, y0, w, h, tol)
    if form == "spitzbogen":
        return pointed_arch(cx, y0, w, h, tol)
    if form == "raute":
        return [(cx, y0), (cx + w / 2, cy), (cx, y0 + h), (cx - w / 2, cy)]
    if form == "herz":
        return heart(cx, cy, w, min(h, 0.95 * w))
    if form == "stern":
        r = min(w, h) / 2
        return star(cx, cy + 0.05 * r, r, 0.46 * r)
    raise ValueError(f"Fensterform {form!r} unbekannt – erlaubt: {', '.join(values(WINDOW_FORMS))}")


def _clip_half(poly: Sequence[Point], a: float, b: float, c: float) -> List[Point]:
    """Sutherland–Hodgman: Teil des (konvexen) Polygons mit a·x + b·y ≤ c. Knoten, die zu dicht
    neben einem Schnittpunkt liegen, fallen weg (sonst Mini-Segmente nach dem Kerf-Versatz)."""
    out: List[Point] = []
    cuts: List[Point] = []
    n = len(poly)
    for i in range(n):
        p, q = poly[i], poly[(i + 1) % n]
        fp, fq = a * p[0] + b * p[1] - c, a * q[0] + b * q[1] - c
        if fp <= 0:
            out.append(p)
        if (fp < 0 < fq) or (fq < 0 < fp):
            t = fp / (fp - fq)
            x = (p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1]))
            out.append(x)
            cuts.append(x)
    if len(out) < 3:
        return []
    out = drop_close(clean(out), 0.2, keep=cuts)
    return out if len(out) >= 3 else []


def window_panes(form: str, shape: List[Point], cx: float, ys: float, m: float, muntins: str) -> List[List[Point]]:
    """Scheiben eines Fensters (Durchbrüche), getrennt durch Sprossen der Breite m."""
    if form not in CONVEX or muntins == "keine":
        return [shape]
    parts = [oriented(shape, True)]
    if muntins in ("kreuz", "senkrecht"):
        parts = [q for p in parts for q in (_clip_half(p, 1, 0, cx - m / 2), _clip_half(p, -1, 0, -(cx + m / 2)))]
    if muntins in ("kreuz", "waagrecht"):
        parts = [q for p in parts for q in (_clip_half(p, 0, 1, ys - m / 2), _clip_half(p, 0, -1, -(ys + m / 2)))]
    out = []
    for p in parts:
        if len(p) >= 3 and signed_area(oriented(p, True)) > 1.5 and inset_polygon(p, 0.45):
            out.append(oriented(p, True))
    return out


def add_window(cv: Canvas, form: str, cx: float, cy: float, w: float, h: float, mode: str,
               muntins: str = "kreuz", deco: str = "rahmen", min_web: float = 1.5, tol: float = 0.05) -> None:
    """Fenster mit Sprossen und Schmuck. Durchbrüche nur in mode='cut'."""
    shape = window_shape(form, cx, cy, w, h, tol)
    x0, y0, x1, y1 = bbox(shape)
    m = max(1.6 * min_web, 0.12 * min(w, h))
    ys = spring_y(form, cy, w, h)
    if mode == "cut":
        for pane in window_panes(form, shape, cx, ys, m, muntins):
            cv.add_hole(pane)
    else:
        cv.part.add_engrave(shape, closed=True)
        if form in CONVEX and muntins != "keine":
            inner = _Poly(shape)
            if muntins in ("kreuz", "senkrecht"):
                _engrave_inside(cv.part, inner, (cx, y0 - 1), (cx, y1 + 1))
            if muntins in ("kreuz", "waagrecht"):
                _engrave_inside(cv.part, inner, (x0 - 1, ys), (x1 + 1, ys))
        cv.block(shape, 0.8)
    window_deco(cv, deco, form, shape, cx, w, h)


def _engrave_inside(part: Part, poly: _Poly, a: Point, b: Point) -> None:
    ts = [0.0, 1.0]
    poly.crossings(a, b, (min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1])), ts)
    ts.sort()
    for t0, t1 in zip(ts, ts[1:]):
        tm = (t0 + t1) / 2
        if t1 - t0 > 1e-6 and poly.contains((a[0] + (b[0] - a[0]) * tm, a[1] + (b[1] - a[1]) * tm)):
            part.add_engrave([(a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0),
                              (a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1)])


def deco_extent(deco: str, w: float) -> float:
    """Zusätzlicher Platzbedarf links/rechts eines Fensters (für die Größenberechnung)."""
    if deco in ("laeden", "herzlaeden", "beides"):
        return 1.6 + 0.45 * w
    return 2.2


def window_deco(cv: Canvas, deco: str, form: str, shape: List[Point], cx: float, w: float, h: float) -> None:
    x0, y0, x1, y1 = bbox(shape)
    part = cv.part
    if deco == "keine":
        return
    shutters = deco in ("laeden", "herzlaeden", "beides")
    box = deco in ("blumen", "beides")
    placed = False
    if shutters:
        sw, g = 0.45 * w, 1.6
        items = []
        for sgn in (-1, 1):
            xa = x1 + g if sgn > 0 else x0 - g - sw
            fr = rect(xa, y0, sw, y1 - y0)
            items.append((fr, True))
            if deco == "herzlaeden":
                hw = min(0.55 * sw, 0.3 * (y1 - y0))
                items.append((heart(xa + sw / 2, y0 + 0.66 * (y1 - y0), hw, 0.9 * hw, 40), True))
                for yy in (y0 + 0.18 * (y1 - y0), y0 + 0.4 * (y1 - y0)):
                    items.append(([(xa + 0.6, yy), (xa + sw - 0.6, yy)], False))
            else:
                k = max(3, int((y1 - y0 - 1.2) / 1.5))
                for i in range(1, k):
                    yy = y0 + (y1 - y0) * i / k
                    items.append(([(xa + 0.6, yy), (xa + sw - 0.6, yy)], False))
        placed = cv.put_all(items, reserve=0.6)
    if box:
        bh = min(max(0.28 * h, 3.0), 6.0)
        gap = 3.6
        bx0, bx1 = x0 - 1.5, x1 + 1.5
        by1 = y0 - gap
        items = [(rect(bx0, by1 - bh, bx1 - bx0, bh), True),
                 ([(bx0 + 0.8, by1 - bh / 2), (bx1 - 0.8, by1 - bh / 2)], False)]
        k = max(2, int((bx1 - bx0) / 3.2))
        for i in range(k):
            fx = bx0 + (bx1 - bx0) * (i + 0.5) / k
            items.append(([(fx, by1), (fx, by1 + 1.1)], False))
            items.append((circle(fx, by1 + 1.65, 0.55, 0.03), True))
        if cv.put_all(items, reserve=0.6):
            placed = True
    if deco == "schnee":
        cap = [(x0 - 1.4, y1 + 1.7)]
        n = max(3, int((x1 - x0 + 2.8) / 2.2))
        for i in range(n + 1):
            x = x0 - 1.4 + (x1 - x0 + 2.8) * i / n
            cap.append((x, y1 + 1.7 + (1.6 if i % 2 else 1.1) + 0.3 * math.sin(i)))
        cap.append((x1 + 1.4, y1 + 1.7))
        sill = [(x0 - 1.8, y0 - 1.8), (x1 + 1.8, y0 - 1.8)]
        if cv.put_all([(cap, True), (sill, False)], reserve=0.6):
            return
    if deco == "rahmen" or not placed:
        if form == "rechteck":
            items = [([(x0 - 2, y0 - 1.5), (x1 + 2, y0 - 1.5)], False),
                     ([(x0 - 1, y1 + 1.5), (x1 + 1, y1 + 1.5)], False)]
        else:
            items = [(grow(shape, 1.5), True), ([(x0 - 2, y0 - 2.6), (x1 + 2, y0 - 2.6)], False)]
        cv.put_all(items, reserve=0.6) or cv.put_all(items[:1], reserve=0.6)


# ---------------------------------------------------------------------------
# Türen
# ---------------------------------------------------------------------------

def door_shape(kind: str, cx: float, y0: float, w: float, h: float, tol: float = 0.05) -> List[Point]:
    """Türkontur, beginnend unten links → unten rechts → … (für den offenen Rahmen)."""
    if kind == "arched":
        return arched(cx, y0, w, h, tol)
    if kind == "rect":
        return rect(cx - w / 2, y0, w, h)
    if kind == "spitzbogen":
        return pointed_arch(cx, y0, w, h, tol)
    if kind == "rund":
        r = w / 2
        k = 0.9                                 # Kreismitte 0.9·r über der Schwelle
        a = math.asin(k)
        xb = r * math.cos(a)
        arc = arc_points(cx, y0 + k * r, r, -a, math.pi + a, tol)
        return clean([(cx - xb, y0), (cx + xb, y0)] + arc[1:-1])
    raise ValueError(f"Tür {kind!r} unbekannt – erlaubt: {', '.join(values(DOORS))}")


def door_size(kind: str, W: float, H: float) -> Tuple[float, float]:
    dw = max(12.0, min(32.0, 0.28 * W))
    dh = min(0.62 * H, 1.9 * dw)
    if kind == "rund":
        dw = min(dw * 1.12, 0.62 * H / 0.95, 34.0)
        dh = 0.95 * dw
    return dw, dh


def add_door(cv: Canvas, kind: str, cx: float, y0: float, w: float, h: float, mode: str,
             deco: str = "rahmen", tol: float = 0.05, seed: int = 0, with_deco: bool = True) -> float:
    """Tür mit Rahmen (+ Schmuck, wenn with_deco). Liefert die Oberkante für die Schild-Platzierung.
    Mit with_deco=False kommt der Schmuck später über door_deco – nach den Fenstern."""
    if kind == "none":
        return y0
    shape = door_shape(kind, cx, y0, w, h, tol)
    top = max(p[1] for p in shape)
    part = cv.part
    if mode == "cut":
        cv.add_hole(shape)
    else:
        part.add_engrave(shape, closed=True)
        inner = _Poly(shape)
        for k in range(1, 4):                                   # Bretter
            x = cx - w / 2 + k * w / 4
            _engrave_inside(part, inner, (x, y0 + 1.0), (x, top - 1.0))
        cv.block(shape, 0.6)
        if deco != "kranz":
            knob = circle(cx + w * 0.3, y0 + h * 0.42, 1.2, tol)
            if all(inner.contains(p) for p in knob):
                part.add_engrave(knob, closed=True)
    fr = door_shape(kind, cx, y0, w + 3.0, h + 1.5, tol)
    frame = fr[1:] + [fr[0]]                                    # offen: ohne Schwelle
    if deco in ("rahmen", "vordach", "laternen", "girlande", "kranz"):
        if cv.fits(frame, closed=False):
            part.add_engrave(frame)
            cv.block_box(bbox(fr), 0.6)
    if not with_deco:
        return top + 1.5
    return door_deco(cv, kind, cx, y0, w, h, mode, deco, tol, seed)


def door_deco_height(deco: str, w: float, mode: str) -> float:
    """Platz, den der Türschmuck über dem Türrahmen braucht (für die Schild-Platzierung)."""
    if deco == "vordach":
        return 3.0 + 0.38 * (w / 2 + 3.6) + 1.8
    if deco == "girlande":
        return 5.5
    if deco == "kranz" and mode != "engrave":
        R = max(3.0, min(0.22 * w, 6.0))
        return 2.8 + 2.45 * R + 1.0
    return 0.0


def door_deco(cv: Canvas, kind: str, cx: float, y0: float, w: float, h: float, mode: str,
              deco: str = "rahmen", tol: float = 0.05, seed: int = 0) -> float:
    """Türschmuck (Vordach, Laternen, Girlande, Kranz). Liefert die Oberkante inkl. Schmuck."""
    if kind == "none":
        return y0
    part = cv.part
    shape = door_shape(kind, cx, y0, w, h, tol)
    top = max(p[1] for p in shape)
    top_ext = top + 1.5
    if deco == "vordach":
        ov = 3.6
        hw = w / 2 + ov
        rise = 0.38 * hw
        ya = top + 3.0
        roof1 = [(cx - hw, ya), (cx, ya + rise), (cx + hw, ya)]
        roof2 = [(cx - hw + 0.4, ya + 1.2), (cx, ya + rise + 1.2), (cx + hw - 0.4, ya + 1.2)]
        br = [[(cx + sgn * (hw - 0.4), ya), (cx + sgn * (hw - 0.4), ya - 2.4)] for sgn in (-1, 1)]
        if cv.put_all([(roof1, False), (roof2, False)] + [(b, False) for b in br], reserve=0.6):
            top_ext = ya + rise + 1.2
    elif deco == "laternen":
        lw = max(3.5, min(7.0, 0.3 * w))
        lh = 1.7 * lw
        for sgn in (-1, 1):
            lx = cx + sgn * (w / 2 + 1.5 + 1.6 + lw / 2)
            ly = y0 + 0.55 * h
            body = [(lx - 0.42 * lw, ly), (lx + 0.42 * lw, ly), (lx + 0.5 * lw, ly + 0.62 * lh),
                    (lx - 0.5 * lw, ly + 0.62 * lh)]
            capt = [(lx - 0.62 * lw, ly + 0.62 * lh), (lx, ly + 0.86 * lh), (lx + 0.62 * lw, ly + 0.62 * lh)]
            items = [(body, True), (capt, True),
                     ([(lx, ly + 0.08 * lh), (lx, ly + 0.55 * lh)], False),
                     ([(lx - 0.42 * lw, ly + 0.31 * lh), (lx + 0.42 * lw, ly + 0.31 * lh)], False),
                     ([(lx, ly + 0.86 * lh), (lx, ly + lh), (lx + sgn * 0.55 * lw, ly + lh)], False),
                     (circle(lx, ly - 0.35, 0.3, 0.03), True)]
            cv.put_all(items, reserve=0.5)
    elif deco == "girlande":
        W2 = w + 8.4
        g = door_shape(kind, cx, y0, W2, h + 4.2, tol)
        y_thr = y0 + 0.7 * h
        ring = g[1:] + [g[0]]                               # rechts hoch, oben drüber, links runter
        path = [p for p in ring if p[1] >= y_thr]
        if kind != "rund":
            path = [(cx + W2 / 2, y_thr)] + path + [(cx - W2 / 2, y_thr)]
        if len(path) >= 2:
            styled_line(cv, path, "girlande", max(3.0, min(5.0, 0.18 * w)), side=+1, seed=seed)
            top_ext = top + 5.0
    elif deco == "kranz":
        R = max(3.0, min(0.3 * w, 8.0)) if mode == "engrave" else max(3.0, min(0.22 * w, 6.0))
        if mode == "engrave":
            c = (cx, y0 + h - max(R + 2.0, h * 0.28))
        else:
            c = (cx, top + 2.8 + 1.45 * R)
        items = [(circle(c[0], c[1], R, tol), True), (circle(c[0], c[1], 0.55 * R, tol), True)]
        rng = random.Random(seed)
        for i in range(7):
            a = 2 * math.pi * (i + rng.random() * 0.5) / 7
            rr = 0.78 * R
            items.append((circle(c[0] + rr * math.cos(a), c[1] + rr * math.sin(a), 0.11 * R, 0.03), True))
        bw = 0.35 * R
        items.append(([(c[0], c[1] - R), (c[0] - bw, c[1] - R + 0.4 * bw), (c[0] - bw, c[1] - R - 0.4 * bw),
                       (c[0], c[1] - R), (c[0] + bw, c[1] - R + 0.4 * bw), (c[0] + bw, c[1] - R - 0.4 * bw),
                       (c[0], c[1] - R)], False))
        items.append(([(c[0], c[1] - R), (c[0] - 0.5 * bw, c[1] - R - 1.1 * bw)], False))
        items.append(([(c[0], c[1] - R), (c[0] + 0.5 * bw, c[1] - R - 1.1 * bw)], False))
        if mode == "engrave":
            for p, cl in items:
                part.add_engrave(p, closed=cl)
        elif cv.put_all(items, reserve=0.6):
            top_ext = c[1] + R + 0.5
    return top_ext


# ---------------------------------------------------------------------------
# Giebel
# ---------------------------------------------------------------------------

def gable_deco(cv: Canvas, kind: str, cx: float, cy: float, r: float, mode: str, text: str = "",
               style: str = "normal", case: str = "gross", text_box: Optional[Box] = None,
               tol: float = 0.05) -> Optional[Box]:
    """Giebelschmuck um (cx, cy) mit Radius r. Liefert die belegte Fläche."""
    part = cv.part
    if kind == "keins" or r < 3.0 and kind != "text":
        return None
    if kind in ("rundfenster", "herz", "stern"):
        if kind == "rundfenster":
            shape = circle(cx, cy, r, tol)
        elif kind == "herz":
            shape = heart(cx, cy, 2.1 * r, 1.9 * r)
        else:
            shape = star(cx, cy + 0.05 * r, 1.12 * r, 0.5 * 1.12 * r)
        if mode == "cut":
            cv.add_hole(shape)
        else:
            part.add_engrave(shape, closed=True)
        ring = circle(cx, cy, r + 1.5, tol) if kind == "rundfenster" else grow(shape, 1.4)
        if cv.fits(ring):
            part.add_engrave(ring, closed=True)
        cv.block(ring, 0.8)
        return bbox(ring)
    if kind == "uhr":
        R = r + 1.0
        items = [(circle(cx, cy, R, tol), True), (circle(cx, cy, R - 0.9, tol), True)]
        for k in range(12):
            a = math.pi / 2 - k * math.pi / 6
            l = 0.24 * R if k % 3 == 0 else 0.12 * R
            ro = R - 1.6
            items.append(([(cx + ro * math.cos(a), cy + ro * math.sin(a)),
                           (cx + (ro - l) * math.cos(a), cy + (ro - l) * math.sin(a))], False))
        items.append(([(cx, cy), (cx + 0.42 * R * math.cos(math.radians(97)), cy + 0.42 * R * math.sin(math.radians(97)))], False))
        items.append(([(cx, cy), (cx + 0.66 * R * math.cos(math.radians(120)), cy + 0.66 * R * math.sin(math.radians(120)))], False))
        if cv.put_all(items, reserve=0.8):
            return (cx - R, cy - R, cx + R, cy + R)
        return None
    if kind == "luke":
        w, h = 1.5 * r, 1.7 * r
        x0, y0 = cx - w / 2, cy - h / 2
        items = [(rect(x0, y0, w, h), True), (rect(x0 - 1.2, y0 - 1.2, w + 2.4, h + 2.4), True),
                 ([(x0, y0), (x0 + w, y0 + h)], False), ([(x0, y0 + h), (x0 + w, y0)], False)]
        if cv.put_all(items, reserve=0.8):
            return (x0 - 1.2, y0 - 1.2, x0 + w + 1.2, y0 + h + 1.2)
        return None
    if kind == "text":
        if not text.strip() or text_box is None:
            return None
        return sign(cv, text, "ohne", [text_box], style, case, min_h=2.5, max_cap=8.0)
    raise ValueError(f"Giebel {kind!r} unbekannt – erlaubt: {', '.join(values(GABLES))}")


# ---------------------------------------------------------------------------
# Schilder
# ---------------------------------------------------------------------------

def _pads(form: str, c: float) -> Tuple[float, float]:
    return {"ohne": (0.25 * c, 0.25 * c), "rahmen": (0.8 * c + 1.6, 0.55 * c + 1.5),
            "rund": (1.0 * c + 1.2, 0.55 * c + 1.3), "oval": (1.0 * c + 1.5, 0.55 * c + 1.3),
            "banner": (0.7 * c + 1.0, 0.5 * c + 1.0), "holz": (1.2 * c + 2.4, 0.55 * c + 1.4),
            "geschweift": (1.0 * c + 1.8, 0.6 * c + 1.6)}[form]


def _extra_w(form: str, h: float) -> float:
    """Zusätzliche Breite außerhalb der Hauptfläche (Banner-Enden)."""
    return 2 * 0.55 * h if form == "banner" else 0.0


def _sign_items(form: str, x0: float, y0: float, x1: float, y1: float, tol: float):
    """Geometrie des Schilds: (Liste (Punkte, geschlossen), Umriss für die Sperrfläche)."""
    w, h = x1 - x0, y1 - y0
    if form == "ohne":
        return [], rect(x0, y0, w, h)
    if form == "rahmen":
        return [(rect(x0, y0, w, h), True), (rect(x0 + 0.8, y0 + 0.8, w - 1.6, h - 1.6), True)], rect(x0, y0, w, h)
    if form == "rund":
        o = rounded_rect(x0, y0, x1, y1, 0.42 * h, tol)
        return [(o, True)], o
    if form == "oval":
        o = ellipse((x0 + x1) / 2, (y0 + y1) / 2, w / 2, h / 2, 96)
        return [(o, True), (ellipse((x0 + x1) / 2, (y0 + y1) / 2, w / 2 - 0.8, h / 2 - 0.8, 96), True)], o
    if form == "banner":
        tw, dy = 0.55 * h, 0.28 * h
        items = [(rect(x0, y0, w, h), True)]
        for sgn, xe in ((-1, x0), (1, x1)):
            xt = xe + sgn * tw
            items.append(([(xe, y0 - dy), (xt, y0 - dy), (xt - sgn * 0.35 * tw, y0 - dy + h / 2),
                           (xt, y1 - dy), (xe, y1 - dy)], False))
            items.append(([(xe, y0 - dy), (xe - sgn * 0.3 * tw, y0)], False))
        outline = [(x0 - tw, y0 - dy), (x1 + tw, y0 - dy), (x1 + tw, y1), (x0 - tw, y1)]
        return items, outline
    if form == "holz":
        o = rounded_rect(x0, y0, x1, y1, 0.12 * h, tol)
        items = [(o, True)]
        for sgn, xe in ((1, x0), (-1, x1)):
            items.append((circle(xe + sgn * 0.11 * w if w < 9 * h else xe + sgn * 1.1 * h * 0.6, (y0 + y1) / 2,
                                 max(0.35, 0.07 * h), 0.03), True))
        for k, f in enumerate((0.28, 0.72)):
            yy = y0 + f * h
            items.append(([(x0 + 0.8, yy), (x0 + 0.8 + 0.12 * w, yy + (0.4 if k else -0.4))], False))
            items.append(([(x1 - 0.8, yy), (x1 - 0.8 - 0.12 * w, yy + (-0.4 if k else 0.4))], False))
        return items, o
    if form == "geschweift":
        r = 0.3 * h
        o = scalloped_rect(x0, y0, x1, y1, r, tol)
        inner = scalloped_rect(x0 + 0.9, y0 + 0.9, x1 - 0.9, y1 - 0.9, r, tol)
        return [(o, True), (inner, True)], rect(x0, y0, w, h)
    raise ValueError(f"Schildform {form!r} unbekannt – erlaubt: {', '.join(values(SIGNS))}")


def top_runs(loop: Sequence[Point], min_len: float = 8.0, slope: float = 1.2) -> List[List[Point]]:
    """Obere Kantenzüge eines gegen den Uhrzeigersinn laufenden Umrisses (Kanten, die nach links
    laufen und höchstens 'slope' steil sind) – dort hängen Eiszapfen & Co. natürlich herab."""
    pts = list(loop)
    if len(pts) < 3:
        return []
    n = len(pts)
    top = [(pts[(i + 1) % n][0] - pts[i][0]) < 0 and
           abs(pts[(i + 1) % n][1] - pts[i][1]) <= slope * abs(pts[(i + 1) % n][0] - pts[i][0])
           for i in range(n)]
    if all(top):
        return [pts + [pts[0]]]
    start = next(i for i in range(n) if not top[i])        # bei einer Nicht-Oberkante beginnen
    runs, cur = [], []
    for k in range(1, n + 1):
        i = (start + k) % n
        if top[i]:
            if not cur:
                cur = [pts[i]]
            cur.append(pts[(i + 1) % n])
        elif cur:
            runs.append(cur)
            cur = []
    if cur:
        runs.append(cur)
    return [r for r in runs if sum(dist(a, b) for a, b in zip(r, r[1:])) >= min_len]


def free_rects(cv: Canvas, cx: float, cy: float, heights: Sequence[float],
               shifts: Sequence[float] = (0.0,), min_w: float = 4.0, max_w: float = 2000.0) -> List[Box]:
    """Größte freie, um cx zentrierte Rechtecke je Höhe und Höhenversatz – größte Fläche zuerst."""
    out = []
    for h in heights:
        for dy in shifts:
            y0, y1 = cy + dy - h / 2, cy + dy + h / 2

            def ok(hw: float) -> bool:
                return cv.fits(rect(cx - hw, y0, 2 * hw, h), solid=True)
            lo = min_w / 2
            if not ok(lo):
                continue
            hi = min(lo * 2, max_w / 2)
            while hi > lo and ok(hi) and hi < max_w / 2:
                lo, hi = hi, min(hi * 2, max_w / 2)
            if hi <= lo or ok(hi):
                out.append((cx - hi, y0, cx + hi, y1))
                continue
            for _ in range(14):
                mid = (lo + hi) / 2
                lo, hi = (mid, hi) if ok(mid) else (lo, mid)
            out.append((cx - lo, y0, cx + lo, y1))
    out.sort(key=lambda b: -(b[2] - b[0]) * (b[3] - b[1]))
    return out


def wrap_variants(text: str) -> List[str]:
    """Der Text selbst und – wenn er Leerzeichen, aber keinen Zeilenumbruch hat – auf 2 bzw. 3
    möglichst gleich lange Zeilen umbrochene Fassungen."""
    out = [text]
    if "|" in text or "\n" in text:
        return out
    words = text.split()
    if len(words) < 2:
        return out
    best2 = min(range(1, len(words)), key=lambda k: abs(len(" ".join(words[:k])) - len(" ".join(words[k:]))))
    out.append(" ".join(words[:best2]) + "|" + " ".join(words[best2:]))
    if len(words) >= 3:
        cands = [(a, b) for a in range(1, len(words) - 1) for b in range(a + 1, len(words))]
        a, b = min(cands, key=lambda ab: max(len(" ".join(words[:ab[0]])), len(" ".join(words[ab[0]:ab[1]])),
                                              len(" ".join(words[ab[1]:]))))
        out.append(" ".join(words[:a]) + "|" + " ".join(words[a:b]) + "|" + " ".join(words[b:]))
    return out


def _fit_sign_text(text: str, form: str, W0: float, H0: float, sx: float, sy: float, style: str,
                   case: str, min_h: float, max_cap: float):
    """Text samt Rahmenabständen in W0×H0 einpassen → (Striche, Schrifthöhe) oder None."""
    n_lines = text.replace("|", "\n").count("\n") + 1
    cap = max_cap
    for _ in range(24):
        px, py = _pads(form, cap)
        iw = W0 / sx - 2 * px - _extra_w(form, min(H0, 2 * py + cap * (n_lines * 1.55 - 0.55)))
        ih = H0 / (sy * (1.28 if form == "banner" else 1.0)) - 2 * py      # Banner-Enden hängen tiefer
        if iw > 1 and ih >= min(cap, min_h):
            try:
                strokes, c2 = fit_text(text, 0.0, 0.0, iw, ih, min_h, cap, style, case)
            except ValueError:
                strokes = None
            if strokes is not None:
                if c2 >= cap - 0.01:
                    return strokes, cap
                cap = c2                                  # kleinere Schrift → schmalerer Rahmen
                continue
        cap *= 0.85                                       # Rahmen frisst den Platz → kleiner
        if cap < min_h:
            return None
    return None


def sign(cv: Canvas, text: str, form: str, cands: Sequence[Box], style: str = "normal",
         case: str = "gross", min_h: float = 3.0, max_cap: float = 9.0, anchor: str = "unten",
         tol: float = 0.05, wrap: bool = True) -> Optional[Box]:
    """Schild mit Text in die erste passende Fläche setzen. cands = freie Rechtecke (x0,y0,x1,y1).
    Passt der Text einzeilig nicht gut, wird er an Leerzeichen umbrochen (wrap).
    Liefert die belegte Fläche oder None (dann wurde nichts gezeichnet)."""
    if not text.strip():
        return None
    variants = wrap_variants(text) if wrap else [text]
    sx, sy = (1.18, 1.12) if form == "oval" else (1.0, 1.0)
    for bx0, by0, bx1, by1 in cands:
        mw, mh = bx1 - bx0, by1 - by0
        if mw < 4 or mh < min_h:
            continue
        cxb = (bx0 + bx1) / 2
        for shrink in (1.0, 0.86, 0.74, 0.64, 0.55, 0.47, 0.4):
            W0 = mw * shrink
            H0 = mh * min(1.0, shrink * 1.15)
            fits = []
            for k, t in enumerate(variants):
                r = _fit_sign_text(t, form, W0, H0, sx, sy, style, case, min_h, max_cap)
                if r is None:
                    continue
                strokes, cap = r
                tx0, ty0, tx1, ty1 = bbox([p for st in strokes for p in st])
                px, py = _pads(form, cap)
                w, h = ((tx1 - tx0) + 2 * px) * sx, ((ty1 - ty0) + 2 * py) * sy
                if w + _extra_w(form, h) > mw + 1e-6 or h * (1.28 if form == "banner" else 1.0) > mh + 1e-6:
                    continue
                # einzeilig bevorzugen, Umbruch nur bei deutlich größerer Schrift
                fits.append((cap * (1.0 if k == 0 else 0.8), strokes, (tx0, ty0, tx1, ty1), w, h))
            fits.sort(key=lambda f: -f[0])
            for _, strokes, (tx0, ty0, tx1, ty1), w, h in fits:
                lo_c = by0 + h / 2 + (0.28 * h if form == "banner" else 0.0)
                hi_c = by1 - h / 2
                if hi_c < lo_c - 1e-6:
                    continue
                n = max(1, int((hi_c - lo_c) / 0.8))
                ys = [lo_c + (hi_c - lo_c) * i / n for i in range(n + 1)]
                if anchor != "unten":
                    mid = (lo_c + hi_c) / 2
                    ys.sort(key=lambda v: abs(v - mid))
                for cy in ys:
                    dx, dy = cxb - (tx0 + tx1) / 2, cy - (ty0 + ty1) / 2
                    moved = [[(x + dx, y + dy) for x, y in st] for st in strokes]
                    x0, y0, x1, y1 = cxb - w / 2, cy - h / 2, cxb + w / 2, cy + h / 2
                    items, outline = _sign_items(form, x0, y0, x1, y1, tol)
                    if not cv.fits(outline, solid=True):
                        continue
                    if cv.put_all(items + [(st, False) for st in moved], reserve=1.0, outline=outline):
                        return bbox(outline)
    return None
    last_err = None
    for bx0, by0, bx1, by1 in cands:
        mw, mh = bx1 - bx0, by1 - by0
        if mw < 4 or mh < min_h:
            continue
        cxb = (bx0 + bx1) / 2
        n_lines = text.count("\n") + 1
        sx, sy = (1.18, 1.12) if form == "oval" else (1.0, 1.0)
        for shrink in (1.0, 0.86, 0.74, 0.64, 0.55, 0.47, 0.4):
            W0 = mw * shrink
            H0 = mh * min(1.0, shrink * 1.15)
            cap = max_cap
            strokes = None
            for _ in range(24):
                px, py = _pads(form, cap)
                iw = W0 / sx - 2 * px - _extra_w(form, min(H0, 2 * py + cap * (n_lines * 1.55 - 0.55)))
                ih = H0 / sy - 2 * py
                if iw > 1 and ih >= min(cap, min_h):
                    try:
                        strokes, c2 = fit_text(text, 0.0, 0.0, iw, ih, min_h, cap, style, case)
                    except ValueError as e:
                        last_err, strokes = e, None
                    if strokes is not None:
                        if c2 >= cap - 0.01:
                            break
                        cap = c2                                  # kleinere Schrift → schmalerer Rahmen
                        continue
                cap *= 0.85                                       # Rahmen frisst den Platz → kleiner
                if cap < min_h:
                    strokes = None
                    break
            if not strokes:
                continue
            tx0, ty0, tx1, ty1 = bbox([p for s in strokes for p in s])
            px, py = _pads(form, cap)
            w, h = (tx1 - tx0) + 2 * px, (ty1 - ty0) + 2 * py
            w, h = w * sx, h * sy
            ext = _extra_w(form, h)
            if w + ext > mw + 1e-6 or h > mh + 1e-6:
                continue
            lo_c = by0 + h / 2 + (0.28 * h if form == "banner" else 0.0)
            hi_c = by1 - h / 2
            if hi_c < lo_c - 1e-6:
                continue
            n = max(1, int((hi_c - lo_c) / 0.8))
            ys = [lo_c + (hi_c - lo_c) * i / n for i in range(n + 1)]
            if anchor != "unten":
                mid = (lo_c + hi_c) / 2
                ys.sort(key=lambda v: abs(v - mid))
            for cy in ys:
                dx, dy = cxb - (tx0 + tx1) / 2, cy - (ty0 + ty1) / 2
                moved = [[(x + dx, y + dy) for x, y in st] for st in strokes]
                x0, y0, x1, y1 = cxb - w / 2, cy - h / 2, cxb + w / 2, cy + h / 2
                items, outline = _sign_items(form, x0, y0, x1, y1, tol)
                if not cv.fits(outline, solid=True):
                    continue
                if cv.put_all(items + [(st, False) for st in moved], reserve=1.0, outline=outline):
                    return bbox(outline)
    return None


# ---------------------------------------------------------------------------
# Wand- und Dachmuster
# ---------------------------------------------------------------------------

def wall_pattern(cv: Canvas, kind: str, box: Box, unit: float, seed: int = 1,
                 rails: Sequence[float] = (), gable: Optional[Tuple[float, float, float]] = None) -> None:
    """Füllt 'box' (x0,y0,x1,y1) mit einem Muster; alles Belegte wird ausgespart.
    rails: Höhen für Fachwerk-Riegel; gable: (x_mitte, y_traufe, y_first) für das Giebeldreieck."""
    if kind in ("keine", None, ""):
        return
    x0, y0, x1, y1 = box
    rng = random.Random(seed)
    u = unit
    if kind == "holz":
        y = y0 + u
        while y < y1:
            cv.draw([(x0, y), (x1, y)])
            x = x0 + rng.uniform(4, 30)
            while x < x1:
                cv.draw([(x, y), (x, min(y + u, y1))])
                if rng.random() < 0.25:
                    kx = x + rng.uniform(3, 9)
                    cv.put(ellipse(kx, y + u / 2, 0.9, 0.42, 20))
                x += rng.uniform(14, 34)
            y += u
    elif kind == "ziegel":
        row, L = 0.8 * u, 2.1 * u
        y, k = y0 + row, 0
        while y < y1 + row:
            if y < y1:
                cv.draw([(x0, y), (x1, y)])
            x = x0 + (L / 2 if k % 2 else L) - L
            while x < x1:
                if x > x0:
                    cv.draw([(x, y - row), (x, min(y, y1))])
                x += L
            y += row
            k += 1
    elif kind == "stein":
        y = y0 + 0.3
        while y < y1:
            rh = u * rng.uniform(1.1, 1.6)
            x = x0 - rng.uniform(0, 4)
            while x < x1:
                sw = rh * rng.uniform(1.2, 2.3)
                cv.draw(rounded_rect(x + 0.35, y + 0.35, x + sw - 0.35, y + rh - 0.35, 0.32 * rh, 0.08), closed=True)
                x += sw
            y += rh
    elif kind == "fachwerk":
        def beam(p, q):
            L = dist(p, q)
            if L < 1e-6:
                return
            nx, ny = -(q[1] - p[1]) / L, (q[0] - p[0]) / L
            for o in (-0.42, 0.0, 0.42):                       # kräftige Linie aus drei Strichen
                cv.draw([(p[0] + nx * o, p[1] + ny * o), (q[0] + nx * o, q[1] + ny * o)])

        top = gable[1] if gable else y1
        levels = sorted({y0 + 1.5, top - (0.0 if gable else 1.5),
                         *[r for r in rails if y0 + 5 < r < top - 5]})
        posts = {x0 + 1.5, x1 - 1.5}
        for B in cv.blocks:                                    # Pfosten neben Fenstern und Tür
            bx0, by0, bx1, by1 = B.bb
            if bx1 - bx0 < 4 or by1 - by0 < 4 or bx1 - bx0 > 0.8 * (x1 - x0) or by0 > top or by1 < y0:
                continue
            for x in (bx0 - 1.0, bx1 + 1.0):
                if x0 + 4 < x < x1 - 4:
                    posts.add(x)
        posts = sorted(posts)
        merged = [posts[0]]
        for x in posts[1:]:
            if x - merged[-1] < 4.0:
                merged[-1] = (merged[-1] + x) / 2 if merged[-1] not in (x0 + 1.5,) else merged[-1]
            else:
                merged.append(x)
        posts = []
        for xa, xb in zip(merged, merged[1:]):
            posts.append(xa)
            k = int((xb - xa) / 24.0)
            posts += [xa + (xb - xa) * (i + 1) / (k + 1) for i in range(k)]
        posts.append(merged[-1])
        for lv in levels:
            beam((x0, lv), (x1, lv))
        for ya, yb in zip(levels, levels[1:]):
            for x in posts:
                beam((x, ya), (x, yb))
            for i, (xa, xb) in enumerate(zip(posts, posts[1:])):
                pw, ph = xb - xa, yb - ya
                if pw < 5 or ph < 5 or not cv.fits(rect(xa + 0.8, ya + 0.8, pw - 1.6, ph - 1.6)):
                    continue
                if pw > 1.3 * ph:
                    beam((xa, ya), (xb, yb))
                    beam((xa, yb), (xb, ya))
                elif i % 2 == 0:
                    beam((xa, ya), (xb, yb))
                else:
                    beam((xa, yb), (xb, ya))
        if gable:
            gx, gy0, gy1 = gable
            beam((gx, gy0), (gx, gy1))
            hw = (x1 - x0) / 2
            beam((gx - 0.6 * hw, gy0), (gx, gy0 + 0.55 * (gy1 - gy0)))
            beam((gx + 0.6 * hw, gy0), (gx, gy0 + 0.55 * (gy1 - gy0)))
    elif kind == "schuppen":
        r = 0.75 * u
        y, k = y1 - 0.2, 0
        while y > y0 - r:
            x = x0 + (r if k % 2 else 0.0) - 2 * r
            while x < x1 + r:
                cv.draw(arc_points(x, y, r, math.pi, 2 * math.pi, 0.05))
                x += 2 * r
            y -= r
            k += 1
    elif kind == "putz":
        n = int((x1 - x0) * (y1 - y0) / 16.0)
        for _ in range(n):
            p = (rng.uniform(x0, x1), rng.uniform(y0, y1))
            cv.put(circle(p[0], p[1], rng.uniform(0.2, 0.32), 0.03))
    elif kind in ("sterne", "herzen"):
        g = max(7.0, 2.0 * u)
        y, row = y0 + g / 2, 0
        while y < y1:
            x = x0 + g / 2 + (g / 2 if row % 2 else 0)
            while x < x1:
                cx, cy = x + rng.uniform(-0.2, 0.2) * g, y + rng.uniform(-0.2, 0.2) * g
                r = rng.uniform(0.17, 0.24) * g
                shape = star(cx, cy, r, 0.45 * r, 5, math.pi / 2 + rng.uniform(-0.3, 0.3)) if kind == "sterne" \
                    else heart(cx, cy, 1.6 * r, 1.4 * r, 36)
                cv.put(shape)
                x += g
            y += 0.87 * g
            row += 1
    else:
        raise ValueError(f"Wandmuster {kind!r} unbekannt – erlaubt: {', '.join(values(WALLS))}")


def roof_pattern(cv: Canvas, kind: str, box: Box, row: float = 6.0, seed: int = 1) -> None:
    """Dachgravur in 'box'; die Traufe liegt bei y0 (Ziegelkanten zeigen dorthin)."""
    if kind in ("keine", None, ""):
        return
    x0, y0, x1, y1 = box
    rng = random.Random(seed)
    if kind in ("ziegel", "schnee"):
        start = y0
        if kind == "schnee":
            sh = min(2.2 * row, 0.35 * (y1 - y0))
            n = max(4, int((x1 - x0) / 3.0))
            wave = [(x0 + (x1 - x0) * i / n, y0 + sh + (0.9 if i % 2 else -0.3) + rng.uniform(-0.4, 0.4))
                    for i in range(n + 1)]
            cv.draw(wave)
            for i in range(1, n, 3):                            # Schneeklumpen
                cv.put(circle(wave[i][0], wave[i][1] - 1.6, 0.45, 0.03))
            start = y0 + sh + 1.5
        tile = 1.35 * row
        y, k = start + row, 0
        while y < y1 + 1e-6:
            cv.draw([(x0, y), (x1, y)])
            x = x0 + (tile / 2 if k % 2 else tile)
            while x < x1 - 0.5:
                cv.draw([(x, y - row), (x, y)])
                x += tile
            y += row
            k += 1
    elif kind == "biber":
        tw = 1.2 * row
        y, k = y0 + 0.2, 0
        while y < y1:
            pts = []
            x = x0 - (tw / 2 if k % 2 else 0.0) - tw
            while x < x1 + tw:
                for j in range(9):
                    a = math.pi + math.pi * j / 8
                    pts.append((x + tw / 2 + tw / 2 * math.cos(a), y + 0.55 * row + 0.55 * row * math.sin(a)))
                x += tw
            cv.draw(pts)
            y += row
            k += 1
    elif kind == "schindel":
        y = y0 + row
        while y < y1 + 1e-6:
            cv.draw([(x0, y), (x1, y)])
            x = x0 + rng.uniform(1, 6)
            while x < x1:
                cv.draw([(x, y - row), (x + rng.uniform(-0.6, 0.6), y)])
                if rng.random() < 0.18:
                    xx = x + rng.uniform(1.0, 2.5)
                    cv.draw([(xx, y - row * 0.9), (xx + 0.3, y - row * rng.uniform(0.35, 0.6))])
                x += rng.uniform(3.5, 8.0)
            y += row
    elif kind == "reet":
        band = 1.6 * row
        y = y0 + 0.2
        while y < y1:
            n = max(6, int((x1 - x0) / 2.5))
            edge = [(x0 + (x1 - x0) * i / n, y + 0.35 * math.sin(i * 1.7)) for i in range(n + 1)]
            cv.draw(edge)
            x = x0 + rng.uniform(0.2, 1.2)
            while x < x1:
                yb = y + 0.4
                cv.draw([(x, yb), (x + rng.uniform(-0.5, 0.5), yb + band * rng.uniform(0.45, 0.9))])
                x += rng.uniform(1.0, 1.7)
            y += band
    elif kind == "sterne":
        g = max(8.0, 1.5 * row)
        y, r_ = y0 + g / 2, 0
        while y < y1:
            x = x0 + g / 2 + (g / 2 if r_ % 2 else 0)
            while x < x1:
                cx, cy = x + rng.uniform(-0.3, 0.3) * g, y + rng.uniform(-0.3, 0.3) * g
                if rng.random() < 0.6:
                    r = rng.uniform(0.14, 0.22) * g
                    cv.put(star(cx, cy, r, 0.42 * r, 5, math.pi / 2 + rng.uniform(-0.4, 0.4)))
                else:
                    cv.put(circle(cx, cy, 0.35, 0.03))
                x += g
            y += 0.87 * g
            r_ += 1
    else:
        raise ValueError(f"Dachmuster {kind!r} unbekannt – erlaubt: {', '.join(values(ROOFS))}")


# ---------------------------------------------------------------------------
# Vorplatz
# ---------------------------------------------------------------------------

def yard(cv: Canvas, kind: str, door_x: float, front_y: float, depth: float, door_w: float, x_range: Tuple[float, float],
         mat_text: str = "", style: str = "normal", case: str = "gross", seed: int = 1) -> None:
    """Gravur auf dem Vorplatz der Bodenplatte. front_y = Vorderkante der Hauswand,
    depth = Tiefe des Vorplatzes (nach -y)."""
    if kind == "keiner":
        return
    rng = random.Random(seed)
    y_top = front_y - 1.6
    if kind in ("matte", "alles"):
        mh = max(6.0, min(0.38 * depth, 12.0))
        avail = x_range[1] - x_range[0] - 4
        widths = [min(max(door_w * f, 12.0), avail) for f in (1.1, 1.4, 1.8, 2.3, 3.0)]
        strokes, mw = [], widths[0]
        if mat_text.strip():
            for mw in widths:
                try:
                    strokes, _ = fit_text(mat_text, door_x, y_top - mh / 2, mw - 3.4, mh - 3.0, 2.0, 5.0, style, case)
                    break
                except ValueError:
                    strokes = []
            if not strokes:
                raise ValueError(f"Fußmatten-Text {mat_text!r} passt nicht (Matte höchstens {widths[-1]:.0f}×{mh:.0f} mm)"
                                 f" – kürzer fassen")
        x0 = door_x - mw / 2
        items = [(rounded_rect(x0, y_top - mh, x0 + mw, y_top, 0.8), True),
                 (rounded_rect(x0 + 0.9, y_top - mh + 0.9, x0 + mw - 0.9, y_top - 0.9, 0.5), True)]
        for i in range(1, int(mw / 1.6)):
            fx = x0 + mw * i / int(mw / 1.6)
            items.append(([(fx, y_top - mh), (fx, y_top - mh - 0.9)], False))
        items += [(st, False) for st in strokes]
        cv.put_all(items, reserve=0.8)
        y_top -= mh + 1.8
    if kind in ("weg", "alles"):
        y = y_top
        k = 0
        while y > front_y - depth + 3.0:
            sw = door_w * rng.uniform(0.38, 0.5)
            sh = min(sw * 0.6, 5.5)
            cx = door_x + (0.16 if k % 2 else -0.16) * door_w + rng.uniform(-0.8, 0.8)
            cv.draw(ellipse(cx, y - sh / 2, sw / 2, sh / 2, 40), closed=True)
            y -= sh + rng.uniform(1.4, 2.4)
            k += 1
    if kind in ("garten", "alles"):
        n = 0
        for side in (-1, 1):
            for j in range(3):
                th = rng.uniform(0.55, 0.85) * min(depth - 3.0, 16.0)
                if th < 5:
                    continue
                tx = door_x + side * (door_w * 0.9 + 4.0 + j * th * 0.75 + rng.uniform(0, 2))
                ty = front_y - depth + 2.0 + rng.uniform(0, max(0.1, depth - th - 4.0))
                tw = 0.62 * th
                tree = [(tx, ty + th), (tx + 0.3 * tw, ty + 0.6 * th), (tx + 0.18 * tw, ty + 0.6 * th),
                        (tx + 0.5 * tw, ty + 0.18 * th), (tx + 0.08 * tw, ty + 0.18 * th),
                        (tx + 0.08 * tw, ty), (tx - 0.08 * tw, ty), (tx - 0.08 * tw, ty + 0.18 * th),
                        (tx - 0.5 * tw, ty + 0.18 * th), (tx - 0.18 * tw, ty + 0.6 * th),
                        (tx - 0.3 * tw, ty + 0.6 * th)]
                if cv.put(oriented(tree, True), reserve=0.8):
                    n += 1
        for _ in range(int((x_range[1] - x_range[0]) * depth / 40)):
            p = (rng.uniform(*x_range), front_y - rng.uniform(1.0, depth))
            cv.put(circle(p[0], p[1], 0.3, 0.03))
