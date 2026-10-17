"""
Kurbeltier – Kurbelkiste (Automat): Kinder drehen an der Kurbel, Nocken auf der Welle heben Stäbe, oben
hüpfen oder wippen Tiere.

3D-Lage (x = Breite entlang der Welle, y = Tiefe, z = Höhe, Kastenwände wie _box.build_box):
  * Welle      Vierkant T × T aus der Platte, läuft in runden Lagern der linken und rechten Wand,
               trägt je Tier eine Nocke (Vierkant-Pressitz), außen links einen Stellring, rechts die Kurbel.
  * Nocke      in der YZ-Ebene unter dem Tier; Form bestimmt die Bewegung (hüpfen, wippen, doppelt).
  * Fuß        waagrechte Scheibe, liegt auf der Nocke; der Stab steckt mit einem Tab darin.
  * Stab       YZ-Ebene, läuft durch einen Schlitz im Deckel; oben vorne ein Tab, der von hinten im Tier steckt.
  * Tier       XZ-Ebene, schaut nach vorne.
"""
from __future__ import annotations

import math
import os
import sys
from typing import Dict, List, Tuple

from steckwerk import Assembly, JointFeature, Part, min_distance, oriented, point_in_polygon, rect, slot_feature
from pakete import flag, integer, num, sel, txt

_here = os.path.dirname(os.path.abspath(__file__))


