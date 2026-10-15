"""
Spukschloss – großes Halloween-Fensterbild mit Scherenschnitt-Szene.

Ein gotischer Spitzbogen mit Krabben (Zierknospen) und Kreuzblume. Darin eine Szene als
Scherenschnitt: Spukhaus, Friedhof oder Hexenhaus mit knorrigem Baum auf welligem Boden. Oben
der Vollmond mit Kratern, vor dem Fledermäuse und/oder eine Hexe auf dem Besen fliegen (als
Durchbruch – mit LED dahinter leuchten sie). Links ein Spinnennetz mit filigranen Fäden, oben
hängt eine Spinne an ihrem Faden. Fenster und Kürbisgesichter sind ausgeschnitten.
Der Bogen steckt mit zwei Zapfen in einer Bodenplatte.
"""
import importlib.util
import math
import os
import random
import sys

from steckwerk import Assembly, Part, arc_points, bezier_q, circle, dist, min_distance, oriented, point_in_polygon, rect, slot_feature
from models import _deko as dk
from models._font import CASES, STYLES, fit_text, unsupported
from models._stand import tab_feature_at
from pakete import bibliothek, flag, integer, num, sel, txt


def _lib():
    return bibliothek("verzierungen").G


g = _lib()
DEBUG = False

SCENES = [("spukhaus", "Spukhaus"), ("friedhof", "Friedhof"), ("hexenhaus", "Hexenhaus")]
SKIES = [("fledermaeuse", "Fledermäuse vor dem Mond"), ("hexe", "Hexe auf dem Besen"),
         ("beides", "Hexe und Fledermäuse"), ("nichts", "nur der Mond")]
FRAMES = [("keine", "keine")] + dk.LINE_STYLES

UEBERSETZUNG = {"en": g.EN}

INFO = dict(
    label="Spukschloss-Fensterbild",
    group="Halloween",
    desc="Gotischer Bogen mit Scherenschnitt-Szene, Mond, Fledermäusen, Spinnennetz und leuchtenden Fenstern.",
    params=[
        num("width", "Breite", 260, 160, 600, help="Höhe ≈ 1,3 × Breite"),
        sel("szene", "Szene", SCENES, "spukhaus"),
        sel("himmel", "Vor dem Mond", SKIES, "beides"),
        integer("fledermaeuse", "Fledermäuse", 4, 1, 7, when={"himmel": ["fledermaeuse", "beides"]}),
        integer("kuerbisse", "Leuchtende Kürbisse", 2, 0, 3),
        flag("spinne", "Spinnennetz und Spinne", True),
        integer("variante", "Variante (Baum, Fledermäuse)", 1, 1, 99, help="andere Zahl = anders gewachsener Baum"),
        sel("rahmen_deko", "Zierlinie auf dem Bogen", FRAMES, "doppelt", section="Gestaltung"),
        txt("text", "Text auf dem Sockel", "Happy Halloween", "| = neue Zeile", section="Schrift und Beschriftung"),
        sel("schrift", "Schrift", [(s, s) for s in STYLES], "kursiv", section="Schrift und Beschriftung"),
        sel("schreibweise", "Schreibweise", dk.FONT_CASES, "gross", section="Schrift und Beschriftung"),
    ],
)


# --------------------------------------------------------------------------------------------------
# Szenen-Elemente (lokal: Mitte x = 0, Boden y = 0, offene Linie von links unten nach rechts unten)
# --------------------------------------------------------------------------------------------------

def _from_closed(poly, cut_y=0.0):
    """Teil einer geschlossenen Kontur oberhalb von y = cut_y als Linie von links nach rechts."""
    P = oriented(poly, True)
    n = len(P)
    hits = []
    for i in range(n):
        a, b = P[i], P[(i + 1) % n]
        if (a[1] - cut_y) * (b[1] - cut_y) < 0:
            t = (cut_y - a[1]) / (b[1] - a[1])
            hits.append((i, (a[0] + t * (b[0] - a[0]), cut_y), b[1] > a[1]))
    up = [h for h in hits if h[2]][0]        # aufsteigend (rechts, CCW)
    down = [h for h in hits if not h[2]][0]
    out = [up[1]]
    k = up[0] + 1
    while True:
        out.append(P[k % n])
        if k % n == down[0]:
            break
        k += 1
    out.append(down[1])
    return list(reversed(out))               # links → rechts


def el_pumpkin(w, face, web):
    h = 0.78 * w
    body = g.pumpkin(0.0, -0.10 * h, w, h)
    line = _from_closed(body, 0.0)
    holes = g.pumpkin_face(face, 0.0, 0.36 * h, 0.80 * w, 0.62 * h)
    return dict(line=line, holes=holes, eng=[("ribs", (0.0, 0.40 * h, w, h))])


def el_tombstone(kind, w, h):
    t = g.tombstone(kind, w, h)
    line = [p for p in t]
    # Kontur beginnt links unten? tombstone liefert (−w/2,0),(w/2,0),… → als Linie links→rechts
    P = oriented(t, True)
    i0 = min(range(len(P)), key=lambda i: (P[i][1], P[i][0]))       # links unten
    rot = P[i0:] + P[:i0]
    # rot läuft CCW: links unten → rechts unten → oben → links … ; Linie = rückwärts ab rechts unten
    i1 = max(range(len(rot)), key=lambda i: (rot[i][0] if rot[i][1] < 1e-6 else -1e9))
    upper = rot[i1:] + [rot[0]]
    line = list(reversed(upper))
    line = [line[0]] + line[1:]
    line = list(reversed(line)) if line[0][0] > line[-1][0] else line
    return dict(line=line, holes=[], eng=[("stone", kind, w, h)])


