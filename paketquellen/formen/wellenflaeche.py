"""
Wellenfläche – eine Fläche z = f(x, y) als Gitter aus gekreuzten Rippen (Waffel-Sliceform).

Die Rippen der Schar A laufen in x-Richtung (Ebenen y = konstant), die der Schar B in y-Richtung.
Jede Rippe steht auf einer geraden Unterkante, oben folgt sie exakt der Fläche. An jeder Kreuzung
sind beide Rippen gleich hoch; A wird von oben, B von unten bis zur halben Höhe geschlitzt.
"""
from __future__ import annotations

import math
import os
import sys
from typing import Callable, Dict, List, Tuple

from steckwerk import Assembly
from pakete import flag, integer, num, sel

_here = os.path.dirname(os.path.abspath(__file__))


def _sub(name: str):
    import importlib.util
    path = os.path.join(_here, name + ".py")
    key = "swpaket_formen_" + name
    mod = sys.modules.get(key)
    if mod is None or getattr(mod, "__file__", None) != path:
        spec = importlib.util.spec_from_file_location(key, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[key] = mod
        spec.loader.exec_module(mod)
    return mod


ST = _sub("_steck")


def _r(x, y):
    return math.hypot(x, y)


# f(x, y) mit x, y ∈ [−1, 1] → Wert in [0, 1]
FUNKTIONEN: Dict[str, Callable[[float, float], float]] = {
    "welle": lambda x, y: 0.5 + 0.5 * math.sin(1.5 * math.pi * x) * math.cos(1.5 * math.pi * y),
    "sattel": lambda x, y: 0.5 + 0.5 * (x * x - y * y),
    "huegel": lambda x, y: math.exp(-3.2 * (x * x + y * y)),
    "tropfen": lambda x, y: 0.5 + 0.5 * math.cos(3.2 * math.pi * min(1.0, _r(x, y) / 1.2)) * (1 - min(1.0, _r(x, y) / 1.45)),
    "duenen": lambda x, y: 0.5 + 0.5 * math.sin(2.2 * math.pi * (x + 0.35 * math.sin(2.0 * y))),
    "zwei_gipfel": lambda x, y: min(1.0, 1.05 * math.exp(-5 * ((x - 0.42) ** 2 + (y - 0.3) ** 2))
                                    + 0.8 * math.exp(-5 * ((x + 0.45) ** 2 + (y + 0.35) ** 2))),
    "kuppel": lambda x, y: math.sqrt(max(0.0, 1 - 0.5 * (x * x + y * y))) * 1.0 - 0.0,
}
FUNKTION_LISTE = [("welle", "Eierkarton-Welle"), ("sattel", "Sattel (Pringle)"), ("huegel", "Hügel (Glocke)"),
                  ("tropfen", "Wassertropfen (Ringwellen)"), ("duenen", "Dünen"), ("zwei_gipfel", "Zwei Gipfel"),
                  ("kuppel", "Kissen")]

INFO = dict(
    label="Wellenfläche",
    group="Formen",
    desc="Eine geschwungene Fläche als Gitter aus gekreuzten Rippen: Eierkarton-Welle, Sattel, Hügel, "
         "Ringwellen, Dünen oder zwei Gipfel. Schön als Schale, Tischdeko oder Wandobjekt.",
    params=[
        sel("funktion", "Fläche", FUNKTION_LISTE, "welle"),
        num("breite", "Breite", 180, 80, 380),
        num("tiefe", "Tiefe", 180, 80, 380),
        num("hoehe", "Höhe der Welle", 45, 10, 150, help="Unterschied zwischen tiefster und höchster Stelle"),
        num("sockel", "Sockel", 20, 6, 80, help="Höhe unter der tiefsten Stelle"),
        integer("rippen_x", "Rippen längs", 7, 2, 16),
        integer("rippen_y", "Rippen quer", 7, 2, 16),
        flag("beschriften", "Rippen beschriften (A1, B1 …)", True),
    ],
)

UEBERSETZUNG = {"en": {
    "Wellenfläche": "Wave surface", "Formen": "Shapes",
    "Eine geschwungene Fläche als Gitter aus gekreuzten Rippen: Eierkarton-Welle, Sattel, Hügel, "
    "Ringwellen, Dünen oder zwei Gipfel. Schön als Schale, Tischdeko oder Wandobjekt.":
        "A curved surface as a grid of crossed ribs: egg-crate wave, saddle, hill, ripples, dunes or two peaks. "
        "Lovely as a bowl, table decoration or wall piece.",
    "Fläche": "Surface", "Breite": "Width", "Tiefe": "Depth", "Höhe der Welle": "Wave height",
    "Unterschied zwischen tiefster und höchster Stelle": "difference between lowest and highest point",
    "Sockel": "Base", "Höhe unter der tiefsten Stelle": "height below the lowest point",
    "Rippen längs": "Ribs lengthwise", "Rippen quer": "Ribs crosswise",
    "Rippen beschriften (A1, B1 …)": "Label the ribs (A1, B1 …)",
    "Eierkarton-Welle": "Egg-crate wave", "Sattel (Pringle)": "Saddle (Pringle)", "Hügel (Glocke)": "Hill (bell)",
    "Wassertropfen (Ringwellen)": "Water drop (ripples)", "Dünen": "Dunes", "Zwei Gipfel": "Two peaks",
    "Kissen": "Cushion",
}}


def build(cfg, name: str = "wellenflaeche", funktion: str = "welle", breite: float = 180.0, tiefe: float = 180.0,
          hoehe: float = 45.0, sockel: float = 20.0, rippen_x: int = 7, rippen_y: int = 7, beschriften: bool = True):
    if funktion not in FUNKTIONEN:
        raise ValueError(f"Unbekannte Fläche {funktion!r}")
    T = cfg.T
    W, D, A, S = cfg.s(breite), cfg.s(tiefe), cfg.s(hoehe), cfg.s(sockel)
    nA, nB = int(rippen_y), int(rippen_x)               # A-Rippen liegen quer verteilt, laufen längs
    f = FUNKTIONEN[funktion]
    h_min = max(4 * T, 3 * T + 4 * cfg.min_web)
    if S < h_min:
        raise ValueError(f"Sockel zu niedrig – mindestens {h_min:.0f} mm bei {T:g} mm Material")
    if not (ST.passt(W, S + A, cfg) and ST.passt(D, S + A, cfg)):
        raise ValueError("Die Rippen werden zu groß für die Platte – Breite, Tiefe oder Höhe verkleinern")
    rand = max(6.0, 2 * T)                              # Überstand hinter der letzten Kreuzung
    ys = [-D / 2 + rand + (D - 2 * rand) * k / (nA - 1) for k in range(nA)]
    xs = [-W / 2 + rand + (W - 2 * rand) * k / (nB - 1) for k in range(nB)]
    for gaps, n, nm in ((ys, nA, "quer"), (xs, nB, "längs")):
        if n > 1 and gaps[1] - gaps[0] < 2 * T + 4 * cfg.min_web + 3:
            raise ValueError(f"Zu viele Rippen {nm} für die Größe – weniger Rippen oder größer machen")
    hz = lambda x, y: S + A * f(max(-1.0, min(1.0, 2 * x / W)), max(-1.0, min(1.0, 2 * y / D)))

    def profil(L: float, top: Callable[[float], float]):
        N = max(60, int(L / 1.5))
        us = [-L / 2 + L * k / N for k in range(N + 1)]
        return [(-L / 2, 0.0), (L / 2, 0.0)] + [(u, top(u)) for u in reversed(us)]

    asm = Assembly(name, params=dict(funktion=funktion, breite=W, tiefe=D, hoehe=A, sockel=S,
                                     rippen_x=nB, rippen_y=nA, xs=xs, ys=ys))
    RA = [ST.Rippe(f"A{i + 1}", profil(W, lambda u, y=y: hz(u, y)), f"A{i + 1}" if beschriften else "")
          for i, y in enumerate(ys)]
    RB = [ST.Rippe(f"B{j + 1}", profil(D, lambda u, x=x: hz(x, u)), f"B{j + 1}" if beschriften else "")
          for j, x in enumerate(xs)]
    for i, y in enumerate(ys):
        for j, x in enumerate(xs):
            h = hz(x, y)
            zm = h / 2
            RA[i].schlitz(f"b{j + 1}", x, zm, True, (zm, h))
            RB[j].schlitz(f"a{i + 1}", y, zm, False, (0.0, zm))
    cap = max(3.0, min(6.0, S * 0.35))
    for rip in RA + RB:
        asm.parts.append(rip.teil(T, cap))
    for i in range(nA):
        for j in range(nB):
            asm.connect(f"A{i + 1}:b{j + 1}", f"B{j + 1}:a{i + 1}")
    asm.notes.append(f"{nA} A-Rippen (Schlitze oben) laufen längs, {nB} B-Rippen (Schlitze unten) quer – "
                     f"{nA * nB} Kreuzungen.")
    asm.notes.append("Zusammenbau: A-Rippen der Reihe nach hinstellen (A1 vorne), dann die B-Rippen von oben "
                     "einschieben, B1 links. Bei vielen Kreuzungen erst halb einschieben, dann reihum ganz.")
    return asm


def _platzierung(asm, cfg, kw):
    xs, ys = asm.params["xs"], asm.params["ys"]
    out = []
    for p in asm.parts:
        k = int(p.name[1:]) - 1
        if p.name[0] == "A":
            out.append([(u, ys[k], z) for u, z in p.outline])
        else:
            out.append([(xs[k], u, z) for u, z in p.outline])
    return out