def _sub(name: str):
    import importlib.util
    path = os.path.join(_here, name + ".py")
    key = "swpaket_bewegung_" + name
    mod = sys.modules.get(key)
    if mod is None or getattr(mod, "__file__", None) != path:
        spec = importlib.util.spec_from_file_location(key, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[key] = mod
        spec.loader.exec_module(mod)
    return mod


B = _sub("_bw")
K = B.K
Figur = B.Figur

TIERE = [("hase", "Hase"), ("frosch", "Frosch"), ("dino", "Dino"), ("kueken", "Küken"), ("gemischt", "gemischt")]
BEWEGUNGEN = [("huepfen", "hüpfen (langsam hoch, plötzlich runter)"), ("wippen", "wippen (sanft auf und ab)"),
              ("doppelt", "doppelt hüpfen (zweimal je Umdrehung)")]
AXLE_PLAY = 0.6

INFO = dict(
    label="Kurbeltier",
    group="Bewegung",
    desc="Kurbelkiste für Kinder: Wer an der Kurbel dreht, lässt oben Hase, Frosch, Dino oder Küken hüpfen. "
         "Welle, Nocken und Kurbel sind komplett aus Holz, durchs Fenster sieht man die Mechanik.",
    params=[
        sel("tier", "Tier", TIERE, "hase"),
        integer("anzahl", "Anzahl Tiere", 2, 1, 3),
        sel("bewegung", "Bewegung", BEWEGUNGEN, "huepfen"),
        num("breite", "Kastenbreite", 150, 70, 260),
        num("tiefe", "Kastentiefe", 80, 60, 130),
        num("hoehe", "Kastenhöhe", 90, 60, 160),
        num("tierhoehe", "Tierhöhe", 70, 35, 130),
        flag("fenster", "Fenster vorne", True, help="zeigt die Nocken bei der Arbeit"),
        txt("aufschrift", "Aufschrift", "", "z. B. ein Name, vorne unter dem Fenster", maxlen=30),
        flag("ausmalen", "Linien zum Ausmalen gravieren", True),
    ],
)

UEBERSETZUNG = {"en": {
    "Kurbeltier": "Crank animal", "Bewegung": "Motion",
    "Kurbelkiste für Kinder: Wer an der Kurbel dreht, lässt oben Hase, Frosch, Dino oder Küken hüpfen. "
    "Welle, Nocken und Kurbel sind komplett aus Holz, durchs Fenster sieht man die Mechanik.":
        "Crank box for children: turning the handle makes a bunny, frog, dino or chick hop on top. Shaft, cams "
        "and crank are all wood, and the window shows the mechanism.",
    "Tier": "Animal", "Hase": "Bunny", "Frosch": "Frog", "Dino": "Dino", "Küken": "Chick", "gemischt": "mixed",
    "Anzahl Tiere": "Number of animals",
    "hüpfen (langsam hoch, plötzlich runter)": "hop (slowly up, suddenly down)",
    "wippen (sanft auf und ab)": "bob (gently up and down)",
    "doppelt hüpfen (zweimal je Umdrehung)": "double hop (twice per turn)",
    "Kastenbreite": "Box width", "Kastentiefe": "Box depth", "Kastenhöhe": "Box height",
    "Tierhöhe": "Animal height", "Fenster vorne": "Front window",
    "zeigt die Nocken bei der Arbeit": "shows the cams at work", "Aufschrift": "Lettering",
    "z. B. ein Name, vorne unter dem Fenster": "e.g. a name, on the front below the window",
    "Linien zum Ausmalen gravieren": "Engrave lines for colouring",
}}


# --------------------------------------------------------------------------------------------------
# Tiere im 100er-Raster (Grundlinie y = 0, Mitte x = 0, schauen nach vorne bzw. nach rechts)
# --------------------------------------------------------------------------------------------------

def _hase():
    f, l = Figur(), []
    for s in (-1, 1):
        f.add(K.ellipse(s * 9, 90, 7.5, 19, rot=-s * 0.15))
        l.append((K.ellipse(s * 9, 91, 3.6, 13, rot=-s * 0.15, n=30), True))
        f.add(K.ellipse(s * 13, 5, 11, 5))
    f.add(K.circle(0, 62, 20, 64))
    f.add(K.ellipse(0, 27, 24, 27))
    B_ = []
    for s in (-1, 1):
        B_.append((B.kreis(s * 7, 66, 2.2, 16), True))
        B_.append((B.kreis(s * 7, 66, 0.9, 8), True))
        for dy in (-1.5, 1.5):
            B_.append(([(s * 6, 57.5 + dy * 0.3), (s * 15, 57.5 + dy * 1.8)], False))
    B_.append(([(-2.2, 59.5), (2.2, 59.5), (0, 57)], True))
    B_.append((K.bez((-4.5, 54), (0, 51.5), (4.5, 54), 8), False))
    B_.append((K.ellipse(0, 26, 13, 16, n=40), True))
    return f, l + B_


def _frosch():
    f, l = Figur(), []
    f.add(K.ellipse(0, 32, 34, 28))
    for s in (-1, 1):
        f.add(K.circle(s * 16, 58, 11, 40))
        f.add(K.ellipse(s * 23, 5, 14, 5.5))
        l.append((B.kreis(s * 16, 58, 6, 24), True))
        l.append((B.kreis(s * 16, 58, 2.6, 14), True))
        l.append((B.kreis(s * 22, 38, 3, 16), True))
    l.append((K.bez((-20, 40), (0, 24), (20, 40), 16), False))
    l.append((K.ellipse(0, 18, 18, 11, n=40), True))
    return f, l


def _dino():
    f, l = Figur(), []
    f.add(K.ellipse(-4, 40, 32, 20))
    f.line([(-30, 42), (-44, 50), (-54, 62)], 16, 4)                             # Schwanz
    f.line([(20, 46), (30, 62), (34, 72)], 15, 12)                               # Hals
    f.add(K.ellipse(40, 76, 14, 10))                                             # Kopf
    for x in (-22, 8):
        f.add(K.rect(x, 0, 12, 28))
        f.add(K.ellipse(x + 6, 3, 8, 3.5))
    for i, (x, y) in enumerate(((-22, 58), (-10, 61), (2, 61), (14, 57), (24, 67))):
        f.add([(x - 5, y - 4), (x + 5, y - 4), (x, y + 6)])                     # Rückenzacken
    l.append((B.kreis(43, 79, 2.2, 16), True))
    l.append((B.kreis(43, 79, 0.9, 8), True))
    l.append((K.bez((44, 71), (49, 69.5), (53, 72), 8), False))
    for x, y in ((-14, 36), (-2, 44), (6, 33), (-24, 44)):
        l.append((B.kreis(x, y, 3, 18), True))
    return f, l


def _kueken():
    f, l = Figur(), []
    f.add(K.circle(-2, 30, 26, 64))
    f.add(K.circle(12, 60, 15, 48))
    f.add([(25, 64), (37, 60), (25, 56)])                                        # Schnabel
    f.add(K.spline([(-26, 34), (-36, 44), (-32, 30), (-38, 26), (-24, 22)], closed=True, n=5))   # Schwanzfedern
    f.add(K.spline([(2, 72), (6, 80), (10, 74), (14, 81), (16, 73)], closed=False, n=4))
    f.line([(4, 72), (6, 79)], 3.2)
    f.line([(10, 73), (13, 80)], 3.2)
    for x in (-10, 6):
        f.line([(x, 6), (x, 0)], 3.4)
        f.add(K.ellipse(x + 3, 1.6, 6, 2))
    l.append((B.kreis(17, 63, 2.2, 16), True))
    l.append((B.kreis(17, 63, 0.9, 8), True))
    l.append((K.bez((-16, 34), (-2, 18), (14, 30), 14), False))                  # Flügel
    l.append((K.bez((-14, 30), (-4, 26), (6, 30), 10), False))
    return f, l


_TIERE = dict(hase=_hase, frosch=_frosch, dino=_dino, kueken=_kueken)


def _nocke(art: str, rmin: float, rmax: float, n: int = 160) -> List[Tuple[float, float]]:
    """Nockenkontur um die Welle (0, 0). Drehrichtung der Kurbel: im Uhrzeigersinn von rechts gesehen."""
    if art == "wippen":                          # Exzenter: Kreis, um e aus der Mitte gerückt
        R, e = (rmax + rmin) / 2, (rmax - rmin) / 2
        return [(e + R * math.cos(2 * math.pi * k / n), R * math.sin(2 * math.pi * k / n)) for k in range(n)]
    pts = []
    for k in range(n):
        t = k / n
        if art == "huepfen":                     # Schnecke: langsam steigen, dann über 40° abfallen
            if t < 0.89:
                q = t / 0.89
                r = rmin + (rmax - rmin) * (q * q * (3 - 2 * q) * 0.35 + q * 0.65)
            else:
                q = (t - 0.89) / 0.11
                r = rmax - (rmax - rmin) * (0.5 - 0.5 * math.cos(math.pi * q))
        else:                                    # doppelt: zwei Buckel je Umdrehung
            r = rmin + (rmax - rmin) * math.sin(2 * math.pi * t) ** 2
        th = 2 * math.pi * t
        pts.append((r * math.cos(th), r * math.sin(th)))
    return pts


def _rechteck_loch(part: Part, fid: str, x: float, y: float, w: float, h: float, pos: float, web: float):
    feat, hole = slot_feature(fid, x, y, w, h, False, pos)
    cx, cy = x + w / 2, y + h / 2
    if not point_in_polygon((cx, cy), part.outline) or min_distance(hole, part.outline, limit=web + 0.3) < web + 0.2:
        raise ValueError(f"{part.name}: kein Platz für den Steckschlitz – Tier größer wählen")
    part.holes = [hh for hh in part.holes if min_distance(hh, hole, limit=web + 0.3) >= web + 0.2
                  and not point_in_polygon(hh[0], hole) and not point_in_polygon((cx, cy), hh)]
    part.holes.append(hole)
    part.features.append(feat)


def _schlitzplatz(part: Part, T: float, tw: float, y_ab: float, web: float):
    """Tiefste Stelle nahe der Mitte, an der ein Schlitz T × tw mit Steg ringsum ins volle Holz passt."""
    x0, y0, x1, y1 = part.bbox()
    y = y_ab
    while y + tw < y1 - web:
        for dx in (0.0, 2.0, -2.0, 4.0, -4.0, 6.0, -6.0, 9.0, -9.0, 12.0, -12.0):
            hole = rect(dx - T / 2, y, T, tw)
            if all(point_in_polygon(p, part.outline) for p in hole) and \
                    min_distance(hole, part.outline, limit=web + 0.6) >= web + 0.5 and \
                    all(min_distance(hole, h, limit=web + 0.6) >= web + 0.5 and not point_in_polygon(h[0], hole)
                        and not point_in_polygon((dx, y + tw / 2), h) for h in part.holes):
                return y, dx
        y += 1.0
    return None, None


def build(cfg, name: str = "kurbeltier", tier: str = "hase", anzahl: int = 2, bewegung: str = "huepfen",
          breite: float = 150.0, tiefe: float = 80.0, hoehe: float = 90.0, tierhoehe: float = 70.0,
          fenster: bool = True, aufschrift: str = "", ausmalen: bool = True):
    from models import _deko as dk
    from models._box import build_box
    dk.check_choice("Tier", tier, TIERE)
    dk.check_choice("Bewegung", bewegung, BEWEGUNGEN)
    n = int(anzahl)
    if not 1 <= n <= 3:
        raise ValueError("Kurbeltier: 1 bis 3 Tiere")
    T = cfg.T
    W, D, H, hf = cfg.s(breite), cfg.s(tiefe), cfg.s(hoehe), cfg.s(tierhoehe)
    web = cfg.min_web
    if W < 45 * n + 2 * T:
        raise ValueError(f"Kurbeltier: Für {n} Tiere muss der Kasten mindestens {45 * n + 2 * T:.0f} mm breit sein")
    notes: List[str] = []
    asm, info = build_box(name, W, D, H, cfg, top="slots")
    asm.params.update(dict(tier=tier, anzahl=n, bewegung=bewegung, tierhoehe=hf))
    vo, li, re, dk_ = (asm.part(f"{name}_{s}") for s in ("vorne", "links", "rechts", "deckel"))
    m_lid = info.lid_margin

    # Maße der Mechanik ------------------------------------------------------------------------
    yc = D / 2
    wr = max(2.6 * T, 9.0)                                   # Stabbreite
    tw = max(cfg.min_tab_width, round(0.55 * wr, 2))         # Tabbreite unten (Fuß) und vorne (Tier)
    rf = wr / 2 + max(2.5, T)                                # Fußscheibe
    hub = T / math.sqrt(2) + max(web, 1.5) + 2.0              # Material um das Vierkantloch
    rmax = min(D / 2 - T - 2.0, (H - 2 * T - 6.0) / 2, 0.4 * H, 38.0)
    rmin = max(hub, 0.5 * rmax)
    if rmax - rmin < 5.0:
        raise ValueError("Kurbeltier: Kasten zu klein für eine sichtbare Bewegung – höher oder tiefer machen")
    zs = rmax + 2.5                                          # Wellenhöhe über dem Boden
    lift = rmax - rmin
    abstand = W / n
    xs = [abstand * (i + 0.5) for i in range(n)]
    if 2 * rf > abstand - 3:
        raise ValueError("Kurbeltier: Tiere stehen zu eng – Kasten breiter oder weniger Tiere")

    # Lager in den Seitenwänden ----------------------------------------------------------------
    rb = (T * math.sqrt(2) + AXLE_PLAY) / 2
    for wall in (li, re):
        hole = B.K.circle(yc - T, zs, rb, 40)
        hole = oriented(hole, False)
        wall.holes.append(hole)
        wall.features.append(JointFeature("lager", "bore_round", 2 * rb, T, pos=0.0, points=list(hole)))

    # Fenster und Aufschrift vorne --------------------------------------------------------------
    if fenster:
        x0, x1 = 3 * T + 2, W - 3 * T - 2
        z0, z1 = 2.5 * T + (10 if aufschrift.strip() else 2), H - 3 * T - 2
        if x1 - x0 > 20 and z1 - z0 > 15:
            r = min(6.0, (z1 - z0) / 4)
            win = K.chain(K.arc(x1 - r, z0 + r, r, -math.pi / 2, 0), K.arc(x1 - r, z1 - r, r, 0, math.pi / 2),
                          K.arc(x0 + r, z1 - r, r, math.pi / 2, math.pi), K.arc(x0 + r, z0 + r, r, math.pi, 1.5 * math.pi))
            vo.add_hole(win)
    if aufschrift.strip():
        from models._font import fit_text
        top = (2.5 * T + 10) if fenster else H - 3 * T
        strokes, _ = fit_text(aufschrift.strip(), W / 2, (2.5 * T + top) / 2 if fenster else H / 2,
                              W - 8 * T, max(5.0, top - 2.5 * T - 2), min_h=3.0, max_cap=12.0)
        cv = dk.Canvas(vo, margin=0.8, hole_margin=0.8, seed=cfg.seed)
        for st in strokes:
            cv.draw(st, False, min_len=0.05)

    # Deckel: Schlitze für die Stäbe ------------------------------------------------------------
    for x in xs:
        dk_.add_hole(rect(m_lid + x - (T + 0.5) / 2, m_lid + yc - (wr + 0.6) / 2, T + 0.5, wr + 0.6))

    # Welle ------------------------------------------------------------------------------------
    g_l, g_r = 1.0, info.base_margin + 1.5                  # Stellring links, Kurbel rechts (vor der Bodenplatte)
    x_start = -g_l - T - 0.5
    La = (W + g_r + T + 0.5) - x_start
    welle = Part(f"{name}_welle", rect(0, 0, La, T))

    def shaft(fid, x0):
        z0 = x0 - x_start
        return JointFeature(fid, "shaft", T, T, pos=0.0, span=(z0, z0 + T),
                            points=[(z0, 0.0), (z0 + T, 0.0), (z0 + T, T), (z0, T)])
    welle.features += [shaft("stellring", -g_l - T), shaft("lager_l", 0.0), shaft("lager_r", W - T),
                       shaft("kurbel", W + g_r)]
    asm.parts.append(welle)
    asm.connect(f"{welle.name}:lager_l", f"{li.name}:lager")
    asm.connect(f"{welle.name}:lager_r", f"{re.name}:lager")

    def vierkant_teil(pname, outline):
        p = Part(pname, outline)
        hole = rect(-T / 2, -T / 2, T, T, ccw=False)
        p.holes.append(hole)
        p.features.append(JointFeature("nabe", "bore_square", T, T, pos=0.0, points=list(hole)))
        asm.parts.append(p)
        return p

    ring = vierkant_teil(f"{name}_stellring", B.K.circle(0, 0, T / math.sqrt(2) + max(4.0, 1.5 * T), 48))
    asm.connect(f"{welle.name}:stellring", f"{ring.name}:nabe")

    # Kurbel: Arm mit Vierkant für die Welle und einem zweiten für den Griff
    lk = max(14.0, min(32.0, zs + T - 9.0))
    rk = T / math.sqrt(2) + max(3.5, 1.4 * T)
    arm = K.stroke([(0, 0), (0, lk)], 2 * rk)
    kurbel = vierkant_teil(f"{name}_kurbel", arm)
    h2 = rect(-T / 2, lk - T / 2, T, T, ccw=False)
    kurbel.holes.append(h2)
    kurbel.features.append(JointFeature("griff", "bore_square", T, T, pos=1.0, points=list(h2)))
    kurbel.add_engrave(K.arc(0, lk * 0.45, rk * 0.55, math.radians(200), math.radians(-20), 16))
    asm.connect(f"{welle.name}:kurbel", f"{kurbel.name}:nabe")
    a = 0.5 + T
    Lg = max(18.0, 6 * T)
    gpts = [(0, 0), (a, 0), (a, -0.8 * T), (a + Lg - 2, -0.8 * T), (a + Lg, -0.2 * T), (a + Lg, 1.2 * T),
            (a + Lg - 2, 1.8 * T), (a, 1.8 * T), (a, T), (0, T)]
    griff = Part(f"{name}_griff", gpts)
    griff.features.append(JointFeature("welle", "shaft", T, T, pos=1.0, span=(0.5, a),
                                       points=[(0.5, 0.0), (a, 0.0), (a, T), (0.5, T)]))
    asm.parts.append(griff)
    asm.connect(f"{griff.name}:welle", f"{kurbel.name}:griff")

    # Stationen: Nocke, Fuß, Stab, Tier ------------------------------------------------------------
    sorten = ["hase", "frosch", "kueken"] if tier == "gemischt" else [tier] * n
    z_unten = zs + rmin + T                                  # Stabunterkante in der tiefsten Stellung
    gap = 3.0
    ov0 = max(tw + 4.0, min(0.4 * hf, 26.0))                 # Stab hinter dem Tier
    mech = dict(zs=zs, rmin=rmin, rmax=rmax, xs=xs, yc=yc, wr=wr, rf=rf, z_unten=z_unten, gap=gap, x_start=x_start,
                g_r=g_r, lk=lk, rk=rk, stationen=[])
    asm.params["mechanik"] = mech
    for i, x in enumerate(xs):
        art = sorten[i % len(sorten)]
        # Tier zuerst: der Steckschlitz muss in vollem Holz liegen
        fig, lines = _TIERE[art]()
        x0b, y0b, x1b, y1b = fig.bbox()
        k = min(hf / (y1b - y0b), (abstand - 6) / (x1b - x0b))
        fig = fig.map(lambda p, k=k: (p[0] * k, p[1] * k))
        tierteil = B.teil(f"{name}_{art}_{i + 1}", fig, cfg, notes, unten_flach=True)
        ys, xs_ = _schlitzplatz(tierteil, T, tw, (ov0 - tw) / 2, web)
        if ys is None:
            raise ValueError(f"{tierteil.name}: kein Platz für den Steckschlitz – Tier größer wählen")
        _rechteck_loch(tierteil, "stab", xs_ - T / 2, ys, T, tw, 20.0 + i, web)
        if xs_:
            tierteil = tierteil.transformed(lambda pts, d=xs_: [(px - d, py) for px, py in pts])
            for ft in tierteil.features:
                ft.points = [(px - xs_, py) for px, py in ft.points]
        if ausmalen:
            B.gravur(tierteil, [([(p[0] * k - xs_, p[1] * k) for p in pts], c) for pts, c in lines], cfg.seed)
        ov = max(ov0, ys + tw + 3.0)
        Lr = (H + T + gap + ov) - z_unten
        c0 = Lr - ov + ys
        # Nocke
        nock = vierkant_teil(f"{name}_nocke_{i + 1}", _nocke(bewegung, rmin, rmax))
        if ausmalen:
            nock.add_engrave(K.arc(0, 0, rmin * 0.6, math.radians(40), math.radians(140), 12))
        welle.features.append(shaft(f"nocke{i + 1}", x - T / 2))
        asm.connect(f"{welle.name}:nocke{i + 1}", f"{nock.name}:nabe")
        welle.add_engrave([(x - T / 2 - x_start, 0.4), (x - T / 2 - x_start, T - 0.4)])
        welle.add_engrave([(x + T / 2 - x_start, 0.4), (x + T / 2 - x_start, T - 0.4)])
        # Fuß
        fuss = Part(f"{name}_fuss_{i + 1}", B.K.circle(0, 0, rf, 48))
        feat, hole = slot_feature("stab", -T / 2, -tw / 2, T, tw, False, 10.0 + i)
        fuss.holes.append(hole)
        fuss.features.append(feat)
        asm.parts.append(fuss)
        # Stab (lokal: u nach hinten, v nach oben; u = 0 ist die Vorderkante)
        a0 = (wr - tw) / 2
        sp = [(0, 0), (a0, 0), (a0, -T), (a0 + tw, -T), (a0 + tw, 0), (wr, 0), (wr, Lr), (0, Lr),
              (0, c0 + tw), (-T, c0 + tw), (-T, c0), (0, c0)]
        stab = Part(f"{name}_stab_{i + 1}", sp)
        stab.features.append(JointFeature("fuss", "tab", tw, T, pos=10.0 + i,
                                          points=[(a0, 0), (a0, -T), (a0 + tw, -T), (a0 + tw, 0)]))
        stab.features.append(JointFeature("tier", "tab", tw, T, pos=20.0 + i,
                                          points=[(0, c0 + tw), (-T, c0 + tw), (-T, c0), (0, c0)]))
        asm.parts.append(stab)
        asm.connect(f"{stab.name}:fuss", f"{fuss.name}:stab")
        mech["stationen"].append(dict(stab=stab.name, tier=tierteil.name, nocke=nock.name, Lr=Lr, ov=ov, c0=c0))
        asm.parts.append(tierteil)
        asm.connect(f"{stab.name}:tier", f"{tierteil.name}:stab")

    for t in dict.fromkeys(notes):
        asm.notes.append(t)
    asm.notes += [
        f"Mechanik: Die Nocken heben die Tiere um {lift:.0f} mm. Je Tier: Stab von oben durch den Deckelschlitz "
        f"schieben, unten die Fußscheibe aufstecken, oben das Tier von vorne auf den Tab stecken (leimen).",
        "Welle: Durch das linke Lager schieben, dabei die Nocken an den gravierten Strichen auffädeln, dann durch das "
        "rechte Lager. Außen links den Stellring, rechts die Kurbel aufpressen und mit einem Tropfen Leim sichern. "
        "Nocken versetzt ausrichten, damit die Tiere abwechselnd hüpfen.",
        "Für Kinderhände am besten 4 mm Sperrholz nehmen, dann wird die Vierkantwelle kräftiger. Lager mit etwas "
        "Kerzenwachs einreiben, dann läuft die Kurbel leicht.",
        "Deckel zum Schluss aufstecken, nicht leimen – so kommt man später noch an die Mechanik.",
    ]
    return asm
