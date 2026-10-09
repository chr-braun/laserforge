"""
ornament.py – Christbaumschmuck-Konfigurator.

Frei kombinierbar:
  form     kugel · stern · herz · glocke · baum · mond · anhaenger · lebkuchen · stiefel · zuckerstange ·
           geschenk · kerze · engel · zapfen · schneemann · schneeflocke
           (Lebkuchenmann/Schneemann mit Gesicht, Geschenk mit Schleife, Zapfen mit Schuppen …)
  muster   keins · punkte · streifen · sterne · flocken · herzen · tannen · karo · wellen (Gravur) ·
           filigran (Durchbrüche)
  rand     gravierte Randlinie (an/aus), rand_stil: linie · doppelt · gestrichelt · punkte · wellen ·
           zickzack · zuckerguss · eiszapfen · lichterkette · girlande · sterne · herzen
  text     Name/Jahr als Einstrich-Gravur; mehrere Namen mit Komma → je ein Anhänger;
           '|' trennt Zeilen ("Anna|2026"); textrahmen: ohne · rahmen · rund · oval · banner · holz ·
           geschweift; schrift: normal · fett · kursiv · schmal · breit · schatten; schreibweise: gross · normal
  haenger  oese (Ring oben) oder loch
  3d       zwei Hälften mit Kreuzschlitz zum Zusammenstecken (ohne Text)
"""
from __future__ import annotations

import math
from typing import Dict, List, Optional, Sequence

from laserforge import (Assembly, Config, JointFeature, Part, Point, arc_points, bbox, bezier_q,
                        circle, clean, inset_polygon, mirror_x, oriented, polygon_ok, rect)
from models import _deko as dk
from models._font import CASES, STYLES, fit_text, unsupported
from models._shapes import (border, cut_axis_slot, fill_pattern, keepout_circle, keepout_rect, star,
                            union_circle)

SHAPES = ["kugel", "stern", "herz", "glocke", "baum", "mond", "anhaenger", "lebkuchen", "stiefel", "zuckerstange",
          "geschenk", "kerze", "engel", "zapfen", "schneemann", "schneeflocke"]
PATTERNS = ["keins", "punkte", "streifen", "sterne", "flocken", "herzen", "tannen", "karo", "wellen", "filigran"]
HANGERS = ["oese", "loch"]
DEFAULTS = dict(size=70.0, shape="stern", pattern="sterne")


class Shape:
    """Grundform: Kontur (CCW), Textbox, Lochposition, Ösen-Ansatz."""

    def __init__(self, outline: List[Point], text_box=None, hole_at: Optional[Point] = None,
                 top: Optional[Point] = None, eye_ok: bool = True, three_d_ok: bool = True,
                 deco=None, deco_keep=None):
        self.outline = oriented(clean(outline), True)
        self.three_d_ok = three_d_ok
        self.deco = deco or []            # [(Linienzug, auch_mit_text)] – feste Gravur der Form (z. B. Gesicht)
        self.deco_keep = deco_keep or []  # Sperrflächen der Deko für das Muster
        self.text_box = text_box          # (cx, cy, w, h) oder None
        self.hole_at = hole_at            # Lochmitte bei haenger='loch'
        self.top = top                    # höchster Punkt (Öse sitzt darauf)
        self.eye_ok = eye_ok


def _kugel(S: float, tol: float) -> Shape:
    ch = 0.1 * S
    r = (S - ch) / 2
    cw = 0.5 * r
    a = math.acos((cw / 2) / r)
    yc = r + r * math.sin(a)
    pts = arc_points(0, r, r, math.pi - a, 2 * math.pi + a, tol)
    pts += [(cw / 2, 2 * r + ch), (-cw / 2, 2 * r + ch)]
    return Shape(pts, (0, 0.92 * r, 1.45 * r, 0.62 * r), (0, 2 * r - 0.2 * r), (0, 2 * r + ch))


