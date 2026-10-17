#!/usr/bin/env python3
"""
motive_bauen.py – zeichnet die eingebauten Motive als Vektor-SVG und legt sie in ./motive ab.

  python3 packaging/motive_bauen.py                 alle Motive neu erzeugen (motive/*.json)
  python3 packaging/motive_bauen.py katze stern     nur diese
  python3 packaging/motive_bauen.py --ziel DIR      in einen anderen Ordner schreiben (zum Prüfen)
  python3 packaging/motive_bauen.py --svg DIR       zusätzlich die SVG-Quellen ablegen (z. B. für Inkscape)

Gezeichnet wird in einem 200×200-Feld, y nach unten (wie in SVG):
  schwarz gefüllt   Material bzw. Umriss des Motivs
  weiß gefüllt      Innenformen (beim Ausschneiden fallen sie heraus, bei Gravur und Silhouette sichtbar)
  schwarzer Strich  Gravurlinien für Details (nur beim Gravieren und bei der Silhouette)

Regeln für saubere Laserteile: Innenformen und Stege mindestens 6 Einheiten (3 % der Motivgröße) breit,
jedes Motiv eine zusammenhängende Fläche. Umgewandelt wird mit dem Importer der Engine (motive.svg_to_motif),
danach werden die Konturen leicht vereinfacht.

Nur Python-Standardbibliothek.
"""
from __future__ import annotations

import argparse
import math
import os
import sys
from typing import Callable, Dict, List, Sequence, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import motive as mt  # noqa: E402

Pt = Tuple[float, float]
TOLERANZ = 0.0012          # Vereinfachung, bezogen auf die längere Seite (1.0)


# --- Zeichenhilfen ---------------------------------------------------------------------------------

def _f(v: float) -> str:
    return f"{v:.2f}".rstrip("0").rstrip(".")


def pts(points: Sequence[Pt]) -> str:
    return " ".join(f"{_f(x)},{_f(y)}" for x, y in points)


def poly(points: Sequence[Pt], fill: str = "#000") -> str:
    return f'<polygon points="{pts(points)}" fill="{fill}"/>'


def path(d: str, fill: str = "#000", transform: str = "") -> str:
    t = f' transform="{transform}"' if transform else ""
    return f'<path d="{d}" fill="{fill}"{t}/>'


def loch(d: str, transform: str = "") -> str:
    return path(d, "#fff", transform)


def kreis(cx: float, cy: float, r: float, fill: str = "#000") -> str:
    return f'<circle cx="{_f(cx)}" cy="{_f(cy)}" r="{_f(r)}" fill="{fill}"/>'


def ellipse(cx: float, cy: float, rx: float, ry: float, rot: float = 0.0, fill: str = "#000") -> str:
    t = f' transform="rotate({_f(rot)} {_f(cx)} {_f(cy)})"' if rot else ""
    return f'<ellipse cx="{_f(cx)}" cy="{_f(cy)}" rx="{_f(rx)}" ry="{_f(ry)}" fill="{fill}"{t}/>'


def linie(d: str) -> str:
    return f'<path d="{d}" fill="none" stroke="#000" stroke-width="1.6"/>'


def kapsel(x1: float, y1: float, x2: float, y2: float, r: float, fill: str = "#000") -> str:
    """Abgerundeter Balken zwischen zwei Punkten (wie ein dicker Strich mit runden Enden)."""
    a = math.atan2(y2 - y1, x2 - x1)
    nx, ny = -math.sin(a) * r, math.cos(a) * r
    body = poly([(x1 + nx, y1 + ny), (x2 + nx, y2 + ny), (x2 - nx, y2 - ny), (x1 - nx, y1 - ny)], fill)
    return body + kreis(x1, y1, r, fill) + kreis(x2, y2, r, fill)


def stern_pts(cx: float, cy: float, R: float, r: float, n: int = 5, rot: float = -90.0) -> List[Pt]:
    out = []
    for i in range(2 * n):
        rad = R if i % 2 == 0 else r
        a = math.radians(rot + i * 180.0 / n)
        out.append((cx + rad * math.cos(a), cy + rad * math.sin(a)))
    return out


def stechpalme(cx: float, cy: float, laenge: float, breite: float, winkel: float, fill: str = "#000") -> str:
    """Stechpalmenblatt: spitzes Blatt mit drei Zacken je Seite, Mitte (cx, cy), Winkel in Grad."""
    a = math.radians(winkel)
    ca, sa = math.cos(a), math.sin(a)
    rand: List[Pt] = []
    n = 60
    for seite in (1, -1):
        for i in range(n + 1):
            t = i / n if seite == 1 else 1 - i / n
            w = breite / 2 * math.sin(math.pi * t) ** 0.8 * (1 - 0.32 * math.sin(3 * math.pi * t) ** 2)
            u, v = (t - 0.5) * laenge, seite * w
            rand.append((cx + u * ca - v * sa, cy + u * sa + v * ca))
    return poly(rand, fill)


