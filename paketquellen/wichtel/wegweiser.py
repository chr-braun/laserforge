"""
Wegweiser – Paket „Wichtel“.

Pfosten mit Zapfen in einem Grasbuckel-Sockel, dazu Pfeilschilder mit eigenen Ortsnamen (graviert), die
abwechselnd nach links und rechts zeigen und vorne auf den Pfosten geleimt werden.
"""
import math

from steckwerk import Assembly, Part, oriented
from pakete import bibliothek, num, sel, txt

Z = bibliothek("verzierungen")
K = Z.K

KOEPFE = [("stern", "Stern"), ("herz", "Herz"), ("dach", "Dach"), ("kugel", "Kugel"), ("spitz", "Spitze")]

UEBERSETZUNG = {"en": {
    "Wegweiser": "Signpost", "Wichtelzubehör": "Elf accessories",
    "Wegweiser mit eigenen Ortsnamen: Pfosten im Sockel, Pfeilschilder abwechselnd nach links und rechts.":
        "Signpost with your own place names: post in a base, arrow signs pointing left and right in turn.",
    "Schilder": "Signs", "Höhe": "Height", "Kopf": "Top", "Stern": "Star", "Herz": "Heart", "Dach": "Roof",
    "Kugel": "Ball", "Spitze": "Point", "Schilderhöhe": "Sign height",
    "Den Pfosten mit dem Zapfen in den Sockel stecken (sitzt er locker: ein Tropfen Leim).":
        "Push the post with its tab into the base (if it is loose: a drop of glue).",
    "Die Schilder von oben nach unten in der Reihenfolge der Namen vorne auf den Pfosten leimen.":
        "Glue the signs onto the front of the post from top to bottom in the order of the names.",
}}

INFO = dict(
    label="Wegweiser", group="Wichtel",
    desc="Wegweiser mit eigenen Ortsnamen: Pfosten im Sockel, Pfeilschilder abwechselnd nach links und rechts.",
    params=[
        txt("schilder", "Schilder", "Nordpol 3000 km|Wichtelhausen|Keksdose", "| trennt die Schilder (bis zu 5)",
            maxlen=120, symbols=True),
        num("hoehe", "Höhe", 110, 50, 300),
        num("schild_h", "Schilderhöhe", 11, 7, 30),
        sel("kopf", "Kopf", KOEPFE, "stern"),
    ],
)

WM = bibliothek("verzierungen").WM
INFO["params"] = WM.mit_massstab("wegweiser", INFO["params"])
UEBERSETZUNG["en"].update(WM.EN)


def build(cfg, name="wegweiser", schilder="Nordpol 3000 km|Wichtelhausen|Keksdose", hoehe=110.0, schild_h=11.0,
          kopf="stern", massstab="wichtel",
          wichtel=70.0):
    if massstab == "wichtel":                     # Maße passend zur Wichtelgröße
        _m = WM.wichtelmass("wegweiser", wichtel, INFO["params"], cfg)
        hoehe, schild_h = _m["hoehe"], _m["schild_h"]
    T = cfg.T
    H, hs = cfg.s(hoehe), cfg.s(schild_h)
    namen = [n.strip() for n in schilder.split("|") if n.strip()][:5]
    if not namen:
        raise ValueError("Mindestens ein Schild eintragen (Namen mit | trennen)")
    notes = []
    w = Z.wmin(cfg)
    bp = max(2.6 * T, min(14.0, H * 0.09))                # Pfostenbreite
    asm = Assembly(name, params=dict(hoehe=H, schilder=len(namen)))
    # --- Pfosten ---
    fig = Z.Figur().add(K.rect(-bp / 2, 0, bp, H - bp * 0.4))
    yk = H - bp * 0.9
    if kopf == "stern":
        fig.add(K.star(0, yk, bp * 1.1, bp * 0.5, 5))
    elif kopf == "herz":
        fig.add(Z.herz(0, yk - bp * 0.1, bp * 2.0))
    elif kopf == "dach":
        fig.add([(-bp * 1.1, yk - bp * 0.4), (bp * 1.1, yk - bp * 0.4), (0, H)])
    elif kopf == "kugel":
        fig.add(K.circle(0, yk, bp * 0.9, 40))
    else:
        fig.add([(-bp / 2, yk), (bp / 2, yk), (0, H)])
    pfosten = Z.figur_teil(cfg, "pfosten", fig, notes, unten_flach=True)
    tw = max(cfg.min_tab_width + 0.6, bp * 0.6)
    Z.zapfen_unten(pfosten, 0.0, tw, T, "fuss", pos=10)
    # Maserung
    Z.gravur(pfosten, [([(-bp * 0.2, 3), (-bp * 0.15, H * 0.4), (-bp * 0.22, H * 0.7)], False),
                       ([(bp * 0.18, H * 0.1), (bp * 0.22, H * 0.5)], False)], rand=0.8)
    asm.parts.append(pfosten)
    # --- Sockel (Grasbuckel) ---
    rx, ry = max(bp * 2.2, 22.0), max(T * 3 + 6, 14.0)
    sockel = Part("sockel", oriented(K.ellipse(0, 0, rx, ry, 0, 96), True))
    Z.schlitz(sockel, "pfosten", 0.0, 0.0, tw, T, 10)
    gras = []
    for k in range(7):
        a = math.pi * 2 * k / 7 + 0.4
        x, y = math.cos(a) * rx * 0.7, math.sin(a) * ry * 0.62
        if abs(y) < T + 2.5 and abs(x) < tw / 2 + 3:
            continue
        gras.append(([(x - 1.6, y - 1.0), (x - 0.6, y + 1.6), (x, y - 0.6), (x + 0.6, y + 1.8), (x + 1.6, y - 1.0)], False))
    Z.gravur(sockel, gras, rand=1.0)
    asm.parts.append(sockel)
    asm.connect("pfosten:fuss", "sockel:pfosten")
    asm.notes.append("Den Pfosten mit dem Zapfen in den Sockel stecken (sitzt er locker: ein Tropfen Leim).")
    # --- Schilder ---
    cap = hs * 0.48
    for i, n in enumerate(namen):
        st, tb, th = Z.textzeilen(n, cap, cap * 0.08)
        L = tb + hs * 1.6 + bp * 0.6
        rechts = i % 2 == 0
        spitze = hs * 0.55
        pts = [(0, 0), (L - spitze, 0), (L, hs / 2), (L - spitze, hs), (0, hs), (hs * 0.3, hs / 2)]
        if not rechts:
            pts = [(L - x, y) for x, y in pts]
        sfig = Z.Figur().add(pts)
        teil = Z.figur_teil(cfg, f"schild{i + 1}", sfig, notes)
        cx = (bp * 0.3 + hs * 0.3 + (L - spitze)) / 2 if rechts else L - (bp * 0.3 + hs * 0.3 + (L - spitze)) / 2
        try:
            st2, _ = Z.text_in_box(n, cx, hs / 2, tb * 1.02 + 0.5, hs * 0.75, cap, 2.5, 0.08)
        except ValueError:
            raise ValueError(f"Das Schild „{n}“ ist zu lang – kürzer fassen")
        Z.gravur(teil, [(s, False) for s in st2], rand=0.6)
        asm.parts.append(teil)
    asm.notes.append("Die Schilder von oben nach unten in der Reihenfolge der Namen vorne auf den Pfosten leimen.")
    if H - bp * 2.5 < len(namen) * (hs + 3):
        notes.append("Die Schilder brauchen mehr Platz als der Pfosten hoch ist – Wegweiser höher machen oder "
                     "weniger Schilder nehmen.")
    asm.notes += notes
    return asm
