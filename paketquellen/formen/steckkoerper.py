"""
Steckkörper – Kugel, Ei, Zwiebel, Tanne und Co. aus zwei Scharen gekreuzter Rippen (Sliceform).

Der Körper ist ein Drehkörper mit dem Radius ρ(z). Jede Rippe ist ein ebener Schnitt im Abstand c von
der Achse: halbe Breite √(ρ(z)² − c²). Zwei Rippen kreuzen sich, wo ρ(z) ≥ √(cₐ² + c_b²); dort bekommen
sie gegenläufige Schlitze bis zur Mitte des gemeinsamen Stücks. Zu kurze Kreuzungen am Rand werden
weggeschnitten statt geschlitzt.
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

# Form → (Höhe / Durchmesser, ρ(t)/R für t = 0…1 von unten nach oben, darf flach stehen)
FORMEN: Dict[str, Tuple[float, Callable[[float], float], bool]] = {
    "kugel": (1.0, lambda t: math.sqrt(max(0.0, 1 - (2 * t - 1) ** 2)), True),
    "ei": (1.3, lambda t: math.sqrt(max(0.0, 1 - (2 * t - 1) ** 2)) * (1 - 0.28 * (2 * t - 1)), True),
    "linse": (0.55, lambda t: math.sqrt(max(0.0, 1 - (2 * t - 1) ** 2)), True),
    "zwiebel": (1.35, lambda t: math.sin(math.pi * min(1.0, t) ** 0.75) * max(0.0, 1 - t) ** 0.35, True),
    "kreisel": (1.0, lambda t: max(0.0, 1 - abs(2 * t - 1)) ** 0.85, True),
    "tanne": (1.5, lambda t: max(0.0, 1 - t) ** 1.08, False),
    "kuppel": (0.5, lambda t: math.sqrt(max(0.0, 1 - t * t)), False),
}
FORM_LISTE = [("kugel", "Kugel"), ("ei", "Ei"), ("linse", "Linse (flach)"), ("zwiebel", "Zwiebelturm"),
              ("kreisel", "Kreisel (Doppelkegel)"), ("tanne", "Tanne (Kegel)"), ("kuppel", "Kuppel (Halbkugel)")]

INFO = dict(
    label="Steckkörper",
    group="Formen",
    desc="Kugel, Ei, Zwiebelturm, Tanne und mehr aus zwei Scharen gekreuzter Rippen. Jede Rippe ist ein "
         "exakt berechneter Schnitt durch den Körper, die Schlitze passen zur Materialstärke.",
    params=[
        sel("form", "Form", FORM_LISTE, "kugel"),
        num("durchmesser", "Durchmesser", 120, 50, 280),
        integer("rippen", "Rippen je Richtung", 6, 2, 12, help="mehr Rippen = feiner, aber mehr Teile"),
        flag("flach_unten", "Unten abgeflacht (steht von allein)", True),
        flag("beschriften", "Rippen beschriften (A1, B1 …)", True),
    ],
)

UEBERSETZUNG = {"en": {
    "Steckkörper": "Slotted solid", "Formen": "Shapes",
    "Kugel, Ei, Zwiebelturm, Tanne und mehr aus zwei Scharen gekreuzter Rippen. Jede Rippe ist ein "
    "exakt berechneter Schnitt durch den Körper, die Schlitze passen zur Materialstärke.":
        "Sphere, egg, onion dome, fir tree and more from two sets of crossed ribs. Every rib is an exactly "
        "computed section through the solid, the slots match the material thickness.",
    "Form": "Shape", "Durchmesser": "Diameter", "Rippen je Richtung": "Ribs per direction",
    "mehr Rippen = feiner, aber mehr Teile": "more ribs = finer, but more parts",
    "Unten abgeflacht (steht von allein)": "Flattened bottom (stands by itself)",
    "Rippen beschriften (A1, B1 …)": "Label the ribs (A1, B1 …)",
    "Kugel": "Sphere", "Ei": "Egg", "Linse (flach)": "Lens (flat)", "Zwiebelturm": "Onion dome",
    "Kreisel (Doppelkegel)": "Spinning top (double cone)", "Tanne (Kegel)": "Fir tree (cone)",
    "Kuppel (Halbkugel)": "Dome (hemisphere)",
}}


def _boden(rho: Callable[[float], float]) -> float:
    """Unterste Höhe t, ab der der Körper halb so breit ist wie maximal – dort steht er flach."""
    ts = [i / 400 for i in range(401)]
    m = max(rho(t) for t in ts)
    for t in ts:
        if rho(t) >= 0.5 * m:
            return t
    return 0.0


def build(cfg, name: str = "steckkoerper", form: str = "kugel", durchmesser: float = 120.0, rippen: int = 6,
          flach_unten: bool = True, beschriften: bool = True):
    if form not in FORMEN:
        raise ValueError(f"Unbekannte Form {form!r}")
    T = cfg.T
    D = cfg.s(durchmesser)
    R = D / 2
    hf, rho_t, kann_flach = FORMEN[form]
    H = hf * D
    n = int(rippen)
    if n < 2:
        raise ValueError("Mindestens 2 Rippen je Richtung")
    t0 = _boden(rho_t) if (flach_unten and kann_flach) else 0.0
    z0 = t0 * H
    rho = lambda z: R * rho_t(min(1.0, max(0.0, z / H)))
    rmax = max(rho(H * k / 400) for k in range(401))
    cmax = 0.72 * rmax
    d = 2 * cmax / (n - 1)
    gap_min = 2 * T + 4 * cfg.min_web + 2.0
    if d < gap_min:
        raise ValueError(f"Zu viele Rippen für {durchmesser:g} mm – höchstens "
                         f"{max(2, int(2 * cmax / gap_min) + 1)} oder größer machen")
    if not ST.passt(2 * rmax, H - z0, cfg):
        raise ValueError(f"Der Körper ist zu groß für die Platte ({cfg.sheet_width:g} × {cfg.sheet_height:g} mm) – "
                         "Durchmesser verkleinern")
    cs = [(k - (n - 1) / 2) * d for k in range(n)]
    L_min = max(4 * T, 3 * T + 4 * cfg.min_web)

    # Kreuzungen planen
    kreuz = {}
    trim: Dict[int, List[float]] = {i: [-1e9, 1e9] for i in range(n)}
    for i, ca in enumerate(cs):
        for j, cb in enumerate(cs):
            r = math.hypot(ca, cb)
            iv = ST.bereich(lambda z: rho(z) - r, z0, H)
            if iv is None:
                continue
            zl, zh = iv
            e = T / 2 + 0.8                                   # Schlitzkanten müssen noch im Holz liegen
            iv2 = ST.bereich(lambda z: rho(z) - max(math.hypot(abs(ca), abs(cb) + e),
                                                    math.hypot(abs(ca) + e, abs(cb))), z0, H)
            if iv2 is not None and iv2[1] - iv2[0] >= L_min:
                kreuz[(i, j)] = (zl, zh)
            else:                                             # zu kurz: Rippe A dort kürzen
                bound = abs(cb) - T / 2 - 1.2
                if cb > 0:
                    trim[i][1] = min(trim[i][1], bound)
                else:
                    trim[i][0] = max(trim[i][0], -bound)

    def profil(c: float):
        iv = ST.bereich(lambda z: rho(z) - abs(c), z0, H)
        if iv is None:
            return None
        a, b = iv
        N = 160
        zs = [a + (b - a) * (1 - math.cos(math.pi * k / N)) / 2 for k in range(N + 1)]
        halb = lambda z: math.sqrt(max(0.0, rho(z) ** 2 - c * c))
        right = [(halb(z), z) for z in zs]
        if right[0][0] > 0.05:                                # flacher Boden
            right.insert(0, (0.0, a))
        if right[-1][0] > 0.05:
            right.append((0.0, b))
        left = [(-x, z) for x, z in reversed(right)]
        return right + left[1:-1]

    asm = Assembly(name, params=dict(form=form, durchmesser=D, hoehe=round(H - z0, 1), rippen=n, abstand=d))
    A, B = [], []
    for i, c in enumerate(cs):
        p = profil(c)
        if p is None:
            raise ValueError("Rippe ohne Fläche – weniger Rippen wählen")
        lo, hi = trim[i]
        if lo > -1e8 or hi < 1e8:
            p = ST.clip_band(p, lo, hi)
        A.append(ST.Rippe(f"A{i + 1}", p, f"A{i + 1}" if beschriften else ""))
        B.append(ST.Rippe(f"B{i + 1}", profil(c), f"B{i + 1}" if beschriften else ""))
    for (i, j), (zl, zh) in sorted(kreuz.items()):
        zm = (zl + zh) / 2
        A[i].schlitz(f"b{j + 1}", cs[j], zm, True, (zm, zh))       # A: von oben
        B[j].schlitz(f"a{i + 1}", cs[i], zm, False, (zl, zm))      # B: von unten
    cap = max(3.0, min(6.0, d * 0.22))
    for rip in A + B:
        if not rip.schlitze:
            raise ValueError(f"Rippe {rip.name} kreuzt keine andere – weniger Rippen wählen")
        asm.parts.append(rip.teil(T, cap))
    for (i, j) in sorted(kreuz):
        asm.connect(f"A{i + 1}:b{j + 1}", f"B{j + 1}:a{i + 1}")

    asm.notes.append(f"{2 * n} Rippen, {len(kreuz)} Kreuzungen. Die A-Rippen haben ihre Schlitze oben, die "
                     "B-Rippen unten.")
    asm.notes.append("Zusammenbau: alle A-Rippen nebeneinander hinstellen (A1 bis A" + str(n) + " der Reihe nach), "
                     "dann jede B-Rippe von oben quer darüber schieben – B1 an Schlitz b1 und so weiter. "
                     "Gleichmäßig von beiden Enden her drücken, nicht verkanten.")
    if T > 3.5 and n > 6:
        asm.notes.append("Tipp: Bei dickem Material und vielen Rippen wird es eng – lieber 3 mm nehmen.")
    return asm


def _platzierung(asm, cfg, kw):
    """Für Vorschaubilder: Rippen als 3D-Polygone (A in Ebene x = c, B in Ebene y = c)."""
    n = int(asm.params["rippen"])
    d = asm.params["abstand"]
    cs = [(k - (n - 1) / 2) * d for k in range(n)]
    out = []
    for p in asm.parts:
        c = cs[int(p.name[1:]) - 1]
        if p.name[0] == "A":
            out.append([(c, u, z) for u, z in p.outline])
        else:
            out.append([(u, c, z) for u, z in p.outline])
    return out
