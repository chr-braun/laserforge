"""
Hampelmann für Kinder – Körper, zwei Arme und zwei Beine als kräftige Einzelteile.

Alle Figuren sind in einem Raster von 100 Einheiten Höhe gezeichnet (Füße auf y = 0, Mitte x = 0) und
werden auf die gewünschte Höhe skaliert. Arme und Beine hängen hinter dem Körper an je einem Gelenkloch;
über dem Gelenk sitzt zur Mitte hin ein Hebel mit Fadenloch. Zieht man den Faden nach unten, fliegen
Arme und Beine nach außen und oben.
"""
from __future__ import annotations

import math
import os
import sys
from typing import Dict, List

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

FIGUREN = [("wichtel", "Wichtel"), ("weihnachtsmann", "Weihnachtsmann"), ("rentier", "Rentier"),
           ("schneemann", "Schneemann"), ("skelett", "Skelett")]
GRIFFE = [("kugel", "Kugel"), ("stern", "Stern"), ("herz", "Herz"), ("kein", "keiner")]

INFO = dict(
    label="Hampelmann",
    group="Bewegung",
    desc="Klassischer Hampelmann zum Ziehen: Wichtel, Weihnachtsmann, Rentier, Schneemann oder ein lustiges "
         "Skelett, kräftig genug für Kinderhände. Mit Gravurlinien zum Ausmalen und Zuggriff.",
    params=[
        sel("figur", "Figur", FIGUREN, "wichtel"),
        num("hoehe", "Höhe", 240, 150, 400, help="von der Mütze bis zu den Füßen, Arme und Beine hängend"),
        num("loch", "Gelenkloch", 3.5, 2, 6, step=0.5, help="für Musterbeutelklammern, Splinte oder Holznieten"),
        num("fadenloch", "Fadenloch", 2, 1.5, 4, step=0.5),
        flag("ausmalen", "Linien zum Ausmalen gravieren", True),
        sel("griff", "Zuggriff", GRIFFE, "stern", help="Anhänger unten an der Zugschnur"),
        flag("aufhaenger", "Aufhängeloch", True),
    ],
)

UEBERSETZUNG = {"en": {
    "Hampelmann": "Jumping jack", "Bewegung": "Motion",
    "Klassischer Hampelmann zum Ziehen: Wichtel, Weihnachtsmann, Rentier, Schneemann oder ein lustiges "
    "Skelett, kräftig genug für Kinderhände. Mit Gravurlinien zum Ausmalen und Zuggriff.":
        "Classic pull-string jumping jack: elf, Santa, reindeer, snowman or a funny skeleton, sturdy enough for "
        "children's hands. With engraved lines for colouring and a pull handle.",
    "Figur": "Figure", "Wichtel": "Elf", "Weihnachtsmann": "Santa", "Rentier": "Reindeer", "Schneemann": "Snowman",
    "Skelett": "Skeleton", "Höhe": "Height",
    "von der Mütze bis zu den Füßen, Arme und Beine hängend": "from the hat to the feet, arms and legs hanging",
    "Gelenkloch": "Joint hole", "für Musterbeutelklammern, Splinte oder Holznieten":
        "for paper fasteners, split pins or wooden rivets",
    "Fadenloch": "String hole", "Linien zum Ausmalen gravieren": "Engrave lines for colouring",
    "Zuggriff": "Pull handle", "Anhänger unten an der Zugschnur": "pendant at the end of the pull string",
    "Kugel": "Ball", "Stern": "Star", "Herz": "Heart", "keiner": "none", "Aufhängeloch": "Hanging hole",
}}


# --------------------------------------------------------------------------------------------------
# Figuren im 100er-Raster. Arme und Beine sind für die rechte Seite (x > 0) gezeichnet.
# --------------------------------------------------------------------------------------------------

def _augen(lin, y, dx=3.6, r=1.15):
    for s in (-1, 1):
        lin.append((B.kreis(s * dx, y, r, 14), True))
        lin.append((B.kreis(s * dx, y, r * 0.45, 8), True))


