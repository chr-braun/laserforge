"""
_figuren.py – detailreiche Motive (Bibliothek „Verzierungen“, ursprünglich aus dem Paket Mehrlagig), alle von Hand gezeichnet.

Jede Funktion liefert eine Figur (siehe _kit.py) in mm. Wo nicht anders gesagt, steht die Figur mit
der Grundlinie auf y = 0 und ist um x = 0 zentriert; die Größe bestimmt der erste Parameter.
Feine Glieder sind so breit angelegt, dass sie ab der Mindestgröße (siehe MIN_GROESSE) den Mindeststeg
von 1 mm halten.
"""
from __future__ import annotations

import math
import os
import sys
from typing import List, Optional, Sequence

_here = os.path.dirname(os.path.abspath(__file__))


def _kit():
    import importlib.util
    import zlib
    path = os.path.join(_here, "_kit.py")
    name = "swbib_verzierungen_%s_%08x" % ("_kit", zlib.crc32(path.encode()))
    mod = sys.modules.get(name)
    if mod is None or getattr(mod, "__file__", None) != path:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return mod


K = _kit()
Figur, bez, bez3, chain, spline, stroke, arc = K.Figur, K.bez, K.bez3, K.chain, K.spline, K.stroke, K.arc


# --------------------------------------------------------------------------------------------------
# Fichte
# --------------------------------------------------------------------------------------------------

def fichte(h: float, seed: int = 1, breite: float = 0.62, schnee: bool = False) -> Figur:
    """Fichte: hängende Äste mit Nadelfransen, Spitzen leicht nach oben gebogen, Spitzentrieb. Höhe h."""
    r = K.rng(seed, "fichte")
    f = Figur()
    trunk_h = 0.06 * h
    tw = max(0.05 * h, 1.4)
    f.add(K.rect(-tw / 2, 0, tw, 0.9 * h), [(-tw * 0.9, 0), (tw * 0.9, 0), (0, 0.5 * h)])
    tiers = 8 + int(h > 50) * 2 + int(h > 100) * 2
    y_bot, y_top = trunk_h + 0.03 * h, h * 0.9
    tw_min = 0.011 * h
    for i in range(tiers):
        t = i / (tiers - 1)
        y = y_bot + (y_top - y_bot) * (t ** 0.95)
        span = breite * h / 2 * (1 - t) ** 1.05 + 0.025 * h
        gap = (y_top - y_bot) / tiers
        for side in (-1, 1):
            w = span * (1 + K.jitter(r, 0.12))
            droop = gap * (0.9 + 0.5 * r.random()) * (1 - 0.4 * t)
            p0 = (0.0, y + gap * 0.25)
            tip = (side * w, y - droop + gap * 0.25)
            c1 = (side * w * 0.30, y + gap * 0.35)
            c2 = (side * w * 0.75, y - droop * 0.9)
            br = bez3(p0, c1, c2, tip, 24)
            # Spitze leicht nach oben
            up = (tip[0] + side * w * 0.06, tip[1] + gap * 0.18)
            br = br + [up]
            f.add(stroke(br, max(0.035 * h * (1 - 0.6 * t), tw_min * 1.6), tw_min * 0.9, cap="rund"))
            # Astfläche: unter dem Ast eine nach außen dünner werdende „Schürze“
            low = []
            for k, q in enumerate(br[:-1]):
                u = k / (len(br) - 2)
                low.append((q[0], q[1] - gap * (0.75 * (1 - u) ** 1.3 + 0.08)))
            f.add(br[:-1] + list(reversed(low)))
            # Nadelfransen an der Unterkante der Schürze (bei kleinen Bäumen gröber)
            if h < 30:
                continue
            n_tw = max(4, int(K.path_len(br) / max(0.8, 0.012 * h)))
            for k in range(1, n_tw):
                u = k / n_tw
                ix = int(u * (len(br) - 2))
                q = low[min(ix, len(low) - 1)] if r.random() < 0.8 else br[ix]
                q2 = br[ix + 1]
                q0 = br[ix]
                ang = math.atan2(q2[1] - q0[1], q2[0] - q0[0])
                ang = math.atan2(q2[1] - q[1], q2[0] - q[0])
                down = ang - side * math.radians(55 + 25 * r.random())
                L = gap * (0.45 + 0.5 * r.random()) * (1 - 0.3 * u) + 0.008 * h
                end = (q[0] + L * math.cos(down), q[1] + L * math.sin(down))
                mid = ((q[0] + end[0]) / 2 + side * L * 0.12, (q[1] + end[1]) / 2)
                f.add(stroke(bez(q, mid, end, 6), tw_min * 1.5, tw_min * 0.3, cap="spitz"))
                if r.random() < 0.45:                              # kurze Triebe nach oben
                    upa = ang + side * math.radians(40 + 20 * r.random())
                    L2 = L * 0.35
                    f.add(stroke([q, (q[0] + L2 * math.cos(upa), q[1] + L2 * math.sin(upa))],
                                 tw_min * 1.2, tw_min * 0.3, cap="spitz"))
    ty = y_top
    f.add(stroke([(0, ty - 0.06 * h), (0, h)], 0.03 * h, 0.006 * h, cap="spitz"))
    for side in (-1, 1):
        f.add(stroke(bez((0, ty - 0.02 * h), (side * 0.03 * h, ty + 0.0 * h), (side * 0.055 * h, ty + 0.03 * h), 6),
                     0.018 * h, 0.004 * h, cap="spitz"))
    if schnee:
        f.merge(_schnee_auf_fichte(h, breite, tiers, y_bot, y_top, r))
    return f


def _schnee_auf_fichte(h, breite, tiers, y_bot, y_top, r) -> Figur:
    f = Figur()
    for i in range(1, tiers - 1, 2):
        t = i / (tiers - 1)
        y = y_bot + (y_top - y_bot) * (t ** 0.92) * 0.97
        th = (y_top - y_bot) / tiers * (1.9 - 0.5 * t)
        w = breite * h / 2 * (1 - t) ** 1.08 * 0.7
        f.add(K.ellipse(0, y + th * 0.55, w, th * 0.22))
    return f


# --------------------------------------------------------------------------------------------------
# Hirsch
# --------------------------------------------------------------------------------------------------

def _leg(f: Figur, pts, widths, hoof: float, wmin: float = 0.0):
    p = spline(pts, n=8)
    ws = [widths[0] + (widths[-1] - widths[0]) * 0 for _ in p]
    # Breiten entlang der Stützpunkte interpolieren
    seg = len(p) - 1
    m = len(widths) - 1
    ws = []
    for i in range(len(p)):
        u = i / seg * m
        k = min(int(u), m - 1)
        ws.append(max(wmin, widths[k] + (widths[k + 1] - widths[k]) * (u - k)))
    f.add(stroke(p, 0, widths=ws, cap="rund"))
    x, y = pts[-1]
    hoof = max(hoof, wmin * 1.2)
    f.add([(x - hoof * 0.55, 0.0), (x + hoof * 0.75, 0.0), (x + hoof * 0.45, hoof * 0.9), (x - hoof * 0.45, hoof * 0.9)])


def _antler(f: Figur, base, beam, tines, w0, w1):
    """Geweihstange als Spline mit Enden: tines = [(u auf der Stange, Endpunkt, Krümmung)]."""
    b = spline([base] + beam, n=10)
    f.add(stroke(b, w0, w1, cap="rund"))
    L = len(b) - 1
    for u, end, bend in tines:
        q = b[int(u * L)]
        w = w0 + (w1 - w0) * u
        mid = ((q[0] + end[0]) / 2 + bend[0], (q[1] + end[1]) / 2 + bend[1])
        f.add(stroke(bez(q, mid, end, 10), w * 0.95, w1, cap="rund"))


