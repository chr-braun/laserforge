"""
Flaschenschild – Preisschild, das über den Flaschenhals gehängt wird (oder an einer Kordel hängt).

Oben das Logo (eigenes Motiv aus „Motive importieren“, SVG oder PNG) oder eine Kopfzeile, darunter
Produktname, Preis inkl. MwSt. und der Grundpreis je Liter, den Steckwerk aus Preis und Inhalt
selbst ausrechnet. Mit einer Preisliste (je Zeile ein Produkt) entstehen alle Schilder auf einmal.
"""
from __future__ import annotations

import re
from typing import List, Optional, Tuple

from steckwerk import Assembly, Part, circle, min_distance, point_in_polygon
from models import _deko as dk
from models._font import STYLES, fit_text, unsupported
from models import motivvorlagen as mv
from pakete import flag, motiv, num, sel, txt

FORMEN = [("bogen", "oben rund"), ("abgerundet", "Rechteck, abgerundet"), ("etikett", "Etikett (Ecken schräg)")]
HALTERUNG = [("hals", "Loch für den Flaschenhals"), ("kordel", "kleines Loch für eine Kordel")]
LOGO = [("motiv", "Logo (eigenes Motiv)"), ("text", "Kopfzeile als Text"), ("kein", "nichts")]
LOGO_ART = [("flaeche", "flächig graviert"), ("umriss", "Umriss graviert"), ("schnitt", "ausgeschnitten")]
RAHMEN = [("keine", "kein Rahmen"), ("linie", "Linie"), ("doppelt", "doppelte Linie"), ("punkte", "Punkte")]
MWST = [("inkl", "inkl. MwSt."), ("19", "inkl. 19 % MwSt."), ("7", "inkl. 7 % MwSt.")]
SCHRIFT = "Schrift und Gestaltung"

INFO = dict(
    label="Flaschenschild",
    group="Verkauf",
    desc="Preisschild für die Flasche: Logo, Name, Preis inkl. MwSt. und Grundpreis je Liter – über den "
         "Flaschenhals gehängt oder an einer Kordel. Mit einer Preisliste alle Schilder auf einmal.",
    params=[
        txt("name_produkt", "Produkt", "Riesling|Spätlese 2023", "| = neue Zeile", 60),
        num("preis", "Preis inkl. MwSt.", 12.90, 0.10, 9999, step=0.01, unit="€"),
        num("inhalt", "Inhalt", 0.75, 0.02, 10, step=0.01, unit="l"),
        txt("liste", "Preisliste (mehrere Schilder)", "",
            "je Zeile ein Produkt: Name; Preis; Inhalt – z. B. „Grauburgunder 2023; 14,50; 0,75“. "
            "Leer = nur das Schild oben.", 2000, rows=5),
        sel("logo", "Oben", LOGO, "motiv"),
        motiv("logo_motiv", "Logo", "glocke", "eigenes Logo über „Motive importieren“ (SVG oder PNG) laden",
              when={"logo": ["motiv"]}),
        sel("logo_art", "Logo als", LOGO_ART, "flaeche", when={"logo": ["motiv"]}),
        txt("kopfzeile", "Kopfzeile", "Weinhaus", "z. B. dein Ladenname", 40, when={"logo": ["text"]}),
        sel("halterung", "Aufhängung", HALTERUNG, "hals"),
        num("hals", "Halsloch Ø", 33, 18, 45, help="Weinflasche ca. 31–33 mm, Sektflasche ca. 30 mm, Spirituosen "
            "oft 28–32 mm – über den Verschluss messen", when={"halterung": ["hals"]}),
        num("breite", "Breite", 55, 35, 120),
        num("hoehe", "Höhe", 110, 50, 200),
        sel("form", "Form", FORMEN, "bogen"),
        sel("mwst", "MwSt.-Zeile", MWST, "inkl", section=SCHRIFT),
        flag("grundpreis", "Grundpreis je Liter zeigen", True, section=SCHRIFT),
        sel("rahmen", "Rahmen", RAHMEN, "linie", section=SCHRIFT),
        sel("schrift", "Schrift", [(s, s) for s in STYLES], "normal", section=SCHRIFT),
    ],
)