def _stern(S: float, tol: float) -> Shape:
    R = S / (1 + math.cos(math.pi / 5))
    cy = S - R
    pts = star(0, cy, R, 0.47 * R)
    return Shape(pts, (0, cy - 0.04 * R, 0.62 * R, 0.34 * R), (0, cy + 0.55 * R), (0, S))


def _herz(S: float, tol: float) -> Shape:
    """Klassisches Herz: auf die Spitze gestelltes Quadrat + zwei Halbkreise (keine scharfe Kerbe)."""
    a = S / (3 / (2 * math.sqrt(2)) + 0.5)            # Gesamthöhe = 1.5·a/√2 + a/2
    q = a / math.sqrt(2)
    r = a / 2
    right_c = (q / 2, 1.5 * q)
    left_c = (-q / 2, 1.5 * q)
    ang = math.atan2(q - 1.5 * q, q - q / 2)              # Richtung Mittelpunkt → rechte Ecke
    pts = [(0.0, 0.0), (q, q)]
    pts += arc_points(right_c[0], right_c[1], r, ang, ang + math.pi, tol)[1:]
    ang2 = math.atan2(2 * q - 1.5 * q, 0 + q / 2)         # Mittelpunkt links → Spitze oben
    pts += arc_points(left_c[0], left_c[1], r, ang2, ang2 + math.pi, tol)[1:]
    rh = max(1.75, 0.025 * S)                             # wie in build_one
    hole_y = 2 * q - max(0.085 * S, math.sqrt(2) * (rh + 1.8))  # Steg zur Herz-Kerbe (45°-Flanken)
    return Shape(pts, (0, 0.53 * S, 0.6 * S, 0.27 * S), (0, hole_y), None, eye_ok=False)


def _glocke(S: float, tol: float) -> Shape:
    right = bezier_q((0.0, 0.88), (0.20, 0.88), (0.21, 0.72), 14)
    right += bezier_q((0.21, 0.72), (0.22, 0.35), (0.42, 0.17), 20)[1:]
    right += [(0.44, 0.12)]
    a = math.atan2(0.04, math.sqrt(0.08 ** 2 - 0.04 ** 2))
    right += arc_points(0, 0.08, 0.08, a, -math.pi / 2, tol / S)
    half = [(x * S, y * S) for x, y in right]
    left = mirror_x(half[:-1])
    pts = half + left
    ymin = min(p[1] for p in pts)
    pts = [(x, y - ymin) for x, y in pts]
    return Shape(pts, (0, (0.42 - ymin / S) * S, 0.34 * S, 0.17 * S), (0, (0.76 - ymin / S) * S),
                 (0, (0.88 - ymin / S) * S))


def _baum(S: float, tol: float) -> Shape:
    from models.tannenbaum import _right_profile
    Wt = 0.78 * S
    th = 0.1 * S
    tw = 0.16 * Wt
    right = _right_profile(S, Wt, th, 3)
    pts = [(-tw / 2, 0), (tw / 2, 0), (tw / 2, th)] + right + [(0, S)] + mirror_x(right) + [(-tw / 2, th)]
    h_t = (S - th) / 3.5
    xl, yl = right[-1]
    need = 1.35 * (max(1.75, 0.025 * S) + 2.2)                 # halbe Breite für Loch + Steg
    y_hole = S - need * (S - yl) / xl
    return Shape(pts, (0, th + 0.42 * h_t, 0.62 * Wt, 0.5 * h_t), (0, y_hole), (0, S))