def hirsch(h: float, wmin_mm: float = 0.0) -> Figur:
    """Stolzer Rothirsch im Profil (blickt nach rechts) mit vielendigem Geweih. h = Schulterhöhe.
    wmin_mm: Mindestbreite von Beinen und Geweih in mm (für kleine Motive)."""
    f = Figur()
    wm = wmin_mm / h
    body = [(-0.50, 1.00), (-0.30, 0.985), (-0.05, 0.98), (0.18, 1.02), (0.28, 1.08), (0.40, 1.21),
            (0.52, 1.36), (0.60, 1.44), (0.655, 1.475), (0.70, 1.47), (0.76, 1.42), (0.84, 1.355),
            (0.905, 1.31), (0.93, 1.275), (0.915, 1.235), (0.87, 1.225), (0.835, 1.21), (0.77, 1.22),
            (0.71, 1.245), (0.665, 1.215), (0.625, 1.12), (0.575, 0.99), (0.53, 0.86), (0.47, 0.72),
            (0.34, 0.60), (0.12, 0.565), (-0.14, 0.585), (-0.34, 0.62), (-0.50, 0.72), (-0.58, 0.86)]
    f.add(spline(body, closed=True, n=8))
    # Mähne: zottiger Behang am Hals
    for k in range(6):
        u = k / 5
        x = 0.60 - 0.09 * u
        y = 1.20 - 0.32 * u
        f.add([(x - 0.03, y + 0.05), (x + 0.045, y - 0.035 - 0.02 * (k % 2)), (x - 0.04, y - 0.02)])
    # Beine (Stützpunkte von oben nach unten)
    _leg(f, [(0.40, 0.72), (0.41, 0.46), (0.385, 0.30), (0.39, 0.14), (0.40, 0.03)], [0.15, 0.08, 0.05, 0.042, 0.042], 0.06, wm)
    _leg(f, [(0.27, 0.68), (0.24, 0.46), (0.20, 0.30), (0.17, 0.15), (0.14, 0.03)], [0.13, 0.07, 0.048, 0.04, 0.04], 0.056, wm)
    _leg(f, [(-0.38, 0.82), (-0.28, 0.56), (-0.42, 0.33), (-0.40, 0.15), (-0.38, 0.03)], [0.25, 0.12, 0.055, 0.042, 0.042], 0.06, wm)
    _leg(f, [(-0.46, 0.82), (-0.38, 0.57), (-0.54, 0.36), (-0.58, 0.18), (-0.61, 0.03)], [0.21, 0.10, 0.05, 0.04, 0.04], 0.056, wm)
    f.add(stroke([(-0.545, 0.95), (-0.60, 0.88)], 0.06, 0.03, cap="rund"))
    # Ohren (nach hinten oben gestellt)
    f.add(spline([(0.62, 1.44), (0.55, 1.50), (0.46, 1.555), (0.53, 1.555), (0.64, 1.485)], closed=True, n=6))
    # Geweih: Stangen schwingen nach hinten, Sprossen zeigen nach vorn
    def stange(base, rot, s):
        ca, sa = math.cos(rot), math.sin(rot)

        def P(x, y):
            x, y = (x - 0.66) * s, (y - 1.48) * s
            return (base[0] + x * ca - y * sa, base[1] + x * sa + y * ca)
        _antler(f, P(0.66, 1.48),
                [P(0.62, 1.62), P(0.53, 1.77), P(0.44, 1.92), P(0.39, 2.06), P(0.40, 2.19)],
                [(0.06, P(0.82, 1.60), (0.01, -0.045)),          # Augspross
                 (0.17, P(0.77, 1.73), (0.0, -0.04)),           # Eissprosse
                 (0.50, P(0.60, 1.99), (0.0, -0.03)),           # Mittelsprosse
                 (0.88, P(0.28, 2.24), (0.0, -0.035)),          # Krone
                 (0.93, P(0.36, 2.33), (-0.02, 0.0)),
                 (0.97, P(0.49, 2.31), (0.0, -0.025))],
                max(wm, 0.08 * s), max(wm, 0.045 * s))
    stange((0.69, 1.47), -0.30, 0.9)                        # fernere Stange, nach vorn geneigt
    stange((0.66, 1.48), 0.0, 1.0)
    return f.place(0, 0, h)


# --------------------------------------------------------------------------------------------------
# Häuser, Kirche, Laterne, Zaun, Schneemann
# --------------------------------------------------------------------------------------------------

def _fenster(f: Figur, cx: float, y: float, w: float, h: float, sprossen: bool = True, bogen: bool = False):
    """Fenster als Durchbruch; mit Sprossenkreuz in vier Scheiben geteilt (Sprosse ≥ 1.1 mm)."""
    if bogen:
        r = w / 2
        win = chain([(cx - r, y), (cx + r, y), (cx + r, y + h - r)], arc(cx, y + h - r, r, 0, math.pi, 14)[1:])
    else:
        win = K.rect(cx - w / 2, y, w, h)
    f.cut(win)
    if sprossen and w >= 4.6 and h >= 5.5:
        s = max(1.15, 0.13 * w)
        f.add(K.rect(cx - s / 2, y - 0.2, s, h + 0.4), K.rect(cx - w / 2 - 0.2, y + h * 0.52 - s / 2, w + 0.4, s))


def _eiszapfen(f: Figur, x0: float, x1: float, y: float, lmax: float, seed: int):
    r = K.rng(seed, "eis")
    x = x0
    while x < x1:
        w = r.uniform(0.8, 1.4) * max(1.4, lmax * 0.28)
        L = r.uniform(0.35, 1.0) * lmax
        f.add([(x, y + 0.3), (x + w, y + 0.3), (x + w * 0.5, y - L)])
        x += w * r.uniform(0.9, 1.6)


def haus(w: float, h: float, seed: int = 1, art: str = "giebel") -> Figur:
    """Winterhaus mit verschneitem Satteldach, Eiszapfen, Schornstein mit Rauchfahne, Sprossenfenstern
    und Tür. w = Breite der Wand, h = Höhe bis zum First. art: giebel | traufe."""
    r = K.rng(seed, "haus")
    f = Figur()
    wall = h * (0.50 if art == "giebel" else 0.58)
    over = 0.10 * w
    snow = max(1.6, 0.035 * h)
    f.add(K.rect(-w / 2, 0, w, wall + 0.5))
    if art == "giebel":
        roof = [(-w / 2 - over, wall - 0.04 * h), (w / 2 + over, wall - 0.04 * h), (0.0, h)]
        f.add(roof)
        # Schneedecke: wulstig über der Dachkante
        f.add(K.stroke([(-w / 2 - over * 1.1, wall - 0.04 * h), (0.0, h + snow * 0.4), (w / 2 + over * 1.1, wall - 0.04 * h)],
                       snow * 1.4, snow * 1.4, cap="rund"))
        _eiszapfen(f, -w / 2 - over, -w / 2 + 0.15 * w, wall - 0.04 * h - snow * 0.5, 0.07 * h, seed)
        _eiszapfen(f, w / 2 - 0.15 * w, w / 2 + over, wall - 0.04 * h - snow * 0.5, 0.07 * h, seed + 1)
        cx = w * 0.22 * (1 if r.random() < 0.5 else -1)
        ch_y = wall + (h - wall) * (1 - abs(cx) / (w / 2 + over))
    else:
        top = h
        roof = [(-w / 2 - over, wall), (w / 2 + over, wall), (w / 2 - 0.12 * w, top), (-w / 2 + 0.12 * w, top)]
        f.add(roof)
        f.add(K.stroke([(-w / 2 - over, wall), (-w / 2 + 0.12 * w, top + snow * 0.3), (w / 2 - 0.12 * w, top + snow * 0.3),
                        (w / 2 + over, wall)], snow * 1.4, snow * 1.4, cap="rund"))
        _eiszapfen(f, -w / 2 - over, w / 2 + over, wall - snow * 0.5, 0.06 * h, seed)
        cx = w * r.uniform(-0.25, 0.25)
        ch_y = top
    # Schornstein mit Rauch
    cw = max(2.6, 0.09 * w)
    f.add(K.rect(cx - cw / 2, ch_y - 0.1 * h, cw, 0.17 * h + (h - ch_y)))
    f.add(K.rect(cx - cw * 0.65, h + 0.06 * h - (h - ch_y) * 0 + (ch_y - h), cw * 1.3, max(1.3, 0.025 * h)))
    sm_y = ch_y + 0.085 * h
    smoke = spline([(cx, sm_y), (cx + 0.06 * h, sm_y + 0.10 * h), (cx - 0.02 * h, sm_y + 0.2 * h),
                    (cx + 0.10 * h, sm_y + 0.30 * h)], n=8)
    f.add(stroke(smoke, max(2.2, 0.06 * h), max(1.3, 0.025 * h), cap="rund"))
    # Fenster und Tür (Licht scheint durch)
    fw = max(5.0, 0.16 * w)
    fh = max(6.0, 0.17 * h)
    door_w = max(5.0, 0.15 * w)
    dx = (-0.22 if r.random() < 0.5 else 0.22) * w
    _tuer(f, dx, door_w, min(0.30 * h, wall * 0.62))
    for x in (-0.25 * w, 0.0, 0.25 * w):
        if abs(x - dx) < door_w * 0.9 + fw / 2:
            continue
        _fenster(f, x, wall * 0.40, fw, fh)
    if art == "giebel":
        _fenster(f, 0.0, wall + 0.10 * (h - wall), fw * 0.8, fh * 0.75, bogen=True)
    return f


