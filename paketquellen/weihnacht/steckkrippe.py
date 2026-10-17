"""
Steckkrippe – Stall zum Zusammenstecken mit flachen Krippenfiguren.

Stall: Bodenplatte, Rückwand mit Sternfenster, zwei Seitenwände mit Sprossenfenster, Portal mit Rundbogen,
Spruchband und Stern von Betlehem auf dem Mast, zweiteiliges Dach (Schindeln, Reet oder Bretter graviert).
Alle Wände sind mit geprüften Zapfen und Schlitzen verbunden, die Dachhälften sitzen mit Schlitzen auf den
Giebelzapfen.

Figuren als Silhouetten mit Steckfuß und ovalem Sockel: Maria, Josef, Kind in der Krippe, Ochse, Esel,
Hirte mit Lamm, Schaf und auf Wunsch die drei Könige. Gesichter, Gewandfalten, Fell und Holzmaserung sind
graviert – als Malhilfe.
"""
from __future__ import annotations

import math
import os
import random
import sys
from typing import List, Tuple

from steckwerk import Assembly, Part, oriented
from pakete import bibliothek, flag, num, sel, txt

_here = os.path.dirname(os.path.abspath(__file__))


def _sub(name: str):
    import importlib.util
    path = os.path.join(_here, name + ".py")
    key = "swpaket_weihnacht_" + name
    mod = sys.modules.get(key)
    if mod is None or getattr(mod, "__file__", None) != path:
        spec = importlib.util.spec_from_file_location(key, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[key] = mod
        spec.loader.exec_module(mod)
    return mod


W = bibliothek("verzierungen").W
E, K = W.E, W.K
Figur = K.Figur

DACH = [("schindeln", "Holzschindeln"), ("reet", "Reet/Stroh"), ("bretter", "Bretter")]

INFO = dict(
    label="Steckkrippe",
    group="Weihnachten",
    desc="Weihnachtskrippe zum Stecken: Stall mit Rundbogen-Portal, Sternfenster und Stern von Betlehem, "
         "dazu Maria, Josef, das Kind in der Krippe, Ochse, Esel, Hirte, Schaf und die drei Könige – "
         "jede Figur mit Steckfuß und Sockel, Gesichter und Gewänder als Malhilfe graviert.",
    params=[
        num("groesse", "Stallbreite", 200, 140, 320),
        sel("dach", "Dachdeckung", DACH, "schindeln"),
        txt("text", "Spruchband am Portal", "Gloria", maxlen=24, help="leer lassen für kein Spruchband",
            section="Schrift und Beschriftung"),
        flag("figuren", "Krippenfiguren mitschneiden", True),
        flag("koenige", "Heilige Drei Könige", True, when={"figuren": [True]}),
    ],
)

UEBERSETZUNG = {"en": {
    "Steckkrippe": "Slot-together nativity",
    "Weihnachtsdeko": "Christmas decor", "Weihnachten": "Christmas",
    "Weihnachtskrippe zum Stecken: Stall mit Rundbogen-Portal, Sternfenster und Stern von Betlehem, "
    "dazu Maria, Josef, das Kind in der Krippe, Ochse, Esel, Hirte, Schaf und die drei Könige – "
    "jede Figur mit Steckfuß und Sockel, Gesichter und Gewänder als Malhilfe graviert.":
        "Slot-together nativity: stable with arched portal, star window and the Star of Bethlehem, plus Mary, "
        "Joseph, the Child in the manger, ox, donkey, shepherd, sheep and the three kings – every figure with a "
        "tab and a stand, faces and robes engraved as a painting guide.",
    "Stallbreite": "Stable width",
    "Dachdeckung": "Roofing",
    "Holzschindeln": "Wooden shingles",
    "Reet/Stroh": "Thatch/straw",
    "Bretter": "Boards",
    "Spruchband am Portal": "Banner on the portal",
    "leer lassen für kein Spruchband": "leave empty for no banner",
    "Schrift und Beschriftung": "Lettering",
    "Krippenfiguren mitschneiden": "Include nativity figures",
    "Heilige Drei Könige": "Three kings",
}}


# --------------------------------------------------------------------------------------------------
# Stall
# --------------------------------------------------------------------------------------------------

class Stall:
    def __init__(self, B: float, T: float, wm: float):
        self.B, self.T, self.wm = B, T, wm
        self.m = max(2 * T, wm + 4.0)                         # Wände sitzen m vom Bodenrand
        self.D = round(0.55 * B, 1)
        self.Hs = 0.36 * B                                     # Traufhöhe außen
        self.Hg = 0.62 * B                                     # Firsthöhe
        self.tan = (self.Hg - self.Hs) / (B / 2)
        self.alpha = math.atan(self.tan)
        self.Le = math.hypot(B / 2, self.Hg - self.Hs)         # Länge der Giebelschräge
        self.Hsw = self.Hs + self.m * self.tan                 # Seitenwandhöhe
        self.Ds = self.D - 2 * self.m - 2 * T                  # Seitenwand zwischen den Innenflächen
        self.tw_s = 0.4 * self.Hsw                             # Zapfen Seitenwand → Portal/Rückwand
        self.tw_sb = min(0.22 * self.Ds, 30.0)
        self.u_sb = [0.25 * self.Ds, 0.75 * self.Ds]
        self.tw_r = min(0.16 * B, 40.0)
        self.wpost = max(0.06 * B, wm + 2.0)
        self.xp = self.m + T + self.wpost                      # Portalpfosten
        self.tw_p = 0.5 * self.xp
        self.s_t = 0.45 * self.Le                              # Giebelzapfen ab Traufe
        self.tw_d = min(0.25 * self.Le, 40.0)
        self.ev = 0.07 * B                                     # Dachüberstand Traufe
        self.ov = 0.06 * B                                     # Dachüberstand vorn/hinten
        self.Ls = self.ev + self.Le
        self.Dr = self.D + 2 * self.ov
        # Stern auf dem Mast
        self.ro = 0.075 * B
        self.ri = max(0.36 * self.ro, max(wm + 0.6, 0.012 * B) / 0.383)
        self.am = 0.383 * self.ri                               # halbe Mastbreite
        self.mast = T / math.cos(self.alpha) + 0.03 * B
        self.y_m = self.Hg - self.am * self.tan                 # Mast trifft die Schräge
        self.star_c = (B / 2, self.Hg + self.mast + 0.924 * self.ri)
        # Rundbogen
        self.y_sp = 0.45 * self.Hs
        self.arx = (B - 2 * self.xp) / 2
        self.ary = 0.65 * self.arx
        self.y_at = self.y_sp + self.ary

    def y_dach(self, x: float) -> float:
        return self.Hg - abs(x - self.B / 2) * self.tan


def _bogen(g: Stall, rx: float, ry: float, n: int = 40):
    cx = g.B / 2
    return [(cx + rx * math.cos(math.pi * (1 - i / n)), g.y_sp + ry * math.sin(math.pi * (1 - i / n)))
            for i in range(n + 1)]


def _stern_punkte(c, ro, ri, ohne_unten=False):
    """Achtstrahliger Stern, langer Strahl oben, kurze Diagonalen. Mit ohne_unten beginnt die Folge am
    Innenpunkt rechts vom unteren Strahl und endet links davon (für den Mast)."""
    pts = []
    for k in range(16):
        a = -math.pi / 2 + k * math.pi / 8
        if k % 2:
            r = ri
        elif k == 8:
            r = 1.3 * ro
        elif k % 4 == 0:
            r = ro
        else:
            r = 0.62 * ro
        pts.append((c[0] + r * math.cos(a), c[1] + r * math.sin(a)))
    return pts[1:] if ohne_unten else pts


def _giebel(g: Stall, prefix_pos: int, portal: bool):
    """Giebelwand (Rückwand oder Portal). Liefert (Punkte CCW, Features)."""
    B, T, Hs = g.B, g.T, g.Hs
    feats = []
    pts: List = []
    if portal:
        p, f = W.kante_mit_zapfen((0.0, 0.0), (g.xp, 0.0), [(g.xp / 2, g.tw_p, "boden0", prefix_pos)], T)
        pts += p
        feats += f
        pts += [(g.xp, 0.0)] + _bogen(g, g.arx, g.ary) + [(B - g.xp, 0.0)]
        p, f = W.kante_mit_zapfen((B - g.xp, 0.0), (B, 0.0), [(g.xp / 2, g.tw_p, "boden1", prefix_pos + 1)], T)
        pts += p[1:]
        feats += f
    else:
        p, f = W.kante_mit_zapfen((0.0, 0.0), (B, 0.0), [(0.25 * B, g.tw_r, "boden0", prefix_pos),
                                                          (0.75 * B, g.tw_r, "boden1", prefix_pos + 1)], T)
        pts += p
        feats += f
    pts.append((B, 0.0))
    # rechte Schräge
    if portal:
        R = (B / 2 + g.am, g.y_m)
    else:
        R = (B / 2, g.Hg)
    p, f = W.kante_mit_zapfen((B, Hs), R, [(g.s_t, g.tw_d, "dach_r", prefix_pos + 5)], T)
    pts += p
    feats += f
    if portal:
        st = _stern_punkte(g.star_c, g.ro, g.ri, True)
        pts += [R] + st
        L = (B / 2 - g.am, g.y_m)
        pts.append(L)
        rest = g.Le - g.am / math.cos(g.alpha)
    else:
        L = (B / 2, g.Hg)
        pts.append(L)
        rest = g.Le
    p, f = W.kante_mit_zapfen(L, (0.0, Hs), [(rest - g.s_t, g.tw_d, "dach_l", prefix_pos + 6)], T)
    pts += p[1:]
    feats += f
    pts.append((0.0, Hs))
    # doppelte Punkte entfernen
    out = []
    for q in pts:
        if not out or math.hypot(q[0] - out[-1][0], q[1] - out[-1][1]) > 1e-6:
            out.append(q)
    if math.hypot(out[0][0] - out[-1][0], out[0][1] - out[-1][1]) < 1e-6:
        out.pop()
    return out, feats


def _loch(part: Part, poly, wm: float) -> bool:
    """Zierloch nur setzen, wenn ringsum genug Material bleibt."""
    from models import _deko as dk
    cv = dk.Canvas(part, margin=wm + 0.4)
    if cv.fits(poly, closed=True, solid=True):
        part.add_hole(oriented(poly, False))
        return True
    return False


def _rueckwand(g: Stall, cfg, wm: float) -> Part:
    from models import _deko as dk
    pts, feats = _giebel(g, 10, False)
    p = Part("rueckwand", oriented(pts, True))
    p.features += feats
    B, T = g.B, g.T
    for k, x in enumerate((g.m + T / 2, B - g.m - T / 2)):
        W.schlitz(p, f"seite{k}", x, g.Hsw / 2, g.tw_s, T, 52 + k, winkel=math.pi / 2)
    # Sternfenster im Giebel, darum ein Kranz kleiner Lichtpunkte
    hg = g.Hg - g.Hs
    c = (B / 2, g.Hs + 0.30 * hg)
    ro = min(0.24 * hg, 0.11 * B)
    star = _stern_punkte(c, ro * 0.85, ro * 0.38)
    _loch(p, star, wm)
    rr = ro * 1.55
    for i in range(12):
        a = math.pi / 2 + i * math.pi / 6
        q = (c[0] + rr * math.cos(a), c[1] + rr * math.sin(a))
        _loch(p, K.circle(q[0], q[1], max(0.9, 0.012 * B), 16), wm)
    # Gravur: Bretter, Querbalken, Kopfbänder, Heuraufe
    cv = dk.Canvas(p, margin=0.8, seed=cfg.seed)
    cv.draw([(0.0, g.Hs - 0.02 * B), (B, g.Hs - 0.02 * B)])
    cv.draw([(0.0, g.Hs - 0.05 * B), (B, g.Hs - 0.05 * B)])
    step = max(9.0, 0.065 * B)
    rnd = random.Random(cfg.seed)
    x = step
    while x < B - step / 3:
        cv.draw([(x, 0.0), (x, g.Hg)])
        for _ in range(2):                                     # Astlöcher
            y = rnd.uniform(0.08, 0.85) * g.Hs
            cv.draw(K.ellipse(x - step / 2, y, 0.10 * step, 0.05 * step, 0.0, 14), True)
        x += step
    # Heuraufe: schräges Gitter unter dem Querbalken
    y0, y1 = 0.38 * g.Hs, g.Hs - 0.08 * B
    x0, x1 = 0.30 * B, 0.70 * B
    cv.draw([(x0, y0), (x1, y0)])
    cv.draw([(x0, y1), (x1, y1)])
    n = 9
    for i in range(n + 1):
        xx = x0 + (x1 - x0) * i / n
        cv.draw([(xx, y0), (xx + 0.03 * B, y1)])
    return p


def _seitenwand(g: Stall, name: str, cfg, wm: float) -> Part:
    from models import _deko as dk
    Ds, H, T = g.Ds, g.Hsw, g.T
    kk = 0 if name.endswith("links") else 1
    p0, f0 = W.kante_mit_zapfen((0.0, 0.0), (Ds, 0.0),
                                [(u, g.tw_sb, f"boden{k}", (30 if name.endswith("links") else 40) + k)
                                 for k, u in enumerate(g.u_sb)], T)
    p1, f1 = W.kante_mit_zapfen((Ds, 0.0), (Ds, H), [(H / 2, g.tw_s, "hinten", 52 + kk)], T)
    p2, f2 = W.kante_mit_zapfen((0.0, H), (0.0, 0.0), [(H / 2, g.tw_s, "vorn", 50 + kk)], T)
    pts = p0 + p1 + [(Ds, H)] + p2
    p = Part(name, oriented(pts, True))
    p.features += f0 + f1 + f2
    # Sprossenfenster mit vier Scheiben
    wx, wy = 0.36 * Ds, 0.30 * H
    cx, cy = Ds / 2, 0.64 * H
    sb = max(wm + 0.6, 0.03 * Ds)
    pw, ph = (wx - sb) / 2, (wy - sb) / 2
    for i in (0, 1):
        for j in (0, 1):
            _loch(p, K.rect(cx - wx / 2 + i * (pw + sb), cy - wy / 2 + j * (ph + sb), pw, ph), wm)
    cv = dk.Canvas(p, margin=0.8, seed=cfg.seed)
    cv.draw(K.rect(cx - wx / 2 - 2.0, cy - wy / 2 - 2.0, wx + 4.0, wy + 4.0), True)
    # Fensterläden (graviert) links und rechts
    for s in (-1, 1):
        x0 = cx + s * (wx / 2 + 3.0)
        x1 = x0 + s * 0.5 * wx
        xa, xb = min(x0, x1), max(x0, x1)
        lad = K.rect(xa, cy - wy / 2 - 2.0, xb - xa, wy + 4.0)
        cv.draw(lad, True)
        cv.draw([(xa, cy - wy / 2 + 2.0), (xb, cy + wy / 2)])
        for k in (1, 2):
            xx = xa + (xb - xa) * k / 3
            cv.draw([(xx, cy - wy / 2 - 2.0), (xx, cy + wy / 2 + 2.0)])
    # Bretter waagerecht, Z-Strebe unten
    step = max(8.0, 0.11 * H)
    y = step
    while y < H - 2:
        cv.draw([(0.0, y), (Ds, y)])
        y += step
    return p


def _boden(g: Stall, cfg) -> Part:
    from models import _deko as dk
    B, D, T, m = g.B, g.D, g.T, g.m
    p = Part("boden", oriented(K.rect(0.0, 0.0, B, D), True))
    for k, x in enumerate((0.25 * B, 0.75 * B)):
        W.schlitz(p, f"rueckwand{k}", x, D - m - T / 2, g.tw_r, T, 10 + k)
    for k, x in enumerate((g.xp / 2, B - g.xp / 2)):
        W.schlitz(p, f"portal{k}", x, m + T / 2, g.tw_p, T, 20 + k)
    for k, u in enumerate(g.u_sb):
        W.schlitz(p, f"links{k}", m + T / 2, m + T + u, g.tw_sb, T, 30 + k, winkel=math.pi / 2)
        W.schlitz(p, f"rechts{k}", B - m - T / 2, m + T + u, g.tw_sb, T, 40 + k, winkel=math.pi / 2)
    cv = dk.Canvas(p, margin=1.0, seed=cfg.seed)
    cv.draw(K.rect(2.0, 2.0, B - 4.0, D - 4.0), True)
    # Stroh: kurze Halme in zufälliger Richtung
    rnd = random.Random(cfg.seed + 7)
    n = int(B * D / 60)
    for _ in range(n):
        x, y = rnd.uniform(4, B - 4), rnd.uniform(4, D - 4)
        a = rnd.uniform(0, math.pi)
        L = rnd.uniform(3.0, 7.0)
        cv.draw([(x, y), (x + L * math.cos(a), y + L * math.sin(a))])
    return p


def _portal(g: Stall, cfg, wm: float, text: str) -> Part:
    from models import _deko as dk
    pts, feats = _giebel(g, 20, True)
    p = Part("portal", oriented(pts, True))
    p.features += feats
    B, T = g.B, g.T
    for k, x in enumerate((g.m + T / 2, B - g.m - T / 2)):
        W.schlitz(p, f"seite{k}", x, g.Hsw / 2, g.tw_s, T, 50 + k, winkel=math.pi / 2)
    # Stern: Mittelloch und Strahlen
    c = g.star_c
    if g.ri * 0.55 >= wm:
        _loch(p, K.circle(c[0], c[1], 0.42 * g.ri, 24), wm)
    cv = dk.Canvas(p, margin=0.6, seed=cfg.seed)
    for k in range(1, 8):
        a = -math.pi / 2 + k * math.pi / 4
        r = (1.3 if k == 4 else (1.0 if k % 2 == 0 else 0.62)) * g.ro
        cv.draw([(c[0] + 0.55 * g.ri * math.cos(a), c[1] + 0.55 * g.ri * math.sin(a)),
                 (c[0] + 0.8 * r * math.cos(a), c[1] + 0.8 * r * math.sin(a))])
    # Spruchband über dem Bogen
    if text.strip():
        y0 = g.y_at + max(0.02 * B, wm + 1.5)
        cands = []
        for hb in (0.085 * B, 0.075 * B, 0.065 * B, 0.055 * B):
            y1 = y0 + hb
            half = (g.Hg - y1) / g.tan - 0.03 * B
            if half > 0.12 * B:
                cands.append((B / 2 - half, y0, B / 2 + half, y1))
        cvt = dk.Canvas(p, margin=1.0, seed=cfg.seed)
        box = dk.sign(cvt, text.strip(), "banner", cands, "normal", "gross", min_h=3.0,
                      max_cap=min(9.0, 0.045 * B), anchor="mitte", tol=cfg.arc_tolerance)
        if box is None:
            raise ValueError(f"Das Spruchband „{text}“ passt nicht auf das Portal – kürzer fassen oder den Stall "
                             f"breiter wählen")
        cv.block_box(box, 1.0)
    # Zierlöcher: kleine Sterne in den Bogenzwickeln
    for s in (-1, 1):
        x = B / 2 + s * (g.arx + 0.5 * g.wpost)
        for y, r in ((g.y_at - 0.02 * B, 0.03 * B), (g.y_at - 0.11 * B, 0.022 * B)):
            _loch(p, K.star(x, y, r, 0.42 * r, 5), wm)
    cv = dk.Canvas(p, margin=0.8, seed=cfg.seed)
    if text.strip():
        cv.block_box(box, 1.0)
    # Bogensteine
    bw = max(0.05 * B, 6.0)
    aus = _bogen(g, g.arx + bw, g.ary + bw)
    cv.draw(aus)
    n = 11
    for i in range(n + 1):
        a = math.pi * (1 - i / n)
        cx = B / 2
        cv.draw([(cx + g.arx * math.cos(a), g.y_sp + g.ary * math.sin(a)),
                 (cx + (g.arx + bw) * math.cos(a), g.y_sp + (g.ary + bw) * math.sin(a))])
    # Pfostensteine
    hst = max(6.0, 0.045 * B)
    for s in (0, 1):
        x0, x1 = (0.0, g.xp) if s == 0 else (B - g.xp, B)
        y, row = hst, 0
        while y < g.y_sp + 0.5 * g.ary:
            cv.draw([(x0, y), (x1, y)])
            xx = x0 + (x1 - x0) * (0.33 if row % 2 else 0.66)
            cv.draw([(xx, y - hst), (xx, y)])
            y += hst
            row += 1
    # Giebelbretter mit Zierleiste an der Dachkante
    off = max(0.035 * B, 5.0)
    cv.draw([(off / math.sin(math.atan2(1, g.tan)) * 0 + 0.0, g.Hs - off), (B / 2, g.Hg - off / math.cos(g.alpha)),
             (B, g.Hs - off)])
    step = max(9.0, 0.06 * B)
    x = B / 2 - step * int(B / 2 / step)
    while x < B:
        y_top = g.y_dach(x) - off / math.cos(g.alpha)
        yb = g.y_sp + g.ary * math.sqrt(max(0.0, 1 - ((x - B / 2) / (g.arx + bw)) ** 2)) + bw \
            if abs(x - B / 2) < g.arx + bw else g.Hs - 0.02 * B
        if y_top > yb:
            cv.draw([(x, yb), (x, y_top)])
        x += step
    return p


def _dach(g: Stall, name: str, kerbe_vorn: bool, muster: str, cfg) -> Part:
    from models import _deko as dk
    Ls, Dr, T = g.Ls, g.Dr, g.T
    z_f = g.ov + g.m + T / 2
    z_b = g.ov + g.D - g.m - T / 2
    zk = z_f if kerbe_vorn else Dr - z_f
    hw = T / 2 + 0.3
    dn = g.am / math.cos(g.alpha) + T * g.tan + 1.0
    pts = [(0.0, 0.0), (Ls, 0.0), (Ls, zk - hw), (Ls - dn, zk - hw), (Ls - dn, zk + hw), (Ls, zk + hw),
           (Ls, Dr), (0.0, Dr)]
    p = Part(name, oriented(pts, True))
    sv, sh = (z_f, z_b) if kerbe_vorn else (Dr - z_f, Dr - z_b)
    W.schlitz(p, "vorn", g.ev + g.s_t, sv, g.tw_d, T, 25 if kerbe_vorn else 26)
    W.schlitz(p, "hinten", g.ev + g.s_t, sh, g.tw_d, T, 15 if kerbe_vorn else 16)
    cv = dk.Canvas(p, margin=0.8, seed=cfg.seed)
    rnd = random.Random(cfg.seed + (1 if kerbe_vorn else 2))
    if muster == "schindeln":
        sh_ = max(7.0, 0.045 * g.B)
        wsh = 1.2 * sh_
        s0, row = 2.0, 0
        while s0 < Ls - 2:
            off = (row % 2) * wsh / 2
            line = []
            z = -wsh
            while z <= Dr + wsh:
                t = ((z - off) % wsh) / wsh
                line.append((s0 + 0.45 * sh_ * (1 - math.sin(math.pi * t)), z))
                z += wsh / 12
            cv.draw(line)
            zj = off
            while zj < Dr:                                     # Fugen zwischen den Schindeln
                if zj > 1.0:
                    cv.draw([(s0 + 0.45 * sh_, zj), (min(Ls, s0 + sh_), zj)])
                zj += wsh
            s0 += sh_
            row += 1
    elif muster == "reet":
        z = 1.5
        while z < Dr - 1:
            a = rnd.uniform(0, 6.3)
            L0 = rnd.uniform(0.0, 0.08) * Ls
            line = [(L0 + s, z + 0.35 * math.sin(a + s / 6.0)) for s in [i * Ls / 30 for i in range(31)]
                    if L0 + s <= Ls]
            cv.draw(line)
            z += rnd.uniform(1.4, 2.4)
        for s in (0.3 * Ls, 0.62 * Ls):                       # Bindungen
            cv.draw([(s, 0.0), (s, Dr)])
            cv.draw([(s + 1.5, 0.0), (s + 1.5, Dr)])
    else:
        step = max(10.0, 0.06 * g.B)
        z = step
        while z < Dr - 2:
            cv.draw([(0.0, z), (Ls, z)])
            for s in (0.1 * Ls, 0.5 * Ls, 0.9 * Ls):
                for dz in (-step * 0.3, step * 0.3):
                    cv.draw(K.circle(s, z - step / 2 + dz, 0.6, 8), True)
            z += step
        for s in (0.1 * Ls, 0.5 * Ls, 0.9 * Ls):
            cv.draw([(s, 0.0), (s, Dr)])
    return p


# --------------------------------------------------------------------------------------------------
# Figuren (Höhe 1, Mitte x = 0, Grundlinie y = 0); liefern (Figur, Gravurlinien)
# --------------------------------------------------------------------------------------------------

def _gesicht(L, cx, cy, r, augen="offen", bart=False):
    """Gesicht im Kopfkreis (cx, cy, r): Augen, Nase, Mund, optional Bart."""
    for s in (-1, 1):
        ex = cx + s * 0.42 * r
        if augen == "offen":
            L.append((K.circle(ex, cy + 0.12 * r, 0.10 * r, 10), True))
            L.append(([(ex - 0.22 * r, cy + 0.35 * r), (ex, cy + 0.42 * r), (ex + 0.22 * r, cy + 0.35 * r)], False))
        else:
            L.append(([(ex - 0.2 * r, cy + 0.12 * r), (ex, cy + 0.0 * r), (ex + 0.2 * r, cy + 0.12 * r)], False))
    L.append(([(cx, cy + 0.05 * r), (cx - 0.08 * r, cy - 0.25 * r), (cx + 0.08 * r, cy - 0.30 * r)], False))
    if bart:
        L.append(([(cx - 0.8 * r, cy - 0.1 * r), (cx - 0.55 * r, cy - 0.75 * r), (cx, cy - 1.05 * r),
                   (cx + 0.55 * r, cy - 0.75 * r), (cx + 0.8 * r, cy - 0.1 * r)], False))
        L.append(([(cx - 0.3 * r, cy - 0.45 * r), (cx, cy - 0.38 * r), (cx + 0.3 * r, cy - 0.45 * r)], False))
        for s in (-0.35, 0.0, 0.35):
            L.append(([(cx + s * r, cy - 0.62 * r), (cx + 1.1 * s * r, cy - 0.9 * r)], False))
    else:
        L.append(([(cx - 0.25 * r, cy - 0.50 * r), (cx, cy - 0.58 * r), (cx + 0.25 * r, cy - 0.50 * r)], False))


def _falten(L, xs_oben, y_oben, xs_unten, y_unten=0.04):
    for a, b in zip(xs_oben, xs_unten):
        L.append((K.spline([(a, y_oben), ((a + b) / 2 + 0.01, (y_oben + y_unten) / 2), (b, y_unten)], n=6), False))


def _saum(L, x0, x1, y, amp=0.012, n=10):
    L.append(([(x0 + (x1 - x0) * i / (4 * n), y + amp * math.sin(i * math.pi / 2)) for i in range(4 * n + 1)], False))


def _josef(wn):
    w = lambda x: max(x, 1.3 * wn)
    f, L = Figur(), []
    f.add(K.spline([(0.21, 0.0), (0.19, 0.18), (0.165, 0.40), (0.15, 0.58), (0.12, 0.655), (0.05, 0.69),
                    (-0.05, 0.69), (-0.12, 0.655), (-0.15, 0.58), (-0.17, 0.40), (-0.195, 0.18), (-0.21, 0.0)], n=8))
    f.add(K.rect(-0.23, 0.0, 0.53, w(0.035)))
    f.add(K.stroke([(0.27, 0.0), (0.27, 0.95)], w(0.032)))
    f.add(K.circle(0.27, 0.955, w(0.032) / 2 + 0.012, 20))
    f.add(K.stroke(K.spline([(0.11, 0.63), (0.19, 0.57), (0.255, 0.585)], n=6), w(0.075), w(0.06)))
    f.add(K.circle(0.265, 0.59, 0.032, 18))
    f.add(K.stroke(K.spline([(-0.11, 0.63), (-0.20, 0.55), (-0.255, 0.49)], n=6), w(0.075), w(0.06)))
    f.add(K.circle(-0.26, 0.485, 0.032, 18))
    # Laterne
    lw_ = max(0.085, 2 * 1.3 * wn + 0.04)
    lx = -0.285
    f.add(K.stroke([(-0.262, 0.47), (lx, 0.44)], w(0.02)))
    f.add([(lx - lw_ / 2 - 0.012, 0.405), (lx + lw_ / 2 + 0.012, 0.405), (lx, 0.45)])
    f.add(K.rect(lx - lw_ / 2, 0.29, lw_, 0.12))
    f.add(K.rect(lx - lw_ / 2 - 0.012, 0.275, lw_ + 0.024, 0.022))
    win = lw_ - 2 * 1.3 * wn
    if win > 0.025:
        f.cut(K.rect(lx - win / 2, 0.31, win, 0.08))
    # Kopf mit Tuch, Bart
    f.add(K.spline([(-0.10, 0.70), (-0.105, 0.80), (-0.075, 0.88), (0.0, 0.905), (0.075, 0.88), (0.105, 0.80),
                    (0.10, 0.70), (0.13, 0.645), (0.0, 0.67), (-0.13, 0.645)], closed=True, n=6))
    f.add(K.spline([(-0.06, 0.78), (-0.062, 0.73), (-0.03, 0.675), (0.0, 0.655), (0.03, 0.675), (0.062, 0.73),
                    (0.06, 0.78)], closed=True, n=6))
    L.append((K.spline([(-0.064, 0.84), (-0.07, 0.78), (-0.05, 0.70), (0.0, 0.672), (0.05, 0.70), (0.07, 0.78),
                        (0.064, 0.84), (0.0, 0.862)], closed=True, n=6), True))
    _gesicht(L, 0.0, 0.79, 0.06, "offen", bart=True)
    L.append(([(-0.08, 0.86), (0.0, 0.885), (0.08, 0.86)], False))        # Stirnband
    # Gürtel mit Knoten, Falten, Ärmel, Saum
    L.append((K.spline([(-0.17, 0.44), (0.0, 0.42), (0.16, 0.44)], n=6), False))
    L.append(([(0.03, 0.42), (0.01, 0.31)], False))
    L.append(([(0.045, 0.42), (0.07, 0.32)], False))
    _falten(L, [-0.09, -0.02, 0.06, 0.11], 0.40, [-0.15, -0.05, 0.06, 0.15])
    _falten(L, [-0.07, 0.06], 0.64, [-0.10, 0.08], 0.46)
    L.append((K.spline([(0.12, 0.63), (0.18, 0.58), (0.20, 0.55)], n=6), False))
    _saum(L, -0.19, 0.19, 0.07)
    for y in (0.33, 0.37):                                    # Laternenfenster-Sprosse
        L.append(([(lx - lw_ / 2, y), (lx + lw_ / 2, y)], False))
    return f, L


def _maria(wn):
    w = lambda x: max(x, 1.3 * wn)
    f, L = Figur(), []
    f.add(K.spline([(0.32, 0.0), (0.28, 0.10), (0.21, 0.24), (0.17, 0.40), (0.15, 0.52), (0.10, 0.60), (0.0, 0.62),
                    (-0.10, 0.60), (-0.15, 0.52), (-0.17, 0.40), (-0.21, 0.24), (-0.28, 0.10), (-0.32, 0.0)], n=8))
    ri = 0.165
    f.add(K.circle(0.0, 0.75, ri + w(0.032), 60))
    f.cut(K.circle(0.0, 0.75, ri, 60))
    f.add(K.spline([(-0.17, 0.45), (-0.155, 0.62), (-0.125, 0.76), (-0.07, 0.84), (0.0, 0.86), (0.07, 0.84),
                    (0.125, 0.76), (0.155, 0.62), (0.17, 0.45), (0.08, 0.55), (-0.08, 0.55)], closed=True, n=6))
    # Heiligenschein: Strahlen als kleine Durchbrüche
    for k in range(9):
        a = math.pi * (0.1 + 0.8 * k / 8)
        rr = ri + w(0.032) / 2
        q = (rr * math.cos(a), 0.75 + rr * math.sin(a))
        L.append((K.circle(q[0], q[1], 0.006, 8), True))
    L.append((K.spline([(-0.07, 0.775), (-0.075, 0.72), (-0.05, 0.67), (0.0, 0.655), (0.05, 0.67), (0.075, 0.72),
                        (0.07, 0.775), (0.0, 0.80)], closed=True, n=6), True))
    _gesicht(L, 0.0, 0.72, 0.065, "zu")
    L.append((K.spline([(-0.12, 0.55), (-0.115, 0.68), (-0.09, 0.79), (0.0, 0.83), (0.09, 0.79), (0.115, 0.68),
                        (0.12, 0.55)], n=6), False))
    # gefaltete Hände, Ärmel
    L.append(([(0.0, 0.53), (-0.035, 0.45), (-0.005, 0.43), (0.0, 0.53), (0.035, 0.45), (0.005, 0.43)], False))
    for s in (-1, 1):
        L.append((K.spline([(s * 0.15, 0.49), (s * 0.09, 0.445), (s * 0.04, 0.45)], n=6), False))
        L.append((K.spline([(s * 0.13, 0.52), (s * 0.20, 0.25), (s * 0.27, 0.03)], n=6), False))
    _falten(L, [-0.06, 0.0, 0.06], 0.40, [-0.13, 0.0, 0.13])
    for x, y in ((-0.20, 0.12), (0.19, 0.20), (-0.15, 0.30), (0.22, 0.08)):
        L.append((K.star(x, y, 0.022, 0.009, 5), True))
    _saum(L, -0.27, 0.27, 0.05)
    return f, L


def _krippe(wn):
    """Kind in der Krippe; Breite ≈ 1.5."""
    w = lambda x: max(x, 1.3 * wn)
    f, L = Figur(), []
    f.add(K.rect(-0.74, 0.0, 1.48, w(0.07)))
    for sx in (-1, 1):
        x0 = sx * 0.56
        f.add(K.stroke([(x0 - 0.13, 0.03), (x0 + 0.13, 0.56)], w(0.09)))
        f.add(K.stroke([(x0 + 0.13, 0.03), (x0 - 0.13, 0.56)], w(0.09)))
    f.add([(-0.62, 0.46), (0.62, 0.46), (0.74, 0.80), (-0.74, 0.80)])
    sh = max(0.06, 0.6 * wn + 0.035)
    for yy in (0.525, 0.655):
        f.cut(K.rect(-0.48, yy, 0.96, sh))
    hay = [(-0.78, 0.78)]
    n = 16
    for i in range(n + 1):
        hay.append((-0.78 + 1.56 * i / n, 0.86 + (0.07 if i % 2 else 0.0)))
    hay.append((0.78, 0.78))
    f.add(hay)
    # Kind mit Heiligenschein
    hc = (-0.36, 0.98)
    rr = 0.205
    f.add(K.circle(hc[0], hc[1], rr + w(0.04), 48))
    f.cut(K.circle(hc[0], hc[1], rr, 48))
    f.add(K.ellipse(0.10, 0.94, 0.42, 0.125, 0.0, 48))
    f.add(K.circle(hc[0], hc[1], 0.13, 40))
    _gesicht(L, hc[0], hc[1] - 0.01, 0.10, "zu")
    for k in range(5):
        x = -0.12 + 0.12 * k
        L.append(([(x, 0.83), (x + 0.10, 1.05)], False))
    L.append((K.spline([(-0.24, 1.0), (-0.05, 1.03), (0.25, 1.02), (0.48, 0.96)], n=6), False))
    # Holz und Heu
    for yy in (0.48, 0.61, 0.74):
        L.append(([(-0.62, yy + 0.01), (0.62, yy + 0.01)], False))
    for sx in (-1, 1):
        L.append((K.circle(sx * 0.56, 0.295, 0.025, 10), True))
    rnd = random.Random(5)
    for _ in range(14):
        x = rnd.uniform(-0.7, 0.7)
        L.append(([(x, 0.80), (x + rnd.uniform(-0.05, 0.05), 0.87)], False))
    return f, L


def _ochse(wn):
    w = lambda x: max(x, 1.3 * wn)
    f, L = Figur(), []
    f.add(K.spline([(0.55, 0.0), (0.70, 0.10), (0.68, 0.32), (0.50, 0.50), (0.10, 0.57), (-0.35, 0.56),
                    (-0.70, 0.46), (-0.85, 0.26), (-0.84, 0.0)], n=8))
    f.add(K.stroke(K.spline([(0.42, 0.33), (0.60, 0.53), (0.72, 0.66)], n=6), w(0.30), w(0.24)))
    f.add(K.spline([(0.62, 0.78), (0.75, 0.86), (0.86, 0.80), (1.00, 0.55), (1.03, 0.42), (0.94, 0.36),
                    (0.84, 0.42), (0.70, 0.55), (0.60, 0.66)], closed=True, n=6))
    f.add(K.ellipse(0.97, 0.44, 0.09, 0.078, 0.3, 30))
    f.add(K.stroke(K.spline([(0.69, 0.82), (0.60, 0.90), (0.56, 0.98), (0.61, 1.03)], n=6), w(0.075), w(0.03)))
    f.add(K.stroke(K.spline([(0.77, 0.80), (0.86, 0.93), (0.94, 0.97)], n=6), w(0.065), w(0.03)))
    f.add(K.ellipse(0.58, 0.72, 0.10, 0.042, 0.35, 24))
    f.add(K.stroke(K.spline([(0.35, 0.12), (0.62, 0.065), (0.82, 0.065)], n=6), w(0.13), w(0.11)))
    f.add(K.stroke(K.spline([(-0.72, 0.42), (-0.84, 0.36), (-0.92, 0.28), (-0.97, 0.15), (-0.955, 0.07)], n=6), w(0.04)))
    f.add(K.ellipse(-0.955, 0.06, 0.042, 0.06, 0.0, 20))
    # Gravur
    L.append((K.circle(0.84, 0.66, 0.026, 12), True))
    L.append(([(0.80, 0.69), (0.84, 0.70), (0.88, 0.68)], False))
    L.append((K.ellipse(1.0, 0.47, 0.018, 0.012, 0.3, 10), True))
    L.append((K.spline([(0.92, 0.38), (0.97, 0.37), (1.02, 0.39)], n=4), False))
    for k in range(3):                                         # Stirnlocken
        L.append((K.arc(0.75 + 0.04 * k, 0.78 - 0.02 * k, 0.02, 0.0, 3.5, 8), False))
    for t in (0.35, 0.6):                                      # Hornringe
        L.append(([(0.66 - 0.05 * t, 0.86 + 0.08 * t), (0.62 - 0.05 * t, 0.84 + 0.1 * t)], False))
    L.append((K.spline([(-0.65, 0.12), (0.0, 0.10), (0.35, 0.17)], n=6), False))
    L.append((K.spline([(-0.72, 0.08), (-0.70, 0.28), (-0.52, 0.40), (-0.32, 0.33), (-0.26, 0.10)], n=6), False))
    L.append(([(0.78, 0.02), (0.80, 0.11)], False))
    L.append(([(-0.36, 0.02), (-0.30, 0.10)], False))
    L.append((K.spline([(-0.20, 0.47), (-0.05, 0.51), (0.06, 0.44), (-0.04, 0.34), (-0.18, 0.36)], closed=True, n=6),
              True))
    L.append((K.spline([(0.20, 0.42), (0.32, 0.45), (0.36, 0.36), (0.26, 0.30)], closed=True, n=6), True))
    for k in range(3):                                         # Wamme
        L.append(([(0.58 + 0.04 * k, 0.40 - 0.02 * k), (0.62 + 0.04 * k, 0.33 - 0.02 * k)], False))
    return f, L


def _esel(wn):
    w = lambda x: max(x, 1.3 * wn)
    f, L = Figur(), []
    f.add(K.ellipse(-0.05, 0.52, 0.34, 0.16, 0.0, 60))
    for x, knie in ((0.22, 0.012), (0.10, -0.01), (-0.17, 0.0), (-0.29, -0.015)):
        f.add(K.stroke([(x, 0.47), (x + knie, 0.25), (x, 0.04)], w(0.068), w(0.05)))
        f.add(K.rect(x - 0.036, 0.0, 0.072, 0.045))
    f.add(K.rect(-0.33, 0.0, 0.59, w(0.035)))
    f.add(K.stroke([(0.17, 0.56), (0.30, 0.76)], w(0.17), w(0.13)))
    f.add(K.spline([(0.24, 0.80), (0.33, 0.86), (0.44, 0.78), (0.56, 0.64), (0.575, 0.575), (0.50, 0.555),
                    (0.42, 0.60), (0.30, 0.70)], closed=True, n=6))
    f.add(K.ellipse(0.51, 0.60, 0.065, 0.05, 0.0, 24))
    f.add(K.ellipse(0.27, 0.93, 0.034, 0.105, 0.35, 24))
    f.add(K.ellipse(0.33, 0.935, 0.034, 0.105, -0.12, 24))
    f.add(K.stroke(K.spline([(-0.37, 0.58), (-0.43, 0.46), (-0.42, 0.32)], n=6), w(0.032)))
    f.add(K.ellipse(-0.42, 0.29, 0.032, 0.055, 0.0, 16))
    # Mähne als Zacken
    a, b = (0.12, 0.64), (0.27, 0.86)
    d = (b[0] - a[0], b[1] - a[1])
    ln = math.hypot(*d)
    u = (d[0] / ln, d[1] / ln)
    nrm = (-u[1], u[0])
    for k in range(6):
        t = (k + 0.5) / 6
        p = (a[0] + d[0] * t, a[1] + d[1] * t)
        f.add([(p[0] - u[0] * 0.025, p[1] - u[1] * 0.025), (p[0] + nrm[0] * 0.05, p[1] + nrm[1] * 0.05),
               (p[0] + u[0] * 0.025, p[1] + u[1] * 0.025), (p[0] - nrm[0] * 0.04, p[1] - nrm[1] * 0.04)])
    # Gravur
    L.append((K.circle(0.36, 0.76, 0.02, 10), True))
    L.append(([(0.33, 0.785), (0.36, 0.795), (0.39, 0.785)], False))
    L.append((K.circle(0.54, 0.62, 0.012, 8), True))
    L.append((K.spline([(0.47, 0.565), (0.52, 0.575), (0.56, 0.57)], n=4), False))
    L.append((K.arc(0.51, 0.60, 0.06, math.radians(100), math.radians(260), 10), False))
    for cx, rot in ((0.27, 0.35), (0.33, -0.12)):
        L.append((K.ellipse(cx, 0.94, 0.012, 0.07, rot, 12), True))
    # Satteldecke mit Fransen, Schulterkreuz
    dx0, dx1, dy0, dy1 = -0.16, 0.08, 0.42, 0.66
    L.append(([(dx0, dy1), (dx1, dy1), (dx1 + 0.01, dy0), (dx0 - 0.01, dy0)], True))
    L.append(([(dx0 + 0.02, dy1 - 0.025), (dx1 - 0.02, dy1 - 0.025)], False))
    for k in range(9):
        x = dx0 + (dx1 - dx0) * k / 8
        L.append(([(x, dy0), (x, dy0 - 0.03)], False))
    L.append(([(0.13, 0.66), (0.13, 0.50)], False))
    L.append((K.spline([(-0.32, 0.42), (-0.05, 0.37), (0.20, 0.42)], n=6), False))
    for x in (0.22, 0.10, -0.17, -0.29):
        L.append(([(x - 0.03, 0.05), (x + 0.03, 0.05)], False))
    return f, L


def _hirte(wn):
    w = lambda x: max(x, 1.3 * wn)
    f, L = Figur(), []
    f.add(K.spline([(0.19, 0.0), (0.17, 0.2), (0.155, 0.42), (0.135, 0.60), (0.06, 0.67), (-0.06, 0.67),
                    (-0.135, 0.60), (-0.155, 0.42), (-0.17, 0.2), (-0.19, 0.0)], n=8))
    f.add(K.spline([(-0.165, 0.46), (-0.155, 0.62), (-0.06, 0.70), (0.06, 0.70), (0.155, 0.62), (0.165, 0.46),
                    (0.08, 0.50), (0.0, 0.48), (-0.08, 0.50)], closed=True, n=6))
    f.add(K.rect(-0.30, 0.0, 0.51, w(0.035)))
    f.add(K.circle(0.0, 0.765, 0.068, 36))
    f.add(K.ellipse(0.0, 0.83, 0.13, w(0.024), 0.0, 36))
    f.add(K.spline([(-0.068, 0.83), (-0.06, 0.885), (0.0, 0.91), (0.06, 0.885), (0.068, 0.83)], closed=True, n=6))
    sw = w(0.03)
    hook = K.arc(-0.225, 0.86, 0.05, math.pi, -0.35, 16)
    f.add(K.stroke([(-0.275, 0.0)] + hook, sw))
    f.add(K.stroke(K.spline([(-0.11, 0.62), (-0.20, 0.56), (-0.265, 0.56)], n=6), w(0.068), w(0.055)))
    f.add(K.circle(-0.27, 0.56, 0.03, 16))
    # Lamm im Arm
    f.add(K.stroke(K.spline([(0.11, 0.62), (0.18, 0.54), (0.11, 0.46)], n=6), w(0.068), w(0.055)))
    lc = (0.19, 0.50)
    f.add(K.ellipse(lc[0], lc[1], 0.10, 0.055, 0.0, 30))
    for k in range(7):
        a = math.pi * k / 6
        f.add(K.circle(lc[0] + 0.09 * math.cos(a), lc[1] + 0.045 * math.sin(a), 0.035, 16))
    f.add(K.ellipse(0.30, 0.54, 0.05, 0.034, -0.35, 20))
    f.add(K.ellipse(0.275, 0.575, 0.035, 0.013, 0.6, 12))
    for x in (0.15, 0.23):
        f.add(K.stroke([(x, 0.47), (x + 0.005, 0.41)], w(0.025)))
    # Gravur
    L.append((K.spline([(-0.055, 0.80), (-0.06, 0.75), (-0.03, 0.71), (0.0, 0.70), (0.03, 0.71), (0.06, 0.75),
                        (0.055, 0.80)], n=6), False))
    _gesicht(L, 0.0, 0.765, 0.055, "offen", bart=True)
    L.append(([(-0.06, 0.845), (0.06, 0.845)], False))
    zz = []
    for k in range(13):
        x = -0.16 + 0.32 * k / 12
        zz.append((x, 0.49 + (0.025 if k % 2 else 0.0) + 0.02 * (1 - abs(x) / 0.16)))
    L.append((zz, False))
    for k in range(6):
        x = -0.12 + 0.05 * k
        L.append((K.arc(x, 0.60, 0.012, 0.0, 3.2, 6), False))
    L.append((K.spline([(-0.15, 0.36), (0.0, 0.345), (0.15, 0.36)], n=6), False))
    L.append((K.spline([(0.04, 0.345), (0.10, 0.34), (0.11, 0.25), (0.05, 0.24), (0.04, 0.345)], n=4), False))
    L.append(([(0.04, 0.32), (0.11, 0.315)], False))
    _falten(L, [-0.09, -0.03, 0.03], 0.33, [-0.15, -0.04, 0.06])
    for k in range(4):
        L.append((K.arc(0.15 + 0.035 * k, 0.505 + 0.012 * (k % 2), 0.012, 0.0, 3.5, 6), False))
    L.append((K.circle(0.315, 0.55, 0.008, 6), True))
    _saum(L, -0.17, 0.17, 0.07)
    return f, L


def _schaf(wn):
    w = lambda x: max(x, 1.3 * wn)
    f, L = Figur(), []
    c = (-0.04, 0.56)
    f.add(K.ellipse(c[0], c[1], 0.38, 0.20, 0.0, 48))
    for k in range(12):
        a = math.pi * (-0.15 + 1.3 * k / 11)
        f.add(K.circle(c[0] + 0.36 * math.cos(a), c[1] + 0.19 * math.sin(a), 0.085, 24))
    f.add(K.ellipse(0.42, 0.66, 0.13, 0.085, -0.5, 30))
    f.add(K.ellipse(0.34, 0.75, 0.075, 0.026, 0.55, 16))
    for x in (-0.30, -0.19, 0.12, 0.23):
        f.add(K.stroke([(x, 0.42), (x, 0.03)], w(0.07)))
    f.add(K.rect(-0.36, 0.0, 0.66, w(0.05)))
    rnd = random.Random(3)
    for _ in range(9):
        x, y = c[0] + rnd.uniform(-0.28, 0.24), c[1] + rnd.uniform(-0.10, 0.12)
        L.append((K.arc(x, y, 0.035, rnd.uniform(0, 3), rnd.uniform(4, 6), 10), False))
    L.append((K.circle(0.45, 0.70, 0.017, 10), True))
    L.append(([(0.52, 0.58), (0.54, 0.60)], False))
    for x in (-0.30, -0.19, 0.12, 0.23):
        L.append(([(x - 0.03, 0.08), (x + 0.03, 0.08)], False))
    return f, L


def _koenig(wn, art: int):
    """art 0: Zackenkrone, Truhe, langer Bart; 1: Lilienkrone, Kelch; 2: Turban, Salbgefäß."""
    w = lambda x: max(x, 1.3 * wn)
    f, L = Figur(), []
    f.add(K.spline([(0.30, 0.0), (0.24, 0.20), (0.19, 0.42), (0.155, 0.59), (0.08, 0.67), (-0.08, 0.67),
                    (-0.155, 0.59), (-0.19, 0.42), (-0.24, 0.20), (-0.30, 0.0)], n=8))
    f.add(K.circle(0.0, 0.75, 0.07, 36))
    # Krone
    if art == 0:
        f.add(K.rect(-0.075, 0.795, 0.15, 0.04))
        for k in range(3):
            x = -0.05 + 0.05 * k
            f.add([(x - 0.028, 0.83), (x + 0.028, 0.83), (x, 0.905)])
            f.add(K.circle(x, 0.91, max(0.016, 0.65 * wn), 12))
    elif art == 1:
        f.add(K.rect(-0.075, 0.795, 0.15, 0.04))
        for k in range(3):
            x = -0.05 + 0.05 * k
            f.add(K.stroke([(x, 0.83), (x, 0.88)], w(0.02)))
            f.add(K.circle(x, 0.89, 0.024, 14))
            f.add(K.circle(x - 0.02, 0.875, 0.014, 10), K.circle(x + 0.02, 0.875, 0.014, 10))
    else:
        f.add(K.ellipse(0.0, 0.83, 0.095, 0.058, 0.0, 30))
        f.add(K.circle(0.0, 0.895, 0.025, 14))
        f.add(K.stroke(K.spline([(0.02, 0.89), (0.07, 0.95), (0.06, 1.0)], n=6), w(0.022), w(0.016)))
    if art == 0:
        f.add(K.spline([(-0.06, 0.74), (-0.055, 0.66), (-0.02, 0.58), (0.0, 0.56), (0.02, 0.58), (0.055, 0.66),
                        (0.06, 0.74)], closed=True, n=6))
    elif art == 1:
        f.add(K.spline([(-0.055, 0.73), (-0.04, 0.67), (0.0, 0.645), (0.04, 0.67), (0.055, 0.73)], closed=True, n=6))
    # Arme zum Geschenk rechts
    f.add(K.stroke(K.spline([(0.10, 0.62), (0.18, 0.55), (0.23, 0.52)], n=6), w(0.07), w(0.055)))
    gx = 0.28
    if art == 0:                                              # Truhe
        f.add(K.rect(gx - 0.075, 0.44, 0.15, 0.08))
        f.add(K.ellipse(gx, 0.52, 0.075, 0.035, 0.0, 24))
        if 0.02 > 1.3 * wn * 0.5:
            f.cut(K.circle(gx, 0.48, 0.012, 10))
    elif art == 1:                                            # Kelch
        f.add([(gx - 0.07, 0.58), (gx + 0.07, 0.58), (gx + 0.03, 0.50), (gx - 0.03, 0.50)])
        f.add(K.stroke([(gx, 0.51), (gx, 0.43)], w(0.022)))
        f.add(K.ellipse(gx, 0.425, 0.045, 0.016, 0.0, 16))
        f.add(K.circle(gx, 0.60, 0.022, 12))
    else:                                                     # Salbgefäß
        f.add(K.spline([(gx - 0.03, 0.42), (gx - 0.065, 0.48), (gx - 0.04, 0.55), (gx - 0.02, 0.58), (gx + 0.02, 0.58),
                        (gx + 0.04, 0.55), (gx + 0.065, 0.48), (gx + 0.03, 0.42)], closed=True, n=6))
        f.add(K.ellipse(gx, 0.59, 0.035, 0.014, 0.0, 14))
        f.add(K.circle(gx, 0.625, 0.02, 12))
    f.add(K.circle(0.225, 0.52, 0.03, 14))
    f.add(K.rect(-0.31, 0.0, 0.62, w(0.035)))
    # Zierlöcher am Saum (Rauten)
    hw_, hh_ = max(0.024, 0.75 * wn), max(0.034, 1.05 * wn)
    step = 2 * hw_ + 1.6 * wn + 0.02
    nx = int(0.40 / step)
    for i in range(-nx, nx + 1):
        x = i * step
        f.cut([(x - hw_, 0.11), (x, 0.11 - hh_), (x + hw_, 0.11), (x, 0.11 + hh_)])
    # Gravur
    L.append((K.spline([(-0.06, 0.79), (-0.065, 0.74), (-0.04, 0.695), (0.0, 0.68), (0.04, 0.695), (0.065, 0.74),
                        (0.06, 0.79)], n=6), False))
    _gesicht(L, 0.0, 0.755, 0.058, "offen", bart=(art != 2))
    if art == 0:
        for s in (-0.03, 0.0, 0.03):
            L.append(([(s, 0.66), (s * 1.2, 0.59)], False))
        for k in range(3):
            L.append((K.circle(-0.05 + 0.05 * k, 0.815, 0.008, 6), True))
    elif art == 1:
        L.append(([(-0.075, 0.815), (0.075, 0.815)], False))
    else:
        for k in range(3):
            L.append((K.arc(0.0, 0.79 + 0.025 * k, 0.09 - 0.012 * k, 0.4, 2.7, 8), False))
        L.append((K.circle(0.0, 0.84, 0.012, 8), True))
    # Mantel: Kanten, Hermelinkragen, Borte
    for s in (-1, 1):
        L.append((K.spline([(s * 0.07, 0.64), (s * 0.10, 0.40), (s * 0.13, 0.17)], n=6), False))
    L.append((K.spline([(-0.15, 0.60), (-0.08, 0.63), (0.0, 0.61), (0.08, 0.63), (0.15, 0.60)], n=6), False))
    for x in (-0.11, -0.06, 0.04, 0.09):
        L.append(([(x, 0.635), (x, 0.615)], False))
    zz = [(-0.27 + 0.54 * k / 18, 0.17 + (0.02 if k % 2 else 0.0)) for k in range(19)]
    L.append((zz, False))
    L.append(([(-0.27, 0.16), (0.27, 0.16)], False))
    for y in (0.30, 0.40, 0.50):
        L.append((K.circle(0.0, y, 0.012, 8), True))
    _falten(L, [-0.15, 0.15], 0.45, [-0.22, 0.22], 0.19)
    if art == 0:
        L.append(([(gx - 0.075, 0.50), (gx + 0.075, 0.50)], False))
        L.append(([(gx - 0.02, 0.52), (gx - 0.02, 0.44)], False))
    elif art == 1:
        L.append(([(gx - 0.055, 0.56), (gx + 0.055, 0.56)], False))
    else:
        L.append(([(gx - 0.05, 0.50), (gx + 0.05, 0.50)], False))
    return f, L


FIGUREN = [
    # name, Bauer, Höhe/B, Mindesthöhe
    ("maria", _maria, 0.27, 38.0),
    ("josef", _josef, 0.34, 46.0),
    ("kind_in_krippe", _krippe, 0.15, 24.0),
    ("ochse", _ochse, 0.19, 30.0),
    ("esel", _esel, 0.25, 36.0),
    ("hirte", _hirte, 0.32, 44.0),
    ("schaf", _schaf, 0.13, 22.0),
]
KOENIGE = [("koenig_kaspar", 0), ("koenig_melchior", 1), ("koenig_balthasar", 2)]


def _figur(asm: Assembly, cfg, name: str, bauer, h: float, notes: List[str], wm: float, art=None):
    from models import _deko as dk
    from models._stand import stand_base
    wn = wm / h
    f, L = bauer(wn) if art is None else bauer(wn, art)
    fig = f.place(0.0, 0.0, h)
    x0, y0, x1, y1 = fig.bbox()
    fig.cut(K.rect(x0 - 2, y0 - 2, x1 - x0 + 4, -y0 + 2))     # alles unter der Standlinie weg
    part = W.figur_teil(cfg, name, fig, notes, unten_flach=True)
    # längste Strecke auf y = 0 (Bodenstreifen) trägt den Zapfen
    best = None
    P = part.outline
    for i in range(len(P)):
        a, b = P[i], P[(i + 1) % len(P)]
        if a[1] == 0.0 and b[1] == 0.0:
            ln = abs(b[0] - a[0])
            if best is None or ln > best[0]:
                best = (ln, min(a[0], b[0]), max(a[0], b[0]))
    if best is None:
        raise ValueError(f"{name}: Standfläche fehlt – Stall größer wählen")
    span, xa, xb = best
    tw = max(2.5 * cfg.T, min(0.45 * span, 0.3 * (x1 - x0)))
    tw = min(tw, span - 2 * (wm + 1.0))
    if tw < 2 * cfg.T:
        raise ValueError(f"{name}: Die Standfläche ist zu schmal für den Steckfuß – Stall größer wählen")
    xc = min(max(0.0, xa + tw / 2 + wm + 1.0), xb - tw / 2 - wm - 1.0)
    W.zapfen_unten(part, xc, tw, cfg.T, "fuss")
    cv = dk.Canvas(part, margin=0.45, hole_margin=0.5, seed=cfg.seed)
    for pts, closed in L:
        cv.draw([(x * h, y * h) for x, y in pts], closed)
    asm.parts.append(part)
    rx = max(0.5 * (x1 - x0) * 0.85 + 2.0, tw / 2 + 4 * cfg.T)
    ry = max(0.32 * rx, 0.16 * h, 3.5 * cfg.T)
    stand_base(asm, part, "fuss", tw, cfg, rx, ry, "sockel_" + name)
    return part


# --------------------------------------------------------------------------------------------------

def build(cfg, name: str = "steckkrippe", groesse: float = 200.0, dach: str = "schindeln", text: str = "Gloria",
          figuren: bool = True, koenige: bool = True):
    from models._font import unsupported
    if dach not in dict(DACH):
        raise ValueError(f"Dachdeckung: unbekannte Auswahl {dach!r}")
    B, T = cfg.s(groesse), cfg.T
    if B < 135:
        raise ValueError("Der Stall ist zu klein – mindestens 140 mm Breite")
    if B > 325:
        raise ValueError("Der Stall ist zu groß für die Platte – höchstens 320 mm Breite")
    if T > 0.03 * B:
        raise ValueError("Für diese Materialstärke ist der Stall zu klein – breiter wählen oder dünneres Holz")
    bad = unsupported(text or "")
    if bad:
        raise ValueError(f"Zeichen {''.join(bad)!r} gibt es in der Schrift nicht")
    wm = W.wmin(cfg)
    g = Stall(B, T, wm)
    asm = Assembly(name, params=dict(groesse=B, dach=dach, text=text, figuren=figuren, koenige=koenige))
    notes: List[str] = []
    boden = _boden(g, cfg)
    rueck = _rueckwand(g, cfg, wm)
    portal = _portal(g, cfg, wm, text or "")
    links = _seitenwand(g, "seitenwand_links", cfg, wm)
    rechts = _seitenwand(g, "seitenwand_rechts", cfg, wm)
    dl = _dach(g, "dach_links", True, dach, cfg)
    dr = _dach(g, "dach_rechts", False, dach, cfg)
    asm.parts += [boden, rueck, portal, links, rechts, dl, dr]
    for k in range(2):
        asm.connect(f"rueckwand:boden{k}", f"boden:rueckwand{k}")
        asm.connect(f"portal:boden{k}", f"boden:portal{k}")
        asm.connect(f"seitenwand_links:boden{k}", f"boden:links{k}")
        asm.connect(f"seitenwand_rechts:boden{k}", f"boden:rechts{k}")
    asm.connect("seitenwand_links:vorn", "portal:seite0")
    asm.connect("seitenwand_rechts:vorn", "portal:seite1")
    asm.connect("seitenwand_links:hinten", "rueckwand:seite0")
    asm.connect("seitenwand_rechts:hinten", "rueckwand:seite1")
    # Dach: Portal-Giebel pos 25/26, Rückwand 15/16 – die Features der Giebel tragen prefix+5/6
    for wand, base in (("portal", 20), ("rueckwand", 10)):
        wp = portal if wand == "portal" else rueck
        for f in wp.features:
            if f.id == "dach_l":
                f.pos = base + 5
            elif f.id == "dach_r":
                f.pos = base + 6
    asm.connect("portal:dach_l", "dach_links:vorn")
    asm.connect("portal:dach_r", "dach_rechts:vorn")
    asm.connect("rueckwand:dach_l", "dach_links:hinten")
    asm.connect("rueckwand:dach_r", "dach_rechts:hinten")
    # Figuren
    if figuren:
        liste = list(FIGUREN)
        for nm, bauer, fh, hmin in liste:
            _figur(asm, cfg, nm, bauer, max(fh * B, hmin), notes, wm)
        if koenige:
            for nm, art in KOENIGE:
                _figur(asm, cfg, nm, _koenig, max(0.35 * B, 48.0), notes, wm, art)
    for t in dict.fromkeys(notes):
        asm.notes.append(t)
    asm.notes += [
        "Aufbau: Rückwand und Portal in die Bodenplatte stecken, dann die Seitenwände von oben zwischen beide "
        "Giebel schieben – ihre seitlichen Zapfen greifen in die Schlitze von Portal und Rückwand.",
        "Dach: Die Dachhälften mit den Schlitzen auf die Zapfen der Giebelschrägen setzen. Die Kerbe am First "
        "gehört nach vorn – dort steht der Stern auf seinem Mast.",
        "Figuren: Jede Figur mit dem Steckfuß in ihren ovalen Sockel stecken; Kind, Ochse und Esel gehören in den "
        "Stall, Hirte, Schaf und Könige davor.",
        "Bemalen: Die Gravurlinien zeigen Gesichter, Gewandfalten, Fell und Holz – vor dem Zusammenstecken mit "
        "Acrylfarbe oder Beize ausmalen.",
    ]
    return asm
