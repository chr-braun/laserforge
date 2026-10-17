"""
Gartenzaun – Paket „Wichtel“.

Lattenzaun in zwei Lagen: hinten die Latten mit Spitzen, Rundköpfen oder Herzen (auf Wunsch mit
Herzausschnitt), vorne die beiden Querriegel zum Aufleimen; dazu Pfosten mit Kugelkappe an beiden Enden.
Der Zaun steckt mit zwei Zapfen in kleinen Füßen.
"""
import importlib.util
import math
import os

from steckwerk import Assembly, Part, oriented
from pakete import flag, num, sel

_spec = importlib.util.spec_from_file_location("swpaket_wichtel__lade_zaun",
                                               os.path.join(os.path.dirname(os.path.abspath(__file__)), "_lade.py"))
_m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_m)
M = _m.markt()
Z, K = M.Z, M.K

KOEPFE = [("spitz", "spitz"), ("rund", "rund"), ("herz", "Herz")]

UEBERSETZUNG = {"en": {
    "Gartenzaun": "Garden fence",
    "Lattenzaun in zwei Lagen: Latten mit Spitzen, Rundköpfen oder Herzen, aufgeleimte Querriegel, Pfosten mit "
    "Kugelkappe – steckt in kleinen Füßen.":
        "Two-layer picket fence: pickets with points, round tops or hearts, glued-on rails, posts with ball caps – "
        "plugs into small feet.",
    "Länge": "Length", "Höhe": "Height", "Lattenkopf": "Picket top", "spitz": "pointed", "rund": "round",
    "Herz": "heart", "Herzausschnitt": "Heart cut-out", "Ausschnitt in jeder zweiten Latte":
        "cut-out in every other picket",
}}

INFO = dict(
    label="Gartenzaun", group="Wichtel",
    desc="Lattenzaun in zwei Lagen: Latten mit Spitzen, Rundköpfen oder Herzen, aufgeleimte Querriegel, Pfosten mit "
         "Kugelkappe – steckt in kleinen Füßen.",
    params=[
        num("laenge", "Länge", 112, 50, 350),
        num("hoehe", "Höhe", 35, 22, 120),
        sel("kopf", "Lattenkopf", KOEPFE, "spitz"),
        flag("ausschnitt", "Herzausschnitt", True, help="Ausschnitt in jeder zweiten Latte"),
    ],
)
INFO["params"] = M.mit_massstab("gartenzaun", INFO["params"])
UEBERSETZUNG["en"].update(M.EN)


def build(cfg, name="gartenzaun", laenge=112.0, hoehe=35.0, kopf="spitz", ausschnitt=True,
          massstab="wichtel", wichtel=70.0):
    if massstab == "wichtel":
        _m = M.mass("gartenzaun", wichtel, INFO["params"], cfg)
        laenge, hoehe = _m["laenge"], _m["hoehe"]
    T = cfg.T
    L, H = cfg.s(laenge), cfg.s(hoehe)
    w = Z.wmin(cfg)
    notes = []
    asm = Assembly(name, params=dict(laenge=L, hoehe=H))
    pb = max(2.6 * T, H * 0.2, cfg.min_tab_width + 4.2)   # Pfostenbreite
    lb = max(3.2 * w, H * 0.14)                     # Lattenbreite
    lz = max(w * 1.1, lb * 0.55)                    # Lücke
    innen = L - 2 * pb
    n = max(2, int((innen - lz) / (lb + lz)))
    lz = (innen - n * lb) / (n + 1)
    hr = max(w * 1.6, H * 0.12)                     # Riegelhöhe
    yr = [H * 0.17, H * 0.5]
    fig = Z.Figur()
    hl = H * 0.86
    for k in range(n):
        x = -L / 2 + pb + lz + k * (lb + lz) + lb / 2
        if kopf == "spitz":
            fig.add([(x - lb / 2, H * 0.06), (x + lb / 2, H * 0.06), (x + lb / 2, hl - lb * 0.6), (x, hl),
                     (x - lb / 2, hl - lb * 0.6)])
        elif kopf == "rund":
            fig.add(K.rect(x - lb / 2, H * 0.06, lb, hl - lb / 2 - H * 0.06), K.circle(x, hl - lb / 2, lb / 2, 24))
        else:
            fig.add(K.rect(x - lb / 2, H * 0.06, lb, hl - lb - H * 0.06), Z.herz(x, hl - lb * 0.55, lb * 1.25))
        if ausschnitt and k % 2 == 1 and lb >= 4 * w:
            fig.merge(Z.ausschnitt("herz", x, (yr[0] + yr[1]) / 2 + hr / 2, min(lb * 0.62, (yr[1] - yr[0] - hr) * 0.8)))
    for yy in yr:                                   # Riegel (hinten, halten die Latten zusammen)
        fig.add(K.rect(-L / 2 + pb - 0.5, yy, innen + 1.0, hr))
    for sg in (-1, 1):                              # Pfosten mit Kugelkappe
        x = sg * (L / 2 - pb / 2)
        fig.add(K.rect(x - pb / 2, 0, pb, H - pb * 0.6))
        fig.add(K.circle(x, H - pb * 0.45, pb * 0.55, 32))
        fig.add(K.rect(x - pb * 0.62, H - pb * 1.05, pb * 1.24, max(1.6, pb * 0.22)))
    zaun = Z.figur_teil(cfg, "zaun", fig, notes, unten_flach=True)
    tw = max(cfg.min_tab_width + 0.6, min(pb - 3.4, cfg.tab_factor * T))
    for k, sg in enumerate((-1, 1)):
        Z.zapfen_unten(zaun, sg * (L / 2 - pb / 2), tw, T, f"fuss{k}", 10 + k)
    lin = []
    for sg in (-1, 1):
        x = sg * (L / 2 - pb / 2)
        lin.append(([(x - pb * 0.12, 2.0), (x + pb * 0.08, (H - pb) * 0.6)], False))
    Z.gravur(zaun, lin, rand=0.7)
    asm.parts.append(zaun)
    # Querriegel vorne (aufleimen): mit Maserung und Nagelköpfen
    for k, yy in enumerate(yr):
        r = Z.figur_teil(cfg, f"riegel{k + 1}", Z.Figur().add(K.rect(-innen / 2, 0, innen, hr)), notes)
        lin = [([(-innen / 2 + 1.5, hr * 0.5), (innen / 2 - 1.5, hr * 0.5)], False)]
        for j in range(n):
            x = -innen / 2 + lz + j * (lb + lz) + lb / 2
            if hr >= 3.2:
                lin.append((K.circle(x, hr * 0.5, max(0.35, hr * 0.1), 10), True))
        Z.gravur(r, lin if hr < 3.2 else lin[1:], rand=0.5)
        asm.parts.append(r)
    # Füße
    Df = max(4 * T + 4, H * 0.4)
    Lf = pb + 2 * max(3.0, T)
    for k in range(2):
        f = Part(f"fuss{k + 1}", oriented(Z.abrunden(K.rect(-Lf / 2, -Df / 2, Lf, Df), min(Lf, Df) * 0.35, 5), True))
        Z.schlitz(f, "zaun", 0.0, 0.0, tw, T, 10 + k)
        asm.parts.append(f)
        asm.connect(f"zaun:fuss{k}", f"fuss{k + 1}:zaun")
    asm.notes.append("Den Zaun mit beiden Pfosten in die Füße stecken, die Querriegel vorne auf die hinteren Riegel "
                     "leimen. Mehrere Zäune lassen sich Pfosten an Pfosten aneinanderreihen.")
    asm.notes += list(dict.fromkeys(notes))
    return asm
