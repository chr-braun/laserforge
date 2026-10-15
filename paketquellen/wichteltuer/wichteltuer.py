"""
Wichteltür – Paket „Wichteltür“.

Zwei Lagen: hinten die Tür mit graviertem Bretterlook, Beschlägen, Türknauf und optionalem Türfenster,
vorne der Rahmen (Steinbogen, Holz oder Ranke) mit verzierter Kante. Die Tür steckt mit zwei Zapfen in
einer Stufe und steht so frei an der Fußleiste. Dazu auf Wunsch ein Namensschild.
"""
import importlib.util
import math
import os

from steckwerk import Assembly
from pakete import integer, num, sel, txt

_spec = importlib.util.spec_from_file_location("swpaket_wichteltuer__lade_tuer",
                                               os.path.join(os.path.dirname(os.path.abspath(__file__)), "_lade.py"))
_m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_m)
M = _m.tuer()
Z, K = M.Z, M.K

TUERFENSTER = [("rund", "rund mit Sprossen"), ("herz", "Herz"), ("stern", "Stern"), ("gitter", "kleines Gitter"),
               ("keins", "keins")]

UEBERSETZUNG = {"en": {
    "Wichteltür": "Elf door",
    "Wichteltür für die Fußleiste: Tür mit Bretterlook und Beschlägen, Rahmen als Steinbogen oder Holz, Stufe zum Hinstellen und Namensschild.":
        "Elf door for the skirting board: door with plank look and fittings, stone arch or wooden frame, a step to stand on and a name sign.",
    "Höhe": "Height", "Breite": "Width", "Form": "Shape", "Rahmenbreite": "Frame width", "Rahmen": "Frame",
    "Kante": "Edge", "Türfenster": "Door window", "Bretter": "Planks", "Namensschild": "Name sign",
    "Text auf der Stufe": "Text on the step", "Rundbogen": "Round arch", "Spitzbogen": "Pointed arch",
    "eckig, oben abgerundet": "square, rounded top", "Steinbogen": "Stone arch", "Holzrahmen": "Wooden frame",
    "mit Herzen": "with hearts", "mit Sternen": "with stars", "mit Punkten": "with dots", "glatt": "plain", "rund mit Sprossen": "round with bars", "Herz": "Heart",
    "Stern": "Star", "kleines Gitter": "small grille", "keins": "none", "keine": "none",
    "Den Rahmen deckungsgleich vorne auf die Tür leimen (unten bündig).":
        "Glue the frame onto the front of the door, flush at the bottom.",
    "Die Tür mit den beiden Zapfen in die Schlitze der Stufe stecken – der Rahmen steht vorne auf der Stufe.":
        "Push the door with its two tabs into the slots of the step – the frame stands on the step in front.",
    "Das Namensschild mittig über das Türfenster leimen.": "Glue the name sign centred above the door window.",
}}

INFO = dict(
    label="Wichteltür", group="Wichteltür",
    desc="Wichteltür für die Fußleiste: Tür mit Bretterlook und Beschlägen, Rahmen als Steinbogen oder Holz, "
         "Stufe zum Hinstellen und Namensschild.",
    params=[
        num("hoehe", "Höhe", 120, 60, 260),
        num("breite", "Breite", 76, 40, 200),
        sel("form", "Form", M.FORMEN, "bogen"),
        num("rahmen_b", "Rahmenbreite", 12, 6, 30),
        sel("rahmen", "Rahmen", M.RAHMEN, "steine"),
        sel("kante", "Kante", [("keine", "keine")] + Z.KANTEN, "keine"),
        sel("fenster", "Türfenster", TUERFENSTER, "rund"),
        integer("bretter", "Bretter", 5, 0, 10),
        txt("schild", "Namensschild", "Wichtel|Fridolin", "| = neue Zeile, leer = ohne Schild", symbols=True),
        txt("matte", "Text auf der Stufe", "", "z. B. „Willkommen“", symbols=True),
    ],
)


