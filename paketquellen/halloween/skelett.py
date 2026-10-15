"""
Skelett-Hampelmann – Totenkopf, Brustkorb mit Rippen, Becken, Ober-/Unterarme mit Händen und
Ober-/Unterschenkel mit Füßen als einzelne Teile.

Alle Teile sind in ihrer Einbaulage gezeichnet (Füße auf y = 0, Mitte x = 0): an jedem Gelenk haben
beide Teile ein Loch an genau derselben Stelle für eine Musterbeutelklammer oder einen Splint. Oberarme
und Oberschenkel bekommen auf Wunsch ein zweites, kleines Loch über dem Gelenk für die Hampelmann-Fäden.
"""
from __future__ import annotations

import math
import os
import sys
from typing import List, Tuple

from steckwerk import Assembly
from pakete import flag, num, sel

_here = os.path.dirname(os.path.abspath(__file__))


def _sub(name: str):
    import importlib.util
    path = os.path.join(_here, name + ".py")
    key = "swpaket_halloween_" + name
    mod = sys.modules.get(key)
    if mod is None or getattr(mod, "__file__", None) != path:
        spec = importlib.util.spec_from_file_location(key, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[key] = mod
        spec.loader.exec_module(mod)
    return mod


SP = _sub("_spuk")
K = SP.K
Figur = K.Figur

INFO = dict(
    label="Skelett-Hampelmann",
    group="Halloween",
    desc="Bewegliches Skelett: Totenkopf, Brustkorb mit Rippen, Becken, Arme mit Händen und Beine mit Füßen als "
         "einzelne Teile mit Gelenklöchern – auf Wunsch mit Fadenlöchern für die Hampelmann-Mechanik.",
    params=[
        num("hoehe", "Gesamthöhe", 300, 150, 500, help="vom Scheitel bis zu den Füßen"),
        num("loch", "Gelenkloch", 3, 2, 6, step=0.5, help="für Musterbeutelklammern oder Splinte"),
        flag("zugfaden", "Hampelmann-Fäden", True, help="zweites Loch über Schulter- und Hüftgelenk"),
        num("fadenloch", "Fadenloch", 2, 1.5, 4, step=0.5, when={"zugfaden": [True]}),
        sel("grinsen", "Gesicht", [("grinsend", "grinsend mit Zähnen"), ("schaurig", "schaurig mit Riss")],
            "grinsend"),
        flag("aufhaenger", "Aufhängeloch im Schädel", True),
    ],
)

UEBERSETZUNG = {"en": {
    "Skelett-Hampelmann": "Skeleton jumping jack",
    "Bewegliches Skelett: Totenkopf, Brustkorb mit Rippen, Becken, Arme mit Händen und Beine mit Füßen als "
    "einzelne Teile mit Gelenklöchern – auf Wunsch mit Fadenlöchern für die Hampelmann-Mechanik.":
        "Moving skeleton: skull, ribcage, pelvis, arms with hands and legs with feet as separate parts with joint "
        "holes – optionally with string holes for the jumping-jack mechanism.",
    "Gesamthöhe": "Total height", "vom Scheitel bis zu den Füßen": "from the top of the skull to the feet",
    "Gelenkloch": "Joint hole", "für Musterbeutelklammern oder Splinte": "for paper fasteners (brads) or split pins",
    "Hampelmann-Fäden": "Jumping-jack strings", "zweites Loch über Schulter- und Hüftgelenk":
        "second hole above the shoulder and hip joints", "Fadenloch": "String hole", "Gesicht": "Face",
    "grinsend mit Zähnen": "grinning with teeth", "schaurig mit Riss": "eerie with a crack",
    "Aufhängeloch im Schädel": "Hanging hole in the skull",
    "Skelett: Gesamthöhe muss zwischen 150 und 500 mm liegen": "Skeleton: total height must be between 150 and 500 mm",
    "Skelett: Gelenkloch muss zwischen 2 und 6 mm liegen": "Skeleton: joint hole must be between 2 and 6 mm",
    "Skelett: Fadenloch muss zwischen 1,5 und 4 mm liegen": "Skeleton: string hole must be between 1.5 and 4 mm",
    "Skelett: Gelenklöcher sind zu groß für diese Höhe – kleineres Loch oder größeres Skelett wählen":
        "Skeleton: joint holes are too large for this height – choose a smaller hole or a larger skeleton",
    "Gelenke: Je eine Musterbeutelklammer (oder Splint mit Unterlegscheibe) durch die übereinanderliegenden "
    "Löcher stecken – Kopf, Arme und Beine liegen vor dem Brustkorb bzw. Becken, Unterarme und Unterschenkel "
    "vor den Oberarmen und Oberschenkeln. Klammern nur so fest biegen, dass alles leicht schwingt.":
        "Joints: push a paper fastener (or a split pin with a washer) through each pair of overlapping holes – "
        "head, arms and legs lie in front of the ribcage or pelvis, forearms and shins in front of the upper arms "
        "and thighs. Bend the fasteners only so tight that everything swings freely.",
    "Hampelmann: Arme und Beine hängen lassen. Einen Faden straff zwischen den beiden Fadenlöchern der Oberarme "
    "spannen, einen zweiten zwischen denen der Oberschenkel (hinten). Den Zugfaden an beiden Querfäden in der "
    "Mitte festknoten und unten mit einer Holzperle beschweren – Ziehen lässt das Skelett zappeln.":
        "Jumping jack: let arms and legs hang down. Tie a string tightly between the two string holes of the upper "
        "arms and a second one between those of the thighs (at the back). Knot the pull string to the middle of "
        "both cross strings and weight it with a wooden bead – pulling makes the skeleton dance.",
    "Aufhängen: Faden durch das Loch im Schädel.": "Hanging: thread through the hole in the skull.",
    "Tipp: Weiß lasiert vor dunklem Hintergrund oder mit nachleuchtender Farbe bemalt.":
        "Tip: stained white in front of a dark background, or painted with glow-in-the-dark paint.",
}}


def _knochen(f: Figur, a, b, w0, wm, w1, wmin):
    """Röhrenknochen von a nach b: Enden breiter, Schaft in der Mitte schmaler."""
    path = [SP.lerp(a, b, t / 12) for t in range(13)]
    widths = []
    for i in range(13):
        t = i / 12
        if t < 0.5:
            wv = w0 + (wm - w0) * math.sin(math.pi * t)
        else:
            wv = w1 + (wm - w1) * math.sin(math.pi * t)
        widths.append(max(wv, wmin))
    f.add(K.stroke(path, 0, widths=widths, cap="rund"))


def build(cfg, name: str = "skelett", hoehe: float = 300.0, loch: float = 3.0, zugfaden: bool = True,
          fadenloch: float = 2.0, grinsen: str = "grinsend", aufhaenger: bool = True):
    from models import _deko as dk
    H = cfg.s(hoehe)
    if not 150 <= H <= 500:
        raise ValueError("Skelett: Gesamthöhe muss zwischen 150 und 500 mm liegen")
    if not 2 <= loch <= 6:
        raise ValueError("Skelett: Gelenkloch muss zwischen 2 und 6 mm liegen")
    if zugfaden and not 1.5 <= fadenloch <= 4:
        raise ValueError("Skelett: Fadenloch muss zwischen 1,5 und 4 mm liegen")
    dk.check_choice("Gesicht", grinsen, [("grinsend", ""), ("schaurig", "")])
    u = H / 100.0
    w, sw = SP.wmin(cfg), SP.smin(cfg)
    d = loch
    ring = max(2.0, 1.25 * w)
    rk = d / 2 + ring + 0.3                       # Gelenkknauf
    if rk > 3.3 * u:
        raise ValueError("Skelett: Gelenklöcher sind zu groß für diese Höhe – kleineres Loch oder größeres Skelett "
                         "wählen")
    ds = fadenloch
    U = lambda x, y: (x * u, y * u)
    # Gelenke (Einbaulage)
    N = U(0, 84.0)
    P = U(0, 52.5)
    S = {s: U(s * 11.5, 78.5) for s in (-1, 1)}
    El = {s: U(s * 14.2, 61.0) for s in (-1, 1)}
    Wr = {s: U(s * 15.6, 46.5) for s in (-1, 1)}
    Hp = {s: U(s * 6.5, 43.0) for s in (-1, 1)}
    Kn = {s: U(s * 7.3, 23.5) for s in (-1, 1)}
    An = {s: U(s * 7.8, 5.5) for s in (-1, 1)}
    notes: List[str] = []
    asm = Assembly(name, params=dict(hoehe=H, loch=d, zugfaden=zugfaden, grinsen=grinsen))
    seed = cfg.seed

    def knauf(f, p, r=None):
        f.add(K.circle(p[0], p[1], r or rk, 40))

    def faden(p, s):
        """Fadenloch über dem Gelenk p, zur Körpermitte versetzt."""
        dist = max(d / 2 + ds / 2 + w + 0.8, 2.6 * u)
        return (p[0] - s * 0.75 * dist, p[1] + 0.66 * dist)

    # ---------------------------------------------------------------- Kopf
    f = Figur()
    cr = K.spline([U(0, 100), U(3.6, 99.3), U(5.5, 96.8), U(5.8, 93.5), U(5.6, 91.2), U(4.6, 89.6),
                   U(4.1, 88.2), U(3.4, 86.4), U(2.4, 85.0), U(0, 84.6), U(-2.4, 85.0), U(-3.4, 86.4),
                   U(-4.1, 88.2), U(-4.6, 89.6), U(-5.6, 91.2), U(-5.8, 93.5), U(-5.5, 96.8), U(-3.6, 99.3)],
                  closed=True, n=6)
    f.add(cr)
    f.line([U(0, 85.5), N], max(2.2 * u, 2 * rk * 0.8))
    knauf(f, N)
    for s in (-1, 1):                                      # Augenhöhlen mit Brauenbogen
        eye = K.spline([U(s * 0.9, 93.6), U(s * 2.0, 94.4), U(s * 3.6, 94.0), U(s * 4.0, 92.6),
                        U(s * 3.4, 91.2), U(s * 2.1, 91.0), U(s * 1.1, 91.8)], closed=True, n=6)
        f.cut(eye)
        f.cut(K.stroke([U(s * 4.6, 90.6), U(s * 5.0, 89.4)], max(0.5 * u, sw)))        # Jochbein-Spalt
    nose = K.spline([U(0, 91.0), U(0.75, 89.3), U(0.35, 88.85), U(0, 89.15), U(-0.35, 88.85), U(-0.75, 89.3)],
                    closed=True, n=5)
    f.cut(nose)
    # Zahnreihe: Mundspalt, Zähne als Stege darüber
    y0, y1 = 86.5 * u, 88.0 * u
    xm = 2.9 * u
    f.cut(K.stroke([(-xm, (y0 + y1) / 2), (xm, (y0 + y1) / 2)], y1 - y0, cap="rund"))
    tw = max(0.75 * u, w)
    gap = max(0.45 * u, sw)
    nt = max(2, int((2 * xm + gap) / (tw + gap)))
    span = nt * tw + (nt - 1) * gap
    if grinsen == "grinsend" or True:
        for i in range(nt):
            x = -span / 2 + i * (tw + gap) + tw / 2
            f.add(K.rect(x - tw / 2, y0 - 0.3 * u, tw, y1 - y0 + 0.6 * u))
    if aufhaenger:
        pass
    gr_kopf = []
    gr_kopf.append((K.spline([U(-1.2, 99.9), U(-0.4, 98.6), U(0.5, 98.9), U(1.2, 97.6), U(2.4, 97.9), U(3.4, 96.5)],
                             n=4), False))                                                     # Schädelnaht
    gr_kopf.append((K.bez(U(-4.9, 90.3), U(-3.6, 86.0), U(-1.6, 85.6), 10), False))             # Unterkiefer
    gr_kopf.append((K.bez(U(4.9, 90.3), U(3.6, 86.0), U(1.6, 85.6), 10), False))
    if grinsen == "schaurig":
        crack = [U(1.2, 99.6), U(1.9, 98.0), U(1.3, 97.0), U(2.3, 95.6)]
        f.cut(K.stroke(crack, max(0.35 * u, sw), max(0.25 * u, sw)))
        gr_kopf.append(([U(2.3, 95.6), U(2.0, 94.9)], False))
    loecher = [(N[0], N[1], d)]
    if aufhaenger:
        loecher.append((0.0, 98.2 * u, max(2.0, min(4.0, 0.7 * u + 1.0))))
    kopf = SP.teil(f"{name}_kopf", f, cfg, notes, loecher)
    SP.gravur(kopf, gr_kopf, seed)
    asm.parts.append(kopf)

    # ---------------------------------------------------------------- Brustkorb mit Wirbelsäule
    f = Figur()
    cage_r = [U(0, 81.3), U(4.0, 81.0), U(6.6, 79.4), U(8.4, 76.2), U(9.4, 72.0), U(9.6, 67.6), U(9.0, 63.8),
              U(7.6, 61.6)]
    cage = K.spline(cage_r + [(-x, y) for x, y in reversed(cage_r[1:])], closed=True, n=6)
    # untere Öffnung (Rippenbogen) als Einschnitt der Kontur
    f.add(cage)
    for s in (-1, 1):                                      # Schlüsselbeine und Schultern
        f.line(K.bez(U(s * 1.0, 80.6), U(s * 6.0, 81.6), S[s], 10), max(1.5 * u, w * 1.3), max(1.2 * u, w))
        knauf(f, S[s], max(rk, 1.9 * u))
    # Zwischenrippenräume als geschwungene Schlitze, Brustbein und Wirbelsäule bleiben stehen
    gw = max(0.9 * u, sw * 1.2)
    rib = max(1.25 * u, w * 1.05)
    k = 0
    y = 79.2 * u
    while y - 2.0 * u > 64.0 * u:
        for s in (-1, 1):
            path = K.bez((s * 2.1 * u, y), (s * 9.6 * u, y + 1.4 * u), (s * 7.2 * u, y - 5.2 * u), 22)
            path = [p for p in path if abs(p[0]) >= 2.0 * u]
            path = SP.innen(path, cage, w + gw / 2 + 0.4)
            if len(path) >= 2 and K.path_len(path) > 3:
                f.cut(K.stroke(path, gw, gw * 0.8, "rund"))
        y -= gw + rib
        k += 1
    # Rippenbogen unten: zwei Bögen neben der Lendenwirbelsäule
    for s in (-1, 1):
        arch = K.chain([(s * 1.6 * u, 61.0 * u)], K.bez((s * 1.6 * u, 65.6 * u), (s * 4.0 * u, 64.5 * u),
                                                         (s * 7.4 * u, 60.8 * u), 12), [(s * 1.6 * u, 59.0 * u)])
        f.cut(arch)
    # Lendenwirbel
    f.add(K.rect(-1.6 * u, 53.0 * u, 3.2 * u, 10.0 * u))
    for j in range(5):
        yv = 54.4 * u + j * 1.9 * u
        f.add(K.rect(-2.5 * u, yv - 0.35 * u, 5.0 * u, max(0.7 * u, w)))           # Querfortsätze
        if j:
            for s in (-1, 1):
                f.cut(K.circle(s * 1.75 * u, yv - 0.95 * u, max(0.35 * u, sw * 0.6), 12))
    knauf(f, P)
    knauf(f, N)
    f.line([U(0, 80.0), N], max(1.8 * u, w * 1.4))
    loecher = [(N[0], N[1], d), (P[0], P[1], d)] + [(S[s][0], S[s][1], d) for s in (-1, 1)]
    torso = SP.teil(f"{name}_brustkorb", f, cfg, notes, loecher)
    SP.gravur(torso, [([U(0, 80.6), U(0, 66.4)], False)], seed)
    asm.parts.append(torso)

    # ---------------------------------------------------------------- Becken
    f = Figur()
    for s in (-1, 1):
        wing = K.spline([U(s * 1.4, 53.6), U(s * 4.6, 52.2), U(s * 8.4, 51.8), U(s * 10.0, 49.8), U(s * 9.4, 46.8),
                         U(s * 7.8, 44.6), U(s * 5.0, 43.2), U(s * 2.0, 45.0), U(s * 1.4, 49.0)], closed=True, n=6)
        f.add(wing)
        f.line([Hp[s], U(s * 3.6, 40.2), U(s * 0.9, 39.4)], max(1.6 * u, w * 1.3))       # Schambein
        f.line([Hp[s], U(s * 5.4, 39.0), U(s * 2.4, 38.6), U(s * 0.9, 39.4)], max(1.3 * u, w * 1.1))  # Sitzbein
        knauf(f, Hp[s], max(rk, 1.8 * u))
    f.add(K.spline([U(-2.6, 53.0), U(2.6, 53.0), U(1.9, 47.5), U(0.9, 43.6), U(0, 42.2), U(-0.9, 43.6),
                    U(-1.9, 47.5)], closed=True, n=5))                                          # Kreuzbein
    f.add(K.rect(-1.1 * u, 38.6 * u, 2.2 * u, 1.6 * u))                                       # Schambeinfuge
    for s in (-1, 1):
        # Darmbeinschaufel mit Durchbruch
        f.cut(K.spline([U(s * 3.6, 50.6), U(s * 6.6, 50.3), U(s * 8.2, 48.8), U(s * 7.0, 46.6), U(s * 4.8, 46.5),
                        U(s * 3.4, 48.2)], closed=True, n=6))
        for j in range(3):                                                                     # Kreuzbeinlöcher
            yy = 51.3 - j * 2.2
            f.cut(K.circle(s * (1.15 - 0.15 * j) * u, yy * u, max(0.38 * u, sw * 0.62), 14))
    knauf(f, P)
    f.line([P, U(0, 53.4)], max(2.2 * u, w))
    loecher = [(P[0], P[1], d)] + [(Hp[s][0], Hp[s][1], d) for s in (-1, 1)]
    becken = SP.teil(f"{name}_becken", f, cfg, notes, loecher)
    asm.parts.append(becken)

    # ---------------------------------------------------------------- Arme
    seite = {-1: "links", 1: "rechts"}
    for s in (-1, 1):
        f = Figur()
        _knochen(f, S[s], El[s], 2.4 * u, 1.35 * u, 2.0 * u, w * 1.1)
        knauf(f, S[s], max(rk, 1.7 * u))
        knauf(f, El[s])
        for c in (-1, 1):                                    # Gelenkrollen am Ellbogen
            f.add(K.circle(El[s][0] + c * 1.0 * u, El[s][1] + 0.4 * u, max(0.75 * u, w * 0.6), 20))
        loecher = [(S[s][0], S[s][1], d), (El[s][0], El[s][1], d)]
        if zugfaden:
            q = faden(S[s], s)
            f.line([S[s], q], max(2 * (ds / 2 + ring), 1.4 * u))
            loecher.append((q[0], q[1], ds))
        part = SP.teil(f"{name}_oberarm_{seite[s]}", f, cfg, notes, loecher)
        SP.gravur(part, [([SP.lerp(S[s], El[s], 0.3), SP.lerp(S[s], El[s], 0.7)], False)], seed)
        asm.parts.append(part)
        # Unterarm: Elle und Speiche mit Spalt, Hand mit Fingern
        f = Figur()
        e, wr = El[s], Wr[s]
        perp = (-(wr[1] - e[1]), wr[0] - e[0])
        L = math.hypot(*perp)
        perp = (perp[0] / L, perp[1] / L)
        off = 0.75 * u
        for c in (-1, 1):
            a = (e[0] + perp[0] * c * off * 0.6, e[1] + perp[1] * c * off * 0.6)
            b = (wr[0] + perp[0] * c * off, wr[1] + perp[1] * c * off)
            _knochen(f, a, b, 1.1 * u, 0.75 * u, 1.0 * u, w)
        knauf(f, e)
        mid1, mid2 = SP.lerp(e, wr, 0.30), SP.lerp(e, wr, 0.80)
        if 2 * off - 0.75 * u >= sw + 0.2 and 2 * off > sw + w:
            gap_w = max(sw, 2 * off - 1.5 * u)
            f.cut(K.stroke([mid1, mid2], gap_w, gap_w * 0.8))
        # Handwurzel, Mittelhand, Finger
        f.add(K.ellipse(wr[0] + s * 0.2 * u, wr[1] - 1.0 * u, 1.55 * u, 1.3 * u, 0.0, 32))
        base = (wr[0] + s * 0.2 * u, wr[1] - 1.6 * u)
        fw = max(0.48 * u, w)
        for j, (dx, L1, L2) in enumerate(((-1.25, 3.0, 2.2), (-0.45, 3.4, 2.6), (0.35, 3.3, 2.5), (1.1, 2.9, 2.1))):
            p0 = (base[0] + s * dx * u * 0.9, base[1])
            ang = math.radians(-90 + s * dx * 7)
            p1 = (p0[0] + math.cos(ang) * L1 * u, p0[1] + math.sin(ang) * L1 * u)
            ang2 = ang - s * math.radians(6)
            p2 = (p1[0] + math.cos(ang2) * L2 * u, p1[1] + math.sin(ang2) * L2 * u)
            f.line([p0, p1], fw)
            f.line([p1, p2], fw * 0.9)
            f.add(K.circle(p1[0], p1[1], max(fw * 0.62, w * 0.55), 14))
        th0 = (base[0] - s * 1.3 * u, base[1] + 0.6 * u)                                    # Daumen
        th1 = (th0[0] - s * 1.6 * u, th0[1] - 1.6 * u)
        th2 = (th1[0] - s * 0.6 * u, th1[1] - 1.8 * u)
        f.line([th0, th1], fw)
        f.line([th1, th2], fw * 0.9)
        f.add(K.circle(th1[0], th1[1], max(fw * 0.62, w * 0.55), 14))
        part = SP.teil(f"{name}_unterarm_{seite[s]}", f, cfg, notes, [(e[0], e[1], d)])
        asm.parts.append(part)

    # ---------------------------------------------------------------- Beine
    for s in (-1, 1):
        f = Figur()
        h, kn = Hp[s], Kn[s]
        _knochen(f, h, kn, 2.4 * u, 1.55 * u, 2.6 * u, w * 1.2)
        knauf(f, h, max(rk, 1.8 * u))
        f.add(K.circle(h[0] + s * 1.6 * u, h[1] - 0.6 * u, 1.1 * u, 24))                     # Rollhügel
        for c in (-1, 1):                                                                   # Gelenkknorren
            f.add(K.circle(kn[0] + c * 1.05 * u, kn[1] + 0.3 * u, 1.05 * u, 24))
        knauf(f, kn)
        loecher = [(h[0], h[1], d), (kn[0], kn[1], d)]
        if zugfaden:
            q = faden(h, s)
            f.line([h, q], max(2 * (ds / 2 + ring), 1.4 * u))
            loecher.append((q[0], q[1], ds))
        part = SP.teil(f"{name}_oberschenkel_{seite[s]}", f, cfg, notes, loecher)
        SP.gravur(part, [([SP.lerp(h, kn, 0.25), SP.lerp(h, kn, 0.72)], False)], seed)
        asm.parts.append(part)
        # Unterschenkel: Schienbein + Wadenbein, Fuß im Profil nach außen
        f = Figur()
        an = An[s]
        _knochen(f, kn, an, 2.4 * u, 1.3 * u, 1.6 * u, w * 1.1)                              # Schienbein
        fa, fb = (kn[0] + s * 1.9 * u, kn[1] - 1.0 * u), (an[0] + s * 1.6 * u, an[1] + 0.4 * u)
        _knochen(f, fa, fb, 1.0 * u, 0.62 * u, 0.9 * u, w)                                   # Wadenbein
        knauf(f, kn)
        f.add(K.circle(an[0] + s * 0.4 * u, an[1], 1.4 * u, 28))                              # Knöchel
        # Fußwurzel mit Ferse, dann Mittelfußknochen und Zehen als einzelne Strahlen
        f.add(K.spline([(an[0] - s * 1.3 * u, an[1] - 0.4 * u), (an[0] - s * 1.5 * u, an[1] - 2.4 * u),
                        (an[0] + s * 0.2 * u, an[1] - 3.1 * u), (an[0] + s * 1.9 * u, an[1] - 2.4 * u),
                        (an[0] + s * 1.7 * u, an[1] + 0.3 * u)], closed=True, n=6))
        tw_ = max(0.55 * u, w)
        step = max(0.95 * u, tw_ + sw + 0.5)
        n_toe = 4 if 4 * step <= 4.2 * u else 3
        for j in range(n_toe):
            y_ = an[1] - 0.5 * u - j * step
            p0 = (an[0] + s * 1.2 * u, y_)
            p1 = (an[0] + s * (4.2 - 0.25 * j) * u, y_ - 0.5 * u)
            p2 = (p1[0] + s * (1.4 - 0.15 * j) * u, p1[1] - 0.45 * u)
            f.line([p0, p1], tw_ * (1.15 if j == 0 else 1.0), tw_)
            f.line([p1, p2], tw_ * 0.95)
            f.add(K.circle(p1[0], p1[1], max(tw_ * 0.62, w * 0.55), 14))
        # Spalt zwischen den Unterschenkelknochen
        g0, g1 = SP.lerp(kn, an, 0.22), SP.lerp(kn, an, 0.78)
        g0 = (g0[0] + s * 1.0 * u, g0[1])
        g1 = (g1[0] + s * 0.85 * u, g1[1])
        if 0.5 * u >= sw:
            f.cut(K.stroke([g0, g1], max(sw, 0.42 * u), max(sw, 0.35 * u)))
        part = SP.teil(f"{name}_unterschenkel_{seite[s]}", f, cfg, notes, [(kn[0], kn[1], d)])
        asm.parts.append(part)

    for t in dict.fromkeys(notes):
        asm.notes.append(t)
    asm.notes.append("Gelenke: Je eine Musterbeutelklammer (oder Splint mit Unterlegscheibe) durch die "
                     "übereinanderliegenden Löcher stecken – Kopf, Arme und Beine liegen vor dem Brustkorb bzw. Becken, "
                     "Unterarme und Unterschenkel vor den Oberarmen und Oberschenkeln. Klammern nur so fest biegen, "
                     "dass alles leicht schwingt.")
    if zugfaden:
        asm.notes.append("Hampelmann: Arme und Beine hängen lassen. Einen Faden straff zwischen den beiden "
                         "Fadenlöchern der Oberarme spannen, einen zweiten zwischen denen der Oberschenkel (hinten). "
                         "Den Zugfaden an beiden Querfäden in der Mitte festknoten und unten mit einer Holzperle "
                         "beschweren – Ziehen lässt das Skelett zappeln.")
    if aufhaenger:
        asm.notes.append("Aufhängen: Faden durch das Loch im Schädel.")
    asm.notes.append("Tipp: Weiß lasiert vor dunklem Hintergrund oder mit nachleuchtender Farbe bemalt.")
    return asm
