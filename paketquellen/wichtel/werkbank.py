"""
Werkbank – Paket „Wichtel“.

Wichtel-Werkbank zum Stecken: zwei Böcke mit Füßen, Arbeitsplatte mit Bankhaken-Löchern und Brettfugen,
Ablagebrett unten und ein Schraubstock zum Aufleimen. Dazu Werkzeug als flache Teile: Werkzeugkiste mit
Griff, Säge, Hammer, Zollstock, Schraubenschlüssel und Holzscheite.
"""
import importlib.util
import math
import os

from steckwerk import Assembly, Part, oriented
from pakete import flag, num

_spec = importlib.util.spec_from_file_location("swpaket_wichtel__lade_werkbank",
                                               os.path.join(os.path.dirname(os.path.abspath(__file__)), "_lade.py"))
_m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_m)
M = _m.markt()
Z, K = M.Z, M.K

UEBERSETZUNG = {"en": {
    "Werkbank": "Workbench",
    "Werkbank zum Stecken mit Ablagebrett und Schraubstock – dazu Werkzeugkiste, Säge, Hammer, Zollstock, "
    "Schraubenschlüssel und Holzscheite.":
        "Slot-together workbench with shelf and vice – plus toolbox, saw, hammer, folding rule, wrench and logs.",
    "Länge": "Length", "Höhe": "Height", "Tiefe": "Depth", "Werkzeug": "Tools",
    "Werkzeugkiste, Säge, Hammer, Zollstock, Schlüssel, Holzscheite":
        "toolbox, saw, hammer, folding rule, wrench, logs",
}}

INFO = dict(
    label="Werkbank", group="Wichtel",
    desc="Werkbank zum Stecken mit Ablagebrett und Schraubstock – dazu Werkzeugkiste, Säge, Hammer, Zollstock, "
         "Schraubenschlüssel und Holzscheite.",
    params=[
        num("laenge", "Länge", 63, 40, 200),
        num("hoehe", "Höhe", 35, 25, 110),
        num("tiefe", "Tiefe", 27, 18, 80),
        flag("werkzeug", "Werkzeug", True, help="Werkzeugkiste, Säge, Hammer, Zollstock, Schlüssel, Holzscheite"),
    ],
)
INFO["params"] = M.mit_massstab("werkbank", INFO["params"])
UEBERSETZUNG["en"].update(M.EN)


def _bock(cfg, name, D, Hb, tw, xt, ys, notes, pos0):
    """Bock (x = Tiefe 0 … D, y = Höhe): Füße unten, oben zwei Zapfen in die Platte, Schlitz fürs Ablagebrett."""
    T = cfg.T
    fb = max(1.6 * T + 1.0, D * 0.2)
    fh = min(Hb * 0.22, (D - 2 * fb) * 0.5)
    # gespiegelt bauen (Oberkante auf y = 0), damit die Zapfen mit zapfen_unten oben landen
    fig = Z.Figur().add(K.rect(0, 0, D, Hb))
    if fh > 1.2 * T + 1.0:
        fig.cut(K.ellipse(D / 2, Hb, D / 2 - fb, fh, 0, 48))
    ysp = Hb - ys
    polster = [Z.schlitz_polster(D / 2, ysp, tw, T, max(2.0, T * 0.8))]
    p = Z.figur_teil(cfg, name, fig, notes, solid=polster, unten_flach=True)
    for k, x in enumerate(xt):
        Z.zapfen_unten(p, x, tw, T, f"oben{k}", pos0 + k)
    p = Z.abbilden(p, lambda q: (q[0], Hb - q[1]))
    Z.schlitz(p, "ablage", D / 2, ys, tw, T, pos0 + 5)
    Z.gravur(p, [([(D * 0.15, Hb * 0.55), (D * 0.85, Hb * 0.55)], False)] if fh > 1.2 * T + 1.0 else [], rand=0.8)
    return p


