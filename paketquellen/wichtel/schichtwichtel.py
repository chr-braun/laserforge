"""
Schichtwichtel – Paket „Wichtel“.

Ein skandinavischer Wichtel (Tomte) aus vier Schichten, die aufeinandergeleimt werden:

  1 Grund      die ganze Silhouette, rundum etwas größer – gibt einen Schattenrand und hält alles zusammen
  2 Körper     Mantel mit Ärmeln, Stiefel und Mütze (mit graviertem Muster)
  3 Bart       wallender Bart mit gravierten Strähnen, dazu die Fäustlinge
  4 Vorne      Fellkrempe mit Nase, Bommel und das Zubehör (Laterne, Herz, Stern, Tanne, Geschenk)

Jede Schicht lässt sich vor dem Leimen in ihrer eigenen Farbe bemalen. Auf Wunsch steht der Wichtel in
einer Standplatte mit seinem Namen oder bekommt eine Öse zum Aufhängen.
"""
from __future__ import annotations

import math
from typing import List, Sequence, Tuple

from steckwerk import Assembly
from pakete import bibliothek, num, sel, txt

Z = bibliothek("verzierungen")
K, E = Z.K, Z.E
Figur = K.Figur
Point = Tuple[float, float]

MUETZEN = [("umgeknickt", "umgeknickt (Zipfel hängt)"), ("spitz", "spitz"), ("bommel", "mit Bommel")]
BAERTE = [("lang", "lang und spitz"), ("rund", "rund und voll"), ("lockig", "lockig"), ("zwei", "zwei Zipfel")]
MUSTER = [("keins", "keins"), ("streifen", "Streifen"), ("sterne", "Sterne"), ("herzen", "Herzen"),
          ("norweger", "Norweger-Zacken")]
ZUBEHOER = [("keins", "keins"), ("laterne", "Laterne"), ("herz", "Herz"), ("stern", "Stern am Stab"),
            ("tanne", "Tannenbaum"), ("geschenk", "Geschenk")]
STAND = [("sockel", "Standplatte mit Namen"), ("flach", "steht auf den Stiefeln"), ("oese", "Öse zum Aufhängen")]

INFO = dict(
    label="Schichtwichtel", group="Wichtel",
    desc="Skandinavischer Wichtel aus vier Schichten: Mütze mit Fellkrempe, Bart mit Strähnen, dicke Nase, "
         "Fäustlinge und Stiefel – mit Zubehör und Standplatte. Schicht für Schicht bemalen und aufeinanderleimen.",
    params=[
        num("groesse", "Höhe", 130, 60, 300),
        sel("muetze", "Mütze", MUETZEN, "umgeknickt"),
        sel("muster", "Mützenmuster", MUSTER, "sterne"),
        sel("bart", "Bart", BAERTE, "lang"),
        sel("zubehoer", "Zubehör", ZUBEHOER, "laterne"),
        sel("stand", "Stand", STAND, "sockel"),
        txt("name_text", "Name", "", "steht vorne auf der Standplatte", maxlen=16,
            when={"stand": ["sockel"]}),
        num("rand", "Schattenrand", 1.5, 0.8, 5),
    ],
)

UEBERSETZUNG = {"en": {
    "Schichtwichtel": "Layered gnome", "Wichtelfiguren": "Elf figures", "Wichtel": "Elves",
    "Skandinavischer Wichtel aus vier Schichten: Mütze mit Fellkrempe, Bart mit Strähnen, dicke Nase, "
    "Fäustlinge und Stiefel – mit Zubehör und Standplatte. Schicht für Schicht bemalen und aufeinanderleimen.":
        "Scandinavian gnome in four layers: hat with fur brim, beard with strands, big nose, mittens and boots – "
        "with accessory and base. Paint layer by layer and glue together.",
    "Höhe": "Height", "Mütze": "Hat", "Mützenmuster": "Hat pattern", "Bart": "Beard", "Zubehör": "Accessory",
    "Stand": "Stand", "Name": "Name", "steht vorne auf der Standplatte": "engraved on the front of the base",
    "Schattenrand": "Shadow border", "umgeknickt (Zipfel hängt)": "folded (tip hanging)", "spitz": "pointed",
    "mit Bommel": "with pompom", "lang und spitz": "long and pointed", "rund und voll": "round and full",
    "lockig": "curly", "zwei Zipfel": "forked", "keins": "none", "Streifen": "stripes", "Sterne": "stars",
    "Herzen": "hearts", "Norweger-Zacken": "Nordic zigzag", "Laterne": "lantern", "Herz": "heart",
    "Stern am Stab": "star on a stick", "Tannenbaum": "fir tree", "Geschenk": "present",
    "Standplatte mit Namen": "base with name", "steht auf den Stiefeln": "stands on its boots",
    "Öse zum Aufhängen": "loop for hanging",
}}


