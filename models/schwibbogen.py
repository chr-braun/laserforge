"""
schwibbogen.py – Lichterbogen nach erzgebirgischer Art.

Ein Bogen mit Kerzen obendrauf, darunter eine Szene als Scherenschnitt (Dorf, Wald oder Kirche),
die auf der Sockelleiste steht. Die Fenster der Häuser sind ausgeschnitten – mit einer
LED-Lichterkette dahinter leuchten sie. Der Bogen steckt mit zwei Zapfen in einer Bodenplatte.

  szene       dorf · wald · kirche
  kerzen      1–11 Kerzen auf dem Bogen
  bogen_deko  Zierlinie auf dem Bogen (Linienstile wie beim Schmuck, oder keine)
  fenster     Fenster der Häuser ausschneiden (an/aus)
  text        Gravur auf der Sockelleiste, z. B. „Frohe Weihnacht“ (| = neue Zeile)
"""
from __future__ import annotations

import math
from typing import List, Optional, Sequence, Tuple

from steckwerk import Assembly, Config, Part, Point, arc_points, arched, bezier_q, oriented, rect, slot_feature
from models import _deko as dk
from models._font import CASES, STYLES, fit_text, unsupported
from models._stand import tab_feature_at

SCENES = [("dorf", "Dorf"), ("wald", "Wald"), ("kirche", "Kirche")]
DECOS = [("keine", "keine")] + dk.LINE_STYLES
DEFAULTS = dict(width=240.0, kerzen=7, szene="dorf")

Poly = List[Point]


# --- Szene: Silhouetten, stehen auf y = 0, Einheit = Innenradius -------------------------------------

def _haus(x: float, w: float, hw: float, hr: float, chimney: bool) -> Tuple[Poly, List[Tuple]]:
    pts = [(x - w / 2, 0), (x - w / 2, hw), (x, hw + hr)]
    if chimney:
        def roof(u):
            return hw + hr * (1 - u / (w / 2))
        x1, x2 = .16 * w, .28 * w
        yc = hw + .92 * hr
        pts += [(x + x1, roof(x1)), (x + x1, yc), (x + x2, yc), (x + x2, roof(x2))]
    pts += [(x + w / 2, hw), (x + w / 2, 0)]
    ww, wh = .2 * w, .3 * hw
    wins = [("rect", x - .22 * w, .5 * hw, ww, wh), ("rect", x + .22 * w, .5 * hw, ww, wh),
            ("bogen", x, hw + .32 * hr, .14 * w, .3 * hr)]
    return pts, wins


def _baum(x: float, w: float, h: float) -> Tuple[Poly, List[Tuple]]:
    t = .16 * w
    right = [(t / 2, 0), (t / 2, .1 * h), (w / 2, .1 * h), (.2 * w, .42 * h), (.36 * w, .42 * h),
             (.12 * w, .72 * h), (.25 * w, .72 * h)]
    pts = [(x - u, v) for u, v in right] + [(x, h)] + [(x + u, v) for u, v in reversed(right)]
    return pts, []


def _kirche(x: float, w: float, h: float) -> Tuple[Poly, List[Tuple]]:
    tw = .26 * w
    pts = [(x - w / 2, 0), (x - w / 2, .3 * h), (x - tw / 2, .42 * h), (x - tw / 2, .64 * h),
           (x - tw / 2 - .03 * w, .64 * h), (x, h), (x + tw / 2 + .03 * w, .64 * h), (x + tw / 2, .64 * h),
           (x + tw / 2, .42 * h), (x + w / 2, .3 * h), (x + w / 2, 0)]
    wins = [("bogen", x, .44 * h, .45 * tw, .14 * h), ("rund", x, .58 * h, .14 * tw, 0),
            ("bogen", x - .33 * w, .12 * h, .1 * w, .12 * h), ("bogen", x + .33 * w, .12 * h, .1 * w, .12 * h)]
    return pts, wins


