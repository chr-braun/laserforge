"""
_rahmen.py – gemeinsame Teile der Umrandungen: Rahmenform, verziertes Vorderteil, Rückwand, Sockel.
Nutzt die Bibliothek „Verzierungen“.
"""
from __future__ import annotations

import math
from typing import List, Optional, Sequence, Tuple

from steckwerk import Part, oriented, point_in_polygon, slot_feature
from pakete import bibliothek

Z = bibliothek("verzierungen")
K = Z.K
Point = Tuple[float, float]
Poly = List[Point]

STILE = [("schlicht", "schlicht mit Durchbrüchen"), ("filigran", "filigran (durchbrochenes Band)")]
FUELLUNGEN = [("mandala", "Rosetten: Mandala"), ("bluete", "Rosetten: Blüte"), ("stern", "Rosetten: Stern"),
              ("schneestern", "Schneesterne"), ("herzen", "Herzen"), ("ringe", "Ringe")]
ECKEN = [("keine", "keine"), ("rosetten", "Rosetten auf den Ecken")] + \
        [("foto_" + k, "Fotoecken: " + v) for k, v in Z.ECKEN]
ECKIGE = ("rechteck", "abgerundet", "achteck")


def _inside_all(poly: Poly, pts: Sequence[Point], y_min: float) -> bool:
    return all(point_in_polygon(p, poly) and p[1] >= y_min for p in pts)


def form_und_fenster(form: str, Wi: float, Hi: float, rand: float, flach: bool,
                     inhalt: Optional[Tuple[float, float]] = None, marge: float = 4.0):
    """Außenform und Fenster. Wi × Hi = Fenster; inhalt = (b, h) eines Fotos, das ganz hinter den Rahmen passen
    muss (für Ovale u. Ä. wird die Außenform dann größer). Liefert (aussen, fenster, y_schnitt) mit Unterkante
    bei y = 0; y_schnitt > 0 heißt: unten gerade abgeschnitten (zum Hinstellen)."""
    Wo, Ho = Wi + 2 * rand, Hi + 2 * rand
    for _ in range(60):
        aussen = Z.kartusche(Wo, Ho, form)
        cy = Ho / 2
        fenster = [(x, y + cy - Hi / 2) for x, y in Z.kartusche(Wi, Hi, form)]
        y_cut = 0.0
        if flach and form in ECKIGE:
            y_cut = 2.0                              # knapp über der Unterkante: Rahmen und Rückwand bündig
        elif flach:
            # unten gerade machen: Sehne mit mindestens 45 % der Breite
            for k in range(1, 400):
                y = Ho * k / 800
                try:
                    x0, x1 = Z.E.quer_x(aussen, y)
                except ValueError:
                    continue
                if x1 - x0 >= 0.45 * Wo:
                    y_cut = y
                    break
        need: List[Point] = []
        if inhalt:
            b, h = inhalt
            need = [(sx * (b / 2 + marge), cy + sy * (h / 2 + marge)) for sx in (-1, 1) for sy in (-1, 1)]
        fy0 = min(p[1] for p in fenster)
        ok = _inside_all(aussen, need, y_cut + 2.0) and fy0 - y_cut >= rand * 0.55
        if ok:
            return aussen, fenster, y_cut
        Wo += 2.0
        Ho += 2.0 * Ho / Wo
    raise ValueError("Für dieses Format findet sich keine passende Rahmenform – breiteren Rand wählen")


def mittellinie(aussen: Poly, fenster: Poly, n: int = 240) -> Poly:
    """Linie mitten im Rahmenband (zwischen Außenform und Fenster)."""
    cx = sum(p[0] for p in fenster) / len(fenster)
    cy = sum(p[1] for p in fenster) / len(fenster)
    out = []
    for i in range(n):
        a = 2 * math.pi * i / n
        d = (math.cos(a), math.sin(a))
        r_in = _strahl(fenster, (cx, cy), d)
        r_out = _strahl(aussen, (cx, cy), d)
        r = (r_in + r_out) / 2
        out.append((cx + d[0] * r, cy + d[1] * r))
    return out


def _strahl(poly: Poly, o: Point, d: Point, naechster: bool = False) -> float:
    best = math.inf if naechster else 0.0
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        ex, ey = b[0] - a[0], b[1] - a[1]
        den = d[0] * ey - d[1] * ex
        if abs(den) < 1e-12:
            continue
        t = ((a[0] - o[0]) * ey - (a[1] - o[1]) * ex) / den
        u = ((a[0] - o[0]) * d[1] - (a[1] - o[1]) * d[0]) / den
        if t > 0 and 0 <= u <= 1:
            best = min(best, t) if naechster else max(best, t)
    return best


def _einsetzen(poly: Poly, d: float) -> Poly:
    from steckwerk import offset_polygon
    return offset_polygon(oriented(poly, True), -d)