HERZ_D = ("M100 178 C60 145 12 112 12 66 C12 36 34 16 60 16 C78 16 92 27 100 42 "
          "C108 27 122 16 140 16 C166 16 188 36 188 66 C188 112 140 145 100 178 Z")


def herz(cx: float, cy: float, s: float, fill: str = "#000") -> str:
    """Herz mit Mitte (cx, cy); s = 1 entspricht 176 Einheiten Breite."""
    return path(HERZ_D, fill, f"translate({_f(cx)} {_f(cy)}) scale({_f(s)}) translate(-100 -97)")


def svg(*teile: str) -> str:
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="200" height="200">\n  '
            + "\n  ".join(teile) + "\n</svg>\n")


# --- Motive ----------------------------------------------------------------------------------------

def stern() -> str:
    """Facettierter Stern: kräftige Grundform, Grate als Gravur (wirkt plastisch)."""
    cx, cy = 100, 106
    p = stern_pts(cx, cy, 96, 41)
    grate = [linie(f"M{_f(cx)} {_f(cy)} L{_f(x)} {_f(y)}") for x, y in p]
    return svg(poly(p), *grate)


def herz_motiv() -> str:
    """Herz im Scherenschnitt-Stil: kleines Herz, zwei Blätter und Punkte als Innenformen."""
    teile = [path(HERZ_D)]
    teile.append(herz(100, 92, 0.26, "#fff"))
    teile.append(ellipse(58, 76, 8, 21, -38, "#fff"))
    teile.append(ellipse(142, 76, 8, 21, 38, "#fff"))
    for x, y in ((100, 136), (78, 120), (122, 120)):
        teile.append(kreis(x, y, 5.5, "#fff"))
    teile.append(linie("M100 160 C68 134 26 106 26 68 C26 44 44 30 62 30 C78 30 90 40 100 54 "
                       "C110 40 122 30 138 30 C156 30 174 44 174 68 C174 106 132 134 100 160 Z"))
    return svg(*teile)


def baum() -> str:
    """Tanne mit hängenden Astebenen, Kugeln als Innenformen und Girlanden als Gravur."""
    teile = []
    ebenen = [(30, 72, 30, 3), (54, 102, 46, 4), (82, 134, 62, 5), (112, 166, 78, 6)]
    for top, b, w, n in ebenen:
        h = b - top
        d = f"M100 {top} C{100 + w * .3} {top + h * .35} {100 + w * .7} {b - h * .3} {100 + w} {b} "
        xs = [100 + w - 2 * w * k / n for k in range(n + 1)]
        for x0, x1 in zip(xs, xs[1:]):
            d += f"Q{_f((x0 + x1) / 2)} {_f(b + 10)} {_f(x1)} {b} "
        d += f"C{100 - w * .7} {b - h * .3} {100 - w * .3} {top + h * .35} 100 {top} Z"
        teile.append(path(d))
    teile.append(poly([(90, 160), (110, 160), (112, 186), (88, 186)]))
    teile.append(poly(stern_pts(100, 24, 17, 7.5)))
    for x, y in ((92, 62), (112, 88), (82, 96), (124, 120), (72, 126), (100, 116), (134, 152),
                 (66, 156), (100, 148)):
        teile.append(kreis(x, y, 5, "#fff"))
    teile.append(linie("M70 102 Q100 112 128 96"))
    teile.append(linie("M56 136 Q96 150 146 128"))
    teile.append(linie("M40 166 Q100 178 160 164"))
    return svg(*teile)