def scene(kind: str):
    """Elemente der Szene, von links nach rechts, nicht überlappend."""
    if kind == "dorf":
        return [_baum(-.80, .14, .30), _haus(-.52, .26, .20, .14, False), _haus(-.14, .32, .26, .20, True),
                _baum(.18, .16, .44), _haus(.48, .26, .22, .15, True), _baum(.78, .13, .28)]
    if kind == "wald":
        xs = [-.82, -.58, -.31, 0, .31, .58, .82]
        hs = [.28, .40, .50, .62, .50, .40, .28]
        ws = [.15, .20, .24, .28, .24, .20, .15]
        return [_baum(x, w, h) for x, w, h in zip(xs, ws, hs)]
    if kind == "kirche":
        return [_baum(-.80, .14, .30), _haus(-.52, .24, .20, .13, True), _kirche(0, .40, .74),
                _haus(.52, .24, .20, .13, False), _baum(.80, .14, .30)]
    raise ValueError(f"Szene {kind!r} unbekannt – erlaubt: {', '.join(dk.values(SCENES))}")


# --- Bauteile -----------------------------------------------------------------------------------------

def _flame(xc: float, y: float, fb: float, fh: float) -> Poly:
    right = bezier_q((xc + fb / 2, y), (xc + .95 * fb, y + .45 * fh), (xc, y + fh), 10)
    left = bezier_q((xc, y + fh), (xc - .95 * fb, y + .45 * fh), (xc - fb / 2, y), 10)
    return right + left[1:]


def _window(kind: str, x: float, y: float, w: float, h: float, tol: float) -> Poly:
    if kind == "rect":
        return rect(x - w / 2, y - h / 2, w, h, ccw=False)
    if kind == "rund":
        return list(reversed(arc_points(x, y, w, 0, 2 * math.pi, tol)[:-1]))
    return arched(x, y - h / 2, w, h, tol, ccw=False)


