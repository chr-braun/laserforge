"""
Kürbis-Leuchte – geschnitzter Halloween-Kürbis zum Hinstellen.

Ein bauchiger Kürbis mit Stiel, Blatt und Ranke. Das Gesicht (oder eine Silhouette) ist
ausgeschnitten, die Rippen und das Blattgeäder sind graviert. Ein Teelicht (LED) dahinter lässt
das Gesicht leuchten. Steht mit einem Zapfen in einem ovalen Sockel, auf Wunsch mit Text.
"""
import importlib.util
import math
import os
import random
import sys

from steckwerk import Assembly, Part, arc_points, bezier_q, circle, min_distance, oriented, point_in_polygon
from models import _deko as dk
from models._font import STYLES, unsupported
from models._stand import stand_base, tab_feature_at
from pakete import bibliothek, flag, num, sel, txt


def _lib():
    return bibliothek("verzierungen").G


g = _lib()

FACES = [("klassisch", "klassisch (Dreiecke)"), ("gruselig", "gruselig mit Fangzähnen"),
         ("froehlich", "fröhlich"), ("katze", "Katzengesicht"), ("fledermaus", "Fledermaus-Silhouette"),
         ("hexe", "Hexe auf dem Besen"), ("spinnennetz", "Spinnennetz")]

UEBERSETZUNG = {"en": g.EN}

INFO = dict(
    label="Kürbis-Leuchte",
    group="Halloween",
    desc="Geschnitzter Kürbis mit Stiel, Blatt und Ranke – Gesicht oder Silhouette leuchtet mit Teelicht.",
    params=[
        num("width", "Breite", 150, 80, 320),
        sel("gesicht", "Gesicht", FACES, "gruselig"),
        flag("rippen", "Rippen gravieren", True),
        flag("blatt", "Blatt und Ranke", True),
        txt("text", "Text auf dem Sockel", "BOO!", "leer = ohne Text", section="Schrift und Beschriftung"),
        sel("schrift", "Schrift", [(s, s) for s in STYLES], "fett", section="Schrift und Beschriftung"),
        sel("schreibweise", "Schreibweise", dk.FONT_CASES, "gross", section="Schrift und Beschriftung"),
    ],
)


def leaf(cx, cy, s, ang):
    """Kürbisblatt mit drei Lappen, Stielansatz bei (cx, cy), zeigt in Richtung ang."""
    pts = g.chain(
        [(0.0, -0.04)],
        g.bez((0.0, -0.04), (0.20, -0.30), (0.42, -0.20), 6),
        g.bez((0.42, -0.20), (0.40, -0.10), (0.55, -0.12), 4),
        g.bez((0.55, -0.12), (0.80, -0.10), (1.0, 0.0), 6),
        g.bez((1.0, 0.0), (0.80, 0.10), (0.55, 0.12), 6),
        g.bez((0.55, 0.12), (0.40, 0.10), (0.42, 0.20), 4),
        g.bez((0.42, 0.20), (0.20, 0.30), (0.0, 0.04), 6),
    )
    pts = [(x, y * 1.7) for x, y in pts]
    return g.place(g.dedupe(pts, 0.004), cx, cy, s, ang)


def leaf_veins(cx, cy, s, ang):
    lines = [[(0.05, 0.0), (0.92, 0.0)]]
    for x, d in ((0.30, 1), (0.30, -1), (0.55, 1), (0.55, -1), (0.75, 1), (0.75, -1)):
        lines.append([(x, 0.0), (x + 0.12, d * 0.22 * (1.1 - x))])
    return [g.place(l, cx, cy, s, ang) for l in lines]