UEBERSETZUNG = {"en": {
    "Flaschenschild": "Bottle tag", "Verkauf": "Shop",
    "Preisschild für die Flasche: Logo, Name, Preis inkl. MwSt. und Grundpreis je Liter – über den "
    "Flaschenhals gehängt oder an einer Kordel. Mit einer Preisliste alle Schilder auf einmal.":
        "Price tag for a bottle: logo, name, price incl. VAT and unit price per litre – hung over the bottle "
        "neck or on a cord. With a price list, all tags at once.",
    "Produkt": "Product", "| = neue Zeile": "| = new line", "Preis inkl. MwSt.": "Price incl. VAT",
    "Inhalt": "Volume", "Preisliste (mehrere Schilder)": "Price list (several tags)",
    "je Zeile ein Produkt: Name; Preis; Inhalt – z. B. „Grauburgunder 2023; 14,50; 0,75“. "
    "Leer = nur das Schild oben.":
        "one product per line: name; price; volume – e.g. “Pinot Gris 2023; 14.50; 0.75”. Empty = only the tag above.",
    "Oben": "Top", "Logo (eigenes Motiv)": "Logo (own motif)", "Kopfzeile als Text": "Header as text",
    "nichts": "nothing", "Logo": "Logo",
    "eigenes Logo über „Motive importieren“ (SVG oder PNG) laden": "load your own logo via “Import motifs” (SVG or PNG)",
    "Logo als": "Logo as", "flächig graviert": "filled engraving", "Umriss graviert": "outline engraved",
    "ausgeschnitten": "cut out", "Kopfzeile": "Header", "z. B. dein Ladenname": "e.g. your shop name",
    "Aufhängung": "Hanging", "Loch für den Flaschenhals": "Hole for the bottle neck",
    "kleines Loch für eine Kordel": "small hole for a cord", "Halsloch Ø": "Neck hole Ø",
    "Weinflasche ca. 31–33 mm, Sektflasche ca. 30 mm, Spirituosen oft 28–32 mm – über den Verschluss messen":
        "wine bottle approx. 31–33 mm, sparkling approx. 30 mm, spirits often 28–32 mm – measure over the closure",
    "Breite": "Width", "Höhe": "Height", "Form": "Shape", "oben rund": "round top",
    "Rechteck, abgerundet": "rounded rectangle", "Etikett (Ecken schräg)": "label (bevelled corners)",
    "MwSt.-Zeile": "VAT line", "inkl. MwSt.": "incl. VAT", "inkl. 19 % MwSt.": "incl. 19 % VAT",
    "inkl. 7 % MwSt.": "incl. 7 % VAT", "Grundpreis je Liter zeigen": "Show unit price per litre",
    "Rahmen": "Frame", "kein Rahmen": "no frame", "Linie": "line", "doppelte Linie": "double line",
    "Punkte": "dots", "Schrift": "Font", "Schrift und Gestaltung": "Font and design",
}}


def euro(x: float) -> str:
    """12.9 → „12,90 €“, 1234.5 → „1.234,50 €“."""
    s = f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return s + " €"


def liter(x: float) -> str:
    s = f"{x:.3f}".rstrip("0").rstrip(".")
    if "." not in s:
        s += ",0"
    return s.replace(".", ",") + " l"


def zahl(s: str, was: str, zeile: int) -> float:
    t = s.strip().replace("€", "").replace("EUR", "").replace("l", "").replace(" ", "")
    if re.fullmatch(r"\d{1,3}(\.\d{3})+(,\d+)?", t):        # 1.234,50
        t = t.replace(".", "")
    t = t.replace(",", ".")
    try:
        v = float(t)
    except ValueError:
        raise ValueError(f"Preisliste Zeile {zeile}: {was} „{s.strip()}“ ist keine Zahl")
    if v <= 0:
        raise ValueError(f"Preisliste Zeile {zeile}: {was} muss größer als 0 sein")
    return v