def _wichtel() -> Dict:
    k, kl = Figur(), []
    k.add([(-15, 76), (15, 76), (3.2, 96), (-3.2, 96)])                         # Zipfelmütze
    k.add(K.circle(0, 96.5, 4.6, 32))                                            # Bommel
    k.add(K.rect(-16.5, 72.5, 33, 6))                                            # Mützenrand
    k.add(K.ellipse(0, 67.5, 10.5, 8.5))                                         # Gesicht
    for s in (-1, 1):
        k.add(K.circle(s * 10.6, 68, 2.8, 20))                                   # Ohren
    k.add(K.spline([(-10.5, 67), (-9.5, 59), (-5.5, 53), (0, 50), (5.5, 53), (9.5, 59), (10.5, 67)],
                   closed=True, n=6))                                            # Bart
    k.add([(-15.5, 63), (15.5, 63), (16.5, 46), (17.5, 29), (-17.5, 29), (-16.5, 46)])   # Kittel
    kl += [([(-16, 78), (16, 78)], False), ([(-16, 73), (16, 73)], False)]
    for y in (83, 89):
        hw = 15 - (y - 76) * 0.6
        kl.append(([(-hw, y), (hw, y)], False))                                  # Mützenringel
    _augen(kl, 69.5)
    kl.append((B.kreis(0, 66, 2.3, 18), True))                                   # Nase
    kl.append((K.bez((-7, 60), (0, 55), (7, 60), 10), False))
    kl.append((K.bez((-4, 55.5), (0, 52.5), (4, 55.5), 8), False))
    kl += [([(-16.4, 44), (16.4, 44)], False), ([(-16.6, 39.5), (16.6, 39.5)], False),
           (K.rect(-3.2, 40.3, 6.4, 3), True)]
    for x in (-10, -3.4, 3.4, 10):                                              # Zackensaum
        kl.append(([(x - 3.3, 31), (x, 34.5), (x + 3.3, 31)], False))
    a, al = Figur(), []
    a.line([(12, 60), (15, 48), (17, 39.5)], 8.5, 7.5)
    a.add(K.ellipse(17.6, 35.2, 4.4, 5))
    a.add(K.circle(14.6, 37.4, 2.2, 18))
    al += [([(13.4, 41.6), (20.6, 40.6)], False)]
    b, bl = Figur(), []
    b.line([(6.5, 34), (7, 20), (7.5, 11)], 8.5, 8)
    b.add(K.spline([(3, 13), (12, 13), (12.5, 6.5), (17, 5.8), (20.5, 9.5), (20.6, 4), (17, 0), (3, 0)],
                   closed=True, n=6))                                            # Schnabelschuh
    bl += [([(3.2, 12.2), (11.8, 12.2)], False)]
    for y in (28, 22, 16):
        bl.append(([(3.2, y), (11, y - 0.4)], False))                            # Ringelstrumpf
    return dict(koerper=(k, kl), arm=(a, al), bein=(b, bl), S=(12, 60), H=(6.5, 34), auf=(0, 96.5))


def _weihnachtsmann() -> Dict:
    k, kl = Figur(), []
    k.add(K.spline([(-14, 76), (14, 76), (11, 86), (3, 93), (-7, 93), (-13.5, 89)], closed=True, n=6))
    k.add(K.circle(-14.5, 88.5, 4.6, 32))
    k.add(K.rect(-16.5, 72, 33, 6.5))
    k.add(K.ellipse(0, 66.5, 10, 8.5))
    k.add(K.spline([(-11.5, 68), (-12.5, 60), (-8.5, 52), (0, 47.5), (8.5, 52), (12.5, 60), (11.5, 68)],
                   closed=True, n=6))
    k.add(K.rect(-15.5, 46, 31, 17))
    k.add(K.ellipse(0, 41, 18, 15))
    kl += [([(-16, 72.6), (16, 72.6)], False), ([(-16, 77.6), (16, 77.6)], False)]
    _augen(kl, 69)
    kl.append((B.kreis(0, 65.5, 2.6, 18), True))
    for s in (-1, 1):
        kl.append((K.bez((0, 63), (s * 4, 61), (s * 8, 63.5), 10), False))       # Schnurrbart
        kl.append((K.bez((s * 8, 58), (s * 6, 54), (s * 2.5, 51.5), 8), False))  # Bartlocken
    kl += [([(-17.6, 38), (17.6, 38)], False), ([(-17.8, 43), (17.8, 43)], False),
           (K.rect(-4, 38.6, 8, 3.8), True), (K.rect(-2, 39.6, 4, 1.8), True)]
    for y in (32, 47.5):
        kl.append((B.kreis(0, y, 1.3, 14), True))
    kl.append(([(0, 29), (0, 36)], False))
    a, al = Figur(), []
    a.line([(12, 60), (16, 48), (18, 39.5)], 9, 8)
    a.add(K.circle(18.5, 34.5, 4.6, 32))
    a.add(K.circle(15.4, 37, 2.2, 18))
    al += [([(13.6, 42), (22.2, 40.4)], False), ([(13.2, 39.6), (22.4, 38)], False)]
    b, bl = Figur(), []
    b.line([(6.5, 34), (7, 17)], 9.5, 9)
    b.add(K.spline([(2, 17), (12, 17), (12.5, 7.5), (18.5, 6.5), (19.5, 1.5), (17, 0), (2, 0)], closed=True, n=6))
    bl += [([(2.2, 16.2), (11.8, 16.2)], False), ([(2.2, 13), (12, 13)], False)]
    return dict(koerper=(k, kl), arm=(a, al), bein=(b, bl), S=(12, 60), H=(6.5, 34), auf=(-14.5, 88.5))


