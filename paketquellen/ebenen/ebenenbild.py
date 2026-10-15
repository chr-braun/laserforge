"""
Ebenenbild – mehrlagiges Schneidebild (Schattenbox) aus 3 bis 6 hintereinander stehenden Ebenen.

Jede Ebene ist ein Rahmen mit einem Teil der Szene: hinten Berge und ferner Wald, in der Mitte der Hirsch,
vorn große Fichten. Hinter allem steht die Rückwand mit Mond und Sternen als Durchbrüchen – mit einer
Lichterkette dahinter leuchtet das Bild.

Aufbau
  sockel   alle Ebenen stecken mit Zapfen in einer Sockelplatte mit Schlitzen (Abstand frei wählbar)
  stapel   Ebenen und Abstandsrahmen liegen aufeinander, vier Vierkantstifte halten alles zusammen
"""
from __future__ import annotations

import math
import os
import sys
from typing import List

from steckwerk import Assembly, JointFeature, Part, oriented
from models import _deko as dk
from models._font import STYLES, unsupported
from pakete import bibliothek, flag, integer, num, sel, txt

_here = os.path.dirname(os.path.abspath(__file__))


def _sub(name: str):
    import importlib.util
    path = os.path.join(_here, name + ".py")
    key = "swpaket_ebenen_" + name
    mod = sys.modules.get(key)
    if mod is None or getattr(mod, "__file__", None) != path:
        spec = importlib.util.spec_from_file_location(key, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[key] = mod
        spec.loader.exec_module(mod)
    return mod


E = bibliothek("verzierungen").E
S = _sub("_szenen")
K = E.K

SZENEN = [("winterwald", "Hirsch im Winterwald"), ("winterdorf", "Winterdorf mit Kirche"),
          ("spukschloss", "Spukschloss mit Hexe"),
          ("weihnachtsnacht", "Weihnachtsnacht mit Rentierschlitten")]
AUFBAU = [("sockel", "stehend im Sockel"), ("stapel", "gestapelt mit Steckstiften")]
RUECKWAND = [("himmel", "Mond und Sterne"), ("glatt", "geschlossen"), ("keine", "ohne Rückwand")]

INFO = dict(
    label="Ebenenbild",
    group="Mehrlagig",
    desc="Mehrlagiges Schneidebild: 3–6 Ebenen hintereinander ergeben eine Szene mit Tiefe, "
         "Mond und Sterne leuchten mit Licht dahinter.",
    params=[
        num("width", "Breite", 180, 100, 400),
        num("height", "Höhe", 220, 100, 400),
        sel("form", "Form", E.FORMEN, "bogen"),
        sel("szene", "Szene", SZENEN, "winterwald"),
        integer("ebenen", "Ebenen", 5, 3, 6, help="ohne Rückwand"),
        sel("aufbau", "Aufbau", AUFBAU, "sockel"),
        num("abstand", "Abstand der Ebenen", 8, 3, 30, help="beim Stapel auf ganze Abstandsrahmen gerundet"),
        num("rand", "Rahmenbreite", 12, 8, 40),
        sel("rueckwand", "Rückwand", RUECKWAND, "himmel"),
        txt("text", "Text unten auf dem Rahmen", "", "leer = ohne", section="Schrift und Beschriftung"),
        sel("schrift", "Schrift", [(s, s) for s in STYLES], "normal", section="Schrift und Beschriftung"),
        sel("schreibweise", "Schreibweise", dk.FONT_CASES, "gross", section="Schrift und Beschriftung"),
    ],
)

UEBERSETZUNG = {"en": {
    "Mehrlagig": "Multi-layer",
    "Ebenenbild": "Layered picture",
    "Mehrlagiges Schneidebild: 3–6 Ebenen hintereinander ergeben eine Szene mit Tiefe, Mond und Sterne leuchten mit Licht dahinter.":
        "Multi-layer cut picture: 3–6 layers one behind the other create a scene with depth; moon and stars glow with a light behind.",
    "Hirsch im Winterwald": "Stag in the winter forest", "Winterdorf mit Kirche": "Winter village with church",
    "Spukschloss mit Hexe": "Haunted castle with witch",
    "Weihnachtsnacht mit Rentierschlitten": "Christmas night with reindeer sleigh",
    "stehend im Sockel": "standing in a base", "gestapelt mit Steckstiften": "stacked with pegs",
    "Mond und Sterne": "Moon and stars", "geschlossen": "closed", "ohne Rückwand": "no back panel",
    "Szene": "Scene", "Ebenen": "Layers", "ohne Rückwand ": "without back panel", "Aufbau": "Construction",
    "Abstand der Ebenen": "Layer spacing", "beim Stapel auf ganze Abstandsrahmen gerundet": "rounded to whole spacer frames when stacked",
    "Rahmenbreite": "Frame width", "Rückwand": "Back panel", "Text unten auf dem Rahmen": "Text at the bottom of the frame",
    "Rundbogen": "Round arch", "Spitzbogen (gotisch)": "Pointed arch (gothic)", "Rechteck, abgerundet": "Rectangle, rounded",
}}


def _check(form, szene, aufbau, rueckwand, ebenen, text, schrift):
    dk.check_choice("Form", form, E.FORMEN)
    dk.check_choice("Szene", szene, SZENEN)
    dk.check_choice("Aufbau", aufbau, AUFBAU)
    dk.check_choice("Rückwand", rueckwand, RUECKWAND)
    if not 3 <= int(ebenen) <= 6:
        raise ValueError("Ebenen: 3 bis 6")
    bad = unsupported(text or "")
    if bad:
        raise ValueError(f"Zeichen {''.join(bad)!r} gibt es in der Gravurschrift nicht")
    if schrift not in STYLES:
        raise ValueError(f"Schrift {schrift!r} unbekannt")


def build(cfg, name="ebenenbild", width=180.0, height=220.0, form="bogen", szene="winterwald", ebenen=5,
          aufbau="sockel", abstand=8.0, rand=12.0, rueckwand="himmel", text="", schrift="normal",
          schreibweise="gross"):
    _check(form, szene, aufbau, rueckwand, ebenen, text, schrift)
    T = cfg.T
    W, H = cfg.s(width), cfg.s(height)
    rand = max(float(rand), T + 2 * cfg.min_web + 4.0)
    n = int(ebenen)
    if W < 4 * rand + 40 or H < 4 * rand + 40:
        raise ValueError("Das Bild ist für diese Rahmenbreite zu klein – größer machen oder schmaleren Rahmen wählen")
    tw = max(cfg.tab_factor * T, 8.0)
    xs = [-0.30 * W, 0.30 * W]
    flach = 2 * (0.30 * W + tw)
    outer = oriented(E.aussen(form, W, H, flach), True)
    inner = oriented(E.innen(form, W, H, rand, flach), True)
    Wi, Hi = W - 2 * rand, H - 2 * rand
    notes: List[str] = []

    lw = E.Leinwand((-W / 2, 0, W / 2, H), px=0.1 if max(W, H) <= 260 else 0.14)
    bereich = lw.flaechen([inner])
    szene_fn, himmel_fn = S.SZENEN[szene]
    figs = szene_fn(Wi, Hi, n, cfg.seed)

    asm = Assembly(name, params=dict(width=W, height=H, form=form, szene=szene, ebenen=n, aufbau=aufbau,
                                     abstand=abstand, rand=rand, rueckwand=rueckwand, text=text))

    def platte(pname: str, holes, oben=None):
        out, tabs = (E.zapfen_einsetzen(outer, xs, tw, T) if aufbau == "sockel" else (outer, []))
        part = Part(pname, out)
        for h in holes:
            part.add_hole(h)
        for k, (seite, x, pts) in enumerate(tabs):
            part.features.append(JointFeature(f"z{k}", "tab", tw, T, pos=0.0, points=pts))
        return part

    plates: List[Part] = []                         # vorne → hinten
    for d, fig in enumerate(figs):                  # figs: hinten → vorne
        fig = fig.place(0, rand, 1.0)
        mat = lw.figur(fig)
        label = f"{name}_ebene{n - d}"
        holes = E.durchbrueche(lw, bereich, mat, cfg.min_web, cfg.kerf, notes, label)
        plates.insert(0, platte(label, holes))
    if rueckwand != "keine":
        holes = []
        if rueckwand == "himmel":
            loch, keep = himmel_fn(Wi, Hi, cfg.seed)
            loch = loch.place(0, rand, 1.0)
            mat = lw.figur(keep.place(0, rand, 1.0))
            lr = lw.figur(loch)
            from motive import Raster
            holes = E.durchbrueche(lw, E._and(lr, bereich), mat, cfg.min_web, cfg.kerf, notes, f"{name}_rueckwand")
        plates.append(platte(f"{name}_rueckwand", holes))
    # Text auf dem vorderen Rahmen
    if text.strip():
        front = plates[0]
        # nur auf dem Rahmenband setzen: Hilfsteil ohne die vielen Bilddurchbrüche (viel schneller)
        band = Part(front.name, front.outline)
        band.add_hole(inner)
        cv = dk.Canvas(band, margin=1.5, seed=cfg.seed)
        y_band = rand
        bx = 0.30 * W - T / 2 - 2.0 if aufbau == "stapel" else 0.42 * W     # Stifte freihalten
        box = (-bx, 1.5, bx, y_band - 1.5)
        if dk.sign(cv, text, "ohne", [box], schrift, schreibweise, min_h=3.0, max_cap=0.6 * rand,
                   anchor="mitte", tol=cfg.arc_tolerance) is None:
            raise ValueError(f"Text {text!r} passt nicht auf den Rahmen – kürzer fassen oder breiteren Rahmen wählen")
        front.engrave += band.engrave
    asm.parts += plates

    if aufbau == "sockel":
        gap = max(float(abstand), cfg.min_web + 0.5)
        reihen = [k * (T + gap) for k in range(len(plates))]
        base, ids = E.sockelplatte(f"{name}_sockel", W + 2 * T, reihen, xs, tw, T, max(8.0, rand * 0.8))
        # Slot-Positionen eindeutig: Reihe k, Zapfen j → pos k*100 + j
        for k, p in enumerate(plates):
            for j, f in enumerate(p.features):
                f.pos = k * 100.0 + j
                asm.connect(f"{p.name}:{f.id}", f"{base.name}:s{k}_{j}")
        asm.parts.append(base)
        asm.notes.append(f"{name}: Ebenen von hinten nach vorn in den Sockel stecken – die Rückwand in die "
                         "hinterste Schlitzreihe, Ebene 1 nach vorn.")
    else:
        # Stapel: zwischen den Ebenen Abstandsrahmen, vier Vierkantstifte durch alle Lagen
        g = max(1, int(round(float(abstand) / T)))
        stapel: List[Part] = []
        for k, p in enumerate(plates):
            stapel.append(p)
            if k < len(plates) - 1:
                for j in range(g):
                    r = Part(f"{name}_abstand{k + 1}_{j + 1}", outer)
                    r.add_hole(inner)
                    stapel.append(r)
        y_seite = min(0.55 * H, H - 0.5 * W) if form in ("bogen", "spitzbogen") else 0.5 * H
        y_seite = max(y_seite, rand + 3 * T)
        lo, ro = E.quer_x(outer, y_seite)
        li, ri = E.quer_x(inner, y_seite)
        punkte = [(-0.30 * W, rand / 2), (0.30 * W, rand / 2), ((lo + li) / 2, y_seite), ((ro + ri) / 2, y_seite)]
        for j, (x, y) in enumerate(punkte):
            for p in stapel:
                E.stiftloch(p, f"b{j}", x, y, T, float(j))
        asm.parts[:] = [q for q in asm.parts if q not in plates] + stapel
        for j in range(len(punkte)):
            st = E.stift(f"{name}_stift{j + 1}", len(stapel), T, float(j))
            asm.parts.append(st)
            for k, p in enumerate(stapel):
                asm.connect(f"{st.name}:l{k}", f"{p.name}:b{j}")
        asm.notes.append(f"{name}: Stapel von vorn nach hinten: Ebene 1, {g} Abstandsrahmen, Ebene 2 … bis zur "
                         f"Rückwand; die vier Vierkantstifte ({len(stapel) * T:.0f} mm) durch alle Lagen schieben. "
                         "Das Bild steht auf der flachen Unterkante.")
    asm.notes.append(f"{name}: Mit einer LED-Lichterkette hinter der Rückwand leuchten Mond und Sterne; "
                     "die Ebenen bekommen Tiefe, wenn du sie unterschiedlich hell lasierst (hinten heller).")
    asm.notes += notes
    return asm