def build(cfg, name="werkbank", laenge=63.0, hoehe=35.0, tiefe=27.0, werkzeug=True, massstab="wichtel",
          wichtel=70.0):
    if massstab == "wichtel":
        _m = M.mass("werkbank", wichtel, INFO["params"], cfg)
        laenge, hoehe, tiefe = _m["laenge"], _m["hoehe"], _m["tiefe"]
    T = cfg.T
    L, H, D = cfg.s(laenge), cfg.s(hoehe), cfg.s(tiefe)
    w = Z.wmin(cfg)
    notes = []
    if H < 3 * T + 12 or D < 3 * T + 8:
        raise ValueError("Die Werkbank ist für diese Materialstärke zu klein – größer wählen")
    asm = Assembly(name, params=dict(laenge=L, hoehe=H, tiefe=D))
    Hb = H - T                                       # Bock unter der Platte
    Db = D - 2.0
    tw = M.tabbreite(cfg, Db, 0.24)
    xt = [Db * 0.27, Db * 0.73]
    ys = Hb * 0.3
    xl = L / 2 - L * 0.12                            # Bockmitte in x
    for k, (seite, sg) in enumerate((("links", -1), ("rechts", 1))):
        asm.parts.append(_bock(cfg, f"bock_{seite}", Db, Hb, tw, xt, ys, notes, 10 + 10 * k))

    # Arbeitsplatte mit Schlitzen, Fugen und Bankhaken-Löchern
    platte = Part("platte", oriented(Z.abrunden(K.rect(-L / 2, 0, L, D), min(L, D) * 0.04, 3), True))
    for k, (seite, sg) in enumerate((("links", -1), ("rechts", 1))):
        for j, x in enumerate(xt):
            Z.schlitz(platte, f"{seite}{j}", sg * xl, 1.0 + x, tw, T, 10 + 10 * k + j, math.pi / 2)
            asm.connect(f"bock_{seite}:oben{j}", f"platte:{seite}{j}")
    lin = M.bretter(-L / 2 + 1.5, 1.5, L / 2 - 1.5, D - 1.5, 3, quer=True, astloch=False)
    r = max(0.5, D * 0.025)
    for k in range(5):
        x = -L * 0.3 + k * L * 0.15
        if abs(abs(x) - xl) > T + 1.5:                     # nicht auf den Schlitzen
            lin.append((K.circle(x, D * 0.84, r, 12), True))
    Z.gravur(platte, lin, rand=0.9, loch_rand=1.2)
    asm.parts.append(platte)

    # Ablagebrett zwischen den Böcken
    Wa = 2 * xl - T - 0.3
    Da = Db
    ablage = Z.brett("ablage", Wa, Da, T, links=[(Da / 2, tw, "links", 15)], rechts=[(Da / 2, tw, "rechts", 25)])
    Z.gravur(ablage, M.bretter(1.2, 1.2, Wa - 1.2, Da - 1.2, 2, quer=True, astloch=False), rand=0.8)
    asm.parts.append(ablage)
    asm.connect("ablage:links", "bock_links:ablage")
    asm.connect("ablage:rechts", "bock_rechts:ablage")

    # Schraubstock (vorne an die Plattenkante leimen)
    s = max(D * 0.55, 6 * w)
    f = Z.Figur()
    f.add(K.rect(-s * 0.5, -s * 0.35, s, s * 0.35))                       # Backe hinten
    f.add(K.rect(-s * 0.5, -s * 0.75, s * 0.56, s * 0.42))                # Körper
    f.add(K.rect(s * 0.02, -s * 0.62, s * 0.38, s * 0.2))                 # Spindelführung
    f.add(K.stroke([(s * 0.3, -s * 0.52), (s * 0.78, -s * 0.52)], max(w * 1.4, s * 0.11)))   # Spindel
    f.add(K.stroke([(s * 0.78, -s * 0.85), (s * 0.78, -s * 0.2)], max(w * 1.3, s * 0.09)))   # Knebel
    for y in (-s * 0.85, -s * 0.2):
        f.add(K.circle(s * 0.78, y, max(w * 0.75, s * 0.07), 16))
    sst = Z.figur_teil(cfg, "schraubstock", f, notes)
    Z.gravur(sst, [([(-s * 0.46, -s * 0.12), (s * 0.46, -s * 0.12)], False),
                   ([(-s * 0.46, -s * 0.24), (s * 0.46, -s * 0.24)], False)], rand=0.5)
    asm.parts.append(sst)

    if werkzeug:
        R = L / 0.9
        # Werkzeugkiste mit Griff
        b, h = R * 0.42, R * 0.2
        f = Z.Figur().add(Z.abrunden([(-b / 2, 0), (b / 2, 0), (b * 0.56, h), (-b * 0.56, h)], h * 0.08, 3))
        hg = h * 0.55
        f.add(Z.abrunden(K.rect(-b * 0.32, h + hg - max(w * 1.3, h * 0.16), b * 0.64, max(w * 1.3, h * 0.16)),
                         h * 0.06, 3))
        for sg in (-1, 1):
            f.add(K.rect(sg * b * 0.32 - (max(w * 1.3, h * 0.14) if sg > 0 else 0), h - 0.5,
                         max(w * 1.3, h * 0.14), hg + 0.5))
        t = Z.figur_teil(cfg, "werkzeugkiste", f, notes, unten_flach=True)
        Z.gravur(t, [([(-b * 0.52, h * 0.5), (b * 0.52, h * 0.5)], False),
                     (K.rect(-b * 0.07, h * 0.38, b * 0.14, h * 0.24), True)], rand=0.6)
        asm.parts.append(t)
        # Säge
        lb, hb_ = R * 0.42, R * 0.1
        f = Z.Figur().add([(0, 0), (lb, hb_ * 0.25), (lb, hb_)])
        zahn = max(1.2, lb / 18)
        for k in range(int(lb / zahn) - 1):
            x = k * zahn
            y = hb_ * 0.25 * x / lb
            f.add([(x, y + 0.01), (x + zahn, y + zahn * hb_ * 0.25 / lb), (x + zahn * 0.5, y - zahn * 0.55)])
        gh = hb_ * 1.9
        f.add(Z.abrunden(K.rect(lb - 1.0, -gh * 0.25, gh * 0.9, gh), gh * 0.25, 4))
        f.cut(Z.abrunden(K.rect(lb + gh * 0.12, gh * 0.05, gh * 0.45, gh * 0.5), gh * 0.15, 3))
        asm.parts.append(Z.figur_teil(cfg, "saege", f, notes))
        # Hammer
        hl = R * 0.3
        f = Z.Figur().add(Z.abrunden(K.rect(-max(w, hl * 0.06), 0, 2 * max(w, hl * 0.06), hl), max(w, hl * 0.05), 3))
        f.add(Z.abrunden([(-hl * 0.32, hl * 0.86), (hl * 0.22, hl * 0.86), (hl * 0.26, hl * 0.82),
                          (hl * 0.26, hl * 1.06), (hl * 0.22, hl * 1.02), (-hl * 0.32, hl * 1.02)], hl * 0.02, 2))
        f.add([(-hl * 0.32, hl * 0.86), (-hl * 0.46, hl * 0.8), (-hl * 0.4, hl * 0.94), (-hl * 0.32, hl * 1.02)])
        t = Z.figur_teil(cfg, "hammer", f, notes)
        Z.gravur(t, [([(-max(w, hl * 0.06) + 0.6, hl * 0.12), (max(w, hl * 0.06) - 0.6, hl * 0.12)], False)], rand=0.3)
        asm.parts.append(t)
        # Zollstock (halb aufgeklappt)
        zb, zl = max(w * 1.3, R * 0.04), R * 0.14
        pts = [(0, 0)]
        for k in range(4):
            a = math.radians(25 if k % 2 == 0 else -25)
            pts.append((pts[-1][0] + zl * math.cos(a), pts[-1][1] + zl * math.sin(a)))
        f = Z.Figur()
        for k in range(4):
            f.add(K.stroke([pts[k], pts[k + 1]], zb, cap="flach"))
            if k < 3:                                       # Gelenk
                f.add(K.circle(pts[k + 1][0], pts[k + 1][1], zb * 0.5, 16))
        t = Z.figur_teil(cfg, "zollstock", f, notes)
        lin = []
        for k in range(4):
            (ax, ay), (bx, by) = pts[k], pts[k + 1]
            for j in range(1, 5):
                u = j / 5
                px, py = ax + (bx - ax) * u, ay + (by - ay) * u
                dx, dy = (bx - ax) / zl, (by - ay) / zl
                lin.append(([(px - dy * zb * 0.45, py + dx * zb * 0.45),
                             (px - dy * zb * (0.1 if j % 2 else -0.05), py + dx * zb * (0.1 if j % 2 else -0.05))],
                            False))
        Z.gravur(t, lin, rand=0.2)
        asm.parts.append(t)
        # Schraubenschlüssel
        sl, sb = R * 0.26, max(w * 1.2, R * 0.035)
        f = Z.Figur().add(K.stroke([(0, 0), (sl, 0)], sb))
        for x, sg in ((0, -1), (sl, 1)):
            f.add(K.circle(x, 0, sb * 1.3, 24))
            f.cut([(x, -sb * 0.45), (x + sg * sb * 1.6, -sb * 0.45), (x + sg * sb * 1.6, sb * 0.45), (x, sb * 0.45)])
        asm.parts.append(Z.figur_teil(cfg, "schluessel", f, notes))
        # Holzscheite (Stirnseite mit Jahresringen)
        for k in range(2):
            rr = R * (0.08 if k else 0.095)
            t = Part(f"holzscheit{k + 1}", oriented(K.ellipse(0, 0, rr, rr * 0.92, 0.3 * k, 48), True))
            ringe = [(K.ellipse(rr * 0.05, 0, rr * f_, rr * 0.9 * f_, 0.3 * k, 32), True) for f_ in (0.62, 0.32)]
            ringe.append(([(rr * 0.1, rr * 0.05), (rr * 0.55, rr * 0.3)], False))
            Z.gravur(t, ringe, rand=0.5)
            asm.parts.append(t)
        asm.notes.append("Werkzeug bemalen und aufleimen: Kiste unter die Bank, Säge und Hammer auf die Platte, "
                         "Holzscheite aufs Ablagebrett.")

    asm.notes.insert(0, "Das Ablagebrett in die Schlitze der beiden Böcke stecken, dann die Platte von oben auf "
                        "die Zapfen der Böcke drücken. Den Schraubstock vorne links an die Plattenkante leimen.")
    asm.notes += list(dict.fromkeys(notes))
    return asm
