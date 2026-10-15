"""
Halloween-Anhänger – filigrane Hänger für Zweige, Fenster und Geschenke.

Fledermaus, Gespenst, Totenkopf, Katze, Hexenhut, Kürbis und Spinnennetz – jeweils mit
Durchbrüchen und feinen Gravuren (Flügelknochen, Stofffalten, Schädelnähte, Sterne …) und einer
Aufhängeöse. Mit „alle“ entsteht das ganze Set auf einmal. Ein Name kann eingraviert werden.
"""
import importlib.util
import math
import os
import random
import sys

from steckwerk import Assembly, Part, arc_points, bezier_q, circle, min_distance, oriented, point_in_polygon, rect
from models import _deko as dk
from models._font import STYLES, fit_text, unsupported
from models._shapes import union_circle
from pakete import bibliothek, num, sel, txt


def _lib():
    return bibliothek("verzierungen").G


g = _lib()

MOTIFS = [("fledermaus", "Fledermaus"), ("geist", "Gespenst"), ("totenkopf", "Totenkopf"), ("katze", "Katze"),
          ("hexenhut", "Hexenhut"), ("kuerbis", "Kürbis"), ("spinnennetz", "Spinnennetz")]

UEBERSETZUNG = {"en": g.EN}

INFO = dict(
    label="Halloween-Anhänger",
    group="Halloween",
    desc="Fledermaus, Gespenst, Totenkopf, Katze, Hexenhut, Kürbis, Spinnennetz – filigran, mit Öse.",
    params=[
        sel("motiv", "Motiv", MOTIFS + [("alle", "alle sieben (Set)")], "alle"),
        num("size", "Größe", 80, 45, 160, help="größte Abmessung in mm"),
        txt("text", "Name (Gespenst, Kürbis, Hut)", "", "leer = ohne", section="Schrift und Beschriftung"),
        sel("schrift", "Schrift", [(s, s) for s in STYLES], "normal", section="Schrift und Beschriftung"),
    ],
)


def _scale_to(poly, S):
    x0, y0, x1, y1 = g.poly_bbox(poly)
    k = S / max(x1 - x0, y1 - y0)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    return [((x - cx) * k, (y - cy) * k) for x, y in poly], k, cx, cy


def _eyelet(outline, x, y_top, r, web):
    """Öse oben anfügen: Ring mit Loch. Liefert (Kontur, Lochkreis)."""
    for dy in (0.35, 0.5, 0.65):
        for dx in (0.0, 0.5, -0.5, 1.0, -1.0):
            cx, cy = x + dx * r, y_top + dy * r
            try:
                out = union_circle(outline, cx, cy, r)
            except ValueError:
                continue
            hole = circle(cx, cy, r - max(web * 1.3, 0.38 * r), 0.05)
            if g.polygon_ok(oriented(out, True)) and min_distance(hole, out, limit=web) >= web:
                return out, hole
    raise ValueError("Öse passt nicht – Anhänger größer wählen")


