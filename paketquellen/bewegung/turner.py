"""
Turner – das alte Akrobaten-Spielzeug: zwei Stäbe, unten mit einem Quersteg drehbar verbunden, oben eine
verdrillte Schnur, an der die Figur mit den Händen hängt. Drückt man die Stäbe unten zusammen, gehen sie
oben auseinander, die Schnur spannt und entdrillt sich, und die Figur schlägt Purzelbäume.
"""
from __future__ import annotations

import os
import sys
from typing import List

from steckwerk import Assembly
from pakete import flag, num, sel

_here = os.path.dirname(os.path.abspath(__file__))


def _sub(name: str):
    import importlib.util
    path = os.path.join(_here, name + ".py")
    key = "swpaket_bewegung_" + name
    mod = sys.modules.get(key)
    if mod is None or getattr(mod, "__file__", None) != path:
        spec = importlib.util.spec_from_file_location(key, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[key] = mod
        spec.loader.exec_module(mod)
    return mod


B = _sub("_bw")
K = B.K
Figur = B.Figur

FIGUREN = [("affe", "Affe"), ("baer", "Bär"), ("wichtel", "Wichtel")]

INFO = dict(
    label="Turner",
    group="Bewegung",
    desc="Akrobat zum Zusammendrücken: Ein Affe, Bär oder Wichtel hängt an einer verdrillten Schnur zwischen "
         "zwei Stäben und schlägt Purzelbäume, wenn man die Stäbe unten zusammendrückt.",
    params=[
        sel("figur", "Figur", FIGUREN, "affe"),
        num("hoehe", "Figurhöhe", 80, 55, 140, help="mit hochgestreckten Armen"),
        num("loch", "Gelenkloch", 3.5, 2, 6, step=0.5, help="für Musterbeutelklammern, Splinte oder Holznieten"),
        num("schnurloch", "Schnurloch", 2.5, 1.5, 4, step=0.5),
        flag("ausmalen", "Linien zum Ausmalen gravieren", True),
    ],
)

UEBERSETZUNG = {"en": {
    "Turner": "Acrobat", "Bewegung": "Motion",
    "Akrobat zum Zusammendrücken: Ein Affe, Bär oder Wichtel hängt an einer verdrillten Schnur zwischen "
    "zwei Stäben und schlägt Purzelbäume, wenn man die Stäbe unten zusammendrückt.":
        "Squeeze acrobat: a monkey, bear or elf hangs on a twisted string between two sticks and turns "
        "somersaults when you squeeze the sticks together at the bottom.",
    "Figur": "Figure", "Affe": "Monkey", "Bär": "Bear", "Wichtel": "Elf", "Figurhöhe": "Figure height",
    "mit hochgestreckten Armen": "with arms stretched up", "Gelenkloch": "Joint hole",
    "für Musterbeutelklammern, Splinte oder Holznieten": "for paper fasteners, split pins or wooden rivets",
    "Schnurloch": "String hole", "Linien zum Ausmalen gravieren": "Engrave lines for colouring",
}}

# Hände im 100er-Raster: oben links und rechts
HAND = (16.0, 92.0)


def _arme_beine(f: Figur, w_arm: float, w_bein: float):
    for s in (-1, 1):
        f.line([(s * 9, 60), (s * 14, 76), (s * 16, 88)], w_arm, w_arm * 0.9)
        f.add(K.circle(s * HAND[0], HAND[1], 5.2, 28))
        f.line([(s * 6, 22), (s * 9, 12), (s * 10, 4)], w_bein, w_bein * 0.9)
        f.add(K.ellipse(s * 12, 3, 7, 3.4))


def _affe():
    f, l = Figur(), []
    _arme_beine(f, 6.5, 7.5)
    f.add(K.ellipse(0, 40, 14, 20))
    f.add(K.circle(0, 68, 13, 48))
    for s in (-1, 1):
        f.add(K.circle(s * 13.5, 70, 5, 24))
        l.append((B.kreis(s * 13.5, 70, 2.6, 14), True))
    f.line([(10, 26), (22, 22), (26, 32), (21, 38)], 3.4, 3)                     # Schwanz
    l.append((K.ellipse(0, 64, 8.5, 6, n=36), True))
    for s in (-1, 1):
        l.append((B.kreis(s * 4.5, 72, 1.8, 14), True))
        l.append((B.kreis(s * 4.5, 72, 0.7, 8), True))
        l.append((B.kreis(s * 1.6, 65.5, 0.6, 8), True))
    l.append((K.bez((-4, 61.5), (0, 59), (4, 61.5), 8), False))
    l.append((K.ellipse(0, 38, 8.5, 12, n=36), True))
    return f, l


def _baer():
    f, l = Figur(), []
    _arme_beine(f, 7.5, 8.5)
    f.add(K.ellipse(0, 40, 16, 21))
    f.add(K.circle(0, 68, 13.5, 48))
    for s in (-1, 1):
        f.add(K.circle(s * 10.5, 79, 5, 24))
        l.append((B.kreis(s * 10.5, 79, 2.4, 14), True))
        l.append((B.kreis(s * 4.8, 71, 1.6, 12), True))
    l.append((K.ellipse(0, 64, 6, 4.5, n=30), True))
    l.append(([(-1.8, 66), (1.8, 66), (0, 64.2)], True))
    l.append((K.bez((-3, 61.5), (0, 60), (3, 61.5), 8), False))
    l.append((K.ellipse(0, 37, 9.5, 12, n=36), True))
    return f, l


def _wichtel():
    f, l = Figur(), []
    _arme_beine(f, 7, 7.5)
    f.add([(-14, 22), (14, 22), (12, 54), (-12, 54)])
    f.add(K.spline([(-9, 63), (-8.5, 55), (0, 48), (8.5, 55), (9, 63)], closed=True, n=5))      # Bart
    f.add(K.ellipse(0, 63, 9, 7.5))
    f.add([(-11, 69), (11, 69), (2.5, 84), (-2.5, 84)])                          # Mütze
    f.add(K.circle(0, 85, 3.8, 24))
    f.add(K.rect(-12, 67.5, 24, 4.5))
    l += [([(-11.6, 71.6), (11.6, 71.6)], False), ([(-13.6, 38), (13.6, 38)], False),
          ([(-13.8, 34.5), (13.8, 34.5)], False), (K.rect(-2.5, 34.8, 5, 3), True)]
    for s in (-1, 1):
        l.append((B.kreis(s * 3.3, 65, 1, 10), True))
    l.append((B.kreis(0, 61.5, 1.9, 14), True))
    l.append((K.bez((-4.5, 56.5), (0, 53), (4.5, 56.5), 8), False))
    return f, l


_BAU = dict(affe=_affe, baer=_baer, wichtel=_wichtel)


def build(cfg, name: str = "turner", figur: str = "affe", hoehe: float = 80.0, loch: float = 3.5,
          schnurloch: float = 2.5, ausmalen: bool = True):
    from models import _deko as dk
    dk.check_choice("Figur", figur, FIGUREN)
    hf = cfg.s(hoehe)
    if not 55 <= hf <= 140:
        raise ValueError("Turner: Figurhöhe muss zwischen 55 und 140 mm liegen")
    if not 2 <= loch <= 6 or not 1.5 <= schnurloch <= 4:
        raise ValueError("Turner: Loch außerhalb des erlaubten Bereichs")
    u = hf / 100.0
    notes: List[str] = []
    asm = Assembly(name, params=dict(figur=figur, hoehe=hf))
    f, lines = _BAU[figur]()
    f = f.map(lambda p: (p[0] * u, p[1] * u))
    hx, hy = HAND[0] * u, HAND[1] * u
    fig = B.teil(f"{name}_{figur}", f, cfg, notes, [(-hx, hy, schnurloch), (hx, hy, schnurloch)])
    if ausmalen:
        B.gravur(fig, [([(x * u, y * u) for x, y in pts], c) for pts, c in lines], cfg.seed)
    asm.parts.append(fig)

    # Stäbe: oben Schnurloch, bei 30 % Gelenkloch für den Quersteg
    sw = max(14.0, 4 * cfg.T + 2)
    L = max(2.4 * hf, 170.0)
    spann = 2 * hx + 2 * max(8.0, 0.18 * hf)                 # Abstand der Stäbe oben (in Ruhe)
    z_g = 0.3 * L
    for s, seite in ((-1, "links"), (1, "rechts")):
        st = Figur()
        st.line([(0, 0), (0, L)], sw, sw)
        part = B.teil(f"{name}_stab_{seite}", st, cfg, notes, [(0, L - sw * 0.6, schnurloch), (0, z_g, loch)])
        if ausmalen:
            for k in range(4):
                y = 8 + k * 6
                part.add_engrave([(-sw / 2 + 2, y), (sw / 2 - 2, y + 2)])          # Griffrillen
        asm.parts.append(part)
    steg = Figur()
    steg.line([(-spann / 2, 0), (spann / 2, 0)], sw, sw)
    asm.parts.append(B.teil(f"{name}_steg", steg, cfg, notes, [(-spann / 2, 0, loch), (spann / 2, 0, loch)]))
    for t in dict.fromkeys(notes):
        asm.notes.append(t)
    asm.notes += [
        f"Zusammenbau: Den Quersteg mit zwei Musterbeutelklammern (oder Holznieten) an die unteren Gelenklöcher "
        f"der Stäbe schrauben, so dass die Stäbe oben etwa {spann:.0f} mm auseinanderstehen und sich leicht drehen.",
        "Schnur: Eine feste Schnur oben durch das Loch des linken Stabs knoten, durch beide Handlöcher der Figur "
        "führen und am rechten Stab festknoten. Die Figur zwischen den Stäben ein paarmal herumdrehen, bis die Schnur "
        "verdrillt ist.",
        "Spielen: Die Stäbe unten zusammendrücken – oben spannt die Schnur, die Figur turnt.",
    ]
    return asm