def _tuer(f: Figur, cx: float, w: float, h: float):
    r = w / 2
    f.cut(chain([(cx - r, 0.9), (cx + r, 0.9), (cx + r, h - r)], arc(cx, h - r, r, 0, math.pi, 12)[1:]))
    # Kranz an der Tür bleibt als Material stehen (Ring mit Durchbrüchen wäre zu fein)
    f.add(K.rect(cx - max(0.6, 0.06 * w), 0.9, max(1.2, 0.12 * w), h - r))


def kirche(h: float, seed: int = 1, turm: str = "zwiebel") -> Figur:
    """Dorfkirche: Schiff mit Rundbogenfenstern und Rosette, Turm mit Schallarkaden, Uhr und
    Zwiebelhaube (oder Spitzhelm), Kreuz auf der Spitze. h = Gesamthöhe."""
    f = Figur()
    tw = 0.20 * h                       # Turmbreite
    tx = -0.20 * h                      # Turmmitte
    nave_w, nave_h = 0.55 * h, 0.30 * h
    nx0 = tx + tw / 2 - 0.02 * h
    # Schiff mit Dach
    f.add(K.rect(nx0, 0, nave_w, nave_h))
    f.add([(nx0 - 0.03 * h, nave_h), (nx0 + nave_w + 0.03 * h, nave_h), (nx0 + nave_w - 0.08 * h, nave_h + 0.17 * h),
           (nx0 + 0.02 * h, nave_h + 0.17 * h)])
    f.add(K.stroke([(nx0 - 0.035 * h, nave_h), (nx0 + 0.02 * h, nave_h + 0.175 * h), (nx0 + nave_w - 0.08 * h, nave_h + 0.175 * h),
                    (nx0 + nave_w + 0.035 * h, nave_h)], 0.022 * h, 0.022 * h))
    _eiszapfen(f, nx0, nx0 + nave_w + 0.03 * h, nave_h - 0.01 * h, 0.035 * h, seed)
    # Apsis rechts
    ax = nx0 + nave_w
    f.add(chain([(ax - 0.01 * h, 0)], arc(ax, 0.0, 0.11 * h, 0, math.pi / 2, 12), [(ax - 0.01 * h, 0.11 * h)]))
    for k in range(3):
        _fenster(f, nx0 + 0.12 * h + k * 0.14 * h, 0.07 * h, 0.055 * h, 0.15 * h, sprossen=False, bogen=True)
    # Turm
    T_top = 0.62 * h
    f.add(K.rect(tx - tw / 2, 0, tw, T_top))
    f.add(K.rect(tx - tw / 2 - 0.012 * h, T_top - 0.01 * h, tw + 0.024 * h, 0.025 * h))     # Gesims
    f.add(K.rect(tx - tw / 2 - 0.012 * h, 0.40 * h, tw + 0.024 * h, 0.018 * h))
    # Portal, Uhr, Schallarkaden
    _tuer(f, tx, 0.09 * h, 0.17 * h)
    f.cut(K.circle(tx, 0.33 * h, 0.055 * h, 40))
    hand_w = max(1.1, 0.012 * h)
    f.add(K.stroke([(tx, 0.33 * h), (tx, 0.33 * h + 0.05 * h)], hand_w, hand_w),
          K.stroke([(tx, 0.33 * h), (tx + 0.04 * h, 0.33 * h - 0.012 * h)], hand_w, hand_w))
    f.add(K.circle(tx, 0.33 * h, hand_w * 0.9, 12))
    # Zeiger hängen an einem Steg zum Rand, damit nichts herausfällt
    f.add(K.rect(tx - hand_w / 2, 0.33 * h - 0.056 * h, hand_w, 0.056 * h))
    for k in (-1, 1):
        _fenster(f, tx + k * 0.045 * h, 0.46 * h, 0.05 * h, 0.12 * h, sprossen=False, bogen=True)
    if turm == "zwiebel":
        b = T_top + 0.015 * h
        dome = spline([(tx - tw / 2 - 0.01 * h, b), (tx - tw * 0.62, b + 0.06 * h), (tx - tw * 0.45, b + 0.13 * h),
                       (tx - 0.02 * h, b + 0.19 * h), (tx, b + 0.21 * h), (tx + 0.02 * h, b + 0.19 * h),
                       (tx + tw * 0.45, b + 0.13 * h), (tx + tw * 0.62, b + 0.06 * h), (tx + tw / 2 + 0.01 * h, b)], n=8)
        f.add(dome)
        # Laterne und kleine Zwiebel
        f.add(K.rect(tx - 0.025 * h, b + 0.19 * h, 0.05 * h, 0.05 * h))
        f.cut(K.rect(tx - 0.012 * h, b + 0.20 * h, 0.024 * h, 0.03 * h))
        f.add(spline([(tx - 0.035 * h, b + 0.24 * h), (tx - 0.03 * h, b + 0.27 * h), (tx, b + 0.30 * h),
                      (tx + 0.03 * h, b + 0.27 * h), (tx + 0.035 * h, b + 0.24 * h)], n=6) + [(tx, b + 0.235 * h)])
        top = b + 0.30 * h
    else:
        b = T_top + 0.015 * h
        f.add([(tx - tw / 2 - 0.01 * h, b), (tx + tw / 2 + 0.01 * h, b), (tx, b + 0.30 * h)])
        top = b + 0.30 * h
    # Kreuz
    cw = max(1.2, 0.012 * h)
    f.add(K.rect(tx - cw / 2, top - 0.01 * h, cw, h - top + 0.01 * h),
          K.rect(tx - 0.025 * h, top + 0.62 * (h - top), 0.05 * h, cw))
    return f


def laterne(h: float) -> Figur:
    """Gusseiserne Straßenlaterne mit verziertem Mast, Bügel und Glaskörper (Scheiben als Durchbrüche)."""
    f = Figur()
    pw = max(1.8, 0.04 * h)
    # Sockel und Mast
    f.add([(-0.08 * h, 0), (0.08 * h, 0), (0.06 * h, 0.04 * h), (0.035 * h, 0.06 * h), (0.03 * h, 0.12 * h),
           (-0.03 * h, 0.12 * h), (-0.035 * h, 0.06 * h), (-0.06 * h, 0.04 * h)])
    f.add(stroke([(0, 0.10 * h), (0, 0.80 * h)], pw * 1.25, pw))
    for y in (0.30 * h, 0.55 * h):
        f.add(K.ellipse(0, y, pw * 0.95, pw * 0.5))
    # Querstrebe mit Schnörkeln
    f.add(K.rect(-0.07 * h, 0.71 * h, 0.14 * h, max(1.2, 0.018 * h)))
    for s in (-1, 1):
        f.add(stroke(spline([(0, 0.66 * h), (s * 0.05 * h, 0.67 * h), (s * 0.07 * h, 0.70 * h), (s * 0.055 * h, 0.725 * h)], n=8),
                     max(1.15, 0.016 * h), max(1.15, 0.016 * h)))
    # Laternenkopf
    y0 = 0.80 * h
    lw, lh = 0.16 * h, 0.15 * h
    body = [(-lw * 0.35, y0), (lw * 0.35, y0), (lw / 2, y0 + lh), (-lw / 2, y0 + lh)]
    f.add(body)
    f.add([(-lw * 0.62, y0 + lh), (lw * 0.62, y0 + lh), (0.0, y0 + lh + 0.07 * h)])
    f.add(K.circle(0, y0 + lh + 0.08 * h, max(1.2, 0.02 * h), 14))
    rib = max(1.15, 0.015 * h)
    gx = lw * 0.5 - rib
    for s in (-1, 1):
        f.cut([(s * rib / 2, y0 + rib), (s * (lw * 0.35 - rib * 0.9), y0 + rib), (s * (lw / 2 - rib), y0 + lh - rib),
               (s * rib / 2, y0 + lh - rib)])
    return f


