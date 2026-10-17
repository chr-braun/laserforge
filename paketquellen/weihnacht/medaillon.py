"""
Scherenschnitt-Medaillon – Fensterbild oder Baumanhänger mit einer Winterszene im Rahmen.

Wie beim Scherenschnitt bleibt die Szene als Silhouette stehen, der Himmel wird ausgeschnitten. Alles
hängt am Rahmen oder am Schneehügel, Mond und Sterne berühren den Rand. Rahmen rund, oval oder als
Rundbogen, auf Wunsch mit Wellenrand außen und Bogenkante innen.
"""
from __future__ import annotations

import math
import os
import sys
from typing import List

from steckwerk import Assembly, oriented
from pakete import bibliothek, flag, integer, num, sel

_here = os.path.dirname(os.path.abspath(__file__))


def _sub(name: str):
    import importlib.util
    path = os.path.join(_here, name + ".py")
    key = "swpaket_filigran_" + name
    mod = sys.modules.get(key)
    if mod is None or getattr(mod, "__file__", None) != path:
        spec = importlib.util.spec_from_file_location(key, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[key] = mod
        spec.loader.exec_module(mod)
    return mod


E = bibliothek("verzierungen").E
FG = _sub("_filigran")
F = bibliothek("verzierungen").F
K = E.K
Figur = K.Figur

RAHMEN = [("rund", "rund"), ("oval", "oval"), ("bogen", "Rundbogen")]
SZENEN = [("kirche", "Dorfkirche im Schnee"), ("hirsch", "Hirsch im Winterwald"), ("krippe", "Krippe mit Stern"),
          ("engel", "Engel zwischen Tannen"), ("schlitten", "Schlitten vor dem Mond"), ("dorf", "Winterdorf")]
KANTEN = [("schlicht", "schlicht"), ("wellen", "Wellenrand außen"), ("bogen", "Bogenkante innen"),
          ("beides", "Wellen und Bögen")]

INFO = dict(
    label="Scherenschnitt-Medaillon",
    group="Weihnachten",
    desc="Fensterbild oder Anhänger im Scherenschnitt-Stil: Kirche, Hirsch, Krippe, Engel, Schlitten oder "
         "Winterdorf im runden, ovalen oder Rundbogen-Rahmen.",
    params=[
        sel("szene", "Szene", SZENEN, "kirche"),
        sel("rahmen", "Rahmen", RAHMEN, "rund"),
        num("groesse", "Höhe", 100, 60, 280),
        sel("kante", "Randverzierung", KANTEN, "beides"),
        flag("mond", "Mond und Sterne", True),
        flag("spiegeln", "Szene spiegeln", False),
        integer("variante", "Variante", 1, 1, 9, help="ändert Bäume und Häuser"),
        integer("anzahl", "Anzahl", 1, 1, 8),
    ],
)

UEBERSETZUNG = {"en": {
    "Scherenschnitt-Medaillon": "Paper-cut medallion", "Filigran": "Filigree", "Weihnachten": "Christmas",
    "Fensterbild oder Anhänger im Scherenschnitt-Stil: Kirche, Hirsch, Krippe, Engel, Schlitten oder "
    "Winterdorf im runden, ovalen oder Rundbogen-Rahmen.":
        "Window picture or pendant in paper-cut style: church, stag, nativity, angel, sleigh or winter village "
        "in a round, oval or arched frame.",
    "Szene": "Scene", "Rahmen": "Frame", "Höhe": "Height", "Randverzierung": "Edge trim",
    "Mond und Sterne": "Moon and stars", "Szene spiegeln": "Mirror scene", "Variante": "Variant",
    "ändert Bäume und Häuser": "changes trees and houses", "Anzahl": "Count",
    "Dorfkirche im Schnee": "Village church in snow", "Hirsch im Winterwald": "Stag in winter forest",
    "Krippe mit Stern": "Nativity with star", "Engel zwischen Tannen": "Angel between firs",
    "Schlitten vor dem Mond": "Sleigh across the moon", "Winterdorf": "Winter village", "rund": "round",
    "oval": "oval", "Rundbogen": "Round arch", "schlicht": "plain", "Wellenrand außen": "Scalloped outside",
    "Bogenkante innen": "Arches inside", "Wellen und Bögen": "Scallops and arches",
}}


# --------------------------------------------------------------------------------------------------
# Rahmen
# --------------------------------------------------------------------------------------------------

def _umriss(rahmen: str, S: float):
    if rahmen == "rund":
        return oriented(K.circle(0, S / 2, S / 2, 200), True)
    if rahmen == "oval":
        return oriented(K.ellipse(0, S / 2, 0.39 * S, S / 2, 0.0, 200), True)
    w = 0.70 * S
    r = w / 2
    return oriented(K.chain([(-r, 0.0), (r, 0.0)], K.arc(0, S - r, r, 0, math.pi, 80)), True)


def _entlang(poly, step):
    """Punkte im Abstand step entlang eines geschlossenen Polygons."""
    pts = list(poly) + [poly[0]]
    L = K.path_len(pts)
    n = max(8, int(round(L / step)))
    return K.resample(pts, L / n)[:n]


# --------------------------------------------------------------------------------------------------
# Szenen: alles in mm, Feld-Unterkante bei y0, Breite W, Höhe H
# --------------------------------------------------------------------------------------------------

def _huegel(x0, x1, y, amp, seed):
    r = K.rng(seed, "huegel")
    ph = r.uniform(0, 6)
    pts = [(x0 - 5, y - 40)]
    n = 40
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i / n
        pts.append((x, y + amp * (0.6 * math.sin(ph + 5.0 * i / n) + 0.4 * math.sin(2 * ph + 11.0 * i / n))))
    pts.append((x1 + 5, y - 40))
    return pts


def _tannen(f, xs, y, hs, seed, schnee=True):
    for i, (x, h) in enumerate(zip(xs, hs)):
        f.merge(F.fichte(h, seed + i, breite=0.55, schnee=schnee).place(x, y - 0.02 * h, 1.0))


def _krippe(h: float) -> Figur:
    """Stall mit Stern, Maria kniend, Josef mit Stab, Kind in der Krippe. h = Höhe bis zur Sternspitze."""
    f = Figur()
    w = 0.05
    # Stall: Pfosten, Dach mit Überstand, Querbalken
    for x in (-0.46, 0.46):
        f.line([(x, 0.0), (x, 0.56)], w)
    f.line([(-0.62, 0.50), (0.0, 0.84), (0.62, 0.50)], 0.07)
    f.line([(-0.46, 0.50), (0.46, 0.50)], 0.035)
    for x in (-0.30, -0.15, 0.15, 0.30):                 # Dachlatten
        y = 0.84 - abs(x) / 0.62 * 0.34
        f.line([(x, 0.50), (x, y)], 0.025)
    # Stern von Bethlehem mit Schweif, berührt den First
    f.add(K.star(0.0, 0.97, 0.12, 0.045, 8))
    f.add(K.stroke([(0.0, 0.86), (0.0, 0.97)], 0.03, 0.03))
    # Krippe auf gekreuzten Beinen, Kind mit Heiligenschein
    f.line([(-0.12, 0.0), (0.10, 0.17)], 0.03)
    f.line([(0.12, 0.0), (-0.10, 0.17)], 0.03)
    f.add([(-0.16, 0.20), (0.16, 0.20), (0.12, 0.14), (-0.12, 0.14)])
    f.add(K.ellipse(0.02, 0.23, 0.10, 0.04, 0.0, 24))
    f.add(K.circle(-0.09, 0.25, 0.045, 18))
    f.add(K.ellipse(-0.09, 0.25, 0.075, 0.075, 0.0, 30))
    f.cut(K.ellipse(-0.09, 0.25, 0.058, 0.058, 0.0, 30))
    f.add(K.circle(-0.09, 0.25, 0.045, 18))
    # Maria kniend (links, blickt zum Kind)
    f.add(K.spline([(-0.40, 0.0), (-0.42, 0.10), (-0.38, 0.22), (-0.33, 0.30), (-0.27, 0.33), (-0.22, 0.30),
                    (-0.20, 0.22), (-0.16, 0.12), (-0.18, 0.04), (-0.24, 0.0)], closed=True, n=6))
    f.add(K.circle(-0.27, 0.37, 0.05, 20))
    f.add(K.spline([(-0.33, 0.30), (-0.34, 0.38), (-0.29, 0.43), (-0.23, 0.42), (-0.21, 0.36)], closed=True, n=6))
    f.add(K.stroke([(-0.24, 0.26), (-0.17, 0.24)], 0.035, 0.03))  # gefaltete Hände
    f.add(K.ellipse(-0.28, 0.41, 0.075, 0.075, 0.0, 30))
    f.cut(K.ellipse(-0.28, 0.41, 0.058, 0.058, 0.0, 30))
    f.add(K.circle(-0.27, 0.37, 0.05, 20))
    # Josef stehend mit Hirtenstab (rechts)
    f.add(K.spline([(0.20, 0.0), (0.22, 0.18), (0.23, 0.32), (0.26, 0.40), (0.31, 0.42), (0.36, 0.40),
                    (0.38, 0.30), (0.39, 0.14), (0.42, 0.0)], closed=True, n=6))
    f.add(K.circle(0.31, 0.47, 0.05, 20))
    f.add(K.spline([(0.27, 0.47), (0.28, 0.40), (0.31, 0.37), (0.34, 0.40), (0.35, 0.46)], closed=True, n=6))  # Bart
    f.line([(0.43, 0.0), (0.43, 0.52)], 0.03)
    f.line(K.arc(0.40, 0.52, 0.03, 0, math.pi, 8), 0.03)
    f.line([(0.36, 0.30), (0.43, 0.34)], 0.04)
    return f.place(0, 0, h)


def _mond(f, cx, cy, r, sichel=True):
    """Mond als Ring (Sichel), der mit dem Rahmen verbunden ist."""
    f.add(K.circle(cx, cy, r, 60))
    if sichel:
        f.cut(K.circle(cx - 0.42 * r, cy + 0.18 * r, 0.86 * r, 60))
    else:
        f.cut(K.circle(cx, cy, r * 0.80, 60))


def _szene(szene: str, W: float, H: float, y0: float, seed: int, mond: bool, wmin: float) -> Figur:
    f = Figur()
    yg = y0 + 0.16 * H                                   # Oberkante Schneehügel
    f.add(_huegel(-W / 2, W / 2, yg, 0.025 * H, seed))
    top = y0 + H
    if szene == "kirche":
        f.merge(F.kirche(0.62 * H, seed, "zwiebel").place(-0.06 * W, yg - 0.01 * H, 1.0))
        _tannen(f, [-0.36 * W, 0.34 * W, 0.44 * W], yg, [0.42 * H, 0.36 * H, 0.26 * H], seed)
        if mond:
            _mond(f, 0.30 * W, top - 0.16 * H, 0.10 * H)
    elif szene == "hirsch":
        h = 0.27 * H
        f.merge(F.hirsch(h, wmin_mm=wmin).place(0.02 * W, yg - 0.02 * H, 1.0))
        _tannen(f, [-0.40 * W, -0.27 * W, 0.40 * W], yg, [0.55 * H, 0.38 * H, 0.46 * H], seed)
        if mond:
            _mond(f, -0.08 * W, top - 0.14 * H, 0.10 * H)
    elif szene == "krippe":
        f.merge(_krippe(0.66 * H).place(0.0, yg - 0.01 * H, 1.0))
        _tannen(f, [-0.42 * W, 0.42 * W], yg, [0.30 * H, 0.26 * H], seed)
    elif szene == "engel":
        f.merge(F.engel(0.62 * H).place(0.0, yg - 0.02 * H, 1.0))
        _tannen(f, [-0.38 * W, -0.25 * W, 0.27 * W, 0.40 * W], yg, [0.44 * H, 0.30 * H, 0.32 * H, 0.46 * H], seed)
        if mond:
            _mond(f, -0.24 * W, top - 0.12 * H, 0.08 * H)
    elif szene == "schlitten":
        # Vollmond oben am Rahmen, das Gespann ist als Schattenriss aus dem Mond geschnitten
        mr = 0.27 * H
        mc = (0.04 * W, top - 0.24 * H)
        f.add(K.circle(mc[0], mc[1], mr, 90))
        n_r = 1 if H < 170 else 2
        x0, gy0, x1, gy1 = F.gespann(n_r).bbox()
        s = 1.50 * mr / (x1 - x0)
        g = F.gespann(n_r, wmin=max(0.05, (wmin * 0.7) / s))
        x0, gy0, x1, gy1 = g.bbox()
        s = 1.50 * mr / (x1 - x0)
        g = g.place(mc[0] - (x0 + x1) / 2 * s, mc[1] - (gy0 + gy1) / 2 * s + 0.02 * mr, s, ang=0.06)
        f.ops += [("-", p) for sg, p in g.ops if sg == "+"]
        f.merge(F.haus(0.20 * W, 0.24 * H, seed, "giebel").place(-0.22 * W, yg - 0.01 * H, 1.0))
        f.merge(F.haus(0.16 * W, 0.19 * H, seed + 1, "traufe").place(0.16 * W, yg - 0.01 * H, 1.0))
        _tannen(f, [-0.42 * W, 0.0, 0.40 * W], yg, [0.30 * H, 0.22 * H, 0.26 * H], seed)
    elif szene == "dorf":
        f.merge(F.kirche(0.50 * H, seed, "spitz").place(0.04 * W, yg - 0.01 * H, 1.0))
        f.merge(F.haus(0.20 * W, 0.26 * H, seed, "giebel").place(-0.28 * W, yg - 0.01 * H, 1.0))
        f.merge(F.haus(0.15 * W, 0.20 * H, seed + 2, "traufe").place(0.36 * W, yg - 0.01 * H, 1.0))
        _tannen(f, [-0.44 * W, -0.10 * W, 0.20 * W], yg, [0.34 * H, 0.20 * H, 0.18 * H], seed)
        if mond:
            _mond(f, -0.22 * W, top - 0.14 * H, 0.09 * H)
    else:
        raise ValueError(f"Unbekannte Szene {szene!r}")
    return f


def _sterne(fld, S, seed, anzahl):
    """Kleine Sterne, die an der Innenkante des Rahmens sitzen (halb im Rahmen, also gehalten)."""
    r = K.rng(seed, "sterne")
    pts = _entlang(fld, 1.0)
    ys = [p[1] for p in fld]
    oben = [p for p in pts if p[1] > min(ys) + 0.55 * (max(ys) - min(ys))]
    out = []
    for k in range(anzahl):
        x, y = oben[int((k + 0.5 + 0.3 * r.uniform(-1, 1)) / anzahl * len(oben)) % len(oben)]
        rs = S * r.uniform(0.035, 0.05)
        cy = (max(ys) + min(ys)) / 2
        d = math.hypot(x, y - cy) or 1.0
        x, y = x - x / d * rs * 0.9, y - (y - cy) / d * rs * 0.9
        out.append(K.star(x, y, rs, rs * 0.42, 5, math.pi / 2 + r.uniform(-0.3, 0.3)))
    return out


# --------------------------------------------------------------------------------------------------

def _teil(cfg, name, szene, rahmen, S, kante, mond, spiegeln, seed, notes):
    web, kerf = cfg.min_web, cfg.kerf
    wmin = web + kerf + 0.45
    umriss = _umriss(rahmen, S)
    rand = max(2 * web + 1.0, 0.04 * S)
    fld = FG.feld(umriss, rand)
    xs = [p[0] for p in fld]
    ys = [p[1] for p in fld]
    W, H, y0 = max(xs) - min(xs), max(ys) - min(ys), min(ys)
    scene = _szene(szene, W, H, y0, seed, mond, wmin)
    if spiegeln:
        scene = scene.map(lambda p: (-p[0], p[1]))
    extra = []
    if kante in ("wellen", "beides"):                    # Wellenrand: Halbkreise auf der Außenkante
        rw = max(1.6, 0.022 * S)
        extra += [K.circle(x, y, rw, 20) for x, y in _entlang(umriss, 1.7 * rw)]
    top = max(p[1] for p in umriss) + (max(1.6, 0.022 * S) if kante in ("wellen", "beides") else 0.0)
    ro = max(3.2, 0.04 * S)
    loop_c = (0.0, top + ro - 1.4)
    extra.append(K.circle(loop_c[0], loop_c[1], ro, 40))
    allx = [p[0] for p in umriss]
    ally = [p[1] for p in umriss]
    pad = 4.0
    lw = E.Leinwand((min(allx) - pad, min(ally) - pad, max(allx) + pad, loop_c[1] + ro + 2), 0.08)
    shape = lw.flaechen([umriss] + extra)
    mat = E._andnot(shape, lw.flaechen([fld]))
    fill = lw.flaechen([fld])
    mat = mat.union(E._and(lw.figur(scene), fill))
    if kante in ("bogen", "beides"):                     # Bogenkante: Halbkreise an der Innenkante
        rb = max(wmin * 1.2, 0.018 * S)
        mat = mat.union(E._and(lw.flaechen([K.circle(x, y, rb, 16) for x, y in _entlang(fld, 2.6 * rb)]), fill))
    if mond:
        mat = mat.union(E._and(lw.flaechen(_sterne(fld, S, seed, 4)), fill))
    mat = E._andnot(mat, lw.flaechen([K.circle(loop_c[0], loop_c[1], ro - max(web + 0.6, 1.4), 32)]))
    return E.teil_aus_raster(name, lw, mat, web, kerf, notes)


def build(cfg, name: str = "medaillon", szene: str = "kirche", rahmen: str = "rund", groesse: float = 100.0,
          kante: str = "beides", mond: bool = True, spiegeln: bool = False, variante: int = 1, anzahl: int = 1):
    if szene not in dict(SZENEN):
        raise ValueError(f"Unbekannte Szene {szene!r}")
    if rahmen not in dict(RAHMEN):
        raise ValueError(f"Unbekannter Rahmen {rahmen!r}")
    S = cfg.s(groesse)
    if S < 20 * (cfg.min_web + cfg.kerf) + 30:
        raise ValueError("Für einen Scherenschnitt ist das Medaillon zu klein – Höhe vergrößern")
    asm = Assembly(name, params=dict(szene=szene, rahmen=rahmen, groesse=S, kante=kante, mond=mond,
                                     spiegeln=spiegeln, variante=variante, anzahl=anzahl))
    notes: List[str] = []
    for i in range(anzahl):
        tag = f"{szene}_{rahmen}" + (f"_{i + 1}" if anzahl > 1 else "")
        seed = cfg.seed * 31 + variante * 7 + i
        asm.parts.append(_teil(cfg, tag, szene, rahmen, S, kante, mond, spiegeln, seed, notes))
    for t in dict.fromkeys(notes):
        asm.notes.append(t)
    asm.notes.append("Ins Fenster hängen: Mit Licht von hinten wirkt der Scherenschnitt am schönsten. "
                     "Feine Stellen mit einem Zahnstocher von hinten aus der Platte drücken.")
    if S < 90:
        asm.notes.append("Tipp: Ab etwa 100 mm Höhe kommen Fenster, Geweih und Gesichter deutlich besser heraus.")
    return asm