# --------------------------------------------------------------------------------------------------
# Formen (Einheit: Höhe = 1, Ursprung unten Mitte)
# --------------------------------------------------------------------------------------------------

def _spiegel(rechts: Sequence[Point]) -> List[Point]:
    """Rechte Hälfte von oben-Mitte nach unten-Mitte → geschlossene, symmetrische Kontur."""
    links = [(-x, y) for x, y in reversed(rechts[1:-1])]
    return list(rechts) + links


def _muetze(art: str) -> Tuple[List[Point], Point]:
    """Mützenkegel (ohne Krempe) und Spitze (für Öse/Bommel)."""
    if art == "umgeknickt":
        pts = [(-0.215, 0.53), (-0.18, 0.70), (-0.08, 0.86), (0.07, 0.94), (0.20, 0.91), (0.30, 0.80),
               (0.335, 0.70), (0.30, 0.71), (0.24, 0.79), (0.15, 0.80), (0.14, 0.70), (0.19, 0.60), (0.215, 0.53)]
        return K.spline(pts[:-1], closed=True, n=8), (0.07, 0.94)
    top = 0.92 if art == "bommel" else 1.0
    rechts = [(0.0, top), (0.05, top - 0.10), (0.13, 0.75), (0.215, 0.53)]
    pts = rechts + [(-x, y) for x, y in reversed(rechts[1:])]
    return K.spline(pts, closed=True, n=8), (0.0, top)


def _bart(art: str) -> List[Point]:
    if art == "rund":
        r = [(0.0, 0.535), (0.18, 0.53), (0.228, 0.45), (0.228, 0.33), (0.185, 0.22), (0.10, 0.16), (0.0, 0.15)]
    elif art == "zwei":
        r = [(0.0, 0.535), (0.17, 0.53), (0.222, 0.44), (0.21, 0.30), (0.15, 0.17), (0.085, 0.095),
             (0.045, 0.16), (0.0, 0.25)]
    else:                                                   # lang (auch Grundform für lockig)
        r = [(0.0, 0.535), (0.17, 0.53), (0.218, 0.46), (0.222, 0.37), (0.19, 0.26), (0.12, 0.165),
             (0.045, 0.10), (0.0, 0.08)]
    return K.spline(_spiegel(r), closed=True, n=8)


def _bart_unten(art: str, x: float) -> float:
    """Ungefähre Unterkante des Barts bei x (für die Strähnen)."""
    if art == "rund":
        return 0.16 + 0.45 * x * x
    if art == "zwei":
        return 0.10 + 0.8 * (abs(x) - 0.085) ** 2 if abs(x) > 0.02 else 0.25
    return 0.08 + 2.2 * x * x


def _herz(cx: float, cy: float, g: float) -> List[Point]:
    return Z.O.herz(cx, cy, g)


# --------------------------------------------------------------------------------------------------

