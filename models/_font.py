"""
_font.py – Einstrich-Schrift (Single-Line-Font) für Gravuren.

Jedes Zeichen besteht aus offenen Linienzügen auf einem Raster: Versalhöhe 6, x-Höhe 4,
Unterlängen bis −2. Einstrich-Schrift ritzt der Laser als saubere Linie – ideal für Namen,
Schilder und Aufschriften.

  Schreibweise  gross  – alles in Großbuchstaben (Standard, wirkt wie Schablonenschrift)
                normal – wie eingegeben, mit Kleinbuchstaben
  Schriftstil   normal · fett · kursiv · schmal · breit · schatten
  Symbole       ♥ ★ ❄ 🎄 (auch ♡ ❤ ☆ ❅ als Varianten)
"""
from __future__ import annotations

import math
from typing import Dict, List, Sequence, Tuple

Point = Tuple[float, float]

_O = [(1, 0), (0, 1), (0, 5), (1, 6), (3, 6), (4, 5), (4, 1), (3, 0), (1, 0)]
_P = [(0, 0), (0, 6), (3, 6), (4, 5), (4, 4), (3, 3), (0, 3)]
_U = [(0, 6), (0, 1), (1, 0), (3, 0), (4, 1), (4, 6)]
_A = [[(0, 0), (2, 6), (4, 0)], [(0.7, 2), (3.3, 2)]]
_DOTS = [[(1, 6.9), (1.5, 6.9)], [(2.5, 6.9), (3, 6.9)]]
# Kleinbuchstaben
_o = [(1, 0), (0, 1), (0, 3), (1, 4), (3, 4), (4, 3), (4, 1), (3, 0), (1, 0)]
_bowl_r = [(4, 3), (3, 4), (1, 4), (0, 3), (0, 1), (1, 0), (3, 0), (4, 1)]       # Bauch rechts offen
_bowl_l = [(0, 1), (1, 0), (3, 0), (4, 1), (4, 3), (3, 4), (1, 4), (0, 3)]       # Bauch links offen
_u = [(0, 4), (0, 1), (1, 0), (3, 0), (4, 1)]
_dots = [[(1, 5.3), (1.5, 5.3)], [(2.5, 5.3), (3, 5.3)]]


def _star() -> List[Point]:
    pts = []
    for k in range(11):
        r = 3.0 if k % 2 == 0 else 1.25
        a = math.pi / 2 + k * math.pi / 5
        pts.append((2 + r * math.cos(a), 2.9 + r * math.sin(a)))
    return pts


def _flake() -> List[List[Point]]:
    out = []
    for k in range(3):
        a = math.pi / 2 + k * math.pi / 3
        dx, dy = 3.0 * math.cos(a), 3.0 * math.sin(a)
        out.append([(2 - dx, 3 - dy), (2 + dx, 3 + dy)])
    for k in range(6):                                            # kleine Spitzen
        a = math.pi / 2 + k * math.pi / 3
        tx, ty = 2 + 2.1 * math.cos(a), 3 + 2.1 * math.sin(a)
        for s in (-1, 1):
            b = a + s * 0.75
            out.append([(tx, ty), (tx + 0.9 * math.cos(b), ty + 0.9 * math.sin(b))])
    return out