def _mond(S: float, tol: float) -> Shape:
    R = S / 2
    d, r2 = 0.42 * R, 0.86 * R
    xi = (R * R - r2 * r2 + d * d) / (2 * d)
    yi = math.sqrt(R * R - xi * xi)
    a1 = math.atan2(yi, xi)
    a2 = math.atan2(yi, xi - d)
    pts = arc_points(0, 0, R, a1, 2 * math.pi - a1, tol)
    pts += arc_points(d, 0, r2, 2 * math.pi - a2, a2, tol)[1:-1]
    pts = [(x, y + R) for x, y in pts]
    # Loch im dicken Teil nahe der oberen Spitze
    ang = math.radians(118)
    ux, uy = math.cos(ang), math.sin(ang)
    px, py = R * ux, R * uy
    # Bandbreite entlang -u bis zum inneren Kreis
    bx, by = px - d, py
    B = -2 * (bx * ux + by * uy)
    C = bx * bx + by * by - r2 * r2
    t = (-B - math.sqrt(max(B * B - 4 * C, 0))) / 2 if C > 0 else 0.0
    hole = (px - ux * t / 2, py - uy * t / 2 + R)
    return Shape(pts, None, hole, None, eye_ok=False)


def _anhaenger(S: float, tol: float) -> Shape:
    """Geschenk-/Namensanhänger: Rechteck mit abgeschrägten oberen Ecken, abgerundet unten."""
    W = 0.62 * S
    r = 0.1 * W
    c = 0.22 * W
    pts = arc_points(-W / 2 + r, r, r, math.pi, 1.5 * math.pi, tol)
    pts += arc_points(W / 2 - r, r, r, 1.5 * math.pi, 2 * math.pi, tol)
    pts += [(W / 2, S - c), (W / 2 - c, S), (-W / 2 + c, S), (-W / 2, S - c)]
    return Shape(pts, (0, 0.44 * S, 0.8 * W, 0.56 * S), (0, S - 0.13 * S), None, eye_ok=False)


# --- Neue Formen (Einheiten relativ zur Höhe S, rechte Hälfte gespiegelt) --------------------------

def _round(pts, S, tol):
    from models.fahrzeug import fillet
    out: List[Point] = []
    for q in fillet([(x * S, y * S, r * S) for x, y, r in pts], tol):
        if not out or math.hypot(q[0] - out[-1][0], q[1] - out[-1][1]) > 0.08:
            out.append(q)
    while len(out) > 3 and math.hypot(out[0][0] - out[-1][0], out[0][1] - out[-1][1]) <= 0.08:
        out.pop()
    return out


def _sym(right, S, tol):
    """Rechte Hälfte (x ≥ 0, unten → oben, Endpunkte auf der Achse) spiegeln und Ecken runden."""
    left = [(-x, y, r) for x, y, r in reversed(right[1:-1])]
    return _round(right + left, S, tol)


def _top_hole(S):
    """Loch knapp unter der Spitze (y = S) mit ausreichendem Steg."""
    return S - max(1.75, 0.025 * S) - max(2.0, .03 * S)


def _circ(cx, cy, r, S, tol):
    return circle(cx * S, cy * S, r * S, tol)


def _arc_u(cx, cy, r, a0, a1):
    """Bogen in Einheitskoordinaten als (x, y, 0)-Punkte (ohne Rundung)."""
    return [(x, y, 0) for x, y in arc_points(cx, cy, r, a0, a1, 0.002)]


def _lebkuchen(S: float, tol: float) -> Shape:
    hy, hr, nx = .84, .16, .09
    a0 = math.atan2(-math.sqrt(hr * hr - nx * nx), nx)
    right = [(0, .30, .05), (.05, 0, .03), (.25, 0, .07), (.20, .36, .05), (.17, .47, .04), (.40, .53, .07),
             (.42, .66, .07), (.16, .66, .05)] + _arc_u(0, hy, hr, a0, math.pi / 2)
    outline = _sym(right, S, tol)
    eyes = [_circ(-.06, .865, .017, S, tol), _circ(.06, .865, .017, S, tol)]
    smile = arc_points(0, .845 * S, .07 * S, math.radians(215), math.radians(325), tol)
    buttons = [_circ(0, y, .02, S, tol) for y in (.60, .52)]
    deco = [(c + [c[0]], True) for c in eyes + buttons] + [(smile, True)]
    keep = [keepout_circle(0, .82 * S, .12 * S), keepout_rect(0, .56 * S, .08 * S, .16 * S)]
    hole = _top_hole(S)
    return Shape(outline, (0, .41 * S, .30 * S, .12 * S), (0, hole), (0, S), deco=deco, deco_keep=keep)


