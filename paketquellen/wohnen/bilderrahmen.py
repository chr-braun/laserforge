"""
Bilderrahmen – Paket „Wohnen“.

Drei Lagen: verziertes Vorderteil mit Fenster, Zwischenrahmen (oben offen, das Foto wird von oben
eingeschoben) und Rückwand. Dazu wahlweise ein Sockel, in den die Rückwand mit zwei Zapfen gesteckt wird,
oder ein Schlüsselloch zum Aufhängen.
"""
import importlib.util
import os

from steckwerk import Assembly
from pakete import flag, num, sel, txt

_spec = importlib.util.spec_from_file_location("swpaket_wohnen__lade_br",
                                               os.path.join(os.path.dirname(os.path.abspath(__file__)), "_lade.py"))
_m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_m)
R = _m.rahmen()
Z, K = R.Z, R.K

FORMATE = [("9x13", "9 × 13 cm"), ("10x15", "10 × 15 cm"), ("13x18", "13 × 18 cm"), ("15x20", "15 × 20 cm"),
           ("10x10", "10 × 10 cm (quadratisch)"), ("eigen", "eigenes Maß")]

UEBERSETZUNG = {"en": {
    "Bilderrahmen": "Picture frame", "Umrandungen": "Frames", "Wohnen": "Home",
    "Rahmen für ein Foto, schlicht mit Durchbrüchen oder filigran, zum Hinstellen oder Aufhängen. Das Foto wird von oben eingeschoben.":
        "Frame for a photo, plain with cut-outs or filigree, to stand or hang. The photo slides in from the top.",
    "Fotoformat": "Photo size", "eigenes Maß": "custom size", "Foto-Breite": "Photo width", "Foto-Höhe": "Photo height",
    "Hochformat": "Portrait", "Form": "Shape", "Randbreite": "Frame width", "Stil": "Style",
    "schlicht mit Durchbrüchen": "plain with cut-outs", "filigran (durchbrochenes Band)": "filigree (open band)",
    "Füllung": "Filling", "Durchbrüche": "Cut-outs", "Kante": "Edge", "Ecken": "Corners", "keine": "none",
    "Rosetten auf den Ecken": "Rosettes on the corners", "Text unten": "Text at the bottom", "Fuß": "Stand",
    "Sockel zum Hinstellen": "Base to stand", "Schlüsselloch zum Aufhängen": "Keyhole for hanging",
    "Vorderteil, Zwischenrahmen und Rückwand deckungsgleich aufeinander leimen (die offene Seite des Zwischenrahmens nach oben).":
        "Glue front, spacer and back on top of each other, edges flush (open side of the spacer at the top).",
    "Das Foto von oben zwischen Vorderteil und Rückwand schieben.": "Slide the photo in from the top between front and back.",
    "Die Rückwand mit den beiden Zapfen in die hinteren Schlitze des Sockels stecken.":
        "Push the two tabs of the back into the rear slots of the base.",
}}

INFO = dict(
    label="Bilderrahmen", group="Wohnen",
    desc="Rahmen für ein Foto, schlicht mit Durchbrüchen oder filigran, zum Hinstellen oder Aufhängen. "
         "Das Foto wird von oben eingeschoben.",
    params=[
        sel("format", "Fotoformat", FORMATE, "10x15"),
        num("foto_b", "Foto-Breite", 100, 40, 250, when={"format": ["eigen"]}),
        num("foto_h", "Foto-Höhe", 150, 40, 250, when={"format": ["eigen"]}),
        flag("hoch", "Hochformat", True),
        sel("form", "Form", Z.FORMEN, "abgerundet"),
        num("rand", "Randbreite", 24, 14, 60),
        sel("stil", "Stil", R.STILE, "filigran"),
        sel("fuellung", "Füllung", R.FUELLUNGEN, "mandala", when={"stil": ["filigran"]}),
        sel("durchbruch", "Durchbrüche", [("keine", "keine")] + Z.DURCHBRUECHE, "herzen", when={"stil": ["schlicht"]}),
        sel("kante", "Kante", [("keine", "keine")] + Z.KANTEN, "bogen"),
        sel("ecken", "Ecken", R.ECKEN, "keine"),
        txt("text", "Text unten", "", "nur beim schlichten Stil, z. B. ein Name oder ein Datum",
            when={"stil": ["schlicht"]}, symbols=True),
        sel("fuss", "Fuß", [("sockel", "Sockel zum Hinstellen"), ("haken", "Schlüsselloch zum Aufhängen")], "sockel"),
    ],
)

