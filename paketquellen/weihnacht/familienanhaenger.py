"""
Familienanhänger – Christbaumschmuck mit den Namen der Familie und der Jahreszahl.

Kugel, Stern, Herz oder Haus mit einem durchbrochenen Zierrand aus Schneeflocken, Tannenzweigen,
Sternen oder Perlen. Die Namen werden graviert oder als Schablonenschrift ausgeschnitten – kleine
Brücken halten dann die Innenformen von A, B, O & Co. Auf Wunsch ein Anhänger je Name.
"""
from __future__ import annotations

import math
import os
import sys
from typing import List, Sequence, Tuple

from steckwerk import Assembly, inset_polygon, oriented, point_in_polygon
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

FORMEN = [("kugel", "Kugel"), ("stern", "Stern"), ("herz", "Herz"), ("haus", "Haus")]
RAENDER = [("flocken", "Schneeflocken"), ("zweige", "Tannenzweige"), ("sterne", "Sterne"), ("perlen", "Perlenrand")]
ARTEN = [("gravur", "graviert"), ("schnitt", "ausgeschnitten (Schablonenschrift)")]
AUFTEILUNG = [("einer", "alle Namen auf einem Anhänger"), ("je_name", "ein Anhänger je Name")]
SCHRIFTEN = [("normal", "normal"), ("fett", "fett"), ("kursiv", "kursiv"), ("schmal", "schmal"), ("breit", "breit")]
SCHREIBWEISEN = [("gross", "GROSSBUCHSTABEN"), ("normal", "wie eingegeben (groß/klein)")]

INFO = dict(
    label="Familienanhänger",
    group="Weihnachtsdeko",
    desc="Christbaumanhänger mit den Namen der Familie und der Jahreszahl – Kugel, Stern, Herz oder Haus mit "
         "durchbrochenem Rand aus Schneeflocken, Tannenzweigen, Sternen oder Perlen.",
    params=[
        txt("namen", "Namen", "Anna|Ben|Clara|Paul", help="mehrere Namen mit | trennen", symbols=True,
            section="Schrift und Beschriftung"),
        txt("jahr", "Jahreszahl", "2026", maxlen=12, help="leer lassen für keine Jahreszahl",
            section="Schrift und Beschriftung"),
        txt("titel", "Überschrift", "", maxlen=30, help="optional, z. B. „Familie Huber“",
            section="Schrift und Beschriftung"),
        sel("aufteilung", "Aufteilung", AUFTEILUNG, "einer"),
        sel("form", "Form", FORMEN, "kugel"),
        num("groesse", "Höhe", 90, 50, 160, help="ohne Öse"),
        sel("rand", "Zierrand", RAENDER, "flocken"),
        sel("art", "Namen", ARTEN, "gravur", section="Schrift und Beschriftung"),
        sel("schrift", "Schrift", SCHRIFTEN, "normal", section="Schrift und Beschriftung",
            when={"art": ["gravur"]}),
        sel("schreibweise", "Schreibweise", SCHREIBWEISEN, "gross", section="Schrift und Beschriftung"),
        flag("innenlinie", "Gravierte Linie innen am Rand", True),
    ],
)