def _stiefel(S: float, tol: float) -> Shape:
    pts = _round([(-.26, 0, .06), (.30, 0, .08), (.40, .08, .10), (.36, .22, .10), (.10, .34, .05), (.08, .78, 0),
                  (.13, .78, .02), (.13, 1, .04), (-.33, 1, .04), (-.33, .78, .02), (-.28, .78, 0),
                  (-.28, .10, .06)], S, tol)
    cuff = [(-.27 * S, .78 * S), (.07 * S, .78 * S)]
    return Shape(pts, (-.10 * S, .50 * S, .28 * S, .30 * S), (-.10 * S, .89 * S), (-.10 * S, S), three_d_ok=False,
                 deco=[(cuff, True)], deco_keep=[keepout_rect(-.10 * S, .78 * S, .40 * S, .03 * S)])


def _zuckerstange(S: float, tol: float) -> Shape:
    k = S / .97
    pts = arc_points(0, .10 * k, .10 * k, math.pi, 2 * math.pi, tol)
    pts += arc_points(.17 * k, .70 * k, .07 * k, math.pi, 0, tol)
    pts += arc_points(.34 * k, .60 * k, .10 * k, math.pi, 2 * math.pi, tol)
    pts += arc_points(.17 * k, .70 * k, .27 * k, 0, math.pi, tol)
    # gravierte Ringel auf dem Stiel
    deco = [([(-.10 * k, y * k), (.10 * k, (y + .08) * k)], True) for y in (.14, .26, .38, .50, .62)]
    keep = [keepout_rect(0, .42 * k, .20 * k, .62 * k)]
    return Shape(pts, None, (.17 * k, .87 * k), (.17 * k, .97 * k), three_d_ok=False, deco=deco, deco_keep=keep)


def _geschenk(S: float, tol: float) -> Shape:
    right = [(0, 0, 0), (.36, 0, .03), (.36, .62, 0), (.40, .62, .02), (.40, .76, .02), (.10, .76, 0),
             (.33, .88, .06), (.27, .99, .05), (.05, .86, .02), (0, .87, 0)]
    pts = _sym(right, S, tol)
    ribbon = [([(x * S, .015 * S), (x * S, .755 * S)], False) for x in (-.05, .05)]
    ribbon += [([(-.395 * S, .69 * S), (-.06 * S, .69 * S)], False), ([(.06 * S, .69 * S), (.395 * S, .69 * S)], False)]
    keep = [keepout_rect(0, .38 * S, .14 * S, .76 * S)]
    hole = .62 * S - max(1.75, 0.025 * S) - max(2.0, .03 * S)
    return Shape(pts, (0, .30 * S, .58 * S, .30 * S), (0, hole), None, eye_ok=False, three_d_ok=False, deco=ribbon,
                 deco_keep=keep)


def _kerze(S: float, tol: float) -> Shape:
    fr, fy, nx = .11, .80, .06
    a0 = math.atan2(-math.sqrt(fr * fr - nx * nx), nx)
    right = [(0, 0, 0), (.28, 0, .02), (.28, .06, .01), (.19, .06, .01), (.19, .62, .02), (nx, .62, .01)]
    right += _arc_u(0, fy, fr, a0, math.radians(30)) + [(0, 1, 0)]
    pts = _sym(right, S, tol)
    drip = [(-.19 * S, .55 * S), (-.12 * S, .55 * S), (-.10 * S, .47 * S), (-.08 * S, .55 * S), (.19 * S, .55 * S)]
    return Shape(pts, (0, .30 * S, .30 * S, .36 * S), (0, .80 * S), (0, S), three_d_ok=False,
                 deco=[(drip, True)],
                 deco_keep=[keepout_rect(0, .53 * S, .38 * S, .10 * S), keepout_circle(0, .80 * S, .10 * S)])