def build(cfg, name="schichtwichtel", groesse=130.0, muetze="umgeknickt", muster="sterne", bart="lang",
          zubehoer="laterne", stand="sockel", name_text="", rand=1.5):
    H = cfg.s(groesse)
    T = cfg.T
    w = Z.wmin(cfg)
    if H < 22 * w:
        raise ValueError(f"Für so viele Details ist der Wichtel zu klein – mindestens {math.ceil(22 * w / 5) * 5:g} mm hoch")
    notes: List[str] = []

    def P(pts):                                             # Einheit → mm
        return [(x * H, y * H) for x, y in pts]

    def L(pts):                                             # Linie Einheit → mm
        return [(x * H, y * H) for x, y in pts]

    unter_null = K.rect(-H, -H, 2 * H, H)                   # alles unter der Standfläche abschneiden

    # ---- Schicht 2: Körper (Mantel, Ärmel, Stiefel, Mütze) -------------------------------------------
    mantel = P(K.spline([(-0.25, 0.085), (-0.21, 0.26), (-0.17, 0.46), (-0.12, 0.57), (0.12, 0.57), (0.17, 0.46),
                         (0.21, 0.26), (0.25, 0.085)], closed=True, n=8))
    stiefel = []
    for s in (-1, 1):
        stiefel.append(P([(s * x, y) for x, y in
                          K.spline([(0.025, 0.0), (0.24, 0.0), (0.285, 0.035), (0.25, 0.085), (0.15, 0.1),
                                    (0.03, 0.095)], closed=True, n=8)]))
    aermel = [K.stroke(L(K.spline([(s * 0.14, 0.47), (s * 0.19, 0.40), (s * 0.215, 0.30)], n=10)),
                       0.10 * H, 0.085 * H)
              for s in (-1, 1)]
    hut, spitze = _muetze(muetze)
    hut = P(hut)
    koerper = Figur().add(mantel, *stiefel, *aermel, hut).cut(unter_null)

    # ---- Schicht 3: Bart und Fäustlinge ----------------------------------------------------------------
    bartf = P(_bart(bart))
    bartfig = Figur().add(bartf)
    faeuste = []
    for s, seite in ((-1, "links"), (1, "rechts")):
        f = Figur().add(P(K.ellipse(s * 0.228, 0.285, 0.056, 0.064, rot=s * 0.5)),
                        P(K.ellipse(s * 0.188, 0.312, 0.026, 0.034, rot=s * 0.9)))
        faeuste.append(("faeustling_" + seite, f))
    if bart == "lockig":
        kreise = []
        for k in range(11):
            a = math.pi * (1.05 + 0.9 * k / 10)
            kreise.append(P(K.circle(0.20 * math.cos(a) * 1.02, 0.30 + 0.20 * math.sin(a), 0.045)))
        bartfig.add(*kreise)

    # ---- Schicht 4: Krempe mit Nase, Bommel, Zubehör ---------------------------------------------------
    krempe = K.stroke(L(K.bez((-0.232, 0.525), (0.0, 0.575), (0.232, 0.525), 16)), 0.085 * H, 0.085 * H)
    nase = P(K.ellipse(0.0, 0.485, 0.072, 0.065))
    vorne = [("krempe", Figur().add(krempe, nase))] + faeuste
    if muetze == "bommel":
        vorne.append(("bommel", Figur().add(P(K.circle(spitze[0], spitze[1] + 0.02, 0.055)))))
    zub = _zubehoer(zubehoer, H, w)
    if zub is not None:
        vorne.append((zubehoer, zub))

    # ---- Schicht 1: Grund = ganze Silhouette, um den Schattenrand größer ------------------------------
    alles = Figur()
    for f in [koerper, bartfig] + [f for _, f in vorne]:
        alles.add(*[poly for op, poly in f.ops if op == "+"])
    if stand == "oese":
        ro = max(0.045 * H, 3.5)
        sx, sy = spitze[0] * H, spitze[1] * H
        alles.add(K.circle(sx, sy + ro * 0.9, ro))
    alles.add(K.rect(-0.22 * H, 0.0, 0.44 * H, 0.07 * H))       # Grund steht durchgehend auf
    alles.cut(unter_null)
    x0, y0, x1, y1 = alles.bbox()
    lw = E.Leinwand((x0 - rand - 4, -1.0, x1 + rand + 4, y1 + rand + 4), Z.px_fuer(max(x1 - x0, y1 - y0)))
    grund_r = lw.figur(alles).dilate(lw.px_fuer(rand))
    grund_r = E._andnot(grund_r, lw.flaechen([K.rect(x0 - 20, -20, x1 - x0 + 40, 20)]))   # flacher Boden
    if stand == "oese":
        grund_r = E._andnot(grund_r, lw.flaechen([K.circle(sx, sy + ro * 0.9, ro - max(cfg.min_web + 0.8, 1.6))]))
    grund = E.teil_aus_raster("grund", lw, grund_r, cfg.min_web, cfg.kerf, notes, unten_flach=True)

    teile = []
    k_teil = Z.figur_teil(cfg, "koerper", koerper, notes, unten_flach=True)
    b_teil = Z.figur_teil(cfg, "bart", bartfig, notes)
    v_teile = [Z.figur_teil(cfg, n, f, notes) for n, f in vorne]

    # ---- Gravuren ----------------------------------------------------------------------------------------
    _gravur(k_teil, [(s, c) for s, c in _muster_linien(muster, muetze, H)] + _mantel_linien(H), rand=0.9)
    _gravur(b_teil, _straehnen(bart, H), rand=0.9)
    _gravur(v_teile[0], _fell(H), rand=0.7)
    if zubehoer == "geschenk":
        _gravur(v_teile[-1], [([(-0.02 * H, 0.17 * H), (-0.02 * H, 0.31 * H)], False),
                               ([(0.02 * H, 0.17 * H), (0.02 * H, 0.31 * H)], False),
                               ([(-0.11 * H, 0.27 * H), (0.11 * H, 0.27 * H)], False)], rand=0.6)
    for t, sgn in zip(v_teile[1:3], (-1, 1)):
        _gravur(t, [(K.bez((sgn * 0.248 * H, 0.33 * H), (sgn * 0.27 * H, 0.31 * H), (sgn * 0.282 * H, 0.285 * H), 8),
                       False)], rand=0.6)
    if muetze == "umgeknickt":
        _gravur(k_teil, [(K.bez((0.13 * H, 0.70 * H), (0.17 * H, 0.77 * H), (0.12 * H, 0.82 * H), 10), False)],
                 rand=0.9)

    asm = Assembly(name, params=dict(groesse=H, muetze=muetze, bart=bart, zubehoer=zubehoer, stand=stand))
    asm.parts += [grund, k_teil, b_teil] + v_teile

    if stand == "sockel":
        tw = max(cfg.min_tab_width + 1.0, min(0.22 * H, 24.0))
        Z.zapfen_unten(grund, 0.0, tw, T, "fuss", 1)
        asm.parts.append(_sockel(cfg, H, tw, name_text, notes))
        asm.connect("grund:fuss", "standplatte:fuss")

    asm.notes.append("Reihenfolge: Grund – Körper – Bart – vorne Krempe mit Nase und Zubehör. Alle Schichten "
                     "unten bündig. Vor dem Leimen bemalen: z. B. Mütze rot, Bart weiß, Mantel grau, Nase rosa.")
    if stand == "sockel":
        asm.notes.append("Den Grund mit dem Zapfen in die Standplatte stecken.")
    for t in dict.fromkeys(notes):
        asm.notes.append(t)
    return asm