def engel() -> str:
    """Engel mit Heiligenschein, Federflügeln, gefalteten Ärmeln und Faltenwurf."""
    teile = []
    for k in (1, -1):
        def X(x: float) -> float:
            return 100 + k * (x - 100)
        teile.append(path(f"M{X(92)} 72 C{X(80)} 46 {X(52)} 30 {X(26)} 34 C{X(16)} 36 {X(10)} 44 {X(12)} 52 "
                          f"C{X(18)} 52 {X(22)} 56 {X(20)} 62 C{X(26)} 62 {X(30)} 66 {X(28)} 72 "
                          f"C{X(34)} 72 {X(38)} 76 {X(36)} 82 C{X(44)} 82 {X(48)} 86 {X(46)} 92 "
                          f"C{X(56)} 92 {X(62)} 98 {X(64)} 104 C{X(76)} 96 {X(86)} 86 {X(92)} 72 Z"))
        teile.append(ellipse(X(42), 50, 14, 3.6, 16 * k, "#fff"))
        teile.append(ellipse(X(56), 74, 12, 3.6, 36 * k, "#fff"))
    teile.append(path("M88 60 C80 92 64 140 44 178 Q57 188 72 179 Q86 188 100 179 Q114 188 128 179 "
                      "Q143 188 156 178 C136 140 120 92 112 60 Z"))
    for k in (1, -1):
        teile.append(path(f"M{100 + k * 10} 64 C{100 + k * 30} 76 {100 + k * 32} 98 {100 + k * 20} 110 "
                          f"L{100 + k * 2} 104 C{100 + k * 8} 92 {100 + k * 8} 78 {100 + k * 10} 64 Z"))
    teile.append(kreis(100, 104, 7))
    teile.append(kreis(100, 48, 16))
    teile.append(path("M82 52 C78 36 88 26 100 26 C112 26 122 36 118 52 C118 60 114 66 110 66 "
                      "L90 66 C86 66 82 60 82 52 Z"))
    teile.append(ellipse(100, 20, 22, 8))
    teile.append(ellipse(100, 20, 14, 3.4, 0, "#fff"))
    teile.append(linie("M90 50 Q94 53 98 50"))
    teile.append(linie("M102 50 Q106 53 110 50"))
    teile.append(linie("M95 58 Q100 61 105 58"))
    teile.append(linie("M86 40 Q92 32 100 32 Q108 32 114 40"))
    teile.append(linie("M90 112 Q100 116 110 112"))
    teile.append(linie("M94 118 Q88 148 78 176"))
    teile.append(linie("M106 118 Q112 148 122 176"))
    teile.append(linie("M100 120 L100 176"))
    return svg(*teile)


def fledermaus() -> str:
    """Fledermaus im Flug: gezackte Flughäute, Fingerknochen als Gravur."""
    teile = []
    for s in (1, -1):
        def X(x: float) -> float:
            return 100 + s * (x - 100)
        teile.append(path(f"M{X(92)} 96 C{X(76)} 74 {X(58)} 60 {X(40)} 60 C{X(26)} 62 {X(14)} 74 {X(6)} 92 "
                          f"Q{X(20)} 102 {X(26)} 120 Q{X(39)} 117 {X(50)} 128 Q{X(61)} 119 {X(72)} 124 "
                          f"Q{X(81)} 114 {X(92)} 114 Z"))
        for tx, ty in ((6, 92), (26, 120), (50, 128), (72, 124)):
            teile.append(linie(f"M{X(40)} 61 L{X(tx)} {ty}"))
        teile.append(linie(f"M{X(90)} 96 L{X(40)} 61"))
        teile.append(poly([(X(86), 76), (X(88), 54), (X(100), 68)]))
        teile.append(kreis(X(88.6), 55, 3.2))
        for tx, ty in ((6, 92), (26, 120), (50, 128), (72, 124)):
            teile.append(kreis(X(tx + (2 if tx < 30 else 0)), ty - 1.5, 3))
    teile.append(ellipse(100, 104, 13, 24))
    teile.append(kreis(100, 78, 14))
    teile.append(kreis(95, 128, 3.4))
    teile.append(kreis(105, 128, 3.4))
    teile.append(kreis(94, 76, 3.4, "#fff"))
    teile.append(kreis(106, 76, 3.4, "#fff"))
    teile.append(linie("M94 88 L97 92 L100 88 L103 92 L106 88"))
    teile.append(linie("M93 100 Q100 104 107 100"))
    teile.append(linie("M93 110 Q100 114 107 110"))
    return svg(*teile)


def geist() -> str:
    """Wehendes Gespenst mit erhobenen Armen und „Buh!“-Mund."""
    d = ("M100 16 C140 16 158 48 158 86 C158 94 170 90 184 76 C188 90 178 108 158 114 "
         "C160 140 166 160 178 176 Q162 170 152 182 Q140 168 126 183 Q113 169 100 183 Q87 169 74 183 "
         "Q62 168 48 178 C44 160 42 140 42 116 C24 112 12 96 16 80 C30 92 40 96 42 88 C42 48 60 16 100 16 Z")
    return svg(path(d),
               ellipse(81, 70, 9.5, 14, -8, "#fff"), ellipse(119, 70, 9.5, 14, 8, "#fff"),
               ellipse(100, 110, 11, 15, 0, "#fff"),
               linie("M70 50 Q80 44 90 50"), linie("M110 50 Q120 44 130 50"),
               linie("M64 138 Q74 152 68 168"), linie("M136 138 Q126 152 132 168"),
               linie("M100 134 Q96 152 100 170"))