def _engel(S: float, tol: float) -> Shape:
    k = 1 / .96
    hy, hr, nx = .83, .13, .07
    a0 = math.atan2(-math.sqrt(hr * hr - nx * nx), nx)
    right = [(0, 0, 0), (.30, 0, .03), (.12, .48, 0), (.40, .40, .05), (.46, .63, .10), (.32, .76, .08),
             (.13, .63, .03)] + _arc_u(0, hy, hr, a0, math.pi / 2)
    outline = _sym([(x * k, y * k, r * k) for x, y, r in right], S, tol)
    feathers = []
    for side in (-1, 1):
        for t in (.50, .58, .66):
            feathers.append(([(side * .20 * k * S, t * k * S), (side * .36 * k * S, (t + .05) * k * S)], True))
    keep = [keepout_rect(s * .30 * k * S, .58 * k * S, .22 * k * S, .30 * k * S) for s in (-1, 1)]
    return Shape(outline, (0, .20 * k * S, .30 * S, .20 * S), (0, _top_hole(S)), (0, S), deco=feathers,
                 deco_keep=keep)


def _zapfen(S: float, tol: float) -> Shape:
    right = [(0, 0, 0)]
    n = 6
    for i in range(n):
        y0 = .06 + .78 * i / n
        y1 = .06 + .78 * (i + .5) / n
        w = .30 * math.sin(math.pi * (y1 + .05) / .95) ** 0.75
        wi = .30 * math.sin(math.pi * (y0 + .05) / .95) ** 0.75
        right += [(max(.04, wi - .03), y0, .01), (w + .03, y1, .045)]
    right += [(.10, .86, .02), (.045, .88, .01), (.045, 1, .01), (0, 1, 0)]
    pts = _sym(right, S, tol)
    scales = []
    for i in range(1, 6):
        y = .06 + .78 * i / n
        w = .30 * math.sin(math.pi * (y + .05) / .95) ** 0.75 - .07
        scales.append(([(-w * S, y * S), (0, (y - .05) * S), (w * S, y * S)], False))
    return Shape(pts, (0, .44 * S, .34 * S, .18 * S), (0, .78 * S), (0, S), deco=scales)


def _schneemann(S: float, tol: float) -> Shape:
    k = 1 / .99
    C = [(.27 * k, .27 * k), (.62 * k, .19 * k), (.86 * k, .13 * k)]   # (Mitte y, Radius)

    def cross(a, b):
        (ya, ra), (yb, rb) = a, b
        d = yb - ya
        y = (d * d + ra * ra - rb * rb) / (2 * d)
        return y + ya, math.sqrt(max(ra * ra - y * y, 0))

    (y1, x1), (y2, x2) = cross(C[0], C[1]), cross(C[1], C[2])
    pts = arc_points(0, C[0][0] * S, C[0][1] * S, -math.pi / 2, math.atan2(y1 - C[0][0], x1), tol)
    pts += arc_points(0, C[1][0] * S, C[1][1] * S, math.atan2(y1 - C[1][0], x1), math.atan2(y2 - C[1][0], x2), tol)[1:]
    pts += arc_points(0, C[2][0] * S, C[2][1] * S, math.atan2(y2 - C[2][0], x2), math.pi / 2, tol)[1:]
    outline = pts + [(-x, y) for x, y in reversed(pts[1:-1])]
    hy = C[2][0]
    face = [_circ(-.045, hy + .03, .015, S, tol), _circ(.045, hy + .03, .015, S, tol)]
    nose = [(0, (hy - .005) * S), (.09 * S, (hy - .025) * S), (0, (hy - .035) * S)]
    btn = [_circ(0, y, .02, S, tol) for y in (C[1][0] + .06, C[1][0] - .04)]
    deco = [(c + [c[0]], True) for c in face + btn] + [(nose, True)]
    keep = [keepout_circle(0, hy * S, C[2][1] * S), keepout_rect(0, C[1][0] * S + .01 * S, .08 * S, .17 * S)]
    return Shape(outline, (0, .25 * k * S, .38 * S, .20 * S), (0, _top_hole(S)), (0, S), deco=deco,
                 deco_keep=keep)


