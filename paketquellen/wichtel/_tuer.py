"""
_tuer.py – gemeinsame Formen für Wichteltür und Wichtelfenster: Öffnung, Rahmen (Steinbogen/Holz),
Standplatte mit Schlitzen. Nutzt die Bibliothek „Verzierungen“.

Koordinaten: x = 0 in der Mitte, y = 0 unten (Boden bzw. Fensterbank).
"""
from __future__ import annotations

import math
from typing import List, Sequence, Tuple

from steckwerk import Part, oriented
from pakete import bibliothek

Z = bibliothek("verzierungen")
K = Z.K
Point = Tuple[float, float]
Poly = List[Point]

FORMEN = [("bogen", "Rundbogen"), ("spitz", "Spitzbogen"), ("eckig", "eckig, oben abgerundet")]
RAHMEN = [("steine", "Steinbogen"), ("holz", "Holzrahmen"), ("herzen", "mit Herzen"), ("sterne", "mit Sternen"),
          ("punkte", "mit Punkten"), ("glatt", "glatt")]


def form(art: str, W: float, H: float) -> Poly:
    """Öffnung bzw. Umriss, unten gerade (y = 0), oben je nach Art."""
    if art == "spitz":
        hs = max(0.0, H - W * 0.75)
        r = W * 0.82                       # gotischer Bogen: zwei Kreisbögen
        top = H
        cx_r = W / 2 - r                   # Mittelpunkt des rechten Bogens (links von der Mitte)
        a0 = 0.0
        a1 = math.acos((0 - cx_r) / r)
        h0 = hs
        arc_r = [(cx_r + r * math.cos(a), h0 + r * math.sin(a)) for a in (a0 + (a1 - a0) * i / 24 for i in range(25))]
        peak = arc_r[-1][1]
        sk = (top - hs) / max(1e-6, peak - hs)
        arc_r = [(x, hs + (y - hs) * sk) for x, y in arc_r]
        arc_l = [(-x, y) for x, y in reversed(arc_r)]
        return [(-W / 2, 0), (W / 2, 0)] + arc_r + arc_l[1:]
    if art == "eckig":
        r = min(W, H) * 0.18
        return [(-W / 2, 0), (W / 2, 0)] + K.arc(W / 2 - r, H - r, r, 0, math.pi / 2, 10) + \
            K.arc(-W / 2 + r, H - r, r, math.pi / 2, math.pi, 10)
    # Rundbogen
    r = W / 2
    hs = max(0.0, H - r)
    if H < r:
        return [(-W / 2, 0), (W / 2, 0)] + [(W / 2 * math.cos(a), H * math.sin(a))
                                             for a in (math.pi * i / 40 for i in range(1, 40))]
    return [(-W / 2, 0), (W / 2, 0), (W / 2, hs)] + K.arc(0, hs, r, 0, math.pi, 48)[1:-1] + [(-W / 2, hs)]


def mitte_linie(art: str, W: float, H: float, rb: float) -> Poly:
    """Offene Linie mitten im Rahmenband (unten links → oben → unten rechts)."""
    p = form(art, W + rb, H + rb / 2)
    # Unterkante weglassen: Punkte ab rechts unten bis links unten
    return p[1:] + [p[0]]


def rahmen_figur(cfg, art: str, W: float, H: float, rb: float, stil: str, kante: str) -> "Z.Figur":
    """Rahmenband um die Öffnung W × H (Breite rb) mit Kantenverzierung; Öffnung ausgeschnitten."""
    w = Z.wmin(cfg)
    aussen = form(art, W + 2 * rb, H + rb)
    fig = Z.Figur().add(aussen)
    if kante != "keine":
        g = max(3.2 * w, min(7.0, rb * 0.45))
        fig.merge(Z.kante(aussen, kante, g, w, ausser=lambda p: p[1] < g * 1.5))
    if stil in ("herzen", "sterne", "punkte"):
        g = max(3 * w, rb * 0.48)
        fig.merge(Z.durchbruch(mitte_linie(art, W, H, rb), stil, g, closed=False,
                               ausser=lambda p: p[1] < rb * 0.8))
    fig.cut(form(art, W, H))
    return fig


def rahmen_gravur(art: str, W: float, H: float, rb: float, stil: str) -> List[Tuple[Poly, bool]]:
    """Fugen im Rahmen: Steine (quer, versetzt) oder Holzmaserung."""
    linien = []
    if stil == "steine":
        mid = mitte_linie(art, W, H, rb)
        L = K.path_len(mid)
        n = max(5, int(L / max(rb * 1.1, 6.0)))
        pts = Z.entlang(mid, L / n, closed=False)
        for (x, y), (tx, ty) in pts:
            nx, ny = -ty, tx
            linien.append(([(x - nx * rb * 0.62, y - ny * rb * 0.62), (x + nx * rb * 0.62, y + ny * rb * 0.62)], False))
    elif stil == "holz":
        for f in (0.33, 0.66):
            p = form(art, W + 2 * rb * f, H + rb * f)
            linien.append((p[1:] + [p[0]], False))
    return linien


def standplatte(cfg, name: str, B: float, Tf: float, slots: Sequence[Tuple[str, float, float, float, float]],
                vorne_rund: bool = True) -> Part:
    """Stufe/Fensterbank: B breit, Tf tief (y 0 = hinten … Tf = vorne), Schlitze [(fid, x, y, länge, pos)]."""
    T = cfg.T
    r = min(Tf * 0.45, 8.0) if vorne_rund else 1.2
    pts = [(-B / 2, 0.0), (B / 2, 0.0)] + K.arc(B / 2 - r, Tf - r, r, 0, math.pi / 2, 10) + \
        K.arc(-B / 2 + r, Tf - r, r, math.pi / 2, math.pi, 10)
    part = Part(name, oriented(pts, True))
    for fid, x, y, L, pos in slots:
        Z.schlitz(part, fid, x, y, L, T, pos)
    return part


def tabbreite(cfg, verfuegbar: float, anteil: float = 0.2) -> float:
    return max(cfg.min_tab_width + 0.6, min(cfg.tab_factor * cfg.T, verfuegbar * anteil))


def text_gravur(part, text: str, cx: float, cy: float, max_w: float, max_h: float, max_cap: float = 8.0,
                was: str = "Der Text"):
    if not text.strip():
        return
    try:
        st, _ = Z.text_in_box(text, cx, cy, max_w, max_h, max_cap, 2.5, 0.08)
    except ValueError:
        raise ValueError(f"{was} „{text.replace('|', ' ')}“ passt nicht drauf – kürzer fassen oder größer machen")
    Z.gravur(part, [(s, False) for s in st], rand=0.8)


def oben_y(poly: Poly, x: float) -> float:
    """Höchster Punkt der Kontur über x."""
    ys = []
    n = len(poly)
    for i in range(n):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % n]
        if (x1 <= x < x2) or (x2 <= x < x1):
            ys.append(y1 + (x - x1) * (y2 - y1) / (x2 - x1))
    return max(ys) if ys else 0.0
