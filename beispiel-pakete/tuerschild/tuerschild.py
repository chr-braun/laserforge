"""
Türschild – Modell aus dem Paket „Türschild“.

Koordinaten in mm, y nach oben. Außenkontur gegen den Uhrzeigersinn, Löcher im Uhrzeigersinn
(add_hole dreht automatisch richtig). Gravuren über add_engrave oder – kollisionsfrei – über
models._deko (Canvas, sign, styled_line …).
"""
from steckwerk import Assembly, Part, circle, rect
from models import _deko as dk
from pakete import num, sel, txt

# Englische Texte für die Sprachwahl: deutscher Text → englischer Text
UEBERSETZUNG = {"en": {
    "Türschild": "Door sign",
    "Hängeschild mit Text, Rahmen und zwei Löchern zum Aufhängen.":
        "Hanging sign with text, frame and two holes for hanging.",
    "Rahmen": "Frame",
    "Schild an einer Kordel durch die beiden Löcher aufhängen.": "Hang the sign on a cord through both holes.",
}}

INFO = dict(
    label="Türschild",
    group="Pakete",
    desc="Hängeschild mit Text, Rahmen und zwei Löchern zum Aufhängen.",
    params=[
        num("width", "Breite", 120, 60, 300),
        num("height", "Höhe", 60, 30, 200),
        txt("text", "Text", "Willkommen", "| = neue Zeile"),
        sel("rahmen", "Rahmen", dk.SIGNS, "holz"),
    ],
)


def build(cfg, name="tuerschild", width=120.0, height=60.0, text="Willkommen", rahmen="holz"):
    W, H = cfg.s(width), cfg.s(height)
    r = min(6.0, H * 0.15)
    outline = rect(-W / 2, 0, W, H)
    part = Part(name, outline)
    for x in (-W / 2 + 8, W / 2 - 8):                       # Aufhängelöcher
        part.add_hole(circle(x, H - 8, 2.0, cfg.arc_tolerance))
    if text.strip():
        cv = dk.Canvas(part, margin=2.0, seed=cfg.seed)
        cands = [(-W / 2 + 14, 4, W / 2 - 14, H - 14), (-W / 2 + 6, 4, W / 2 - 6, H - 14)]
        if dk.sign(cv, text, rahmen, cands, "normal", "gross", min_h=3.0, max_cap=0.3 * H,
                   anchor="mitte", tol=cfg.arc_tolerance) is None:
            raise ValueError(f"Text {text!r} passt nicht aufs Schild – kürzer fassen oder größer machen")
    asm = Assembly(name, params=dict(width=W, height=H, text=text, rahmen=rahmen))
    asm.parts.append(part)
    asm.notes.append("Schild an einer Kordel durch die beiden Löcher aufhängen.")
    return asm
