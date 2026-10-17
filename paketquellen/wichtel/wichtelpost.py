"""
Wichtelpost (Briefkasten) – Paket „Wichtel“.

Wichtel-Briefkasten auf einem Pfosten im Grasbuckel: Kasten mit Dach und Briefschlitz in zwei Lagen,
Namensschild, Fähnchen zum Aufleimen und zwei kleine Briefe mit Herz.
"""
import importlib.util
import math
import os

from steckwerk import Assembly, Part, oriented
from pakete import integer, num, sel, txt

_spec = importlib.util.spec_from_file_location("swpaket_wichtel__lade_post",
                                               os.path.join(os.path.dirname(os.path.abspath(__file__)), "_lade.py"))
_m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_m)
M = _m.markt()
Z, K = M.Z, M.K

DAECHER = [("giebel", "Giebeldach"), ("rund", "Runddach")]

UEBERSETZUNG = {"en": {
    "Wichtel-Briefkasten": "Elf mailbox",
    "Briefkasten auf dem Pfosten: Kasten mit Dach und Briefschlitz in zwei Lagen, Namensschild, Fähnchen und "
    "kleine Briefe.":
        "Mailbox on a post: box with roof and letter slot in two layers, name plate, flag and little letters.",
    "Name": "Name", "Höhe": "Height", "Dach": "Roof", "Giebeldach": "gable roof", "Runddach": "round roof",
    "Briefe": "Letters",
}}

INFO = dict(
    label="Wichtel-Briefkasten", group="Wichtel",
    desc="Briefkasten auf dem Pfosten: Kasten mit Dach und Briefschlitz in zwei Lagen, Namensschild, Fähnchen und "
         "kleine Briefe.",
    params=[
        txt("name_text", "Name", "Wichtelpost", "", maxlen=16),
        num("hoehe", "Höhe", 84, 45, 250),
        sel("dach", "Dach", DAECHER, "giebel"),
        integer("briefe", "Briefe", 2, 0, 5),
    ],
)
INFO["params"] = M.mit_massstab("wichtelpost", INFO["params"])
UEBERSETZUNG["en"].update(M.EN)


