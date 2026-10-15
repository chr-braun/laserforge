"""
Wichtelbank – Paket „Wichtelmöbel“.

Zwei Seitenwangen mit Füßen und Ausschnittmotiv, der Sitz steckt mit je zwei Zapfen in den Wangen,
die Lehne steckt mit zwei Zapfen von oben im Sitz. Hält ohne Leim.
"""
import importlib.util
import os

from steckwerk import Assembly
from pakete import flag, num, sel, txt

_spec = importlib.util.spec_from_file_location("swpaket_wichtelmoebel__lade_bank",
                                               os.path.join(os.path.dirname(os.path.abspath(__file__)), "_lade.py"))
_m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_m)
M = _m.moebel()
Z, K = M.Z, M.K

UEBERSETZUNG = {"en": {
    "Wichtelbank": "Elf bench", "Wichtelmöbel": "Elf furniture",
    "Kleine Steckbank mit Lehne: Wangen mit Füßen und Ausschnittmotiv, Sitz und Lehne werden gesteckt.":
        "Small slot-together bench with backrest: side panels with feet and a cut-out motif, seat and backrest just plug in.",
    "Länge": "Length", "Tiefe": "Depth", "Sitzhöhe": "Seat height", "Lehne": "Backrest", "Lehnenhöhe": "Backrest height",
    "Wangen oben": "Side panel top", "Motiv": "Motif", "Kante der Lehne": "Backrest edge", "Text auf der Lehne": "Text on the backrest",
    "geschwungen": "curved", "Rundbogen": "round arch", "gerade, abgerundet": "straight, rounded", "Giebel": "gable",
    "keins": "none", "keine": "none",
    "Den Sitz mit seinen Zapfen in die Schlitze der beiden Wangen stecken.":
        "Push the seat with its tabs into the slots of both side panels.",
    "Die Lehne von oben in die hinteren Schlitze des Sitzes stecken.":
        "Push the backrest from above into the rear slots of the seat.",
}}

INFO = dict(
    label="Wichtelbank", group="Wichtelmöbel",
    desc="Kleine Steckbank mit Lehne: Wangen mit Füßen und Ausschnittmotiv, Sitz und Lehne werden gesteckt.",
    params=[
        num("laenge", "Länge", 70, 40, 200),
        num("tiefe", "Tiefe", 26, 18, 80),
        num("sitzhoehe", "Sitzhöhe", 28, 16, 90),
        flag("lehne", "Lehne", True),
        num("lehnenhoehe", "Lehnenhöhe", 26, 12, 90, when={"lehne": [True]}),
        sel("oben", "Wangen oben", M.OBEN, "geschwungen"),
        sel("motiv", "Motiv", M.MOTIVE, "herz"),
        sel("kante", "Kante der Lehne", [("keine", "keine")] + Z.KANTEN, "bogen", when={"lehne": [True]}),
        txt("text", "Text auf der Lehne", "", "z. B. „Wichtelruh“", when={"lehne": [True]}, symbols=True),
    ],
)


