"""
Motiv-Vorlagen – eigene Motive (SVG/PNG aus der Motiv-Bibliothek) frei auf einer Grundform platzieren.

  aufsteller   Platte mit Standsockel
  schild       Hängeschild mit Löchern oder Schraublöchern
  anhaenger    kleiner Anhänger mit Loch
  untersetzer  Untersetzer (rund oder eckig), Motive standardmäßig flächig graviert
  silhouette   das Motiv selbst wird zum Teil – mit Sockel, Öse oder frei

Platzierung (Parameter „motive“): Liste von {id, x, y, groesse, drehung, spiegeln, art}
  x, y      Mitte des Motivs in mm, gemessen von der Mitte der Grundform
  groesse   längere Seite des Motivs in mm
  drehung   Grad gegen den Uhrzeigersinn
  art       schnitt (Durchbruch), umriss (Gravurlinie), flaeche (flächig graviert, Schraffur)
"""
from __future__ import annotations

import math
from typing import Dict, List, Optional, Sequence, Tuple

import motive as mt
from steckwerk import Assembly, Part, Point, circle, ellipse, min_distance, offset_polygon, oriented, \
    point_in_polygon, polygon_ok, rect, signed_area
from models import _deko as dk
from models._font import STYLES, fit_text, unsupported
from models._stand import stand_base, tab_feature_at

ARTEN = [("schnitt", "ausschneiden"), ("umriss", "Umriss gravieren"), ("flaeche", "flächig gravieren")]
ART_KEYS = [a for a, _ in ARTEN]
FORMEN = [("abgerundet", "Rechteck, abgerundet"), ("rechteck", "Rechteck"), ("bogen", "Rundbogen"),
          ("spitzbogen", "Spitzbogen"), ("oval", "oval"), ("rund", "rund"), ("herz", "Herz")]
FORMEN_AUFSTELLER = [f for f in FORMEN if f[0] not in ("herz",)]
FORMEN_ANHAENGER = [("rund", "rund"), ("oval", "oval"), ("abgerundet", "Rechteck, abgerundet"), ("herz", "Herz"),
                    ("bogen", "Rundbogen")]
FORMEN_UNTERSETZER = [("rund", "rund"), ("abgerundet", "Quadrat, abgerundet"), ("achteck", "Achteck")]
AUFHAENGUNG = [("zwei_loecher", "zwei Löcher oben"), ("ein_loch", "ein Loch oben"), ("schrauben", "vier Schraublöcher"),
               ("keine", "keine")]
FUSS = [("sockel", "Standsockel"), ("oese", "Öse zum Aufhängen"), ("keiner", "nichts (freie Form)")]
INNEN = [("schnitt", "Innenformen ausschneiden"), ("gravur", "Innenformen gravieren")]


# ---------------------------------------------------------------------------
# Grundformen
# ---------------------------------------------------------------------------

def _arched(W: float, H: float) -> List[Point]:
    r = W / 2
    if H <= r + 1:
        return ellipse(0, 0, W / 2, H, n=96)[:49]
    from steckwerk import arc_points
    pts = [(-W / 2, 0.0), (W / 2, 0.0)] + arc_points(0, H - r, r, 0.0, math.pi, 0.05)
    return pts


