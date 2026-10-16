"""
Wichtelzimmer – Paket „Wichtel“.

Baut aus Möbeln, Tür, Fenster und Zubehör dieses Pakets ein komplettes Zimmer im selben Maßstab: Alle Maße
folgen der Höhe der Wichtelfigur. Jedes Stück kommt als eigene Baugruppe (eigene Datei beim Export).
"""
import importlib.util
import os

from models import wichtel as figur
from pakete import bibliothek, flag, integer, num, sel, txt

_spec = importlib.util.spec_from_file_location("swpaket_wichtel__lade_zimmer",
                                               os.path.join(os.path.dirname(os.path.abspath(__file__)), "_lade.py"))
_lade = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_lade)
MOEBEL = _lade.moebel()
FIGUREN = [("schicht", "Schicht-Wichtel (4 Lagen)"), ("einfach", "einfache Steckfigur")]

STUECKE = [
    # (Schalter, Bezeichnung, Paket, Modell, Standard)
    ("figur", "Wichtelfigur", "", "", True),
    ("tuer", "Tür", "wichtel", "wichteltuer", True),
    ("fenster", "Fenster", "wichtel", "wichtelfenster", True),
    ("bank", "Bank", "wichtel", "wichtelbank", True),
    ("tisch", "Tisch", "wichtel", "wichteltisch", True),
    ("bett", "Bett", "wichtel", "wichtelbett", True),
    ("leiter", "Leiter", "wichtel", "wichtelleiter", False),
    ("wegweiser", "Wegweiser", "wichtel", "wegweiser", False),
    ("waescheleine", "Wäscheleine", "wichtel", "waescheleine", False),
]

UEBERSETZUNG = {"en": {
    "Wichtelzimmer": "Elf room", "Wichtelwelt": "Elf world",
    "Ein komplettes Wichtelzimmer im selben Maßstab: Figur, Tür, Fenster, Möbel und Zubehör passend zur Wichtelgröße.":
        "A complete elf room in one scale: figure, door, window, furniture and accessories matching the elf size.",
    "Wichtelgröße": "Elf size", "Höhe der Wichtelfigur; alles andere richtet sich danach":
        "height of the elf figure; everything else follows from it",
    "Wichtelfigur": "Elf figure", "Tür": "Door", "Fenster": "Window", "Bank": "Bench", "Tisch": "Table",
    "Bett": "Bed", "Leiter": "Ladder", "Wegweiser": "Signpost", "Wäscheleine": "Clothesline",
    "Hocker": "Stools", "Motiv": "Motif", "Name": "Name", "Name auf Türschild, Bett und Figur":
        "name on the door sign, bed and figure",
    "Figur": "Figure", "Schicht-Wichtel (4 Lagen)": "layered gnome (4 layers)",
    "einfache Steckfigur": "simple slot-together figure",
}}

INFO = dict(
    label="Wichtelzimmer", group="Wichtel",
    desc="Ein komplettes Wichtelzimmer im selben Maßstab: Figur, Tür, Fenster, Möbel und Zubehör passend zur "
         "Wichtelgröße.",
    params=[num("wichtel", "Wichtelgröße", 70, 40, 160, help="Höhe der Wichtelfigur; alles andere richtet sich danach"),
            txt("name_text", "Name", "Fridolin", "Name auf Türschild, Bett und Figur", maxlen=16)]
           + [flag(k, label, std) for k, label, _, _, std in STUECKE]
           + [sel("figur_art", "Figur", FIGUREN, "schicht", when={"figur": [True]}),
              integer("hocker", "Hocker", 2, 0, 4, when={"tisch": [True]}),
              sel("motiv", "Motiv", MOEBEL.MOTIVE, "herz")],
)


def build(cfg, name="wichtelzimmer", wichtel=70.0, name_text="Fridolin", hocker=2, motiv="herz",
          figur_art="schicht", **an):
    R = float(wichtel)
    gewaehlt = [s for s in STUECKE if an.get(s[0], s[4])]
    if not gewaehlt:
        raise ValueError("Bitte mindestens ein Stück auswählen")
    WM = bibliothek("verzierungen").WM
    zu_klein = [(WM.mindestgroesse(s[3], cfg.T / cfg.scale), s[1]) for s in gewaehlt
                if s[3] in WM.MIN_FAKTOR and R < WM.mindestgroesse(s[3], cfg.T / cfg.scale) - 1e-9]
    if zu_klein:
        namen = [n for _, n in zu_klein]
        liste = namen[0] if len(namen) == 1 else ", ".join(namen[:-1]) + " und " + namen[-1]
        raise ValueError(f"Bei {cfg.T:g} mm Holz muss der Wichtel für {liste} mindestens "
                         f"{max(m for m, _ in zu_klein):g} mm groß sein – Wichtelgröße erhöhen")
    extra = dict(
        wichteltuer=dict(schild=f"Wichtel|{name_text}" if name_text.strip() else ""),
        wichtelbank=dict(motiv=motiv), wichtelbett=dict(motiv=motiv, name_text=name_text),
        wichteltisch=dict(motiv=motiv, hocker=int(hocker)),
    )
    out = []
    for key, label, pid, modell, _ in gewaehlt:
        try:
            if key == "figur" and figur_art == "schicht" and R >= 60:
                mod = _lade.modul("schichtwichtel")
                params = {p["key"]: p["default"] for p in mod.INFO["params"]}
                params.update(groesse=R, name_text=name_text, zubehoer="laterne")
                asm = mod.build(cfg, name="wichtelfigur", **params)
            elif key == "figur":
                asm = figur.build(cfg, name="wichtelfigur", height=R, text=name_text)
                if figur_art == "schicht":
                    asm.notes.insert(0, "Der Schicht-Wichtel braucht mindestens 60 mm – hier kommt die einfache "
                                        "Steckfigur.")
            else:
                mod = _lade.modul(modell)
                params = {p["key"]: p["default"] for p in mod.INFO["params"]}
                params.update(massstab="wichtel", wichtel=R, **extra.get(modell, {}))
                asm = mod.build(cfg, name=modell, **params)
        except ValueError as e:
            raise ValueError(f"{label}: {e}")
        out.extend(asm if isinstance(asm, list) else [asm])
    out[0].notes.insert(0, f"Wichtelzimmer für einen {R:g} mm großen Wichtel: "
                           + ", ".join(label for _, label, _, _, _ in gewaehlt) + ".")
    return out