def produkte(name: str, preis: float, inhalt: float, liste: str) -> List[Tuple[str, float, float]]:
    rows = [l for l in (liste or "").replace("\r", "").split("\n") if l.strip()]
    if not rows:
        return [(name, float(preis), float(inhalt))]
    out = []
    for i, r in enumerate(rows, 1):
        f = [x for x in r.split(";")]
        if len(f) < 2:
            raise ValueError(f"Preisliste Zeile {i}: bitte „Name; Preis; Inhalt“ – Semikolon zwischen den Angaben")
        n = f[0].strip()
        if not n:
            raise ValueError(f"Preisliste Zeile {i}: der Name fehlt")
        p = zahl(f[1], "Preis", i)
        v = zahl(f[2], "Inhalt", i) if len(f) > 2 and f[2].strip() else float(inhalt)
        if v > 20:                                           # 750 (ml) statt 0,75
            v = v / 1000.0
        out.append((n, p, v))
    if len(out) > 40:
        raise ValueError("Höchstens 40 Schilder auf einmal – Liste aufteilen")
    return out


def _umriss(form: str, W: float, H: float, tol: float):
    if form == "bogen":
        r = W / 2
        return dk.ccw_arch(W, H, tol) if hasattr(dk, "ccw_arch") else \
            [(-W / 2, 0.0), (W / 2, 0.0)] + dk.arc_points(0.0, H - r, r, 0.0, 3.141592653589793, tol)
    if form == "etikett":
        c = min(W, H) * 0.22
        return [(-W / 2 + 3, 0.0), (W / 2 - 3, 0.0), (W / 2, 3.0), (W / 2, H - c), (W / 2 - c, H),
                (-W / 2 + c, H), (-W / 2, H - c), (-W / 2, 3.0)]
    return dk.rounded_rect(-W / 2, 0.0, W / 2, H, min(6.0, W * 0.12), tol)


def _schild(cfg, nm: str, produkt: str, preis: float, inhalt: float, kw, notes: List[str]) -> Part:
    tol, web = cfg.arc_tolerance, max(cfg.min_web, 1.2)
    W, H = cfg.s(kw["breite"]), cfg.s(kw["hoehe"])
    out = _umriss(kw["form"], W, H, tol)
    part = Part(nm, out)
    rand = max(3.0, W * 0.06)
    if kw["halterung"] == "hals":
        rh = kw["hals"] / 2
        if W / 2 - rh < max(5.0, 2 * web + 2):
            raise ValueError(f"Für ein Halsloch von {kw['hals']:g} mm muss das Schild mindestens "
                             f"{kw['hals'] + 2 * max(5.0, 2 * web + 2):.0f} mm breit sein")
        cy = H - W / 2
        hole = circle(0.0, cy, rh, tol)
        oben = cy - rh - 2.5
    else:
        rh = 2.5
        cy = H - rand - rh - 2
        hole = circle(0.0, cy, rh, tol)
        oben = cy - rh - 2.5
    if min_distance(hole, out) < max(web * 2, 4.0):
        raise ValueError("Das Loch sitzt zu nah am Rand – Schild breiter oder höher machen")
    part.add_hole(hole)
    unten = rand
    innen = rand + (2.0 if kw["rahmen"] != "keine" else 0.5)
    x0, x1 = -W / 2 + innen, W / 2 - innen
    h = oben - unten
    if h < 30:
        raise ValueError("Unter dem Loch bleibt zu wenig Platz für Name und Preis – Schild höher machen")
    zeilen = []                                              # (Text, Anteil an der Höhe, Schriftstil)
    st = kw["schrift"]
    if kw["logo"] == "text" and kw["kopfzeile"].strip():
        zeilen.append(("kopf", kw["kopfzeile"], 0.12))
    elif kw["logo"] == "motiv":
        zeilen.append(("logo", "", 0.24))
    zeilen.append(("name", produkt, 0.26 if "|" in produkt else 0.18))
    zeilen.append(("preis", euro(preis), 0.19))
    zeilen.append(("mwst", dict(MWST)[kw["mwst"]], 0.075))
    if kw["grundpreis"]:
        zeilen.append(("gp", f"{liter(inhalt)} ({euro(preis / inhalt)}/l)", 0.085))
    summe = sum(z[2] for z in zeilen)
    luecke = (1.0 - summe) / (len(zeilen) + 1) if summe < 1 else 0.02
    cv = dk.Canvas(part, margin=1.0, hole_margin=1.5, seed=cfg.seed)
    y = oben
    placed = []
    for art, text, anteil in zeilen:
        y -= luecke * h
        bh = anteil * h
        yc = y - bh / 2
        if art == "logo":
            g = min(bh, (x1 - x0) * 0.8)
            placed = mv.resolve([dict(id=kw["logo_motiv"], x=0.0, y=yc, groesse=g, art=kw["logo_art"])], 0.0)
            if kw["logo_art"] == "schnitt":
                mv.cut_motifs(part, placed, cfg, web, notes)
        else:
            cap = {"preis": 0.95, "name": 0.75, "kopf": 0.8}.get(art, 0.95) * bh
            stil = "fett" if art == "preis" and st == "normal" else st
            try:
                strokes, _ = fit_text(text, 0.0, yc, x1 - x0, bh, min_h=2.2 if art in ("mwst", "gp") else 2.8,
                                      max_cap=min(cap, bh / (1 + 1.55 * text.count("|"))), style=stil,
                                      case="normal")
            except ValueError:
                raise ValueError(f"„{text.replace('|', ' ')}“ passt nicht aufs Schild – kürzer fassen oder "
                                 "Schild größer machen")
            for s in strokes:
                cv.draw(s, min_len=0.05)
        y -= bh
    if placed and kw["logo_art"] != "schnitt":
        mv.engrave_motifs(cv, placed, 0.3)
    if kw["rahmen"] != "keine":
        mv._frame(cv, out, kw["rahmen"], max(2.0, rand * 0.6), max(1.2, W * 0.025), cfg.seed)
    return part