def geschenk() -> str:
    """Geschenk mit großer Schleife, Band als Gravur und Punktemuster."""
    teile = [path("M32 94 L168 94 L168 180 Q168 186 162 186 L38 186 Q32 186 32 180 Z"),
             path("M22 72 L178 72 L178 92 Q178 98 172 98 L28 98 Q22 98 22 92 Z")]
    for s in (1, -1):
        X = lambda x, s=s: 100 + s * (x - 100)  # noqa: E731
        teile.append(path(f"M100 70 C{X(82)} 32 {X(36)} 26 {X(38)} 54 C{X(40)} 72 {X(76)} 76 100 70 Z"))
    teile.append(ellipse(100, 64, 15, 13))
    for s in (1, -1):
        teile.append(ellipse(100 + s * 36, 54, 12, 6.5, 22 * s, "#fff"))
    for x in (50, 70, 130, 150):
        for y in (112, 168):
            teile.append(kreis(x, y, 5, "#fff"))
    teile.append(kreis(60, 140, 5, "#fff"))
    teile.append(kreis(140, 140, 5, "#fff"))
    for x in (90, 110):
        teile.append(linie(f"M{x} 99 L{x} 185"))
        teile.append(linie(f"M{x} 74 L{x} 96"))
    teile.append(linie("M33 132 L89 132"))
    teile.append(linie("M111 132 L167 132"))
    teile.append(linie("M33 150 L89 150"))
    teile.append(linie("M111 150 L167 150"))
    return svg(*teile)


def glocke() -> str:
    """Glocke mit Krone, Klöppel, Zierband und Stechpalmenzweig."""
    teile = [path("M100 32 C128 32 140 54 142 82 C144 114 150 140 176 158 Q182 166 172 170 "
                  "L28 170 Q18 166 24 158 C50 140 56 114 58 82 C60 54 72 32 100 32 Z"),
             kreis(100, 26, 13), kreis(100, 26, 6, "#fff"),
             kreis(100, 178, 11)]
    teile.append(stechpalme(68, 36, 54, 22, 200))
    teile.append(stechpalme(132, 36, 54, 22, -20))
    for x, y in ((90, 42), (100, 48), (110, 42)):
        teile.append(kreis(x, y, 6))
    for i in range(7):
        teile.append(kreis(58 + i * 14, 150, 4.2, "#fff"))
    teile.append(linie("M46 138 Q100 148 154 138"))
    teile.append(linie("M38 160 Q100 168 162 160"))
    teile.append(linie("M76 62 Q68 100 62 128"))
    teile.append(linie("M84 60 Q78 92 74 116"))
    return svg(*teile)


def hexe() -> str:
    """Hexe auf dem Besen: wehender Umhang, Hut mit Knick, Reisigbesen."""
    teile = [kapsel(30, 128, 168, 98, 3.6)]
    teile.append(path("M46 116 C34 112 22 110 14 112 L16 140 C26 140 36 136 48 132 Z"))
    for ex, ey in ((6, 104), (4, 116), (4, 128), (8, 140), (16, 150)):
        teile.append(kapsel(40, 124, ex, ey, 3.6))
    teile.append(path("M78 112 C72 88 80 66 98 60 C112 56 122 66 120 84 C126 92 132 98 136 106 "
                      "L120 112 C116 102 112 98 108 96 C106 108 108 118 112 128 L96 130 Z"))
    teile.append(path("M96 64 C80 70 56 76 36 96 C50 92 52 100 44 108 C58 102 64 108 60 116 "
                      "C72 108 80 104 88 100 Z"))
    teile.append(kreis(104, 54, 10))
    teile.append(path("M110 52 C116 53 122 56 124 60 C120 62 115 61 110 60 Z"))
    teile.append(kreis(122, 59.5, 2.6))
    teile.append(path("M96 50 C90 58 80 64 72 64 C80 58 86 52 90 44 Z"))
    teile.append(kreis(73, 63, 3))
    for cx, cy in ((37, 96), (45, 107), (61, 115)):
        teile.append(kreis(cx, cy, 3.2))
    teile.append(poly([(58, 114), (90, 98), (82, 118), (66, 124)]))
    teile.append(ellipse(102, 45, 22, 4.5, -10))
    teile.append(path("M88 44 C88 30 84 16 74 8 C86 10 98 20 104 30 C108 36 112 40 114 42 Z"))
    teile.append(kreis(75, 9, 3.4))
    teile.append(path("M110 126 L122 124 C128 124 132 128 134 132 L112 134 Z"))
    for a, b in ((6, 108), (4, 124), (8, 138), (18, 146)):
        teile.append(linie(f"M44 126 L{a + 8} {b}"))
    teile.append(linie("M46 118 L50 136"))
    teile.append(linie("M86 76 Q92 92 92 112"))
    teile.append(linie("M100 40 L110 38"))
    return svg(*teile)


