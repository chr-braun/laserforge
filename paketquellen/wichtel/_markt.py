"""
_markt.py – gemeinsame Bausteine des Wichtelmarkts im Paket „Wichtel“: Wichtel-Maßstab für die Marktmodelle,
Lebkuchen-Formen mit Zuckerguss, Holzmaserung und Pflaster als Gravur.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Sequence, Tuple

from pakete import bibliothek

Z = bibliothek("verzierungen")
K = Z.K
WM = Z.WM
Point = Tuple[float, float]

# Maße als Vielfaches der Wichtelhöhe (bei 70 mm die Standardwerte der Modelle)
VERHAELTNIS: Dict[str, Dict[str, float]] = {
    "lebkuchenstand": dict(breite=1.1, hoehe=1.5, tiefe=0.42),
    "kreidetafel": dict(hoehe=0.95, breite=0.6),
    "backstube": dict(groesse=0.6),
    "wichtelpost": dict(hoehe=1.2),
    "gartenzaun": dict(laenge=1.6, hoehe=0.5),
    "werkbank": dict(laenge=0.9, hoehe=0.5, tiefe=0.38),
    "wegelaterne": dict(hoehe=1.35),
}
MIN_FAKTOR: Dict[str, float] = dict(lebkuchenstand=13.0, kreidetafel=9.0, wichtelpost=9.0, gartenzaun=10.0,
                                   werkbank=14.0, wegelaterne=11.0)


def mindestgroesse(modell: str, T: float) -> float:
    m = max(40.0, MIN_FAKTOR.get(modell, 0.0) * T)
    return float(math.ceil(m / 5.0 - 1e-9) * 5)


def mit_massstab(modell: str, params: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    keys = set(VERHAELTNIS[modell])
    out = WM.massstab_params()
    for p in params:
        if p["key"] in keys:
            p = dict(p, when=dict(p.get("when") or {}, massstab=["frei"]))
        out.append(p)
    return out


def mass(modell: str, groesse: float, params: List[Dict[str, Any]], cfg=None) -> Dict[str, float]:
    if cfg is not None:
        m = mindestgroesse(modell, cfg.T / cfg.scale)
        if float(groesse) < m - 1e-9:
            raise ValueError(f"Bei {cfg.T:g} mm Holz muss der Wichtel dafür mindestens {m:g} mm groß sein – "
                             f"Wichtelgröße erhöhen oder dünneres Holz nehmen")
    grenzen = {p["key"]: (p.get("min"), p.get("max")) for p in params}
    out = {}
    for key, f in VERHAELTNIS[modell].items():
        v = round(f * float(groesse), 1)
        lo, hi = grenzen.get(key, (None, None))
        out[key] = min(max(v, lo if lo is not None else v), hi if hi is not None else v)
    return out


EN = dict(WM.EN)
EN.update({"Wichtelmarkt": "Elf market"})


# --------------------------------------------------------------------------------------------------
# Hilfen
# --------------------------------------------------------------------------------------------------

def tabbreite(cfg, verfuegbar: float, anteil: float = 0.3) -> float:
    return max(cfg.min_tab_width + 0.6, min(cfg.tab_factor * cfg.T, verfuegbar * anteil))


def text_gravur(part, text: str, cx: float, cy: float, max_w: float, max_h: float, max_cap: float = 8.0,
                rand: float = 0.6):
    if not text.strip():
        return
    try:
        st, _ = Z.text_in_box(text, cx, cy, max_w, max_h, max_cap, 1.8, 0.08)
    except ValueError:
        raise ValueError(f"Der Text „{text.replace('|', ' ')}“ passt nicht drauf – kürzer fassen oder größer wählen")
    Z.gravur(part, [(s, False) for s in st], rand=rand)


def bretter(x0: float, y0: float, x1: float, y1: float, n: int, quer: bool = True, astloch: bool = True):
    """Fugen einer Bretterwand (quer = waagerechte Bretter) mit ein paar Astlöchern."""
    out = []
    for k in range(1, n):
        if quer:
            y = y0 + (y1 - y0) * k / n
            out.append(([(x0, y), (x1, y)], False))
        else:
            x = x0 + (x1 - x0) * k / n
            out.append(([(x, y0), (x, y1)], False))
    if astloch:
        for k, (u, v) in enumerate(((0.23, 0.5), (0.71, 0.5))):
            if quer:
                h = (y1 - y0) / n
                cx, cy = x0 + (x1 - x0) * u, y0 + h * (k * 2 % n + v)
                r = min(h * 0.18, 2.0)
            else:
                b = (x1 - x0) / n
                cx, cy = x0 + b * (k * 2 % n + v), y0 + (y1 - y0) * u
                r = min(b * 0.18, 2.0)
            if r > 0.6:
                out.append((K.ellipse(cx, cy, r * 1.4, r, n=16), True))
    return out


def pflaster(x0: float, y0: float, x1: float, y1: float, s: float):
    """Kopfsteinpflaster: versetzte, abgerundete Steine."""
    out = []
    reihe = 0
    y = y0 + s * 0.15
    while y + s * 0.7 < y1:
        x = x0 + (s * 0.5 if reihe % 2 else 0.0) + s * 0.1
        while x + s * 0.85 < x1:
            out.append((Z.abrunden(K.rect(x, y, s * 0.85, s * 0.62), s * 0.18, 3), True))
            x += s
        y += s * 0.75
        reihe += 1
    return out


def zuckerguss(poly: Sequence[Point], d: float, welle: float, schritt: float):
    """Gewellte Zuckergusslinie im Abstand d innerhalb einer (gegen den Uhrzeigersinn laufenden) Kontur."""
    from steckwerk import offset_polygon, oriented
    try:
        inn = offset_polygon(oriented(list(poly), True), -d)
    except Exception:
        return []
    if len(inn) < 3:
        return []
    pts = K.resample(list(inn) + [inn[0]], schritt / 4)
    out = []
    for i, (x, y) in enumerate(pts):
        a, b = pts[i - 1], pts[(i + 1) % len(pts)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1.0
        s = welle * math.sin(i * math.pi / 2)
        out.append((x - dy / L * s, y + dx / L * s))
    return [(out, True)]


def lebkuchenmann(cx: float, cy: float, g: float) -> List[Point]:
    """Lebkuchenmann der Höhe g, Mitte (cx, cy) – Kopf, Arme und Beine als eine Kontur."""
    f = K.Figur()
    s = g
    f.add(K.circle(cx, cy + 0.3 * s, 0.19 * s, 40))
    f.add(Z.abrunden(K.rect(cx - 0.17 * s, cy - 0.2 * s, 0.34 * s, 0.38 * s), 0.1 * s, 4))
    for sg in (-1, 1):
        f.add(K.stroke([(cx + sg * 0.1 * s, cy + 0.1 * s), (cx + sg * 0.38 * s, cy + 0.04 * s)], 0.17 * s))
        f.add(K.stroke([(cx + sg * 0.08 * s, cy - 0.1 * s), (cx + sg * 0.2 * s, cy - 0.4 * s)], 0.18 * s))
    return f


def lebkuchenmann_gravur(cx: float, cy: float, g: float):
    s = g
    out = [(K.arc(cx, cy + 0.29 * s, 0.08 * s, math.pi * 1.2, math.pi * 1.8, 10), False)]      # Lächeln
    for x in (-0.06, 0.06):
        out.append((K.circle(cx + x * s, cy + 0.35 * s, 0.022 * s, 10), True))                   # Augen
    for y in (0.1, 0.0, -0.1):
        out.append((K.circle(cx, cy + y * s, 0.028 * s, 10), True))                              # Knöpfe
    for sg in (-1, 1):                                                                            # Zickzack
        x0 = cx + sg * 0.3 * s
        out.append(([(x0, cy + 0.11 * s), (x0 + sg * 0.025 * s, cy + 0.03 * s),
                     (x0 + sg * 0.05 * s, cy + 0.1 * s), (x0 + sg * 0.075 * s, cy + 0.02 * s)], False))
        y0 = cy - 0.36 * s
        out.append(([(cx + sg * 0.12 * s, y0 + 0.04 * s), (cx + sg * 0.16 * s, y0 - 0.01 * s),
                     (cx + sg * 0.2 * s, y0 + 0.03 * s), (cx + sg * 0.25 * s, y0 - 0.02 * s)], False))
    return out


def zuckerstange(x: float, y: float, h: float, b: float, links: bool = False):
    """Zuckerstange (J-Form) der Höhe h und Stärke b, unten bei (x, y). Liefert (Fläche, Streifen)."""
    sg = -1 if links else 1
    r = h * 0.17
    pfad = [(x, y), (x, y + h - r)] + [(x + sg * (r - r * math.cos(a)), y + h - r + r * math.sin(a))
                                       for a in (math.pi * i / 12 for i in range(1, 13))]
    pfad = pfad[:-2]
    flaeche = K.stroke(pfad, b)
    streifen = []
    pts = K.resample(pfad, b * 1.1)
    for i in range(1, len(pts) - 1):
        (ax, ay), (bx, by) = pts[i - 1], pts[i + 1]
        dx, dy = bx - ax, by - ay
        L = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / L, dx / L
        px, py = pts[i]
        streifen.append(([(px - nx * b * 0.5 - dx / L * b * 0.3, py - ny * b * 0.5 - dy / L * b * 0.3),
                          (px + nx * b * 0.5 + dx / L * b * 0.3, py + ny * b * 0.5 + dy / L * b * 0.3)], False))
    return flaeche, streifen[::2]
