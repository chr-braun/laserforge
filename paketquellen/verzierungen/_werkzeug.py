"""
_werkzeug.py – Werkzeuge der Bibliothek „Verzierungen“ (aus dem Weihnachtsdeko-Paket übernommen).

  lade            Hilfsmodul des Pakets laden (eindeutiger Modulname je Paket)
  wmin            Mindestbreite eines Stegs, der das Ausgleichen der Leinwand sicher übersteht
  figur_teil      Figur → laserfestes Teil (Raster, Stege/Schlitze geprüft, Inseln entfernt)
  zapfen_unten    Steckzapfen an der geraden Unterkante (y = 0) eines Teils einsetzen
  schlitz         exakter Rechteckschlitz (auch gedreht) als Loch + JointFeature
  gravur          Linien kollisionsfrei gravieren (nie über Schnitte, nie über den Rand)
  textzeilen      Text als Strichschrift mit frei wählbarem Buchstabenabstand
  schablone       Text als Schablonenschrift ausschneiden (Brücken halten die Innenformen)
"""
from __future__ import annotations

import math
import os
import sys
import zlib
from typing import List, Optional, Sequence, Tuple

from steckwerk import JointFeature, Part, Point, oriented, rect, signed_area

_here = os.path.dirname(os.path.abspath(__file__))


def lade(name: str):
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


E = lade("_ebenen")
K = E.K
Poly = List[Point]


def wmin(cfg) -> float:
    return cfg.min_web + cfg.kerf + 0.45


def px_fuer(groesse: float) -> float:
    """Rasterweite passend zur Teilgröße (fein genug für Details, schnell genug für große Teile)."""
    return max(0.06, min(0.12, groesse / 1600.0))


def figur_teil(cfg, name: str, fig, notes: List[str], solid: Sequence[Poly] = (), unten_flach: bool = False,
               px: Optional[float] = None, frei: Sequence[Poly] = ()) -> Part:
    """Figur → Teil. solid: Flächen, die sicher Material bleiben (z. B. um Schlitze);
    frei: Flächen, die zusätzlich ausgeschnitten werden (vor dem Prüfen)."""
    x0, y0, x1, y1 = fig.bbox()
    for p in solid:
        xs = [q[0] for q in p]
        ys = [q[1] for q in p]
        x0, y0, x1, y1 = min(x0, min(xs)), min(y0, min(ys)), max(x1, max(xs)), max(y1, max(ys))
    px = px or px_fuer(max(x1 - x0, y1 - y0))
    lw = E.Leinwand((x0 - 3, y0 - 3, x1 + 3, y1 + 3), px)
    mat = lw.figur(fig)
    if frei:
        mat = E._andnot(mat, lw.flaechen(frei))
    if solid:
        mat = mat.union(lw.flaechen(solid))
    return E.teil_aus_raster(name, lw, mat, cfg.min_web, cfg.kerf, notes, unten_flach)


def zapfen_unten(part: Part, x: float, tw: float, T: float, fid: str, pos: float = 0.0) -> JointFeature:
    out, feats = E.zapfen_einsetzen(part.outline, [x], tw, T)
    if not feats:
        raise ValueError(f"{part.name}: Für den Steckfuß ist die Standfläche zu schmal – größer wählen")
    part.outline = oriented(out, True)
    f = JointFeature(fid, "tab", tw, T, pos=pos, points=feats[0][2])
    part.features.append(f)
    return f


def zapfen_kante(a: Point, b: Point, s: float, tw: float, T: float, fid: str, pos: float) -> Tuple[Poly, JointFeature]:
    """Zapfen auf der Kante a→b (Außenkontur CCW, Material links): Mitte bei Abstand s von a, ragt T nach außen.
    Liefert die vier Eckpunkte (in Laufrichtung) und das Feature."""
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
    nx, ny = uy, -ux                                       # rechts der Laufrichtung = außen
    p0 = (a[0] + ux * (s - tw / 2), a[1] + uy * (s - tw / 2))
    p3 = (a[0] + ux * (s + tw / 2), a[1] + uy * (s + tw / 2))
    pts = [p0, (p0[0] + nx * T, p0[1] + ny * T), (p3[0] + nx * T, p3[1] + ny * T), p3]
    return pts, JointFeature(fid, "tab", tw, T, pos=pos, points=list(pts))