def build(cfg, name="kuerbis", width=150.0, gesicht="gruselig", rippen=True, blatt=True, text="BOO!",
          schrift="fett", schreibweise="gross"):
    T = cfg.T
    W = cfg.s(width)
    if not 80 <= W <= 320:
        raise ValueError("Kürbis: Breite muss zwischen 80 und 320 mm liegen")
    dk.check_choice("Gesicht", gesicht, FACES)
    bad = unsupported(text or "")
    if bad:
        raise ValueError(f"Zeichen {''.join(bad)!r} gibt es in der Gravurschrift nicht")
    web = max(cfg.min_web * 1.6, 1.6)
    tol = cfg.arc_tolerance
    rng = random.Random(cfg.seed)
    H = 0.80 * W
    yc = 0.07 * H                                   # flache Standfläche
    body = g.pumpkin(0.0, 0.0, W, H, lobes=5)
    line = _upper(body, yc)                         # links → rechts über den Stiel
    tw = max(0.22 * W, 4 * T)
    xl, xr = line[0][0], line[-1][0]
    bottom = [(xr, yc), (tw / 2, yc), (tw / 2, yc - T), (-tw / 2, yc - T), (-tw / 2, yc), (xl, yc)]
    outline = oriented(g.dedupe(line + bottom[1:-1], 0.1), True)
    stem_top = max(p[1] for p in outline)
    # Blatt am Stiel
    leaf_at = None
    if blatt:
        from validator import check_kerf
        top_y = H * 0.94
        ls = 0.36 * W
        for ang in (math.radians(-12), math.radians(-4), math.radians(-22)):
            try:
                lp = leaf(0.07 * W, top_y - 0.02 * H, ls, ang)
                new = g.op2(outline, lp, "union")
                probe = Part("probe", new)
                if check_kerf(probe, probe.compensated(cfg.kerf_offset), cfg):
                    continue                             # zu spitzer Zwickel zwischen Blatt und Kürbis
                outline = new
                leaf_at = (0.07 * W, top_y - 0.02 * H, ls, ang)
                break
            except ValueError:
                continue
    part = Part(f"{name}_kuerbis", outline, features=[tab_feature_at("fuss", -tw / 2, yc, tw, T)])

    # Gesicht / Silhouette
    fw, fh = 0.74 * W, 0.62 * H
    fcx, fcy = 0.0, 0.47 * H
    holes = []
    if gesicht in ("klassisch", "gruselig", "froehlich", "katze"):
        holes = g.pumpkin_face(gesicht, fcx, fcy, fw, fh)
    elif gesicht == "fledermaus":
        holes = [oriented(g.place(g.bat_unit(0.6), fcx, fcy - 0.02 * H, 0.66 * W), False)]
        for s_ in (-1, 1):
            holes.append(circle(fcx + s_ * 0.06 * W, fcy + 0.25 * H, 0.025 * W, tol))
    elif gesicht == "hexe":
        holes = [oriented(g.place(g.witch_unit(), fcx, fcy, 0.80 * W, 0.1), False)]
        if not g.hole_ok(holes[0], 0.3) or g.min_gap(holes[0], 3) < web:   # kleiner Kürbis: Besen zu dünn
            holes = [oriented(g.place(g.hat_unit(), fcx, fcy - 0.04 * H, 0.55 * W), False)]
    elif gesicht == "spinnennetz":
        R = 0.30 * W
        holes = g.web(fcx, fcy, R, math.radians(90), math.radians(450), 5, 12, max(web, 1.4))[1]
    for h in holes:
        if g.hole_ok(h, 0.3) and abs(g.signed_area(h)) > 4.0 and \
                min_distance(h, outline, limit=2 * web) >= 2 * web:
            part.add_hole(h)
    if not part.holes:
        raise ValueError("Gesicht passt nicht – Kürbis größer wählen")

    # Gravuren: Rippen, Glanz, Stiel, Blattadern, Ranke
    cv = dk.Canvas(part, margin=1.0, hole_margin=1.2, seed=cfg.seed)
    if rippen:
        for s_ in (-1, 1):
            for f in (0.16, 0.33, 0.47):
                p0 = (s_ * f * 0.30 * W, 0.86 * H)
                p1 = (s_ * f * 0.36 * W, yc + 0.03 * H)
                c = (s_ * (0.10 + f * 1.05) * W, 0.45 * H)
                cv.draw(bezier_q(p0, c, p1, 24))
        if gesicht != "spinnennetz":
            cv.draw(bezier_q((0.0, 0.88 * H), (0.0, 0.45 * H), (0.0, yc + 0.03 * H), 12))
    if gesicht == "spinnennetz":
        cv.put(g.spider(fcx, fcy - 0.01 * H, 0.16 * W, 0.5), True)
    for k in range(4):                                              # Glanzlicht links oben
        r = 0.36 * W - k * 0.022 * W
        cv.draw(arc_points(0.0, 0.47 * H, r, math.radians(128 + 4 * k), math.radians(152 - 3 * k), 0.1))
    for dx in (-0.02, 0.0, 0.02):                                   # Stielfasern
        cv.draw([(dx * W, 0.90 * H), (dx * W * 1.4 + 0.02 * W, stem_top - 0.03 * H)])
    if leaf_at:
        for l in leaf_veins(*leaf_at):
            cv.draw(l)
        # Ranke: Spirale neben dem Stiel
        cx_, cy_ = -0.13 * W, 0.92 * H
        sp = [(cx_ + (0.005 + 0.0016 * t) * W * math.cos(t * 0.55 + 1.0),
               cy_ + (0.005 + 0.0016 * t) * W * math.sin(t * 0.55 + 1.0)) for t in range(0, 40)]
        cv.draw(sp)

    asm = Assembly(name, params=dict(width=W, gesicht=gesicht, **({"text": text} if text else {})))
    asm.parts.append(part)
    stand_base(asm, part, "fuss", tw, cfg, 0.36 * W, 0.16 * W, f"{name}_sockel", text or "", schrift,
               schreibweise)
    asm.notes.append(f"{name}: Kürbis in den Sockel stecken, LED-Teelicht dahinter stellen. "
                     "Tipp: Rückseite mit orangem Transparentpapier bekleben, dann leuchtet das Gesicht warm.")
    return asm


