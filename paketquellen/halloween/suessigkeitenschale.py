"""
Süßigkeitenschale – gesteckte Schale als Hexenkessel oder ausgehöhlter Kürbis.

Vorder- und Rückwand sind große Schauwände mit der Silhouette (Kessel mit Rand, Henkeln, Klauenfüßen
und aufsteigenden Blasen; Kürbis mit Rippen, Zickzack-Schnittkante, Blatt und Ranke). Die Seitenwände
stecken mit Zapfen in Schlitzen der Schauwände, der Boden steckt mit Zapfen ringsum in Schlitzen aller
vier Wände. Alle Verbindungen sind als JointFeature hinterlegt und werden vom Validator geprüft.
In Schauwänden und Seitenwänden sind Motive ausgeschnitten: Gesicht, Fledermäuse vor dem Mond oder
ein Spinnennetz mit Spinne.

3D-Lage: x = Breite (Mitte 0), y = Tiefe (vorne 0), z = Höhe (Unterkante der Seitenwände 0).
"""
from __future__ import annotations

import math
import os
import sys
from typing import List, Tuple

from steckwerk import Assembly, Part, clean, oriented, profile_edge, rect, slot_feature, tab_centers, \
    tab_features, tab_segments
from pakete import num, sel

_here = os.path.dirname(os.path.abspath(__file__))