UEBERSETZUNG = {"en": {
    "Familienanhänger": "Family ornament", "Weihnachtsdeko": "Christmas decor",
    "Christbaumanhänger mit den Namen der Familie und der Jahreszahl – Kugel, Stern, Herz oder Haus mit "
    "durchbrochenem Rand aus Schneeflocken, Tannenzweigen, Sternen oder Perlen.":
        "Tree ornament with the family's names and the year – bauble, star, heart or house with an open border "
        "of snowflakes, fir sprigs, stars or pearls.",
    "Namen": "Names", "mehrere Namen mit | trennen": "separate several names with |",
    "Schrift und Beschriftung": "Font and lettering", "Jahreszahl": "Year",
    "leer lassen für keine Jahreszahl": "leave empty for no year", "Überschrift": "Heading",
    "optional, z. B. „Familie Huber“": "optional, e.g. “The Smiths”", "Aufteilung": "Layout",
    "alle Namen auf einem Anhänger": "all names on one ornament", "ein Anhänger je Name": "one ornament per name",
    "Form": "Shape", "Kugel": "Bauble", "Stern": "Star", "Herz": "Heart", "Haus": "House", "Höhe": "Height",
    "ohne Öse": "without the loop", "Zierrand": "Decorative border", "Schneeflocken": "Snowflakes",
    "Tannenzweige": "Fir sprigs", "Sterne": "Stars", "Perlenrand": "Pearl border", "graviert": "engraved",
    "ausgeschnitten (Schablonenschrift)": "cut out (stencil lettering)", "Schrift": "Font", "normal": "regular",
    "fett": "bold", "kursiv": "italic", "schmal": "narrow", "breit": "wide", "Schreibweise": "Letter case",
    "GROSSBUCHSTABEN": "CAPITALS", "wie eingegeben (groß/klein)": "as typed (upper/lower case)",
    "Gravierte Linie innen am Rand": "Engraved line inside the border",
    "Bitte mindestens einen Namen eingeben.": "Please enter at least one name.",
    "Aufhängen: Band oder Kordel durch die Öse ziehen.": "To hang: thread a ribbon or cord through the loop.",
    "Tipp: Ausgeschnittene Namen wirken mit farbigem Papier oder Folie dahinter besonders schön.":
        "Tip: Cut-out names look lovely with coloured paper or foil glued behind.",
    "Tipp: Für ausgeschnittene Namen sind 2–3 mm Holz ideal; feine Brücken vorsichtig auslösen.":
        "Tip: 2–3 mm wood is ideal for cut-out names; free the fine bridges carefully.",
}}


# --------------------------------------------------------------------------------------------------
# Formen: Höhe S, unten y = 0, mittig x = 0. Liefert (Umriss, Oberkante für die Öse, Textmitte)
# --------------------------------------------------------------------------------------------------

def _form(form: str, S: float):
    if form == "kugel":
        return oriented(K.circle(0, S / 2, S / 2, 160), True), S, (0.0, S / 2)
    if form == "stern":
        R = S / (1 + math.cos(math.pi / 5))
        cy = R * math.cos(math.pi / 5)
        st = K.star(0, cy, R, 0.6 * R, 5)
        st = oriented(W.abrunden(st, 0.07 * R, 6), True)
        return st, max(p[1] for p in st), (0.0, cy + 0.02 * R)
    if form == "herz":
        from models import _deko as dk
        h = dk.heart(0, S / 2, 1.08 * S, S)
        h = oriented(W.abrunden(h, 0.02 * S, 4), True)
        kerbe = min(p[1] for p in h if abs(p[0]) < 0.03 * S and p[1] > S / 2)
        return h, kerbe, (0.0, 0.60 * S)
    # Haus: Wand, Dach mit Überstand, Schornstein
    w, hw, ov = 0.78 * S, 0.56 * S, 0.07 * S
    pts = [(-w / 2, 0), (w / 2, 0), (w / 2, hw), (w / 2 + ov, hw - 0.6 * ov), (w / 2 + ov + 0.02 * S, hw + 0.03 * S)]
    k = (S - hw) / (w / 2 + ov)                            # Dachneigung
    cx0, cx1 = 0.20 * S, 0.30 * S
    pts += [(cx1, S - k * cx1), (cx1, 0.98 * S), (cx0, 0.98 * S), (cx0, S - k * cx0)]
    pts += [(0, S), (-w / 2 - ov - 0.02 * S, hw + 0.03 * S), (-w / 2 - ov, hw - 0.6 * ov), (-w / 2, hw)]
    pts = W.abrunden(pts, 0.012 * S, 4)
    return oriented(pts, True), S, (0.0, 0.40 * S)


# --------------------------------------------------------------------------------------------------
# Zierrand: Ornament entlang der Mittellinie des Bandes
# --------------------------------------------------------------------------------------------------