def _upper(poly, cut_y):
    P = oriented(poly, True)
    n = len(P)
    hits = []
    for i in range(n):
        a, b = P[i], P[(i + 1) % n]
        if (a[1] - cut_y) * (b[1] - cut_y) < 0:
            t = (cut_y - a[1]) / (b[1] - a[1])
            hits.append((i, (a[0] + t * (b[0] - a[0]), cut_y), b[1] > a[1]))
    up = [h for h in hits if h[2]][0]
    down = [h for h in hits if not h[2]][0]
    out = [up[1]]
    k = up[0] + 1
    while True:
        out.append(P[k % n])
        if k % n == down[0]:
            break
        k += 1
    out.append(down[1])
    return list(reversed(out))


def _round_web(cx, cy, R, t):
    """Rundes Spinnennetz als Löcher (Fäden bleiben stehen)."""
    holes = []
    spokes = 10
    rings = 4
    angs = [2 * math.pi * i / spokes for i in range(spokes + 1)]
    radii = [R * (0.25 + 0.75 * k / rings) for k in range(1, rings + 1)]
    for k in range(rings):
        r_in = radii[k - 1] if k > 0 else 0.0
        r_out = radii[k]
        for i in range(spokes):
            aa, ab = angs[i], angs[i + 1]
            rr = max(r_in * 0.9, t)
            da = (t * 0.6) / rr
            ia, ib = aa + da, ab - da
            if ib - ia < 0.05:
                continue
            o = [(cx + (r_out - t / 2 - 0.12 * r_out * (ab - aa) * math.sin(math.pi * j / 10)) *
                  math.cos(ia + (ib - ia) * j / 10),
                  cy + (r_out - t / 2 - 0.12 * r_out * (ab - aa) * math.sin(math.pi * j / 10)) *
                  math.sin(ia + (ib - ia) * j / 10)) for j in range(11)]
            if k == 0:
                rc = (t * 0.6) / math.sin((ab - aa) / 2)
                inner = [(cx + rc * math.cos((aa + ab) / 2), cy + rc * math.sin((aa + ab) / 2))]
            else:
                inner = [(cx + (r_in + t / 2 - 0.12 * r_in * (ab - aa) * math.sin(math.pi * j / 10)) *
                          math.cos(ib - (ib - ia) * j / 10),
                          cy + (r_in + t / 2 - 0.12 * r_in * (ab - aa) * math.sin(math.pi * j / 10)) *
                          math.sin(ib - (ib - ia) * j / 10)) for j in range(11)]
            cell = g.dedupe(o + inner, 0.08)
            if len(cell) >= 3 and abs(g.signed_area(cell)) > 3.0:
                holes.append(cell)
    # Abstand zwischen Löchern sichern
    out = []
    for h in holes:
        if all(min_distance(h, q, limit=t) >= t * 0.95 for q in out):
            out.append(h)
    return out