def _sub(name: str):
    import importlib.util
    path = os.path.join(_here, name + ".py")
    key = "swpaket_halloween_" + name
    mod = sys.modules.get(key)
    if mod is None or getattr(mod, "__file__", None) != path:
        spec = importlib.util.spec_from_file_location(key, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[key] = mod
        spec.loader.exec_module(mod)
    return mod


SP = _sub("_spuk")
K = SP.K
E = SP.E
Figur = K.Figur

FORMEN = [("kessel", "Hexenkessel"), ("kuerbis", "Kürbis")]
MOTIV_VORNE = [("gesicht", "Gesicht"), ("fledermaeuse", "Fledermäuse vor dem Mond"), ("spinnennetz", "Spinnennetz"),
               ("ohne", "ohne Ausschnitt")]
MOTIV_SEITE = [("fledermaeuse", "Fledermäuse"), ("spinnennetz", "Spinnennetz"), ("ohne", "ohne Ausschnitt")]

INFO = dict(
    label="Süßigkeitenschale",
    group="Halloween",
    desc="Gesteckte Schale als Hexenkessel oder Kürbis: Schauwände mit Silhouette, ausgeschnittene Motive "
         "(Gesicht, Fledermäuse, Spinnennetz), Boden und Seitenwände mit Zapfen und Schlitzen.",
    params=[
        sel("form", "Form", FORMEN, "kessel"),
        num("breite", "Breite", 150, 90, 240, help="Innenraum außen gemessen, die Schauwände sind breiter"),
        num("tiefe", "Tiefe", 110, 70, 200),
        num("hoehe", "Höhe", 90, 50, 160, help="Höhe der Seitenwände"),
        sel("motiv_vorne", "Motiv vorne und hinten", MOTIV_VORNE, "gesicht"),
        sel("gesicht", "Gesicht", [("klassisch", "klassisch"), ("gruselig", "gruselig")], "gruselig",
            when={"motiv_vorne": ["gesicht"]}),
        sel("motiv_seiten", "Motiv an den Seiten", MOTIV_SEITE, "fledermaeuse"),
    ],
)

UEBERSETZUNG = {"en": {
    "Süßigkeitenschale": "Candy bowl",
    "Gesteckte Schale als Hexenkessel oder Kürbis: Schauwände mit Silhouette, ausgeschnittene Motive "
    "(Gesicht, Fledermäuse, Spinnennetz), Boden und Seitenwände mit Zapfen und Schlitzen.":
        "Slot-together bowl as a witch's cauldron or a pumpkin: display walls with a silhouette, cut-out motifs "
        "(face, bats, spider web), base and side walls with tenons and slots.",
    "Form": "Shape", "Hexenkessel": "Witch's cauldron", "Kürbis": "Pumpkin", "Breite": "Width", "Tiefe": "Depth",
    "Höhe": "Height", "Innenraum außen gemessen, die Schauwände sind breiter":
        "inner box measured outside, the display walls are wider",
    "Höhe der Seitenwände": "height of the side walls", "Motiv vorne und hinten": "Motif front and back",
    "Gesicht": "Face", "Fledermäuse vor dem Mond": "Bats against the moon", "Spinnennetz": "Spider web",
    "ohne Ausschnitt": "no cut-out", "klassisch": "classic", "gruselig": "creepy",
    "Motiv an den Seiten": "Motif on the sides", "Fledermäuse": "Bats",
    "Schale: Breite muss zwischen 90 und 240 mm liegen": "Bowl: width must be between 90 and 240 mm",
    "Schale: Tiefe muss zwischen 70 und 200 mm liegen": "Bowl: depth must be between 70 and 200 mm",
    "Schale: Höhe muss zwischen 50 und 160 mm liegen": "Bowl: height must be between 50 and 160 mm",
    "Schale: für diese Materialstärke zu klein – Maße vergrößern": "Bowl: too small for this material thickness – increase the size",
    "Zusammenbau: Boden mit seinen Zapfen erst in die eine, dann in die andere Seitenwand stecken. Dann Vorder- und "
    "Rückwand aufschieben, sodass die Zapfen von Seitenwänden und Boden in ihren Schlitzen sitzen. Bei Bedarf "
    "einen Tropfen Holzleim in die Schlitze geben.":
        "Assembly: push the base with its tenons into one side wall, then into the other. Then slide on the front "
        "and back walls so the tenons of side walls and base sit in their slots. Add a drop of wood glue if needed.",
    "Tipp: Für kleine Süßigkeiten die Ausschnitte von innen mit Transparentpapier hinterkleben – mit einem "
    "LED-Teelicht wird die Schale zur Laterne.":
        "Tip: for small sweets, back the cut-outs from inside with tracing paper – with an LED tea light the bowl "
        "becomes a lantern.",
}}


# --------------------------------------------------------------------------------------------------
# Silhouetten der Schauwände (Panel-Koordinaten: x Mitte 0, z wie 3D)
# --------------------------------------------------------------------------------------------------

def _kessel(W: float, H: float, w: float, seed: int) -> Tuple[Figur, list, float, float]:
    """Kessel: bauchiger Körper, Rand, Henkel, Klauenfüße, Blasen. Liefert (Figur, Gravur, z_unten, rand_unten)."""
    f = Figur()
    m = max(8.0, 0.07 * W)
    ht = W / 2 + m                                   # Halbbreite am Rand
    hb = W / 2 + max(16.0, 0.20 * W)                 # Bauch
    zb = -max(10.0, 0.14 * H)                        # Boden des Bauchs
    rim_h = max(7.0, 0.09 * H)
    body = K.spline([(0.0, zb), (0.55 * hb, zb + 0.03 * H), (0.93 * hb, 0.12 * H), (hb, 0.38 * H),
                     (0.96 * hb, 0.62 * H), (ht + 0.25 * (hb - ht), 0.84 * H), (ht, H - rim_h * 0.5),
                     (0.5 * ht, H - rim_h * 0.5), (0.0, H - rim_h * 0.5), (-0.5 * ht, H - rim_h * 0.5),
                     (-ht, H - rim_h * 0.5), (-(ht + 0.25 * (hb - ht)), 0.84 * H), (-0.96 * hb, 0.62 * H),
                     (-hb, 0.38 * H), (-0.93 * hb, 0.12 * H), (-0.55 * hb, zb + 0.03 * H)], closed=True, n=8,
                    tension=0.4)
    f.add(body)
    lip = ht + max(4.0, 0.03 * W)
    f.add(K.stroke([(-lip + rim_h / 2, H), (lip - rim_h / 2, H)], rim_h, cap="rund"))     # Rand
    # Henkel (Ringe an Laschen)
    gr = []
    R = max(9.0, 0.075 * W)
    for s in (-1, 1):
        cx, cz = s * (0.96 * hb + R * 0.55), 0.62 * H
        f.add(K.circle(cx, cz, R, 48))
        f.add(K.stroke([(s * 0.85 * hb, cz + R * 0.2), (cx, cz + R * 0.2)], R * 0.9))
    for s in (-1, 1):
        cx, cz = s * (0.96 * hb + R * 0.55), 0.62 * H
        f.cut(K.circle(cx + s * R * 0.12, cz - R * 0.05, R - max(3.5, 1.7 * w) - R * 0.12, 48))
    # Klauenfüße
    for s in (-1, 1):
        x0 = s * 0.52 * hb
        fh = max(9.0, 0.10 * H)
        f.add([(x0 - 0.10 * hb, zb + 0.06 * H), (x0 + 0.10 * hb, zb + 0.06 * H), (x0 + s * 0.02 * hb + 0.06 * hb, zb - fh * 0.6),
               (x0 + s * 0.10 * hb, zb - fh), (x0, zb - fh * 0.75), (x0 - s * 0.08 * hb, zb - fh),
               (x0 - 0.07 * hb, zb - fh * 0.5)])
        for k in (-1, 0, 1):
            f.add(K.stroke([(x0 + k * 0.06 * hb, zb - fh * 0.7), (x0 + k * 0.09 * hb, zb - fh * 1.05)],
                           max(w * 1.2, 0.025 * hb), w, "spitz"))
    zmin = zb - max(9.0, 0.10 * H) * 1.1
    # Blasen über dem Rand (verbunden)
    r = K.rng(seed, "blasen")
    bx = [(-0.30, 0.55), (-0.08, 0.85), (0.16, 0.65), (0.36, 0.45)]
    for i, (fx, fr) in enumerate(bx):
        br = max(4.5, 0.045 * W) * fr * 1.6
        cx = fx * W
        f.add(K.circle(cx, H + rim_h / 2 + br * 0.55, br, 40))
        if fr > 0.6:
            f.add(K.circle(cx + br * 0.5, H + rim_h / 2 + br * 1.55, br * 0.55, 32))
    # Gravuren: Randbänder, Nieten, Glanzbogen, Tropfen über den Rand
    gr.append(([(-ht + 2, H - rim_h * 0.5 - 2.5), (ht - 2, H - rim_h * 0.5 - 2.5)], False))
    band = 0.80 * H
    gr.append(([(-0.97 * hb, band), (0.97 * hb, band)], False))
    gr.append(([(-0.97 * hb, band - 4.5), (0.97 * hb, band - 4.5)], False))
    for i in range(-6, 7):
        gr.append((K.circle(i * 0.14 * hb, band - 2.25, 0.9, 10), True))
    gr.append((K.arc(-0.35 * hb, 0.36 * H, 0.45 * hb, math.radians(150), math.radians(215), 16), False))
    for fx in (-0.42, 0.05, 0.30):
        x = fx * W
        L = (0.10 + 0.08 * r.random()) * H
        drip = K.chain([(x - 3, H - rim_h * 0.5)], K.bez((x - 2, H - rim_h * 0.5 - L * 0.6), (x - 2.5, H - rim_h * 0.5 - L),
                                                          (x, H - rim_h * 0.5 - L), 6),
                       K.bez((x, H - rim_h * 0.5 - L), (x + 2.5, H - rim_h * 0.5 - L), (x + 2, H - rim_h * 0.5 - L * 0.6), 6),
                       [(x + 3, H - rim_h * 0.5)])
        gr.append((drip, False))
    return f, gr, zmin, H - rim_h * 0.5


def _zickzack(x0: float, x1: float, z: float, a: float) -> List[Tuple[float, float]]:
    n = max(3, int(round(abs(x1 - x0) / (2.2 * a))))
    pts = []
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i / n
        pts.append((x, z + (a / 2 if i % 2 == 0 else -a / 2)))
    return pts


def _kuerbis(W: float, H: float, w: float, seed: int, sw: float = 1.0) -> Tuple[Figur, list, float, float]:
    f = Figur()
    hw = W / 2 + max(14.0, 0.18 * W)
    zb = -max(4.0, 0.05 * H)
    zc = 0.45 * H
    ry = 0.62 * H
    lobes = [(0.0, 0.42, 1.0), (0.30, 0.38, 0.97), (-0.30, 0.38, 0.97), (0.62, 0.33, 0.9), (-0.62, 0.33, 0.9)]
    for fx, frx, fry in lobes:
        f.add(K.ellipse(fx * hw, zc, frx * hw, fry * ry, 0.0, 72))
    a = max(6.0, min(12.0, 0.08 * H))
    zz = _zickzack(-hw * 1.2, hw * 1.2, H, a)
    f.cut(zz + [(hw * 1.3, H + ry), (-hw * 1.3, H + ry)])                         # ausgeschnittener Deckel
    f.cut(K.rect(-hw * 1.3, zb - ry, hw * 2.6, ry))                                  # gerader Stand
    # Blatt und Ranke auf dem Rand
    s = max(30.0, 0.30 * W)
    x0 = 0.42 * hw
    mid = K.bez((x0, H - a), (x0 + 0.3 * s, H + 0.35 * s), (x0 + 0.85 * s, H + 0.22 * s), 16)
    widths = [max(0.30 * s * math.sin(math.pi * (0.06 + 0.94 * i / 16)) ** 0.8, w) * (1 + 0.15 * math.sin(i * 2.1))
              for i in range(17)]
    f.add(K.stroke(mid, 0, widths=widths, cap="spitz"))
    f.cut(K.stroke(mid[3:14], sw, sw * 0.8))
    tend = K.spline([(x0 - 0.05 * s, H - a * 0.3), (x0 - 0.25 * s, H + 0.25 * s), (x0 - 0.50 * s, H + 0.22 * s),
                     (x0 - 0.55 * s, H + 0.08 * s), (x0 - 0.43 * s, H + 0.03 * s), (x0 - 0.40 * s, H + 0.11 * s)], n=8)
    f.line(tend, max(w * 1.2, 0.04 * s))
    gr = []
    for fx in (-0.47, -0.16, 0.16, 0.47):
        gr.append((K.bez((fx * hw * 0.9, zb + 2), (fx * hw * 1.25, zc), (fx * hw * 0.9, H - a), 16), False))
    zmin = zb
    return f, gr, zmin, H - a / 2


# --------------------------------------------------------------------------------------------------
# Motive als Lochfiguren in einem Fenster (x0..x1, z0..z1)
# --------------------------------------------------------------------------------------------------

def _nur_plus(fig: Figur) -> Figur:
    return Figur([o for o in fig.ops if o[0] == "+"])


def _motiv(art: str, box, cfg, seed: int, gesicht: str = "gruselig", form: str = "kessel") -> Figur:
    x0, z0, x1, z1 = box
    bw, bh = x1 - x0, z1 - z0
    cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
    w = SP.wmin(cfg)
    f = Figur()
    if art == "gesicht":
        g, _ = SP.kuerbis(1.0, cfg, gesicht)
        holes = [p for s_, p in g.ops if s_ == "-" and len(p) <= 12]       # Augen, Nase, Mund
        face = Figur().add(*holes)
        fx0, fy0, fx1, fy1 = face.bbox()
        k = min(bw / (fx1 - fx0), bh / (fy1 - fy0)) * 0.92
        f.merge(face.map(lambda p: (cx + (p[0] - (fx0 + fx1) / 2) * k, cz + (p[1] - (fy0 + fy1) / 2) * k)))
    elif art == "fledermaeuse":
        rm = min(bw, bh) * 0.30
        mx, mz = x0 + bw * 0.70, z0 + bh * 0.62
        f.add(K.circle(mx, mz, rm, 64))
        f.cut(K.circle(mx + rm * 0.42, mz + rm * 0.22, rm * 0.86, 64))                   # Sichel
        r = K.rng(seed, "fledermaeuse")
        spots = [(0.22, 0.68, 0.40, "segeln"), (0.40, 0.25, 0.32, "hoch"), (0.95, 0.20, 0.22, "tief"),
                 (0.08, 0.22, 0.24, "kurve"), (0.97, 0.90, 0.16, "hoch")]
        gap = w + 1.5
        taken = [(mx - rm - gap, mz - rm - gap, mx + rm + gap, mz + rm + gap)]
        for fx, fz, fs, pose in spots:
            S = min(bw, 2.2 * bh) * fs
            for _ in range(4):
                if S < 20:
                    break
                bat, _ = SP.fledermaus(S, pose, cfg, augen=False)
                b = _nur_plus(bat).place(x0 + fx * bw, z0 + fz * bh, 1.0, (r.random() - 0.5) * 0.4)
                bx0, bz0, bx1, bz1 = b.bbox()
                # ins Fenster schieben
                dx = max(0.0, x0 - bx0) - max(0.0, bx1 - x1)
                dz = max(0.0, z0 - bz0) - max(0.0, bz1 - z1)
                b = b.place(dx, dz, 1.0)
                bx0, bz0, bx1, bz1 = b.bbox()
                if bx0 >= x0 - 0.01 and bx1 <= x1 + 0.01 and bz0 >= z0 - 0.01 and bz1 <= z1 + 0.01 and \
                        not any(bx0 < t[2] and t[0] < bx1 and bz0 < t[3] and t[1] < bz1 for t in taken):
                    f.merge(b)
                    taken.append((bx0 - gap, bz0 - gap, bx1 + gap, bz1 + gap))
                    break
                S *= 0.8
    elif art == "spinnennetz":
        R = min(bw, bh) * 1.05
        hub = (x0 + 1.0, z1 - 1.0)
        f.add(K.rect(x0, z0, bw, bh))
        net, ends, outer, angs, radii = SP.netz(hub[0], hub[1], R, -math.pi / 2, 0.0, max(3, int(R / 14)),
                                                5, w, seed, False, False, voll=False)
        f.ops += [("-", p) for s_, p in net.ops if s_ == "+"]
        sp = SP.spinne(min(bw, bh) * 0.42, cfg, x0 + bw * 0.72, z0 + bh * 0.40, 0.3, zeichnung=False)
        f.ops += [("-", p) for s_, p in sp.ops if s_ == "+"]
        f.ops.append(("-", K.stroke([(x0 + bw * 0.72, z1), (x0 + bw * 0.72, z0 + bh * 0.40)], w)))
    return f


# --------------------------------------------------------------------------------------------------
# Bauteile
# --------------------------------------------------------------------------------------------------

def build(cfg, name: str = "suessigkeitenschale", form: str = "kessel", breite: float = 150.0, tiefe: float = 110.0,
          hoehe: float = 90.0, motiv_vorne: str = "gesicht", gesicht: str = "gruselig",
          motiv_seiten: str = "fledermaeuse"):
    from models import _deko as dk
    dk.check_choice("Form", form, FORMEN)
    dk.check_choice("Motiv vorne und hinten", motiv_vorne, MOTIV_VORNE)
    dk.check_choice("Motiv an den Seiten", motiv_seiten, MOTIV_SEITE)
    dk.check_choice("Gesicht", gesicht, [("klassisch", ""), ("gruselig", "")])
    W, D, H = cfg.s(breite), cfg.s(tiefe), cfg.s(hoehe)
    if not 90 <= W <= 240:
        raise ValueError("Schale: Breite muss zwischen 90 und 240 mm liegen")
    if not 70 <= D <= 200:
        raise ValueError("Schale: Tiefe muss zwischen 70 und 200 mm liegen")
    if not 50 <= H <= 160:
        raise ValueError("Schale: Höhe muss zwischen 50 und 160 mm liegen")
    T = cfg.T
    if min(W, D, H) < 12 * T:
        raise ValueError("Schale: für diese Materialstärke zu klein – Maße vergrößern")
    web, kerf = cfg.min_web, cfg.kerf
    w = SP.wmin(cfg)
    Ds = D - 2 * T                    # Seitenwand zwischen den Schauwänden
    Wi = W - 2 * T                    # Boden zwischen den Seitenwänden
    zb = max(1.5 * T, 5.0)            # Unterkante des Bodens
    seed = cfg.seed
    notes: List[str] = []
    asm = Assembly(name, params=dict(form=form, breite=W, tiefe=D, hoehe=H, motiv_vorne=motiv_vorne,
                                     motiv_seiten=motiv_seiten))

    # Verbindungsmaße
    inset_z = max(2.5 * T, 8.0)
    zc_s, tw_s = tab_centers(H - zb - T, cfg, inset=inset_z)       # Seitenwand-Zapfen (über dem Boden)
    zc_s = [zb + T + c for c in zc_s]
    xc_b, tw_b = tab_centers(Wi, cfg, inset=2 * T)                  # Bodenzapfen vorne/hinten (lokal 0..Wi)
    uc_b, tw_u = tab_centers(Ds, cfg, inset=2 * T)                  # Bodenzapfen links/rechts (lokal 0..Ds)

    # ------------------------------------------------------------ Schauwände
    if form == "kessel":
        sil, grav, zmin, z_rand = _kessel(W, H, w, seed)
    else:
        sil, grav, zmin, z_rand = _kuerbis(W, H, w, seed, SP.smin(cfg))
    top_slot = max(zc_s) + tw_s / 2
    if top_slot > z_rand - max(4.0, 1.5 * T):
        raise ValueError("Schale: für diese Materialstärke zu klein – Maße vergrößern")
    win = (-W / 2 + T + max(6.0, 2 * T), zb + T + max(6.0, 2 * T), W / 2 - T - max(6.0, 2 * T),
           z_rand - max(6.0, 0.08 * H))
    for side in ("vorne", "hinten"):
        pname = f"{name}_{side}"
        slots = []                                     # (fid, x, z, w, h, length_along_x, pos)
        for k, zc in enumerate(zc_s):
            slots.append((f"links{k}", -W / 2, zc - tw_s / 2, T, tw_s, False, zc))
            slots.append((f"rechts{k}", W / 2 - T, zc - tw_s / 2, T, tw_s, False, zc))
        for k, c in enumerate(xc_b):
            x = -Wi / 2 + c
            slots.append((f"boden{k}", x - tw_b / 2, zb, tw_b, T, True, x))
        x0_, z0_, x1_, z1_ = sil.bbox()
        lw = E.Leinwand((x0_ - 3, z0_ - 3, x1_ + 3, z1_ + 3), max(0.08, min(0.12, (x1_ - x0_) / 2600)))
        mat = lw.figur(sil)
        if motiv_vorne != "ohne":
            mf = _motiv(motiv_vorne, win, cfg, seed + (0 if side == "vorne" else 5), gesicht, form)
            fenster = lw.flaechen([K.rect(win[0], win[1], win[2] - win[0], win[3] - win[1])])
            mat = E._andnot(mat, E._and(lw.figur(mf), fenster))
        guard = lw.flaechen([K.rect(x - 2.2 - web, z - 2.2 - web, wd + 4.4 + 2 * web, ht + 4.4 + 2 * web)
                             for _, x, z, wd, ht, _, _ in slots])
        mat = mat.union(E._and(guard, lw.figur(sil)))
        part = E.teil_aus_raster(pname, lw, mat, web, kerf, notes)
        for fid, x, z, wd, ht, along_x, pos in slots:
            sl = rect(x, z, wd, ht)
            part.holes = [h for h in part.holes if all(not (x - 1.5 <= q[0] <= x + wd + 1.5 and
                                                            z - 1.5 <= q[1] <= z + ht + 1.5) for q in h)]
            feat, hole = slot_feature(fid, x, z, wd, ht, along_x, pos)
            part.holes.append(hole)
            part.features.append(feat)
        SP.gravur(part, grav, seed)
        asm.parts.append(part)

    # ------------------------------------------------------------ Seitenwände
    zig = form == "kuerbis"
    a_z = max(6.0, min(12.0, 0.08 * H))
    for side in ("links", "rechts"):
        pname = f"{name}_seite_{side}"
        p0, p1, p2, p3 = (0.0, 0.0), (Ds, 0.0), (Ds, H), (0.0, H)
        pts = [p0]
        right_c = sorted(zc_s)
        pts += profile_edge(p1, p2, tab_segments(H, right_c, tw_s, T))
        feats = tab_features("hinten", p1, p2, right_c, tw_s, T, lambda t: t)
        if zig:
            top = _zickzack(Ds, 0.0, H - a_z / 2, a_z)
            top[0], top[-1] = (Ds, H), (0.0, H)
            pts += top[:-1]
        else:
            pts.append(p2)
        left_c = sorted(H - z for z in zc_s)
        pts += profile_edge(p3, p0, tab_segments(H, left_c, tw_s, T))
        feats += tab_features("vorne", p3, p0, left_c, tw_s, T, lambda t: H - t)
        part = Part(pname, clean(pts), features=feats)
        # Bodenschlitze
        for k, c in enumerate(uc_b):
            feat, hole = slot_feature(f"boden{k}", c - tw_u / 2, zb, tw_u, T, True, c)
            part.holes.append(hole)
            part.features.append(feat)
        # Motiv
        if motiv_seiten != "ohne":
            mg = max(6.0, 2 * T)
            box = (mg, zb + T + mg, Ds - mg, (H - a_z if zig else H) - mg)
            if box[2] - box[0] > 25 and box[3] - box[1] > 20:
                lw = E.Leinwand((-T - 2, -2, Ds + T + 2, H + 2), max(0.08, min(0.12, Ds / 2000)))
                bereich = lw.flaechen([K.rect(box[0], box[1], box[2] - box[0], box[3] - box[1])])
                mf = _motiv(motiv_seiten, box, cfg, seed + (11 if side == "links" else 17))
                material = E._andnot(bereich, lw.figur(mf))
                for h in E.durchbrueche(lw, bereich, material, web, kerf, notes, pname):
                    part.add_hole(h)
        if zig:
            gr = []
        else:
            gr = [([(2.0, H - 4.0), (Ds - 2.0, H - 4.0)], False), ([(2.0, 0.80 * H), (Ds - 2.0, 0.80 * H)], False)]
        SP.gravur(part, gr, seed)
        asm.parts.append(part)

    # ------------------------------------------------------------ Boden
    q0, q1, q2, q3 = (-Wi / 2, 0.0), (Wi / 2, 0.0), (Wi / 2, Ds), (-Wi / 2, Ds)
    pts = []
    pts += profile_edge(q0, q1, tab_segments(Wi, xc_b, tw_b, T))
    feats = tab_features("vorne", q0, q1, xc_b, tw_b, T, lambda t: -Wi / 2 + t)
    pts += profile_edge(q1, q2, tab_segments(Ds, uc_b, tw_u, T))
    feats += tab_features("rechts", q1, q2, uc_b, tw_u, T, lambda t: t)
    back_c = sorted(Wi - c for c in xc_b)
    pts += profile_edge(q2, q3, tab_segments(Wi, back_c, tw_b, T))
    feats += tab_features("hinten", q2, q3, back_c, tw_b, T, lambda t: Wi / 2 - t)
    left_c = sorted(Ds - c for c in uc_b)
    pts += profile_edge(q3, q0, tab_segments(Ds, left_c, tw_u, T))
    feats += tab_features("links", q3, q0, left_c, tw_u, T, lambda t: Ds - t)
    boden = Part(f"{name}_boden", clean(pts), features=feats)
    # Spinnennetz-Gravur auf dem Boden
    net, ends, outer, angs, radii = SP.netz(0.0, Ds / 2, min(Wi, Ds) * 0.42, 0.0, 2 * math.pi, 5, 10, 0.8, seed,
                                            False, False, voll=True)
    lines = []
    for a in angs:
        lines.append(([(math.cos(a) * 3, Ds / 2 + math.sin(a) * 3),
                       (math.cos(a) * min(Wi, Ds) * 0.45, Ds / 2 + math.sin(a) * min(Wi, Ds) * 0.45)], False))
    for rr in radii:
        n = len(angs)
        for i in range(n):
            a, b = angs[i], angs[(i + 1) % n] + (2 * math.pi if i == n - 1 else 0)
            pa = (math.cos(a) * rr, Ds / 2 + math.sin(a) * rr)
            pb = (math.cos(b) * rr, Ds / 2 + math.sin(b) * rr)
            c = SP.lerp(SP.lerp(pa, pb, 0.5), (0.0, Ds / 2), 0.2 * (b - a))
            lines.append((K.bez(pa, c, pb, 10), False))
    SP.gravur(boden, lines, seed, rand=2.0)
    asm.parts.append(boden)

    # ------------------------------------------------------------ Verbindungen
    def paare(pa: str, pre_a: str, pb: str, pre_b: str) -> None:
        fa = sorted([f for f in asm.part(pa).features if f.id.startswith(pre_a)], key=lambda f: f.pos)
        fb = sorted([f for f in asm.part(pb).features if f.id.startswith(pre_b)], key=lambda f: f.pos)
        for a, b in zip(fa, fb):
            asm.connect(f"{pa}:{a.id}", f"{pb}:{b.id}")

    for side in ("vorne", "hinten"):
        for ws in ("links", "rechts"):
            paare(f"{name}_seite_{ws}", side, f"{name}_{side}", ws)
    # Boden vorne/hinten: nach Position paaren
    for side in ("vorne", "hinten"):
        bf = sorted([f for f in boden.features if f.id.startswith(side)], key=lambda f: f.pos)
        pf = sorted([f for f in asm.part(f"{name}_{side}").features if f.id.startswith("boden")], key=lambda f: f.pos)
        for a, b in zip(bf, pf):
            asm.connect(f"{boden.name}:{a.id}", f"{name}_{side}:{b.id}")
    for side in ("links", "rechts"):
        bf = sorted([f for f in boden.features if f.id.startswith(side)], key=lambda f: f.pos)
        pf = sorted([f for f in asm.part(f"{name}_seite_{side}").features if f.id.startswith("boden")],
                    key=lambda f: f.pos)
        for a, b in zip(bf, pf):
            asm.connect(f"{boden.name}:{a.id}", f"{name}_seite_{side}:{b.id}")
    for t in dict.fromkeys(notes):
        asm.notes.append(t)
    asm.notes.append("Zusammenbau: Boden mit seinen Zapfen erst in die eine, dann in die andere Seitenwand stecken. "
                     "Dann Vorder- und Rückwand aufschieben, sodass die Zapfen von Seitenwänden und Boden in ihren "
                     "Schlitzen sitzen. Bei Bedarf einen Tropfen Holzleim in die Schlitze geben.")
    asm.notes.append("Tipp: Für kleine Süßigkeiten die Ausschnitte von innen mit Transparentpapier hinterkleben – mit "
                     "einem LED-Teelicht wird die Schale zur Laterne.")
    return asm
