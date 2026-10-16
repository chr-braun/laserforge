"""
Wichtelfenster – Paket „Wichteltür“.

Fensterrahmen mit Sprossen (steckt mit zwei Zapfen in der Fensterbank), dahinter auf Wunsch eine Lage mit
gerafften Gardinen, dazu zwei Fensterläden mit Motiv und ein Blumenkasten für die Fensterbank.
"""
import importlib.util
import math
import os

from steckwerk import Assembly
from pakete import bibliothek, flag, num, sel

_spec = importlib.util.spec_from_file_location("swpaket_wichteltuer__lade_fenster",
                                               os.path.join(os.path.dirname(os.path.abspath(__file__)), "_lade.py"))
_m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_m)
M = _m.tuer()
Z, K = M.Z, M.K

SPROSSEN = [("kreuz", "Kreuz"), ("doppelkreuz", "doppeltes Kreuz"), ("senkrecht", "senkrecht"),
            ("waagrecht", "waagrecht"), ("keine", "keine")]
LAEDEN = [("keine", "keine")] + [(k, "mit " + v) for k, v in Z.AUSSCHNITTE[:5]] + [("glatt", "glatt")]
BLUMEN = [("keine", "kein Blumenkasten"), ("bluete", "Blüten"), ("stern", "Sternblumen"), ("sonne", "Sonnenblumen"),
          ("tannen", "Tannenzweige")]

UEBERSETZUNG = {"en": {
    "Wichtelfenster": "Elf window", "Wichteltür": "Elf door",
    "Fenster mit Sprossen auf einer Fensterbank, dazu Gardinen, Fensterläden mit Motiv und ein Blumenkasten.":
        "Window with glazing bars on a sill, plus curtains, shutters with a motif and a flower box.",
    "Breite": "Width", "Höhe": "Height", "Form": "Shape", "Rahmenbreite": "Frame width", "Rahmen": "Frame",
    "Sprossen": "Glazing bars", "Gardinen": "Curtains", "Fensterläden": "Shutters", "Blumenkasten": "Flower box",
    "Kreuz": "cross", "doppeltes Kreuz": "double cross", "senkrecht": "vertical", "waagrecht": "horizontal",
    "keine": "none", "glatt": "plain", "kein Blumenkasten": "no flower box", "Blüten": "Blossoms",
    "Sternblumen": "Star flowers", "Sonnenblumen": "Sunflowers", "Tannenzweige": "Fir twigs",
    "Das Fenster mit den Zapfen in die Fensterbank stecken.": "Push the window with its tabs into the sill.",
    "Die Gardinen-Lage hinten deckungsgleich ans Fenster leimen (steht hinter dem Fenster auf der Fensterbank).":
        "Glue the curtain layer flush to the back of the window (it stands behind the window on the sill).",
    "Die Fensterläden links und rechts neben das Fenster an die Wand kleben.":
        "Stick the shutters to the wall left and right of the window.",
    "Den Blumenkasten vorne auf die Fensterbank leimen.": "Glue the flower box onto the front of the sill.",
    "Tipp: Butterbrotpapier hinter die Scheiben kleben – mit einem LED-Licht dahinter leuchtet das Fenster.":
        "Tip: glue baking paper behind the panes – with an LED light behind it the window glows.",
}}

INFO = dict(
    label="Wichtelfenster", group="Wichteltür",
    desc="Fenster mit Sprossen auf einer Fensterbank, dazu Gardinen, Fensterläden mit Motiv und ein Blumenkasten.",
    params=[
        num("breite", "Breite", 50, 30, 160),
        num("hoehe", "Höhe", 60, 30, 200),
        sel("form", "Form", M.FORMEN, "bogen"),
        num("rahmen_b", "Rahmenbreite", 7, 4, 20),
        sel("rahmen", "Rahmen", M.RAHMEN, "holz"),
        sel("sprossen", "Sprossen", SPROSSEN, "kreuz"),
        flag("gardinen", "Gardinen", True),
        sel("laeden", "Fensterläden", LAEDEN, "herz"),
        sel("blumen", "Blumenkasten", BLUMEN, "bluete"),
    ],
)

WM = bibliothek("verzierungen").WM
INFO["params"] = WM.mit_massstab("wichtelfenster", INFO["params"])
UEBERSETZUNG["en"].update(WM.EN)