def _rentier() -> Dict:
    k, kl = Figur(), []
    for s in (-1, 1):                                                             # Geweih
        k.line([(s * 4, 80), (s * 9, 89), (s * 11.5, 98)], 3.4, 2.8)
        k.line([(s * 7.6, 86.5), (s * 2.8, 94)], 2.8, 2.6)
        k.line([(s * 9.8, 91.5), (s * 16.5, 95.5)], 2.8, 2.6)
        k.add(K.ellipse(s * 11, 78, 5.2, 2.6, rot=s * 0.45))                     # Ohren
    k.add(K.ellipse(0, 75, 9, 9.5))
    k.add(K.ellipse(0, 66, 7, 6))
    k.add(K.rect(-5.5, 52, 11, 12))
    k.add(K.ellipse(0, 40, 13.5, 17))
    _augen(kl, 76, 3.8)
    kl.append((B.kreis(0, 67.5, 3, 20), True))
    kl.append((B.kreis(0, 67.5, 1.6, 12), True))
    kl.append((K.bez((-3.5, 63.2), (0, 61), (3.5, 63.2), 8), False))
    for s in (-1, 1):
        kl.append((K.ellipse(s * 11, 78, 3.2, 1.2, rot=s * 0.45, n=20), True))
    kl.append((K.bez((-5.4, 56.5), (0, 54.5), (5.4, 56.5), 10), False))           # Halsband
    kl.append((B.kreis(0, 52.6, 1.9, 16), True))                                  # Glöckchen
    kl.append((K.ellipse(0, 38, 7.5, 10.5, n=36), True))                          # Bauch
    a, al = Figur(), []
    a.line([(9, 52), (12.5, 40), (14, 31)], 7.5, 6.5)
    a.add(K.rect(10.4, 25, 7.4, 6.5))
    al += [([(10.6, 30.4), (17.6, 30.4)], False), ([(14.1, 25.6), (14.1, 29.6)], False)]
    b, bl = Figur(), []
    b.line([(6, 32), (7.5, 18), (8, 8)], 8, 7)
    b.add(K.rect(4, 0, 8.4, 7.5))
    bl += [([(4.2, 7), (12.2, 7)], False), ([(8.2, 0.6), (8.2, 6)], False)]
    return dict(koerper=(k, kl), arm=(a, al), bein=(b, bl), S=(9, 52), H=(6, 32), auf=(0, 81))


def _schneemann() -> Dict:
    k, kl = Figur(), []
    k.add(K.rect(-8, 79, 16, 16))                                                # Zylinder
    k.add(K.rect(-13.5, 77.5, 27, 3.8))
    k.add(K.circle(0, 69, 10, 48))
    k.add(K.circle(0, 41, 17.5, 64))
    k.line([(-9.5, 59.5), (9.5, 59.5)], 5.5)                                     # Schal
    k.line([(5.5, 59), (9.5, 49.5)], 5, 4.5)
    kl += [([(-7.6, 83), (7.6, 83)], False), ([(-7.6, 86.5), (7.6, 86.5)], False)]
    _augen(kl, 72, 3.6, 1.3)
    kl.append(([(0, 69.6), (8.5, 68.3), (0, 67)], True))                         # Rübennase
    for i in range(5):
        a = math.radians(215 + i * 27.5)
        kl.append((B.kreis(6 * math.cos(a), 67 + 4.2 * math.sin(a) + 1.2, 0.75, 10), True))
    for y in (48, 41, 34):
        kl.append((B.kreis(0, y, 1.7, 16), True))
    kl += [([(-9, 58), (9, 58)], False), ([(-9, 61), (9, 61)], False), ([(7.2, 52.5), (10.2, 53.6)], False)]
    a, al = Figur(), []
    a.line([(11, 53), (15.5, 44), (19, 36)], 5, 4)
    a.line([(15.8, 43.6), (20.8, 46.2)], 3.2, 2.8)                               # Zweig
    a.add(K.circle(19.6, 33, 4, 28))                                             # Fäustling
    a.add(K.circle(16.8, 35.2, 2, 16))
    b, bl = Figur(), []
    b.line([(7, 30), (8, 12)], 8, 7.5)
    b.add(K.spline([(3, 13), (13, 13), (13.5, 5), (17, 2.5), (16, 0), (3, 0)], closed=True, n=6))
    bl += [([(3.2, 12.2), (12.8, 12.2)], False), ([(3.2, 8.5), (13, 8.5)], False)]
    return dict(koerper=(k, kl), arm=(a, al), bein=(b, bl), S=(11, 53), H=(7, 30), auf=(0, 90))