def hexenhut() -> str:
    """Hexenhut mit geknickter Spitze, Hutband mit Schnalle und Flicken."""
    teile = [path("M8 150 C30 170 170 172 192 150 C176 140 150 134 130 132 C122 108 112 74 112 50 "
                  "C114 36 124 28 142 30 C132 18 108 14 96 28 C86 40 82 70 76 100 C74 112 72 124 70 132 "
                  "C50 134 24 140 8 150 Z")]
    teile.append(path("M92 118 L110 118 L110 134 L92 134 Z", "#fff"))
    teile.append(linie("M72 116 Q100 122 126 116"))
    teile.append(linie("M70 134 Q100 140 130 134"))
    teile.append(linie("M86 114 L116 114 L116 138 L86 138 Z"))
    teile.append(poly(stern_pts(96, 94, 9, 4), "#fff"))
    teile.append(poly(stern_pts(104, 66, 6, 2.8), "#fff"))
    teile.append(linie("M98 40 Q104 34 112 34"))
    teile.append(linie("M30 152 Q100 164 170 152"))
    return svg(*teile)


def katze() -> str:
    """Sitzende Katze im Profil mit eingerolltem Schwanz, Halsband und Glöckchen."""
    teile = [path("M62 184 C40 184 34 160 42 132 C50 104 64 88 84 82 C86 66 82 54 86 42 L82 16 L100 32 "
                  "C106 30 110 30 116 32 L128 14 L128 40 C136 48 136 62 128 70 C122 74 118 76 118 82 "
                  "C126 98 130 122 128 150 C128 166 134 178 142 186 Z"),
             path("M58 176 C90 196 150 198 172 182 C188 172 188 152 174 146 C180 158 174 170 160 174 "
                  "C140 182 100 182 64 168 Z"),
             ellipse(115, 48, 6, 3.6, 12, "#fff"),
             kreis(106, 92, 4.6, "#fff"),
             linie("M86 80 Q102 90 120 82"),
             linie("M106 122 Q112 152 110 182"),
             linie("M58 150 Q74 128 92 148 Q98 168 90 182"),
             linie("M90 34 L96 40"),
             linie("M122 26 L122 36"),
             linie("M128 62 L120 64")]
    return svg(*teile)


def kerze() -> str:
    """Kerze mit Wachsläufern und Flamme, auf einem Halter mit Henkel und Stechpalme."""
    teile = [path("M80 94 Q100 100 120 94 L120 162 L80 162 Z"),
             ellipse(100, 94, 20, 5),
             ellipse(80, 112, 4, 11), ellipse(120, 126, 4, 13),
             path("M100 26 C114 46 118 58 112 68 C108 76 92 76 88 68 C82 58 86 46 100 26 Z"),
             poly([(97, 70), (103, 70), (103, 92), (97, 92)]),
             path("M100 46 C106 54 107 60 104 64 C102 67 98 67 96 64 C93 60 94 54 100 46 Z", "#fff"),
             path("M36 160 L164 160 Q172 160 170 168 Q152 184 100 184 Q48 184 30 168 Q28 160 36 160 Z"),
             kreis(172, 170, 14), kreis(172, 170, 7, "#fff"),
             stechpalme(44, 146, 46, 20, 175), stechpalme(52, 136, 40, 18, 215)]
    for x, y in ((62, 154), (55, 158), (64, 147), (57, 150)):
        teile.append(kreis(x, y, 5.5))
    teile.append(linie("M88 100 L88 152"))
    teile.append(linie("M112 102 Q114 124 112 150"))
    teile.append(linie("M82 96 Q100 102 118 96"))
    teile.append(linie("M46 174 Q100 182 154 174"))
    return svg(*teile)