GLYPHS: Dict[str, List[List[Point]]] = {
    "A": _A,
    "B": [[(0, 0), (0, 6), (3, 6), (4, 5), (4, 4), (3, 3), (0, 3)], [(3, 3), (4, 2), (4, 1), (3, 0), (0, 0)]],
    "C": [[(4, 5), (3, 6), (1, 6), (0, 5), (0, 1), (1, 0), (3, 0), (4, 1)]],
    "D": [[(0, 0), (0, 6), (2.5, 6), (4, 4.5), (4, 1.5), (2.5, 0), (0, 0)]],
    "E": [[(4, 6), (0, 6), (0, 0), (4, 0)], [(0, 3), (3, 3)]],
    "F": [[(4, 6), (0, 6), (0, 0)], [(0, 3), (3, 3)]],
    "G": [[(4, 5), (3, 6), (1, 6), (0, 5), (0, 1), (1, 0), (3, 0), (4, 1), (4, 3), (2.2, 3)]],
    "H": [[(0, 0), (0, 6)], [(4, 0), (4, 6)], [(0, 3), (4, 3)]],
    "I": [[(1, 6), (3, 6)], [(2, 6), (2, 0)], [(1, 0), (3, 0)]],
    "J": [[(4, 6), (4, 1), (3, 0), (1, 0), (0, 1)]],
    "K": [[(0, 0), (0, 6)], [(4, 6), (0, 2)], [(1.3, 3.3), (4, 0)]],
    "L": [[(0, 6), (0, 0), (4, 0)]],
    "M": [[(0, 0), (0, 6), (2, 3), (4, 6), (4, 0)]],
    "N": [[(0, 0), (0, 6), (4, 0), (4, 6)]],
    "O": [_O],
    "P": [_P],
    "Q": [_O, [(2.5, 1.5), (4, -0.3)]],
    "R": [_P, [(2, 3), (4, 0)]],
    "S": [[(4, 5), (3, 6), (1, 6), (0, 5), (0, 4), (1, 3), (3, 3), (4, 2), (4, 1), (3, 0), (1, 0), (0, 1)]],
    "T": [[(0, 6), (4, 6)], [(2, 6), (2, 0)]],
    "U": [_U],
    "V": [[(0, 6), (2, 0), (4, 6)]],
    "W": [[(0, 6), (1, 0), (2, 4), (3, 0), (4, 6)]],
    "X": [[(0, 0), (4, 6)], [(0, 6), (4, 0)]],
    "Y": [[(0, 6), (2, 3), (4, 6)], [(2, 3), (2, 0)]],
    "Z": [[(0, 6), (4, 6), (0, 0), (4, 0)]],
    "Ä": _A + _DOTS,
    "Ö": [_O] + _DOTS,
    "Ü": [_U] + _DOTS,
    "ß": [[(0, 0), (0, 5), (1, 6), (3, 6), (4, 5), (4, 4.2), (2.5, 3.3), (4, 2.3), (4, 1), (3, 0), (1.8, 0)]],
    "a": [[(4, 4), (4, 0)], _bowl_r],
    "b": [[(0, 6), (0, 0)], _bowl_l],
    "c": [_bowl_r],
    "d": [[(4, 6), (4, 0)], _bowl_r],
    "e": [[(0, 2), (4, 2), (4, 3), (3, 4), (1, 4), (0, 3), (0, 1), (1, 0), (3.6, 0)]],
    "f": [[(3.6, 6), (2.6, 6), (1.6, 5), (1.6, 0)], [(0.4, 4), (3.2, 4)]],
    "g": [[(4, 4), (4, -1), (3, -2), (1, -2), (0.3, -1.4)], _bowl_r],
    "h": [[(0, 6), (0, 0)], [(0, 3), (1, 4), (3, 4), (4, 3), (4, 0)]],
    "i": [[(2, 4), (2, 0)], [(2, 5.4), (2, 5.9)]],
    "j": [[(2.6, 4), (2.6, -1), (1.6, -2), (0.4, -2)], [(2.6, 5.4), (2.6, 5.9)]],
    "k": [[(0, 6), (0, 0)], [(3.6, 4), (0, 1.4)], [(1.3, 2.3), (3.8, 0)]],
    "l": [[(1.4, 6), (1.4, 1), (2.4, 0), (3.2, 0)]],
    "m": [[(0, 0), (0, 4)], [(0, 3), (0.8, 4), (1.3, 4), (2, 3), (2, 0)],
          [(2, 3), (2.7, 4), (3.2, 4), (4, 3), (4, 0)]],
    "n": [[(0, 0), (0, 4)], [(0, 3), (1, 4), (3, 4), (4, 3), (4, 0)]],
    "o": [_o],
    "p": [[(0, 4), (0, -2)], _bowl_l],
    "q": [[(4, 4), (4, -2)], _bowl_r],
    "r": [[(0, 0), (0, 4)], [(0, 2.5), (1.5, 4), (3.4, 4)]],
    "s": [[(4, 3.4), (3, 4), (1, 4), (0, 3.2), (1, 2.1), (3, 1.9), (4, 0.8), (3, 0), (1, 0), (0, 0.6)]],
    "t": [[(1.5, 5.6), (1.5, 1), (2.5, 0), (3.5, 0)], [(0.3, 4), (3.2, 4)]],
    "u": [_u, [(4, 4), (4, 0)]],
    "v": [[(0, 4), (2, 0), (4, 4)]],
    "w": [[(0, 4), (1, 0), (2, 3), (3, 0), (4, 4)]],
    "x": [[(0, 0), (4, 4)], [(0, 4), (4, 0)]],
    "y": [[(0, 4), (2, 0.2)], [(4, 4), (1, -2)]],
    "z": [[(0, 4), (4, 4), (0, 0), (4, 0)]],
    "ä": [[(4, 4), (4, 0)], _bowl_r] + _dots,
    "ö": [_o] + _dots,
    "ü": [_u, [(4, 4), (4, 0)]] + _dots,
    "0": [_O, [(0.6, 0.8), (3.4, 5.2)]],
    "1": [[(1, 4.5), (2.5, 6), (2.5, 0)], [(1, 0), (4, 0)]],
    "2": [[(0, 5), (1, 6), (3, 6), (4, 5), (4, 4), (0, 0), (4, 0)]],
    "3": [[(0, 5), (1, 6), (3, 6), (4, 5), (4, 4), (3, 3), (1.5, 3)],
          [(3, 3), (4, 2), (4, 1), (3, 0), (1, 0), (0, 1)]],
    "4": [[(3, 0), (3, 6), (0, 2), (4, 2)]],
    "5": [[(4, 6), (0, 6), (0, 3.4), (3, 3.6), (4, 2.6), (4, 1), (3, 0), (1, 0), (0, 1)]],
    "6": [[(4, 5), (3, 6), (1, 6), (0, 5), (0, 1), (1, 0), (3, 0), (4, 1), (4, 2.5), (3, 3.5), (0, 3.2)]],
    "7": [[(0, 6), (4, 6), (1.5, 0)]],
    "8": [[(1, 3), (0, 4), (0, 5), (1, 6), (3, 6), (4, 5), (4, 4), (3, 3), (1, 3), (0, 2), (0, 1),
           (1, 0), (3, 0), (4, 1), (4, 2), (3, 3)]],
    "9": [[(0, 1), (1, 0), (3, 0), (4, 1), (4, 5), (3, 6), (1, 6), (0, 5), (0, 3.5), (1, 2.5), (4, 2.8)]],
    "-": [[(1, 3), (3, 3)]],
    "+": [[(2, 1.5), (2, 4.5)], [(0.5, 3), (3.5, 3)]],
    ".": [[(1.8, 0), (2.2, 0)]],
    ",": [[(2.2, 0.4), (1.6, -0.8)]],
    ":": [[(1.8, 0), (2.2, 0)], [(1.8, 3), (2.2, 3)]],
    ";": [[(1.8, 3), (2.2, 3)], [(2.2, 0.4), (1.6, -0.8)]],
    "!": [[(2, 6), (2, 1.6)], [(1.8, 0), (2.2, 0)]],
    "?": [[(0, 5), (1, 6), (3, 6), (4, 5), (4, 4), (2, 2.6), (2, 1.6)], [(1.8, 0), (2.2, 0)]],
    "&": [[(4, 0), (0.8, 4.2), (0.8, 5.2), (1.6, 6), (2.6, 5.2), (2.6, 4.4), (0, 2), (0, 1), (1, 0),
           (2.6, 0), (4, 2)]],
    "'": [[(2, 6), (1.7, 4.8)]],
    '"': [[(1.3, 6), (1.3, 4.6)], [(2.7, 6), (2.7, 4.6)]],
    "(": [[(3, 6.5), (1.8, 5), (1.5, 3), (1.8, 1), (3, -0.5)]],
    ")": [[(1, 6.5), (2.2, 5), (2.5, 3), (2.2, 1), (1, -0.5)]],
    "/": [[(0, 0), (4, 6)]],
    "*": [[(2, 1), (2, 5)], [(0.3, 2), (3.7, 4)], [(0.3, 4), (3.7, 2)]],
    "=": [[(0.5, 2), (3.5, 2)], [(0.5, 4), (3.5, 4)]],
    "#": [[(1.3, 0.5), (1.8, 5.5)], [(2.7, 0.5), (3.2, 5.5)], [(0.3, 2), (4, 2)], [(0.3, 4), (4, 4)]],
    "°": [[(2, 6), (1.4, 5.4), (2, 4.8), (2.6, 5.4), (2, 6)]],
    "♥": [[(2, 0.2), (0.4, 2.4), (0, 3.6), (0.3, 4.8), (1.1, 5.4), (2, 4.8), (2.9, 5.4), (3.7, 4.8),
           (4, 3.6), (3.6, 2.4), (2, 0.2)]],
    "★": [_star()],
    "❄": _flake(),
    "🎄": [[(2, 6), (0.6, 3.8), (1.4, 3.8), (0, 1.4), (4, 1.4), (2.6, 3.8), (3.4, 3.8), (2, 6)], [(2, 1.4), (2, 0)]],
    " ": [],
}
ALIASES = {"♡": "♥", "❤": "♥", "☆": "★", "✩": "★", "✶": "★", "❅": "❄", "❆": "❄", "ẞ": "ß",
           "„": '"', "“": '"', "”": '"', "‘": "'", "’": "'", "–": "-", "—": "-", " ": " "}