def vorderteil(cfg, name: str, aussen: Poly, fenster: Poly, y_cut: float, stil: str, fuellung: str,
               kante: str, ecken: str, durchbruch: str, form: str, notes: List[str]) -> Part:
    """Verziertes Vorderteil (Rahmen mit Fenster)."""
    w = Z.wmin(cfg)
    fig = Z.Figur().add(aussen)
    if kante != "keine":
        g = max(3.2 * w, min(9.0, _bandbreite(aussen, fenster) * 0.32))
        fig.merge(Z.kante(aussen, kante, g, w, ausser=(lambda p: p[1] < y_cut + g * 1.2) if y_cut > 0 else None))
    band = _bandbreite(aussen, fenster)
    mitte = mittellinie(aussen, fenster)
    if stil == "filigran":
        rw = max(1.6 * w, band * 0.16)
        innen_aussen = _einsetzen(aussen, rw)
        fenster_rand = _einsetzen(fenster, -rw)
        fig.cut(innen_aussen)                    # Band öffnen …
        fig.add(fenster_rand)                    # … inneren Rand behalten
        r = (band - 2 * rw) / 2 + rw * 0.55
        schritt = 2 * r * (0.92 if fuellung in ("herzen", "ringe") else 0.98)
        for (x, y), (tx, ty) in Z.entlang(mitte, schritt):
            a = math.atan2(ty, tx)
            if fuellung in ("mandala", "bluete", "stern", "schneestern"):
                fig.merge(Z.rosette(r, fuellung, 8, w).map(lambda p, x=x, y=y, a=a: (
                    x + p[0] * math.cos(a) - p[1] * math.sin(a), y + p[0] * math.sin(a) + p[1] * math.cos(a))))
                if fuellung != "mandala":            # spitze Blätter: Stege zu beiden Rändern
                    nx, ny = -math.sin(a), math.cos(a)
                    r0 = r * (0.3 if fuellung == "stern" else 0.55)
                    for s in (-1, 1):
                        L = min(r + rw * 1.2, _strahl(aussen, (x, y), (s * nx, s * ny), True) - rw * 0.35)
                        fig.add(_steg((x + s * nx * r0, y + s * ny * r0),
                                      (x + s * nx * L, y + s * ny * L), max(1.5 * w, r * 0.16)))
            elif fuellung == "herzen":
                fig.add(Z.herz(x, y - r * 0.05, 2.15 * r, rot=a))
                fig.cut(Z.herz(x, y - r * 0.02, 1.05 * r, rot=a))
            else:
                fig.add(K.circle(x, y, r))
                fig.cut(K.circle(x, y, max(r - 1.8 * w, r * 0.45)))
        fig.cut(fenster)
    else:
        fig.cut(fenster)
        if durchbruch != "keine":
            g = max(3 * w, band * 0.38)
            fig.merge(Z.durchbruch(mitte, durchbruch, g, ausser=lambda p: p[1] < y_cut + band * 0.5))
    if ecken == "rosetten" and form in ECKIGE:
        x0, y0 = min(p[0] for p in aussen), min(p[1] for p in aussen)
        x1, y1 = max(p[0] for p in aussen), max(p[1] for p in aussen)
        r = band * 0.72
        for cx, cy in ((x0 + band / 2, y0 + band / 2), (x1 - band / 2, y0 + band / 2),
                       (x0 + band / 2, y1 - band / 2), (x1 - band / 2, y1 - band / 2)):
            fig.add(K.circle(cx, cy, r * 0.98))
            fig.merge(Z.rosette(r, "mandala", 8, w).map(lambda p, cx=cx, cy=cy: (p[0] + cx, p[1] + cy)))
    elif ecken.startswith("foto_") and form in ("rechteck", "abgerundet"):
        fx0, fy0 = min(p[0] for p in fenster), min(p[1] for p in fenster)
        fx1, fy1 = max(p[0] for p in fenster), max(p[1] for p in fenster)
        g = min(fx1 - fx0, fy1 - fy0) * 0.26
        e = Z.ecke(g, ecken[5:], w)
        o = w                                    # Überlappung mit dem Rahmen
        fig.merge(e.map(lambda p: (fx0 - o + p[0], fy0 - o + p[1])))
        fig.merge(e.map(lambda p: (fx1 + o - p[0], fy0 - o + p[1])))
        fig.merge(e.map(lambda p: (fx0 - o + p[0], fy1 + o - p[1])))
        fig.merge(e.map(lambda p: (fx1 + o - p[0], fy1 + o - p[1])))
    if y_cut > 0:
        fig.cut(K.rect(-1e4, -1e4, 2e4, 1e4 + y_cut))
    teil = Z.figur_teil(cfg, name, fig, notes, unten_flach=False)
    return _nach_unten(teil, y_cut)