def kuerbis() -> str:
    """Kürbislaterne mit Rippen, Stiel und Blatt; Gesicht als Innenformen."""
    teile = [ellipse(46, 122, 36, 52), ellipse(154, 122, 36, 52), ellipse(72, 120, 40, 58),
             ellipse(128, 120, 40, 58), ellipse(100, 118, 40, 62),
             path("M92 62 C90 50 94 38 104 28 L114 32 C106 42 104 52 106 62 Z"),
             path("M104 60 C118 42 140 36 154 46 C144 50 138 60 128 66 C118 70 108 68 104 60 Z")]
    teile.append(poly([(60, 110), (88, 110), (74, 86)], "#fff"))
    teile.append(poly([(112, 110), (140, 110), (126, 86)], "#fff"))
    teile.append(poly([(92, 132), (108, 132), (100, 120)], "#fff"))
    teile.append(path("M52 142 Q100 190 148 142 Q100 160 52 142 Z", "#fff"))
    teile.append(poly([(76, 140), (88, 140), (88, 158), (76, 156)]))
    teile.append(poly([(112, 140), (124, 140), (124, 156), (112, 158)]))
    teile.append(linie("M114 58 Q130 50 146 47"))
    for a, b in (("M74 64 Q62 74 58 88", "M58 156 Q64 168 74 174"),
                 ("M126 64 Q138 74 142 88", "M142 156 Q136 168 126 174")):
        teile.append(linie(a))
        teile.append(linie(b))
    teile.append(linie("M30 104 Q22 122 30 142"))
    teile.append(linie("M170 104 Q178 122 170 142"))
    return svg(*teile)


def lebkuchen() -> str:
    """Lebkuchenmann mit Zuckerguss-Wellen, Knöpfen und Fliege."""
    teile = [kreis(100, 42, 26), ellipse(100, 114, 36, 46), ellipse(100, 70, 16, 8),
             kapsel(56, 96, 144, 96, 15),
             kapsel(84, 136, 66, 176, 16), kapsel(116, 136, 134, 176, 16)]
    teile.append(kreis(90, 38, 4.5, "#fff"))
    teile.append(kreis(110, 38, 4.5, "#fff"))
    teile.append(path("M86 52 Q100 64 114 52 Q100 72 86 52 Z", "#fff"))
    teile.append(poly([(88, 72), (99, 78), (88, 84)], "#fff"))
    teile.append(poly([(112, 72), (101, 78), (112, 84)], "#fff"))
    for y in (100, 120, 140):
        teile.append(kreis(100, y, 5.5, "#fff"))
    teile.append(linie("M60 84 Q56 90 60 96 Q64 102 60 108"))
    teile.append(linie("M140 84 Q144 90 140 96 Q136 102 140 108"))
    teile.append(linie("M54 170 Q60 166 66 170 Q72 174 78 170"))
    teile.append(linie("M122 170 Q128 166 134 170 Q140 174 146 170"))
    teile.append(linie("M78 22 Q100 10 122 22"))
    return svg(*teile)


def mond() -> str:
    """Schlafender Mond mit Gesichtsprofil, Zipfelmütze und Stern."""
    teile = [kreis(96, 104, 82), kreis(134, 88, 70, "#fff"),
             path("M66 98 C70 102 78 108 76 114 C74 118 68 118 64 116 Z"),
             path("M64 124 C68 126 72 128 70 132 C68 134 64 134 62 133 Z")]
    teile.append(linie("M44 92 Q52 98 60 92"))
    teile.append(linie("M46 95 L44 99"))
    teile.append(linie("M52 97 L52 101"))
    teile.append(linie("M58 95 L60 99"))
    teile.append(linie("M38 116 Q44 120 50 116"))
    teile.append(poly(stern_pts(48, 150, 9, 4), "#fff"))
    teile.append(poly(stern_pts(70, 170, 6.5, 3), "#fff"))
    teile.append(linie("M24 74 Q20 104 30 132"))
    return svg(*teile)


def schneemann() -> str:
    """Schneemann mit Zylinder, wehendem Schal, Rübennase und Zweigarmen."""
    teile = [kreis(100, 150, 38), kreis(100, 100, 28), kreis(100, 60, 21),
             path("M72 38 Q72 34 76 34 L124 34 Q128 34 128 38 L128 42 L72 42 Z"),
             path("M82 36 L84 8 Q84 4 88 4 L112 4 Q116 4 116 8 L118 36 Z"),
             poly([(118, 58), (144, 62), (118, 66)]),
             path("M78 76 Q100 88 122 76 L124 86 Q100 98 76 86 Z"),
             path("M80 84 L68 124 L74 122 L72 130 L78 126 L80 132 L84 126 L88 128 L90 92 Z")]
    teile.append(kapsel(76, 98, 34, 72, 3.2))
    teile.append(kapsel(46, 80, 40, 64, 3.0))
    teile.append(kapsel(124, 98, 166, 78, 3.2))
    teile.append(kapsel(154, 84, 162, 66, 3.0))
    teile.append(path("M86 22 L114 22 L114 29 L86 29 Z", "#fff"))
    teile.append(kreis(93, 54, 4.2, "#fff"))
    teile.append(kreis(107, 54, 4.2, "#fff"))
    for y in (104, 120, 144, 164):
        teile.append(kreis(100, y, 4.6, "#fff"))
    teile.append(linie("M90 68 Q100 74 110 68"))
    teile.append(linie("M70 82 L76 86"))
    teile.append(linie("M84 100 L80 120"))
    return svg(*teile)