def schneemann(h: float, seed: int = 1) -> Figur:
    """Schneemann mit Zylinder, Schal mit wehenden Enden, Zweigarmen und Besen."""
    f = Figur()
    r1, r2, r3 = 0.22 * h, 0.16 * h, 0.115 * h
    y1 = r1 * 0.95
    y2 = y1 + r1 * 0.85 + r2 * 0.75
    y3 = y2 + r2 * 0.85 + r3 * 0.8
    f.add(K.ellipse(0, y1, r1 * 1.05, r1, n=60), K.circle(0, y2, r2, 50), K.circle(0, y3, r3, 40))
    # Zylinder
    hy = y3 + r3 * 0.75
    f.add(K.rect(-r3 * 1.15, hy, r3 * 2.3, max(1.2, 0.025 * h)), K.rect(-r3 * 0.75, hy, r3 * 1.5, 0.15 * h))
    f.cut(K.rect(-r3 * 0.75 - 1, hy + 0.035 * h, r3 * 1.5 + 2, max(1.0, 0.012 * h)))
    f.add(K.rect(-r3 * 0.75, hy + 0.035 * h - 0.2, r3 * 1.5, 0.4))
    # Karottennase
    f.add([(r3 * 0.85, y3 + 0.01 * h), (r3 * 0.85, y3 - 0.03 * h), (r3 + 0.10 * h, y3 - 0.025 * h)])
    # Schal
    sy = y2 + r2 * 0.80
    f.add(K.ellipse(0, sy, r2 * 0.95, 0.03 * h))
    f.add(stroke(spline([(-r2 * 0.3, sy), (-r2 * 0.5, sy - 0.08 * h), (-r2 * 0.75, sy - 0.12 * h)], n=6),
                 0.045 * h, 0.035 * h, cap="flach"))
    f.add(stroke(spline([(-r2 * 0.6, sy), (-r2 * 1.2, sy + 0.01 * h), (-r2 * 1.8, sy - 0.03 * h)], n=6),
                 0.04 * h, 0.03 * h, cap="flach"))
    # Arme aus Zweigen
    aw = max(1.2, 0.022 * h)
    for s in (-1, 1):
        a0 = (s * r2 * 0.8, y2 + r2 * 0.2)
        a1 = (s * (r2 + 0.17 * h), y2 + r2 * (0.9 if s > 0 else 0.5))
        f.add(stroke([a0, a1], aw * 1.3, aw))
        f.add(stroke([((a0[0] + a1[0] * 2) / 3, (a0[1] + a1[1] * 2) / 3), (a1[0] - s * 0.02 * h, a1[1] + 0.06 * h)], aw, aw * 0.9))
        f.add(stroke([a1, (a1[0] + s * 0.05 * h, a1[1] + 0.03 * h)], aw, aw * 0.9))
    # Besen in der linken Hand
    bx = -(r2 + 0.15 * h)
    f.add(stroke([(bx, 0.0), (bx + 0.03 * h, y2 + 0.18 * h)], aw * 1.2, aw * 1.2))
    f.add([(bx - 0.06 * h, 0.0), (bx + 0.06 * h, 0.0), (bx + 0.02 * h, 0.13 * h), (bx - 0.015 * h, 0.13 * h)])
    return f


def zaun(x0: float, x1: float, h: float, seed: int = 1) -> Figur:
    """Lattenzaun mit spitzen Latten, zwei Querriegeln und Schneehauben."""
    f = Figur()
    lw = max(1.6, 0.12 * h)
    gap = max(1.6, 0.10 * h)
    x = x0
    while x + lw <= x1:
        f.add([(x, 0), (x + lw, 0), (x + lw, h * 0.86), (x + lw / 2, h), (x, h * 0.86)])
        x += lw + gap
    for y in (0.25 * h, 0.62 * h):
        f.add(K.rect(x0 - lw * 0.3, y, x1 - x0 + lw * 0.6, max(1.2, 0.09 * h)))
    return f


# --------------------------------------------------------------------------------------------------
# Knorriger Spukbaum
# --------------------------------------------------------------------------------------------------

def knorrbaum(h: float, seed: int = 1, lean: float = 0.0, min_w: float = 1.3, dichte: float = 1.0,
              krone: float = 1.0) -> Figur:
    """Kahler, knorriger Baum: geschwungener Stamm mit Wurzeln und Astloch, Äste gabeln sich mehrfach,
    werden zur Spitze hin dünner und enden in feinen, gekrümmten Zweigen. lean > 0 neigt nach rechts.
    h = Höhe, Fuß bei (0, 0)."""
    r = K.rng(seed, "knorr")
    f = Figur()
    trunk_w = 0.075 * h

    def ast(p, ang, L, w, tiefe, curl):
        # geschwungener Ast: zwei gegenläufige Krümmungen = knorrig
        a1 = ang + curl * r.uniform(0.15, 0.35)
        a2 = ang - curl * r.uniform(0.10, 0.40)
        c1 = (p[0] + math.cos(a1) * L * 0.35, p[1] + math.sin(a1) * L * 0.35)
        e = (p[0] + math.cos(ang) * L, p[1] + math.sin(ang) * L)
        c2 = (e[0] - math.cos(a2) * L * 0.35, e[1] - math.sin(a2) * L * 0.35)
        path = K.bez3(p, c1, c2, e, max(6, int(L / 2.5)))
        w_end = max(min_w * 0.9, w * r.uniform(0.62, 0.72))
        end_tip = tiefe <= 0 or w_end <= min_w * 1.05
        f.add(stroke(path, w, (min_w * 0.55 if end_tip else w_end), cap="spitz" if end_tip else "rund"))
        if end_tip:
            return
        # Gabelung: Fortsetzung + 1–2 Seitenäste; kleine Zweige entlang des Asts
        out_ang = math.atan2(path[-1][1] - path[-2][1], path[-1][0] - path[-2][0])
        n = 2 if r.random() < 0.65 else 3
        spread = r.uniform(0.40, 0.70)
        for k in range(n):
            da = (k - (n - 1) / 2) * spread * 2 / max(1, n - 1) + K.jitter(r, 0.12)
            na = out_ang + da
            na += (math.pi / 2 - na) * 0.12                                    # leicht nach oben ziehen
            ast(e, na, L * r.uniform(0.66, 0.82) * (1.0 if abs(da) < 0.3 else 0.85),
                w_end * (1.0 if abs(da) < 0.2 else r.uniform(0.78, 0.92)), tiefe - 1, -curl)
        if w > 2.2 * min_w and dichte > 0:
            for _ in range(int(r.uniform(0, 2.4) * dichte)):
                u = r.uniform(0.35, 0.85)
                q = path[int(u * (len(path) - 1))]
                side = 1 if r.random() < 0.5 else -1
                ast(q, ang + side * r.uniform(0.7, 1.1), L * r.uniform(0.25, 0.4), max(min_w, w * 0.4), 1, curl)

    # Stamm: S-förmig, unten breit mit Wurzelanlauf
    top = (lean * 0.28 * h, 0.42 * h * krone)
    stamm = K.bez3((0, 0), (K.jitter(r, 0.05 * h) - lean * 0.06 * h, 0.15 * h),
                   (top[0] + K.jitter(r, 0.05 * h), top[1] - 0.15 * h), top, 18)
    f.add(stroke(stamm, trunk_w * 1.35, trunk_w, cap="rund"))
    for s, ln in ((-1, 0.16), (1, 0.14), (-1, 0.08), (1, 0.09)):
        root = K.bez((s * trunk_w * 0.15, 0.06 * h), (s * ln * 0.6 * h, 0.03 * h), (s * ln * h, -0.01 * h), 8)
        f.add(stroke(root, trunk_w * 0.55 * (ln / 0.16), min_w * 0.8, cap="spitz"))
    # Astloch
    if trunk_w > 7:
        f.cut(K.ellipse(stamm[7][0] + trunk_w * 0.05, stamm[7][1], trunk_w * 0.18, trunk_w * 0.32, 0.1, 20))
    # Krone
    base_ang = math.pi / 2 - lean * 0.6
    L0 = 0.30 * h * krone
    ast(top, base_ang + 0.55 + K.jitter(r, 0.1), L0 * 0.95, trunk_w * 0.72, 5, 1)
    ast(top, base_ang - 0.50 + K.jitter(r, 0.1), L0, trunk_w * 0.78, 5, -1)
    ast((stamm[12][0], stamm[12][1]), base_ang + (0.95 if lean <= 0 else -0.95), L0 * 0.75, trunk_w * 0.5, 4, 1)
    return f