def build(cfg, name="wichteltuer", hoehe=120.0, breite=76.0, form="bogen", rahmen_b=12.0, rahmen="steine",
          kante="keine", fenster="rund", bretter=5, schild="Wichtel|Fridolin", matte=""):
    T = cfg.T
    H, B, rb = cfg.s(hoehe), cfg.s(breite), cfg.s(rahmen_b)
    w = Z.wmin(cfg)
    rb = max(rb, 2.5 * w)
    Wt, Ht = B - 2 * rb, H - rb
    if Wt < 20 or Ht < 30:
        raise ValueError("Die Tür ist zu klein für diesen Rahmen – größer machen oder den Rahmen schmaler")
    notes = []
    asm = Assembly(name, params=dict(hoehe=H, breite=B, form=form, rahmen=rahmen, fenster=fenster))
    oeff = M.form(form, Wt, Ht)
    # --- Tür (hinten, volle Größe) ---
    fig = Z.Figur().add(M.form(form, B, H))
    fy = min(Ht * 0.7, M.oben_y(oeff, 0) - Wt * 0.3)            # Mitte des Türfensters
    fr = min(Wt * 0.17, Ht * 0.1)
    if fenster == "rund":
        fig.cut(K.circle(0, fy, fr, 64))
        s = max(1.3 * w, fr * 0.14)
        fig.add(K.rect(-s / 2, fy - fr - 0.5, s, 2 * fr + 1), K.rect(-fr - 0.5, fy - s / 2, 2 * fr + 1, s))
    elif fenster in ("herz", "stern"):
        fig.merge(Z.ausschnitt(fenster, 0, fy, fr * 2.1))
    elif fenster == "gitter":
        g = fr * 1.7
        fig.cut(K.rect(-g / 2, fy - g / 2, g, g))
        s = max(1.3 * w, g * 0.1)
        for x in ((-g / 6, g / 6) if g >= 15 else (0.0,)):
            fig.add(K.rect(x - s / 2, fy - g / 2 - 0.5, s, g + 1))
    tuer = Z.figur_teil(cfg, "tuer", fig, notes, unten_flach=True)
    tw = M.tabbreite(cfg, B, 0.18)
    xs = [-B * 0.3, B * 0.3]
    for k, x in enumerate(xs):
        Z.zapfen_unten(tuer, x, tw, T, f"fuss{k}", pos=10 + k)
    _tuer_gravur(tuer, oeff, Wt, Ht, int(bretter), fy, fr if fenster != "keins" else 0.0)
    asm.parts.append(tuer)
    # --- Rahmen (vorne) ---
    rfig = M.rahmen_figur(cfg, form, Wt, Ht, rb, rahmen, kante)
    rteil = Z.figur_teil(cfg, "rahmen", rfig, notes, unten_flach=True)
    Z.gravur(rteil, M.rahmen_gravur(form, Wt, Ht, rb, rahmen), rand=0.8)
    asm.parts.append(rteil)
    asm.notes.append("Den Rahmen deckungsgleich vorne auf die Tür leimen (unten bündig).")
    # --- Stufe ---
    m = max(2.2, T * 0.8)
    Tf = m + 2 * T + max(10.0, H * 0.1)
    stufe = M.standplatte(cfg, "stufe", B + 2 * max(6.0, rb * 0.6), Tf,
                          [(f"tuer{k}", x, m + T / 2, tw, 10 + k) for k, x in enumerate(xs)])
    if matte.strip():
        M.text_gravur(stufe, matte, 0, m + 2 * T + (Tf - m - 2 * T) / 2, B * 0.8, (Tf - m - 2 * T) * 0.6, 7.0,
                      "Der Text auf der Stufe")
    else:
        lin = []
        y0, y1 = m + 2 * T + 2, Tf - 2
        x = -B / 2
        k = 0
        while x < B / 2 - 4:                                     # Pflastersteine
            sw = 7.0 + (k % 3)
            lin.append((Z.abrunden([(x, y0), (x + sw - 1.2, y0), (x + sw - 1.2, y1), (x, y1)], 1.5), True))
            x += sw
            k += 1
        Z.gravur(stufe, lin, rand=1.0)
    asm.parts.append(stufe)
    for k in range(2):
        asm.connect(f"tuer:fuss{k}", f"stufe:tuer{k}")
    asm.notes.append("Die Tür mit den beiden Zapfen in die Schlitze der Stufe stecken – der Rahmen steht vorne "
                     "auf der Stufe.")
    # --- Namensschild ---
    if schild.strip():
        zeilen = len([z for z in schild.split("|") if z.strip()])
        Ws = min(Wt * 0.86, 70.0)
        while True:
            Hs = min(Ws * 0.55, 6.0 + zeilen * 7.5)
            umr = [(x, y - Hs / 2) for x, y in Z.kartusche(Ws, Hs, "kartusche")]
            teil = Z.figur_teil(cfg, "schild", Z.Figur().add(umr), notes)
            try:
                M.text_gravur(teil, schild, 0, 0, Ws * 0.72, Hs * 0.7, 6.5, "Der Name")
                break
            except ValueError:
                if Ws >= B * 1.2:
                    raise
                Ws = min(Ws * 1.15, B * 1.2)
        asm.parts.append(teil)
        asm.notes.append("Das Namensschild mittig über das Türfenster leimen.")
    asm.notes += notes
    return asm


def _tuer_gravur(part, oeff, Wt, Ht, bretter, fy, fr):
    """Bretterfugen, Querriegel mit Strebe, Beschläge und Türknauf (nur innerhalb der Öffnung)."""
    lin = []
    rand = 1.2
    if bretter > 1:
        for i in range(1, bretter):
            x = -Wt / 2 + Wt * i / bretter
            lin.append(([(x, rand), (x, M.oben_y(oeff, x) - rand)], False))
    yb = [Ht * 0.16, min(Ht * 0.5, fy - fr - 6.0)]
    hb = max(4.0, Ht * 0.06)
    for y in yb:
        lin.append((Z.abrunden([(-Wt / 2 + rand, y), (Wt / 2 - rand, y), (Wt / 2 - rand, y + hb),
                                (-Wt / 2 + rand, y + hb)], 0.8), True))
    lin.append(([(Wt / 2 - 3, yb[0] + hb + 1), (-Wt / 2 + 3, yb[1] - 1)], False))       # Strebe
    for y in yb:                                                                    # Scharniere
        L = Wt * 0.42
        lin.append((Z.abrunden([(-Wt / 2 - 2, y + hb * 0.2), (-Wt / 2 + L, y + hb * 0.35),
                                (-Wt / 2 + L, y + hb * 0.65), (-Wt / 2 - 2, y + hb * 0.8)], 0.6), True))
    kx, ky = Wt * 0.3, (yb[0] + yb[1]) / 2 + hb / 2
    r = max(2.0, Wt * 0.045)
    lin.append((K.circle(kx, ky, r, 24), True))
    lin.append((K.circle(kx, ky, r * 0.45, 12), True))
    lin.append(([(kx - 0.8, ky - r * 2.2), (kx, ky - r * 1.6), (kx + 0.8, ky - r * 2.2), (kx - 0.8, ky - r * 2.2)], False))
    Z.gravur(part, lin, rand=0.8)