def stiefel() -> str:
    """Nikolausstiefel mit Fellkrempe, Aufhänger und Zuckerstange."""
    teile = [path("M58 40 L58 140 C58 166 72 182 100 184 L160 184 C178 184 186 174 184 162 C182 150 172 146 162 144 "
                  "L130 140 C126 140 124 136 124 130 L124 40 Z"),
             path("M48 22 Q48 16 54 16 L132 16 Q138 16 138 22 L138 48 Q131 56 124 48 Q117 56 110 48 Q103 56 96 48 "
                  "Q89 56 82 48 Q75 56 68 48 Q61 56 54 48 Q48 52 48 46 Z"),
             kreis(52, 16, 12), kreis(52, 16, 6, "#fff"),
             path("M118 16 L118 -2 C118 -16 136 -18 140 -6 C142 2 136 6 132 2 C132 -6 126 -6 126 0 L126 16 Z")]
    for i, x in enumerate(range(62, 132, 13)):
        teile.append(kreis(x, 28 if i % 2 == 0 else 38, 4.4, "#fff"))
    teile.append(herz(91, 100, 0.16, "#fff"))
    teile.append(linie("M64 60 L64 138 C64 160 76 176 100 178 L158 178"))
    teile.append(linie("M120 -2 L126 2"))
    teile.append(linie("M120 8 L126 12"))
    teile.append(linie("M152 150 C166 150 174 160 172 172"))
    return svg(*teile)


def totenkopf() -> str:
    """Totenkopf mit Wangenknochen, Zahnreihe und Rissen."""
    teile = [path("M100 12 C150 12 178 46 176 90 C175 110 166 122 156 128 L152 146 Q150 154 142 154 "
                  "L58 154 Q50 154 48 146 L44 128 C34 122 25 110 24 90 C22 46 50 12 100 12 Z"),
             path("M62 146 L138 146 L138 176 Q138 188 126 188 L74 188 Q62 188 62 176 Z")]
    teile.append(path("M52 94 C52 78 66 72 80 74 C94 76 98 88 94 100 C90 110 78 114 66 110 C56 106 52 100 52 94 Z",
                      "#fff"))
    teile.append(path("M148 94 C148 78 134 72 120 74 C106 76 102 88 106 100 C110 110 122 114 134 110 "
                      "C144 106 148 100 148 94 Z", "#fff"))
    teile.append(path("M100 116 C104 124 110 132 106 136 C104 138 100 136 100 134 C100 136 96 138 94 136 "
                      "C90 132 96 124 100 116 Z", "#fff"))
    for x in (70, 84, 98, 112, 126):
        teile.append(path(f"M{x} 150 L{x + 6} 150 L{x + 6} 172 Q{x + 3} 176 {x} 172 Z", "#fff"))
    teile.append(linie("M122 18 L116 32 L124 42 L118 56"))
    teile.append(linie("M46 120 Q56 126 66 124"))
    teile.append(linie("M154 120 Q144 126 134 124"))
    teile.append(linie("M76 64 Q86 60 94 64"))
    teile.append(linie("M106 64 Q114 60 124 64"))
    return svg(*teile)


def zapfen() -> str:
    """Tannenzapfen mit Schuppenkleid und Tannenzweig."""
    cx, cy, rx, ry = 100, 112, 48, 76
    umriss: List[Pt] = []
    n = 400
    for i in range(n):
        t = 2 * math.pi * i / n
        rows = 9
        bump = max(0.0, math.cos(rows * 2 * t)) ** 1.5
        k = 1 + 0.07 * bump
        sx, sy = math.cos(t), math.sin(t)
        y = cy + ry * sy * k
        x = cx + rx * sx * k * (0.82 + 0.18 * (1 - (y - (cy - ry)) / (2 * ry)))
        umriss.append((x, y))
    teile = [poly(umriss)]
    teile.append(kapsel(100, 46, 100, 28, 4))
    x0, y0, x1, y1 = 99, 31, 160, 14
    teile.append(kapsel(x0, y0, x1, y1, 3.2))
    dx, dy = x1 - x0, y1 - y0
    lang = math.hypot(dx, dy)
    ux, uy = dx / lang, dy / lang
    for i in range(2, 9):
        t = i / 9
        bx, by = x0 + dx * t, y0 + dy * t
        nl = 15 - 6 * t
        for seite in (1, -1):
            nx, ny = -uy * seite, ux * seite
            teile.append(kapsel(bx, by, bx + (nx * 0.8 + ux * 0.6) * nl, by + (ny * 0.8 + uy * 0.6) * nl, 2.4))
    row = 0
    y = 52
    while y < 180:
        half = rx * math.sqrt(max(0.0, 1 - ((y - cy) / ry) ** 2)) * 0.82 - 10
        x = cx - half + (10 if row % 2 else 0)
        while x + 20 <= cx + half:
            teile.append(linie(f"M{_f(x)} {_f(y)} Q{_f(x + 10)} {_f(y + 12)} {_f(x + 20)} {_f(y)}"))
            x += 20
        y += 14
        row += 1
    return svg(*teile)


