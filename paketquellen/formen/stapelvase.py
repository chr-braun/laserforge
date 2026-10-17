"""
Stapelvase – gedrehte Vase, Windlicht oder Skulptur aus gestapelten Lagen.

Jede Lage ist ein Querschnitt r(θ) · s(z) der Form, um den Winkel Verdrehung · z/H gedreht. Lagen werden
aufeinander geklebt. Ein durchgehendes rundes Loch für einen Glaseinsatz (Teelichtglas, Reagenzglas)
führt die Lagen beim Kleben; ohne Einsatz gibt es ein Loch für einen Rundstab. Jede Lage trägt ihre
Nummer und eine Marke, an die die Spitze der nächsten Lage gehört.
"""
from __future__ import annotations

import math
import os
import sys
from typing import Callable, Dict, List, Tuple

from steckwerk import Assembly, Part, circle, dist_to_boundary, point_in_polygon
from pakete import flag, integer, num, sel

FORMEN = [("stern", "Stern"), ("vieleck", "Vieleck"), ("bluete", "Blüte"), ("zahnrad", "Zahnkranz"),
          ("welle", "Wellenrand")]
VERLAEUFE: Dict[str, Callable[[float], float]] = {
    "gerade": lambda t: 1.0,
    "bauch": lambda t: 0.82 + 0.18 * math.sin(math.pi * t),
    "taille": lambda t: 1.0 - 0.22 * math.sin(math.pi * t),
    "tulpe": lambda t: 0.78 + 0.22 * math.sin(math.pi * (0.25 + 0.75 * t)),
    "kegel": lambda t: 1.0 - 0.4 * t,
    "kelch": lambda t: 0.62 + 0.38 * t ** 1.6,
}
VERLAUF_LISTE = [("gerade", "gerade"), ("bauch", "bauchig"), ("taille", "mit Taille"), ("tulpe", "Tulpe"),
                 ("kegel", "nach oben schmaler"), ("kelch", "Kelch (oben weit)")]

INFO = dict(
    label="Stapelvase",
    group="Formen",
    desc="Gedrehte Vase, Windlicht oder Skulptur aus gestapelten Lagen – Stern, Vieleck, Blüte oder Zahnkranz, "
         "bauchig, mit Taille oder als Kelch. Ein Glaseinsatz führt die Lagen beim Kleben.",
    params=[
        sel("form", "Querschnitt", FORMEN, "stern"),
        integer("ecken", "Ecken", 6, 3, 16),
        sel("verlauf", "Verlauf", VERLAUF_LISTE, "bauch"),
        num("durchmesser", "Durchmesser", 140, 50, 280),
        num("hoehe", "Höhe", 120, 15, 300, help="wird auf ganze Lagen gerundet"),
        num("drehung", "Verdrehung", 90, -360, 360, step=5, unit="°", help="Drehung von unten bis oben"),
        num("einsatz", "Glaseinsatz Ø", 50, 0, 200, help="0 = massiv mit Loch für einen Rundstab"),
        num("rundstab", "Rundstab Ø", 6, 3, 12, when={"einsatz": [0]}),
        integer("boden", "Bodenlagen ohne Loch", 1, 0, 5, help="dicht für eine Vase, 0 = Hülse"),
        flag("beschriften", "Lagen nummerieren und Marke gravieren", True),
    ],
)

UEBERSETZUNG = {"en": {
    "Stapelvase": "Stacked vase", "Formen": "Shapes",
    "Gedrehte Vase, Windlicht oder Skulptur aus gestapelten Lagen – Stern, Vieleck, Blüte oder Zahnkranz, "
    "bauchig, mit Taille oder als Kelch. Ein Glaseinsatz führt die Lagen beim Kleben.":
        "Twisted vase, lantern or sculpture from stacked layers – star, polygon, flower or gear rim, bulbous, "
        "waisted or as a goblet. A glass insert guides the layers while gluing.",
    "Querschnitt": "Cross-section", "Ecken": "Points", "Verlauf": "Profile", "Durchmesser": "Diameter",
    "Höhe": "Height", "wird auf ganze Lagen gerundet": "rounded to whole layers", "Verdrehung": "Twist",
    "Drehung von unten bis oben": "rotation from bottom to top", "Glaseinsatz Ø": "Glass insert Ø",
    "0 = massiv mit Loch für einen Rundstab": "0 = solid with a hole for a dowel", "Rundstab Ø": "Dowel Ø",
    "Bodenlagen ohne Loch": "Bottom layers without hole", "dicht für eine Vase, 0 = Hülse": "watertight for a vase, 0 = sleeve",
    "Lagen nummerieren und Marke gravieren": "Number the layers and engrave a mark",
    "Stern": "Star", "Vieleck": "Polygon", "Blüte": "Flower", "Zahnkranz": "Gear rim", "Wellenrand": "Wavy rim",
    "gerade": "straight", "bauchig": "bulbous", "mit Taille": "waisted", "Tulpe": "Tulip",
    "nach oben schmaler": "narrowing upwards", "Kelch (oben weit)": "Goblet (wide at the top)",
}}