def build(cfg, name: str = "flaschenschild", name_produkt: str = "Riesling|Spätlese 2023", preis: float = 12.90,
          inhalt: float = 0.75, liste: str = "", logo: str = "motiv", logo_motiv: str = "glocke",
          logo_art: str = "flaeche", kopfzeile: str = "Weinhaus", halterung: str = "hals", hals: float = 33.0,
          breite: float = 55.0, hoehe: float = 110.0, form: str = "bogen", mwst: str = "inkl",
          grundpreis: bool = True, rahmen: str = "linie", schrift: str = "normal"):
    for key, val, opts in (("Form", form, FORMEN), ("Aufhängung", halterung, HALTERUNG), ("Oben", logo, LOGO),
                           ("Logo als", logo_art, LOGO_ART), ("Rahmen", rahmen, RAHMEN), ("MwSt.-Zeile", mwst, MWST)):
        dk.check_choice(key, val, opts)
    liste_p = produkte(name_produkt, preis, inhalt, liste)
    for n, _, _ in liste_p:
        bad = unsupported(n + (kopfzeile if logo == "text" else ""))
        if bad:
            raise ValueError(f"Diese Zeichen kann die Gravurschrift nicht: {' '.join(bad)}")
    kw = dict(breite=breite, hoehe=hoehe, form=form, halterung=halterung, hals=hals, logo=logo,
              logo_motiv=logo_motiv, logo_art=logo_art, kopfzeile=kopfzeile, mwst=mwst, grundpreis=grundpreis,
              rahmen=rahmen, schrift=schrift)
    notes: List[str] = []
    asm = Assembly(name, params=dict(produkte=len(liste_p), breite=breite, hoehe=hoehe, hals=hals))
    namen = set()
    for i, (n, p, v) in enumerate(liste_p):
        base = re.sub(r"[^a-z0-9]+", "_", n.lower().replace("|", " ").replace("ä", "ae").replace("ö", "oe")
                      .replace("ü", "ue").replace("ß", "ss")).strip("_")[:24] or f"schild{i + 1}"
        nm = base if base not in namen else f"{base}_{i + 1}"
        namen.add(nm)
        asm.parts.append(_schild(cfg, nm, n, p, v, kw, notes))
    asm.notes += sorted(set(notes))
    if halterung == "hals":
        asm.notes.append(f"Halsloch {hals:g} mm – vorher an einer Flasche über den Verschluss messen. "
                         "Schild von oben über den Flaschenhals schieben.")
    asm.notes.append("Grundpreis je Liter wird aus Preis und Inhalt berechnet (Preisangabenverordnung). "
                     "Tipp: dünnes Sperrholz (1,5–3 mm), Gravur dunkel mit wenig Leistung.")
    return asm