SYMBOLS = ["♥", "★", "❄", "🎄"]
STYLES = ["normal", "fett", "kursiv", "schmal", "breit", "schatten"]
CASES = ["gross", "normal"]
CAP = 6.0              # Versalhöhe im Raster
GAP = 1.3              # Abstand zwischen zwei Zeichen (Raster)
SPACE = 3.0            # Wortabstand (Raster)
LINE_GAP = 0.55        # Zeilenabstand in Versalhöhen
MIN_W = 1.2            # schmale Zeichen (i, l, !) bekommen etwas Luft

_BOUNDS = {}
for _c, _st in GLYPHS.items():
    _xs = [p[0] for s in _st for p in s]
    _BOUNDS[_c] = (min(_xs), max(_xs)) if _xs else (0.0, SPACE - GAP)


def _sym(c: str) -> str:
    return ALIASES.get(c, c)


def normalize(text: str, case: str = "gross") -> str:
    """Text in darstellbare Zeichen umsetzen (Unbekanntes wird zu '?')."""
    t = "".join(_sym(c) for c in text)
    if case == "gross":
        t = "".join(c if c == "ß" else c.upper() for c in t)
    out = []
    for c in t:
        if c in GLYPHS:
            out.append(c)
        elif c.upper() in GLYPHS:
            out.append(c.upper())
        else:
            out.append("?")
    return "".join(out)