def build(cfg: Config, name: str = "schwibbogen", width: Optional[float] = None, kerzen: int = DEFAULTS["kerzen"],
          szene: str = DEFAULTS["szene"], bogen_deko: str = "sterne", fenster: bool = True, text: str = "",
          schrift: str = "normal", schreibweise: str = "gross") -> Assembly:
    T = cfg.T
    tol = cfg.arc_tolerance
    W = cfg.s(width or DEFAULTS["width"])
    if not 120 <= W <= 600:
        raise ValueError("Schwibbogen: Breite muss zwischen 120 und 600 mm liegen")
    if not 1 <= int(kerzen) <= 11:
        raise ValueError("Schwibbogen: 1 bis 11 Kerzen")
    kerzen = int(kerzen)
    dk.check_choice("Bogen-Deko", bogen_deko, DECOS)
    if schrift not in STYLES:
        raise ValueError(f"Schrift {schrift!r} unbekannt – erlaubt: {', '.join(STYLES)}")
    if schreibweise not in CASES:
        raise ValueError(f"Schreibweise {schreibweise!r} unbekannt – erlaubt: {', '.join(CASES)}")
    bad = unsupported(text or "")
    if bad:
        raise ValueError(f"Zeichen {''.join(bad)!r} gibt es in der Gravurschrift nicht")
    elems = scene(szene)

    Ro = W / 2
    bw = max(0.065 * W, 3 * T, 8.0)                   # Breite des Bogens
    Ri = Ro - bw
    hb = max(0.09 * W, 2.5 * T + 8.0)                 # Sockelleiste
    cw = max(0.032 * W, 6.0)
    ch = 0.085 * W
    fb, fh = 0.62 * cw, 1.5 * cw
    tw = max(0.1 * W, 4 * T)
    xt = Ro - 0.16 * W

    # Außenkontur: Unterkante mit zwei Zapfen, Bogen mit Kerzen
    pts: Poly = [(-Ro, 0.0)]
    for x0 in (-xt - tw / 2, xt - tw / 2):
        pts += [(x0, 0.0), (x0, -T), (x0 + tw, -T), (x0 + tw, 0.0)]
    pts += [(Ro, 0.0)]
    angs = [math.pi / 2] if kerzen == 1 else [math.radians(35 + 110 * i / (kerzen - 1)) for i in range(kerzen)]
    a_prev = 0.0
    for a in angs:
        xc = Ro * math.cos(a)
        xr, xl = xc + cw / 2, xc - cw / 2
        ar, al = math.acos(xr / Ro), math.acos(xl / Ro)
        y_top = hb + Ro * math.sin(a) + ch
        pts += arc_points(0, hb, Ro, a_prev, ar, tol)
        pts += [(xr, y_top), (xc + fb / 2, y_top)] + _flame(xc, y_top, fb, fh)[1:] + [(xl, y_top)]
        a_prev = al
    pts += arc_points(0, hb, Ro, a_prev, math.pi, tol)
    arch = Part(f"{name}_bogen", oriented(pts, True),
                features=[tab_feature_at("fuss_l", -xt - tw / 2, 0.0, tw, T),
                          tab_feature_at("fuss_r", xt - tw / 2, 0.0, tw, T)])

    # Innenraum: Himmel über der Szene (ein Durchbruch, die Szene bleibt stehen)
    web = max(cfg.min_web * 2.0, 2.5)
    sky: Poly = [(-Ri, hb)]
    holes_win: List[Poly] = []
    for poly, wins in elems:
        for x, y in poly:
            X, Y = x * Ri, hb + y * Ri
            lim = hb + math.sqrt(max(Ri * Ri - X * X, 0.0)) - web
            if Y > lim:
                raise ValueError("Szene passt nicht unter den Bogen")
            sky.append((X, Y))
        if fenster:
            for kind, x, y, w, h in wins:
                win = _window(kind, x * Ri, hb + y * Ri, w * Ri, h * Ri, tol)
                xs = [p[0] for p in win]
                if max(xs) - min(xs) >= 3.0:
                    holes_win.append(win)
    sky.append((Ri, hb))
    sky += arc_points(0, hb, Ri, 0.0, math.pi, tol)[1:-1]
    arch.add_hole(oriented(sky, False))
    for h in holes_win:
        arch.add_hole(h)

    # Gravuren: Zierlinie auf dem Bogen, Text auf der Sockelleiste
    if bogen_deko != "keine":
        cv = dk.Canvas(arch, margin=0.8, seed=cfg.seed)
        r = Ri + 0.18 * bw
        path = arc_points(0, hb, r, math.pi, 0.0, tol)
        dk.styled_line(cv, path, bogen_deko, 0.62 * bw, side=+1, seed=cfg.seed, gravity=False)
    if text.strip():
        box_w = 2 * (xt - tw / 2) - 4.0
        strokes, _ = fit_text(text, 0.0, hb / 2, box_w, hb - 2 * max(2.0, 0.15 * hb), min_h=3.0,
                              max_cap=0.5 * hb, style=schrift, case=schreibweise)
        for s in strokes:
            arch.add_engrave(s)

    # Bodenplatte mit zwei Schlitzen
    D = max(40.0, 0.17 * W, 8 * T)
    PW = W + 0.06 * W
    plate = Part(f"{name}_platte", rect(-PW / 2, -0.55 * D, PW, D))
    for fid, x in (("fuss_l", -xt), ("fuss_r", xt)):
        feat, hole = slot_feature(fid, x - tw / 2, -T / 2, tw, T, True, 0.0)
        plate.holes.append(hole)
        plate.features.append(feat)
    plate.add_engrave(rect(-PW / 2 + 3.0, -0.55 * D + 3.0, PW - 6.0, D - 6.0), closed=True)

    asm = Assembly(name, params=dict(width=W, kerzen=kerzen, szene=szene, bogen_deko=bogen_deko,
                                     fenster=fenster, **({"text": text} if text else {})))
    asm.parts += [arch, plate]
    for fid in ("fuss_l", "fuss_r"):
        asm.connect(f"{arch.name}:{fid}", f"{plate.name}:{fid}")
    asm.notes.append(f"{name}: Bogen mit beiden Zapfen in die Bodenplatte stecken (bei Bedarf leimen). "
                     "Eine LED-Lichterkette hinter der Szene lässt die Fenster leuchten.")
    return asm