def _gravur(part, linien, rand):
    """Wie Z.gravur, aber gegen eine vereinfachte Kontur geprüft – bei großen Wichteln sonst sehr langsam."""
    from steckwerk import Part
    from models.motivvorlagen import tidy
    tol = max(0.04, min(0.25, 0.0012 * max(part.bbox()[2] - part.bbox()[0], part.bbox()[3] - part.bbox()[1])))
    probe = Part(part.name, tidy(part.outline, tol, 0.3))
    for h in part.holes:
        probe.add_hole(h)
    Z.gravur(probe, linien, rand=rand)
    part.engrave.extend(probe.engrave)


def _zubehoer(art: str, H: float, w: float):
    def P(pts):
        return [(x * H, y * H) for x, y in pts]
    lw_ = max(w, 0.018 * H)
    if art == "laterne":
        f = Figur()
        f.add(K.stroke(P(K.bez((0.25, 0.28), (0.315, 0.30), (0.315, 0.22), 10)), lw_))
        f.add(P([(0.262, 0.198), (0.368, 0.198), (0.315, 0.245)]))                 # Dach
        f.add(P(K.rect(0.275, 0.075, 0.08, 0.135)))                               # Gehäuse
        f.add(P(K.rect(0.262, 0.065, 0.106, 0.025)))                              # Fuß
        rw = max(0.022, 1.6 / H)
        f.cut(P(K.rect(0.275 + rw, 0.105, 0.08 - 2 * rw, 0.08)))                  # Fenster
        return f
    if art == "herz":
        return Figur().add(P(_herz(0.0, 0.25, 0.17)))
    if art == "stern":
        f = Figur().add(K.stroke(P([(0.235, 0.29), (0.33, 0.56)]), lw_))
        f.add(P(K.star(0.345, 0.61, 0.085, 0.038, 5)))
        return f
    if art == "tanne":
        f = Figur()
        for k, (yb, bw, h) in enumerate(((0.06, 0.20, 0.13), (0.14, 0.16, 0.12), (0.22, 0.11, 0.11))):
            f.add(P([(0.37 - bw / 2, yb), (0.37 + bw / 2, yb), (0.37, yb + h)]))
        f.add(P(K.rect(0.355, 0.0, 0.03, 0.065)))
        f.add(P(K.star(0.37, 0.345, 0.03, 0.013, 5)))
        return f
    if art == "geschenk":
        f = Figur().add(P(K.rect(-0.10, 0.165, 0.20, 0.125)), P(K.rect(-0.115, 0.27, 0.23, 0.045)))
        f.add(P(K.ellipse(-0.045, 0.335, 0.05, 0.026, rot=0.45)), P(K.ellipse(0.045, 0.335, 0.05, 0.026, rot=-0.45)))
        f.add(P(K.circle(0.0, 0.322, 0.018)))
        return f
    return None


