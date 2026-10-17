"""
Wichteltisch – Paket „Wichtel“.

Tischplatte mit verzierter Kante, zwei Beine mit Füßen und Ausschnittmotiv (stecken mit Zapfen in der
Platte) und eine Querstrebe zwischen den Beinen. Dazu auf Wunsch passende Hocker.
"""
import importlib.util
import math
import os

from steckwerk import Assembly
from pakete import bibliothek, integer, num, sel

_spec = importlib.util.spec_from_file_location("swpaket_wichtel__lade_tisch",
                                               os.path.join(os.path.dirname(os.path.abspath(__file__)), "_lade.py"))
_m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_m)
M = _m.moebel()
Z, K = M.Z, M.K

FORMEN = [("oval", "oval"), ("rund", "rund"), ("abgerundet", "rechteckig, abgerundet"), ("rechteck", "rechteckig"),
          ("achteck", "achteckig")]

UEBERSETZUNG = {"en": {
    "Wichteltisch": "Elf table", "Wichtelmöbel": "Elf furniture",
    "Tisch zum Stecken mit verzierter Platte, zwei Beinen mit Motiv und Querstrebe – auf Wunsch mit passenden Hockern.":
        "Slot-together table with decorated top, two legs with a motif and a stretcher – optionally with matching stools.",
    "Form": "Shape", "Breite": "Width", "Tiefe": "Depth", "Höhe": "Height", "Kante": "Edge", "Motiv": "Motif",
    "Hocker": "Stools", "Hockerhöhe": "Stool height", "oval": "oval", "rund": "round",
    "rechteckig, abgerundet": "rectangular, rounded", "rechteckig": "rectangular", "achteckig": "octagonal",
    "keine": "none", "keins": "none",
    "Die Querstrebe in die Schlitze der beiden Beine stecken, dann die Beine mit den Zapfen in die Tischplatte.":
        "Push the stretcher into the slots of both legs, then the legs with their tabs into the table top.",
    "Hocker genauso zusammenstecken: Strebe in die Beine, Beine in die Sitzfläche.":
        "Assemble the stools the same way: stretcher into the legs, legs into the seat.",
}}

INFO = dict(
    label="Wichteltisch", group="Wichtel",
    desc="Tisch zum Stecken mit verzierter Platte, zwei Beinen mit Motiv und Querstrebe – auf Wunsch mit "
         "passenden Hockern.",
    params=[
        sel("form", "Form", FORMEN, "oval"),
        num("breite", "Breite", 70, 40, 200),
        num("tiefe", "Tiefe", 46, 30, 150),
        num("hoehe", "Höhe", 40, 24, 120),
        sel("kante", "Kante", [("keine", "keine")] + Z.KANTEN, "perlen"),
        sel("motiv", "Motiv", M.MOTIVE, "herz"),
        integer("hocker", "Hocker", 2, 0, 4),
        num("hockerhoehe", "Hockerhöhe", 24, 18, 80),
    ],
)

WM = bibliothek("verzierungen").WM
INFO["params"] = WM.mit_massstab("wichteltisch", INFO["params"])
UEBERSETZUNG["en"].update(WM.EN)


def _form(form: str, W: float, H: float):
    f = {"rund": "oval", "abgerundet": "abgerundet", "rechteck": "rechteck", "achteck": "achteck"}.get(form, "oval")
    if form == "rund":
        W = H = min(W, H)
    return [(x, y - H / 2) for x, y in Z.kartusche(W, H, f)], W, H


def _halbe_breite(umr, y: float) -> float:
    """Halbe Breite der Platte (in x) auf Höhe y."""
    x0, x1 = Z.E.quer_x(umr, y)
    return min(-x0, x1)


