"""
Wäscheleine – Paket „Wichtelzubehör“.

Zwei Pfosten mit Querholz stecken in einer langen Wiesen-Bodenplatte. Durch die Löcher im Querholz wird
ein Faden gespannt, an den die Mini-Wäsche geklebt oder mit Mini-Klammern gehängt wird.
"""
import math

from steckwerk import Assembly, Part, oriented
from pakete import bibliothek, integer, num, sel

Z = bibliothek("verzierungen")
K = Z.K

WAESCHE = ["hemd", "hose", "socke", "kleid", "muetze", "handtuch", "socke2", "unterhose"]

UEBERSETZUNG = {"en": {
    "Wäscheleine": "Clothesline", "Wichtelzubehör": "Elf accessories",
    "Wäscheleine mit zwei Pfosten auf einer Wiese und Mini-Wäsche: Hemd, Hose, Socken, Kleid, Zipfelmütze …":
        "Clothesline with two posts on a meadow and tiny laundry: shirt, trousers, socks, dress, pointy hat …",
    "Länge": "Length", "Höhe": "Height", "Wäschestücke": "Pieces of laundry", "Wäschegröße": "Laundry size",
    "Muster": "Pattern", "Punkte": "dots", "Streifen": "stripes", "Herzen": "hearts", "ohne": "plain",
    "Die beiden Pfosten mit den Zapfen in die Bodenplatte stecken.": "Push both posts with their tabs into the base plate.",
    "Einen Faden durch die Löcher der Querhölzer spannen und die Wäsche daran kleben.":
        "Stretch a thread through the holes of the cross bars and glue the laundry to it.",
}}

INFO = dict(
    label="Wäscheleine", group="Wichtelzubehör",
    desc="Wäscheleine mit zwei Pfosten auf einer Wiese und Mini-Wäsche: Hemd, Hose, Socken, Kleid, Zipfelmütze …",
    params=[
        num("laenge", "Länge", 120, 60, 300),
        num("hoehe", "Höhe", 60, 30, 150),
        integer("stuecke", "Wäschestücke", 6, 0, 8),
        num("groesse", "Wäschegröße", 18, 10, 40),
        sel("muster", "Muster", [("punkte", "Punkte"), ("streifen", "Streifen"), ("herzen", "Herzen"),
                                 ("ohne", "ohne")], "punkte"),
    ],
)


def build(cfg, name="waescheleine", laenge=120.0, hoehe=60.0, stuecke=6, groesse=18.0, muster="punkte"):
    T = cfg.T
    L, H, g = cfg.s(laenge), cfg.s(hoehe), cfg.s(groesse)
    w = Z.wmin(cfg)
    notes = []
    asm = Assembly(name, params=dict(laenge=L, hoehe=H, stuecke=int(stuecke)))
    bp = max(2.6 * T, 7.0)
    qb = max(bp * 2.6, 18.0)                   # Querholz-Länge
    qh = max(2 * w + 3.6, 7.0)                 # Querholz-Höhe (mit Loch)
    tw = max(cfg.min_tab_width + 0.6, bp * 0.6)
    xs = [-L / 2 + bp, L / 2 - bp]
    for k in range(2):
        fig = Z.Figur().add(K.rect(-bp / 2, 0, bp, H - qh / 2))
        fig.add(Z.abrunden([(-qb / 2, H - qh), (qb / 2, H - qh), (qb / 2, H), (-qb / 2, H)], qh * 0.45))
        fig.add([(-bp / 2, H - qh - bp * 0.8), (bp / 2, H - qh - bp * 0.8), (bp * 1.2, H - qh + 0.1),
                 (-bp * 1.2, H - qh + 0.1)])                     # Kopfband
        for x in (-qb / 2 + qh * 0.5, qb / 2 - qh * 0.5):
            fig.cut(K.circle(x, H - qh / 2, 1.25, 16))
        p = Z.figur_teil(cfg, f"pfosten{k + 1}", fig, notes, unten_flach=True)
        Z.zapfen_unten(p, 0.0, tw, T, "fuss", pos=10 + k)
        asm.parts.append(p)
    # Bodenplatte als Wiese mit gewelltem Rand
    ry = max(T * 3 + 8, 16.0)
    umr = []
    n = 120
    for i in range(n):
        a = 2 * math.pi * i / n
        rr = 1.0 + 0.04 * math.sin(a * 14)
        umr.append((math.cos(a) * (L / 2 + bp * 1.6) * rr, math.sin(a) * ry * rr))
    boden = Part("wiese", oriented(umr, True))
    for k, x in enumerate(xs):
        Z.schlitz(boden, f"pfosten{k + 1}", x, 0.0, tw, T, 10 + k)
    lin = []
    for i in range(int(L / 9)):
        x = -L / 2 + 9 * (i + 0.5)
        y = (ry * 0.45) * (1 if i % 2 else -1)
        lin.append(([(x - 1.6, y - 1.0), (x - 0.6, y + 1.6), (x, y - 0.6), (x + 0.6, y + 1.8), (x + 1.6, y - 1.0)], False))
    for x in (-L * 0.2, L * 0.15):                                # zwei Blümchen
        lin.append((K.circle(x, ry * 0.05, 1.2, 12), True))
        for j in range(5):
            a = 2 * math.pi * j / 5
            lin.append((K.circle(x + math.cos(a) * 2.4, ry * 0.05 + math.sin(a) * 2.4, 1.1, 10), True))
    Z.gravur(boden, lin, rand=1.0)
    asm.parts.append(boden)
    for k in range(2):
        asm.connect(f"pfosten{k + 1}:fuss", f"wiese:pfosten{k + 1}")
    asm.notes.append("Die beiden Pfosten mit den Zapfen in die Bodenplatte stecken.")
    for i in range(int(stuecke)):
        art = WAESCHE[i % len(WAESCHE)]
        pts = _stueck(art, g)
        fig = Z.Figur().add(pts)
        if art == "muetze":
            fig.add(K.circle(-g * 0.05, g * 0.08, g * 0.11, 20))           # Bommel
        teil = Z.figur_teil(cfg, f"{art.rstrip('2')}{i + 1}", fig, notes)
        _muster(teil, pts, art, muster, g)
        asm.parts.append(teil)
    if int(stuecke):
        asm.notes.append("Einen Faden durch die Löcher der Querhölzer spannen und die Wäsche daran kleben.")
    asm.notes += notes
    return asm