# --------------------------------------------------------------------------------------------------
# Weihnachtsmann im Rentierschlitten
# --------------------------------------------------------------------------------------------------

def _glied(f: Figur, pts, widths, wmin: float, huf: float = 0.0):
    p = spline(pts, n=8)
    seg = len(p) - 1
    m = len(widths) - 1
    ws = []
    for i in range(len(p)):
        u = i / seg * m
        k = min(int(u), m - 1)
        ws.append(max(wmin, widths[k] + (widths[k + 1] - widths[k]) * (u - k)))
    f.add(stroke(p, 0, widths=ws, cap="rund"))
    if huf:
        a = math.atan2(p[-1][1] - p[-2][1], p[-1][0] - p[-2][0])
        f.add(K.ellipse(p[-1][0] + math.cos(a) * huf * 0.3, p[-1][1] + math.sin(a) * huf * 0.3, huf * 0.75, huf * 0.5, a, 12))


def rentier_flug(wmin: float = 0.05, nase: bool = False) -> Figur:
    """Fliegendes Rentier im Galopp-Sprung (blickt nach rechts), Einheit: Schulterhöhe ≈ 1.
    wmin = Mindestbreite der Beine/Geweihenden in Einheiten (für den Laser)."""
    f = Figur()
    body = [(-0.50, 0.98), (-0.30, 0.97), (-0.05, 0.96), (0.18, 1.00), (0.28, 1.06), (0.40, 1.18),
            (0.50, 1.31), (0.57, 1.38), (0.62, 1.415), (0.67, 1.41), (0.73, 1.37), (0.81, 1.31),
            (0.87, 1.27), (0.895, 1.24), (0.88, 1.205), (0.835, 1.195), (0.80, 1.18), (0.74, 1.19),
            (0.68, 1.21), (0.63, 1.17), (0.59, 1.08), (0.54, 0.96), (0.48, 0.84), (0.40, 0.72),
            (0.28, 0.63), (0.10, 0.60), (-0.14, 0.61), (-0.34, 0.64), (-0.50, 0.73), (-0.57, 0.86)]
    f.add(spline(body, closed=True, n=8))
    # Brustbehang (Rentiere haben eine helle, zottige Halsmähne)
    for k in range(5):
        u = k / 4
        x, y = 0.56 - 0.10 * u, 1.10 - 0.30 * u
        f.add([(x - 0.03, y + 0.04), (x + 0.035, y - 0.03 - 0.015 * (k % 2)), (x - 0.03, y - 0.02)])
    # Sprung: Vorderbeine nach vorn angewinkelt, Hinterbeine gestreckt
    _glied(f, [(0.38, 0.76), (0.52, 0.62), (0.70, 0.60), (0.80, 0.50)], [0.15, 0.08, 0.05, 0.045], wmin, 0.07)
    _glied(f, [(0.28, 0.72), (0.40, 0.55), (0.36, 0.40), (0.47, 0.32)], [0.13, 0.07, 0.045, 0.04], wmin, 0.065)
    _glied(f, [(-0.38, 0.80), (-0.56, 0.62), (-0.78, 0.56), (-1.00, 0.52)], [0.24, 0.10, 0.05, 0.045], wmin, 0.07)
    _glied(f, [(-0.46, 0.78), (-0.64, 0.56), (-0.80, 0.42), (-0.96, 0.34)], [0.20, 0.09, 0.045, 0.04], wmin, 0.065)
    f.add(stroke([(-0.53, 0.95), (-0.62, 0.99)], 0.07, 0.04))                             # Stummelschwanz
    f.add(spline([(0.60, 1.38), (0.52, 1.44), (0.44, 1.49), (0.52, 1.49), (0.62, 1.43)], closed=True, n=6))  # Ohr
    # Rentiergeweih: geschwungene Stange nach hinten oben, Schaufel vorn, Sprossen nach vorn
    for dx, s in ((0.02, 0.85), (0.0, 1.0)):
        def P(x, y):
            return (0.62 + dx + (x - 0.62) * s, 1.42 + (y - 1.42) * s)
        _antler(f, P(0.62, 1.42), [P(0.50, 1.58), P(0.37, 1.71), P(0.31, 1.87), P(0.37, 2.02), P(0.48, 2.10)],
                [(0.05, P(0.80, 1.50), (0.0, 0.04)),
                 (0.28, P(0.55, 1.76), (0.01, -0.03)),
                 (0.55, P(0.17, 1.90), (0.0, 0.03)),
                 (0.80, P(0.52, 2.20), (0.02, -0.03))],
                max(wmin, 0.07 * s), max(wmin, 0.045 * s))
    if nase:
        f.add(K.circle(0.90, 1.23, 0.055, 14))
    return f


def schlitten(wmin: float = 0.05) -> Figur:
    """Geschwungener Schlitten mit Weihnachtsmann und Geschenkesack, fährt nach rechts.
    Einheit wie rentier_flug (Kufenlänge ≈ 2.1)."""
    f = Figur()
    # Kufe mit Schnecke vorn
    kufe = chain([(-1.05, 0.30)], spline([(-1.05, 0.30), (-0.9, 0.18), (-0.4, 0.16), (0.5, 0.16), (0.85, 0.22),
                                          (1.0, 0.38), (0.95, 0.52), (0.84, 0.50), (0.84, 0.40), (0.92, 0.40)], n=8))
    f.add(stroke(kufe, max(wmin, 0.07), max(wmin, 0.06)))
    for x in (-0.65, -0.05, 0.45):
        f.add(stroke([(x, 0.16), (x + 0.06, 0.40)], max(wmin, 0.07), max(wmin, 0.07)))
    # Wanne: hinten hohe Lehne mit Schnecke, vorne geschwungener Bug
    wanne = spline([(-0.95, 0.38), (-1.05, 0.70), (-1.02, 0.95), (-0.88, 1.02), (-0.80, 0.92), (-0.86, 0.84),
                    (-0.70, 0.72), (-0.30, 0.66), (0.10, 0.66), (0.36, 0.70), (0.52, 0.62), (0.50, 0.44),
                    (0.30, 0.36), (-0.60, 0.36)], closed=True, n=8)
    f.add(wanne)
    # Schwanenhals-Schnecke am Bug
    f.add(stroke(spline([(0.30, 0.66), (0.56, 0.70), (0.74, 0.84), (0.80, 0.98), (0.72, 1.06), (0.63, 1.01),
                         (0.66, 0.93), (0.72, 0.95)], n=8), max(wmin, 0.11), max(wmin, 0.06)))
    # Zierranke auf der Wanne (Durchbruch)
    f.cut(stroke(spline([(-0.55, 0.50), (-0.30, 0.58), (-0.05, 0.48), (0.20, 0.56), (0.38, 0.50)], n=8), 0.045, 0.03))
    # Weihnachtsmann: Körper, Kopf mit Mütze und Bart, Arm mit Zügeln
    f.add(spline([(-0.58, 0.66), (-0.64, 0.92), (-0.56, 1.16), (-0.42, 1.24), (-0.28, 1.16), (-0.22, 0.95),
                  (-0.24, 0.66)], closed=True, n=8))
    f.add(K.circle(-0.40, 1.34, 0.11, 24))
    f.add(spline([(-0.30, 1.30), (-0.22, 1.24), (-0.26, 1.14), (-0.36, 1.18)], closed=True, n=6))      # Bart
    f.add(spline([(-0.52, 1.38), (-0.48, 1.48), (-0.60, 1.56), (-0.74, 1.50), (-0.80, 1.40),
                  (-0.66, 1.46), (-0.58, 1.40)], closed=True, n=8))                                   # Mütze
    f.add(K.circle(-0.81, 1.38, 0.05, 12))                                                              # Bommel
    f.add(K.ellipse(-0.42, 1.40, 0.13, 0.04, 0.2, 16))                                                 # Mützenrand
    f.add(stroke([(-0.28, 1.12), (-0.08, 1.02), (0.08, 1.06)], max(wmin, 0.09), max(wmin, 0.07)))       # Arm
    # Geschenkesack hinten
    f.add(spline([(-1.0, 0.70), (-1.10, 0.95), (-1.02, 1.18), (-0.86, 1.26), (-0.74, 1.20), (-0.70, 0.95),
                  (-0.74, 0.70)], closed=True, n=8))
    f.add(K.rect(-0.94, 1.22, 0.12, 0.08))
    f.add(K.rect(-0.66, 0.66, 0.16, 0.30), K.rect(-0.58 - 0.12, 0.96, 0.24, 0.06))                   # Paket
    return f