def build(cfg, name="wichtelpost", name_text="Wichtelpost", hoehe=84.0, dach="giebel", briefe=2,
          massstab="wichtel", wichtel=70.0):
    if massstab == "wichtel":
        hoehe = M.mass("wichtelpost", wichtel, INFO["params"], cfg)["hoehe"]
    T = cfg.T
    H = cfg.s(hoehe)
    w = Z.wmin(cfg)
    notes = []
    asm = Assembly(name, params=dict(hoehe=H))
    Bk = H * 0.5                                    # Kastenbreite
    Hk = H * 0.3                                    # Kastenhöhe (ohne Dach)
    yk = H - Hk - H * 0.14                          # Unterkante Kasten
    bp = max(2.6 * T, H * 0.075)                    # Pfosten

    # Lage 1: Pfosten + Kasten + Dach in einem Stück
    fig = Z.Figur().add(K.rect(-bp / 2, 0, bp, yk + 2))
    fig.add(Z.abrunden(K.rect(-bp / 2 - 1.8, 0, bp + 3.6, max(3.0, H * 0.03)), 0.8, 3))
    kasten = Z.abrunden(K.rect(-Bk / 2, yk, Bk, Hk), Bk * 0.05, 3)
    fig.add(kasten)
    ov = Bk * 0.08
    if dach == "giebel":
        dachpoly = Z.abrunden([(-Bk / 2 - ov, yk + Hk - 0.5), (Bk / 2 + ov, yk + Hk - 0.5), (0, H)], Bk * 0.03, 2)
    else:
        hb = H - (yk + Hk)
        dachpoly = [(-Bk / 2 - ov, yk + Hk - 0.5), (Bk / 2 + ov, yk + Hk - 0.5)] + \
            [((Bk / 2 + ov) * math.cos(a), yk + Hk - 0.5 + (hb + 0.5) * math.sin(a))
             for a in (math.pi * i / 32 for i in range(1, 32))]
    fig.add(dachpoly)
    # Stütze unter dem Kasten
    fig.add(K.stroke([(-bp / 2, yk - Hk * 0.45), (-Bk * 0.3, yk + 0.5)], max(w * 1.2, 2.0)))
    fig.add(K.stroke([(bp / 2, yk - Hk * 0.45), (Bk * 0.3, yk + 0.5)], max(w * 1.2, 2.0)))
    grund = Z.figur_teil(cfg, "pfosten", fig, notes, unten_flach=True)
    tw = max(cfg.min_tab_width + 0.6, min(bp + 3.6 - 3.4, cfg.tab_factor * T))
    Z.zapfen_unten(grund, 0.0, tw, T, "fuss", 10)
    lin = [([(-bp * 0.15, 3.5), (-bp * 0.05, yk * 0.5), (-bp * 0.18, yk - Hk * 0.5)], False),
           ([(bp * 0.2, yk * 0.2), (bp * 0.15, yk * 0.7)], False)]
    if dach == "giebel":
        for k in range(1, 4):                       # Schindeln
            t = k / 4
            yy = yk + Hk + (H - yk - Hk) * t * 0.85
            xx = (Bk / 2 + ov) * (1 - t * 0.85) - 1.5
            lin.append(([(-xx, yy), (xx, yy)], False))
    else:
        for k in range(1, 3):
            r = (Bk / 2 + ov) * (1 - k * 0.3)
            lin.append((K.arc(0, yk + Hk, r, 0.15, math.pi - 0.15, 20), False))
    Z.gravur(grund, lin, rand=0.8)
    asm.parts.append(grund)

    # Lage 2: Klappe vorne mit Briefschlitz und Namensschild
    m = max(1.8, Bk * 0.07)
    Bf, Hf = Bk - 2 * m, Hk - 2 * m
    fig = Z.Figur().add(Z.abrunden(K.rect(-Bf / 2, yk + m, Bf, Hf), Bf * 0.05, 3))
    hs = max(1.4, Hf * 0.09)
    fig.cut(Z.abrunden(K.rect(-Bf * 0.32, yk + m + Hf * 0.72, Bf * 0.64, hs), hs * 0.5, 4))
    klappe = Z.figur_teil(cfg, "klappe", fig, notes)
    lin = [(Z.abrunden(K.rect(-Bf * 0.4, yk + m + Hf * 0.66, Bf * 0.8, hs + Hf * 0.12), 1.0, 3), True)]
    Z.gravur(klappe, lin, rand=0.6)
    if name_text.strip():
        hsch = Hf * 0.34
        lin = [(Z.abrunden(K.rect(-Bf * 0.42, yk + m + Hf * 0.12, Bf * 0.84, hsch), 1.2, 3), True)]
        Z.gravur(klappe, lin, rand=0.6)
        M.text_gravur(klappe, name_text, 0.0, yk + m + Hf * 0.12 + hsch / 2, Bf * 0.78, hsch * 0.66, hsch * 0.55)
    asm.parts.append(klappe)

    # Fähnchen (seitlich ans Kastenende leimen)
    fl = max(Hk * 0.9, 6 * w)
    fb = max(w * 1.3, 2.2)
    fig = Z.Figur().add(K.rect(0, 0, fb, fl))
    fig.add([(0, fl - fl * 0.42), (fl * 0.48, fl - fl * 0.42 + fl * 0.02), (fl * 0.46, fl), (0, fl)])
    fig.add(K.circle(fb / 2, fb / 2, fb * 0.9, 16))
    asm.parts.append(Z.figur_teil(cfg, "faehnchen", fig, notes))

    # Briefe
    bb, bh = max(Bk * 0.5, 8 * w), max(Bk * 0.34, 5.5 * w)
    for k in range(int(briefe)):
        t = Part(f"brief{k + 1}", oriented(K.rect(0, 0, bb, bh), True))
        Z.gravur(t, [([(0.9, bh - 0.9), (bb / 2, bh * 0.42), (bb - 0.9, bh - 0.9)], False),
                     (Z.herz(bb * 0.5, bh * 0.25, bh * 0.28), True)], rand=0.5)
        asm.parts.append(t)

    # Sockel (Grasbuckel)
    rx, ry = max(Bk * 0.62, 18.0), max(T * 3 + 6, H * 0.12)
    sockel = Part("sockel", oriented(K.ellipse(0, 0, rx, ry, 0, 96), True))
    Z.schlitz(sockel, "pfosten", 0.0, 0.0, tw, T, 10)
    gras = []
    for k in range(9):
        a = math.pi * 2 * k / 9 + 0.3
        x, y = math.cos(a) * rx * 0.7, math.sin(a) * ry * 0.6
        if abs(y) < T + 2.5 and abs(x) < tw / 2 + 3:
            continue
        gras.append(([(x - 1.6, y - 1.0), (x - 0.6, y + 1.6), (x, y - 0.6), (x + 0.6, y + 1.8), (x + 1.6, y - 1.0)],
                     False))
    Z.gravur(sockel, gras, rand=1.0)
    asm.parts.append(sockel)
    asm.connect("pfosten:fuss", "sockel:pfosten")

    asm.notes.append("Den Pfosten in den Sockel stecken, die Klappe vorne auf den Kasten leimen (unten und seitlich "
                     "gleich viel Rand), das Fähnchen rechts an den Kasten. Briefe in den Schlitz stecken oder "
                     "danebenlegen.")
    asm.notes += list(dict.fromkeys(notes))
    return asm