def plate(form: str, W: float, H: float, flat_bottom: float = 0.0) -> List[Point]:
    """Grundform, Mitte unten bei (0, 0), Höhe H, Breite W, gegen den Uhrzeigersinn.
    flat_bottom: Mindestbreite einer geraden Unterkante (für den Steckzapfen in den Sockel)."""
    if form == "rechteck":
        p = rect(-W / 2, 0, W, H)
    elif form == "abgerundet":
        p = dk.rounded_rect(-W / 2, 0, W / 2, H, 0.12 * min(W, H))
    elif form == "bogen":
        p = _arched(W, H)
    elif form == "spitzbogen":
        p = dk.pointed_arch(0, 0, W, H)
    elif form in ("oval", "rund"):
        if form == "rund":
            W = H = min(W, H)
        p = ellipse(0, H / 2, W / 2, H / 2, n=144)
        if flat_bottom:
            hw = min(0.95, (flat_bottom / 2) / (W / 2))
            cut = max(0.06 * H, H / 2 * (1 - math.sqrt(1 - hw * hw)))
            p = dk._clip_half(p, 0.0, -1.0, -cut)
            p = [(x, y - cut) for x, y in p]
    elif form == "herz":
        p = dk.heart(0, H / 2, W, H)
    elif form == "achteck":
        s = min(W, H)
        p = [(s / 2 * math.cos(math.radians(22.5 + 45 * k)), s / 2 + s / 2 * math.sin(math.radians(22.5 + 45 * k)))
             for k in range(8)]
        p = [(x / math.cos(math.radians(22.5)), y) for x, y in p]
        p = [(x, (y - s / 2) / math.cos(math.radians(22.5)) + s / 2) for x, y in p]
    else:
        raise ValueError(f"Grundform {form!r} unbekannt")
    return oriented(p, True)


def with_tab(outline: List[Point], tw: float, T: float) -> List[Point]:
    """Steckzapfen mittig in die gerade Unterkante (y = 0) einsetzen."""
    P = oriented(outline, True)
    i0 = min(range(len(P)), key=lambda i: (round(P[i][1], 6), P[i][0]))
    P = P[i0:] + P[:i0]
    if abs(P[0][1]) > 1e-6 or abs(P[1][1]) > 1e-6 or not (P[0][0] < -tw / 2 - 1 and P[1][0] > tw / 2 + 1):
        raise ValueError("Die Grundform hat unten keine gerade Kante für den Sockel")
    return [P[0], (-tw / 2, 0.0), (-tw / 2, -T), (tw / 2, -T), (tw / 2, 0.0)] + P[1:]


# ---------------------------------------------------------------------------
# Motive setzen
# ---------------------------------------------------------------------------