SHAPE_FN = {"kugel": _kugel, "stern": _stern, "herz": _herz, "glocke": _glocke, "baum": _baum,
            "mond": _mond, "anhaenger": _anhaenger, "lebkuchen": _lebkuchen, "stiefel": _stiefel,
            "zuckerstange": _zuckerstange, "geschenk": _geschenk, "kerze": _kerze, "engel": _engel,
            "zapfen": _zapfen, "schneemann": _schneemann}


def build_one(cfg: Config, name: str, shape: str, S: float, pattern: str, text: str, hanger: str,
              rand: bool, seed: int, three_d: bool = False, rand_stil: str = "linie",
              textrahmen: str = "ohne", schrift: str = "normal", schreibweise: str = "gross") -> List[Part]:
    """Ein Anhänger (bzw. zwei Steckhälften bei 3D)."""
    T = cfg.T
    tol = cfg.arc_tolerance
    if shape not in SHAPE_FN:
        raise ValueError(f"Form {shape!r} unbekannt – erlaubt: {', '.join(SHAPES)}")
    if pattern not in PATTERNS:
        raise ValueError(f"Muster {pattern!r} unbekannt – erlaubt: {', '.join(PATTERNS)}")
    if hanger not in HANGERS:
        raise ValueError(f"Aufhänger {hanger!r} unbekannt – erlaubt: oese, loch")
    dk.check_choice("Randstil", rand_stil, dk.LINE_STYLES)
    dk.check_choice("Textrahmen", textrahmen, dk.SIGNS)
    if schrift not in STYLES:
        raise ValueError(f"Schrift {schrift!r} unbekannt – erlaubt: {', '.join(STYLES)}")
    if schreibweise not in CASES:
        raise ValueError(f"Schreibweise {schreibweise!r} unbekannt – erlaubt: {', '.join(CASES)}")
    bad = unsupported(text or "")
    if bad:
        raise ValueError(f"Zeichen {''.join(bad)!r} gibt es in der Gravurschrift nicht")
    if three_d and text:
        raise ValueError("Text ist bei 3D-Steckanhängern nicht möglich (der Schlitz läuft durch die Mitte)")
    sh = SHAPE_FN[shape](S, tol)
    if text and sh.text_box is None:
        raise ValueError(f"Form {shape!r} hat keinen Platz für Text")
    if three_d and (shape == "mond" or not sh.three_d_ok):
        raise ValueError(f"Die Form {shape!r} eignet sich nicht für die 3D-Steckversion")
    base = sh.outline
    outline = base
    avoid: List[List[Point]] = []
    rh = max(1.75, 0.025 * S)                      # Ø 3.5 mm reicht für Band und Haken
    use_eye = hanger == "oese" and sh.eye_ok and sh.top is not None
    if use_eye:
        re = rh + max(2.2, 0.6 * T)
        hx, hy = sh.top[0], sh.top[1] + re - 0.35 * re
        outline = _drop_short(union_circle(base, hx, hy, re, tol), 0.3)
        avoid.append(keepout_circle(hx, hy, re + 1.5))
        avoid.append(keepout_rect(hx, sh.top[1] - 2, 2 * re, 6))   # Ansatz der Öse freihalten
    else:
        hx, hy = sh.hole_at
        avoid.append(keepout_circle(hx, hy, rh + 2.2))
    parts: List[Part] = []
    pieces = [("", None)] if not three_d else [("_a", True), ("_b", False)]
    ys0 = [p[1] for p in base]
    y_mid = (min(ys0) + max(ys0)) / 2
    for suffix, from_top in pieces:
        out = outline
        pre = base                      # Rand/Muster an der Grundform ohne Öse ausrichten
        feats = []
        slot_avoid = []
        with_hole = True
        if three_d:
            # Teil A (Schlitz von oben) bekommt keine Öse; die Öse sitzt an Teil B
            src = base if from_top else outline
            out, slot = cut_axis_slot(src, T, y_mid, from_top)
            if not polygon_ok(out):
                raise ValueError(f"Form {shape!r} ist bei {T:g} mm Material zu klein für die 3D-Steckversion")
            span = (y_mid, max(ys0)) if from_top else (min(ys0), y_mid)
            feats.append(JointFeature("kreuz", "halving", span[1] - span[0], T, span=span, points=slot))
            slot_avoid = [keepout_rect(0, (span[0] + span[1]) / 2, T + 3.0, span[1] - span[0] + 6)]
            with_hole = not from_top
        part = Part(f"{name}{suffix}", out, features=feats)
        if with_hole:
            part.add_hole(circle(hx, hy, rh, tol))
        av = avoid + slot_avoid
        if text:
            cx, cy, w, h = sh.text_box
            if textrahmen == "ohne":
                strokes, hcap = fit_text(text, cx, cy, w, h, min_h=2.5, max_cap=0.16 * S, style=schrift,
                                         case=schreibweise)
                for s in strokes:
                    part.add_engrave(s)
                xs = [p[0] for s in strokes for p in s]
                ys_ = [p[1] for s in strokes for p in s]
                box = (min(xs), min(ys_), max(xs), max(ys_))
            else:
                cv = dk.Canvas(part, margin=1.0, seed=seed)
                for a in av:
                    cv.block(a)
                cands = dk.free_rects(cv, cx, cy, [g * h for g in (2.2, 1.8, 1.45, 1.15, 0.9)],
                                      [0.0, 0.15 * h, -0.15 * h, 0.3 * h, -0.3 * h])
                cands += [(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)]
                box = dk.sign(cv, text, textrahmen, cands, schrift, schreibweise, min_h=2.5,
                              max_cap=0.14 * S, anchor="mitte", tol=tol)
                if box is None:
                    raise ValueError(f"Text {text!r} passt mit Rahmen „{textrahmen}“ nicht auf die Form {shape!r}"
                                     f" – kürzer fassen, ohne Rahmen oder größer machen")
            av.append(rect(box[0] - 2.0, box[1] - 2.0, box[2] - box[0] + 4.0, box[3] - box[1] + 4.0))
        if sh.deco and not three_d:
            cv = dk.Canvas(part, margin=1.0, seed=seed)
            for a in av:
                cv.block(a)
            for line, with_text in sh.deco:
                if with_text or not text:
                    closed = len(line) > 3 and line[0] == line[-1]
                    cv.draw(line[:-1] if closed else line, closed=closed)
            av = av + sh.deco_keep + [b for line, wt in sh.deco if wt or not text for b in _band(line, 1.2)]
        margin = max(2.0, 0.045 * S)
        band = 0.0
        if rand:
            d = max(1.5, 0.025 * S)
            if rand_stil == "linie":
                border(part, pre, d, av)
            else:
                ins = inset_polygon(pre, d)
                if polygon_ok(ins):
                    band = max(2.0, min(4.0, 0.055 * S))
                    cv = dk.Canvas(part, margin=0.6, seed=seed)
                    for a in av:
                        cv.block(a, 0.2)
                    dk.styled_line(cv, ins + [ins[0]], rand_stil, band, side=+1, seed=seed)
        region = _inset_safe(pre, margin + (1.2 if rand else 0.0) + band)
        if region:
            fill_pattern(part, region, pattern, av, seed=seed, scale=max(0.7, min(1.4, S / 70)),
                         cut_web=max(cfg.min_web * 1.6, 1.6))
        parts.append(part)
    return parts