def gespann(rentiere: int = 3, wmin: float = 0.05) -> Figur:
    """Schlitten mit Rentieren in einer Reihe, durch Zügel verbunden, Einheit Schulterhöhe.
    Fährt nach rechts, leicht ansteigend. Ursprung = Schlittenmitte."""
    f = schlitten(wmin)
    rein = max(wmin * 1.1, 0.045)
    hand = (0.08, 1.06)
    x = 1.05 + 1.0
    prev = None
    for k in range(rentiere):
        y = 0.25 + 0.18 * k
        r = rentier_flug(wmin, nase=(k == rentiere - 1)).place(x, y, 0.92)
        f.merge(r)
        brust = (x + 0.40 * 0.92, y + 0.90 * 0.92)
        # Zügel vom Schlitten zum Brustgeschirr, Geschirr als Ring um die Brust
        f.add(stroke(spline([hand, ((hand[0] + brust[0]) / 2, (hand[1] + brust[1]) / 2 - 0.08), brust], n=8), rein, rein))
        f.add(K.ellipse(x + 0.40 * 0.92, y + 0.88 * 0.92, 0.07, 0.13, 0.5, 14))
        if prev is not None:
            f.add(stroke([prev, (x - 0.50 * 0.92, y + 0.85 * 0.92)], rein, rein))
        prev = brust
        x += 1.75
    return f


# --------------------------------------------------------------------------------------------------
# Einzelmotive für Aufsteck-Verzierungen (Höhe h in mm, Fuß bei y = 0, Mitte x = 0)
# --------------------------------------------------------------------------------------------------

def schneeflocke(h: float, seed: int = 1) -> Figur:
    """Sechsstrahliger Eiskristall: Hauptarme mit gestaffelten Seitenästen, Sechseck-Kern mit Durchbruch."""
    r = K.rng(seed, "flocke")
    R = h / 2
    w = max(1.6, 0.075 * R)
    f = Figur()
    zweige = [(0.30, 0.30, 0.95), (0.52, 0.36, 0.95), (0.72, 0.24, 0.9), (0.86, 0.12, 0.8)]
    zweige = [(u + K.jitter(r, 0.02), L * r.uniform(0.9, 1.1), b) for u, L, b in zweige]
    for k in range(6):
        a = math.pi / 2 + k * math.pi / 3
        ca, sa = math.cos(a), math.sin(a)
        f.add(stroke([(0, 0), (ca * R, sa * R)], w * 1.3, w * 0.8, cap="spitz"))
        for u, L, _ in zweige:
            p = (ca * R * u, sa * R * u)
            for s in (-1, 1):
                b = a + s * math.pi / 3.2
                q = (p[0] + math.cos(b) * R * L, p[1] + math.sin(b) * R * L)
                f.add(stroke([p, q], w, w * 0.75, cap="spitz"))
        # kleine Raute an der Spitze
        tip = (ca * R * 0.96, sa * R * 0.96)
        f.add(K.ellipse(tip[0], tip[1], w * 1.4, w * 0.8, a, 12))
    hexa = [(math.cos(math.pi / 6 + k * math.pi / 3) * R * 0.22, math.sin(math.pi / 6 + k * math.pi / 3) * R * 0.22) for k in range(6)]
    f.add(hexa)
    f.cut([(x * 0.5, y * 0.5) for x, y in hexa])
    return f.place(0, R, 1.0)


def zierstern(h: float, zacken: int = 8) -> Figur:
    """Stern mit tropfenförmigen Durchbrüchen in jedem Strahl und Blüte in der Mitte."""
    R = h / 2
    f = Figur()
    f.add(K.star(0, 0, R, R * 0.48, zacken))
    f.add(K.star(0, 0, R * 0.72, R * 0.40, zacken, rot=math.pi / 2 + math.pi / zacken))
    for k in range(zacken):
        a = math.pi / 2 + 2 * math.pi * k / zacken
        cx, cy = math.cos(a) * R * 0.58, math.sin(a) * R * 0.58
        f.cut(K.ellipse(cx, cy, R * 0.15, R * 0.045, a, 20))
        b = a + math.pi / zacken
        f.cut(K.circle(math.cos(b) * R * 0.42, math.sin(b) * R * 0.42, R * 0.04, 12))
    f.cut(K.star(0, 0, R * 0.22, R * 0.10, zacken))
    f.add(K.circle(0, 0, R * 0.07, 16))
    return f.place(0, R, 1.0)


def eule(h: float) -> Figur:
    """Eule auf einem Ast: Federohren, große Augen (Mondsichel-Durchbrüche mit Pupille), Brustgefieder,
    Flügel mit Federschlitzen. h = Gesamthöhe."""
    f = Figur()
    s = h
    body = spline([(0.0, 0.10), (0.22, 0.14), (0.31, 0.32), (0.30, 0.55), (0.25, 0.72), (0.27, 0.86), (0.20, 0.98),
                   (0.10, 0.88), (0.0, 0.86), (-0.10, 0.88), (-0.20, 0.98), (-0.27, 0.86), (-0.25, 0.72),
                   (-0.30, 0.55), (-0.31, 0.32), (-0.22, 0.14)], closed=True, n=8)
    f.add(body)
    # Augen: großer Kreis, darin bleibt eine Pupille stehen, die oben am Rand hängt (Sichel)
    for sx in (-1, 1):
        cx, cy = sx * 0.12, 0.70
        eye = K.circle(cx, cy, 0.095, 40)
        f.cut(eye)
        f.add(K.circle(cx + sx * 0.012, cy + 0.025, 0.06, 30))
        f.add(K.circle(cx, cy + 0.075, 0.03, 12))
    f.add([(-0.035, 0.66), (0.035, 0.66), (0.0, 0.58)])                                   # Schnabel
    f.add(K.rect(-0.02, 0.64, 0.04, 0.06))
    # Brustgefieder: Reihen kleiner Bögen
    for row, (y, n) in enumerate(((0.46, 3), (0.38, 4), (0.30, 3), (0.22, 2))):
        for k in range(n):
            x = (k - (n - 1) / 2) * 0.085
            f.cut(stroke(K.arc(x, y, 0.032, math.pi * 1.1, math.pi * 1.9, 8), 0.018, 0.018))
    # Flügel: Bogen mit Federschlitzen
    for sx in (-1, 1):
        for k in range(3):
            y0 = 0.50 - k * 0.09
            f.cut(stroke(spline([(sx * 0.21, y0), (sx * 0.25, y0 - 0.06), (sx * 0.24, y0 - 0.13)], n=6), 0.016, 0.01, cap="spitz"))
    # Ast mit Krallen
    f.add(stroke(spline([(-0.55, 0.06), (-0.2, 0.10), (0.15, 0.08), (0.55, 0.12)], n=10), 0.08, 0.05))
    f.add(stroke([(0.38, 0.11), (0.48, 0.20)], 0.04, 0.025))
    for sx in (-1, 1):
        for k in range(3):
            f.add(stroke([(sx * 0.08 + (k - 1) * 0.025, 0.15), (sx * 0.08 + (k - 1) * 0.035, 0.09)], 0.025, 0.02))
    return f.place(0, 0, s)


