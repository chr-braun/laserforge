"""
Lebkuchenstand – Paket „Wichtel“.

Ein kleiner Marktstand zum Stecken: hinten der Rahmen mit Pfosten, gestreifter Markise mit Bogenkante,
Namensschild und einer Girlande aus Lebkuchenherzen; vorne die Theke aus zwei Seitenteilen, Thekenbrett und
Bretter-Blende. Alles steht in einer Grundplatte mit graviertem Kopfsteinpflaster. Dazu Ware zum Aufleimen:
Lebkuchenherzen mit Zuckerguss, Lebkuchenmänner und Zuckerstangen.
"""
import importlib.util
import math
import os

from steckwerk import Assembly, Part, oriented
from pakete import flag, integer, num, sel, txt

_spec = importlib.util.spec_from_file_location("swpaket_wichtel__lade_stand",
                                               os.path.join(os.path.dirname(os.path.abspath(__file__)), "_lade.py"))
_m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_m)
M = _m.markt()
Z, K = M.Z, M.K

DACH = [("bogen", "Bogenkante"), ("zacken", "Zackenkante")]
SCHILD = [("stern", "mit Stern"), ("herz", "mit Herz"), ("schlicht", "schlicht")]

UEBERSETZUNG = {"en": {
    "Lebkuchenstand": "Gingerbread stall",
    "Marktstand zum Stecken: gestreifte Markise, Namensschild, Herzgirlande, Theke mit Bretterblende und "
    "Pflaster-Grundplatte – dazu Lebkuchenherzen, Lebkuchenmänner und Zuckerstangen.":
        "Slot-together market stall: striped awning, name sign, heart garland, counter with plank front and "
        "cobblestone base – plus gingerbread hearts, gingerbread men and candy canes.",
    "Schild": "Sign", "Text auf dem Schild": "Text on the sign", "Breite": "Width", "Höhe": "Height",
    "Tiefe": "Depth", "Markise": "Awning", "Bogenkante": "scalloped", "Zackenkante": "zigzag",
    "Schildschmuck": "Sign decoration", "mit Stern": "with star", "mit Herz": "with heart", "schlicht": "plain",
    "Herzgirlande": "Heart garland", "Ware": "Goods", "Lebkuchenherzen, Männer und Zuckerstangen":
        "gingerbread hearts, men and candy canes", "Herzen": "Hearts", "Text auf der Theke": "Text on the counter",
}}

INFO = dict(
    label="Lebkuchenstand", group="Wichtel",
    desc="Marktstand zum Stecken: gestreifte Markise, Namensschild, Herzgirlande, Theke mit Bretterblende und "
         "Pflaster-Grundplatte – dazu Lebkuchenherzen, Lebkuchenmänner und Zuckerstangen.",
    params=[
        txt("schild", "Schild", "Lebkuchen", "Text auf dem Schild", maxlen=20),
        txt("theke_text", "Text auf der Theke", "", "", maxlen=20),
        num("breite", "Breite", 77, 45, 220),
        num("hoehe", "Höhe", 105, 60, 300),
        num("tiefe", "Tiefe", 29, 18, 90),
        sel("dach", "Markise", DACH, "bogen"),
        sel("schmuck", "Schildschmuck", SCHILD, "stern"),
        flag("girlande", "Herzgirlande", True),
        flag("ware", "Ware", True, help="Lebkuchenherzen, Männer und Zuckerstangen"),
        integer("herzen", "Herzen", 3, 1, 6, when={"ware": [True]}),
    ],
)
INFO["params"] = M.mit_massstab("lebkuchenstand", INFO["params"])
UEBERSETZUNG["en"].update(M.EN)


def _oben_rund(W, H, r):
    """Rechteck 0…W × 0…H, nur oben abgerundet (unten bleibt die Standfläche voll)."""
    tr = [(W - r + r * math.cos(a), H - r + r * math.sin(a)) for a in (math.pi / 2 * i / 8 for i in range(9))]
    tl = [(r + r * math.cos(a), H - r + r * math.sin(a)) for a in (math.pi / 2 + math.pi / 2 * i / 8 for i in range(9))]
    return [(0, 0), (W, 0)] + tr + tl