def _drop_short(pts, d):
    """Mini-Kanten (z. B. Ösen-Schnittpunkt dicht an einem Bogenpunkt) entfernen – stören den Kerf-Versatz."""
    out: List[Point] = []
    for q in pts:
        if not out or math.hypot(q[0] - out[-1][0], q[1] - out[-1][1]) > d:
            out.append(q)
    while len(out) > 3 and math.hypot(out[0][0] - out[-1][0], out[0][1] - out[-1][1]) <= d:
        out.pop()
    return out


def _band(line, w):
    """Sperrstreifen der Breite 2·w um einen Linienzug (je Segment ein Rechteck)."""
    out = []
    for (x0, y0), (x1, y1) in zip(line, line[1:]):
        L = math.hypot(x1 - x0, y1 - y0)
        if L < 1e-6:
            continue
        ux, uy = (x1 - x0) / L * w, (y1 - y0) / L * w
        out.append([(x0 - ux + uy, y0 - uy - ux), (x1 + ux + uy, y1 + uy - ux),
                    (x1 + ux - uy, y1 + uy + ux), (x0 - ux - uy, y0 - uy + ux)])
    return out


def _inset_safe(pts, d):
    from laserforge import inset_polygon, polygon_ok
    ins = inset_polygon(pts, d)
    return ins if polygon_ok(ins) else None