def build(cfg, name="wichtelfenster", breite=50.0, hoehe=60.0, form="bogen", rahmen_b=7.0, rahmen="holz",
          sprossen="kreuz", gardinen=True, laeden="herz", blumen="bluete", massstab="wichtel",
          wichtel=70.0):
    if massstab == "wichtel":                     # Maße passend zur Wichtelgröße
        _m = WM.wichtelmass("wichtelfenster", wichtel, INFO["params"], cfg)
        breite, hoehe, rahmen_b = _m["breite"], _m["hoehe"], _m["rahmen_b"]
    T = cfg.T
    B, H, rb = cfg.s(breite), cfg.s(hoehe), cfg.s(rahmen_b)
    w = Z.wmin(cfg)
    rb = max(rb, 2.5 * w)
    Wt, Ht = B - 2 * rb, H - 2 * rb
    if Wt < 14 or Ht < 14:
        raise ValueError("Das Fenster ist zu klein für diesen Rahmen – größer machen oder den Rahmen schmaler")
    notes = []
    asm = Assembly(name, params=dict(breite=B, hoehe=H, form=form, sprossen=sprossen, laeden=laeden, blumen=blumen))
    oeff = [(x, y + rb) for x, y in M.form(form, Wt, Ht)]
    aussen = M.form(form, B, H)
    # --- Fenster ---
    fig = Z.Figur().add(aussen)
    if rahmen in ("herzen", "sterne", "punkte") and rb >= 6:
        mid = [(x, y + rb * 0.5) for x, y in M.form(form, Wt + rb, Ht + rb)]
        fig.merge(Z.durchbruch(mid, rahmen, max(3 * w, rb * 0.5), closed=True))
    fig.cut(oeff)
    s = max(1.5 * w, min(Wt, Ht) * 0.06)
    xs_spr, ys_spr = [], []
    if sprossen in ("kreuz", "senkrecht"):
        xs_spr = [0.0]
    if sprossen == "doppelkreuz":
        xs_spr = [-Wt / 6, Wt / 6]
    top = M.oben_y(oeff, 0)
    if sprossen in ("kreuz", "waagrecht"):
        ys_spr = [rb + min(Ht * 0.55, (top - rb) * 0.55)]
    if sprossen == "doppelkreuz":
        ys_spr = [rb + (top - rb) * 0.36, rb + (top - rb) * 0.68]
    for x in xs_spr:
        fig.add(K.rect(x - s / 2, rb - 0.5, s, top - rb + 1))
    for y in ys_spr:
        fig.add(K.rect(-Wt / 2 - 0.5, y - s / 2, Wt + 1, s))
    fenster = Z.figur_teil(cfg, "fenster", fig, notes, unten_flach=True)
    tw = M.tabbreite(cfg, B, 0.2)
    xt = [-B * 0.3, B * 0.3]
    for k, x in enumerate(xt):
        Z.zapfen_unten(fenster, x, tw, T, f"fuss{k}", pos=10 + k)
    lin = []
    if rahmen == "holz":
        p = M.form(form, B - rb, H - rb)
        lin.append(([(x, y + rb / 2) for x, y in p], True))
    elif rahmen == "steine":
        mid = [(x, y + rb * 0.5) for x, y in M.form(form, Wt + rb, Ht + rb)]
        L = K.path_len(mid + [mid[0]])
        for (x, y), (tx, ty) in Z.entlang(mid, max(rb * 1.2, 6.0)):
            nx, ny = -ty, tx
            lin.append(([(x - nx * rb * 0.6, y - ny * rb * 0.6), (x + nx * rb * 0.6, y + ny * rb * 0.6)], False))
    Z.gravur(fenster, lin, rand=0.7)
    asm.parts.append(fenster)
    # --- Gardinen (Lage dahinter) ---
    m = max(2.2, T * 0.8)
    if gardinen:
        g = Z.Figur().add(aussen).cut(oeff)
        for sx in (-1, 1):
            # geraffter Vorhang: oben breit (folgt dem Bogen), an der Raffung schmal, unten wieder breiter
            x0 = sx * (Wt / 2 + 1.0)
            yr, yb = rb + (top - rb) * 0.42, rb - 0.5
            wo, wr, wu = Wt * 0.32, Wt * 0.1, Wt * 0.17
            oben = [(x0 - sx * wo * t, M.oben_y(oeff, sx * (Wt / 2 - wo * t)) + 1.0)
                    for t in (i / 12 for i in range(13))]
            y_o = oben[-1][1]
            seite = [(x0 - sx * (wo - (wo - wr) * t ** 0.7), y_o - (y_o - yr) * t) for t in (i / 12 for i in range(1, 13))]
            unten = [(x0 - sx * (wr + (wu - wr) * t ** 1.5), yr - (yr - yb) * t) for t in (i / 8 for i in range(1, 9))]
            g.add(oben + seite + unten + [(x0, yb)])
        # Volant oben
        if form == "eckig":
            g.add(K.rect(-Wt / 2 - 1, top - Ht * 0.12, Wt + 2, Ht * 0.12 + 1))
        hinten = Z.figur_teil(cfg, "gardinen", g, notes, unten_flach=True)
        asm.parts.append(hinten)
        asm.notes.append("Die Gardinen-Lage hinten deckungsgleich ans Fenster leimen (steht hinter dem Fenster auf "
                         "der Fensterbank).")
    # --- Fensterbank ---
    tiefe = m + 2 * T + max(10.0, H * 0.16)
    y_slot = m + (T if gardinen else 0.0) + T / 2
    bank = M.standplatte(cfg, "fensterbank", B + 2 * max(4.0, rb * 0.6), tiefe,
                         [(f"fenster{k}", x, y_slot, tw, 10 + k) for k, x in enumerate(xt)], vorne_rund=False)
    asm.parts.append(bank)
    for k in range(2):
        asm.connect(f"fenster:fuss{k}", f"fensterbank:fenster{k}")
    asm.notes.append("Das Fenster mit den Zapfen in die Fensterbank stecken.")
    # --- Fensterläden ---
    if laeden != "keine":
        wl, hl = Wt / 2 + rb * 0.4, min(H - rb, top + rb * 0.3)
        for sx, nm in ((-1, "laden_links"), (1, "laden_rechts")):
            umr = Z.abrunden([(0, 0), (wl, 0), (wl, hl), (0, hl)], min(wl, hl) * 0.08)
            lf = Z.Figur().add(umr)
            if laeden != "glatt":
                gm = min(wl * 0.55, hl * 0.22)
                lf.merge(Z.ausschnitt(laeden, wl / 2, hl * 0.72, gm))
            teil = Z.figur_teil(cfg, nm, lf, notes)
            lin = []
            n = max(3, int(wl / 5))
            for i in range(1, n):
                x = wl * i / n
                lin.append(([(x, 1.0), (x, hl - 1.0)], False))
            for y in (hl * 0.14, hl * 0.42):
                lin.append((Z.abrunden([(1.2, y), (wl - 1.2, y), (wl - 1.2, y + 3.5), (1.2, y + 3.5)], 0.6), True))
            Z.gravur(teil, lin, rand=0.8)
            if sx > 0:
                teil = Z.abbilden(teil, lambda q, wl=wl: (wl - q[0], q[1]))
            asm.parts.append(teil)
        asm.notes.append("Die Fensterläden links und rechts neben das Fenster an die Wand kleben.")
    # --- Blumenkasten ---
    if blumen != "keine":
        asm.parts.append(_blumenkasten(cfg, B * 0.86, max(10.0, H * 0.17), blumen, w, notes))
        asm.notes.append("Den Blumenkasten vorne auf die Fensterbank leimen.")
    asm.notes.append("Tipp: Butterbrotpapier hinter die Scheiben kleben – mit einem LED-Licht dahinter leuchtet "
                     "das Fenster.")
    asm.notes += notes
    return asm