def unsupported(text: str) -> List[str]:
    bad = set()
    for c in text:
        if c in "\n|":
            continue
        c = _sym(c)
        if c not in GLYPHS and c.upper() not in GLYPHS:
            bad.add(c.upper())
    return sorted(bad)


def _advance(c: str, sx: float) -> float:
    x0, x1 = _BOUNDS[c]
    return max(x1 - x0, MIN_W) * sx + GAP


def text_width(line: str, style: str = "normal") -> float:
    """Breite einer (bereits normalisierten) Zeile in Rastereinheiten."""
    sx = {"schmal": 0.75, "breit": 1.3}.get(style, 1.0)
    if not line:
        return 0.0
    return sum(_advance(c, sx) for c in line) - GAP


def _line_strokes(line: str, style: str) -> List[List[Point]]:
    """Zeile im Raster, links bei x=0, Grundlinie y=0 (ohne fett/schatten)."""
    sx = {"schmal": 0.75, "breit": 1.3}.get(style, 1.0)
    slant = 0.2 if style == "kursiv" else 0.0
    out: List[List[Point]] = []
    x = 0.0
    for c in line:
        x0, x1 = _BOUNDS[c]
        pad = max(0.0, MIN_W - (x1 - x0)) / 2                    # schmale Zeichen mittig
        for stroke in GLYPHS[c]:
            out.append([(x + (px - x0 + pad) * sx + slant * py, py) for px, py in stroke])
        x += _advance(c, sx)
    return out