def _flocke(cx, cy, r, ang, w):
    f = K.Figur()
    for k in range(6):
        a = ang + k * math.pi / 3
        ca, sa = math.cos(a), math.sin(a)
        tip = (cx + ca * r, cy + sa * r)
        f.line([(cx, cy), tip], w)
        for u, L in ((0.52, 0.34), (0.78, 0.2)):
            p = (cx + ca * r * u, cy + sa * r * u)
            for sgn in (1, -1):
                b = a + sgn * math.pi / 3
                f.line([p, (p[0] + math.cos(b) * r * L, p[1] + math.sin(b) * r * L)], w * 0.95)
    f.add(K.circle(cx, cy, 1.25 * w, 16))
    return f


def _flocke_loch(cx, cy, r, ang, sl):
    """Schneeflocke als Schlitzmuster: sechs Arme mit je einem Zweigpaar (Schnittflächen)."""
    out = []
    for k in range(6):
        a = ang + k * math.pi / 3
        ca, sa = math.cos(a), math.sin(a)
        p0 = (cx + ca * max(0.36 * r, 2.7), cy + sa * max(0.36 * r, 2.7))
        out.append(K.stroke([p0, (cx + ca * r, cy + sa * r)], sl, sl * 0.85))
        p = (cx + ca * r * 0.66, cy + sa * r * 0.66)
        for sgn in (1, -1):
            b = a + sgn * math.radians(42)
            out.append(K.stroke([p, (p[0] + math.cos(b) * r * 0.32, p[1] + math.sin(b) * r * 0.32)], sl * 0.9, sl * 0.8))
    out.append(K.ellipse(cx, cy, 0.9, 0.9, 0.0, 6))
    return out


def _zweig_loch(cx, cy, L, ang, sl, nl):
    """Tannenzweig als Schlitzmuster: Mittelrippe mit schräg nach vorn stehenden Nadeln."""
    ca, sa = math.cos(ang), math.sin(ang)
    a = (cx - ca * L / 2, cy - sa * L / 2)
    b = (cx + ca * L / 2, cy + sa * L / 2)
    out = [K.stroke([a, b], sl, sl * 0.8)]
    pitch = sl + 1.9
    t = -0.32 * L
    k = 0
    while t < 0.40 * L:
        p = (cx + ca * t, cy + sa * t)
        for sgn in (1, -1):
            g = ang + sgn * math.radians(48)
            ln = nl * (1.0 - 0.45 * max(0.0, t / (0.5 * L)))
            out.append(K.stroke([p, (p[0] + math.cos(g) * ln, p[1] + math.sin(g) * ln)], sl * 0.95, sl * 0.8))
        t += pitch
        k += 1
    return out


def _rand(rand: str, mid, bw: float, w: float, seed: int):
    """Figur des Zierrands (Material im Band) oder Löcher (Liste) – je nach Art."""
    f = K.Figur()
    holes = []
    if rand == "flocken":                                  # Schneeflocken als feine Schlitze
        sl = max(1.1, w * 0.62)
        for i, ((x, y), (tx, ty)) in enumerate(W.entlang(mid, 0.8 * bw)):
            if i % 2 == 0 and 0.44 * bw >= 5.6:
                holes.append(_flocke_loch(x, y, 0.44 * bw, math.atan2(-tx, ty), sl))
            elif i % 2 == 0:
                holes.append([K.sparkle(x, y, 0.42 * bw, 0.22, 6, math.atan2(-tx, ty))])
            else:
                holes.append([K.sparkle(x, y, 0.22 * bw, 0.28, 4, math.atan2(ty, tx))])
    elif rand == "zweige":                                 # Girlande aus Zweigen und Beeren
        sl = max(1.0, w * 0.6)
        for i, ((x, y), (tx, ty)) in enumerate(W.entlang(mid, 0.95 * bw)):
            ang = math.atan2(ty, tx)
            if i % 3 == 2:
                for dx, dy in ((-0.12, 0.10), (0.12, 0.10), (0.0, -0.12)):
                    holes.append([K.circle(x + (dx * tx - dy * ty) * bw, y + (dx * ty + dy * tx) * bw, 0.095 * bw + 0.25, 12)])
            else:
                holes.append(_zweig_loch(x, y, 1.15 * bw, ang + (0.35 if i % 3 == 0 else -0.35), sl, 0.30 * bw))
    elif rand == "sterne":
        pts = W.entlang(mid, 0.95 * bw)
        for i, ((x, y), (tx, ty)) in enumerate(pts):
            if i % 2 == 0:
                holes.append([K.star(x, y, 0.36 * bw, 0.16 * bw, 5, math.atan2(-tx, ty))])
            else:
                holes.append([K.circle(x, y, 0.10 * bw + 0.2, 14)])
    else:                                                  # Perlen
        for i, ((x, y), _) in enumerate(W.entlang(mid, 0.62 * bw)):
            holes.append([K.circle(x, y, 0.20 * bw, 18)])
    return f, holes


