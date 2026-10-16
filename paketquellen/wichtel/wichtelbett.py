"""
Wichtelbett – Paket „Wichtel“.

Kopf- und Fußteil mit Füßen und Ausschnittmotiv, die Liegefläche steckt mit je zwei Zapfen dazwischen.
Kissen und Bettdecke sind auf die Liegefläche graviert, der Name auf das Kopfteil.
"""
import importlib.util
import math
import os

from steckwerk import Assembly
from pakete import bibliothek, num, sel, txt

_spec = importlib.util.spec_from_file_location("swpaket_wichtel__lade_bett",
                                               os.path.join(os.path.dirname(os.path.abspath(__file__)), "_lade.py"))
_m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_m)
M = _m.moebel()
Z, K = M.Z, M.K

DECKEN = [("karo", "kariert"), ("herzen", "mit Herzen"), ("sterne", "mit Sternen"), ("streifen", "gestreift"),
          ("glatt", "glatt"), ("keine", "ohne Decke")]

UEBERSETZUNG = {"en": {
    "Wichtelbett": "Elf bed", "Wichtelmöbel": "Elf furniture",
    "Bett zum Stecken: Kopf- und Fußteil mit Motiv, Liegefläche mit graviertem Kissen und Bettdecke, Name am Kopfteil.":
        "Slot-together bed: head and foot board with a motif, bed surface with engraved pillow and blanket, name on the headboard.",
    "Länge": "Length", "Breite": "Width", "Liegehöhe": "Bed height", "Kopfteil": "Headboard height",
    "Fußteil": "Footboard height", "Form oben": "Top shape", "Motiv": "Motif", "Bettdecke": "Blanket",
    "Name am Kopfteil": "Name on the headboard", "kariert": "checked", "mit Herzen": "with hearts",
    "mit Sternen": "with stars", "gestreift": "striped", "glatt": "plain", "ohne Decke": "no blanket",
    "geschwungen": "curved", "Rundbogen": "round arch", "gerade, abgerundet": "straight, rounded", "Giebel": "gable",
    "keins": "none",
    "Die Liegefläche mit ihren Zapfen in die Schlitze von Kopf- und Fußteil stecken (Kissen zum Kopfteil).":
        "Push the bed surface with its tabs into the slots of head and foot board (pillow towards the headboard).",
}}

INFO = dict(
    label="Wichtelbett", group="Wichtel",
    desc="Bett zum Stecken: Kopf- und Fußteil mit Motiv, Liegefläche mit graviertem Kissen und Bettdecke, "
         "Name am Kopfteil.",
    params=[
        num("laenge", "Länge", 80, 40, 220),
        num("breite", "Breite", 45, 25, 140),
        num("liegehoehe", "Liegehöhe", 18, 10, 60),
        num("kopfteil", "Kopfteil", 50, 25, 150),
        num("fussteil", "Fußteil", 32, 18, 120),
        sel("oben", "Form oben", M.OBEN, "bogen"),
        sel("motiv", "Motiv", M.MOTIVE, "mond"),
        sel("decke", "Bettdecke", DECKEN, "karo"),
        txt("name_text", "Name am Kopfteil", "", "z. B. der Name des Wichtels", symbols=True),
    ],
)

WM = bibliothek("verzierungen").WM
INFO["params"] = WM.mit_massstab("wichtelbett", INFO["params"])
UEBERSETZUNG["en"].update(WM.EN)