def _bbox(strokes: Sequence[Sequence[Point]]) -> Tuple[float, float, float, float]:
    xs = [p[0] for s in strokes for p in s]
    ys = [p[1] for s in strokes for p in s]
    return min(xs), min(ys), max(xs), max(ys)


def text_strokes(text: str, style: str = "normal", case: str = "gross") -> List[List[Point]]:
    """Mehrzeiliger Text im Raster (Versalhöhe 6), Zeilen zentriert, oberste Zeile bei y=0."""
    lines = [normalize(ln.strip(), case) for ln in text.replace("|", "\n").split("\n") if ln.strip()]
    out: List[List[Point]] = []
    for i, ln in enumerate(lines):
        w = text_width(ln, style)
        y = -i * (1 + LINE_GAP) * CAP
        out += [[(x - w / 2, yy + y) for x, yy in s] for s in _line_strokes(ln, style)]
    return out


def fit_text(text: str, cx: float, cy: float, max_w: float, max_h: float,
             min_h: float = 3.0, max_cap: float = 12.0, style: str = "normal",
             case: str = "gross") -> Tuple[List[List[Point]], float]:
    """Mehrzeiligen Text ('|' oder Zeilenumbruch trennt Zeilen) in eine Box einpassen und dort
    zentrieren. Liefert (Striche in mm, Versalhöhe). ValueError, wenn er nur kleiner als min_h passt."""
    if style not in STYLES:
        raise ValueError(f"Schriftstil {style!r} unbekannt – erlaubt: {', '.join(STYLES)}")
    if case not in CASES:
        raise ValueError(f"Schreibweise {case!r} unbekannt – erlaubt: {', '.join(CASES)}")
    base = [s for s in text_strokes(text, style, case) if s]
    if not base:
        return [], 0.0
    x0, y0, x1, y1 = _bbox(base)
    # fett/schatten: Zusatzstriche in mm, als Rand in der Box reservieren
    extra = {"fett": 0.05, "schatten": 0.1}.get(style, 0.0)            # × Versalhöhe
    w_u, h_u = max(x1 - x0, 1e-9), max(y1 - y0, 1e-9)
    s = min(max_w / (w_u + extra * CAP), max_h / (h_u + extra * CAP), max_cap / CAP)
    h = s * CAP
    if h < min_h - 1e-9:
        raise ValueError(f"Text {text!r} passt nur mit {h:.1f} mm Schrifthöhe (min. {min_h:g} mm) – "
                         f"kürzer fassen oder größer machen")
    d = extra * h
    ox = cx - (x0 + x1) / 2 * s - (d / 2 if style == "fett" else d / 2)
    oy = cy - (y0 + y1) / 2 * s + (d / 2 if style == "schatten" else -d / 2)
    strokes = [[(ox + x * s, oy + y * s) for x, y in st] for st in base]
    if style == "fett":
        strokes = strokes + [[(x + d, y) for x, y in st] for st in strokes] + \
            [[(x + d / 2, y + d) for x, y in st] for st in strokes]
    elif style == "schatten":
        strokes = strokes + [[(x + d, y - d) for x, y in st] for st in strokes]
    return strokes, h


def render_line(line: str, cx: float, y0: float, h: float, style: str = "normal",
                case: str = "gross") -> List[List[Point]]:
    """Zeile mit Versalhöhe h, horizontal zentriert um cx, Grundlinie bei y0 (ohne fett/schatten)."""
    s = h / CAP
    ln = normalize(line, case)
    w = text_width(ln, style)
    return [[(cx + (x - w / 2) * s, y0 + y * s) for x, y in st] for st in _line_strokes(ln, style)]