def _muster_linien(muster: str, muetze: str, H: float):
    """Gravur auf der Mütze (wird an der Mützenkontur beschnitten)."""
    out = []
    y0, y1 = 0.60, 0.98
    if muster == "streifen":
        for k in range(-6, 8):
            x = k * 0.07
            out.append(([(x * H, y0 * H), ((x + 0.2) * H, y1 * H)], False))
    elif muster == "norweger":
        for y in (0.63, 0.74, 0.85):
            pts = []
            for k in range(13):
                pts.append(((-0.24 + k * 0.04) * H, (y + (0.02 if k % 2 else -0.02)) * H))
            out.append((pts, False))
    elif muster in ("sterne", "herzen"):
        pos = [(-0.10, 0.63), (0.05, 0.66), (0.14, 0.62), (-0.03, 0.74), (0.09, 0.77), (0.02, 0.86)]
        if muetze == "umgeknickt":
            pos += [(0.21, 0.84), (-0.09, 0.80)]
        for x, y in pos:
            if muster == "sterne":
                st = K.star(x * H, y * H, 0.03 * H, 0.013 * H, 5)
            else:
                st = Z.O.herz(x * H, y * H, 0.05 * H)
            out.append((st, True))
    return out


def _mantel_linien(H: float):
    """Saum am Mantel und Schaft der Stiefel."""
    out = [([(-0.24 * H, 0.125 * H), (0.24 * H, 0.125 * H)], False)]
    for s in (-1, 1):                                       # Sohle
        out.append(([(s * 0.04 * H, 0.022 * H), (s * 0.255 * H, 0.022 * H)], False))
    return out


def _straehnen(art: str, H: float):
    """Geschwungene Strähnen, die zur Bartspitze hin zusammenlaufen."""
    out = []
    n = 9
    for i in range(n):
        u = -1 + 2 * i / (n - 1)
        x = 0.165 * u
        yb = _bart_unten(art, x * 0.8) + 0.045
        if art == "zwei":
            xe = (0.085 if u > 0 else -0.085) + 0.06 * u
        else:
            xe = 0.55 * x
        welle = 0.018 * (1 if i % 2 else -1)
        out.append((K.bez3((x * H, 0.455 * H), ((x * 1.05 + welle) * H, 0.36 * H),
                           ((xe - welle) * H, (yb + 0.08) * H), (xe * H, yb * H), 14), False))
    return out


def _fell(H: float):
    """Kleine Bögen als Fellstruktur auf der Krempe."""
    out = []
    for k in range(9):
        x = -0.18 + 0.045 * k
        y = 0.525 + 0.04 * (1 - (x / 0.232) ** 2) * 0.5
        out.append((K.arc(x * H, y * H, 0.013 * H, 0.2, math.pi - 0.2, 6), False))
    return out


def _sockel(cfg, H: float, tw: float, text: str, notes):
    from steckwerk import Part, oriented
    T = cfg.T
    rx = max(0.34 * H, tw / 2 + 10)
    ry = max(0.13 * H, 2.4 * T + 7)
    platte = Part("standplatte", oriented(K.ellipse(0.0, 0.0, rx, ry, n=64), True))
    ys = -ry + max(3.0, 0.22 * ry) + T / 2
    Z.schlitz(platte, "fuss", 0.0, ys, tw, T, 1)
    if text.strip():
        top = ys + T / 2 + 4 * T + 1.0
        st, _ = Z.text_in_box(text, 0.0, (top + ry - 2.0) / 2, rx * 1.3, max(ry - 2.0 - top, 3.0), 0.1 * H, 2.5)
        _gravur(platte, [(s, False) for s in st], rand=1.0)
    return platte