def _hatch(poly_set: Sequence[Sequence[Point]], step: float, angle: float = 0.0) -> List[List[Point]]:
    """Schraffur (gerade/ungerade über alle Konturen) im Abstand step, Winkel in Grad."""
    a = math.radians(angle)
    ca, sa = math.cos(a), math.sin(a)
    rot = [[(x * ca + y * sa, -x * sa + y * ca) for x, y in p] for p in poly_set]
    ys = [y for p in rot for _, y in p]
    if not ys:
        return []
    y = min(ys) + step / 2
    out = []
    flip = False
    while y < max(ys):
        xs = []
        for p in rot:
            n = len(p)
            for i in range(n):
                (x0, y0), (x1, y1) = p[i], p[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
        xs.sort()
        segs = [(xs[i], xs[i + 1]) for i in range(0, len(xs) - 1, 2)]
        if flip:
            segs = [(b, a_) for a_, b in reversed(segs)]
        for x0, x1 in segs:
            if abs(x1 - x0) > 0.3:
                out.append([(x0 * ca - y * sa, x0 * sa + y * ca), (x1 * ca - y * sa, x1 * sa + y * ca)])
        flip = not flip
        y += step
    return out


def tidy(poly: Sequence[Point], tol: float = 0.04, min_len: float = 0.18) -> List[Point]:
    """Für den Laser aufräumen: Douglas-Peucker in mm und Kanten kürzer als min_len zusammenfassen
    (Mini-Kanten aus Kurven oder Pixelkonturen stören den Kerf-Versatz und kosten Rechenzeit)."""
    p = mt.simplify(list(poly), tol)
    changed = True
    while changed and len(p) > 4:
        changed = False
        out = [p[0]]
        for q in p[1:]:
            if math.hypot(q[0] - out[-1][0], q[1] - out[-1][1]) < min_len:
                changed = True
                continue
            out.append(q)
        if len(out) > 3 and math.hypot(out[0][0] - out[-1][0], out[0][1] - out[-1][1]) < min_len:
            out.pop()
            changed = True
        p = out
    return p


class Placed:
    def __init__(self, idx: int, spec: dict, m: dict):
        self.idx, self.spec, self.m = idx, spec, m
        x, y, s = spec["x"], spec["y"], spec["groesse"]
        a, f = spec.get("drehung", 0.0), bool(spec.get("spiegeln"))
        self.name = f"Motiv {idx + 1} ({m.get('name', m['id'])})"
        self.areas = [(tidy(mt.place(fl["aussen"], x, y, s, a, f)),
                       [tidy(mt.place(h, x, y, s, a, f)) for h in fl["loecher"]]) for fl in m["flaechen"]]
        self.lines = [mt.place(li, x, y, s, a, f) for li in m["linien"]]
        self.art = spec.get("art", "schnitt")


def resolve(specs: Sequence[dict], cy: float) -> List[Placed]:
    """Platzierungen laden; y der Spezifikation zählt ab der Mitte der Grundform (cy)."""
    out = []
    for i, s in enumerate(specs or []):
        s = dict(dict(x=0.0, y=0.0, groesse=50.0, drehung=0.0, spiegeln=False, art="schnitt"), **s)
        s["y"] += cy
        out.append(Placed(i, s, mt.load(s["id"])))
    return out


def cut_motifs(part: Part, placed: Sequence[Placed], cfg, web: float, notes: List[str]) -> None:
    """Motive mit art=schnitt als Durchbrüche einsetzen – mit verständlichen Fehlermeldungen."""
    for P in placed:
        if P.art != "schnitt":
            continue
        if not P.areas:
            notes.append(f"{P.name} besteht nur aus Linien – es wird graviert.")
            P.art = "umriss"
            continue
        islands = 0
        for outer, holes in P.areas:
            islands += len(holes)
            if not all(point_in_polygon(q, part.outline) for q in outer[:: max(1, len(outer) // 40)]) or \
                    min_distance(outer, part.outline, limit=web) < web:
                raise ValueError(f"{P.name} ragt über den Rand oder sitzt zu nah daran – "
                                 f"verschieben oder kleiner machen")
            for h in part.holes:
                if min_distance(outer, h, limit=web) < web or point_in_polygon(outer[0], h) or \
                        point_in_polygon(h[0], outer):
                    raise ValueError(f"{P.name} liegt zu dicht an einem anderen Ausschnitt "
                                     f"(mindestens {web:.1f} mm Steg) – verschieben oder kleiner machen")
            if abs(signed_area(outer)) < 1.0:
                raise ValueError(f"{P.name} ist zu klein zum Ausschneiden – größer machen oder gravieren")
            comp = offset_polygon(oriented(outer, False), cfg.kerf_offset)
            if len(comp) < 3 or not polygon_ok(oriented(comp, True)) or \
                    signed_area(comp) * signed_area(oriented(outer, False)) <= 0:
                raise ValueError(f"{P.name} hat zu feine Stellen zum Ausschneiden – größer machen oder "
                                 f"„Umriss gravieren“ wählen")
            part.add_hole(outer)
        if islands:
            notes.append(f"{P.name}: {islands} Innenfläche(n) fallen beim Ausschneiden heraus – "
                         f"wer sie behalten will, wählt „Umriss gravieren“.")


def engrave_motifs(cv: dk.Canvas, placed: Sequence[Placed], hatch: float) -> None:
    for P in placed:
        if P.art in ("umriss", "flaeche"):
            for outer, holes in P.areas:
                cv.draw(outer, True)
                for h in holes:
                    cv.draw(h, True)
                if P.art == "flaeche":
                    for seg in _hatch([outer] + holes, hatch, P.spec.get("drehung", 0.0) + 15.0):
                        cv.draw(seg)
        for li in P.lines:
            cv.draw(li)
        for outer, _ in P.areas:
            cv.block(outer, 0.8)


def motif_summary(specs: Sequence[dict]) -> str:
    return "; ".join(f"{s['id']}@{s['x']:g},{s['y']:g} {s['groesse']:g}mm {s.get('art', 'schnitt')}"
                     for s in specs or []) or "keine"


def _check_text(*texts: str) -> None:
    for t in texts:
        bad = unsupported(t or "")
        if bad:
            raise ValueError(f"Zeichen {''.join(bad)!r} gibt es in der Gravurschrift nicht")


def _frame(cv: dk.Canvas, outline: List[Point], rahmen: str, inset: float, size: float, seed: int) -> None:
    if rahmen in ("keine", "", None):
        return
    inner = offset_polygon(oriented(outline, True), -inset)
    if len(inner) < 3 or not polygon_ok(inner):
        return
    loop = oriented(inner, True)
    dk.styled_line(cv, loop + [loop[0]], rahmen, size, side=1, seed=seed)


def _text(cv: dk.Canvas, text: str, cx: float, cy: float, w: float, h: float, schrift: str,
          schreibweise: str = "gross") -> None:
    if not text.strip():
        return
    strokes, _ = fit_text(text, cx, cy, w, h, min_h=2.5, max_cap=0.6 * h, style=schrift, case=schreibweise)
    for s in strokes:
        cv.draw(s)


# ---------------------------------------------------------------------------
# Vorlagen
# ---------------------------------------------------------------------------

def _web(cfg) -> float:
    return max(cfg.min_web * 1.5, 1.5)


def build_aufsteller(cfg, name="aufsteller", width=120.0, height=150.0, form="bogen", motive=None,
                     rahmen="linie", schraffur=0.3, text="", schrift="normal", sockel_text="", schreibweise="gross"):
    T = cfg.T
    W, H = cfg.s(width), cfg.s(height)
    dk.check_choice("Form", form, FORMEN_AUFSTELLER)
    _check_text(text, sockel_text)
    web = _web(cfg)
    tw = min(max(0.35 * W, 4 * T), 0.6 * W)
    outline = with_tab(plate(form, W, H, flat_bottom=tw + 4.0), tw, T)
    part = Part(f"{name}_platte", outline, features=[tab_feature_at("fuss", -tw / 2, 0.0, tw, T)])
    notes: List[str] = []
    placed = resolve(motive or [], H / 2)
    cut_motifs(part, placed, cfg, web, notes)
    cv = dk.Canvas(part, margin=1.2, hole_margin=1.2, seed=cfg.seed)
    engrave_motifs(cv, placed, schraffur)
    _frame(cv, plate(form, W, H, flat_bottom=tw + 4.0), rahmen, 0.05 * min(W, H), 0.035 * min(W, H), cfg.seed)
    _text(cv, text, 0.0, 0.11 * H, 0.7 * W, 0.12 * H, schrift, schreibweise)
    asm = Assembly(name, params=dict(width=W, height=H, form=form, motive=motif_summary(motive)))
    asm.parts.append(part)
    stand_base(asm, part, "fuss", tw, cfg, max(0.42 * W, tw / 2 + 12), max(0.16 * W, 3.5 * T), f"{name}_sockel",
               sockel_text or "", schrift, schreibweise)
    asm.notes += notes + [f"{name}: Platte in den Sockel stecken."]
    return asm


def _hang_holes(form: str, W: float, H: float, kind: str, r: float, inset: float, outline) -> List[List[Point]]:
    if kind == "keine":
        return []
    if kind == "ein_loch":                                # unter der Oberkante in der Mitte (beim Herz: unter der Kerbe)
        n = len(outline)
        ys = []
        for i in range(n):
            (xa, ya), (xb, yb) = outline[i], outline[(i + 1) % n]
            if (xa <= 0 < xb) or (xb <= 0 < xa):
                ys.append(ya + (0 - xa) * (yb - ya) / (xb - xa))
        y = (max(ys) if ys else max(q[1] for q in outline)) - inset - r
        for _ in range(60):
            c = circle(0.0, y, r)
            if all(point_in_polygon(q, outline) for q in c) and min_distance(c, outline) >= inset * 0.6:
                break
            y -= 0.5
        return [circle(0.0, y, r)]
    if kind == "zwei_loecher":
        pts = [(-W / 2 + inset + r, H - inset - r), (W / 2 - inset - r, H - inset - r)]
    else:
        pts = [(sx * (W / 2 - inset - r), y) for sx in (-1, 1) for y in (inset + r, H - inset - r)]
    out = []
    for x, y in pts:
        # bei Bögen/Ovalen nach innen rücken, bis das Loch sicher in der Platte liegt
        for k in range(40):
            c = circle(x, y, r)
            if all(point_in_polygon(q, outline) for q in c) and min_distance(c, outline) >= inset * 0.6:
                break
            x *= 0.96
            y = H / 2 + (y - H / 2) * 0.96
        out.append(circle(x, y, r))
    return out


def build_schild(cfg, name="schild", width=200.0, height=120.0, form="abgerundet", aufhaengung="zwei_loecher",
                 motive=None, rahmen="doppelt", schraffur=0.3, text="Willkommen", schrift="normal", schreibweise="gross"):
    W, H = cfg.s(width), cfg.s(height)
    dk.check_choice("Form", form, FORMEN)
    dk.check_choice("Aufhängung", aufhaengung, AUFHAENGUNG)
    _check_text(text)
    web = _web(cfg)
    outline = plate(form, W, H)
    part = Part(f"{name}", outline)
    r = max(1.6, min(3.0, 0.02 * min(W, H) + 1))
    for h in _hang_holes(form, W, H, aufhaengung, r, max(4.0, 0.05 * min(W, H)), outline):
        part.add_hole(h)
    notes: List[str] = []
    placed = resolve(motive or [], H / 2)
    cut_motifs(part, placed, cfg, web, notes)
    cv = dk.Canvas(part, margin=1.2, hole_margin=1.5, seed=cfg.seed)
    engrave_motifs(cv, placed, schraffur)
    _frame(cv, outline, rahmen, 0.045 * min(W, H), 0.03 * min(W, H), cfg.seed)
    _text(cv, text, 0.0, 0.16 * H, 0.72 * W, 0.18 * H, schrift, schreibweise)
    asm = Assembly(name, params=dict(width=W, height=H, form=form, aufhaengung=aufhaengung,
                                     motive=motif_summary(motive)))
    asm.parts.append(part)
    asm.notes += notes + ([f"{name}: an einer Kordel oder mit Schrauben aufhängen."] if aufhaengung != "keine" else [])
    return asm


def build_anhaenger(cfg, name="anhaenger", size=60.0, form="rund", motive=None, rahmen="linie", schraffur=0.25,
                    text="", schrift="normal", schreibweise="gross"):
    S = cfg.s(size)
    dk.check_choice("Form", form, FORMEN_ANHAENGER)
    _check_text(text)
    web = _web(cfg)
    W, H = (S, S) if form in ("rund", "herz") else (0.72 * S, S) if form in ("oval", "bogen") else (0.8 * S, S)
    outline = plate(form, W, H)
    part = Part(name, outline)
    r = max(1.5, min(2.5, 0.035 * S))
    top = max(y for _, y in outline)
    cx_top = 0.0
    if form == "herz":                                       # Herz: Loch in die linke Wölbung
        cx_top = -0.25 * W
        top = max(y for x, y in outline if x < -0.1 * W)
    hole = circle(cx_top, top - max(3.0, 0.07 * S) - r, r)
    if form == "herz":
        for _ in range(30):
            if min_distance(hole, outline) >= max(2.0, web):
                break
            hole = [(x, y - 0.5) for x, y in hole]
    part.add_hole(hole)
    notes: List[str] = []
    placed = resolve(motive or [], H / 2)
    cut_motifs(part, placed, cfg, web, notes)
    cv = dk.Canvas(part, margin=1.0, hole_margin=1.2, seed=cfg.seed)
    engrave_motifs(cv, placed, schraffur)
    _frame(cv, outline, rahmen, max(2.0, 0.05 * S), 0.03 * S, cfg.seed)
    _text(cv, text, 0.0, 0.17 * H, 0.66 * W, 0.15 * H, schrift, schreibweise)
    asm = Assembly(name, params=dict(size=S, form=form, motive=motif_summary(motive)))
    asm.parts.append(part)
    asm.notes += notes + [f"{name}: Band oder Kordel durch das Loch fädeln."]
    return asm


def build_untersetzer(cfg, name="untersetzer", size=100.0, form="rund", motive=None, rahmen="doppelt",
                      schraffur=0.3, text="", schrift="normal", schreibweise="gross"):
    S = cfg.s(size)
    dk.check_choice("Form", form, FORMEN_UNTERSETZER)
    _check_text(text)
    web = _web(cfg)
    outline = plate(form, S, S)
    part = Part(name, outline)
    notes: List[str] = []
    placed = resolve(motive or [], S / 2)
    if any(p.art == "schnitt" for p in placed):
        notes.append(f"{name}: Ausgeschnittene Motive lassen Flüssigkeit durch – für Untersetzer lieber gravieren.")
    cut_motifs(part, placed, cfg, web, notes)
    cv = dk.Canvas(part, margin=1.0, hole_margin=1.2, seed=cfg.seed)
    engrave_motifs(cv, placed, schraffur)
    _frame(cv, outline, rahmen, 0.04 * S, 0.03 * S, cfg.seed)
    _text(cv, text, 0.0, 0.17 * S, 0.6 * S, 0.12 * S, schrift, schreibweise)
    asm = Assembly(name, params=dict(size=S, form=form, motive=motif_summary(motive)))
    asm.parts.append(part)
    asm.notes += notes
    return asm


# ---------------------------------------------------------------------------
# Silhouette: das Motiv ist das Teil
# ---------------------------------------------------------------------------

def _to_raster(polys_mm: Sequence[Sequence[Point]], box, px: float):
    x0, y0, x1, y1 = box
    W = int((x1 - x0) / px) + 6
    H = int((y1 - y0) / px) + 6
    r = mt.Raster(W, H)

    def to_px(p):
        return [((x - x0) / px + 3, (y1 - y) / px + 3) for x, y in p]

    def back(p):                                     # raster_to_areas liefert y nach oben: y' = H - y_px
        return [((x - 3) * px + x0, y1 - (H - y - 3) * px) for x, y in p]
    return r, to_px, back


def build_silhouette(cfg, name="silhouette", motiv="katze", size=120.0, fuss="sockel", innen="schnitt",
                     sockel_text="", schrift="normal", schreibweise="gross"):
    T = cfg.T
    Hh = cfg.s(size)
    dk.check_choice("Fuß", fuss, FUSS)
    dk.check_choice("Innenformen", innen, INNEN)
    _check_text(sockel_text)
    m = mt.load(motiv)
    if not m["flaechen"]:
        raise ValueError(f"Motiv „{m.get('name', motiv)}“ besteht nur aus Linien – als Silhouette braucht es Flächen")
    web = _web(cfg)
    size = Hh                                                 # längere Seite des Motivs
    areas = [(mt.place(f["aussen"], 0.0, 0.0, size), [mt.place(h, 0.0, 0.0, size) for h in f["loecher"]])
             for f in m["flaechen"]]
    ymin = min(y for o, _ in areas for _, y in o)
    areas = [([(x, y - ymin) for x, y in o], [[(x, y - ymin) for x, y in h] for h in hs]) for o, hs in areas]
    lines = [[(x, y - ymin) for x, y in mt.place(li, 0.0, 0.0, size)] for li in m["linien"]]   # Gravurdetails
    notes: List[str] = []
    asm = Assembly(name, params=dict(motiv=motiv, size=Hh, fuss=fuss, innen=innen))
    extra: List[List[Point]] = []
    ring = None
    tw = 0.0
    if fuss == "sockel":
        xs_low = [x for o, _ in areas for x, y in o if y < 0.06 * Hh]
        sh = -(min(xs_low) + max(xs_low)) / 2                  # Fußleiste mittig unter die Standfläche
        areas = [([(x + sh, y) for x, y in o], [[(x + sh, y) for x, y in h] for h in hs]) for o, hs in areas]
        lines = [[(x + sh, y) for x, y in li] for li in lines]
        xa, xb = min(xs_low) + sh, max(xs_low) + sh
        bar_h = max(2.5, 1.2 * T, 0.03 * Hh)
        half = max((xb - xa) / 2, 2 * T + 5 + bar_h)
        xa, xb = -half, half
        extra.append(rect(xa, -bar_h * 0.6, xb - xa, bar_h))
        tw = min(max(0.6 * half, 4 * T), 2 * half - 2 * (bar_h + 3))
    elif fuss == "oese":
        top_y = max(y for o, _ in areas for _, y in o)
        x_top = max(((x, y) for o, _ in areas for x, y in o), key=lambda p: p[1])[0]
        ro = max(4.0, 0.05 * Hh)
        ring = (x_top, top_y + ro * 0.55, ro)
        extra.append(circle(*ring))
    # Motiv und Fuß/Öse über ein feines Raster vereinigen und dabei glätten: Kerben schmaler als der
    # Laserstrahl verschwinden (sonst verknotet sich die Kerf-Kontur)
    allp = [o for o, _ in areas] + extra
    x0 = min(x for p in allp for x, _ in p) - 1
    y0 = min(y for p in allp for _, y in p) - 1
    x1 = max(x for p in allp for x, _ in p) + 1
    y1 = max(y for p in allp for _, y in p) + 1
    px = max(0.08, max(x1 - x0, y1 - y0) / 1400)
    r, to_px, back = _to_raster(allp, (x0, y0, x1, y1), px)
    acc = r.fill([to_px(p) for o, hs in areas for p in [o] + hs], "evenodd")
    if extra:
        acc = acc.union(r.fill([to_px(p) for p in extra], "nonzero"))
    k = max(1, int(math.ceil((cfg.kerf_offset * 2 + 0.15) / px)))
    acc = acc.close(k)
    res = mt.raster_to_areas(acc, tol=0.5, smooth=1)
    areas = [(oriented(back(f["aussen"]), True), [oriented(back(h), False) for h in f["loecher"]]) for f in res]
    if fuss == "sockel":
        dy = -min(y for o, _ in areas for _, y in o)
        areas = [([(x, y + dy) for x, y in o], [[(x, y + dy) for x, y in h] for h in hs]) for o, hs in areas]
        lines = [[(x, y + dy) for x, y in li] for li in lines]
        areas = [([(x, 0.0 if y < 0.05 else y) for x, y in o], hs) for o, hs in areas]   # Unterkante exakt auf 0
        # Lücken zwischen Motiv-Unterkante und Fußleiste schließen (z. B. Gespenst-Saum)
        lim = max(bar_h * 2.5, 0.12 * Hh)
        areas = [(o, [h for h in hs if max(y for _, y in h) > lim]) for o, hs in areas]
    areas.sort(key=lambda a: -abs(signed_area(a[0])))
    if fuss != "keiner" and len(areas) > 1:
        notes.append(f"{name}: {len(areas) - 1} kleine Einzelteile hängen nicht am Motiv und fallen weg.")
        areas = areas[:1]
    parts = []
    for k, (outer, holes) in enumerate(areas):
        if abs(signed_area(outer)) < 4.0:
            continue
        pname = f"{name}_motiv" + (f"{k + 1}" if len(areas) > 1 else "")
        outline = oriented(tidy(outer, 0.05, 0.25), True)
        holes = [tidy(h, 0.05, 0.25) for h in holes]
        feats = []
        if fuss == "sockel" and k == 0:
            outline = _tab_into_bottom(outline, tw, T)
            feats = [tab_feature_at("fuss", -tw / 2, 0.0, tw, T)]
        part = Part(pname, outline, features=feats)
        cut_holes, eng = [], []
        for h in holes:
            if innen == "schnitt" and abs(signed_area(h)) >= 2.0 and min_distance(h, outline, limit=web) >= web:
                comp = offset_polygon(oriented(h, False), cfg.kerf_offset)
                if len(comp) >= 3 and polygon_ok(oriented(comp, True)):
                    cut_holes.append(h)
                    continue
            eng.append(h)
        for h in cut_holes:
            part.add_hole(h)
        if ring and k == 0:
            cx, cy, ro = ring
            ri = max(1.5, 0.45 * ro)
            c = circle(cx, cy, ri)
            if all(point_in_polygon(q, outline) for q in c) and min_distance(c, outline) >= min(web, ro - ri - 0.2) \
                    and all(min_distance(c, h) >= web for h in part.holes):
                part.add_hole(c)
            else:
                notes.append(f"{name}: Für die Öse war kein Platz für ein Loch.")
        if eng or (lines and k == 0):
            # Die Gravuren liegen innen im Material; den (bei feinen Motiven teuren) Innenversatz der
            # Außenkontur braucht es dafür nicht – Abstand zu den Schnitten halten die Sperrflächen.
            cv = dk.Canvas(part, margin=0.0, hole_margin=1.0, seed=cfg.seed)
            for o in [outline]:
                cv.block_strokes([(o, True)], 1.0)
            for h in eng:
                cv.draw(h, True)
            if k == 0:
                for li in lines:                              # Gravurdetails des Motivs (Gesicht, Falten …)
                    cv.draw(li)
        parts.append(part)
    if not parts:
        raise ValueError("Die Silhouette ist zu klein – größer machen")
    asm.parts += parts
    if fuss == "sockel":
        bw = max(x for x, _ in parts[0].outline) - min(x for x, _ in parts[0].outline)
        stand_base(asm, parts[0], "fuss", tw, cfg, max(0.5 * bw, tw / 2 + 12), max(0.18 * bw, 3.5 * T),
                   f"{name}_sockel", sockel_text or "", schrift, schreibweise)
        asm.notes.append(f"{name}: Figur in den Sockel stecken.")
    elif fuss == "oese":
        asm.notes.append(f"{name}: Band durch die Öse fädeln.")
    asm.notes += notes
    return asm


def _tab_into_bottom(outline: List[Point], tw: float, T: float) -> List[Point]:
    """Zapfen in die gerade Unterkante der Fußleiste setzen (Punktfolge auf y = 0 rund um x = 0)."""
    P = oriented(outline, True)
    n = len(P)
    on = [abs(y) < 1e-6 for _, y in P]
    if all(on):
        raise ValueError("Ungültige Kontur")
    k0 = next(i for i in range(n) if not on[i])
    P = P[k0:] + P[:k0]                                   # beginnt neben der Unterkante
    on = on[k0:] + on[:k0]
    i = 0
    while i < n:
        if on[i]:
            j = i
            while j + 1 < n and on[j + 1]:
                j += 1
            a, b = P[i], P[j]
            if a[0] < -tw / 2 - 1.0 and b[0] > tw / 2 + 1.0:
                return P[:i + 1] + [(-tw / 2, 0.0), (-tw / 2, -T), (tw / 2, -T), (tw / 2, 0.0)] + P[j:]
            i = j + 1
        else:
            i += 1
    raise ValueError("Für den Sockel fehlt eine gerade Unterkante – „Öse“ oder „nichts“ als Fuß wählen")
