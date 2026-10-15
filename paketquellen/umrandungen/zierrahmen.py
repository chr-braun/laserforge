"""
Zierrahmen – Umrandung für Schilder, Uhren, Spiegel oder Bilder (Paket „Umrandungen“).

Der Rahmen hat ein Fenster mit frei wählbarem Innenmaß. Dahinter wahlweise ein Schild mit graviertem Text,
das durch das Fenster zu sehen ist. Hinstellen im Sockel, aufhängen oder einfach aufkleben.
"""
import importlib.util
import os

from steckwerk import Assembly
from pakete import flag, num, sel, txt

_spec = importlib.util.spec_from_file_location("swpaket_umrandungen__lade_zr",
                                               os.path.join(os.path.dirname(os.path.abspath(__file__)), "_lade.py"))
_m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_m)
R = _m.rahmen()
Z, K = R.Z, R.K

UEBERSETZUNG = {"en": {
    "Zierrahmen": "Ornamental frame",
    "Verzierte Umrandung mit frei wählbarem Innenmaß – für Namensschilder, Uhren, Spiegel oder Bilder. Auf Wunsch mit Schild und graviertem Text dahinter.":
        "Decorated surround with any inner size – for name signs, clocks, mirrors or pictures. Optionally with an engraved sign behind it.",
    "Innenbreite": "Inner width", "Innenhöhe": "Inner height", "Schild dahinter": "Sign behind",
    "Text auf dem Schild": "Text on the sign", "Fuß": "Stand", "ohne (zum Aufkleben)": "none (to glue on)",
    "Sockel zum Hinstellen": "Base to stand", "Schlüsselloch zum Aufhängen": "Keyhole for hanging",
    "Rahmen und Schild deckungsgleich aufeinander leimen.": "Glue frame and sign on top of each other, edges flush.",
    "Mit den beiden Zapfen in die Schlitze des Sockels stecken.": "Push the two tabs into the slots of the base.",
}}

INFO = dict(
    label="Zierrahmen", group="Umrandungen",
    desc="Verzierte Umrandung mit frei wählbarem Innenmaß – für Namensschilder, Uhren, Spiegel oder Bilder. "
         "Auf Wunsch mit Schild und graviertem Text dahinter.",
    params=[
        num("innen_b", "Innenbreite", 110, 30, 300),
        num("innen_h", "Innenhöhe", 60, 20, 300),
        sel("form", "Form", Z.FORMEN, "kartusche"),
        num("rand", "Randbreite", 22, 12, 60),
        sel("stil", "Stil", R.STILE, "filigran"),
        sel("fuellung", "Füllung", R.FUELLUNGEN, "bluete", when={"stil": ["filigran"]}),
        sel("durchbruch", "Durchbrüche", [("keine", "keine")] + Z.DURCHBRUECHE, "punkte", when={"stil": ["schlicht"]}),
        sel("kante", "Kante", [("keine", "keine")] + Z.KANTEN, "perlen"),
        sel("ecken", "Ecken", R.ECKEN, "keine"),
        flag("schild", "Schild dahinter", True),
        txt("text", "Text auf dem Schild", "Familie|Sonnenschein", "| = neue Zeile", when={"schild": [True]},
            symbols=True),
        sel("fuss", "Fuß", [("keine", "ohne (zum Aufkleben)"), ("sockel", "Sockel zum Hinstellen"),
                            ("haken", "Schlüsselloch zum Aufhängen")], "haken"),
    ],
)


def build(cfg, name="zierrahmen", innen_b=110.0, innen_h=60.0, form="kartusche", rand=22.0, stil="filigran",
          fuellung="bluete", durchbruch="punkte", kante="perlen", ecken="keine", schild=True,
          text="Familie|Sonnenschein", fuss="haken"):
    T = cfg.T
    Wi, Hi, rand = cfg.s(innen_b), cfg.s(innen_h), cfg.s(rand)
    notes = []
    aussen, fenster, y_cut = R.form_und_fenster(form, Wi, Hi, rand, fuss == "sockel")
    rahmen = R.vorderteil(cfg, "rahmen", aussen, fenster, y_cut, stil, fuellung, kante, ecken, durchbruch, form, notes)
    asm = Assembly(name, params=dict(innen=(Wi, Hi), form=form, rand=rand, stil=stil, fuss=fuss))
    asm.parts.append(rahmen)
    traeger = rahmen
    if schild:
        platte = R.platte(cfg, "schild", aussen, y_cut, 1.5, notes)
        if text.strip():
            fx0, fx1 = min(p[0] for p in fenster), max(p[0] for p in fenster)
            fy0, fy1 = min(p[1] for p in fenster) - y_cut, max(p[1] for p in fenster) - y_cut
            try:
                st, cap = Z.text_in_box(text, (fx0 + fx1) / 2, (fy0 + fy1) / 2, (fx1 - fx0) * 0.8, (fy1 - fy0) * 0.7,
                                        min(16.0, (fy1 - fy0) * 0.4), 3.0, 0.08)
            except ValueError:
                raise ValueError(f"Der Text „{text.replace('|', ' ')}“ passt nicht ins Fenster – kürzer fassen oder "
                                 f"das Innenmaß vergrößern")
            Z.gravur(platte, [(s, False) for s in st], rand=0.8)
        asm.parts.append(platte)
        traeger = platte
        asm.notes.append("Rahmen und Schild deckungsgleich aufeinander leimen.")
    if fuss == "sockel":
        traeger_neu = R.gerade_unten(traeger)
        asm.parts[asm.parts.index(traeger)] = traeger_neu
        traeger = traeger_neu
        W_r = max(p[0] for p in traeger.outline) - min(p[0] for p in traeger.outline)
        tw = max(2 * T + 2, min(16.0, W_r * 0.16))
        xs = R.fuss_x(traeger, tw, 0.26)
        for k, x in enumerate(xs):
            Z.zapfen_unten(traeger, x, tw, T, f"fuss{k}", pos=200 + k)
        H_r = max(p[1] for p in traeger.outline)
        tiefe = max(30.0, min(60.0, H_r * 0.35))
        asm.parts.append(R.sockel(cfg, "sockel", W_r * 0.86, tiefe, xs, tw, -T * 0.5 if schild else 0.0, 200, "punkte"))
        for k in range(len(xs)):
            asm.connect(f"{traeger.name}:fuss{k}", f"sockel:schlitz{k}")
        asm.notes.append("Mit den beiden Zapfen in die Schlitze des Sockels stecken.")
    elif fuss == "haken":
        if not schild:
            raise ValueError("Zum Aufhängen braucht der Rahmen das Schild dahinter (Schlüsselloch) – Schild einschalten")
        H_r = max(p[1] for p in traeger.outline)
        traeger.add_hole(R.schluesselloch(0, H_r - max(9.0, rand * 0.5)))
    asm.notes += notes
    return asm