def kante_mit_zapfen(a: Point, b: Point, zapfen: Sequence[Tuple[float, float, str, float]], T: float
                     ) -> Tuple[Poly, List[JointFeature]]:
    """Punkte von a bis vor b mit Zapfen [(s, tw, fid, pos)] – für exakt konstruierte Konturen."""
    out = [a]
    feats = []
    for s, tw, fid, pos in sorted(zapfen):
        pts, f = zapfen_kante(a, b, s, tw, T, fid, pos)
        out += pts
        feats.append(f)
    return out, feats



def brett(name: str, W: float, H: float, T: float, unten=(), rechts=(), oben=(), links=()) -> Part:
    """Exaktes Rechteck (0, 0)–(W, H) mit Steckzapfen der Tiefe T an beliebigen Seiten.
    Jede Seite: Liste von (Mitte, Breite, Feature-ID, pos); Mitte ist x (unten/oben) bzw. y (links/rechts)."""
    out: Poly = []
    feats: List[JointFeature] = []
    for a, b, liste, s_von in (((0.0, 0.0), (W, 0.0), unten, lambda m: m),
                               ((W, 0.0), (W, H), rechts, lambda m: m),
                               ((W, H), (0.0, H), oben, lambda m: W - m),
                               ((0.0, H), (0.0, 0.0), links, lambda m: H - m)):
        pts, fs = kante_mit_zapfen(a, b, [(s_von(m), tw, fid, pos) for m, tw, fid, pos in liste], T)
        out += pts
        feats += fs
    return Part(name, oriented(out, True), features=feats)


def abbilden(part: Part, fn) -> Part:
    """Teil mit allen Löchern, Gravuren und Steck-Merkmalen abbilden (fn: Punkt → Punkt),
    z. B. spiegeln oder drehen. Spiegeln dreht die Umlaufrichtung – wird korrigiert."""
    from steckwerk import Stroke
    m = lambda pts: [fn(q) for q in pts]
    feats = [JointFeature(f.id, f.kind, f.length, f.depth, list(f.segments), f.pos, f.span, m(f.points))
             for f in part.features]
    return Part(part.name, oriented(m(part.outline), True), [oriented(m(h), False) for h in part.holes],
                [Stroke(m(st.points), st.closed) for st in part.engrave], feats, part.note)


def kopfueber(part: Part) -> Part:
    """An der Waagerechten y = 0 spiegeln (Oberkante wird Unterkante und umgekehrt)."""
    return abbilden(part, lambda q: (q[0], -q[1]))

def schlitz(part: Part, fid: str, cx: float, cy: float, laenge: float, T: float, pos: float,
            winkel: float = 0.0) -> Poly:
    """Rechteckschlitz laenge × T, Mitte (cx, cy), Längsrichtung um winkel gedreht."""
    c, s = math.cos(winkel), math.sin(winkel)
    pts = []
    for u, v in ((-laenge / 2, -T / 2), (laenge / 2, -T / 2), (laenge / 2, T / 2), (-laenge / 2, T / 2)):
        pts.append((cx + u * c - v * s, cy + u * s + v * c))
    hole = oriented(pts, False)
    part.holes.append(hole)
    part.features.append(JointFeature(fid, "slot", laenge, T, pos=pos, points=list(hole)))
    return hole


def schlitz_polster(cx: float, cy: float, laenge: float, T: float, rand: float, winkel: float = 0.0) -> Poly:
    """Fläche um einen Schlitz, die Material bleiben muss."""
    c, s = math.cos(winkel), math.sin(winkel)
    L, B = laenge / 2 + rand, T / 2 + rand
    return [(cx + u * c - v * s, cy + u * s + v * c) for u, v in ((-L, -B), (L, -B), (L, B), (-L, B))]