MOTIVE: Dict[str, Tuple[str, Callable[[], str]]] = {
    "baum": ("Tannenbaum", baum),
    "engel": ("Engel", engel),
    "fledermaus": ("Fledermaus", fledermaus),
    "geist": ("Geist", geist),
    "geschenk": ("Geschenk", geschenk),
    "glocke": ("Glocke", glocke),
    "herz": ("Herz", herz_motiv),
    "hexe": ("Hexe", hexe),
    "hexenhut": ("Hexenhut", hexenhut),
    "katze": ("Katze", katze),
    "kerze": ("Kerze", kerze),
    "kuerbis": ("Kürbis", kuerbis),
    "lebkuchen": ("Lebkuchenmann", lebkuchen),
    "mond": ("Mond", mond),
    "schneemann": ("Schneemann", schneemann),
    "stern": ("Stern", stern),
    "stiefel": ("Nikolausstiefel", stiefel),
    "totenkopf": ("Totenkopf", totenkopf),
    "zapfen": ("Tannenzapfen", zapfen),
}


def _vereinfacht(m: dict) -> dict:
    """Konturen aus dem Raster-Importer ausdünnen (Form bleibt, Dateien werden klein)."""
    size = max(m.get("w", 1.0), m.get("h", 1.0)) or 1.0
    tol = TOLERANZ * size
    for fl in m["flaechen"]:
        fl["aussen"] = [list(p) for p in mt.simplify([tuple(p) for p in fl["aussen"]], tol)]
        fl["loecher"] = [[list(p) for p in mt.simplify([tuple(p) for p in h], tol)] for h in fl["loecher"]]
    m["linien"] = [[list(p) for p in mt.simplify([tuple(p) for p in li], tol, closed=False)] for li in m["linien"]]
    return m


def bauen(mid: str, ziel: str, svg_dir: str = "") -> dict:
    name, zeichnen = MOTIVE[mid]
    text = zeichnen()
    if svg_dir:
        os.makedirs(svg_dir, exist_ok=True)
        with open(os.path.join(svg_dir, mid + ".svg"), "w", encoding="utf-8") as fh:
            fh.write(text)
    m = _vereinfacht(mt.svg_to_motif(text.encode("utf-8")))
    if len(m["flaechen"]) != 1:
        raise ValueError(f"{mid}: {len(m['flaechen'])} getrennte Flächen – ein Motiv muss zusammenhängen")
    m = mt.normalize(m)
    m["name"] = name
    m["quelle"] = "eingebaut"
    os.makedirs(ziel, exist_ok=True)
    import json
    with open(os.path.join(ziel, mid + ".json"), "w", encoding="utf-8") as fh:
        json.dump(m, fh, ensure_ascii=False, separators=(",", ":"))
    return m


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Eingebaute Motive zeichnen")
    ap.add_argument("ids", nargs="*", help="nur diese Motive (Default: alle)")
    ap.add_argument("--ziel", default=mt.BUILTIN_DIR, help="Zielordner (Default: ./motive)")
    ap.add_argument("--svg", default="", help="SVG-Quellen zusätzlich hier ablegen")
    a = ap.parse_args(argv)
    ids = a.ids or sorted(MOTIVE)
    unbekannt = [i for i in ids if i not in MOTIVE]
    if unbekannt:
        raise SystemExit(f"Unbekannte Motive: {', '.join(unbekannt)}")
    fehler = 0
    for mid in ids:
        try:
            m = bauen(mid, a.ziel, a.svg)
        except ValueError as e:
            print(f"FEHLER {e}")
            fehler += 1
            continue
        fl = m["flaechen"][0]
        print(f"{mid:12s} {len(fl['aussen']):4d} Punkte außen · {len(fl['loecher']):2d} Innenformen · "
              f"{len(m['linien']):2d} Gravurlinien")
    return 1 if fehler else 0


if __name__ == "__main__":
    sys.exit(main())