def build(cfg: Config, name: str = "ornament", shape: str = DEFAULTS["shape"], size: Optional[float] = None,
          height: Optional[float] = None, pattern: str = DEFAULTS["pattern"], text: str = "",
          hanger: str = "oese", rand: bool = True, three_d: bool = False, count: int = 1,
          seed: Optional[int] = None, rand_stil: str = "linie", textrahmen: str = "ohne",
          schrift: str = "normal", schreibweise: str = "gross") -> Assembly:
    """Ein oder mehrere Anhänger. Mehrere Namen: text='Anna,Ben,Clara' (je ein Anhänger)."""
    S = cfg.s(size or height or DEFAULTS["size"])
    seed = cfg.seed if seed is None else seed
    asm = Assembly(f"{name}_{shape}", params=dict(shape=shape, size=S, pattern=pattern, text=text,
                                                 hanger=hanger, rand=rand, three_d=three_d))
    for k, v, d in (("rand_stil", rand_stil, "linie"), ("textrahmen", textrahmen, "ohne"),
                    ("schrift", schrift, "normal"), ("schreibweise", schreibweise, "gross")):
        if v != d:
            asm.params[k] = v
    if shape == "schneeflocke":
        if text:
            raise ValueError("Schneeflocken haben keinen Platz für Text – nimm z. B. form=anhaenger")
        from models import schneeflocke
        sub = schneeflocke.build(cfg, name=f"{name}_flocke", size=S, count=max(count, 1), seed=seed,
                                 three_d=three_d)
        sub.name = asm.name
        sub.params.update(asm.params)
        return sub
    names = [t.strip() for t in text.split(",")] if text else [""] * max(count, 1)
    for i, t in enumerate(names):
        label = _slug(t) if t else f"{i + 1:02d}"
        parts = build_one(cfg, f"{shape}_{label}", shape, S, pattern, t, hanger, rand, seed + i, three_d,
                          rand_stil, textrahmen, schrift, schreibweise)
        asm.parts += parts
        if three_d:
            asm.connect(f"{parts[0].name}:kreuz", f"{parts[1].name}:kreuz")
    if three_d:
        asm.notes.append("Teil B (Schlitz unten, mit Öse) von oben auf Teil A (Schlitz oben) schieben.")
    asm.notes.append("Aufhängen: Band oder Draht durch Öse/Loch (Ø ≥ 3.5 mm).")
    return asm


def _slug(t: str) -> str:
    rep = {"Ä": "ae", "Ö": "oe", "Ü": "ue", "ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"}
    s = "".join(rep.get(c, c) for c in t.replace("|", "_"))
    s = "".join(c.lower() if c.isalnum() else "_" for c in s)
    return s.strip("_")[:24] or "text"