def _skelett() -> Dict:
    k, kl = Figur(), []
    k.add(K.spline([(0, 88), (8, 86), (11, 79), (10, 72), (7, 67.5), (-7, 67.5), (-10, 72), (-11, 79), (-8, 86)],
                   closed=True, n=6))                                            # Schädel
    k.add(K.rect(-6, 62.5, 12, 7))                                               # Kiefer
    for s in (-1, 1):
        k.cut(K.ellipse(s * 4.2, 76.5, 3.2, 3.6))                                 # Augenhöhlen
    k.cut([(0, 73), (1.8, 69.6), (-1.8, 69.6)])                                  # Nase
    k.add(K.rect(-2.8, 28, 5.6, 36))                                             # Wirbelsäule
    k.add(K.ellipse(0, 51.5, 12.5, 9.5))                                         # Brustkorb
    for y in (56, 51.5, 47):
        for s in (-1, 1):
            k.cut(K.stroke(K.bez((s * 4.6, y + 0.4), (s * 9, y + 1.4), (s * 10, y - 1.8), 10), 2, 1.8))
    k.line([(-12, 58), (12, 58)], 4)                                             # Schultern
    k.add(K.spline([(-10, 36), (10, 36), (8.5, 29), (3, 25.5), (-3, 25.5), (-8.5, 29)], closed=True, n=6))
    for x in (-4, -2, 0, 2, 4):
        kl.append(([(x, 62.8), (x, 69)], False))                                  # Zähne
    kl.append(([(-6, 66), (6, 66)], False))
    for y in (40, 37.6):
        kl.append(([(-2.6, y), (2.6, y)], False))
    a, al = Figur(), []
    a.line([(11, 58), (13.5, 47), (15.5, 37)], 3.6, 3.2)
    for p in ((13.5, 47), (15.5, 37)):
        a.add(K.circle(p[0], p[1], 2.6, 20))
    a.add(K.circle(16, 33, 3.4, 24))                                              # Hand
    for dx, ln in ((-2.6, 4.2), (0, 5), (2.6, 4.2)):
        a.line([(16 + dx * 0.8, 31), (16 + dx, 31 - ln)], 1.9, 1.7)
    b, bl = Figur(), []
    b.line([(6, 32), (6.8, 19), (7.4, 7)], 4.2, 3.6)
    b.add(K.circle(6.8, 19, 3, 24))
    b.add(K.spline([(3, 6.5), (11, 6.5), (14.5, 3), (13.5, 0), (3, 0)], closed=True, n=6))
    return dict(koerper=(k, kl), arm=(a, al), bein=(b, bl), S=(11, 58), H=(6, 32), auf=(0, 84.5))


_BAU = dict(wichtel=_wichtel, weihnachtsmann=_weihnachtsmann, rentier=_rentier, schneemann=_schneemann,
            skelett=_skelett)


def _griff(form: str, r: float) -> Figur:
    f = Figur()
    if form == "stern":
        f.add(K.star(0, 0, r, r * 0.5, 5))
        f.add(K.circle(0, 0, r * 0.62, 32))
    elif form == "herz":
        f.add(K.spline([(0, -r), (r * 0.95, r * 0.05), (r * 0.75, r * 0.8), (0, r * 0.5), (-r * 0.75, r * 0.8),
                        (-r * 0.95, r * 0.05)], closed=True, n=8))
    else:
        f.add(K.circle(0, 0, r, 48))
    return f


