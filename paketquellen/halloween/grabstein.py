"""
Grabstein – schaurige Tischdeko mit graviertem Grabspruch.

Ein Grabstein (rund, gotisch, Kreuz oder schief abgebrochen) mit Zierrahmen, Grabspruch,
Ornament (Totenkopf, Fledermaus, Kreuz), Rissen und Efeuranke. Auf Wunsch schaut ein Gespenst
hinter dem Stein hervor. Steht in einem Erdhügel-Sockel.
"""
import importlib.util
import math
import os
import random
import sys

from steckwerk import Assembly, Part, bezier_q, circle, min_distance, oriented
from models import _deko as dk
from models._font import STYLES, fit_text, unsupported
from models._stand import stand_base, tab_feature_at
from pakete import bibliothek, flag, num, sel, txt


def _lib():
    return bibliothek("verzierungen").G


g = _lib()

FORMS = [("rund", "rund"), ("gotisch", "gotisch (Spitzbogen)"), ("kreuz", "Kreuz"), ("schief", "schief abgebrochen")]
ORNAMENTS = [("totenkopf", "Totenkopf"), ("fledermaus", "Fledermaus"), ("kreuz", "Kreuz"), ("keins", "keins")]

UEBERSETZUNG = {"en": g.EN}

INFO = dict(
    label="Grabstein",
    group="Halloween",
    desc="Grabstein mit Grabspruch, Ornament, Rissen und Efeu – auf Wunsch mit Gespenst dahinter.",
    params=[
        num("height", "Höhe", 140, 70, 280),
        sel("form", "Form", FORMS, "gotisch"),
        sel("ornament", "Ornament", ORNAMENTS, "totenkopf", when={"form": ["rund", "gotisch", "schief"]}),
        flag("geist", "Gespenst schaut hervor", True),
        flag("efeu", "Efeuranke", True),
        txt("text", "Grabspruch", "R.I.P.|Hier ruht|Graf Dracula|1431-1476", "| = neue Zeile",
            section="Schrift und Beschriftung"),
        sel("schrift", "Schrift", [(s, s) for s in STYLES], "normal", section="Schrift und Beschriftung"),
        txt("sockel_text", "Text auf dem Sockel", "", "leer = ohne", section="Schrift und Beschriftung"),
    ],
)