def build(cfg, name="wichtelbank", laenge=70.0, tiefe=26.0, sitzhoehe=28.0, lehne=True, lehnenhoehe=26.0,
          oben="geschwungen", motiv="herz", kante="bogen", text=""):
    T = cfg.T
    L, D, hs = cfg.s(laenge), cfg.s(tiefe), cfg.s(sitzhoehe)
    notes = []
    asm = Assembly(name, params=dict(laenge=L, tiefe=D, sitzhoehe=hs, lehne=lehne, oben=oben, motiv=motiv))
    tw = M.tabbreite(cfg, D)
    ys = [D * 0.3, D * 0.7]                       # Zapfen-Mitten über die Tiefe (symmetrisch)
    if hs < 3 * T + 6:
        raise ValueError("Die Sitzhöhe ist für diese Materialstärke zu klein")
    # Wangen: etwas höher als der Sitz (Armlehne)
    ha = max(6.0, min(hs * 0.4, 18.0))
    Hw = hs + ha
    fh = M.fussbogen_hoehe(cfg, D, Hw)
    box = (D * 0.2, fh + 2.5, D * 0.8, hs - T - 3.0)
    for seite, pos0 in (("links", 10), ("rechts", 20)):
        schl = [(f"sitz{k}", y, hs - T / 2, tw, pos0 + k, 0.0) for k, y in enumerate(ys)]
        asm.parts.append(M.wange(cfg, f"wange_{seite}", D, Hw, oben, motiv, notes, schl, box))
    # Sitz: Brett zwischen den Wangen, Zapfen an den Stirnseiten
    Ls = L - M.EINZUG
    sitz = Z.brett("sitz", Ls, D, T,
                   links=[(y, tw, f"links{k}", 10 + k) for k, y in enumerate(ys)],
                   rechts=[(y, tw, f"rechts{k}", 20 + k) for k, y in enumerate(ys)])
    asm.parts.append(sitz)
    for k in range(2):
        asm.connect(f"sitz:links{k}", f"wange_links:sitz{k}")
        asm.connect(f"sitz:rechts{k}", f"wange_rechts:sitz{k}")
    asm.notes.append("Den Sitz mit seinen Zapfen in die Schlitze der beiden Wangen stecken.")
    if lehne:
        Hl = cfg.s(lehnenhoehe)
        Wl = Ls - 1.0
        tlw = M.tabbreite(cfg, Wl, 0.18)
        xs = [-Wl * 0.28, Wl * 0.28]
        m = max(2.2, T * 0.8)
        y_l = D - m - T / 2                       # Lehne steht hinten auf dem Sitz
        for k, x in enumerate(xs):
            Z.schlitz(sitz, f"lehne{k}", Ls / 2 + x, y_l, tlw, T, 30 + k)
        umr = [(x - Wl / 2, y) for x, y in M.umriss(Wl, Hl, "bogen" if oben == "bogen" else
                                                    ("spitz" if oben == "spitz" else "geschwungen"))]
        if oben == "gerade":
            umr = Z.abrunden([(-Wl / 2, 0), (Wl / 2, 0), (Wl / 2, Hl), (-Wl / 2, Hl)], min(Wl, Hl) * 0.14)
        w = Z.wmin(cfg)
        fig = Z.Figur().add(umr)
        if kante != "keine":
            g = max(3.2 * w, min(5.0, Hl * 0.16))
            fig.merge(Z.kante(umr, kante, g, w, ausser=lambda p: p[1] < Hl * 0.45 or abs(p[0]) > Wl / 2 - g))
        txt_h = 0.0
        if text.strip():
            txt_h = min(9.0, Hl * 0.32)
        if motiv != "keine":
            g = min(Hl - txt_h - 6.0, Wl * 0.3) * 0.75
            if g >= 3 * w:
                for x in ((0.0,) if Wl < 60 else (-Wl * 0.3, Wl * 0.3)) if txt_h else (0.0,):
                    fig.merge(Z.ausschnitt(motiv, x, Hl * 0.5 if not txt_h else Hl * 0.42, g))
        rl = Z.figur_teil(cfg, "lehne", fig, notes, unten_flach=True)
        for k, x in enumerate(xs):
            Z.zapfen_unten(rl, x, tlw, T, f"fuss{k}", pos=30 + k)
        if txt_h:
            M.text_gravur(rl, text, 0.0, Hl * 0.42 if motiv == "keine" or Wl >= 60 else Hl * 0.22,
                          Wl * (0.4 if motiv != "keine" and Wl >= 60 else 0.8), txt_h, txt_h)
        asm.parts.append(rl)
        for k in range(2):
            asm.connect(f"lehne:fuss{k}", f"sitz:lehne{k}")
        asm.notes.append("Die Lehne von oben in die hinteren Schlitze des Sitzes stecken.")
    asm.notes += notes
    return asm