def _r(form: str, k: int, th: float) -> float:
    """Radius (≤ 1) des Querschnitts beim Winkel th, Spitze bei th = 0."""
    if form == "vieleck":
        a = math.pi / k
        x = (th % (2 * a)) - a
        return math.cos(a) / math.cos(x)
    if form == "stern":
        a = math.pi / k
        x = abs((th % (2 * a)) - a) / a                   # 1 an der Spitze, 0 im Tal
        inner = 0.62 if k <= 6 else 0.72
        return inner + (1 - inner) * x ** 1.0
    if form == "bluete":
        c = math.cos(k * th)
        return 0.8 + 0.2 * c if c >= 0 else 0.8 + 0.12 * c
    if form == "zahnrad":
        c = math.cos(k * th)
        return 0.86 + 0.14 * max(-1.0, min(1.0, 2.2 * c))
    if form == "welle":
        return 0.9 + 0.1 * math.cos(k * th)
    raise ValueError(f"Unbekannter Querschnitt {form!r}")


def _umriss(form: str, k: int, R: float, rot: float, n: int = 0) -> List[Tuple[float, float]]:
    n = n or max(120, 24 * k)
    pts = []
    for i in range(n):
        th = 2 * math.pi * i / n
        r = R * _r(form, k, th)
        pts.append((r * math.cos(th + rot), r * math.sin(th + rot)))
    return pts