def _steg(a: Point, b: Point, breite: float) -> Poly:
    """Rechteckiger Steg von a nach b."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / L * breite / 2, dx / L * breite / 2
    return [(a[0] + nx, a[1] + ny), (b[0] + nx, b[1] + ny), (b[0] - nx, b[1] - ny), (a[0] - nx, a[1] - ny)]


def _bandbreite(aussen: Poly, fenster: Poly) -> float:
    ax0, ay0 = min(p[0] for p in aussen), min(p[1] for p in aussen)
    ax1, ay1 = max(p[0] for p in aussen), max(p[1] for p in aussen)
    fx0, fy0 = min(p[0] for p in fenster), min(p[1] for p in fenster)
    fx1, fy1 = max(p[0] for p in fenster), max(p[1] for p in fenster)
    return max(4.0, min(fx0 - ax0, ax1 - fx1, ay1 - fy1))


def _nach_unten(part: Part, y_cut: float) -> Part:
    """Teil so verschieben, dass die (gerade) Unterkante auf y = 0 liegt."""
    if not y_cut:
        return part
    f = lambda pts: [(x, y - y_cut) for x, y in pts]
    p = part.transformed(f)
    p.outline = [(x, 0.0 if abs(y) < 0.35 else y) for x, y in p.outline]
    return p


def platte(cfg, name: str, aussen: Poly, y_cut: float, einzug: float, notes: List[str],
           ausschnitt: Optional[Poly] = None) -> Part:
    """Ebene, um einzug kleinere Platte (Zwischenrahmen oder Rückwand); ausschnitt wird herausgeschnitten."""
    fig = Z.Figur().add(_einsetzen(aussen, einzug))
    if ausschnitt:
        fig.cut(ausschnitt)
    if y_cut > 0:
        fig.cut(K.rect(-1e4, -1e4, 2e4, 1e4 + y_cut))
    return _nach_unten(Z.figur_teil(cfg, name, fig, notes, unten_flach=False), y_cut)


def fuss_x(part: Part, tw: float, anteil: float = 0.27) -> List[float]:
    """x-Positionen der zwei Steckzapfen auf der geraden Standfläche (y = 0)."""
    xs = [p[0] for p in part.outline if abs(p[1]) < 0.05]
    W = max(p[0] for p in part.outline) - min(p[0] for p in part.outline)
    if len(xs) < 2:
        raise ValueError(f"{part.name}: keine gerade Standfläche für den Sockel")
    m, h = (min(xs) + max(xs)) / 2, (max(xs) - min(xs)) / 2
    d = min(W * anteil, h - tw / 2 - 2.0)
    if d < tw:
        if h - tw / 2 - 2.0 < 0:
            raise ValueError(f"{part.name}: Für den Steckfuß ist die Standfläche zu schmal – größer wählen")
        return [m]                                   # schmale Standfläche: ein Zapfen in der Mitte
    return [m - d, m + d]


def gerade_unten(part: Part) -> Part:
    """Unterkante exakt auf y = 0 legen (für Steckzapfen)."""
    y0 = min(p[1] for p in part.outline)
    p = part.transformed(lambda pts: [(x, y - y0) for x, y in pts])
    out = [(x, 0.0 if y < 0.3 else y) for x, y in p.outline]
    n = len(out)
    out = [q for i, q in enumerate(out) if not (q[1] == 0.0 and out[i - 1][1] == 0.0 and out[(i + 1) % n][1] == 0.0)]
    p.outline = oriented(out, True)
    return p


def sockel(cfg, name: str, breite: float, tiefe: float, xs: Sequence[float], tw: float, y_schlitz: float,
           pos0: float, verzierung: str = "keine") -> Part:
    """Standplatte mit Schlitzen für die Zapfen der Rückwand (Schlitze entlang x)."""
    from models import _deko as dk
    T = cfg.T
    part = Part(name, oriented(dk.rounded_rect(-breite / 2, -tiefe / 2, breite / 2, tiefe / 2, min(6.0, tiefe / 4)), True))
    for k, x in enumerate(xs):
        feat, hole = slot_feature(f"schlitz{k}", x - tw / 2, y_schlitz - T / 2, tw, T, True, pos0 + k)
        part.holes.append(hole)
        part.features.append(feat)
    if verzierung != "keine":
        linien = []
        r = 2.4
        x = -breite / 2 + 5
        while x < breite / 2 - 5:
            linien.append((K.circle(x, tiefe / 2 - 4.5, 1.0, 10), True))
            linien.append((K.circle(x, -tiefe / 2 + 4.5, 1.0, 10), True))
            x += r * 2.5
        Z.gravur(part, linien, rand=1.2)
    return part


def schluesselloch(cx: float, cy: float, r: float = 4.0, b: float = 3.4, L: float = 9.0) -> Poly:
    """Schlüsselloch zum Aufhängen an einem Nagel: Kreis oben, Schlitz nach unten."""
    a0 = math.atan2(-math.sqrt(r * r - (b / 2) ** 2), b / 2)
    a1 = math.pi - a0 if a0 < 0 else a0
    pts = K.arc(cx, cy, r, a0, a0 + (2 * math.pi - 2 * abs(math.pi / 2 + a0)), 28)
    return pts + [(cx - b / 2, cy - L), (cx + b / 2, cy - L)]