def _blumenkasten(cfg, Wk, hk, blumen, w, notes):
    """Kastenfront mit Blumen, die oben herausschauen (unten gerade, steht auf der Fensterbank)."""
    fig = Z.Figur().add(Z.abrunden([(-Wk / 2, 0), (Wk / 2, 0), (Wk / 2 + 1.5, hk), (-Wk / 2 - 1.5, hk)], 1.0))
    n = max(3, int(Wk / max(9.0, hk * 0.9)))
    r = min(Wk / n * 0.42, hk * 0.5)
    for i in range(n):
        x = -Wk / 2 + Wk * (i + 0.5) / n
        h = hk + r * (1.1 if i % 2 else 1.7)
        if blumen == "tannen":
            fig.merge(Z.zweig(h - hk * 0.4 + r, "tanne", w).map(
                lambda p, x=x: (x + p[1], hk * 0.4 + p[0])))
            continue
        fig.line([(x, hk - 1), (x, h)], max(1.4 * w, r * 0.22))
        fig.add(Z.blatt((x, hk + (h - hk) * 0.3), math.pi * (0.25 if i % 2 else 0.75), r * 0.9, r * 0.4))
        if blumen == "stern":
            fig.add(K.star(x, h, r, r * 0.5, 5))
        else:
            k = 8 if blumen == "sonne" else 5
            for j in range(k):
                a = 2 * math.pi * j / k + math.pi / 2
                fig.add(K.circle(x + math.cos(a) * r * 0.55, h + math.sin(a) * r * 0.55, r * (0.3 if k == 8 else 0.45), 20))
            fig.add(K.circle(x, h, r * 0.45, 20))
        if r * 0.4 >= 2 * w:
            fig.cut(K.circle(x, h, r * 0.2, 16))
    teil = Z.figur_teil(cfg, "blumenkasten", fig, notes, unten_flach=True)
    lin = [([(-Wk / 2 + 1.5, hk * y), (Wk / 2 - 1.5, hk * y)], False) for y in (0.36, 0.68)]
    Z.gravur(teil, lin, rand=0.8)
    return teil