def engel(h: float) -> Figur:
    """Engel mit ausgebreiteten Flügeln, Heiligenschein und Posaune. h = Gesamthöhe."""
    f = Figur()
    # Kleid: Glocke mit geschwungenem Saum
    f.add(spline([(-0.27, 0.0), (-0.17, 0.22), (-0.10, 0.45), (-0.07, 0.60), (0.07, 0.60), (0.10, 0.45), (0.17, 0.22),
                  (0.27, 0.0), (0.16, 0.035), (0.06, 0.0), (-0.05, 0.035), (-0.16, 0.0)], closed=True, n=6))
    # Kopf, Haar, Heiligenschein (Ring liegt auf dem Kopf auf)
    f.add(K.circle(0.0, 0.69, 0.075, 30))
    f.add(spline([(-0.08, 0.66), (-0.09, 0.74), (-0.03, 0.78), (0.05, 0.77), (0.09, 0.71), (0.06, 0.64)], closed=True, n=6))
    halo = K.ellipse(0.0, 0.80, 0.11, 0.035, 0.0, 40)
    f.add(halo)
    f.cut(K.ellipse(0.0, 0.80, 0.075, 0.014, 0.0, 30))
    f.add(K.rect(-0.012, 0.74, 0.024, 0.06))
    # Flügel: gefächerte Schwungfedern, jede mit Federkiel als Schlitz
    for sx in (-1, 1):
        sh = (sx * 0.09, 0.56)
        f.add(K.ellipse(sx * 0.12, 0.54, 0.09, 0.07, 0.0, 24))
        for k in range(5):
            ang = math.radians(8 + k * 12)
            L = 0.44 - 0.035 * k
            d = (sx * math.cos(ang), math.sin(ang))
            c = (sh[0] + d[0] * L * 0.55, sh[1] + d[1] * L * 0.55 - 0.03)
            rot = math.atan2(d[1], d[0])
            f.add(K.ellipse(c[0], c[1], L / 2, 0.058 - 0.005 * k, rot, 28))
            p0 = (sh[0] + d[0] * L * 0.40, sh[1] + d[1] * L * 0.40 - 0.03)
            p1 = (sh[0] + d[0] * L * 0.88, sh[1] + d[1] * L * 0.88 - 0.03)
            f.cut(stroke([p0, p1], 0.018, 0.008, cap="spitz"))
    # Posaune
    f.add(stroke([(0.04, 0.62), (0.26, 0.74)], 0.025, 0.03))
    f.add([(0.24, 0.72), (0.32, 0.82), (0.36, 0.74)])
    # Ärmel mit Händen
    f.add(stroke(spline([(-0.06, 0.55), (0.02, 0.58), (0.08, 0.64)], n=6), 0.06, 0.05))
    # Gürtel-Ornament
    f.cut(K.ellipse(0.0, 0.30, 0.035, 0.07, 0.0, 20))
    f.cut(K.circle(0.0, 0.16, 0.025, 14))
    return f.place(0, 0, h)


# --------------------------------------------------------------------------------------------------
# Weihnachtsmann, Lastwagen mit Baum, Nussknacker (für Ebenenmotiv und Aufsteckdeko)
# --------------------------------------------------------------------------------------------------

def _schlitz(f: Figur, path, h: float, k: float = 1.0):
    """Feine Schnittlinie (Durchbruch) entlang path in Einheitskoordinaten; mindestens 0,9 mm breit."""
    f.cut(stroke(path, max(0.011 * k, 0.9 / h), max(0.011 * k, 0.9 / h)))


def weihnachtsmann(h: float) -> Figur:
    """Winkender Weihnachtsmann mit Mütze, Rauschebart, Pelzbesatz, Gürtel und Geschenkesack. h = Gesamthöhe."""
    f = Figur()
    # Stiefel und Beine
    for s in (-1, 1):
        f.add(spline([(s * 0.03, 0.0), (s * 0.20, 0.0), (s * 0.21, 0.04), (s * 0.15, 0.07), (s * 0.13, 0.13),
                      (s * 0.04, 0.13)], closed=True, n=6))
        f.add(K.rect(min(s * 0.04, s * 0.13), 0.10, 0.09, 0.14))
    # Mantel: A-Linie mit Pelzsaum
    mantel = spline([(-0.27, 0.22), (-0.24, 0.38), (-0.19, 0.52), (-0.16, 0.60), (0.0, 0.63), (0.16, 0.60),
                     (0.19, 0.52), (0.24, 0.38), (0.27, 0.22), (0.14, 0.20), (0.0, 0.21), (-0.14, 0.20)],
                    closed=True, n=8)
    f.add(mantel)
    f.add(stroke(spline([(-0.29, 0.215), (-0.15, 0.19), (0.0, 0.20), (0.15, 0.19), (0.29, 0.215)], n=8),
                 0.07, 0.07))
    _schlitz(f, spline([(-0.21, 0.25), (-0.14, 0.237), (0.0, 0.245), (0.14, 0.237), (0.21, 0.25)], n=8), h)
    # Pelzleiste vorn
    for x in (-0.035, 0.035):
        _schlitz(f, [(x, 0.28), (x, 0.34)], h)
        _schlitz(f, [(x, 0.46), (x, 0.52)], h)
    # Gürtel mit Schnalle
    _schlitz(f, spline([(-0.17, 0.362), (0.0, 0.37), (0.17, 0.362)], n=6), h)
    _schlitz(f, spline([(-0.16, 0.432), (0.0, 0.44), (0.16, 0.432)], n=6), h)
    for x in (-0.05, 0.05):                              # Schnalle
        _schlitz(f, [(x, 0.39), (x, 0.405)], h)
    # Kopf, Bart, Schnurrbart
    f.add(K.ellipse(0.0, 0.70, 0.085, 0.09, 0.0, 30))
    bart = spline([(-0.10, 0.70), (-0.14, 0.62), (-0.12, 0.54), (-0.07, 0.48), (0.0, 0.45), (0.07, 0.48),
                   (0.12, 0.54), (0.14, 0.62), (0.10, 0.70), (0.05, 0.665), (0.0, 0.67), (-0.05, 0.665)],
                  closed=True, n=8)
    f.add(bart)
    for x0, x1, y0 in ((-0.07, -0.03, 0.62), (0.03, 0.07, 0.62), (-0.09, -0.05, 0.56), (0.05, 0.09, 0.56),
                       (-0.03, 0.02, 0.52)):
        _schlitz(f, spline([(x0, y0 + 0.02), ((x0 + x1) / 2, y0 - 0.01), (x1, y0 + 0.02)], n=5), h, 0.9)
    _schlitz(f, spline([(-0.07, 0.675), (-0.035, 0.655), (0.0, 0.668), (0.035, 0.655), (0.07, 0.675)], n=6), h)
    # Augen und Nase
    for s in (-1, 1):
        f.cut(K.ellipse(s * 0.035, 0.725, max(0.011, 0.8 / h), max(0.014, 0.9 / h), 0.0, 12))
    # Mütze: fällt nach links, Bommel, Pelzrand
    f.add([(-0.11, 0.765), (0.11, 0.765), (0.07, 0.86), (0.0, 0.93), (-0.09, 0.955), (-0.18, 0.92), (-0.24, 0.85),
           (-0.19, 0.875), (-0.12, 0.885), (-0.07, 0.86)])
    f.add(K.circle(-0.25, 0.83, 0.045, 20))
    f.add(stroke(spline([(-0.12, 0.765), (0.0, 0.79), (0.12, 0.765)], n=6), 0.055, 0.055))
    # Rechter Arm winkt, Fäustling mit Daumen
    f.add(stroke(spline([(0.15, 0.57), (0.24, 0.62), (0.30, 0.72), (0.31, 0.80)], n=8), 0.10, 0.08))
    f.add(stroke([(0.27, 0.775), (0.35, 0.775)], 0.035, 0.035))
    f.add(K.ellipse(0.31, 0.86, 0.045, 0.06, 0.2, 20))
    f.add(K.ellipse(0.355, 0.85, 0.018, 0.035, -0.5, 12))
    # Linker Arm hält den Sack über der Schulter
    f.add(stroke(spline([(-0.15, 0.57), (-0.21, 0.55), (-0.23, 0.62), (-0.20, 0.66)], n=6), 0.10, 0.08))
    f.add(spline([(-0.19, 0.64), (-0.30, 0.70), (-0.40, 0.66), (-0.44, 0.54), (-0.42, 0.42), (-0.34, 0.36),
                  (-0.26, 0.40), (-0.22, 0.50), (-0.20, 0.58)], closed=True, n=8))
    _schlitz(f, spline([(-0.40, 0.60), (-0.36, 0.52), (-0.37, 0.44)], n=5), h)
    _schlitz(f, spline([(-0.30, 0.64), (-0.29, 0.56), (-0.31, 0.46)], n=5), h, 0.9)
    # Geschenk schaut aus dem Sack
    f.add(K.rect(-0.385, 0.64, 0.12, 0.09))
    _schlitz(f, [(-0.325, 0.66), (-0.325, 0.72)], h, 0.8)
    f.add(K.ellipse(-0.35, 0.735, 0.03, 0.02, 0.5, 12), K.ellipse(-0.30, 0.735, 0.03, 0.02, -0.5, 12))
    return f.place(0, 0, h)


