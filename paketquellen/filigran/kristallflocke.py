"""
Kristall-Schneeflocken – jede Flocke anders, gewachsen wie ein echter Eiskristall.

Sechs Arme mit Farnzweigen (Dendriten), kleinen Sechseckplatten, Querriegeln und Spitzen. Ein Zufallsgenerator
setzt die Arme aus diesen Bausteinen zusammen; die Variante bestimmt die Flocke, bei mehreren Stück ist jede
Flocke einzigartig. Zweige bleiben in ihrem Sechstel, damit sich benachbarte Arme nie berühren.
"""
from __future__ import annotations

import math
import os
import sys
from typing import List

from steckwerk import Assembly, JointFeature, Part
from pakete import bibliothek, flag, integer, num, sel

_here = os.path.dirname(os.path.abspath(__file__))


def _sub(name: str):
    import importlib.util
    path = os.path.join(_here, name + ".py")
    key = "swpaket_filigran_" + name
    mod = sys.modules.get(key)
    if mod is None or getattr(mod, "__file__", None) != path:
        spec = importlib.util.spec_from_file_location(key, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[key] = mod
        spec.loader.exec_module(mod)
    return mod


E = bibliothek("verzierungen").E
FG = _sub("_filigran")
K = E.K
P = FG.P
AL = math.pi / 3                                          # 60° zwischen den Armen

ARTEN = [("gemischt", "gemischt (jede anders)"), ("farn", "Farn (Dendrit)"), ("sternplatte", "Sternplatte"),
         ("feder", "Federstern")]
FEINHEIT = [("fein", "fein (für 1,5–2 mm Holz)"), ("mittel", "mittel"), ("kraeftig", "kräftig (für 4 mm)")]

INFO = dict(
    label="Kristall-Schneeflocken",
    group="Filigran",
    desc="Filigrane Eiskristalle mit Farnzweigen, Sechseckplatten und Spitzen – jede Flocke wächst anders. "
         "Als Anhänger oder zum Stecken über Kreuz.",
    params=[
        sel("art", "Kristallart", ARTEN, "gemischt"),
        num("groesse", "Durchmesser", 90, 40, 250),
        sel("feinheit", "Feinheit", FEINHEIT, "mittel"),
        integer("variante", "Variante", 1, 1, 999, help="jede Zahl ergibt eine andere Flocke"),
        integer("anzahl", "Anzahl", 1, 1, 24, help="mehrere Flocken sind alle verschieden"),
        flag("oese", "Öse zum Aufhängen", True),
        flag("steckbar", "3D: zwei Teile über Kreuz", False),
    ],
)

UEBERSETZUNG = {"en": {
    "Kristall-Schneeflocken": "Crystal snowflakes", "Filigran": "Filigree",
    "Filigrane Eiskristalle mit Farnzweigen, Sechseckplatten und Spitzen – jede Flocke wächst anders. "
    "Als Anhänger oder zum Stecken über Kreuz.":
        "Filigree ice crystals with fern branches, hexagonal plates and tips – every flake grows differently. "
        "As a pendant or slotted crosswise.",
    "Kristallart": "Crystal type", "Durchmesser": "Diameter", "Feinheit": "Fineness", "Variante": "Variant",
    "jede Zahl ergibt eine andere Flocke": "every number gives a different flake", "Anzahl": "Count",
    "mehrere Flocken sind alle verschieden": "several flakes are all different",
    "Öse zum Aufhängen": "Hanging loop", "3D: zwei Teile über Kreuz": "3D: two pieces slotted crosswise",
    "gemischt (jede anders)": "mixed (each different)", "Farn (Dendrit)": "Fern (dendrite)",
    "Sternplatte": "Stellar plate", "Federstern": "Feather star", "fein (für 1,5–2 mm Holz)": "fine (for 1.5–2 mm wood)",
    "mittel": "medium", "kräftig (für 4 mm)": "bold (for 4 mm)",
}}

_DICKE = dict(fein=0.0, mittel=0.3, kraeftig=0.7)


# --------------------------------------------------------------------------------------------------
# Wachstum eines Arms (im Keil um die +y-Achse, rechte Hälfte; gespiegelt und 6× gedreht)
# --------------------------------------------------------------------------------------------------

def _lmax(r: float, w: float) -> float:
    """Längster 60°-Zweig ab Radius r, dessen Spitze sicher im eigenen Sechstel bleibt."""
    return max(0.0, 0.70 * r - 1.2 * w)


def _zweig(M, r: float, L: float, rnd, tiefe: int, k: float) -> None:
    """Zweig unter 60° vom Arm, auf Wunsch selbst mit kleinen Seitenzweigen (parallel zum Arm)."""
    if L < 2.5 * M.w:
        return
    b = P(r, 0)
    d = (math.sin(AL), math.cos(AL))
    tip = (b[0] + d[0] * L, b[1] + d[1] * L)
    M.sym([b, tip], k)
    if tiefe > 0:
        m = int(L / (3.2 * M.w))
        for j in range(1, m + 1):
            f = j / (m + 1)
            q = (b[0] + d[0] * L * f, b[1] + d[1] * L * f)
            ls = L * (1 - f) * rnd.uniform(0.35, 0.55)
            if ls > 2.2 * M.w:
                # Seitenzweig parallel zum Hauptarm (nach außen); bleibt im Keil
                M.sym([q, (q[0], q[1] + ls)], k * 0.85)


def _platte(M, r: float, s: float, k: float, rippen: bool) -> None:
    """Kleine Sechseckplatte auf dem Arm (Mittelpunkt bei Radius r, Umkreis s), auf Wunsch mit Rippen."""
    pts = [(s * math.cos(a), r + s * math.sin(a)) for a in [i * AL + math.pi / 6 for i in range(6)]]
    for j in range(6):
        a = -2 * math.pi * j / 6
        M.frei(FG.rot(pts + [pts[0]], a), k)
        if rippen:
            for q in pts:
                M.frei(FG.rot([(0.0, r), q], a), k * 0.75)


def _riegel(M, r: float, L: float, k: float) -> None:
    M.sym([P(r, 0), (L, r)], k)


def _arm(M, R: float, art: str, rnd) -> None:
    w = M.w
    d = R / w
    # Kern
    kern = rnd.choice(["hex", "stern", "ring", "platte"]) if art == "gemischt" else {"farn": "ring", "sternplatte": "platte",
                                                                             "feder": "stern"}[art]
    rc = R * rnd.uniform(0.16, 0.24)
    M.perle(0, 0, max(1.6 * w, 0.06 * R))
    if kern == "platte":                                 # große Sternplatte: Sechseck mit Rippen und Innenring
        rc = R * rnd.uniform(0.32, 0.40)
        M.sym([P(rc, 0), P(rc, AL)], 1.05, mirror=False)
        M.sym([P(rc * 0.62, 0), P(rc * 0.62, AL)], 0.85, mirror=False)
        M.sym([P(rc * 0.62, AL / 2), P(rc, AL / 2)], 0.8, mirror=False)
        if d > 26:
            M.sym([P(rc * 0.30, 0), P(rc * 0.30, AL)], 0.8, mirror=False)
            M.sym([P(rc * 0.78, 0), (rc * 0.20, rc * 0.80)], 0.75)
    elif kern == "hex":
        M.sym([P(rc, 0), P(rc, AL)], 1.0, mirror=False)
        if d > 22:
            M.sym([P(rc * 0.55, 0), P(rc * 0.55, AL)], 0.85, mirror=False)
    elif kern == "stern":
        M.sym([P(rc, 0), P(rc * 0.62, AL / 2)], 0.95)
    else:
        M.kreis(rc, 0.95)
    # Hauptarm
    M.sym([P(0, 0), P(R * 0.97, 0)], 1.25, mirror=False)
    # Bausteine entlang des Arms
    r = rc + 1.8 * w
    if art == "farn":
        bau = ["farn"]
    elif art == "sternplatte":
        bau = ["zweig", "platte"]
    elif art == "feder":
        bau = ["feder"]
    else:
        bau = [rnd.choice(["zweig", "platte", "riegel", "farn"]) for _ in range(3 if kern != "platte" else 2)]
        if not {"zweig", "farn"} & set(bau):
            bau[rnd.randrange(len(bau))] = "zweig"
    spitze = rnd.choice(["raute", "platte", "pfeil"]) if art == "gemischt" else {
        "farn": "pfeil", "sternplatte": "platte", "feder": "raute"}[art]
    r_end = R * 0.80
    seg = (r_end - r) / len(bau)
    for b in bau:
        r0, r1 = r, r + seg
        if b == "farn":                                  # dichte Farnzweige, Hüllkurve wie ein Tannenbaum
            step = max(2.6 * w, (r1 - r0) / max(2, int(d / 4)))
            q = r0 + step * 0.5
            while q < r1:
                u = (q - r0) / (r1 - r0)
                L = min(_lmax(q, w), (R - q) * 0.8, R * (0.30 * math.sin(math.pi * (0.25 + 0.75 * u))))
                _zweig(M, q, L, rnd, 1 if d > 30 else 0, 0.85)
                q += step
        elif b == "feder":                               # gleichmäßig kurze Zweige wie eine Feder
            step = max(2.4 * w, (r1 - r0) / max(3, int(d / 3)))
            q = r0 + step * 0.5
            while q < r1:
                L = min(_lmax(q, w), R * 0.16 * (1.15 - 0.6 * (q - r0) / (r1 - r0)))
                _zweig(M, q, L, rnd, 0, 0.8)
                q += step
        elif b == "zweig":
            q = r0 + seg * rnd.uniform(0.35, 0.6)
            _zweig(M, q, min(_lmax(q, w), seg * rnd.uniform(0.9, 1.4)), rnd, 1 if d > 26 else 0, 0.9)
        elif b == "platte":
            s = min(seg * 0.45, R * 0.13)
            if s > 2.2 * w:
                _platte(M, r0 + seg * 0.5, s, 0.85, s > 3.5 * w)
        elif b == "riegel":
            q = r0 + seg * 0.5
            M.sym([P(q, 0), (min(_lmax(q, w) * 0.75, seg * 0.9), q + seg * 0.35)], 0.9)
            M.sym([P(q - seg * 0.3, 0), (min(_lmax(q, w) * 0.5, seg * 0.6), q - seg * 0.05)], 0.85)
        r = r1
    # Spitze
    if spitze == "raute":
        t = [(0, R * 0.80), (R * 0.06, R * 0.88), (0, R * 0.98), (-R * 0.06, R * 0.88)]
        M.sym(t + [t[0]], 0.9, mirror=False)
    elif spitze == "platte":
        _platte(M, R * 0.88, R * 0.09, 0.85, R * 0.09 > 3.5 * w)
    else:
        M.sym([P(R * 0.97, 0), (R * 0.08, R * 0.86)], 0.9)


def _flocke(art: str, R: float, w: float, wmin: float, seed: int):
    rnd = K.rng(seed, "kristall")
    M = FG.Muster(w, 6, wmin=wmin, R=R)
    _arm(M, R, art, rnd)
    return M.figur()


def _teil(cfg, name, art, S, feinheit, seed, oese, achse, notes) -> Part:
    web, kerf, T = cfg.min_web, cfg.kerf, cfg.T
    wmin = web + kerf + 0.45
    w = wmin + _DICKE[feinheit]
    R = S / 2
    fig = _flocke(art, R, w, wmin, seed)
    ro = max(3.0, 0.04 * S)
    top = R
    lw = E.Leinwand((-R - 2, -R - 2, R + 2, R + 2 * ro + 2), 0.08)
    mat = lw.figur(fig)
    if oese:
        lc = (0.0, top + ro - 1.0)
        mat = mat.union(lw.flaechen([K.circle(lc[0], lc[1], ro, 40)]))
        mat = E._andnot(mat, lw.flaechen([K.circle(lc[0], lc[1], ro - max(web + 0.6, 1.4), 32)]))
    if achse:
        bw = T + 2 * (web + kerf + 0.8)
        mat = mat.union(lw.flaechen([K.rect(-bw / 2, -R * 0.97, bw, R * 1.94)]))
    return E.teil_aus_raster(name, lw, mat, web, kerf, notes)


def build(cfg, name: str = "kristallflocke", art: str = "gemischt", groesse: float = 90.0, feinheit: str = "mittel",
          variante: int = 1, anzahl: int = 1, oese: bool = True, steckbar: bool = False):
    from models._shapes import cut_axis_slot
    if art not in dict(ARTEN):
        raise ValueError(f"Unbekannte Kristallart {art!r}")
    S = cfg.s(groesse)
    if S < 14 * (cfg.min_web + cfg.kerf) + 16:
        raise ValueError("Für einen feinen Kristall ist die Flocke zu klein – Durchmesser vergrößern")
    asm = Assembly(name, params=dict(art=art, groesse=S, feinheit=feinheit, variante=variante, anzahl=anzahl,
                                     oese=oese, steckbar=steckbar))
    notes: List[str] = []
    T = cfg.T
    for i in range(anzahl):
        seed = cfg.seed * 1009 + variante * 37 + i * 101
        tag = f"flocke_{variante}" + (f"_{i + 1}" if anzahl > 1 else "")
        if not steckbar:
            asm.parts.append(_teil(cfg, tag, art, S, feinheit, seed, oese, False, notes))
            continue
        for suf, from_top in (("_a", True), ("_b", False)):
            p = _teil(cfg, tag + suf, art, S, feinheit, seed, oese and not from_top, True, notes)
            out, slot = cut_axis_slot(p.outline, T, 0.0, from_top)
            ys = [q[1] for q in p.outline]
            span = (0.0, max(ys)) if from_top else (min(ys), 0.0)
            q = Part(p.name, out, features=[JointFeature("kreuz", "halving", span[1] - span[0], T, span=span,
                                                         points=slot)])
            for h in p.holes:
                q.add_hole(h)
            asm.parts.append(q)
        asm.connect(f"{tag}_a:kreuz", f"{tag}_b:kreuz")
    for t in dict.fromkeys(notes):
        asm.notes.append(t)
    if steckbar:
        asm.notes.append("Teil B (Schlitz unten, mit Öse) von oben auf Teil A (Schlitz oben) schieben.")
    asm.notes.append("Feine Kristalle vorsichtig aus der Platte lösen – mit einem Zahnstocher von hinten drücken. "
                     "Mit weißer Farbe oder Glitzer besprüht wirken sie wie echter Schnee.")
    if feinheit == "fein" and T > 2.5:
        asm.notes.append(f"Tipp: Feine Kristalle wirken in 1,5–2 mm Holz am schönsten (eingestellt: {T:g} mm).")
    return asm