def el_mansion(w, h, seed, web):
    m = g.mansion(w, h, seed, web)
    line = m["poly"]
    return dict(line=line, holes=m["holes"], eng=[("walls", m["walls"]), ("roofs", m["roofs"])])


def el_crypt(w, h):
    """Gruft: Tempelfront mit Giebel, Kreuz, Spitzbogentür und Säulenfugen."""
    ped = 0.30 * h
    body = h - ped - 0.12 * h
    cw = 0.06 * w
    line = [(-w / 2, 0.0), (-w / 2, body), (-w / 2 - 0.05 * w, body), (-w / 2 - 0.05 * w, body + 0.05 * h),
            (-cw / 2, body + ped), (-cw / 2, h - 0.08 * h), (-cw * 1.8, h - 0.08 * h), (-cw * 1.8, h - 0.08 * h + cw),
            (-cw / 2, h - 0.08 * h + cw), (-cw / 2, h + 0.06 * h), (cw / 2, h + 0.06 * h), (cw / 2, h - 0.08 * h + cw),
            (cw * 1.8, h - 0.08 * h + cw), (cw * 1.8, h - 0.08 * h), (cw / 2, h - 0.08 * h), (cw / 2, body + ped),
            (w / 2 + 0.05 * w, body + 0.05 * h), (w / 2 + 0.05 * w, body), (w / 2, body), (w / 2, 0.0)]
    holes = [g._window_holes("spitz", 0.0, 0.06 * h, 0.30 * w, 0.52 * h)]
    for s in (-1, 1):
        holes.append(rect(s * 0.34 * w - 0.03 * w, 0.08 * h, 0.06 * w, body - 0.18 * h))
    holes.append(g._window_holes("rund", 0.0, body + 0.06 * h, 0.12 * w, 0.12 * w))
    return dict(line=line, holes=holes, eng=[("walls", [(-w / 2, 0.0, w / 2, body)])])


def el_cottage(w, h, web):
    """Schiefes Hexenhaus: durchhängendes Dach, krummer Schornstein, schiefe Fenster."""
    wall = 0.45 * h
    lean = 0.05 * w
    line = [(-w / 2, 0.0), (-w / 2 + lean * 0.3, wall), (-w / 2 - 0.08 * w, wall - 0.04 * h)]
    ridge = (0.05 * w, h * 0.92)
    line += g.bez((-w / 2 - 0.08 * w, wall - 0.04 * h), (-0.25 * w, 0.62 * h), ridge, 10)[1:]
    # Schornstein, schief, rechts vom First
    def roof_y(x):
        t = (x - ridge[0]) / (w / 2 + 0.08 * w - ridge[0])
        return ridge[1] + (wall - 0.02 * h - ridge[1]) * t - 0.05 * h * math.sin(math.pi * t)
    c0 = 0.20 * w
    line += [(c0, roof_y(c0)), (c0 + 0.04 * w, roof_y(c0) + 0.26 * h), (c0 + 0.02 * w, roof_y(c0) + 0.26 * h),
             (c0 + 0.03 * w, roof_y(c0) + 0.31 * h), (c0 + 0.17 * w, roof_y(c0) + 0.31 * h),
             (c0 + 0.16 * w, roof_y(c0) + 0.26 * h), (c0 + 0.13 * w, roof_y(c0) + 0.26 * h),
             (c0 + 0.11 * w, roof_y(c0 + 0.11 * w))]
    xs = [c0 + 0.11 * w + (w / 2 + 0.08 * w - c0 - 0.11 * w) * k / 6 for k in range(1, 7)]
    line += [(x, roof_y(x)) for x in xs]
    line += [(w / 2 - lean * 0.2, wall - 0.02 * h), (w / 2, 0.0)]
    holes = []
    # Tür (Rundbogen, leicht schief) und zwei Fenster mit Kreuzsprossen (4 Scheiben)
    holes.append(g._window_holes("spitz", -0.12 * w, 0.0 + max(web, 1.5) + 1.0, 0.20 * w, 0.34 * h))
    for (cx, cy, ww, hh) in ((0.24 * w, 0.18 * h, 0.20 * w, 0.17 * h), (0.0, 0.66 * h, 0.13 * w, 0.13 * w)):
        m = max(web * 1.2, 1.4)
        if cy > 0.5 * h:
            holes.append(g._window_holes("rund", cx, cy, ww, ww))
            continue
        pw, ph = (ww - m) / 2, (hh - m) / 2
        for i in range(2):
            for j in range(2):
                holes.append(rect(cx - ww / 2 + i * (pw + m), cy + j * (ph + m), pw, ph))
    return dict(line=line, holes=holes, eng=[("walls_holz", [(-w / 2, 0.0, w / 2, wall)]),
                                             ("roofs", [(-w / 2, wall - 0.04 * h, w / 2, h)])])