def gravur(part: Part, linien: Sequence[Tuple[Sequence[Point], bool]], rand: float = 0.7,
           loch_rand: Optional[float] = None, sperr: Sequence[Poly] = (), canvas=None):
    from models import _deko as dk
    cv = canvas or dk.Canvas(part, margin=rand, hole_margin=loch_rand if loch_rand is not None else rand)
    for b in sperr:
        cv.block(b, 0.4)
    for pts, closed in linien:
        if len(pts) >= 2:
            cv.draw(list(pts), closed)
    return cv


# --------------------------------------------------------------------------------------------------
# Schrift
# --------------------------------------------------------------------------------------------------

def textzeilen(text: str, cap: float, gap_mm: float = 0.0, style: str = "normal", case: str = "gross",
               zeilenabstand: float = 0.55) -> Tuple[List[Poly], float, float]:
    """Text (| = neue Zeile) in mm, Zeilen zentriert um x = 0, oberste Grundlinie y = 0.
    gap_mm: zusätzlicher Buchstabenabstand. Liefert (Striche, Breite, Höhe)."""
    from models import _font as fo
    s = cap / fo.CAP
    sx = {"schmal": 0.75, "breit": 1.3}.get(style, 1.0)
    slant = 0.2 if style == "kursiv" else 0.0
    lines = [fo.normalize(ln.strip(), case) for ln in text.replace("\n", "|").split("|") if ln.strip()]
    out: List[Poly] = []
    wmax = 0.0
    for i, ln in enumerate(lines):
        strokes = []
        x = 0.0
        for c in ln:
            x0, x1 = fo._BOUNDS[c]
            pad = max(0.0, fo.MIN_W - (x1 - x0)) / 2
            for st in fo.GLYPHS[c]:
                strokes.append([((x + (px - x0 + pad) * sx + slant * py) * s, py * s) for px, py in st])
            x += fo._advance(c, sx) + gap_mm / s
        w = (x - fo.GAP - gap_mm / s) * s
        wmax = max(wmax, w)
        y = -i * (1 + zeilenabstand) * cap
        out += [[(px - w / 2, py + y) for px, py in st] for st in strokes]
        if style == "fett":                                # zweite und dritte Linie leicht versetzt
            d = 0.05 * cap
            out += [[(px - w / 2 + d, py + y) for px, py in st] for st in strokes]
            out += [[(px - w / 2 + d / 2, py + y + d) for px, py in st] for st in strokes]
    n = len(lines)
    h = cap * (n + (n - 1) * zeilenabstand)
    return out, wmax, h


def text_in_box(text: str, cx: float, cy: float, max_w: float, max_h: float, max_cap: float, min_cap: float,
                gap_faktor: float = 0.0, style: str = "normal", case: str = "gross",
                zeilenabstand: float = 0.55, gap_min: float = 0.0) -> Tuple[List[Poly], float]:
    """Text so groß wie möglich (≤ max_cap) in die Box setzen. ValueError, wenn er kleiner als min_cap würde."""
    cap = max_cap
    for _ in range(40):
        gap = max(gap_min, gap_faktor * cap)
        st, w, h = textzeilen(text, cap, gap, style, case, zeilenabstand)
        if not st:
            return [], 0.0
        if w <= max_w + 1e-6 and h <= max_h + 1e-6:
            xs = [p[0] for s in st for p in s]
            ys = [p[1] for s in st for p in s]
            dx = cx - (min(xs) + max(xs)) / 2
            dy = cy - (min(ys) + max(ys)) / 2
            return [[(x + dx, y + dy) for x, y in s] for s in st], cap
        cap *= 0.94
        if cap < min_cap - 1e-9:
            break
    raise ValueError(f"Der Text „{text.replace('|', ' ')}“ ist zu lang für diese Größe – kürzer fassen "
                     f"oder größer wählen")


