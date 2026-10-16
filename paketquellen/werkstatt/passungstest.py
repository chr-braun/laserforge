"""
Passungstest – Paket „Werkstatt“.

Ein Kamm mit Schlitzen in leicht verschiedenen Breiten und ein Probestück aus demselben Holz. Unter jedem
Schlitz steht der Kerf, mit dem genau dieser Schlitz zur Standardbreite wird. Das Probestück in die Schlitze
stecken: Der Wert unter dem Schlitz, in dem es satt sitzt, kommt ins Materialprofil.
"""
from steckwerk import Assembly, Part, oriented
from pakete import bibliothek, integer, num, sel

Z = bibliothek("verzierungen")
K = Z.K

SCHRITTE = [("0.02", "0,02 mm (fein)"), ("0.05", "0,05 mm"), ("0.1", "0,1 mm (grob)")]

UEBERSETZUNG = {"en": {
    "Passungstest": "Fit test", "Werkstatt": "Workshop",
    "Kamm mit Schlitzen in verschiedenen Breiten: zeigt in einem Schnitt den richtigen Kerf für dein Holz.":
        "Comb with slots of different widths: shows the right kerf for your wood in a single cut.",
    "Schlitze": "Slots", "Abstufung": "Step", "Schlitztiefe": "Slot depth",
    "0,02 mm (fein)": "0.02 mm (fine)", "0,05 mm": "0.05 mm", "0,1 mm (grob)": "0.1 mm (coarse)",
}}

INFO = dict(
    label="Passungstest", group="Werkstatt",
    desc="Kamm mit Schlitzen in verschiedenen Breiten: zeigt in einem Schnitt den richtigen Kerf für dein Holz.",
    params=[
        integer("schlitze", "Schlitze", 7, 3, 11),
        sel("schritt", "Abstufung", SCHRITTE, "0.05"),
        num("tiefe", "Schlitztiefe", 10, 6, 20),
    ],
)


def _zahl(v: float) -> str:
    return f"{v:.2f}".replace(".", ",")


def werte(kerf: float, schlitze: int, schritt: float):
    """(Breitenzugabe d, empfohlener Kerf) je Schlitz, von schmal nach breit. Ein Schlitz, der um d breiter
    gezeichnet ist und satt passt, heißt: mit Kerf − d sitzt der Standardschlitz genauso."""
    mitte = (schlitze - 1) / 2
    out = []
    for i in range(schlitze):
        d = round((i - mitte) * schritt, 4)
        k = round(kerf - d, 4)
        if k >= -1e-9:
            out.append((d, max(k, 0.0)))
    return out


def build(cfg, name="passungstest", schlitze=7, schritt="0.05", tiefe=10.0):
    T, kerf = cfg.T, cfg.kerf
    st = float(schritt)
    liste = werte(kerf, int(schlitze), st)
    if len(liste) < 3:
        raise ValueError("Bei so kleinem Kerf bleiben zu wenige Schlitze – feinere Abstufung wählen")
    if T - 0.5 * (int(schlitze) - 1) * st < 0.5:
        raise ValueError("Die Abstufung ist für diese Materialstärke zu grob")
    D = max(tiefe, 2 * T)
    teil = max(T + abs(liste[-1][0]) + 2 * cfg.min_web + 3.5, 13.0)   # Raster je Schlitz
    rand = 4.0
    feld = 9.0                                                     # Höhe des Beschriftungsfelds
    W = rand * 2 + teil * len(liste)
    H = D + feld + 3.0
    xs = [rand + teil * (i + 0.5) for i in range(len(liste))]
    pts = [(0.0, 0.0), (W, 0.0), (W, H)]
    for (d, _), x in reversed(list(zip(liste, xs))):
        w = T + d
        pts += [(x + w / 2, H), (x + w / 2, H - D), (x - w / 2, H - D), (x - w / 2, H)]
    pts.append((0.0, H))
    kamm = Part("kamm", oriented(pts, True))
    linien = []
    for (d, k), x in zip(liste, xs):
        st_, _ = Z.text_in_box(_zahl(k), x, (H - D) / 2 + 0.5, teil - 2.0, feld - 3.0, 4.0, 2.0)
        linien += [(s, False) for s in st_]
        if abs(d) < 1e-9:                                          # Schlitz mit dem aktuellen Kerf
            linien.append(([(x - 3.0, 1.6), (x + 3.0, 1.6)], False))
    Z.gravur(kamm, linien, rand=0.8)
    probe = Part("probestueck", oriented(K.rect(0, 0, 40.0, max(14.0, D + 4.0)), True))
    txt, _ = Z.text_in_box(f"{T:g} MM|KERF {_zahl(kerf)}", 20.0, max(14.0, D + 4.0) / 2, 34.0,
                           max(14.0, D + 4.0) - 4.0, 4.0, 2.0)
    Z.gravur(probe, [(s, False) for s in txt], rand=0.8)
    asm = Assembly(name, params=dict(schlitze=len(liste), schritt=st, kerf=kerf, T=T))
    asm.parts += [kamm, probe]
    asm.notes.append(
        "Beide Teile aus demselben Holz schneiden. Das Probestück nacheinander in die Schlitze stecken: Es soll "
        "mit leichtem Druck hineingehen und von allein halten. Die Zahl unter diesem Schlitz ist dein Kerf – "
        "im Materialprofil eintragen. Unterstrichen ist der Schlitz mit dem aktuellen Kerf.")
    asm.notes.append("Sitzt es in keinem Schlitz gut, den Test mit dem neuen Kerf noch einmal schneiden.")
    return asm