# --------------------------------------------------------------------------------------------------
# Beschriftung
# --------------------------------------------------------------------------------------------------

def _zeilen_varianten(namen: List[str]) -> List[List[str]]:
    n = len(namen)
    out = [list(namen)]
    if n >= 2:
        out.append([" & ".join(namen)] if n == 2 else [" ".join(namen)])
    if n >= 3:
        k = (n + 1) // 2
        out.append([" ".join(namen[i:i + 2]) for i in range(0, n, 2)] if n > 3 else [" & ".join(namen[:2]), namen[2]])
    if n >= 5:
        out.append([" ".join(namen[i:i + 3]) for i in range(0, n, 3)])
    return out


def _block(zeilen: List[Tuple[str, float]], cap: float, gap: float, style: str, case: str):
    """Zeilen [(text, relative Größe)] untereinander, Mitte (0, 0). Liefert (Striche, Breite, Höhe)."""
    parts = []
    y = 0.0
    wmax = 0.0
    for i, (t, rel) in enumerate(zeilen):
        c = cap * rel
        st, w, h = W.textzeilen(t, c, gap * rel, style, case)
        if i:
            y -= 0.5 * cap * max(rel, 0.8)
        y -= c                                               # Grundlinie dieser Zeile
        parts += [[(x, yy + y) for x, yy in s] for s in st]
        wmax = max(wmax, w)
    if not parts:
        return [], 0.0, 0.0
    ys = [p[1] for s in parts for p in s]
    y0, y1 = min(ys), max(ys)
    return [[(x, yy - (y0 + y1) / 2) for x, yy in s] for s in parts], wmax, y1 - y0


def _passt(poly, x0, y0, x1, y1) -> bool:
    n = 8
    for i in range(n + 1):
        t = i / n
        for p in ((x0 + (x1 - x0) * t, y0), (x0 + (x1 - x0) * t, y1), (x0, y0 + (y1 - y0) * t), (x1, y0 + (y1 - y0) * t)):
            if not point_in_polygon(p, poly):
                return False
    return True


def _versuch(feld, center, zeilen, cap, gap, style, case):
    st, w, h = _block(zeilen, cap, gap(cap) if callable(gap) else gap, style, case)
    if not st:
        return None
    ys = [p[1] for p in feld]
    fh = max(ys) - min(ys)
    for dy in (0.0, 0.03, -0.03, 0.06, -0.06, 0.09, -0.09, 0.12, -0.12, 0.16, -0.16):
        cy = center[1] + dy * fh
        if _passt(feld, center[0] - w / 2, cy - h / 2, center[0] + w / 2, cy + h / 2):
            return [[(x + center[0], y + cy) for x, y in s] for s in st]
    return None


def _text_einpassen(feld, center, varianten, cap_max, cap_min, gap, style, case):
    """Größte Schrift (cap_min … cap_max) über alle Zeilenvarianten. Liefert (Striche, cap) oder None."""
    best = None
    for zeilen in varianten:
        if _versuch(feld, center, zeilen, cap_min, gap, style, case) is None:
            continue
        lo, hi = cap_min, cap_max
        if _versuch(feld, center, zeilen, hi, gap, style, case) is not None:
            lo = hi
        else:
            while hi - lo > 0.05:
                mid = (lo + hi) / 2
                if _versuch(feld, center, zeilen, mid, gap, style, case) is not None:
                    lo = mid
                else:
                    hi = mid
        if best is None or lo > best[0] * 1.04:
            best = (lo, zeilen)
    if best is None:
        return None
    return _versuch(feld, center, best[1], best[0], gap, style, case), best[0]


