"""
Weihnachtsanhänger – ein Set klassischer Christbaumanhänger mit vielen Details.

Lebkuchenhaus mit Zuckerguss, Hirsch/Rentier mit Glöckchen-Halsband, Nikolausstiefel mit Pelzkrempe und
Stechpalme, Lebkuchenmann mit Zuckergussverzierung und Zuckerstange mit Schleife. Fenster, Herzen, Augen
und Sterne sind ausgeschnitten, Zuckerguss, Nähte und Streifen graviert. Auf Wunsch mit Namen.
"""
from __future__ import annotations

import math
import os
import sys
from typing import List

from steckwerk import Assembly, inset_polygon, oriented
from pakete import bibliothek, flag, integer, num, sel, txt

_here = os.path.dirname(os.path.abspath(__file__))


def _sub(name: str):
    import importlib.util
    path = os.path.join(_here, name + ".py")
    key = "swpaket_weihnacht_" + name
    mod = sys.modules.get(key)
    if mod is None or getattr(mod, "__file__", None) != path:
        spec = importlib.util.spec_from_file_location(key, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[key] = mod
        spec.loader.exec_module(mod)
    return mod


W = bibliothek("verzierungen").W
F = bibliothek("verzierungen").F
E, K = W.E, W.K
Figur = K.Figur

MOTIVE = [("alle", "alle (Set)"), ("lebkuchenhaus", "Lebkuchenhaus"), ("hirsch", "Hirsch/Rentier"),
          ("stiefel", "Nikolausstiefel"), ("lebkuchenmann", "Lebkuchenmann"), ("zuckerstange", "Zuckerstange")]

INFO = dict(
    label="Weihnachtsanhänger",
    group="Weihnachtsdeko",
    desc="Anhänger-Set: Lebkuchenhaus mit Zuckerguss, Hirsch, Nikolausstiefel, Lebkuchenmann und Zuckerstange – "
         "ausgeschnittene Fenster und Herzen, gravierte Verzierungen, auf Wunsch mit Namen.",
    params=[
        sel("motiv", "Motiv", MOTIVE, "alle"),
        num("groesse", "Höhe", 90, 60, 180),
        txt("text", "Name", "", maxlen=20, help="optional, wird eingraviert", section="Schrift und Beschriftung"),
        flag("verzierung", "Zuckerguss und Verzierungen gravieren", True),
        integer("anzahl", "Anzahl je Motiv", 1, 1, 8),
    ],
)

UEBERSETZUNG = {"en": {
    "Weihnachtsanhänger": "Christmas ornaments", "Weihnachtsdeko": "Christmas decor",
    "Anhänger-Set: Lebkuchenhaus mit Zuckerguss, Hirsch, Nikolausstiefel, Lebkuchenmann und Zuckerstange – "
    "ausgeschnittene Fenster und Herzen, gravierte Verzierungen, auf Wunsch mit Namen.":
        "Ornament set: gingerbread house with icing, stag, Santa boot, gingerbread man and candy cane – cut-out "
        "windows and hearts, engraved decorations, optionally with a name.",
    "Motiv": "Motif", "alle (Set)": "all (set)", "Lebkuchenhaus": "Gingerbread house", "Hirsch/Rentier": "Stag/reindeer",
    "Nikolausstiefel": "Santa boot", "Lebkuchenmann": "Gingerbread man", "Zuckerstange": "Candy cane",
    "Höhe": "Height", "Name": "Name", "optional, wird eingraviert": "optional, will be engraved",
    "Schrift und Beschriftung": "Font and lettering",
    "Zuckerguss und Verzierungen gravieren": "Engrave icing and decorations", "Anzahl je Motiv": "Count per motif",
    "Aufhängen: Band oder Kordel durch die Öse ziehen; die Zuckerstange hängt mit ihrem Haken am Zweig.":
        "To hang: thread a ribbon or cord through the loop; the candy cane hooks onto a branch.",
    "Tipp: Mit Acrylfarbe bemalen – die Gravur zeigt, wo Zuckerguss, Streifen und Pelz hingehören.":
        "Tip: Paint with acrylics – the engraving shows where icing, stripes and fur go.",
}}


# --------------------------------------------------------------------------------------------------
# Motive: jedes liefert (Figur in mm, Öse (x, y) oder None, Gravur-Funktion, Namensfeld)
# Gravur-Funktion: g(cv, dk) zeichnet mit der Leinwand cv.
# --------------------------------------------------------------------------------------------------

def _lebkuchenhaus(S: float, wm: float):
    f = Figur()
    u = S
    f.add(K.rect(-0.34 * u, 0, 0.68 * u, 0.57 * u))
    roof = [(-0.49 * u, 0.48 * u), (0.0, 0.95 * u), (0.49 * u, 0.48 * u)]
    th = 0.075 * u
    f.add(K.stroke(roof, 2 * th, 2 * th, "rund"))
    f.add([(-0.40 * u, 0.50 * u), (0, 0.92 * u), (0.40 * u, 0.50 * u)])
    # Schnee-/Zuckergusskante: Bögen auf dem Dach
    for side in (-1, 1):
        a = (side * 0.49 * u, 0.48 * u)
        b = (0.0, 0.95 * u)
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        n = int(L / (0.06 * u))
        nx, ny = (b[1] - a[1]) / L, -(b[0] - a[0]) / L
        if side < 0:
            nx, ny = -nx, -ny
        for k in range(1, n):
            t = k / n
            x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
            f.add(K.circle(x + nx * th * 0.95, y + ny * th * 0.95, 0.028 * u, 14))
        # Zuckergusstropfen unter der Traufe (hängen an der Dachkante)
        for k in range(3):
            x = side * (0.385 + 0.045 * k) * u
            k_d = (0.95 - 0.48) / 0.49
            yb = 0.48 * u + (0.49 * u - abs(x)) * k_d - th * math.sqrt(1 + k_d * k_d) + 0.012 * u
            f.add(K.chain([(x - 0.017 * u, yb + 0.02 * u)], K.arc(x, yb - 0.01 * u * (k % 2), 0.017 * u, math.pi, 2 * math.pi, 8),
                          [(x + 0.017 * u, yb + 0.02 * u)]))
    # Schornstein
    f.add(K.rect(0.17 * u, 0.62 * u, 0.12 * u, 0.30 * u), K.rect(0.15 * u, 0.89 * u, 0.16 * u, 0.045 * u))
    # Fenster mit Sprossen (Durchbrüche), Herz im Giebel
    m = max(wm, 0.03 * u)
    for cx in (-0.18 * u, 0.18 * u):
        x0, y0, ww, hh = cx - 0.075 * u, 0.25 * u, 0.15 * u, 0.15 * u
        f.cut(K.rect(x0, y0, ww, hh))
        f.add(K.rect(cx - m / 2, y0 - 1, m, hh + 2), K.rect(x0 - 1, y0 + hh / 2 - m / 2, ww + 2, m))
    from models._deko import heart
    f.cut(heart(0, 0.69 * u, 0.12 * u, 0.11 * u))
    oese = (0.0, 0.95 * u + th)

    def gravur(cv, dk):
        # Zuckerguss unter der Dachkante
        for side in (-1, 1):
            p = [(side * 0.40 * u, 0.535 * u), (0.0, 0.875 * u)]
            dk.styled_line(cv, p, "zuckerguss", 0.05 * u, side=-side, seed=3)
        # Fensterrahmen aus Zuckerguss
        for cx in (-0.18 * u, 0.18 * u):
            x0, y0, ww, hh = cx - 0.075 * u, 0.25 * u, 0.15 * u, 0.15 * u
            g = 0.018 * u
            cv.draw(K.rect(x0 - g, y0 - g, ww + 2 * g, hh + 2 * g), True)
            dk.styled_line(cv, [(x0 - 0.03 * u, y0 - 0.035 * u), (x0 + ww + 0.03 * u, y0 - 0.035 * u)],
                           "wellen", 0.03 * u, side=-1, seed=1)
        # Tür mit Bogen, Herz und Klinke
        dw, dh = 0.15 * u, 0.24 * u
        door = K.chain([(-dw / 2, 0.0), (-dw / 2, dh - dw / 2)], K.arc(0, dh - dw / 2, dw / 2, math.pi, 0, 16),
                       [(dw / 2, 0.0)])
        cv.draw(door)
        inner = [(x * 0.78, y * 0.9) for x, y in door]
        cv.draw(inner)
        cv.draw(heart(0, 0.15 * u, 0.05 * u, 0.045 * u), True)
        cv.draw(K.circle(0.045 * u, 0.09 * u, 0.008 * u + 0.3, 10), True)
        # Bonbons auf dem Dach und Wellenlinie am Sockel
        for k, (x, y) in enumerate([(-0.24, 0.62), (-0.10, 0.73), (0.06, 0.81), (-0.30, 0.55), (0.30, 0.55),
                                    (0.10, 0.62), (-0.02, 0.62)]):
            r = (0.022 if k % 2 else 0.016) * u
            cv.draw(K.circle(x * u, y * u, r, 16), True)
            cv.draw(K.circle(x * u, y * u, r * 0.45, 10), True)
        dk.styled_line(cv, [(-0.33 * u, 0.04 * u), (-0.10 * u, 0.04 * u)], "wellen", 0.03 * u, side=1, seed=2)
        dk.styled_line(cv, [(0.10 * u, 0.04 * u), (0.33 * u, 0.04 * u)], "wellen", 0.03 * u, side=1, seed=2)
    namensfeld = (-0.30 * u, 0.43 * u, 0.30 * u, 0.53 * u)
    return f, oese, gravur, namensfeld


def _hirsch(S: float, wm: float):
    h = S / 2.42
    f = Figur()
    f.merge(F.hirsch(h, wmin_mm=max(wm * 1.1, 0.0)))
    # Schneehügel unter den Hufen verbindet die Beine
    hill = K.chain([(-0.80 * h, 0.0)], K.bez((-0.75 * h, 0.12 * h), (-0.1 * h, 0.16 * h), (0.62 * h, 0.07 * h), 16),
                   [(0.62 * h, 0.07 * h), (0.70 * h, -0.07 * h), (-0.80 * h, -0.07 * h)])
    f.add(K.spline(hill, closed=True, n=6))
    # Sterne im Hügel
    for x in (-0.55, -0.05, 0.40):
        f.cut(K.star(x * h, -0.005 * h, 0.045 * h + 0.3, 0.02 * h + 0.15, 5))
    oese = (-0.10 * h, 1.0 * h)
    f.add(K.stroke([(-0.10 * h, 0.95 * h), (-0.10 * h, 1.04 * h)], max(wm * 1.3, 0.09 * h)))

    def gravur(cv, dk):
        cv.draw(K.circle(0.80 * h, 1.36 * h, 0.022 * h + 0.2, 12), True)              # Auge
        cv.draw(K.bez((0.86 * h, 1.27 * h), (0.89 * h, 1.25 * h), (0.91 * h, 1.27 * h), 6))   # Maul
        # Halsband mit Glöckchen
        band = K.bez((0.47 * h, 1.12 * h), (0.58 * h, 1.10 * h), (0.66 * h, 1.27 * h), 12)
        cv.draw(band)
        cv.draw([(x, y - 0.045 * h) for x, y in band])
        for t in (0.25, 0.55, 0.85):
            x, y = band[int(t * (len(band) - 1))]
            cv.draw(K.circle(x + 0.01 * h, y - 0.085 * h, 0.028 * h, 14), True)
        # Fell an Brust und Bauch
        for k in range(5):
            y = 0.95 * h - 0.06 * k * h
            x = 0.50 * h - 0.02 * k * h
            cv.draw([(x, y), (x - 0.04 * h, y - 0.03 * h), (x, y - 0.05 * h)])
        for k in range(6):
            x = -0.40 * h + 0.13 * k * h
            cv.draw([(x, 0.64 * h), (x + 0.04 * h, 0.61 * h), (x + 0.08 * h, 0.64 * h)])
        # Rückenlinie mit Tupfen (Rentierfell)
        for x, y in ((-0.35, 0.90), (-0.22, 0.88), (-0.08, 0.86), (0.05, 0.87), (-0.28, 0.80), (-0.12, 0.79)):
            cv.draw(K.circle(x * h, y * h, 0.018 * h + 0.2, 10), True)
        dk.styled_line(cv, [(-0.75 * h, 0.03 * h), (0.6 * h, 0.035 * h)], "wellen", 0.03 * h, side=1, seed=4)
    namensfeld = (-0.40 * h, 0.68 * h, 0.30 * h, 0.92 * h)
    return f, oese, gravur, namensfeld


def _blatt(cx, cy, s, a):
    """Stechpalmenblatt der Länge s: drei Zacken je Seite mit eingezogenen Bögen dazwischen."""
    tips = [(0.0, 0.0), (0.22, 0.20), (0.50, 0.24), (0.78, 0.17), (1.0, 0.0)]
    top = [tips[0]]
    for p0, p1 in zip(tips, tips[1:]):
        c = ((p0[0] + p1[0]) / 2, 0.45 * (p0[1] + p1[1]) / 2)
        top += K.bez(p0, c, p1, 8)[1:]
    pts = top + [(x, -y) for x, y in reversed(top[1:-1])]
    ca, sa = math.cos(a), math.sin(a)
    return [(cx + (x * ca - y * sa) * s, cy + (x * sa + y * ca) * s) for x, y in pts]


def _stechpalme(f: Figur, cx, cy, s, ang):
    """Zwei gezackte Stechpalmenblätter und drei Beeren (Länge eines Blatts = s)."""
    for a in (ang + 0.5, ang - 0.5):
        f.add(_blatt(cx, cy, s, a))
    for dx, dy in ((-0.05, -0.03), (0.08, 0.07), (-0.03, 0.12)):
        f.add(K.circle(cx + dx * s, cy + dy * s, 0.09 * s, 14))


def _stiefel(S: float, wm: float):
    u = S
    f = Figur()
    shaft = [(-0.26, 0.72), (-0.27, 0.40), (-0.28, 0.16), (-0.25, 0.05), (-0.17, 0.0), (0.12, 0.0), (0.30, 0.01),
             (0.42, 0.05), (0.47, 0.13), (0.45, 0.20), (0.40, 0.21), (0.37, 0.16), (0.30, 0.20), (0.18, 0.26),
             (0.11, 0.33), (0.10, 0.50), (0.12, 0.72)]
    f.add(K.spline([(x * u, y * u) for x, y in shaft], closed=True, n=8))
    # Krempe mit flauschigem Rand
    from models._deko import rounded_rect
    cx0, cy0, cx1, cy1 = -0.31 * u, 0.68 * u, 0.16 * u, 0.87 * u
    f.add(rounded_rect(cx0, cy0, cx1, cy1, 0.04 * u))
    for k in range(9):
        x = cx0 + (cx1 - cx0) * (k + 0.5) / 9
        f.add(K.circle(x, cy0 + 0.005 * u, 0.03 * u, 14), K.circle(x, cy1 - 0.005 * u, 0.03 * u, 14))
    # Bommel am Zehenende, Stechpalme an der Krempe
    f.add(K.circle(0.43 * u, 0.20 * u, 0.04 * u, 18))
    _stechpalme(f, 0.12 * u, 0.79 * u, 0.24 * u, -0.15)
    # Durchbrüche: Stern im Schaft, kleine Sterne
    f.cut(K.star(-0.09 * u, 0.42 * u, 0.09 * u, 0.04 * u, 5))
    f.cut(K.star(-0.17 * u, 0.24 * u, 0.035 * u + 0.4, 0.016 * u + 0.2, 5, 1.2))
    f.cut(K.star(0.02 * u, 0.23 * u, 0.03 * u + 0.4, 0.014 * u + 0.2, 5, 0.3))
    oese = (-0.24 * u, cy1 + 0.03 * u + 2.0)
    f.add(K.stroke([(-0.24 * u, cy1 - 1.0), (-0.24 * u, oese[1] + 1.0)], max(wm * 1.6, 0.035 * u)))

    def gravur(cv, dk):
        # Ferse und Kappe abgesetzt
        cv.draw(K.bez((-0.27 * u, 0.15 * u), (-0.14 * u, 0.16 * u), (-0.13 * u, 0.0), 12))
        cv.draw(K.bez((0.30 * u, 0.012 * u), (0.26 * u, 0.12 * u), (0.36 * u, 0.17 * u), 12))
        # Ziernaht entlang des Schafts
        seam = [(x * u, y * u) for x, y in [(-0.22, 0.66), (-0.23, 0.30), (-0.20, 0.10), (-0.10, 0.06),
                                            (0.20, 0.06), (0.33, 0.10)]]
        dk.styled_line(cv, K.spline(seam, n=8), "gestrichelt", 0.02 * u, side=1)
        # Flausch auf der Krempe
        r = cv.rng
        for k in range(26):
            x = r.uniform(cx0 + 0.03 * u, cx1 - 0.05 * u)
            y = r.uniform(cy0 + 0.04 * u, cy1 - 0.04 * u)
            rr = r.uniform(0.006, 0.012) * u
            pts = K.circle(x, y, rr, 8)
            if cv.fits(pts):
                cv.draw(pts, True)
        # Blattadern
        # Blattadern
        for a in (-0.15 + 0.5, -0.15 - 0.5):
            cv.draw([(0.12 * u + math.cos(a) * 0.04 * u, 0.79 * u + math.sin(a) * 0.04 * u),
                     (0.12 * u + math.cos(a) * 0.2 * u, 0.79 * u + math.sin(a) * 0.2 * u)])
        # Schneeflöckchen auf dem Schaft
        for x, y in ((-0.18, 0.56), (0.02, 0.60), (0.02, 0.34)):
            for k in range(3):
                a = k * math.pi / 3
                d = 0.025 * u
                cv.draw([(x * u - d * math.cos(a), y * u - d * math.sin(a)), (x * u + d * math.cos(a), y * u + d * math.sin(a))])
    namensfeld = (cx0 + 0.02 * u, cy0 + 0.035 * u, 0.05 * u, cy1 - 0.035 * u)
    return f, oese, gravur, namensfeld


def _lebkuchenmann(S: float, wm: float):
    u = S
    f = Figur()
    f.add(K.circle(0, 0.81 * u, 0.165 * u, 60))
    body = [(-0.19, 0.64), (-0.21, 0.45), (-0.17, 0.28), (0.0, 0.25), (0.17, 0.28), (0.21, 0.45), (0.19, 0.64),
            (0.0, 0.67)]
    f.add(K.spline([(x * u, y * u) for x, y in body], closed=True, n=8))
    for s in (-1, 1):
        f.add(K.stroke([(s * 0.12 * u, 0.58 * u), (s * 0.30 * u, 0.60 * u), (s * 0.40 * u, 0.66 * u)], 0.17 * u, 0.15 * u))
        f.add(K.stroke([(s * 0.09 * u, 0.36 * u), (s * 0.17 * u, 0.18 * u), (s * 0.22 * u, 0.075 * u)], 0.18 * u, 0.17 * u))
        f.add(K.circle(s * 0.40 * u, 0.66 * u, 0.075 * u, 40), K.circle(s * 0.22 * u, 0.075 * u, 0.085 * u, 40))
    # Augen als Durchbrüche
    for s in (-1, 1):
        f.cut(K.circle(s * 0.06 * u, 0.85 * u, max(0.024 * u, 1.1), 16))
    oese = (0.0, 0.975 * u)

    def gravur(cv, dk):
        cv.draw(K.arc(0, 0.82 * u, 0.08 * u, math.radians(205), math.radians(335), 14))      # Lächeln
        for s in (-1, 1):
            cv.draw(K.circle(s * 0.105 * u, 0.775 * u, 0.018 * u, 12), True)              # Bäckchen
            # Zuckerguss an Handgelenken und Knöcheln
            x0 = s * 0.33 * u
            cv.draw([(x0 + s * 0.0, 0.69 * u + k) for k in (0.0,)] + [(x0 - s * 0.03 * u, 0.55 * u)])
            wz = [(x0 + s * 0.02 * u - s * 0.006 * u * (i % 2), 0.70 * u - i * 0.022 * u) for i in range(8)]
            cv.draw([(x + s * 0.035 * u * ((i % 2) - 0.5), y) for i, (x, y) in enumerate(wz)])
            ank = [(s * 0.13 * u + i * s * 0.028 * u, 0.15 * u + 0.012 * u * (i % 2)) for i in range(7)]
            cv.draw(ank)
        # Fliege
        bx, by = 0.0, 0.625 * u
        cv.draw([(bx, by), (bx - 0.06 * u, by + 0.03 * u), (bx - 0.06 * u, by - 0.03 * u)], True)
        cv.draw([(bx, by), (bx + 0.06 * u, by + 0.03 * u), (bx + 0.06 * u, by - 0.03 * u)], True)
        # Knöpfe
        for y in (0.55, 0.47, 0.39):
            cv.draw(K.circle(0, y * u, 0.022 * u, 14), True)
        # Zuckergusswellen am Rand von Kopf und Bauch
        head = K.circle(0, 0.81 * u, 0.125 * u, 60)
        cv.draw(K.chain(*[[(0 + (0.125 * u + 0.012 * u * math.sin(9 * a)) * math.cos(a),
                            0.81 * u + (0.125 * u + 0.012 * u * math.sin(9 * a)) * math.sin(a))]
                          for a in [math.radians(20 + 140 * i / 40) for i in range(41)]]))
        del head
    namensfeld = (-0.15 * u, 0.30 * u, 0.15 * u, 0.36 * u)
    return f, oese, gravur, namensfeld


def _zuckerstange(S: float, wm: float):
    u = S
    w = 0.14 * u
    r = 0.15 * u
    path = K.chain([(0.0, 0.0 + w / 2), (0.0, 0.80 * u)], K.arc(-r, 0.80 * u, r, 0.0, math.pi, 28),
                   [(-2 * r, 0.80 * u), (-2 * r, 0.70 * u)])
    f = Figur()
    f.add(K.stroke(path, w, w, "rund"))
    # Schleife: zwei Schlaufen (Tropfenform mit Durchbruch), Knoten, Bänder mit Schwalbenschwanz
    bx, by = 0.0, 0.66 * u
    for sg in (-1, 1):
        loop = K.spline([(bx, by), (bx + sg * 0.08 * u, by + 0.075 * u), (bx + sg * 0.19 * u, by + 0.07 * u),
                         (bx + sg * 0.20 * u, by + 0.0), (bx + sg * 0.12 * u, by - 0.02 * u)], closed=True, n=8)
        f.add(loop)
        f.cut(K.spline([(bx + sg * 0.065 * u, by + 0.02 * u), (bx + sg * 0.10 * u, by + 0.045 * u),
                        (bx + sg * 0.16 * u, by + 0.042 * u), (bx + sg * 0.165 * u, by + 0.01 * u),
                        (bx + sg * 0.11 * u, by + 0.0)], closed=True, n=8))
        tail = [(bx + sg * 0.01 * u, by - 0.01 * u), (bx + sg * 0.10 * u, by - 0.09 * u), (bx + sg * 0.15 * u, by - 0.19 * u)]
        f.add(K.stroke(tail, 0.05 * u, 0.06 * u, "flach"))
        ex, ey = tail[-1]
        f.cut([(ex - 0.02 * u, ey - 0.01 * u), (ex + 0.02 * u, ey - 0.01 * u), (ex, ey + 0.025 * u)])
    f.add(K.ellipse(bx, by + 0.01 * u, 0.04 * u, 0.045 * u, 0.0, 18))
    _stechpalme(f, 0.04 * u, 0.30 * u, 0.19 * u, 0.35)
    oese = None

    def gravur(cv, dk):
        # Streifen: Paare schräger Linien quer über die Stange
        for i, ((x, y), (tx, ty)) in enumerate(W.entlang(path, 0.075 * u, closed=False)):
            if i % 2:
                continue
            a = math.radians(50)
            vx, vy = tx * math.cos(a) - ty * math.sin(a), tx * math.sin(a) + ty * math.cos(a)
            L = w
            for off in (0.0, 0.025 * u):
                c = (x + tx * off, y + ty * off)
                cv.draw([(c[0] - vx * L, c[1] - vy * L), (c[0] + vx * L, c[1] + vy * L)])
    namensfeld = (-0.045 * u, 0.06 * u, 0.045 * u, 0.50 * u)
    return f, oese, gravur, namensfeld


BAUER = dict(lebkuchenhaus=_lebkuchenhaus, hirsch=_hirsch, stiefel=_stiefel, lebkuchenmann=_lebkuchenmann,
             zuckerstange=_zuckerstange)


def _name(cv, dk, name: str, feld, senkrecht: bool):
    from models._font import fit_text
    x0, y0, x1, y1 = feld
    if senkrecht:                                          # entlang der Stange von unten nach oben
        st, cap = fit_text(name, 0.0, 0.0, y1 - y0, (x1 - x0), min_h=2.5, max_cap=x1 - x0)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        st = [[(cx - y, cy + x) for x, y in s] for s in st]
    else:
        st, cap = fit_text(name, (x0 + x1) / 2, (y0 + y1) / 2, x1 - x0, y1 - y0, min_h=2.5, max_cap=y1 - y0)
    if not all(cv.fits(s, closed=False) for s in st):
        return False
    for s in st:
        cv.part.add_engrave(s)
    xs = [p[0] for s in st for p in s]
    ys = [p[1] for s in st for p in s]
    cv.block_box((min(xs), min(ys), max(xs), max(ys)), 1.0)
    return True


def _anhaenger(cfg, tag: str, motiv: str, S: float, name: str, verzierung: bool, notes: List[str]):
    from models import _deko as dk
    wm = W.wmin(cfg)
    fig, oese, gravur, feld = BAUER[motiv](S, wm)
    frei = []
    if oese is not None:
        r_oe = max(3.4, 0.045 * S)
        c = (oese[0], oese[1] + r_oe - 1.4)
        fig.add(K.circle(c[0], c[1], r_oe, 40))
        frei.append(K.circle(c[0], c[1], r_oe - max(wm + 0.4, 1.6), 48))
    part = W.figur_teil(cfg, tag, fig, notes)
    for h in frei:                                         # Öse exakt als Kreis (nicht über das Raster)
        part.add_hole(oriented(h, False))
    cv = dk.Canvas(part, margin=0.7, seed=cfg.seed)
    if name.strip():
        try:
            ok = _name(cv, dk, name.strip(), feld, motiv == "zuckerstange")
        except ValueError:
            ok = False
        if not ok:
            raise ValueError(f"Der Name „{name}“ passt nicht auf {dict(MOTIVE)[motiv]} – kürzer fassen oder größer wählen")
    if verzierung:
        gravur(cv, dk)
    return part


def build(cfg, name: str = "weihnachtsanhaenger", motiv: str = "alle", groesse: float = 90.0, text: str = "",
          verzierung: bool = True, anzahl: int = 1):
    if motiv not in dict(MOTIVE):
        raise ValueError(f"Motiv: unbekannte Auswahl {motiv!r}")
    S = cfg.s(groesse)
    if S < 50:
        raise ValueError("Die Anhänger sind zu klein – mindestens 50 mm Höhe")
    from models._font import unsupported
    bad = unsupported(text or "")
    if bad:
        raise ValueError(f"Zeichen {''.join(bad)!r} gibt es in der Schrift nicht")
    asm = Assembly(name, params=dict(motiv=motiv, groesse=S, anzahl=anzahl))
    notes: List[str] = []
    motive = [m for m, _ in MOTIVE if m != "alle"] if motiv == "alle" else [motiv]
    for m in motive:
        for i in range(int(anzahl)):
            tag = m + (f"_{i + 1}" if anzahl > 1 else "")
            asm.parts.append(_anhaenger(cfg, tag, m, S, text or "", verzierung, notes))
    for t in dict.fromkeys(notes):
        asm.notes.append(t)
    asm.notes.append("Aufhängen: Band oder Kordel durch die Öse ziehen; die Zuckerstange hängt mit ihrem Haken am Zweig.")
    if verzierung:
        asm.notes.append("Tipp: Mit Acrylfarbe bemalen – die Gravur zeigt, wo Zuckerguss, Streifen und Pelz hingehören.")
    return asm