def _stueck(art, g):
    """Umriss eines Wäschestücks, Oberkante (an der Leine) bei y = g."""
    if art == "hemd":
        return [(-g * 0.5, g), (-g * 0.15, g), (0, g * 0.88), (g * 0.15, g), (g * 0.5, g), (g * 0.62, g * 0.62),
                (g * 0.38, g * 0.55), (g * 0.36, 0), (-g * 0.36, 0), (-g * 0.38, g * 0.55), (-g * 0.62, g * 0.62)]
    if art == "hose":
        return [(-g * 0.35, g), (g * 0.35, g), (g * 0.4, 0), (g * 0.1, 0), (0, g * 0.55), (-g * 0.1, 0), (-g * 0.4, 0)]
    if art in ("socke", "socke2"):
        s = 1 if art == "socke" else -1
        pts = [(-g * 0.15, g), (g * 0.15, g), (g * 0.15, g * 0.35)] + \
            [(g * 0.15 - g * 0.22 * (1 - math.cos(a)), g * 0.2 - g * 0.2 * math.sin(a)) for a in
             (math.pi * i / 10 for i in range(11))] + [(-g * 0.45, g * 0.2), (-g * 0.45, g * 0.05)]
        pts = [(x, y) for x, y in pts]
        pts = Z.abrunden([(-g * 0.15, g), (g * 0.15, g), (g * 0.15, g * 0.3), (-g * 0.25, 0), (-g * 0.55, 0),
                          (-g * 0.55, g * 0.22), (-g * 0.15, g * 0.38)], g * 0.07)
        return [(s * x, y) for x, y in pts]
    if art == "kleid":
        return [(-g * 0.18, g), (g * 0.18, g), (g * 0.26, g * 0.62), (g * 0.5, 0), (-g * 0.5, 0), (-g * 0.26, g * 0.62)]
    if art == "muetze":
        return [(-g * 0.38, g), (g * 0.38, g), (g * 0.36, g * 0.78)] + \
            K.bez((g * 0.36, g * 0.78), (g * 0.25, g * 0.25), (-g * 0.05, g * 0.08), 14)[1:] + \
            K.bez((-g * 0.05, g * 0.08), (-g * 0.2, g * 0.4), (-g * 0.36, g * 0.78), 14)[1:]
    if art == "unterhose":
        return [(-g * 0.4, g), (g * 0.4, g), (g * 0.4, g * 0.6), (g * 0.12, g * 0.3), (-g * 0.12, g * 0.3),
                (-g * 0.4, g * 0.6)]
    return Z.abrunden([(-g * 0.35, g), (g * 0.35, g), (g * 0.35, g * 0.1), (-g * 0.35, g * 0.1)], g * 0.05)   # handtuch


def _muster(teil, pts, art, muster, g):
    lin = [([(-g * 0.1, g - 0.8), (-g * 0.1, g - g * 0.18)], False), ([(g * 0.1, g - 0.8), (g * 0.1, g - g * 0.18)], False)]
    if art == "handtuch":
        lin += [([(-g * 0.33, g * y), (g * 0.33, g * y)], False) for y in (0.25, 0.3)]
    if muster == "punkte":
        for i in range(5):
            for j in range(5):
                lin.append((K.circle(-g * 0.4 + g * 0.2 * i + (g * 0.1 if j % 2 else 0), g * 0.12 + g * 0.18 * j, g * 0.03, 8), True))
    elif muster == "streifen":
        lin += [([(-g * 0.7, g * y), (g * 0.7, g * y)], False) for y in (0.3, 0.45, 0.6, 0.75)]
    elif muster == "herzen":
        lin.append((Z.herz(0, g * 0.5, g * 0.22), True))
    Z.gravur(teil, lin, rand=0.7)