def build(cfg, name: str = "stapelvase", form: str = "stern", ecken: int = 6, verlauf: str = "bauch",
          durchmesser: float = 140.0, hoehe: float = 120.0, drehung: float = 90.0, einsatz: float = 50.0,
          rundstab: float = 6.0, boden: int = 1, beschriften: bool = True):
    from models._font import fit_text
    if verlauf not in VERLAEUFE:
        raise ValueError(f"Unbekannter Verlauf {verlauf!r}")
    if form not in dict(FORMEN):
        raise ValueError(f"Unbekannter Querschnitt {form!r}")
    T = cfg.T
    k = int(ecken)
    R = cfg.s(durchmesser) / 2
    H = cfg.s(hoehe)
    N = max(2, int(round(H / T)))
    if N > 150:
        raise ValueError(f"{N} Lagen sind zu viele – niedriger bauen oder dickeres Material nehmen")
    loch = cfg.s(einsatz) / 2 if einsatz > 0 else rundstab / 2
    wand = max(3.0, 2 * cfg.min_web + 1.0)
    prof = VERLAEUFE[verlauf]
    rmin_form = min(_r(form, k, 2 * math.pi * i / 720) for i in range(720))
    tw = math.radians(drehung)
    asm = Assembly(name, params=dict(form=form, ecken=k, verlauf=verlauf, durchmesser=2 * R, lagen=N,
                                     hoehe=round(N * T, 1), drehung=drehung, einsatz=einsatz))
    gross = 2 * R * max(prof(i / 50) for i in range(51))
    if not (gross + 1 <= min(cfg.sheet_width, cfg.sheet_height) - 2 * cfg.sheet_margin):
        raise ValueError("Die Lagen werden zu groß für die Platte – Durchmesser verkleinern")
    for i in range(N):
        t = (i + 0.5) / N
        Ri = R * prof(t)
        rot = tw * i / max(1, N - 1)
        out = _umriss(form, k, Ri, rot)
        p = Part(f"L{i + 1:02d}", out)
        mit_loch = i >= int(boden)
        if mit_loch:
            if Ri * rmin_form - loch < wand:
                engste = min(R * prof((j + 0.5) / N) for j in range(int(boden), N)) * rmin_form
                if einsatz > 0:
                    raise ValueError(f"Lage {i + 1}: zwischen Glaseinsatz und Rand bleibt zu wenig Holz – Glas höchstens "
                                     f"{max(0, int(2 * (engste - wand))):d} mm oder die Vase breiter machen")
                raise ValueError(f"Lage {i + 1}: für den Rundstab ist die Vase zu schmal – breiter machen")
            p.add_hole(circle(0, 0, loch, cfg.arc_tolerance))
        if beschriften:
            inner = loch if mit_loch else 0.0
            # Marke: kurzer Strich in Richtung der Spitze der nächsten Lage
            nxt = tw * (i + 1) / max(1, N - 1) if i + 1 < N else None
            if nxt is not None:
                r_out = Ri * _r(form, k, (nxt - rot) % (2 * math.pi))
                r1 = r_out - 1.6
                r0 = max(inner + 1.6, r1 - 5.0)
                if r1 - r0 > 1.5:
                    a = (math.cos(nxt), math.sin(nxt))
                    seg = [(r0 * a[0], r0 * a[1]), (r1 * a[0], r1 * a[1])]
                    if all(point_in_polygon(q, out) and dist_to_boundary(q, out) > 0.9 for q in seg):
                        p.add_engrave(seg)
            # Nummer im Ring zwischen Loch und Rand, gegenüber der Marke
            ring = Ri * rmin_form - inner
            cap = max(2.5, min(5.0, ring * 0.45))
            for ang in (rot + math.pi + math.pi / k, rot + math.pi / k, rot + math.pi / 2):
                rc = inner + ring / 2
                cx, cy = rc * math.cos(ang), rc * math.sin(ang)
                try:
                    strokes, _ = fit_text(str(i + 1), cx, cy, ring * 0.9, cap * 1.3, min_h=2.2, max_cap=cap)
                except ValueError:
                    continue
                if strokes and all(point_in_polygon(q, out) and dist_to_boundary(q, out) > 0.9
                                   and math.hypot(*q) > inner + 0.9 for s in strokes for q in s):
                    for s in strokes:
                        p.add_engrave(s)
                    break
        asm.parts.append(p)
    asm.notes.append(f"{N} Lagen à {T:g} mm = {N * T:.0f} mm hoch, oben um {drehung:g}° gedreht.")
    if einsatz > 0:
        asm.notes.append(f"Glaseinsatz mit {einsatz:g} mm Außendurchmesser (z. B. Teelicht- oder Windlichtglas) "
                         "als Führung einsetzen und die Lagen der Reihe nach (1 unten) mit Holzleim aufkleben.")
    else:
        asm.notes.append(f"Rundstab Ø {rundstab:g} mm als Führung durch alle Lagen stecken, Lagen der Reihe nach "
                         "(1 unten) aufkleben.")
    if beschriften:
        asm.notes.append("Die kleine Marke auf jeder Lage zeigt, wo die Spitze der nächsten Lage hingehört.")
    if einsatz > 0 and boden == 0:
        asm.notes.append("Ohne Bodenlage ist es eine Hülse – das Glas steht dann direkt auf dem Tisch.")
    return asm


def _flaechen3d(asm, cfg, kw):
    """Für Vorschaubilder: Seitenwände jeder Lage plus Deckfläche (Viereck-Liste, Farbe)."""
    import math as _m
    T = cfg.T
    out = []
    for i, p in enumerate(asm.parts):
        o = p.outline
        z0, z1 = i * T, (i + 1) * T
        for j in range(len(o)):
            a, b = o[j - 1], o[j]
            nx, ny = b[1] - a[1], a[0] - b[0]
            light = 0.55 + 0.45 * max(0.0, (nx * 0.6 + ny * -0.8) / (_m.hypot(nx, ny) or 1))
            out.append(([(a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], z1), (a[0], a[1], z1)], light))
    top = asm.parts[-1].outline
    out.append(([(x, y, len(asm.parts) * T) for x, y in top], 1.0))
    return out