def build(cfg, name="wichtelbett", laenge=80.0, breite=45.0, liegehoehe=18.0, kopfteil=50.0, fussteil=32.0,
          oben="bogen", motiv="mond", decke="karo", name_text="", massstab="wichtel",
          wichtel=70.0):
    if massstab == "wichtel":                     # Maße passend zur Wichtelgröße
        _m = WM.wichtelmass("wichtelbett", wichtel, INFO["params"], cfg)
        laenge, breite, liegehoehe, kopfteil, fussteil = _m["laenge"], _m["breite"], _m["liegehoehe"], _m["kopfteil"], _m["fussteil"]
    T = cfg.T
    L, B, hl = cfg.s(laenge), cfg.s(breite), cfg.s(liegehoehe)
    Hk, Hf = cfg.s(kopfteil), cfg.s(fussteil)
    notes = []
    asm = Assembly(name, params=dict(laenge=L, breite=B, liegehoehe=hl, oben=oben, motiv=motiv, decke=decke))
    ue = max(2.0, T)                                   # Kopf-/Fußteil stehen seitlich etwas über
    Bk = B + 2 * ue
    Hf = max(Hf, hl + 2 * T + 6)
    Hk = max(Hk, Hf)
    tw = M.tabbreite(cfg, B, 0.2)
    ys = [B * 0.25, B * 0.75]
    if hl < 2 * T + 5:
        raise ValueError("Die Liegehöhe ist für diese Materialstärke zu klein")
    for teil, Hh, pos0 in (("kopfteil", Hk, 40), ("fussteil", Hf, 50)):
        schl = [(f"liege{k}", ue + y, hl - T / 2, tw, pos0 + k, 0.0) for k, y in enumerate(ys)]
        oben_frei = hl + 4.0
        txt_h = min(8.0, (Hh - oben_frei) * 0.25) if (teil == "kopfteil" and name_text.strip()) else 0.0
        box = (Bk * 0.2, oben_frei + txt_h + (2.5 if txt_h else 0.0), Bk * 0.8, Hh - 4.0 - min(Bk / 2, Hh * 0.35) * 0.12)
        p = M.wange(cfg, teil, Bk, Hh, oben, motiv, notes, schl, box if box[3] - box[1] > 8 else None)
        if txt_h:
            M.text_gravur(p, name_text, Bk / 2, oben_frei + txt_h / 2, Bk * 0.8, txt_h, txt_h)
        asm.parts.append(p)
    Ll = L - M.EINZUG
    liege = Z.brett("liegeflaeche", Ll, B, T,
                    links=[(y, tw, f"kopf{k}", 40 + k) for k, y in enumerate(ys)],
                    rechts=[(y, tw, f"fuss{k}", 50 + k) for k, y in enumerate(ys)])
    _bettzeug(liege, Ll, B, decke)
    asm.parts.append(liege)
    for k in range(2):
        asm.connect(f"liegeflaeche:kopf{k}", f"kopfteil:liege{k}")
        asm.connect(f"liegeflaeche:fuss{k}", f"fussteil:liege{k}")
    asm.notes.append("Die Liegefläche mit ihren Zapfen in die Schlitze von Kopf- und Fußteil stecken "
                     "(Kissen zum Kopfteil).")
    asm.notes += notes
    return asm


def _rrect(x0, y0, x1, y1, r):
    return Z.abrunden([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], r)


def _bettzeug(part, L, B, decke):
    """Kissen am Kopfende (x = 0), Bettdecke darüber – alles graviert."""
    m = 2.5
    linien = []
    kl = min(L * 0.2, B * 0.55)
    kissen = _rrect(m, B * 0.14, m + kl, B * 0.86, min(kl, B) * 0.25)
    linien.append((kissen, True))
    linien.append(([(m + kl * 0.3, B * 0.2), (m + kl * 0.5, B * 0.5), (m + kl * 0.3, B * 0.8)], False))  # Delle
    if decke == "keine":
        Z.gravur(part, linien, rand=0.8)
        return
    x0, x1 = m + kl + 2.0, L - m
    y0, y1 = m, B - m
    linien.append((_rrect(x0, y0, x1, y1, 2.0), True))
    umschlag = x0 + min(10.0, (x1 - x0) * 0.16)
    linien.append(([(umschlag, y0 + 0.8), (umschlag, y1 - 0.8)], False))
    if decke == "karo":
        n = max(2, int((x1 - umschlag) / 9))
        for i in range(1, n):
            x = umschlag + (x1 - umschlag) * i / n
            linien.append(([(x, y0 + 0.8), (x, y1 - 0.8)], False))
        nb = max(2, int((y1 - y0) / 9))
        for j in range(1, nb):
            y = y0 + (y1 - y0) * j / nb
            linien.append(([(umschlag + 0.8, y), (x1 - 0.8, y)], False))
    elif decke == "streifen":
        n = max(2, int((x1 - umschlag) / 5))
        for i in range(1, n):
            x = umschlag + (x1 - umschlag) * i / n
            linien.append(([(x, y0 + 0.8), (x, y1 - 0.8)], False))
    elif decke in ("herzen", "sterne"):
        g = min(7.0, (y1 - y0) / 4)
        nx = max(1, int((x1 - umschlag) / (g * 2.0)))
        ny = max(1, int((y1 - y0) / (g * 2.0)))
        for i in range(nx):
            for j in range(ny):
                cx = umschlag + (x1 - umschlag) * (i + 0.5) / nx
                cy = y0 + (y1 - y0) * (j + 0.5) / ny + (g * 0.4 if i % 2 else 0)
                if cy + g / 2 > y1 - 1:
                    continue
                if decke == "herzen":
                    linien.append((Z.herz(cx, cy - g * 0.1, g, rot=-math.pi / 2), True))
                else:
                    linien.append((K.star(cx, cy, g * 0.5, g * 0.22, 5, 0.0), True))
    Z.gravur(part, linien, rand=0.8)