# --------------------------------------------------------------------------------------------------

def _anhaenger(cfg, name, form, S, rand, art, namen, jahr, titel, schrift, schreibweise, innenlinie, notes):
    web, kerf = cfg.min_web, cfg.kerf
    wm = W.wmin(cfg)
    U, top, center = _form(form, S)
    ro = max(1.6 * wm, 0.028 * S)                     # Außenrand
    bw = max(dict(kugel=0.15, herz=0.125, haus=0.125, stern=0.095)[form] * S, 6.0)   # Zierband
    aussen_in = inset_polygon(U, ro)
    feld = inset_polygon(U, ro + bw)
    if len(feld) < 3:
        raise ValueError("Für diesen Rand ist der Anhänger zu klein – Höhe vergrößern")
    mid = inset_polygon(U, ro + bw / 2)
    extra = []
    if form == "kugel":                               # Krone mit Öse
        cw, ch = 0.22 * S, 0.075 * S
        extra.append(K.rect(-cw / 2, top - 1.5, cw, ch + 1.5))
        extra.append(K.rect(-cw / 2 - 0.6, top + ch - 0.25 * ch, cw + 1.2, 0.25 * ch))
        top += ch
    r_oe = max(3.4, 0.045 * S)
    oe = (0.0, top + (0.35 * r_oe if form == "herz" else r_oe - 1.3))
    extra.append(K.circle(oe[0], oe[1], r_oe, 40))
    xs = [p[0] for p in U]
    ys = [p[1] for p in U]
    lw = E.Leinwand((min(xs) - 3, min(ys) - 3, max(xs) + 3, max(max(ys), oe[1] + r_oe) + 3), W.px_fuer(S) * 0.85)
    shape = lw.flaechen([U] + extra)
    w = wm + 0.15
    orn, loecher = _rand(rand, mid, bw, w, cfg.seed)
    zone_r = r_oe + 0.45 * bw
    loecher = [h for g in loecher if min(math.hypot(q[0] - oe[0], q[1] - oe[1]) for h in g for q in h) > zone_r + 0.3
               for h in g]
    band = E._andnot(lw.flaechen([aussen_in]), lw.flaechen([feld]))
    if True:
        mat = E._andnot(shape, E._and(lw.flaechen(loecher), band))
    mat = mat.union(E._and(lw.flaechen([K.circle(oe[0], oe[1], zone_r, 40)]), shape))
    mat = E._andnot(mat, lw.flaechen([K.circle(oe[0], oe[1], r_oe - max(wm + 0.4, 1.6), 32)]))

    # Text
    zeilen_v = []
    nam = [n.strip() for n in namen if n.strip()]
    for v in _zeilen_varianten(nam):
        z = ([(titel.strip(), 0.72)] if titel.strip() else []) + [(t, 1.0) for t in v]
        if jahr.strip():
            j = jahr.strip()
            if art == "schnitt":
                z.append((j, 0.8))
            else:
                z.append(("★ " + j + " ★" if len(j) <= 6 else j, 0.62))
        zeilen_v.append(z)
    m_txt = max(1.6, 0.035 * S)
    text_feld = inset_polygon(feld, m_txt + (1.2 if innenlinie else 0.0))
    if len(text_feld) < 3:
        raise ValueError("Für den Text bleibt zu wenig Platz – Höhe vergrößern")
    cap_max = 0.16 * S
    fehler = ("Die Namen passen nicht auf den Anhänger – kürzer fassen, „ein Anhänger je Name“ wählen oder "
              "die Höhe vergrößern")
    if art == "schnitt":
        res = None
        for cap_try in (cap_max, 0.85 * cap_max, 0.72 * cap_max, 0.6 * cap_max, 8.0):
            sw = max(1.1, kerf + 0.9, 0.1 * cap_try)
            def gap(c, sw=sw):
                return max(0.0, sw + wm + 0.45 - 0.217 * c)
            r = _text_einpassen(text_feld, center, zeilen_v, cap_try, 8.0, gap, "breit", schreibweise)
            if r is not None and r[1] >= 0.75 * cap_try:
                res = r
                break
            res = res or r
        if res is None:
            raise ValueError("Die Namen passen als ausgeschnittene Schrift nicht auf den Anhänger – kürzer fassen, "
                             "„ein Anhänger je Name“ oder „graviert“ wählen, oder die Höhe vergrößern")
        strokes, cap = res
        mat = E._andnot(mat, W.schablone(lw, strokes, sw, wm + 0.35, cap))
    else:
        res = _text_einpassen(text_feld, center, zeilen_v, cap_max, 3.0, 0.0, schrift, schreibweise)
        if res is None:
            raise ValueError(fehler)
        strokes, cap = res
    part = E.teil_aus_raster(name, lw, mat, web, kerf, notes)
    lines = []
    if innenlinie:
        il = inset_polygon(feld, 1.0)
        if len(il) >= 3:
            lines.append((il, True))
    if art != "schnitt":
        lines += [(s, False) for s in strokes]
    W.gravur(part, lines, rand=0.6)
    return part