def build_one(cfg, name, motiv, S, text, schrift, rng, web):
    holes = []
    eng = []                                   # (punkte, geschlossen)
    put = []                                   # geschlossene Ornamente (nur ganz)
    text_box = None
    if motiv == "fledermaus":
        base = g.bat_unit(0.35)
        poly, k, cx, cy = _scale_to(base, S)
        T_ = lambda p: ((p[0] - cx) * k, (p[1] - cy) * k)
        for s_ in (1, -1):
            sh = (s_ * 0.10, 0.075)
            for tip in ((0.50, 0.185), (0.40, 0.005), (0.28, -0.05), (0.15, -0.085)):
                tp = (s_ * tip[0] * 0.93, tip[1] * 0.85 + 0.01)
                eng.append(([T_(sh), T_(((sh[0] + tp[0]) / 2, (sh[1] + tp[1]) / 2 + 0.02)), T_(tp)], False))
            holes.append(circle(*T_((s_ * 0.022, 0.05)), max(0.010 * S, 0.9), 0.05))
        top = max(p[1] for p in poly if abs(p[0]) < 0.02 * S) if any(abs(p[0]) < 0.02 * S for p in poly) else 0
        eye_x, eye_y = 0.0, T_((0, 0.085))[1]
    elif motiv == "geist":
        poly, k, cx, cy = _scale_to(g.ghost_unit(), S)
        T_ = lambda p: ((p[0] - cx) * k, (p[1] - cy) * k)
        for s_ in (1, -1):
            e = [(x + s_ * 0.085, y + 0.30) for x, y in g._ellipse_pts(0, 0, 0.05, 0.075, 0, 2 * math.pi, 22)[:-1]]
            holes.append([T_(p) for p in e])
        holes.append([T_((x, y + 0.15)) for x, y in g._ellipse_pts(0, 0, 0.05, 0.065, 0, 2 * math.pi, 22)[:-1]])
        for s_ in (1, -1):                                     # Stofffalten
            eng.append(([T_((s_ * 0.18, -0.05)), T_((s_ * 0.20, -0.25)), T_((s_ * 0.24, -0.40))], False))
            eng.append(([T_((s_ * 0.06, -0.20)), T_((s_ * 0.05, -0.34))], False))
        text_box = (T_((0, -0.07)), 0.40 * S, 0.12 * S)
        eye_x, eye_y = 0.0, T_((0, 0.50))[1]
    elif motiv == "totenkopf":
        poly, k, cx, cy = _scale_to(g.skull_unit(), S)
        T_ = lambda p: ((p[0] - cx) * k, (p[1] - cy) * k)
        holes = [[T_((x / S0, y / S0)) for x, y in h] for S0 in (1.0,) for h in g.skull_holes(0, 0, 1.0)]
        eng.append(([T_((0.0, 0.48)), T_((0.02, 0.40)), T_((-0.02, 0.33)), T_((0.01, 0.26))], False))   # Naht
        eng.append(([T_((-0.30, 0.30)), T_((-0.22, 0.34)), T_((-0.16, 0.30))], False))
        eng.append(([T_((0.22, 0.42)), T_((0.26, 0.34)), T_((0.33, 0.30)), T_((0.30, 0.22))], False))  # Riss
        eng.append(([T_((-0.25, -0.26)), T_((0.25, -0.26))], False))
        eye_x, eye_y = 0.0, T_((0, 0.50))[1]
    elif motiv == "katze":
        poly, k, cx, cy = _scale_to(g.cat_unit(), S)
        T_ = lambda p: ((p[0] - cx) * k, (p[1] - cy) * k)
        put.append([T_(p) for p in [(0.02, 0.22), (0.05, 0.245), (0.08, 0.22), (0.05, 0.205)]])   # Auge
        for dy in (-0.01, 0.02):                                                                 # Schnurrhaare
            eng.append(([T_((0.06, 0.12 + dy)), T_((0.14, 0.13 + dy * 2))], False))
        eng.append(([T_((-0.12, 0.08)), T_((-0.02, 0.05)), T_((0.07, 0.08))], False))           # Halsband
        put.append(circle(*T_((-0.02, 0.025)), 0.018 * S, 0.05))                               # Glöckchen
        eng.append(([T_((-0.20, -0.30)), T_((-0.16, -0.10))], False))
        eye_x, eye_y = T_((-0.10, 0.30))[0], T_((-0.1, 0.36))[1]
    elif motiv == "hexenhut":
        poly, k, cx, cy = _scale_to(g.hat_unit(), S)
        T_ = lambda p: ((p[0] - cx) * k, (p[1] - cy) * k)
        eng.append(([T_((-0.21, -0.16)), T_((-0.02, -0.15)), T_((0.20, -0.16))], False))      # Hutband
        eng.append(([T_((-0.215, -0.20)), T_((-0.02, -0.19)), T_((0.205, -0.20))], False))
        bw, bh = 0.07, 0.06
        holes.append([T_(p) for p in rect(-0.035, -0.205, bw, bh)])                             # Schnalle
        for (x, y, r) in ((-0.05, 0.02, 0.03), (0.05, 0.10, 0.022), (0.0, -0.08, 0.018), (0.08, 0.22, 0.02)):
            put.append([T_(p) for p in g.place([(math.cos(math.pi / 2 + i * math.pi / 5) * (1 if i % 2 == 0 else 0.45),
                                                    math.sin(math.pi / 2 + i * math.pi / 5) * (1 if i % 2 == 0 else 0.45))
                                                   for i in range(10)], x, y, r)])
        text_box = (T_((0.0, -0.31)), 0.70 * S, 0.06 * S)
        eye_x, eye_y = T_((0.31, 0.36))[0], T_((0.31, 0.37))[1]
    elif motiv == "kuerbis":
        pk = g.pumpkin(0.0, 0.0, 1.0, 0.80)
        poly, k, cx, cy = _scale_to(pk, S)
        T_ = lambda p: ((p[0] - cx) * k, (p[1] - cy) * k)
        holes = [[T_(p) for p in h] for h in g.pumpkin_face("klassisch", 0.0, 0.40, 0.74, 0.55)]
        for s_ in (-1, 1):
            for f in (0.18, 0.36):
                eng.append((bezier_q(T_((s_ * f * 0.3, 0.70)), T_((s_ * (0.1 + f), 0.40)), T_((s_ * f * 0.35, 0.04)),
                                     16), False))
        text_box = None if not text else (T_((0.0, 0.62)), 0.36 * S, 0.06 * S)
        eye_x, eye_y = T_((0.03, 0.98))[0], max(p[1] for p in poly)
    elif motiv == "spinnennetz":
        R = S / 2
        poly = circle(0.0, 0.0, R, cfg.arc_tolerance)
        holes = g.web(0.0, 0.0, R - max(web, 1.4) * 1.2, math.radians(90), math.radians(450), 5, 12,
                      max(web, 1.4))[1]
        put.append(g.spider(0.0, -0.02 * S, 0.30 * S, 0.5))
        eye_x, eye_y = 0.0, R
        holes = [h for h in holes if not any(point_in_polygon(p, put[-1]) for p in h) and
                 min_distance(h, put[-1], limit=1.0) >= 1.0]
    else:
        raise ValueError(motiv)
    if motiv not in ("spinnennetz",):
        poly = oriented(poly, True)
    # Öse oben
    r_e = max(0.07 * S, 3.4)
    top_pts = [p for p in poly if abs(p[0] - eye_x) < r_e * 0.6]
    y_top = max(p[1] for p in top_pts) if top_pts else eye_y
    outline, eye_hole = _eyelet(poly, eye_x, y_top, r_e, web)
    part = Part(f"{name}", outline)
    part.add_hole(eye_hole)
    for h in holes:
        if g.hole_ok(h, 0.3) and abs(g.signed_area(h)) > 2.0 and \
                min_distance(h, outline, limit=web) >= web and min_distance(h, eye_hole, limit=web) >= web and \
                all(min_distance(h, q, limit=web) >= web for q in part.holes):
            part.add_hole(h)
    cv = dk.Canvas(part, margin=0.9, hole_margin=0.9, seed=cfg.seed)
    for p_ in put:
        cv.put(p_, True, reserve=0.6)
    if text and text_box:
        (tx, ty), bw_, bh_ = text_box
        try:
            strokes, _ = fit_text(text, tx, ty, bw_, bh_, min_h=2.2, max_cap=bh_, style=schrift)
            for st in strokes:
                cv.draw(st)
            cv.block_strokes([(st, False) for st in strokes], 0.6)
        except ValueError:
            pass
    for pts, closed in eng:
        cv.draw(pts, closed)
    return part


def build(cfg, name="halloween_anhaenger", motiv="alle", size=80.0, text="", schrift="normal"):
    S = cfg.s(size)
    if not 45 <= S <= 160:
        raise ValueError("Anhänger: Größe muss zwischen 45 und 160 mm liegen")
    if motiv != "alle":
        dk.check_choice("Motiv", motiv, MOTIFS)
    bad = unsupported(text or "")
    if bad:
        raise ValueError(f"Zeichen {''.join(bad)!r} gibt es in der Gravurschrift nicht")
    web = max(cfg.min_web * 1.5, 1.5)
    rng = random.Random(cfg.seed)
    motifs = [m for m, _ in MOTIFS] if motiv == "alle" else [motiv]
    asm = Assembly(name, params=dict(motiv=motiv, size=S, **({"text": text} if text else {})))
    for m in motifs:
        asm.parts.append(build_one(cfg, f"{name}_{m}", m, S, text, schrift, rng, web))
    asm.notes.append("Anhänger an einem Faden durch die Öse aufhängen. Tipp: schwarz lasiert vor einem "
                     "hellen Fenster wirken sie wie Scherenschnitte.")
    return asm