def build(cfg, name="grabstein", height=140.0, form="gotisch", ornament="totenkopf", geist=True, efeu=True,
          text="R.I.P.|Hier ruht|Graf Dracula|1431-1476", schrift="normal", sockel_text=""):
    T = cfg.T
    H = cfg.s(height)
    if not 70 <= H <= 280:
        raise ValueError("Grabstein: Höhe muss zwischen 70 und 280 mm liegen")
    dk.check_choice("Form", form, FORMS)
    dk.check_choice("Ornament", ornament, ORNAMENTS)
    for t_ in (text, sockel_text):
        bad = unsupported(t_ or "")
        if bad:
            raise ValueError(f"Zeichen {''.join(bad)!r} gibt es in der Gravurschrift nicht")
    rng = random.Random(cfg.seed)
    web = max(cfg.min_web * 1.6, 1.6)
    W = 0.66 * H if form != "kreuz" else 0.62 * H
    stone = g.tombstone(form, W, H)
    tw = max(0.4 * W, 4 * T)
    # Unterkante mit Zapfen
    P = oriented(stone, True)
    i0 = min(range(len(P)), key=lambda i: (P[i][1], P[i][0]))
    P = P[i0:] + P[:i0]                       # beginnt links unten, läuft nach rechts unten …
    bx0 = -W / 2 if form != "kreuz" else -0.16 * W
    bx1 = -bx0
    tw = min(tw, (bx1 - bx0) * 0.7)
    rest = P[1:]                               # ab rechts unten über oben zurück
    outline = [(bx0, 0.0), (-tw / 2, 0.0), (-tw / 2, -T), (tw / 2, -T), (tw / 2, 0.0)] + rest
    outline = oriented(g.dedupe(outline, 0.1), True)
    # Gespenst hinter dem Stein
    ghost_box = None
    if geist:
        gh = 0.50 * H
        for dx, ang in ((0.34, -0.22), (0.30, -0.15), (0.38, -0.30), (0.26, -0.1)):
            gx, gy = dx * W + 0.06 * H, H * 0.90
            gp = g.place(g.ghost_unit(), gx, gy, gh, ang)
            try:
                outline = g.op2(outline, gp, "union")
                ghost_box = (gx, gy, gh, ang)
                break
            except ValueError:
                continue
    part = Part(f"{name}_stein", outline, features=[tab_feature_at("fuss", -tw / 2, 0.0, tw, T)])
    if ghost_box:
        gx, gy, gh, ang = ghost_box
        for s_ in (-1, 1):
            e = g._ellipse_pts(0, 0, 0.045, 0.07, 0, 2 * math.pi, 20)[:-1]
            e = [(x + s_ * 0.085, y + 0.30) for x, y in e]
            h = g.place(e, gx, gy, gh, ang)
            if min_distance(h, outline, limit=web) >= web:
                part.add_hole(h)
        mouth = g.place([(x, y + 0.14) for x, y in g._ellipse_pts(0, 0, 0.045, 0.06, 0, 2 * math.pi, 20)[:-1]],
                        gx, gy, gh, ang)
        if min_distance(mouth, outline, limit=web) >= web:
            part.add_hole(mouth)

    cv = dk.Canvas(part, margin=1.2, hole_margin=1.2, seed=cfg.seed)
    # Zierrahmen
    if form != "kreuz":
        inner = g.tombstone(form, W * 0.86, H * 0.90)
        inner = [(x, y + 0.04 * H) for x, y in inner]
        cv.draw(inner, True)
        inner2 = g.tombstone(form, W * 0.80, H * 0.85)
        inner2 = [(x, y + 0.06 * H) for x, y in inner2]
        cv.draw(inner2, True)
    # Ornament oben
    top_text = 0.70 * H if form != "schief" else 0.62 * H
    if form == "kreuz":
        orn_y = None
    else:
        orn_y = 0.78 * H if form != "schief" else 0.68 * H
    if orn_y and ornament != "keins":
        s = 0.14 * H
        if ornament == "totenkopf":
            sk = g.place(g.skull_unit(), 0.0, orn_y, s)
            cv.draw(sk, True)
            for hh in g.skull_holes(0.0, orn_y, s):
                cv.draw(hh, True)
            cv.block(sk, 0.8)
            for sgn in (-1, 1):                                       # gekreuzte Knochen
                a = math.radians(35) * sgn
                L = s * 0.75
                p0 = (-L * math.cos(a), orn_y - 0.42 * s - L * math.sin(a) * 0.4)
                p1 = (L * math.cos(a), orn_y - 0.42 * s + L * math.sin(a) * 0.4)
                cv.draw([p0, p1])
        elif ornament == "fledermaus":
            cv.put(g.place(g.bat_unit(0.5), 0.0, orn_y, s * 1.9), True, reserve=0.8)
        elif ornament == "kreuz":
            c = 0.06 * H
            cv.put([(-c / 4, orn_y - c), (c / 4, orn_y - c), (c / 4, orn_y + c * 0.2), (c * 0.8, orn_y + c * 0.2),
                    (c * 0.8, orn_y + c * 0.6), (c / 4, orn_y + c * 0.6), (c / 4, orn_y + c * 1.2),
                    (-c / 4, orn_y + c * 1.2), (-c / 4, orn_y + c * 0.6), (-c * 0.8, orn_y + c * 0.6),
                    (-c * 0.8, orn_y + c * 0.2), (-c / 4, orn_y + c * 0.2)], True, reserve=0.8)
        top_text = orn_y - 0.12 * H
    # Grabspruch
    if text.strip():
        if form == "kreuz":
            box = (0.0, 0.62 * H + 0.16 * W, 0.92 * W, 0.12 * W)
            lines = text.replace("|", " ").split()
            text_ = " ".join(lines[:1]) if lines else ""
            strokes, _ = fit_text(text_, box[0], box[1], box[2], box[3], min_h=2.0, max_cap=0.1 * W, style=schrift)
        else:
            y_lo = 0.14 * H
            strokes, _ = fit_text(text, 0.0, (y_lo + top_text) / 2, W * 0.66, top_text - y_lo, min_h=2.2,
                                  max_cap=0.075 * H, style=schrift)
        for st in strokes:
            cv.draw(st)
        cv.block_strokes([(st, False) for st in strokes], 0.8)
    # Risse
    for k in range(2):
        px, py = rng.uniform(-0.3, 0.3) * W, rng.uniform(0.55, 0.85) * H
        pts = [(px, py)]
        for _ in range(6):
            px += rng.uniform(-0.06, 0.06) * W
            py -= rng.uniform(0.03, 0.06) * H
            pts.append((px, py))
        cv.draw(pts)
        b = pts[3]
        cv.draw([b, (b[0] + rng.choice((-1, 1)) * 0.06 * W, b[1] - 0.04 * H)])
    # Efeu: Ranke von unten links hoch mit Blättern
    if efeu:
        x0 = bx0 + 0.05 * W
        path = [(x0 + 0.04 * W * math.sin(i * 0.7), 0.02 * H + i * 0.035 * H) for i in range(14)]
        cv.draw(path)
        for i in range(2, 14, 2):
            p = path[i]
            sgn = 1 if i % 4 == 0 else -1
            lf = [(0, 0), (0.5, 0.35), (1.0, 0.0), (0.5, -0.35)]
            lf = g.place(lf, p[0], p[1], 0.06 * H, math.radians(40 if sgn > 0 else 140))
            cv.put(lf, True)
    # Gras am Fuß
    x = bx0 + 1.0
    while x < bx1 - 1.0:
        hgt = rng.uniform(0.03, 0.07) * H
        cv.draw([(x, 0.012 * H), (x + rng.uniform(-0.02, 0.02) * W, 0.012 * H + hgt)])
        x += rng.uniform(0.02, 0.04) * W

    asm = Assembly(name, params=dict(height=H, form=form, ornament=ornament, geist=geist))
    asm.parts.append(part)
    stand_base(asm, part, "fuss", tw, cfg, max(0.55 * W, tw / 2 + 12), 0.22 * W, f"{name}_huegel",
               sockel_text or "", schrift, "gross")
    asm.notes.append(f"{name}: Stein in den Erdhügel stecken. Tipp: Stein mit grauer Lasur, Gravur dunkel "
                     "auslegen – dann wirkt er wie verwittert.")
    return asm