def build(cfg, name: str = "hampelmann", figur: str = "wichtel", hoehe: float = 240.0, loch: float = 3.5,
          fadenloch: float = 2.0, ausmalen: bool = True, griff: str = "stern", aufhaenger: bool = True):
    from models import _deko as dk
    dk.check_choice("Figur", figur, FIGUREN)
    dk.check_choice("Zuggriff", griff, GRIFFE)
    H = cfg.s(hoehe)
    if not 150 <= H <= 400:
        raise ValueError("Hampelmann: Höhe muss zwischen 150 und 400 mm liegen")
    if not 2 <= loch <= 6:
        raise ValueError("Hampelmann: Gelenkloch muss zwischen 2 und 6 mm liegen")
    if not 1.5 <= fadenloch <= 4:
        raise ValueError("Hampelmann: Fadenloch muss zwischen 1,5 und 4 mm liegen")
    u = H / 100.0
    rg = B.ring(cfg)
    hebel = max(5.0 * u, loch / 2 + fadenloch / 2 + rg + 1.2)       # Abstand Gelenk → Fadenloch
    spec = _BAU[figur]()
    notes: List[str] = []
    asm = Assembly(name, params=dict(figur=figur, hoehe=H, loch=loch, fadenloch=fadenloch))
    sc = lambda pts: B.skaliert(pts, u)
    S, Hp = sc([spec["S"]])[0], sc([spec["H"]])[0]

    def gr(part, lines, mirror=False):
        if ausmalen:
            B.gravur(part, [((B.spiegel(sc(p)) if mirror else sc(p)), c) for p, c in lines], cfg.seed)

    # Körper
    kf, kl = spec["koerper"]
    kf = kf.map(lambda p: (p[0] * u, p[1] * u))
    lo = [(s * S[0], S[1], loch) for s in (-1, 1)] + [(s * Hp[0], Hp[1], loch) for s in (-1, 1)]
    if aufhaenger:
        ax, ay = sc([spec["auf"]])[0]
        lo.append((ax, ay, max(2.5, min(4.0, 0.9 * u + 1.0))))
    koerper = B.teil(f"{name}_koerper", kf, cfg, notes, lo)
    gr(koerper, kl)
    asm.parts.append(koerper)

    # Arme und Beine: rechts gezeichnet, links gespiegelt; Hebel mit Fadenloch zur Mitte hin
    seite = {1: "rechts", -1: "links"}
    for key, P, ang in (("arm", S, 37.0), ("bein", Hp, 37.0)):
        f0, l0 = spec[key]
        f0 = f0.map(lambda p: (p[0] * u, p[1] * u))
        a = math.radians(ang)
        q = (P[0] - hebel * math.sin(a), P[1] + hebel * math.cos(a))
        f0.line([P, q], 2 * (fadenloch / 2 + rg))
        f0.add(K.circle(P[0], P[1], loch / 2 + rg + 0.4, 40))
        for s in (1, -1):
            f = f0 if s == 1 else f0.map(lambda p: (-p[0], p[1]))
            px, qx = s * P[0], s * q[0]
            part = B.teil(f"{name}_{key}_{seite[s]}", f, cfg, notes, [(px, P[1], loch), (qx, q[1], fadenloch)])
            gr(part, l0, mirror=(s == -1))
            asm.parts.append(part)

    if griff != "kein":
        r = max(9.0, min(16.0, 5.5 * u))
        gp = B.teil(f"{name}_griff", _griff(griff, r).map(lambda p: (p[0], p[1] - r - 5)), cfg, notes,
                    [(0.0, -5 - r + 0.55 * r, max(2.5, fadenloch + 0.5))])
        asm.parts.append(gp)

    for t in dict.fromkeys(notes):
        asm.notes.append(t)
    asm.notes.append("Gelenke: Arme und Beine liegen hinter dem Körper. Je eine Musterbeutelklammer, einen Splint "
                     "oder eine Holzniete durch die übereinanderliegenden Löcher stecken und nur so fest machen, "
                     "dass alles locker schwingt. Für kleine Kinder Holznieten statt Klammern nehmen.")
    asm.notes.append("Fäden: Arme und Beine hängen lassen. Hinten einen Faden straff zwischen den Fadenlöchern "
                     "der Arme spannen und einen zweiten zwischen denen der Beine. Die Zugschnur an beiden "
                     "Querfäden in der Mitte festknoten, unten den Zuggriff anbinden.")
    if aufhaenger:
        asm.notes.append("Aufhängen: Kordel durch das obere Loch.")
    if ausmalen:
        asm.notes.append("Ausmalen: Die gravierten Linien helfen beim Bemalen. Gut gehen Holzbeize, Acrylfarbe "
                         "oder Buntstifte; für Spielzeug speichelfesten Lack nehmen.")
    return asm