UEBERLAPP = 4.0          # so weit verdeckt das Vorderteil das Foto an jeder Seite


def build(cfg, name="bilderrahmen", format="10x15", foto_b=100.0, foto_h=150.0, hoch=True, form="abgerundet",
          rand=24.0, stil="filigran", fuellung="mandala", durchbruch="herzen", kante="bogen", ecken="keine",
          text="", fuss="sockel"):
    if format != "eigen":
        a, b = (float(v) * 10 for v in format.split("x"))
        foto_b, foto_h = min(a, b), max(a, b)
    else:
        foto_b, foto_h = float(foto_b), float(foto_h)
    if not hoch:
        foto_b, foto_h = foto_h, foto_b
    T = cfg.T
    rand = cfg.s(rand)
    notes = []
    fb, fh = foto_b, foto_h
    Wi, Hi = fb - 2 * UEBERLAPP, fh - 2 * UEBERLAPP
    aussen, fenster, y_cut = R.form_und_fenster(form, Wi, Hi, rand, fuss == "sockel", inhalt=(fb, fh))
    vorne = R.vorderteil(cfg, "vorderteil", aussen, fenster, y_cut, stil, fuellung, kante, ecken, durchbruch, form, notes)
    cy = (max(p[1] for p in aussen) + min(p[1] for p in aussen)) / 2
    fx0 = min(p[0] for p in fenster)
    fy0 = min(p[1] for p in fenster)
    fcx = (min(p[0] for p in fenster) + max(p[0] for p in fenster)) / 2
    fcy = (fy0 + max(p[1] for p in fenster)) / 2
    schacht = K.rect(fcx - fb / 2 - 0.6, fcy - fh / 2 - 0.6, fb + 1.2, 1e4)          # Foto + Luft, oben offen
    zwischen = R.platte(cfg, "zwischenrahmen", aussen, y_cut, 2.0, notes, ausschnitt=schacht)
    rueck = R.platte(cfg, "rueckwand", aussen, y_cut, 2.0, notes)
    if text.strip() and stil == "schlicht":
        band_u = fy0 - y_cut
        try:
            st, cap = Z.text_in_box(text, fcx, band_u * 0.5, (max(p[0] for p in fenster) - fx0) * 0.9,
                                    band_u * 0.55, min(9.0, band_u * 0.5), 3.0)
        except ValueError:
            raise ValueError(f"Der Text „{text}“ passt nicht unter das Fenster – kürzer fassen oder Randbreite erhöhen")
        Z.gravur(vorne, [(s, False) for s in st], rand=0.8)
    asm = Assembly(name, params=dict(format=format, foto=(fb, fh), form=form, rand=rand, stil=stil, fuss=fuss))
    asm.parts += [vorne, zwischen]
    if fuss == "sockel":
        rueck = R.gerade_unten(rueck)
        W_r = max(p[0] for p in rueck.outline) - min(p[0] for p in rueck.outline)
        tw = max(2 * T + 2, min(18.0, W_r * 0.18))
        xs = R.fuss_x(rueck, tw, 0.27)
        for k, x in enumerate(xs):
            Z.zapfen_unten(rueck, x, tw, T, f"fuss{k}", pos=100 + k)
        H_r = max(p[1] for p in rueck.outline)
        tiefe = max(34.0, min(70.0, H_r * 0.32))
        so = R.sockel(cfg, "sockel", W_r * 0.86, tiefe, xs, tw, -T * 1.0, 100, "punkte")
        asm.parts += [rueck, so]
        for k in range(len(xs)):
            asm.connect(f"rueckwand:fuss{k}", f"sockel:schlitz{k}")
    else:
        H_r = max(p[1] for p in rueck.outline)
        y = H_r - max(10.0, rand * 0.55)
        rueck.add_hole(R.schluesselloch(0, y))
        asm.parts.append(rueck)
    asm.notes += notes
    asm.notes.append("Vorderteil, Zwischenrahmen und Rückwand deckungsgleich aufeinander leimen "
                     "(die offene Seite des Zwischenrahmens nach oben).")
    asm.notes.append("Das Foto von oben zwischen Vorderteil und Rückwand schieben.")
    if fuss == "sockel":
        asm.notes.append("Die Rückwand mit den beiden Zapfen in die hinteren Schlitze des Sockels stecken.")
    return asm
