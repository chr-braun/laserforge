"""
_szenen.py – Bildaufbau der mehrlagigen Schneidebilder.

Eine Szene liefert für n Ebenen je eine Figur (hinten → vorne) im Sichtfenster: x von −W/2 bis W/2,
y von 0 (Unterkante) bis H. Alles, was auf einer Ebene stehen bleibt, muss mit dem Boden oder dem
Rahmen verbunden sein. Dazu kommt die Gestaltung der Rückwand (Mond, Sterne, Schlitten …).
"""
from __future__ import annotations

import math
import os
import sys
from typing import Callable, Dict, List, Sequence, Tuple
from pakete import bibliothek

_here = os.path.dirname(os.path.abspath(__file__))


def _sub(name: str):
    import importlib.util
    path = os.path.join(_here, name + ".py")
    key = "swpaket_ebenen_" + name
    mod = sys.modules.get(key)
    if mod is None or getattr(mod, "__file__", None) != path:
        spec = importlib.util.spec_from_file_location(key, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[key] = mod
        spec.loader.exec_module(mod)
    return mod


K = bibliothek("verzierungen").K
F = bibliothek("verzierungen").F
G = bibliothek("verzierungen").G
Figur = K.Figur


# --------------------------------------------------------------------------------------------------
# Gelände
# --------------------------------------------------------------------------------------------------

def profil(W: float, base: float, amp: float, seed: int, wellen: int = 3, salt: str = "") -> Callable[[float], float]:
    """Sanft gewellte Geländelinie y(x)."""
    r = K.rng(seed, "profil", salt)
    terms = [(r.uniform(0.5, 1.0) / (k + 1), (k + 1 + r.random() * 0.6) * math.pi / W, r.uniform(0, 2 * math.pi))
             for k in range(wellen)]
    norm = sum(a for a, _, _ in terms)

    def y(x: float) -> float:
        return base + amp * sum(a * math.sin(f * x + p) for a, f, p in terms) / norm
    return y


def boden(W: float, yfn: Callable[[float], float], step: float = 1.5) -> List[Tuple[float, float]]:
    n = int(W / step) + 2
    pts = [(-W / 2 - 6 + (W + 12) * i / n, yfn(-W / 2 - 6 + (W + 12) * i / n)) for i in range(n + 1)]
    return pts + [(W / 2 + 6, -30.0), (-W / 2 - 6, -30.0)]


def berge(W: float, H: float, seed: int, base: float, hoehe: float) -> Figur:
    """Bergkette mit gezackten Graten und einzelnen Gipfeln."""
    r = K.rng(seed, "berge")
    f = Figur()
    xs = [-W / 2 - 8]
    while xs[-1] < W / 2 + 8:
        xs.append(xs[-1] + r.uniform(0.10, 0.22) * W)
    pts = [(-W / 2 - 8, base)]
    for i, x in enumerate(xs[1:], 1):
        peak = (xs[i - 1] + x) / 2 + K.jitter(r, 0.03 * W)
        ph = base + hoehe * r.uniform(0.45, 1.0)
        # Grat zum Gipfel mit kleinen Zacken
        a = pts[-1]
        for k in range(1, 6):
            u = k / 6
            pts.append((a[0] + (peak - a[0]) * u, a[1] + (ph - a[1]) * u + K.jitter(r, 0.012 * H)))
        pts.append((peak, ph))
        valley = base + hoehe * r.uniform(0.05, 0.35)
        for k in range(1, 6):
            u = k / 6
            pts.append((peak + (x - peak) * u, ph + (valley - ph) * u + K.jitter(r, 0.012 * H)))
    f.add(pts + [(W / 2 + 8, -30.0), (-W / 2 - 8, -30.0)])
    return f


def wald(f: Figur, W: float, yfn, h0: float, h1: float, dichte: float, seed: int, x0=None, x1=None, salt=""):
    """Reihe von Fichten auf dem Gelände (Abstand ~ dichte × Höhe)."""
    r = K.rng(seed, "wald", salt)
    x = (x0 if x0 is not None else -W / 2 - h1 * 0.2)
    end = x1 if x1 is not None else W / 2 + h1 * 0.2
    k = 0
    while x < end:
        h = r.uniform(h0, h1)
        f.merge(F.fichte(h, seed * 31 + k, breite=r.uniform(0.5, 0.66)).place(x, yfn(x) - 0.04 * h, 1.0))
        x += h * dichte * r.uniform(0.7, 1.2)
        k += 1


# --------------------------------------------------------------------------------------------------
# Szene: Hirsch im Winterwald
# --------------------------------------------------------------------------------------------------

def winterwald(W: float, H: float, n: int, seed: int) -> List[Figur]:
    def berg():
        return berge(W, H, seed, 0.40 * H, 0.32 * H)

    def wald_fern():
        f = Figur()
        y = profil(W, 0.30 * H, 0.05 * H, seed, salt="fern")
        f.add(boden(W, y))
        wald(f, W, y, 0.10 * H, 0.17 * H, 0.42, seed, salt="fern")
        return f

    def wald_zwischen():
        f = Figur()
        y = profil(W, 0.22 * H, 0.05 * H, seed, salt="zw")
        f.add(boden(W, y))
        wald(f, W, y, 0.18 * H, 0.28 * H, 0.55, seed + 5, x0=-W / 2 - 10, x1=-0.05 * W, salt="zl")
        wald(f, W, y, 0.18 * H, 0.28 * H, 0.55, seed + 6, x0=0.25 * W, salt="zr")
        return f

    def hirsch():
        f = Figur()
        y = profil(W, 0.15 * H, 0.04 * H, seed, salt="hirsch")
        f.add(boden(W, y))
        sh = 0.22 * H
        hx = -0.02 * W
        # kleiner Hügel unter dem Hirsch
        top = y(hx) + 0.035 * H
        f.add(K.ellipse(hx, top - 0.05 * H, 0.34 * W, 0.05 * H, n=96))
        f.merge(F.hirsch(sh).place(hx + 0.12 * sh, top - 0.004 * H, 1.0, flip=True))
        wald(f, W, y, 0.30 * H, 0.42 * H, 0.5, seed + 2, x0=-W / 2 - 10, x1=-0.34 * W, salt="hl")
        wald(f, W, y, 0.22 * H, 0.30 * H, 0.5, seed + 4, x0=0.30 * W, salt="hr")
        return f

    def wald_nah():
        f = Figur()
        y = profil(W, 0.09 * H, 0.03 * H, seed, salt="nah")
        f.add(boden(W, y))
        wald(f, W, y, 0.40 * H, 0.55 * H, 0.45, seed + 3, x0=0.36 * W, salt="nr")
        return f

    def vorne():
        f = Figur()
        y = profil(W, 0.045 * H, 0.025 * H, seed, salt="vorne")
        f.add(boden(W, y))
        r = K.rng(seed, "vorne")
        f.merge(F.fichte(1.0 * H, seed + 11, breite=0.48).place(-W / 2 + 0.04 * W, y(-W / 2) - 0.02 * H, 1.0))
        f.merge(F.fichte(0.55 * H, seed + 12, breite=0.5).place(-W / 2 + 0.17 * W, y(-0.33 * W) - 0.02 * H, 1.0))
        f.merge(F.fichte(0.9 * H, seed + 13, breite=0.48).place(W / 2 - 0.05 * W, y(W / 2) - 0.02 * H, 1.0))
        for k in range(int(W / 14)):                                   # Gräser im Schnee
            x = -W / 2 + r.uniform(0, W)
            hh = r.uniform(0.02, 0.05) * H
            f.add(K.stroke(K.bez((x, y(x) - 1), (x + K.jitter(r, hh * 0.4), y(x) + hh * 0.6),
                                 (x + K.jitter(r, hh * 0.6), y(x) + hh), 6), 0.012 * H, 0.004 * H, cap="spitz"))
        return f

    order = {3: [wald_fern, hirsch, vorne],
             4: [berg, wald_fern, hirsch, vorne],
             5: [berg, wald_fern, hirsch, wald_nah, vorne],
             6: [berg, wald_fern, wald_zwischen, hirsch, wald_nah, vorne]}
    return [fn() for fn in order[n]]


def himmel_winterwald(W: float, H: float, seed: int) -> Tuple[Figur, Figur]:
    """Rückwand: (Durchbrüche, stehen bleibendes Material in den Durchbrüchen)."""
    loch = Figur()
    keep = Figur()
    loch.add(K.circle(0.26 * W, 0.78 * H, 0.10 * min(W, H), 96))
    sterne(loch, W, H, seed, [(0.26 * W, 0.78 * H, 0.14 * min(W, H))])
    return loch, keep


def sterne(f: Figur, W: float, H: float, seed: int, frei: Sequence[Tuple[float, float, float]], n: int = 0):
    """Funkelsterne im oberen Himmel, mit Abstand zueinander und zu den freien Kreisen."""
    r = K.rng(seed, "sterne")
    n = n or int(W * H / 1100)
    placed = list(frei)
    tries = 0
    while n and tries < 600:
        tries += 1
        x = r.uniform(-0.45 * W, 0.45 * W)
        y = r.uniform(0.45 * H, 0.95 * H)
        s = r.uniform(1.6, 3.6) * (1 + 0.004 * min(W, H))
        if any(math.hypot(x - a, y - b) < s + c + 4 for a, b, c in placed):
            continue
        placed.append((x, y, s))
        if r.random() < 0.6:
            f.add(K.sparkle(x, y, s, waist=0.24))
        else:
            f.add(K.star(x, y, s, s * 0.45, 5))
        n -= 1


# --------------------------------------------------------------------------------------------------
# Szene: Winterdorf
# --------------------------------------------------------------------------------------------------

def _dorf(f: Figur, W: float, yfn, xs, hmin: float, hmax: float, seed: int, salt: str):
    r = K.rng(seed, "dorf", salt)
    for k, x in enumerate(xs):
        h = r.uniform(hmin, hmax)
        w = h * r.uniform(0.85, 1.15)
        art = "traufe" if r.random() < 0.35 else "giebel"
        f.merge(F.haus(w, h, seed * 17 + k, art).place(x, yfn(x) - 0.03 * h, 1.0))


def winterdorf(W: float, H: float, n: int, seed: int) -> List[Figur]:
    def berg():
        return berge(W, H, seed + 1, 0.42 * H, 0.26 * H)

    def wald_fern():
        f = Figur()
        y = profil(W, 0.34 * H, 0.04 * H, seed, salt="dfern")
        f.add(boden(W, y))
        wald(f, W, y, 0.08 * H, 0.13 * H, 0.40, seed, salt="dfern")
        return f

    def dorf_fern():
        f = Figur()
        y = profil(W, 0.27 * H, 0.03 * H, seed, salt="dorf1")
        f.add(boden(W, y))
        _dorf(f, W, y, [-0.36 * W, -0.22 * W, 0.20 * W, 0.36 * W], 0.13 * H, 0.17 * H, seed, "a")
        f.merge(F.kirche(0.50 * H, seed).place(0.02 * W, y(0.0) - 0.01 * H, 1.0))
        return f

    def dorf_nah():
        f = Figur()
        y = profil(W, 0.15 * H, 0.03 * H, seed, salt="dorf2")
        f.add(boden(W, y))
        _dorf(f, W, y, [-0.33 * W, 0.33 * W], 0.22 * H, 0.26 * H, seed + 3, "b")
        wald(f, W, y, 0.22 * H, 0.30 * H, 0.5, seed + 4, x0=-W / 2 - 8, x1=-0.43 * W, salt="dl")
        wald(f, W, y, 0.22 * H, 0.30 * H, 0.5, seed + 5, x0=0.46 * W, salt="dr")
        return f

    def strasse():
        f = Figur()
        y = profil(W, 0.075 * H, 0.015 * H, seed, salt="str")
        f.add(boden(W, y))
        f.merge(F.laterne(0.42 * H).place(-0.13 * W, y(-0.13 * W) - 0.01 * H, 1.0))
        f.merge(F.schneemann(0.24 * H, seed).place(0.20 * W, y(0.20 * W) - 0.01 * H, 1.0))
        f.merge(F.zaun(-0.08 * W, 0.08 * W, 0.07 * H).place(0, y(0.0) - 0.008 * H, 1.0))
        f.merge(F.zaun(0.30 * W, 0.46 * W, 0.07 * H).place(0, y(0.38 * W) - 0.008 * H, 1.0))
        return f

    def vorne():
        f = Figur()
        y = profil(W, 0.035 * H, 0.015 * H, seed, salt="dvorne")
        f.add(boden(W, y))
        f.merge(F.fichte(0.92 * H, seed + 21, breite=0.40, schnee=True).place(-W / 2 + 0.03 * W, y(-W / 2) - 0.02 * H, 1.0))
        f.merge(F.fichte(0.70 * H, seed + 22, breite=0.40, schnee=True).place(W / 2 - 0.04 * W, y(W / 2) - 0.02 * H, 1.0))
        return f

    order = {3: [dorf_fern, strasse, vorne],
             4: [berg, dorf_fern, strasse, vorne],
             5: [berg, dorf_fern, dorf_nah, strasse, vorne],
             6: [berg, wald_fern, dorf_fern, dorf_nah, strasse, vorne]}
    return [fn() for fn in order[n]]


def himmel_mond(W: float, H: float, seed: int, mx: float = -0.28, my: float = 0.80, rf: float = 0.09) -> Tuple[Figur, Figur]:
    loch = Figur()
    mr = rf * min(W, H)
    loch.add(K.circle(mx * W, my * H, mr, 120))
    sterne(loch, W, H, seed, [(mx * W, my * H, mr * 1.4)])
    return loch, Figur()


# --------------------------------------------------------------------------------------------------
# Szene: Spukschloss
# --------------------------------------------------------------------------------------------------

def _unit(poly, x: float, y: float, s: float, ang: float = 0.0, flip: bool = False) -> Figur:
    return Figur().add(poly).place(x, y, s, ang, flip)


def _baum(x: float, y: float, h: float, seed: int, lean: float = 0.0, spread: float = 1.0) -> Figur:
    return F.knorrbaum(h, seed, lean=lean, krone=spread).place(x, y, 1.0)


def spukschloss(W: float, H: float, n: int, seed: int) -> List[Figur]:
    def berg():
        f = Figur()
        y = profil(W, 0.36 * H, 0.10 * H, seed, wellen=2, salt="sberg")
        f.add(boden(W, y))
        return f

    def schloss():
        f = Figur()
        y = profil(W, 0.30 * H, 0.05 * H, seed, salt="sschloss")
        f.add(boden(W, y))
        cx = 0.12 * W
        m = G.mansion(0.52 * W, 0.42 * H, seed, 1.2)
        g = Figur().add(m["poly"] + [(0.26 * W, -0.05 * H), (-0.26 * W, -0.05 * H)])
        g.cut(*m["holes"])
        f.merge(g.place(cx, y(cx) - 0.01 * H, 1.0))
        f.merge(_baum(-0.34 * W, y(-0.34 * W) - 0.01 * H, 0.26 * H, seed + 1, lean=0.1))
        return f

    def friedhof():
        f = Figur()
        y = profil(W, 0.17 * H, 0.03 * H, seed, salt="sfried")
        f.add(boden(W, y))
        r = K.rng(seed, "gräber")
        arten = ["rund", "gotisch", "kreuz", "schief", "rund"]
        for k, x in enumerate([-0.22 * W, -0.10 * W, 0.04 * W, 0.18 * W]):
            h = r.uniform(0.07, 0.10) * H
            stein = Figur().add(G.tombstone(arten[k % len(arten)], h * 0.7, h))
            f.merge(stein.place(x, y(x) - 0.01 * H, 1.0, ang=K.jitter(r, 0.08)))
        bar, gap = 1.6, 3.0
        x0, x1 = 0.26 * W, 0.50 * W
        fence = Figur().add(G.fence(x0, x1, 0.10 * H, bar, gap) + [(x1, -0.03 * H), (x0, -0.03 * H)])
        fence.cut(*G.fence_holes(x0, x1, 0.10 * H, bar, gap))
        f.merge(fence.place(0, y(0.38 * W) - 0.005 * H, 1.0))
        # Katze auf dem Zaunpfosten
        f.merge(_unit(G.cat_unit(), 0.29 * W, y(0.38 * W) + 0.12 * H, 0.08 * H))
        return f

    def kuerbisse():
        f = Figur()
        y = profil(W, 0.08 * H, 0.02 * H, seed, salt="skuerbis")
        f.add(boden(W, y))
        for x, w, kind in ((-0.10 * W, 0.17 * H, "gruselig"), (0.14 * W, 0.12 * H, "klassisch")):
            h = w * 0.82
            k = Figur().add(G.pumpkin(0.0, 0.0, w, h))
            k.cut(*G.pumpkin_face(kind, 0.0, h * 0.50, w * 0.74, h * 0.55))
            f.merge(k.place(x, y(x) - 0.14 * h, 1.0))
        return f

    def vorne():
        f = Figur()
        y = profil(W, 0.035 * H, 0.015 * H, seed, salt="svorne")
        f.add(boden(W, y))
        f.merge(_baum(-0.47 * W, y(-0.47 * W) - 0.02 * H, 0.85 * H, seed + 7, lean=0.25, spread=0.75))
        f.merge(_baum(0.48 * W, y(0.48 * W) - 0.02 * H, 0.70 * H, seed + 8, lean=-0.25, spread=0.7))
        return f

    order = {3: [schloss, friedhof, vorne],
             4: [schloss, friedhof, kuerbisse, vorne],
             5: [berg, schloss, friedhof, kuerbisse, vorne],
             6: [berg, schloss, friedhof, kuerbisse, vorne, vorne]}
    figs = [fn() for fn in order[n]]
    if n == 6:      # sechste Ebene: zweite Baumreihe statt doppelter Bäume
        f = Figur()
        y = profil(W, 0.24 * H, 0.03 * H, seed, salt="sbaum")
        f.add(boden(W, y))
        f.merge(_baum(-0.30 * W, y(-0.30 * W), 0.40 * H, seed + 11, lean=0.15))
        f.merge(_baum(0.40 * W, y(0.40 * W), 0.36 * H, seed + 12, lean=-0.1))
        figs = [figs[0], figs[1], f, figs[2], figs[3], figs[4]]
    return figs


def himmel_spuk(W: float, H: float, seed: int) -> Tuple[Figur, Figur]:
    """Großer Vollmond; Hexe und Fledermäuse fliegen über den Mondrand und bleiben so mit der Rückwand
    verbunden."""
    mx, my, mr = -0.16 * W, 0.70 * H, 0.17 * min(W, H)
    loch = Figur().add(K.circle(mx, my, mr, 140))
    sterne(loch, W, H, seed, [(mx, my, mr * 1.4)], n=max(4, int(W * H / 4000)))
    keep = Figur()
    keep.merge(_unit(G.witch_unit(), mx + 0.05 * mr, my - 0.12 * mr, 2.25 * mr, ang=0.10))
    for (dx, dy, s, wing) in ((-0.62, 0.62, 0.62, 0.6), (0.60, 0.62, 0.5, -0.4), (0.80, -0.38, 0.46, 0.2)):
        keep.merge(_unit(G.bat_unit(wing), mx + dx * mr, my + dy * mr, s * mr, ang=K.jitter(K.rng(seed, dx), 0.2)))
    return loch, keep


# --------------------------------------------------------------------------------------------------
# Szene: Weihnachtsnacht – der Weihnachtsmann fliegt mit seinem Gespann am Mond vorbei
# --------------------------------------------------------------------------------------------------

def _sternenschweif(f: Figur, pts, w0: float, w1: float, seed: int):
    """Funkelnder Schweif: geschwungene Bahn mit aufsitzenden Funkelsternen (alles verbunden)."""
    r = K.rng(seed, "schweif")
    bahn = K.spline(pts, n=12)
    f.add(K.stroke(bahn, w0, w1, cap="spitz"))
    L = K.path_len(bahn)
    pos = K.resample(bahn, 11.0)
    for i, (x, y) in enumerate(pos[1:-1], 1):
        u = i / len(pos)
        size = (4.2 - 1.8 * u) * r.uniform(0.8, 1.1)
        side = 1 if i % 2 else -1
        a, b = pos[i - 1], pos[i + 1]
        d = math.hypot(b[0] - a[0], b[1] - a[1]) or 1
        nx, ny = -(b[1] - a[1]) / d, (b[0] - a[0]) / d
        off = side * (w0 + (w1 - w0) * u) * 0.6
        if r.random() < 0.7:
            f.add(K.sparkle(x + nx * off, y + ny * off, size, waist=0.3, rot=math.pi / 2 + K.jitter(r, 0.3)))
        else:
            f.add(K.star(x + nx * off, y + ny * off, size * 0.8, size * 0.38, 5))


def weihnachtsnacht(W: float, H: float, n: int, seed: int) -> List[Figur]:
    def berg():
        return berge(W, H, seed + 2, 0.36 * H, 0.18 * H)

    def wald_fern():
        f = Figur()
        y = profil(W, 0.30 * H, 0.04 * H, seed, salt="wfern")
        f.add(boden(W, y))
        wald(f, W, y, 0.08 * H, 0.13 * H, 0.40, seed + 1, salt="wfern")
        return f

    def gespann():
        f = Figur()
        y = profil(W, 0.24 * H, 0.03 * H, seed, salt="wges")
        f.add(boden(W, y))
        r = K.rng(seed, "wdorf")
        for k, x in enumerate((-0.40 * W, -0.27 * W, 0.24 * W, 0.38 * W)):
            h = r.uniform(0.09, 0.12) * H
            f.merge(F.haus(h * r.uniform(0.9, 1.1), h, seed * 7 + k, "giebel").place(x, y(x) - 0.02 * h, 1.0))
        f.merge(F.kirche(0.34 * H, seed, turm="spitz").place(-0.02 * W, y(0.0) - 0.01 * H, 1.0))
        s = 0.10 * W
        sx, sy = -0.26 * W, 0.66 * H
        f.merge(F.gespann(2, 1.6 / s).place(sx, sy, s, ang=0.10))
        # Schweif vom Rahmen links bis hinter den Schlitten
        hinten = (sx - 1.0 * s * math.cos(0.10), sy + 0.45 * s - 1.0 * s * math.sin(0.10))
        _sternenschweif(f, [(-W / 2 - 6, 0.52 * H), (-0.44 * W, 0.58 * H), (hinten[0] - 0.05 * W, hinten[1] - 0.015 * H),
                            hinten], 2.6, 1.7, seed)
        return f

    def dorf():
        f = Figur()
        y = profil(W, 0.15 * H, 0.03 * H, seed, salt="wdorf2")
        f.add(boden(W, y))
        _dorf(f, W, y, [-0.30 * W, 0.08 * W, 0.30 * W], 0.17 * H, 0.22 * H, seed + 9, "w")
        return f

    def wald_nah():
        f = Figur()
        y = profil(W, 0.09 * H, 0.03 * H, seed, salt="wnah")
        f.add(boden(W, y))
        wald(f, W, y, 0.30 * H, 0.42 * H, 0.45, seed + 3, x0=-W / 2 - 10, x1=-0.36 * W, salt="wnl")
        f.merge(F.schneemann(0.18 * H, seed).place(-0.12 * W, y(-0.12 * W) - 0.01 * H, 1.0))
        return f

    def vorne():
        f = Figur()
        y = profil(W, 0.04 * H, 0.015 * H, seed, salt="wvorne")
        f.add(boden(W, y))
        f.merge(F.fichte(0.62 * H, seed + 31, breite=0.46, schnee=True).place(-W / 2 + 0.03 * W, y(-W / 2) - 0.02 * H, 1.0))
        f.merge(F.fichte(0.88 * H, seed + 32, breite=0.44, schnee=True).place(W / 2 - 0.05 * W, y(W / 2) - 0.02 * H, 1.0))
        f.merge(F.fichte(0.45 * H, seed + 33, breite=0.5, schnee=True).place(W / 2 - 0.18 * W, y(0.32 * W) - 0.02 * H, 1.0))
        return f

    order = {3: [gespann, dorf, vorne],
             4: [berg, gespann, dorf, vorne],
             5: [berg, gespann, dorf, wald_nah, vorne],
             6: [berg, wald_fern, gespann, dorf, wald_nah, vorne]}
    return [fn() for fn in order[n]]


def himmel_weihnacht(W: float, H: float, seed: int) -> Tuple[Figur, Figur]:
    return himmel_mond(W, H, seed, mx=-0.07, my=0.73, rf=0.19)


SZENEN = {"winterwald": (winterwald, himmel_winterwald),
          "winterdorf": (winterdorf, himmel_mond),
          "spukschloss": (spukschloss, himmel_spuk),
          "weihnachtsnacht": (weihnachtsnacht, himmel_weihnacht)}