def build(cfg, name="wichteltisch", form="oval", breite=70.0, tiefe=46.0, hoehe=40.0, kante="perlen",
          motiv="herz", hocker=2, hockerhoehe=24.0, massstab="wichtel",
          wichtel=70.0):
    if massstab == "wichtel":                     # Maße passend zur Wichtelgröße
        _m = WM.wichtelmass("wichteltisch", wichtel, INFO["params"], cfg)
        breite, tiefe, hoehe, hockerhoehe = _m["breite"], _m["tiefe"], _m["hoehe"], _m["hockerhoehe"]
    W, D, H = cfg.s(breite), cfg.s(tiefe), cfg.s(hoehe)
    notes = []
    asm = Assembly(name, params=dict(form=form, breite=W, tiefe=D, hoehe=H, hocker=int(hocker)))
    umr, W, D = _form(form, W, D)
    gestell(cfg, asm, "", umr, W, D, H, motiv, kante, notes, 40, form in ("oval", "rund"))
    asm.notes.append("Die Querstrebe in die Schlitze der beiden Beine stecken, dann die Beine mit den Zapfen "
                     "in die Tischplatte.")
    for n in range(int(hocker)):
        d = max(min(W, D) * 0.56, 6 * cfg.T + 16)
        gestell(cfg, asm, f"hocker{n + 1}_", K.circle(0, 0, d / 2, 72), d, d, cfg.s(hockerhoehe), motiv, kante,
                notes, 100 + 30 * n, False)
    if int(hocker):
        asm.notes.append("Hocker genauso zusammenstecken: Strebe in die Beine, Beine in die Sitzfläche.")
    asm.notes += notes
    return asm


def gestell(cfg, asm, pre, umr, W, D, H, motiv, kante, notes, pos0, rund):
    """Platte + zwei Beine mit Füßen + Querstrebe. Teilenamen mit Präfix pre, Positionen ab pos0."""
    T = cfg.T
    Bb = D * (0.5 if rund else 0.62)                             # Beinbreite (quer)
    hl = H - T
    if hl < 2 * T + 8:
        raise ValueError("Die Höhe ist für diese Materialstärke zu klein")
    mit_strebe = True
    tw = M.tabbreite(cfg, Bb, 0.22)
    zx = [Bb * 0.24, Bb * 0.76]                                  # Zapfen auf der Bein-Oberkante
    if Bb * 0.24 - tw / 2 < 2.5 + min(Bb, hl) * 0.08:
        zx = [Bb / 2]                                            # schmales Bein: ein Zapfen in der Mitte
    rand = max(2.0, T * 0.8) + tw / 2
    a = W * 0.36                                                 # Beine so weit außen wie die Platte erlaubt
    for _ in range(40):
        try:
            if min(_halbe_breite(umr, Bb * 0.26 + rand), _halbe_breite(umr, -Bb * 0.26 - rand)) > a + T / 2 + rand:
                break
        except ValueError:
            pass
        a *= 0.96
    fh = M.fussbogen_hoehe(cfg, Bb, hl)
    hb = max(2.6 * T, min(12.0, hl * 0.2))
    tq = M.tabbreite(cfg, hb, 0.6)
    yq = fh + hb / 2 + 3.0
    if mit_strebe and yq + hb / 2 + T + 6 > hl:
        mit_strebe = False
    box = (Bb * 0.22, (yq + hb / 2 + 3.0) if mit_strebe else fh + 3.0, Bb * 0.78, hl - T - 4.0)
    for k, seite in enumerate(("links", "rechts")):
        b = M.bein(cfg, f"{pre}bein_{seite}", Bb, hl, motiv, notes,
                   [(x, f"oben{j}", pos0 + 10 * k + j) for j, x in enumerate(zx)], tw,
                   [("strebe", Bb / 2, yq, tq, pos0 + 20 + k, math.pi / 2)] if mit_strebe else [], box)
        asm.parts.append(b)
    if mit_strebe:
        Lq = 2 * a - T - M.EINZUG
        strebe = Z.brett(f"{pre}strebe", Lq, hb, T, links=[(hb / 2, tq, "links", pos0 + 20)],
                         rechts=[(hb / 2, tq, "rechts", pos0 + 21)])
        if motiv != "keine" and Lq > 30:
            Z.gravur(strebe, [(Z.herz(Lq / 2, hb / 2 - hb * 0.3, hb * 0.6), True)], rand=0.8)
        asm.parts.append(strebe)
        asm.connect(f"{pre}strebe:links", f"{pre}bein_links:strebe")
        asm.connect(f"{pre}strebe:rechts", f"{pre}bein_rechts:strebe")
    schl = []
    for k, sx in enumerate((-a, a)):
        for j, x in enumerate(zx):
            yy = (x - Bb / 2) * (1 if k == 0 else -1)            # links und rechts gegenläufig
            schl.append((f"bein{k}_{j}", sx, yy, tw, pos0 + 10 * k + j, math.pi / 2))
    platte = M.platte(cfg, f"{pre}platte" if not pre else f"{pre}sitz", umr, notes, schl, kante)
    asm.parts.append(platte)
    for k, seite in enumerate(("links", "rechts")):
        for j in range(len(zx)):
            asm.connect(f"{pre}bein_{seite}:oben{j}", f"{platte.name}:bein{k}_{j}")