def build(cfg, name="lebkuchenstand", schild="Lebkuchen", theke_text="", breite=77.0, hoehe=105.0, tiefe=29.0,
          dach="bogen", schmuck="stern", girlande=True, ware=True, herzen=3, massstab="wichtel", wichtel=70.0):
    if massstab == "wichtel":
        _m = M.mass("lebkuchenstand", wichtel, INFO["params"], cfg)
        breite, hoehe, tiefe = _m["breite"], _m["hoehe"], _m["tiefe"]
    T = cfg.T
    B, H, D = cfg.s(breite), cfg.s(hoehe), cfg.s(tiefe)
    w = Z.wmin(cfg)
    notes = []
    if D < 4 * T + 6 or H < B * 0.7:
        raise ValueError("Der Stand ist für diese Materialstärke zu klein oder zu flach – größer wählen")
    asm = Assembly(name, params=dict(breite=B, hoehe=H, tiefe=D))

    # ---------------- Theke ----------------
    hc = H * 0.33                                    # Thekenhöhe (Oberkante Brett)
    ueber = max(2.5, T * 0.9)                        # Seitenteile ragen etwas über das Brett
    xs = B / 2 - T / 2 - 0.5                         # Mitte der Seitenteile
    tw = M.tabbreite(cfg, D, 0.32)
    fb = max(1.6 * T + 1.0, D * 0.22)
    fb = max(fb, cfg.min_tab_width + 4.2)
    twf = min(fb - 3.4, tw)
    bogen = twf >= cfg.min_tab_width + 0.6 and D - 2 * fb > 2 * T
    fuesse = [fb / 2, D - fb / 2] if bogen else [D / 2]
    if not bogen:
        twf = tw
    for seite, sg, pos0 in (("links", -1, 10), ("rechts", 1, 20)):
        fig = Z.Figur().add(_oben_rund(D, hc + ueber, min(D, hc) * 0.14))
        if bogen:
            fig.cut(K.ellipse(D / 2, 0, D / 2 - fb, min(hc * 0.2, (D - 2 * fb) * 0.45), 0, 48))
        polster = [Z.schlitz_polster(D / 2, hc - T / 2, tw, T, max(2.0, T * 0.8))]
        p = Z.figur_teil(cfg, f"seite_{seite}", fig, notes, solid=polster, unten_flach=True)
        for k, x in enumerate(fuesse):
            Z.zapfen_unten(p, x, twf, T, f"fuss{k}", pos0 + 5 + k)
        Z.schlitz(p, "brett", D / 2, hc - T / 2, tw, T, pos0 + 1)
        asm.parts.append(p)
    Wb = 2 * xs - T - 0.3
    brett = Z.brett("thekenbrett", Wb, D, T, links=[(D / 2, tw, "links", 11)], rechts=[(D / 2, tw, "rechts", 21)])
    Z.gravur(brett, M.bretter(1.5, 1.5, Wb - 1.5, D - 1.5, max(2, int(D / 9)), quer=True, astloch=False), rand=0.8)
    asm.parts.append(brett)
    asm.connect("thekenbrett:links", "seite_links:brett")
    asm.connect("thekenbrett:rechts", "seite_rechts:brett")

    # Blende vorne (geleimt): Bretter, oben Bogenkante
    Wf, Hf = 2 * xs + T, hc + ueber
    bl = Z.abrunden([(-Wf / 2, 0), (Wf / 2, 0), (Wf / 2, Hf), (-Wf / 2, Hf)], min(Wf, Hf) * 0.06)
    blende = Z.figur_teil(cfg, "blende", Z.Figur().add(bl), notes, unten_flach=True)
    lin = M.bretter(-Wf / 2 + 1.2, 1.2, Wf / 2 - 1.2, Hf - 1.2, max(3, int(Hf / 8)), quer=True)
    if theke_text.strip():
        lin = [l for l in lin if not l[1]]
        M.text_gravur(blende, theke_text, 0.0, Hf * 0.5, Wf * 0.78, Hf * 0.4, Hf * 0.3)
        lin = [([(-Wf / 2 + 1.2, y), (Wf / 2 - 1.2, y)], False) for (pts, _) in lin for y in [pts[0][1]]
               if abs(y - Hf * 0.5) > Hf * 0.22]
    Z.gravur(blende, lin, rand=0.8)
    asm.parts.append(blende)

    # ---------------- Rahmen mit Markise und Schild ----------------
    pw = max(2.4 * T, B * 0.075)
    xp = B / 2 - pw / 2
    ya = H * 0.62                                   # Unterkante der Markise
    ah = H * 0.15
    ov = B * 0.06
    Bm = B + 2 * ov
    fig = Z.Figur()
    for sg in (-1, 1):
        fig.add(K.rect(sg * xp - pw / 2, 0, pw, ya + ah * 0.5))
        fig.add(Z.abrunden(K.rect(sg * xp - pw / 2 - 2.2, 0, pw + 4.4, max(3.0, H * 0.035)), 1.0, 3))   # Sockel
    n = max(5, int(round(Bm / (0.105 * B + 0.5))))
    if n % 2 == 0:
        n += 1
    rr = Bm / (2 * n)
    markise = [(-Bm / 2, ya), (Bm / 2, ya), (B / 2 - ov * 0.2, ya + ah), (-B / 2 + ov * 0.2, ya + ah)]
    fig.add(markise)
    for k in range(n):
        cx = -Bm / 2 + rr * (2 * k + 1)
        if dach == "bogen":
            fig.add(K.circle(cx, ya, rr, 24))
        else:
            fig.add([(cx - rr, ya + 0.1), (cx + rr, ya + 0.1), (cx, ya - rr * 1.3)])
    # Giebel über der Markise und Schild
    hs = H * 0.15
    ws = B * 0.82
    ys = H - hs - (H * 0.07 if schmuck != "schlicht" else 0.0)
    fig.add([(-B / 2 + ov * 0.2, ya + ah - 0.2), (B / 2 - ov * 0.2, ya + ah - 0.2), (0, ys + 0.2)])
    schild_poly = Z.abrunden(K.rect(-ws / 2, ys, ws, hs), hs * 0.3, 6)
    fig.add(schild_poly)
    if schmuck == "stern":
        fig.add(K.star(0, H - H * 0.055, H * 0.065, H * 0.03, 5))
    elif schmuck == "herz":
        fig.add(Z.herz(0, H - H * 0.06, H * 0.1))
    # Herzgirlande zwischen den Pfosten
    gl = []
    if girlande:
        x0, x1 = -xp + pw / 2, xp - pw / 2
        yg = ya - rr * 1.1 - max(1.5, H * 0.012)
        sag = H * 0.06
        pfad = K.bez((x0, yg), (0, yg - 2 * sag), (x1, yg), 30)
        fig.add(K.stroke(pfad, max(w, 1.0) * 1.05))
        nh = max(3, int((x1 - x0) / (0.13 * B)))
        gh = min(0.11 * B, (x1 - x0) / nh * 0.8)
        for k in range(nh):
            t = (k + 0.5) / nh
            px = (1 - t) ** 2 * x0 + 2 * (1 - t) * t * 0 + t * t * x1
            py = (1 - t) ** 2 * yg + 2 * (1 - t) * t * (yg - 2 * sag) + t * t * yg
            fig.add(K.stroke([(px, py), (px, py - gh * 0.35)], max(w, 1.0)))
            hz = Z.herz(px, py - gh * 0.75, gh)
            fig.add(hz)
            gl.append(hz)
    rahmen = Z.figur_teil(cfg, "rahmen", fig, notes, unten_flach=True)
    twr = max(cfg.min_tab_width + 0.6, min(pw * 0.7, cfg.tab_factor * T))
    for k, sg in enumerate((-1, 1)):
        Z.zapfen_unten(rahmen, sg * xp, twr, T, f"fuss{k}", 30 + k)
    # Gravur: Streifen der Markise, Schrift, Maserung der Pfosten, Zuckerguss der Herzen
    lin = []
    for k in range(1, n):
        xb = -Bm / 2 + rr * 2 * k
        xt = xb * (B - ov * 0.4) / Bm
        lin.append(([(xb, ya + 0.6), (xt, ya + ah - 0.6)], False))
    lin.append(([(-B / 2 + ov * 0.2 + 1.0, ya + ah - 1.4), (B / 2 - ov * 0.2 - 1.0, ya + ah - 1.4)], False))
    for sg in (-1, 1):
        lin.append(([(sg * xp - pw * 0.1, 2.0), (sg * xp + pw * 0.08, ya * 0.5), (sg * xp - pw * 0.05, ya - 2)],
                    False))
    for hz in gl:
        lin += M.zuckerguss(hz, max(0.9, w * 0.55), 0.35, 1.6)
    Z.gravur(rahmen, lin, rand=0.7)
    if schild.strip():
        M.text_gravur(rahmen, schild, 0.0, ys + hs / 2, ws * 0.86, hs * 0.62, hs * 0.5)
    asm.parts.append(rahmen)

    # ---------------- Grundplatte ----------------
    m = max(4.0, T * 1.5)
    yf = D + 1.0 + T / 2                              # Mitte der Rahmenschlitze
    Dg = yf + T / 2 + m
    x0, x1 = -B / 2 - ov - m * 0.5, B / 2 + ov + m * 0.5
    umr = Z.abrunden([(x0, -m), (x1, -m), (x1, Dg), (x0, Dg)], min(m * 1.5, 8.0))
    platte = Part("grundplatte", oriented(umr, True))
    for k, sg in enumerate((-1, 1)):
        Z.schlitz(platte, f"rahmen{k}", sg * xp, yf, twr, T, 30 + k)
    for seite, sg, pos0 in (("links", -1, 10), ("rechts", 1, 20)):    # Seitenteile stehen in der Tiefe
        for k, x in enumerate(fuesse):
            Z.schlitz(platte, f"seite_{seite}{k}", sg * xs, x, twf, T, pos0 + 5 + k, math.pi / 2)
            asm.connect(f"seite_{seite}:fuss{k}", f"grundplatte:seite_{seite}{k}")
    for k in range(2):
        asm.connect(f"rahmen:fuss{k}", f"grundplatte:rahmen{k}")
    Z.gravur(platte, M.pflaster(x0 + 1, -m + 1, x1 - 1, Dg - 1, max(3.5, B * 0.07)), rand=0.9, loch_rand=1.2)
    asm.parts.append(platte)

    # ---------------- Ware ----------------
    if ware:
        g = B * 0.16
        for k in range(int(herzen)):
            gk = g * (1.0 - 0.12 * (k % 3))
            hz = Z.herz(0, 0, gk)
            t = Z.figur_teil(cfg, f"lebkuchenherz{k + 1}", Z.Figur().add(hz), notes)
            Z.gravur(t, M.zuckerguss(hz, max(0.9, gk * 0.07), max(0.3, gk * 0.025), max(1.4, gk * 0.1))
                     + [(K.circle(-gk * 0.18, gk * 0.08, gk * 0.06, 12), True),
                        (K.circle(gk * 0.18, gk * 0.08, gk * 0.06, 12), True),
                        (K.circle(0, -gk * 0.14, gk * 0.06, 12), True)], rand=0.5)
            asm.parts.append(t)
        gm = B * 0.24
        for k in range(2):
            t = Z.figur_teil(cfg, f"lebkuchenmann{k + 1}", M.lebkuchenmann(0, 0, gm), notes)
            Z.gravur(t, M.lebkuchenmann_gravur(0, 0, gm), rand=0.4)
            asm.parts.append(t)
        for k in range(2):
            fl, st = M.zuckerstange(0, 0, B * 0.22, max(w * 1.25, B * 0.04), links=bool(k))
            t = Z.figur_teil(cfg, f"zuckerstange{k + 1}", Z.Figur().add(fl), notes)
            Z.gravur(t, st, rand=0.25)
            asm.parts.append(t)
        asm.notes.append("Ware nach Lust aufleimen: Herzen an die Blende oder den Rahmen, Lebkuchenmänner aufs "
                         "Thekenbrett, Zuckerstangen an die Pfosten.")

    asm.notes.insert(0, "Die beiden Seitenteile in die vorderen Schlitze der Grundplatte stecken, das "
                        "Thekenbrett mit seinen Zapfen in die Seitenteile, den Rahmen hinten in die Grundplatte. "
                        "Die Blende vorne auf die Theke leimen.")
    asm.notes.append("Bemalen: Markise rot-weiß im Wechsel der Streifen, Schild weiß, Herzen braun mit weißem "
                     "Zuckerguss.")
    asm.notes += list(dict.fromkeys(notes))
    return asm