def schablone(lw, strokes: Sequence[Poly], sw: float, steg: float, cap: float = 0.0):
    """Buchstaben als Schnittfläche (Raster) mit Brücken: Innenformen (O, A, B, …) bleiben über
    Stege mit dem Rest verbunden. Kleine Innenformen hängen an einer Brücke nach unten, hohe (O, D, 0)
    an zwei Brücken oben und unten. Liefert das Raster der auszuschneidenden Fläche."""
    segs = [K.stroke([s[i], s[i + 1]], sw, sw, "rund") for s in strokes for i in range(len(s) - 1)
            if math.hypot(s[i + 1][0] - s[i][0], s[i + 1][1] - s[i][1]) > 1e-6]
    holes = lw.flaechen([g for g in segs if len(g) >= 3])
    for runde in range(4):
        areas = lw.konturen(holes)
        inseln = [h for f in areas for h in f["loecher"] if abs(signed_area(h)) > 0.05]
        if not inseln:
            break
        bruecken = []
        for h in inseln:
            xs = [p[0] for p in h]
            ys = [p[1] for p in h]
            cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
            hoch = max(ys) - min(ys)
            if runde >= 2:
                bruecken.append(rect(min(xs) - 1.6 * sw, cy - steg / 2, max(xs) - min(xs) + 3.2 * sw, steg))
            elif cap and hoch < 0.5 * cap and runde == 0:
                bruecken.append(rect(cx - steg / 2, min(ys) - 1.6 * sw, steg, hoch / 2 + 1.6 * sw))
            else:
                bruecken.append(rect(cx - steg / 2, min(ys) - 1.6 * sw, steg, hoch + 3.2 * sw))
        holes = E._andnot(holes, lw.flaechen(bruecken))
    return holes


def abrunden(poly: Sequence[Point], r: float, n: int = 6) -> Poly:
    """Ecken eines Polygons mit Radius r verrunden (r wird an kurzen Kanten verkleinert)."""
    P = list(poly)
    m = len(P)
    out: Poly = []
    for i in range(m):
        a, b, c = P[i - 1], P[i], P[(i + 1) % m]
        l1 = math.hypot(b[0] - a[0], b[1] - a[1])
        l2 = math.hypot(c[0] - b[0], c[1] - b[1])
        if l1 < 1e-9 or l2 < 1e-9:
            continue
        u1 = ((a[0] - b[0]) / l1, (a[1] - b[1]) / l1)
        u2 = ((c[0] - b[0]) / l2, (c[1] - b[1]) / l2)
        cosang = max(-1.0, min(1.0, u1[0] * u2[0] + u1[1] * u2[1]))
        ang = math.acos(cosang)
        if ang > math.pi - 1e-3:
            out.append(b)
            continue
        t = r / math.tan(ang / 2)
        t = min(t, 0.45 * l1, 0.45 * l2)
        rr = t * math.tan(ang / 2)
        p1 = (b[0] + u1[0] * t, b[1] + u1[1] * t)
        p2 = (b[0] + u2[0] * t, b[1] + u2[1] * t)
        bis = (u1[0] + u2[0], u1[1] + u2[1])
        bl = math.hypot(*bis) or 1.0
        dc = rr / math.sin(ang / 2)
        cc = (b[0] + bis[0] / bl * dc, b[1] + bis[1] / bl * dc)
        a1 = math.atan2(p1[1] - cc[1], p1[0] - cc[0])
        a2 = math.atan2(p2[1] - cc[1], p2[0] - cc[0])
        d = a2 - a1
        while d > math.pi:
            d -= 2 * math.pi
        while d < -math.pi:
            d += 2 * math.pi
        for k in range(n + 1):
            aa = a1 + d * k / n
            out.append((cc[0] + rr * math.cos(aa), cc[1] + rr * math.sin(aa)))
    return out


def entlang(poly: Sequence[Point], step: float, closed: bool = True) -> List[Tuple[Point, Point]]:
    """Punkte im Abstand ≈ step entlang eines Polygons mit Tangente: [(punkt, tangente)]."""
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