def build(cfg, name: str = "familienanhaenger", namen: str = "Anna|Ben|Clara|Paul", jahr: str = "2026",
          titel: str = "", aufteilung: str = "einer", form: str = "kugel", groesse: float = 90.0,
          rand: str = "flocken", art: str = "gravur", schrift: str = "normal", schreibweise: str = "gross",
          innenlinie: bool = True):
    from models._font import unsupported
    for key, val, opts in (("Form", form, FORMEN), ("Zierrand", rand, RAENDER), ("Namen", art, ARTEN),
                           ("Aufteilung", aufteilung, AUFTEILUNG), ("Schrift", schrift, SCHRIFTEN),
                           ("Schreibweise", schreibweise, SCHREIBWEISEN)):
        if val not in dict(opts):
            raise ValueError(f"{key}: unbekannte Auswahl {val!r}")
    liste = [n.strip() for n in (namen or "").replace("\n", "|").split("|") if n.strip()]
    if not liste:
        raise ValueError("Bitte mindestens einen Namen eingeben.")
    bad = unsupported("".join(liste) + (jahr or "") + (titel or ""))
    if bad:
        raise ValueError(f"Zeichen {''.join(bad)!r} gibt es in der Schrift nicht")
    if len(liste) > 12:
        raise ValueError("Höchstens 12 Namen – für mehr „ein Anhänger je Name“ wählen")
    S = cfg.s(groesse)
    if S < 40:
        raise ValueError("Der Anhänger ist zu klein – mindestens 40 mm Höhe")
    asm = Assembly(name, params=dict(namen=namen, jahr=jahr, titel=titel, aufteilung=aufteilung, form=form,
                                     groesse=S, rand=rand, art=art))
    notes: List[str] = []
    gruppen = [liste] if aufteilung == "einer" else [[n] for n in liste]
    used = set()
    for i, g in enumerate(gruppen):
        tag = f"{form}_" + "".join(c for c in g[0].lower() if c.isalnum())[:12] if aufteilung != "einer" else form
        if tag in used or not tag.strip("_"):
            tag = f"{form}_{i + 1}"
        used.add(tag)
        asm.parts.append(_anhaenger(cfg, tag, form, S, rand, art, g, jahr or "", titel or "", schrift,
                                    schreibweise, innenlinie, notes))
    for t in dict.fromkeys(notes):
        asm.notes.append(t)
    asm.notes.append("Aufhängen: Band oder Kordel durch die Öse ziehen.")
    if art == "schnitt":
        asm.notes.append("Tipp: Ausgeschnittene Namen wirken mit farbigem Papier oder Folie dahinter besonders schön.")
        if cfg.T > 3.1:
            asm.notes.append("Tipp: Für ausgeschnittene Namen sind 2–3 mm Holz ideal; feine Brücken vorsichtig auslösen.")
    return asm