def el_cauldron(w, h, web):
    """Hexenkessel auf zwei Beinen, darunter lodert das Feuer (Flammen stehen im Durchbruch),
    oben brodeln Blasen."""
    rx, ry = 0.46 * w, 0.28 * h
    cy = 0.52 * h
    pot_y = cy - ry
    lw = max(0.07 * w, web * 2.2)
    fx = 0.36 * w                                      # Fußmitte
    E = lambda a: (rx * math.cos(math.radians(a)), cy + ry * math.sin(math.radians(a)))
    rim = cy + ry * math.sin(math.radians(155))
    line = [(-fx - lw / 2, 0.0), E(205)]
    line += g._ellipse_pts(0.0, cy, rx, ry, math.radians(205), math.radians(155), 8)[1:]
    line += [(-rx * 1.06, rim), (-rx * 1.06, rim + 0.07 * h)]
    top = rim + 0.07 * h
    for bx, br in ((-0.26 * w, 0.075 * w), (-0.04 * w, 0.10 * w), (0.20 * w, 0.065 * w)):
        line += [(bx - br, top)] + g.arc(bx, top, br, math.pi, 0.0, 10)[1:-1] + [(bx + br, top)]
    line += [(rx * 1.06, top), (rx * 1.06, rim)]
    line += g._ellipse_pts(0.0, cy, rx, ry, math.radians(25), math.radians(-25), 8)
    line += [(fx + lw / 2, 0.0)]
    line = g.dedupe(line, 0.15, closed=False)
    # Durchbruch zwischen den Beinen mit Flammen
    m = max(web * 1.2, 1.2)
    yb = max(2.2 * web, 0.05 * h)
    inner_l = (-fx + lw / 2, yb)
    inner_r = (fx - lw / 2, yb)
    under = g._ellipse_pts(0.0, cy, rx - m, ry - m, math.radians(232), math.radians(308), 10)
    hole = [inner_l] + under + [inner_r]
    # Flammen von rechts nach links (Unterkante)
    fh_max0 = (under[len(under) // 2][1] - yb) - 1.8 * m
    flames = 3 if fh_max0 >= 3.0 else 0              # zu flach für Flammen: schlichter Durchbruch
    x0, x1 = inner_r[0] - m, inner_l[0] + m
    fh_max = (under[len(under) // 2][1] - yb) - 1.8 * m
    for k in range(flames):
        a_ = x0 + (x1 - x0) * k / flames
        b_ = x0 + (x1 - x0) * (k + 1) / flames
        mid = (a_ + b_) / 2
        fh = fh_max * (0.95 if k == 1 else 0.7)
        hole += [(a_, yb)] if k == 0 else []
        hole += g.bez((a_ - 0.1 * (a_ - b_), yb), (a_, yb + fh * 0.5), (mid + 0.15 * (b_ - a_), yb + fh), 5)
        hole += g.bez((mid + 0.15 * (b_ - a_), yb + fh), (mid, yb + fh * 0.45), (b_ + 0.1 * (a_ - b_), yb), 5)
    hole = g.dedupe(hole, 0.12)
    return dict(line=line, holes=[hole], eng=[("kessel", (0.0, cy, rx, ry))])


def el_fence(w, h, web):
    bar = max(0.045 * w, web * 1.4)
    gap = max(2.0 * bar, 3.2)
    line = g.fence(-w / 2, w / 2, h, bar, gap)
    holes = g.fence_holes(-w / 2, w / 2, h, bar, gap)
    return dict(line=line, holes=holes, eng=[])


def el_cat(h):
    c = g.cat_unit()
    poly = [(x * h, (y + 0.5) * h) for x, y in c]
    return dict(line=_from_closed(poly, 0.0 + 0.004 * h), holes=[], eng=[])


def el_tree(Ri, h, seed, web, box, lean=0.0):
    t = g.good_tree(0.0, h, seed, max(web, 1.2), box, lean=lean, min_w=max(1.3, web * 0.95), depth=7)
    return dict(line=_from_closed(t, 0.0 + 0.001), holes=[], eng=[("bark", h)])


# --------------------------------------------------------------------------------------------------
# Bau
# --------------------------------------------------------------------------------------------------

def _arch(W, ys, R, bump=0.0, step=10.0, tol=0.1):
    """Spitzbogen: rechte Seite hoch, rechter Bogen zur Spitze, linker Bogen runter (CCW-Anteil)."""
    cxr = W / 2 - R                               # Mittelpunkt des rechten Bogens (links der Mitte)
    a_end = math.acos(-cxr / R)                   # Winkel bei x = 0
    n = max(16, int(R * a_end / 2.0))
    right = []
    for i in range(n + 1):
        a = a_end * i / n
        s = R * a
        r = R + (bump * abs(math.sin(math.pi * s / step)) ** 0.7 if bump else 0.0)
        right.append((cxr + r * math.cos(a), ys + r * math.sin(a)))
    apex_y = ys + R * math.sin(a_end)
    right[-1] = (0.0, apex_y)
    left = [(-x, y) for x, y in reversed(right)]
    return right, left[1:], apex_y


def build(cfg, name="spukschloss", width=260.0, szene="spukhaus", himmel="beides", fledermaeuse=4,
          kuerbisse=2, spinne=True, variante=1, rahmen_deko="doppelt", text="Happy Halloween",
          schrift="kursiv", schreibweise="gross"):
    T = cfg.T
    W = cfg.s(width)
    if not 160 <= W <= 600:
        raise ValueError("Spukschloss: Breite muss zwischen 160 und 600 mm liegen")
    dk.check_choice("Szene", szene, SCENES)
    dk.check_choice("Himmel", himmel, SKIES)
    dk.check_choice("Zierlinie", rahmen_deko, FRAMES)
    if schrift not in STYLES or schreibweise not in CASES:
        raise ValueError("Schrift oder Schreibweise unbekannt")
    bad = unsupported(text or "")
    if bad:
        raise ValueError(f"Zeichen {''.join(bad)!r} gibt es in der Gravurschrift nicht")
    fledermaeuse = max(0, min(7, int(fledermaeuse)))
    kuerbisse = max(0, min(3, int(kuerbisse)))
    seed = int(variante) * 7919 + cfg.seed
    rng = random.Random(seed)
    web = max(cfg.min_web * 1.6, 1.6, 0.006 * W)       # Mindeststeg für filigrane Teile
    tol = cfg.arc_tolerance

    bw = max(0.055 * W, 3.5 * T, 9.0)                   # Rahmenbreite
    hb = max(0.085 * W, 2.5 * T + 10.0)                 # Sockel
    R = 0.74 * W
    ys = 0.44 * W
    tw = max(0.1 * W, 4 * T)                            # Zapfen
    xt = W / 2 - 0.17 * W

    # ---------------------------------------------------------------- Außenkontur
    bump = 0.018 * W
    o_right, o_left, apex = _arch(W, ys, R, bump=bump, step=0.075 * W)
    # Kreuzblume an der Spitze
    fw, fh = 0.035 * W, 0.075 * W
    k0 = max(i for i, p in enumerate(o_right) if p[0] > fw * 0.6)
    yb = o_right[k0][1]
    fin = [(fw * 0.6, yb), (fw * 0.35, apex + 0.25 * fh), (fw * 1.1, apex + 0.45 * fh), (fw * 0.9, apex + 0.6 * fh),
           (fw * 0.3, apex + 0.55 * fh), (fw * 0.5, apex + 0.78 * fh), (0.0, apex + fh)]
    fin_l = [(-x, y) for x, y in reversed(fin[:-1])]
    outer = [(-W / 2, 0.0)]
    for x0 in (-xt - tw / 2, xt - tw / 2):
        outer += [(x0, 0.0), (x0, -T), (x0 + tw, -T), (x0 + tw, 0.0)]
    outer += [(W / 2, 0.0)]
    outer += o_right[:k0 + 1] + fin + fin_l + o_left[len(o_left) - k0 - 1:] if False else []
    outer += o_right[:k0 + 1] + fin + fin_l + [(-x, y) for x, y in reversed(o_right[:k0 + 1])]
    outer = g.dedupe(outer, 0.12)
    arch = Part(f"{name}_bogen", oriented(outer, True),
                features=[tab_feature_at("fuss_l", -xt - tw / 2, 0.0, tw, T),
                          tab_feature_at("fuss_r", xt - tw / 2, 0.0, tw, T)])

    # ---------------------------------------------------------------- Himmel (innen)
    Wi = W - 2 * bw
    i_right, i_left, i_apex = _arch(Wi, ys, R - bw)
    amp = 0.022 * W
    ph = rng.uniform(0, 6.28)

    def ground(x):
        return hb + amp * (0.55 + 0.45 * math.sin(2.3 * x / Wi * math.pi + ph))

    def inside_sky(p, m):
        """liegt p mindestens m innerhalb des inneren Bogens?"""
        x, y = p
        if abs(x) > Wi / 2 - m:
            return False
        if y <= ys:
            return True
        cxr = Wi / 2 - (R - bw)
        cx = cxr if x >= 0 else -cxr
        return math.hypot(x - cx, y - ys) <= (R - bw) - m

    # Mond: oben rechts, ragt in den Rahmen
    rm = 0.19 * W
    a_m = math.radians(27)
    cxr = Wi / 2 - (R - bw)
    mx = cxr + (R - bw) * math.cos(a_m) - 0.62 * rm * math.cos(a_m)
    my = ys + (R - bw) * math.sin(a_m) - 0.62 * rm * math.sin(a_m)
    moon = circle(mx, my, rm, tol)

    cxl = -cxr

    def arch_x_left(y):
        """x des inneren Bogens links auf Höhe y"""
        if y <= ys:
            return -Wi / 2
        return cxl - math.sqrt(max((R - bw) ** 2 - (y - ys) ** 2, 0.0))

    # Spinnennetz links am Bogen
    web_poly, web_holes = None, []
    if spinne:
        wy = ys + 0.33 * W
        wx = arch_x_left(wy) - bw * 0.4
        a_n = math.atan2(ys - wy, cxl - wx)              # nach innen zum Bogenmittelpunkt
        Rw = 0.21 * W
        web_poly, web_holes = g.web(wx, wy, Rw, a_n - math.radians(48), a_n + math.radians(40), 6, 8,
                                    max(web * 0.95, 1.3))

    # Spinne: hängt oben links am Bogen
    spider_poly = None
    spider_cands = []
    if spinne:
        sp_S = 0.11 * W
        sx = -0.07 * W
        top_y = ys + math.sqrt(max((R - bw) ** 2 - (sx - cxl) ** 2, 0.0)) + bw * 0.5
        sp_y = ys + 0.36 * W
        for grow in (1.0, 1.2, 1.45, 1.75):           # kleine Szenen: Spinne größer, sonst verkleben die Beine
            sp = g.spider(sx, sp_y - (grow - 1) * 0.3 * sp_S, sp_S * grow, max(web, 1.2), thread_top=top_y)
            if g.polygon_ok(oriented(sp, True)) and g.min_gap(sp, 3) >= 0.15:
                spider_cands.append(sp)
        spider_poly = spider_cands[0] if spider_cands else None

    def blocked(p, m):
        if math.hypot(p[0] - mx, p[1] - my) < rm + m:
            return True
        if spider_poly and g.poly_bbox(spider_poly)[0] - m < p[0] < g.poly_bbox(spider_poly)[2] + m and \
                p[1] > g.poly_bbox(spider_poly)[1] - m:
            return True
        if web_poly and (point_in_polygon(p, web_poly) or min(dist(p, q) for q in web_poly[::3]) < m):
            return True
        return False

    # ---------------------------------------------------------------- Szene
    U = Wi
    if szene == "spukhaus":
        plan = [("tree", 0.70), ("stein_r", 0.12), ("pumpkin", 0), ("mansion", 0.60), ("pumpkin", 1),
                ("fence", 0.13), ("pumpkin", 2)]
    elif szene == "friedhof":
        plan = [("tree", 0.72), ("pumpkin", 0), ("stein_k", 0.18), ("stein_g", 0.15), ("pumpkin", 1),
                ("stein_s", 0.13), ("crypt", 0.46), ("pumpkin", 2)]
    else:
        plan = [("tree", 0.70), ("pumpkin", 0), ("cottage", 0.50), ("cauldron", 0.17), ("pumpkin", 1),
                ("cat", 0.13), ("pumpkin", 2)]
    faces = ["klassisch", "gruselig", "froehlich", "katze"]
    pk_size = 0.085 if szene != "hexenhaus" else 0.075
    plan = [(k, pk_size if k == "pumpkin" else sz, int(sz) if k == "pumpkin" else 0) for k, sz in plan
            if k != "pumpkin" or sz < kuerbisse]
    gap = 3.0 * web

    def make(kind, size, k=0, hf=1.0):
        if kind.startswith("stein"):
            form = {"stein_r": "rund", "stein_k": "kreuz", "stein_g": "gotisch", "stein_s": "schief"}[kind]
            return el_tombstone(form, size * U * 0.75, size * U * 1.25)
        if kind == "mansion":
            return el_mansion(size * U * 0.80, size * U * 1.2 * hf, seed, web)
        if kind == "fence":
            return el_fence(size * U, size * U * 1.25, web)
        if kind == "crypt":
            return el_crypt(size * U * 0.62, size * U * 1.15 * hf)
        if kind == "cottage":
            return el_cottage(size * U * 0.95, size * U * 1.1 * hf, web)
        if kind == "cauldron":
            return el_cauldron(size * U, size * U * 0.95, web)
        if kind == "cat":
            return el_cat(size * U * 1.6)
        if kind == "pumpkin":
            return el_pumpkin(size * U, faces[k % 4], web)
        raise ValueError(kind)

    def span(e):
        xs = [p[0] for p in e["line"]]
        return min(xs), max(xs)

    tree_slot = 0.17 * U
    f = 1.0
    for _ in range(12):
        hf = min(1.5, f ** -0.6)
        built = [(k, sz if k == "tree" else sz * f, None if k == "tree" else make(k, sz * f, n, hf))
                 for k, sz, n in plan]
        widths = [tree_slot * f if e is None else span(e)[1] - span(e)[0] for k, sz, e in built]
        avail = Wi - 4 * web
        total = sum(widths) + gap * (len(built) + 1)
        if total <= avail:
            break
        f *= 0.93
    else:
        raise ValueError("Szene passt nicht in den Bogen – größere Breite wählen")
    extra = (avail - total) / (len(built) + 1)
    x = -Wi / 2 + 2 * web + gap + extra
    slots = []                                   # (kind, size, element, x_mitte, lo, hi)
    for (k, sz, e), wdt in zip(built, widths):
        if e is None:
            slots.append((k, sz, None, x + wdt * 0.5, x, x + wdt))
        else:
            lo, hi = span(e)
            slots.append((k, sz, e, x - lo, x, x + wdt))
        x += wdt + gap + extra
    def base_of(kind, lo, hi, xc):
        if kind == "tree":
            return ground(xc) - 1.0
        return min(ground(lo + (hi - lo) * k / 8) for k in range(9)) - (0.012 * U if kind == "pumpkin" else 1.0)

    # Elemente, die an Mond, Netz oder Bogen stoßen, niedriger bauen
    for i, (k, sz, e, xc, lo, hi) in enumerate(slots):
        if e is None or k == "pumpkin":
            continue
        n_ = next(n for kk, szz, n in plan if kk == k)
        hfi = min(1.5, f ** -0.6)
        for _ in range(12):
            b = base_of(k, lo, hi, xc)
            pts_ = [(p[0] + xc, p[1] + b) for p in e["line"]]
            if all(inside_sky(q, 2 * web) and not blocked(q, 2.5 * web) for q in pts_ if q[1] > ground(q[0]) + 0.5):
                break
            hfi *= 0.9
            e = make(k, sz, n_, hfi)
        else:
            raise ValueError("Szene passt nicht unter den Bogen – größere Breite wählen")
        slots[i] = (k, sz, e, xc, lo, hi)
    boxes = []
    for k, sz, e, xc, lo, hi in slots:
        if e is not None:
            bb = g.poly_bbox([(p[0] + xc, p[1] + base_of(k, lo, hi, xc)) for p in e["line"]])
            boxes.append(bb)
    placed = []
    for k, sz, e, xc, lo, hi in slots:
        if e is None:
            m = 2.5 * web

            def box(p, x=xc):
                q = (p[0] + x, p[1] + ground(x) - 1.0)
                if not inside_sky(q, m + 1.5) or blocked(q, m):
                    return False
                return not any(b[0] - m < q[0] < b[2] + m and q[1] < b[3] + m for b in boxes)
            e = None
            for th in (1.0, 0.8, 0.65):          # bei wenig Platz einen kleineren Baum versuchen
                try:
                    e = el_tree(Wi / 2, sz * U * th, seed + 13, web, box, lean=-0.28 if xc < 0 else 0.28)
                    break
                except ValueError:
                    pass
            if e is None:
                continue                         # kein Platz für den Baum – Szene bleibt ohne
        line = e["line"]
        placed.append((xc, e, k, line[0][0] + xc, line[-1][0] + xc))

    # Himmelskontur: Boden + Elemente von links nach rechts, dann innerer Bogen
    xL, xR = -Wi / 2, Wi / 2
    sky = [(xL, ground(xL))]
    holes_scene = []
    eng_jobs = []
    cur = xL
    for x, e, kind, lo, hi in placed:
        base = base_of(kind, lo, hi, x)
        n = max(2, int((lo - cur) / 3.0))
        sky += [(cur + (lo - cur) * k / n, ground(cur + (lo - cur) * k / n)) for k in range(1, n)]
        line = _clip_ground([(p[0] + x, p[1] + base) for p in e["line"]], ground)
        sky += line
        for h in e["holes"]:
            holes_scene.append([(p[0] + x, p[1] + base) for p in h])
        eng_jobs.append((x, base, e, kind))
        cur = hi
    n = max(2, int((xR - cur) / 3.0))
    sky += [(cur + (xR - cur) * k / n, ground(cur + (xR - cur) * k / n)) for k in range(1, n + 1)]
    for p in sky:
        if not inside_sky(p, web) and p[1] > ground(p[0]) + 0.5:
            raise ValueError("Szene passt nicht unter den Bogen – größere Breite wählen")
    sky += i_right[1:] + i_left[:-1]
    sky = g.dedupe(sky, 0.12)
    sky = oriented(sky, True)
    # Mond, Netz und Spinne aus dem Himmel herausnehmen (sie hängen am Rahmen)
    sky = g.op2(sky, moon, "minus")
    if spinne:
        sky = g.op2(sky, web_poly, "minus")
        for sp in spider_cands:                  # erste Spinne, die frei hängt (nur der Faden berührt den Bogen)
            try:
                sky = g.op2(sky, sp, "minus")
                break
            except ValueError:
                continue
    arch.add_hole(_stumpf(sky, cfg))
    for h in holes_scene:
        bx = g.poly_bbox(h)
        if abs(g.signed_area(h)) >= 5.0 and min(bx[2] - bx[0], bx[3] - bx[1]) >= 1.8 and g.hole_ok(h, 0.3) and \
                all(min_distance(h, o, limit=web) >= web for o in arch.holes + [arch.outline]):
            arch.add_hole(h)
    # Netzzellen: nur ganz im Material
    for h in web_holes:
        if all(not point_in_polygon(p, sky) for p in h) and \
                min_distance(h, sky, limit=web) >= web and min_distance(h, arch.outline, limit=web) >= web:
            arch.add_hole(h)

    # Vor dem Mond: Hexe und/oder Fledermäuse als Durchbrüche
    moon_items = []
    inner_r = rm - max(web * 1.5, 0.05 * rm)
    if himmel in ("hexe", "beides"):
        wu = g.witch_unit()
        s = 1.55 * rm
        moon_items.append(g.place(wu, mx - 0.05 * rm, my - 0.05 * rm, s, ang=0.12))
    nb = fledermaeuse if himmel in ("fledermaeuse", "beides") else 0
    if himmel == "beides":
        nb = min(nb, 3)
    tries = 0
    while nb > 0 and tries < 400:
        tries += 1
        sz = rm * rng.uniform(0.42, 0.62) * (0.8 if himmel == "beides" else 1.0)
        a = rng.uniform(0, 2 * math.pi)
        rr = rng.uniform(0, inner_r - sz * 0.5)
        bx, by = mx + rr * math.cos(a), my + rr * math.sin(a)
        bat = g.place(g.bat_unit(rng.uniform(-1, 1)), bx, by, sz, ang=rng.uniform(-0.35, 0.35), flip=rng.random() < 0.5)
        if any(math.hypot(p[0] - mx, p[1] - my) > inner_r for p in bat):
            continue
        if any(min_distance(bat, it, limit=web * 1.5) < web * 1.5 for it in moon_items):
            continue
        moon_items.append(bat)
        nb -= 1
    for it in moon_items:
        arch.add_hole(oriented(it, False))

    # ---------------------------------------------------------------- Gravuren
    cv = dk.Canvas(arch, margin=0.8, hole_margin=0.9, seed=cfg.seed)
    # Text im Sockel
    if text.strip():
        box_w = 2 * (xt - tw / 2) - 6.0
        strokes, _ = fit_text(text, 0.0, hb * 0.48, box_w, hb - 2 * max(2.0, 0.17 * hb), min_h=3.0,
                              max_cap=0.42 * hb, style=schrift, case=schreibweise)
        for s_ in strokes:
            arch.add_engrave(s_)
        cv.block_strokes([(s_, False) for s_ in strokes], 0.8)
    # Mond: Krater und Schattenbögen
    for k in range(70):
        cr = rm * rng.uniform(0.05, 0.13)
        a = rng.uniform(0, 2 * math.pi)
        rr = rng.uniform(0, rm - cr - 2)
        c = circle(mx + rr * math.cos(a), my + rr * math.sin(a), cr, 0.1)
        if cv.put(c, True, reserve=0.8):
            cv.put(circle(mx + rr * math.cos(a) + cr * 0.2, my + rr * math.sin(a) - cr * 0.2, cr * 0.55, 0.1), True)
    for k in range(1, 5):
        r = rm - k * max(1.4, 0.035 * rm)
        cv.draw(arc_points(mx, my, r, math.radians(110 + 6 * k), math.radians(250 - 6 * k), 0.1))
    # Rahmen-Zierlinie
    if rahmen_deko != "keine":
        mid_r = R - bw / 2
        path = [(W / 2 - bw / 2, hb)] + _arch(W - bw, ys, mid_r)[0][1:] + _arch(W - bw, ys, mid_r)[1]
        path += [(-W / 2 + bw / 2, hb)]
        dk.styled_line(cv, path, rahmen_deko, 0.42 * bw, side=0, seed=cfg.seed, gravity=False) \
            if False else dk.styled_line(cv, _offset_line(path, -0.2 * bw), rahmen_deko, 0.45 * bw, side=+1,
                                         seed=cfg.seed, gravity=False)
    # Boden: Grasnarbe knapp unter der Bodenlinie
    gx = xL + 2
    while gx < xR - 2:
        y = ground(gx) - 1.6
        hgt = rng.uniform(1.2, 2.6)
        cv.draw([(gx, y - hgt), (gx + rng.uniform(-0.6, 0.6), y)])
        gx += rng.uniform(1.6, 3.4)
    # Szenen-Gravuren
    for x, base, e, kind in eng_jobs:
        for job in e["eng"]:
            _engrave(cv, job, x, base, rng, web)

    # ---------------------------------------------------------------- Bodenplatte
    D = max(44.0, 0.18 * W, 8 * T)
    PW = W + 0.06 * W
    plate = Part(f"{name}_platte", dk.rounded_rect(-PW / 2, -0.55 * D, PW / 2, 0.45 * D, min(8.0, D * 0.2), tol))
    for fid, x in (("fuss_l", -xt), ("fuss_r", xt)):
        feat, hole = slot_feature(fid, x - tw / 2, -T / 2, tw, T, True, 0.0)
        plate.holes.append(hole)
        plate.features.append(feat)
    pcv = dk.Canvas(plate, margin=1.0, seed=cfg.seed)
    pcv.draw(dk.rounded_rect(-PW / 2 + 3.5, -0.55 * D + 3.5, PW / 2 - 3.5, 0.45 * D - 3.5, max(1.0, min(8.0, D * 0.2) - 3.5), tol), True)
    for sx_, sy_ in ((-1, -1), (1, -1)):
        cx_ = sx_ * (PW / 2 - 3.5)
        cy_ = -0.55 * D + 3.5
        a0 = 0.0 if sx_ < 0 else math.pi / 2
        _web_engrave(pcv, cx_, cy_, min(0.75 * D, 0.2 * PW), a0, a0 + math.pi / 2)
    asm = Assembly(name, params=dict(width=W, szene=szene, himmel=himmel, spinne=spinne, kuerbisse=kuerbisse,
                                     variante=variante, **({"text": text} if text else {})))
    asm.parts += [arch, plate]
    for fid in ("fuss_l", "fuss_r"):
        asm.connect(f"{arch.name}:{fid}", f"{plate.name}:{fid}")
    asm.notes.append(f"{name}: Bogen mit beiden Zapfen in die Bodenplatte stecken (bei Bedarf leimen). "
                     "Eine LED-Lichterkette oder ein Teelicht im Glas dahinter lässt Fenster, Kürbisse, "
                     "Fledermäuse und Hexe leuchten. Tipp: Rückseite mit orangem Transparentpapier bekleben.")
    return asm


def _stumpf(poly, cfg):
    """Spitze Zwickel eines Lochs (z. B. zwischen Bogen und Spinnenfaden) kappen, damit der Kerf-Versatz
    sauber bleibt: spitze Ecken werden zu einer kurzen Fase, notfalls mit ausgedünnten Nachbarpunkten."""
    from validator import check_kerf, check_path
    d = cfg.kerf_offset
    if d <= 0:
        return poly
    poly = oriented(poly, False)
    xs, ys = [q[0] for q in poly], [q[1] for q in poly]
    rahmen = rect(min(xs) - 5, min(ys) - 5, max(xs) - min(xs) + 10, max(ys) - min(ys) + 10)
    for winkel, abstand in ((0.0, 0.0), (35.0, 0.0), (50.0, 4 * d + 0.3), (65.0, 8 * d + 0.5), (80.0, 8 * d + 0.5)):
        cand = _fasen(_duenn(poly, abstand), winkel, 8 * d + 0.6) if winkel else poly
        probe = Part("probe", rahmen, [cand])
        comp = probe.compensated(d)
        if not check_path(comp.holes[0], True, cfg) and not check_kerf(probe, comp, cfg):
            return cand
    return poly


def _duenn(poly, abstand):
    if abstand <= 0:
        return list(poly)
    out = [poly[0]]
    for q in poly[1:]:
        if dist(out[-1], q) >= abstand:
            out.append(q)
    return out


def _fasen(poly, winkel, laenge):
    n = len(poly)
    out = []
    for i, b in enumerate(poly):
        a, c = poly[i - 1], poly[(i + 1) % n]
        u = (a[0] - b[0], a[1] - b[1])
        v = (c[0] - b[0], c[1] - b[1])
        lu, lv = math.hypot(*u), math.hypot(*v)
        if lu < 1e-9 or lv < 1e-9:
            continue
        cosw = max(-1.0, min(1.0, (u[0] * v[0] + u[1] * v[1]) / (lu * lv)))
        if math.degrees(math.acos(cosw)) < winkel:
            t = min(laenge, 0.45 * lu, 0.45 * lv)
            out += [(b[0] + u[0] / lu * t, b[1] + u[1] / lu * t), (b[0] + v[0] / lv * t, b[1] + v[1] / lv * t)]
        else:
            out.append(b)
    return out


def _clip_ground(line, ground, lift=0.4):
    """Anfang und Ende einer Element-Linie an der welligen Bodenlinie abschneiden."""
    def f(p):
        return p[1] - ground(p[0]) - lift

    def cut(a, b):
        lo, hi = 0.0, 1.0
        for _ in range(40):
            m = (lo + hi) / 2
            q = (a[0] + (b[0] - a[0]) * m, a[1] + (b[1] - a[1]) * m)
            if f(q) < 0:
                lo = m
            else:
                hi = m
        return (a[0] + (b[0] - a[0]) * hi, a[1] + (b[1] - a[1]) * hi)

    i = 0
    while i < len(line) - 1 and f(line[i]) < 0:
        i += 1
    j = len(line) - 1
    while j > 0 and f(line[j]) < 0:
        j -= 1
    out = line[i:j + 1]
    if i > 0:
        out = [cut(line[i - 1], line[i])] + out
    if j < len(line) - 1:
        out = out + [cut(line[j + 1], line[j])]
    return out


def _offset_line(path, d):
    r, l = g.strip(path, 2 * abs(d), 2 * abs(d))
    return l if d > 0 else r


def _web_engrave(cv, cx, cy, R, a0, a1):
    spokes = 5
    angs = [a0 + (a1 - a0) * i / spokes for i in range(spokes + 1)]
    for a in angs:
        cv.draw([(cx, cy), (cx + R * math.cos(a), cy + R * math.sin(a))])
    for k in range(1, 5):
        r = R * k / 4.3
        for i in range(spokes):
            p0 = (cx + r * math.cos(angs[i]), cy + r * math.sin(angs[i]))
            p1 = (cx + r * math.cos(angs[i + 1]), cy + r * math.sin(angs[i + 1]))
            m = (cx + r * 0.86 * math.cos((angs[i] + angs[i + 1]) / 2), cy + r * 0.86 * math.sin((angs[i] + angs[i + 1]) / 2))
            cv.draw(bezier_q(p0, m, p1, 8))


def _engrave(cv, job, x, base, rng, web):
    kind = job[0]
    mv = lambda b: (b[0] + x, b[1] + base, b[2] + x, b[3] + base)
    if kind == "walls":
        for b in job[1]:
            dk.wall_pattern(cv, "stein", mv(b), max(2.6, (b[2] - b[0]) * 0.055), seed=rng.randint(1, 999))
    elif kind == "walls_holz":
        for b in job[1]:
            dk.wall_pattern(cv, "holz", mv(b), max(3.0, (b[2] - b[0]) * 0.07), seed=rng.randint(1, 999))
    elif kind == "roofs":
        for b in job[1]:
            dk.roof_pattern(cv, "schindel", mv(b), row=max(2.5, (b[3] - b[1]) * 0.1), seed=rng.randint(1, 999))
    elif kind == "ribs":
        cx, cy, w, h = job[1]
        for s in (-1, 1):
            for f in (0.22, 0.40):
                p0 = (x + cx + s * f * w * 0.4, base + 0.02 * h)
                p1 = (x + cx + s * f * w * 0.4, base + 0.82 * h)
                c = (x + cx + s * f * w * 1.25, base + 0.42 * h)
                cv.draw(bezier_q(p0, c, p1, 14))
    elif kind == "stone":
        _, form, w, h = job
        inner = [(px + x, py + base) for px, py in g.tombstone(form, w * 0.80, h * 0.86)]
        inner = [(px, py + 0.04 * h) for px, py in inner]
        if form != "kreuz":
            cv.draw(inner, True)
            cap = min(0.16 * w, 0.12 * h)
            try:
                strokes, _ = fit_text("RIP", x, base + 0.62 * h, 0.6 * w, cap * 1.2, min_h=1.5, max_cap=cap)
            except ValueError:
                strokes = []                     # Stein zu klein für Schrift
            for s_ in strokes:
                cv.draw(s_)
        # Riss
        px, py = x + rng.uniform(-0.2, 0.2) * w, base + 0.85 * h
        pts = [(px, py)]
        for k in range(5):
            px += rng.uniform(-0.08, 0.08) * w
            py -= rng.uniform(0.05, 0.09) * h
            pts.append((px, py))
        cv.draw(pts)
    elif kind == "kessel":
        cx, cy, r, ry = job[1]
        for k in (0.35, 0.6):
            cv.draw(arc_points(x + cx, base + cy, r * k + 1, math.radians(200), math.radians(340), 0.1))
    elif kind == "bark":
        h = job[1]
        for k in range(-2, 3):
            xs = x + k * 0.012 * h
            pts = [(xs + 0.004 * h * math.sin(i * 1.3 + k), base + 0.07 * h + i * 0.03 * h) for i in range(8)]
            cv.draw(pts)