def lkw_baum(h: float, seed: int = 1) -> Figur:
    """Alter Pick-up mit Tannenbaum auf der Ladefläche und Kranz am Kühler, fährt nach rechts.
    h = Höhe bis zur Baumspitze (Länge ≈ 1,9·h)."""
    f = Figur()
    r = 0.15                                              # Radradius
    xr, xf = -0.55, 0.52
    # Karosserie: Ladefläche, Kabine, Motorhaube mit runden Kotflügeln
    body = [(-0.86, 0.17), (-0.86, 0.38), (-0.14, 0.38), (-0.12, 0.62), (-0.08, 0.66), (0.20, 0.66), (0.26, 0.62),
            (0.36, 0.44), (0.66, 0.42), (0.80, 0.38), (0.84, 0.30), (0.85, 0.17)]
    f.add(body)
    for xc in (xr, xf):                                   # Kotflügel
        f.add(chain(K.arc(xc, 0.15, r + 0.06, 0.0, math.pi, 16)))
        f.add(stroke(K.arc(xc, 0.15, r + 0.07, -0.05, math.pi + 0.05, 16), 0.05, 0.05))
    f.add(stroke([(-0.88, 0.17), (0.87, 0.17)], 0.045, 0.045))   # Stoßstange/Trittbrett
    # Räder mit Felge; ein Spalt trennt sie oben vom Kotflügel, seitlich bleiben sie an der Karosserie
    for xc in (xr, xf):
        f.cut(K.circle(xc, 0.15, r + 0.03, 32))
        f.add(K.circle(xc, 0.15, r, 36))
        f.add(K.rect(xc - r - 0.035, 0.12, 2 * r + 0.07, 0.06))
        f.cut(K.circle(xc, 0.15, r * 0.62, 28))
        f.add(K.circle(xc, 0.15, r * 0.30, 18))
        for k in range(6):
            a = k * math.pi / 3
            f.add(stroke([(xc + 0.28 * r * math.cos(a), 0.15 + 0.28 * r * math.sin(a)),
                          (xc + 0.66 * r * math.cos(a), 0.15 + 0.66 * r * math.sin(a))], 0.022, 0.022))
    # Fenster der Kabine, Türlinie, Griff
    f.cut([(-0.08, 0.46), (-0.08, 0.61), (0.18, 0.61), (0.24, 0.52), (0.24, 0.46)])
    f.add(stroke([(0.07, 0.46), (0.07, 0.61)], 0.03, 0.03))
    _schlitz(f, [(-0.10, 0.22), (-0.10, 0.44)], h)
    _schlitz(f, [(0.27, 0.22), (0.27, 0.44)], h)
    _schlitz(f, [(-0.02, 0.41), (0.06, 0.41)], h, 1.2)
    # Kühlergrill mit Streben, Scheinwerfer, Kranz
    for k in range(4):
        _schlitz(f, [(0.70 + 0.03 * k, 0.24), (0.70 + 0.03 * k, 0.36)], h, 0.9)
    f.add(K.circle(0.83, 0.40, 0.04, 16))
    f.cut(K.circle(0.83, 0.40, 0.022, 12))
    # Ladefläche: Bordwand-Linien
    _schlitz(f, [(-0.84, 0.30), (-0.16, 0.30)], h)
    # Kranz an der Tür
    f.cut(K.circle(0.12, 0.31, 0.068, 24))
    f.add(K.circle(0.12, 0.31, 0.056, 24))
    f.cut(K.circle(0.12, 0.31, 0.03, 18))
    f.add(stroke(spline([(0.12, 0.26), (0.09, 0.22), (0.12, 0.25), (0.15, 0.22), (0.12, 0.26)], n=5), 0.02, 0.02))
    sc = h / 0.70                                        # Einheit → mm (Kabinendach ≈ 0,66 über dem Boden)
    f = f.place(0, 0, sc)
    # Tannenbaum auf der Ladefläche, liegt schräg, Spitze ragt über die Kabine (in mm gezeichnet)
    tree = fichte(0.85 * sc, seed, breite=0.50, schnee=True).place(-0.22 * sc, 0.47 * sc, 1.0, ang=1.40)
    f.ops = tree.ops + f.ops
    f.add(stroke([(-0.62 * sc, 0.37 * sc), (-0.55 * sc, 0.62 * sc), (-0.44 * sc, 0.37 * sc)],
                 max(1.2, 0.02 * sc), max(1.2, 0.02 * sc)))
    return f


def nussknacker(h: float) -> Figur:
    """Erzgebirgischer Nussknacker: hoher Tschako mit Federbusch, Bart, Uniform mit Tressen, Säbel. h = Höhe."""
    f = Figur()
    # Sockel und Stiefel
    f.add(K.rect(-0.17, 0.0, 0.34, 0.06))
    for s in (-1, 1):
        f.add(K.rect(s * 0.02 if s > 0 else -0.11, 0.04, 0.09, 0.20))
        f.add(spline([(s * 0.015, 0.04), (s * 0.13, 0.04), (s * 0.13, 0.10), (s * 0.015, 0.10)], closed=True, n=4))
    # Rock und Jacke mit Tressen und Knöpfen
    f.add([(-0.15, 0.22), (0.15, 0.22), (0.13, 0.52), (-0.13, 0.52)])
    _schlitz(f, [(-0.105, 0.30), (0.105, 0.30)], h)
    for k in range(4):
        y = 0.34 + 0.04 * k
        _schlitz(f, [(-0.07, y), (0.07, y)], h, 0.8)
    _schlitz(f, [(-0.11, 0.50), (-0.11, 0.33)], h, 0.8)
    _schlitz(f, [(0.11, 0.50), (0.11, 0.33)], h, 0.8)
    # Epauletten und Arme
    for s in (-1, 1):
        f.add(K.ellipse(s * 0.15, 0.51, 0.06, 0.025, 0.0, 18))
        f.add(stroke([(s * 0.155, 0.50), (s * 0.19, 0.32)], 0.08, 0.07))
        f.add(K.circle(s * 0.19, 0.30, 0.038, 14))
        for k in range(2):
            _schlitz(f, [(s * (0.16 + 0.03 * k), 0.53), (s * (0.165 + 0.03 * k), 0.515)], h, 0.7)
    # Säbel
    f.add(stroke([(0.21, 0.30), (0.24, 0.08)], 0.035, 0.025))
    f.add(stroke([(0.16, 0.31), (0.25, 0.31)], 0.03, 0.03))
    # Kopf mit großem Mund, Bart, Nase
    f.add(K.rect(-0.10, 0.52, 0.20, 0.17))
    f.add(spline([(-0.11, 0.62), (-0.13, 0.55), (-0.08, 0.50), (0.0, 0.48), (0.08, 0.50), (0.13, 0.55),
                  (0.11, 0.62), (0.0, 0.59)], closed=True, n=6))
    _schlitz(f, [(-0.07, 0.585), (0.07, 0.585)], h, 1.3)
    for x in (-0.07, -0.035, 0.0, 0.035, 0.07):
        _schlitz(f, [(x, 0.55), (x * 1.2, 0.51)], h, 0.7)
    f.add(K.ellipse(0.0, 0.625, 0.025, 0.03, 0.0, 12))
    for s in (-1, 1):
        f.cut(K.ellipse(s * 0.045, 0.66, max(0.011, 0.8 / h), max(0.013, 0.9 / h), 0.0, 12))
    # Tschako mit Schild, Kokarde, Federbusch
    f.add(K.rect(-0.12, 0.69, 0.24, 0.03))
    f.add([(-0.10, 0.71), (0.10, 0.71), (0.12, 0.90), (-0.12, 0.90)])
    f.add(K.rect(-0.13, 0.89, 0.26, 0.025))
    f.add(K.star(0.0, 0.80, 0.05, 0.022, 6))
    f.cut(K.circle(0.0, 0.80, max(0.012, 0.9 / h), 10))
    f.add(stroke(spline([(0.0, 0.88), (0.02, 0.96), (-0.01, 1.0)], n=6), 0.065, 0.035))
    return f.place(0, 0, h)
