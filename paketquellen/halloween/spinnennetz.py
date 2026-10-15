"""
Spinnennetz – filigranes Netz als Fensterbild, Anhänger, Ecknetz für die Fensterecke oder Untersetzer.

Speichen mit leicht unregelmäßigen Winkeln, zwischen den Speichen durchhängende Fangfäden, eine dichte
Nabe, Tautropfen und auf Wunsch gerissene Fäden. Eine Kreuzspinne sitzt im Netz, weitere hängen an
ihrem Faden darunter. Als Untersetzer bleibt die Fläche geschlossen und das Netz wird graviert.
"""
from __future__ import annotations

import math
import os
import sys
from typing import List

from steckwerk import Assembly, Part, oriented
from pakete import flag, integer, num, sel

_here = os.path.dirname(os.path.abspath(__file__))


def _sub(name: str):
    import importlib.util
    path = os.path.join(_here, name + ".py")
    key = "swpaket_halloween_" + name
    mod = sys.modules.get(key)
    if mod is None or getattr(mod, "__file__", None) != path:
        spec = importlib.util.spec_from_file_location(key, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[key] = mod
        spec.loader.exec_module(mod)
    return mod


SP = _sub("_spuk")
K = SP.K

FORMEN = [("rund", "rund (Fensterbild/Anhänger)"), ("ecke", "Ecknetz (Viertelkreis)"),
          ("untersetzer", "Untersetzer (Netz graviert)")]
ECKEN = [("links", "linke obere Ecke"), ("rechts", "rechte obere Ecke")]
FEINHEIT = [("fein", "fein (für 2 mm Holz)"), ("mittel", "mittel"), ("kraeftig", "kräftig (für 4 mm)")]
_DICKE = dict(fein=0.0, mittel=0.35, kraeftig=0.8)

INFO = dict(
    label="Spinnennetz",
    group="Halloween",
    desc="Filigranes Netz mit durchhängenden Fäden, Tautropfen und Kreuzspinnen – rund mit Öse, als Ecknetz "
         "für die Fensterecke oder als Untersetzer mit graviertem Netz.",
    params=[
        sel("form", "Form", FORMEN, "rund"),
        sel("ecke", "Ecke", ECKEN, "links", when={"form": ["ecke"]}),
        num("groesse", "Größe", 160, 60, 280, help="Durchmesser, beim Ecknetz die Kantenlänge"),
        integer("ringe", "Ringe (Fangfäden)", 7, 3, 12),
        integer("speichen", "Speichen", 12, 6, 24, help="beim Ecknetz auf den Viertelkreis verteilt: halb so viele"),
        sel("feinheit", "Feinheit", FEINHEIT, "mittel"),
        integer("spinnen", "Spinnen", 2, 0, 3, help="die erste sitzt im Netz, weitere hängen am Faden darunter"),
        flag("riss", "Gerissene Fäden", True),
        flag("tropfen", "Tautropfen", True),
        flag("oese", "Öse zum Aufhängen", True, when={"form": ["rund", "ecke"]}),
    ],
)

NOTIZ_RINGE = ("Für diese Größe waren zu viele Ringe gewählt – es wurden so viele geschnitten, wie mit sicheren "
               "Stegen hineinpassen.")

NOTIZ_SPEICHEN = ("Für diese Größe waren zu viele Speichen gewählt – es wurden weniger geschnitten, damit die Mitte "
                  "offen bleibt.")

UEBERSETZUNG = {"en": {
    NOTIZ_SPEICHEN: "Too many spokes were chosen for this size – fewer were cut so the centre stays open.",
    NOTIZ_RINGE: "Too many rings were chosen for this size – as many were cut as fit with safe webs.",
    "Spinnennetz": "Spider web",
    "Filigranes Netz mit durchhängenden Fäden, Tautropfen und Kreuzspinnen – rund mit Öse, als Ecknetz "
    "für die Fensterecke oder als Untersetzer mit graviertem Netz.":
        "Filigree web with sagging threads, dew drops and garden spiders – round with a loop, as a corner web for "
        "the window corner or as a coaster with an engraved web.",
    "Form": "Shape", "rund (Fensterbild/Anhänger)": "round (window picture/pendant)",
    "Ecknetz (Viertelkreis)": "corner web (quarter circle)", "Untersetzer (Netz graviert)": "coaster (engraved web)",
    "Ecke": "Corner", "linke obere Ecke": "top left corner", "rechte obere Ecke": "top right corner",
    "Größe": "Size", "Durchmesser, beim Ecknetz die Kantenlänge": "diameter; edge length for the corner web",
    "Ringe (Fangfäden)": "Rings (capture threads)", "Speichen": "Spokes",
    "beim Ecknetz auf den Viertelkreis verteilt: halb so viele": "corner web: half as many, spread over the quarter circle",
    "Feinheit": "Fineness", "fein (für 2 mm Holz)": "fine (for 2 mm wood)", "mittel": "medium",
    "kräftig (für 4 mm)": "bold (for 4 mm)", "Spinnen": "Spiders",
    "die erste sitzt im Netz, weitere hängen am Faden darunter": "the first sits in the web, others hang on a thread below",
    "Gerissene Fäden": "Torn threads", "Tautropfen": "Dew drops", "Öse zum Aufhängen": "Hanging loop",
    "Spinnennetz: Größe muss zwischen 60 und 280 mm liegen": "Spider web: size must be between 60 and 280 mm",
    "Spinnennetz: 3 bis 12 Ringe": "Spider web: 3 to 12 rings",
    "Spinnennetz: 6 bis 24 Speichen": "Spider web: 6 to 24 spokes",
    "Spinnennetz: 0 bis 3 Spinnen": "Spider web: 0 to 3 spiders",
    "Spinnennetz: zu viele Ringe für diese Größe – weniger Ringe, feinere Fäden oder ein größeres Netz wählen":
        "Spider web: too many rings for this size – choose fewer rings, finer threads or a larger web",
    "Netz an der Öse an einen Saugnapfhaken oder Faden hängen. Feine Fäden vorsichtig aus der Platte lösen – "
    "mit einem Zahnstocher von hinten drücken, nicht ziehen.":
        "Hang the web by its loop on a suction hook or thread. Release the fine threads carefully from the sheet – "
        "push from behind with a toothpick, do not pull.",
    "Ecknetz mit der Ecke in die Fensterecke setzen (Öse an einen Saugnapf oder mit Klebepunkten befestigen).":
        "Put the corner web into the window corner (loop on a suction cup, or fix it with adhesive dots).",
    "Untersetzer: Gravur dunkel beizen oder mit Öl einlassen, dann tritt das Netz deutlich hervor.":
        "Coaster: stain the engraving dark or oil it, then the web stands out clearly.",
    "Tipp: Schwarz lasiert vor einem hellen Fenster oder weiß lasiert vor dunklem Hintergrund.":
        "Tip: stained black in front of a bright window, or white in front of a dark background.",
}}


def _haengespinnen(f, cfg, n, starts, R, w, rng, size0):
    """Spinnen an Fäden unter den Ankerpunkten starts = [(x, y)] (von unten nach oben sortiert)."""
    for k in range(n):
        if k >= len(starts):
            break
        x, y = starts[k]
        L = R * (0.32 + 0.14 * k + 0.05 * rng.random())
        size = size0 * (1 - 0.15 * k)
        sp_top = y - L
        # Faden mit leichter Pendelkurve
        f.line(K.bez((x, y + w), (x + 0.03 * R, y - L * 0.5), (x, sp_top), 12), w * 0.95)
        f.merge(SP.spinne(size, cfg, x, sp_top - 0.09 * size, 0.0))


def build(cfg, name: str = "spinnennetz", form: str = "rund", ecke: str = "links", groesse: float = 160.0,
          ringe: int = 7, speichen: int = 12, feinheit: str = "mittel", spinnen: int = 2, riss: bool = True,
          tropfen: bool = True, oese: bool = True):
    from models import _deko as dk
    dk.check_choice("Form", form, FORMEN)
    dk.check_choice("Ecke", ecke, ECKEN)
    dk.check_choice("Feinheit", feinheit, FEINHEIT)
    S = cfg.s(groesse)
    ringe, speichen, spinnen = int(ringe), int(speichen), int(spinnen)
    if not 60 <= S <= 280:
        raise ValueError("Spinnennetz: Größe muss zwischen 60 und 280 mm liegen")
    if not 3 <= ringe <= 12:
        raise ValueError("Spinnennetz: 3 bis 12 Ringe")
    if not 6 <= speichen <= 24:
        raise ValueError("Spinnennetz: 6 bis 24 Speichen")
    if not 0 <= spinnen <= 3:
        raise ValueError("Spinnennetz: 0 bis 3 Spinnen")
    w = SP.wmin(cfg) + _DICKE[feinheit] + max(0.0, (S - 120) * 0.003)
    R = S / 2 if form != "ecke" else S * 0.96
    hub = max(0.07 * R, 2.2 * w)
    abstand = 2.2 * w + 2.0 if form != "untersetzer" else 2.5    # Gravur darf dichter liegen
    notes: List[str] = []
    if (R - hub) / ringe < abstand:
        passt = int((R - hub) / abstand)
        if passt < 3 and (R - hub) / 3 >= 2.0 * w + 1.5:   # drei Ringe gehen noch, etwas enger
            passt = 3
        if passt < 3:
            raise ValueError("Spinnennetz: zu viele Ringe für diese Größe – weniger Ringe, feinere Fäden oder ein "
                             "größeres Netz wählen")
        ringe = passt
        notes.append(NOTIZ_RINGE)
    if form != "untersetzer":                              # Nabe darf nicht das halbe Netz füllen
        span, r_ = (SP.TAU, 0.93 * R) if form == "rund" else (math.pi / 2, R)
        pro = 1 if form == "rund" else 2
        maxsp = int(0.4 * r_ * span / (w + 3.2)) * pro
        if speichen > maxsp:
            speichen = max(6, maxsp)
            notes.append(NOTIZ_SPEICHEN)
    rng = K.rng(cfg.seed, "spinnennetz")
    asm = Assembly(name, params=dict(form=form, groesse=S, ringe=ringe, speichen=speichen, feinheit=feinheit,
                                     spinnen=spinnen))
    if form == "untersetzer":
        asm.parts.append(_untersetzer(cfg, f"{name}_untersetzer", R, ringe, speichen, spinnen, riss, rng))
        asm.notes.extend(notes)
        asm.notes.append("Untersetzer: Gravur dunkel beizen oder mit Öl einlassen, dann tritt das Netz deutlich hervor.")
        return asm
    loecher = []
    if form == "rund":
        R0 = R * 0.93                                       # Platz für die Ankerfäden
        f, ends, outer, angs, radii = SP.netz(0.0, 0.0, R0, math.pi / 2, math.pi / 2 + SP.TAU, ringe, speichen, w,
                                              cfg.seed, riss, tropfen, voll=True)
        gr = f.gravur
        for (x, y), a in zip(ends, angs):                  # Ankerfäden mit Knötchen
            if abs(math.sin(a) - 1) < 1e-6 and oese:
                continue
            e = (x + 0.06 * R * math.cos(a), y + 0.06 * R * math.sin(a))
            f.line([(x, y), e], w)
            f.add(K.circle(e[0], e[1], w * 0.9, 16))
        if spinnen:
            a = math.radians(-35)
            r0 = radii[max(0, ringe // 2 - 1)]
            sp_ = (0.50 * R0, cfg, r0 * math.cos(a), r0 * math.sin(a), a - math.pi / 2 + 0.35)
            f.merge(SP.spinne_frei(*sp_))
            f.merge(SP.spinne(*sp_))
            low = sorted(outer, key=lambda p: p[1])
            starts = [p for p in low if p[0] > 0.25 * R0][:1] + [p for p in low if p[0] < -0.25 * R0][:1]
            _haengespinnen(f, cfg, spinnen - 1, starts, R0, w, rng, 0.40 * R0)
        if oese:
            d = max(3.0, min(6.0, 0.03 * S))
            ring = max(1.6 * SP.wmin(cfg), 2.4)
            cy = R0 + d / 2 + ring * 0.7
            f.line([(0.0, R0 - w), (0.0, cy)], 1.6 * w)
            loecher.append((0.0, cy, d))
        tag = "rund"
    else:
        n = max(3, speichen // 2)
        f, ends, outer, angs, radii = SP.netz(0.0, 0.0, R, -math.pi / 2, 0.0, ringe, n, w, cfg.seed, riss, tropfen,
                                              voll=False)
        gr = f.gravur
        # kräftige Randfäden entlang der Fensterkanten
        f.line([(0.0, 0.0), (R * 1.02, 0.0)], 1.5 * w)
        f.line([(0.0, 0.0), (0.0, -R * 1.02)], 1.5 * w)
        if spinnen:
            a = math.radians(-45)
            r0 = radii[max(0, ringe // 2)]
            sp_ = (0.42 * R, cfg, r0 * math.cos(a), r0 * math.sin(a), a - math.pi / 2 + 0.25)
            f.merge(SP.spinne_frei(*sp_))
            f.merge(SP.spinne(*sp_))
            starts = sorted(outer, key=lambda p: p[1])
            starts = [p for p in starts if p[0] > 0.25 * R][:3]
            starts.sort(key=lambda p: p[0])
            _haengespinnen(f, cfg, spinnen - 1, starts[::max(1, len(starts) - 1)], R * 0.6, w, rng, 0.24 * R)
        if oese:
            d = max(3.0, min(6.0, 0.03 * S))
            ring = max(1.6 * SP.wmin(cfg), 2.4)
            o = d / 2 + ring + 0.5
            f.add(K.circle(o, -o, d / 2 + ring, 40))
            loecher.append((o, -o, d))
        if ecke == "rechts":
            f = f.place(0.0, 0.0, 1.0, flip=True)
            loecher = [(-x, y, d) for x, y, d in loecher]
        tag = f"ecke_{ecke}"
    if form == "ecke" and ecke == "rechts":
        gr = [([(-x, y) for x, y in pts], c) for pts, c in gr]
    part = SP.teil(f"{name}_{tag}", f, cfg, notes, loecher)
    SP.gravur(part, gr, cfg.seed)
    asm.parts.append(part)
    for t in dict.fromkeys(notes):
        asm.notes.append(t)
    if form == "ecke":
        asm.notes.append("Ecknetz mit der Ecke in die Fensterecke setzen (Öse an einen Saugnapf oder mit Klebepunkten "
                         "befestigen).")
    else:
        asm.notes.append("Netz an der Öse an einen Saugnapfhaken oder Faden hängen. Feine Fäden vorsichtig aus der "
                         "Platte lösen – mit einem Zahnstocher von hinten drücken, nicht ziehen.")
    asm.notes.append("Tipp: Schwarz lasiert vor einem hellen Fenster oder weiß lasiert vor dunklem Hintergrund.")
    return asm


def _untersetzer(cfg, name, R, ringe, speichen, spinnen, riss, rng) -> Part:
    """Geschlossene Scheibe mit Bogenrand; Netz und Spinne graviert."""
    from steckwerk import point_in_polygon
    n = speichen
    angs = [math.pi / 2 + SP.TAU * i / n for i in range(n)]
    P = lambda r, a: (r * math.cos(a), r * math.sin(a))
    outline = []
    for i in range(n):
        a, b = angs[i], angs[(i + 1) % n] + (SP.TAU if i == n - 1 else 0.0)
        pa, pb = P(R, a), P(R, b)
        c = SP.lerp(SP.lerp(pa, pb, 0.5), (0.0, 0.0), 0.10 * (2 * math.pi / n))
        outline += K.bez(pa, c, pb, 16)[:-1]
    part = Part(name, oriented(outline, True))
    lines = []
    Ri = R - 3.0
    inner = []
    for i in range(n):
        a, b = angs[i], angs[(i + 1) % n] + (SP.TAU if i == n - 1 else 0.0)
        pa, pb = P(Ri, a), P(Ri, b)
        c = SP.lerp(SP.lerp(pa, pb, 0.5), (0.0, 0.0), 0.10 * (2 * math.pi / n))
        inner += K.bez(pa, c, pb, 16)[:-1]
    lines.append((inner, True))
    hub = 0.08 * Ri
    radii = [hub + (Ri * 0.92 - hub) * ((k + 1) / ringe) ** 0.92 for k in range(ringe)]
    spider_polys = []
    if spinnen:
        a = math.radians(-40)
        r0 = radii[max(0, ringe // 2 - 1)]
        fig = SP.spinne(0.34 * Ri, cfg, r0 * math.cos(a), r0 * math.sin(a), a - math.pi / 2 + 0.35, zeichnung=True)
        x0, y0, x1, y1 = fig.bbox()
        lw = SP.E.Leinwand((x0 - 2, y0 - 2, x1 + 2, y1 + 2), 0.08)
        for ar in lw.konturen(lw.figur(fig)):
            spider_polys.append(ar["aussen"])
            for h in ar["loecher"]:
                lines.append((h, True))
            lines.append((ar["aussen"], True))
    for i in range(n):
        lines.append(([P(hub * 0.5, angs[i]), P(Ri * 0.97, angs[i])], False))
    for k, r in enumerate(radii):
        for i in range(n):
            if riss and k in (ringe // 2,) and i % 5 == 2:
                continue
            a, b = angs[i], angs[(i + 1) % n] + (SP.TAU if i == n - 1 else 0.0)
            pa, pb = P(r, a), P(r, b)
            c = SP.lerp(SP.lerp(pa, pb, 0.5), (0.0, 0.0), 0.20 * (b - a))
            lines.append((K.bez(pa, c, pb, 14), False))
    lines.append((K.circle(0, 0, hub * 0.6, 24), True))
    from models import _deko as dk
    cv = dk.Canvas(part, margin=1.0, seed=cfg.seed)
    for sp in spider_polys:
        cv.block(sp, 0.5)
    spider_set = {id(p) for p in spider_polys}
    for pts, closed in lines:
        if spider_polys and any(pts is sp for sp in spider_polys):
            continue
        cv.draw(list(pts), closed)
    # Spinne selbst (Umriss und Zeichnung) direkt gravieren
    for sp in spider_polys:
        part.add_engrave(sp, True)
    for pts, closed in lines:
        if closed and spider_polys and any(point_in_polygon(pts[0], sp) for sp in spider_polys) and \
                not any(pts is sp for sp in spider_polys):
            part.add_engrave(pts, True)
    return part
