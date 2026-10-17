"""
Backstube – Paket „Wichtel“.

Weihnachtsbäckerei im Wichtelformat: Backblech mit Griffen, Backbrett, Teigrolle, Ausstecher (Herz, Stern,
Tanne) als Ringe, Plätzchen mit Zuckerguss und Lebkuchenmänner. Alles flache Teile zum Bemalen und
Aufleimen – auf den Wichteltisch, ins Wichtelzimmer oder an den Lebkuchenstand.
"""
import importlib.util
import math
import os

from steckwerk import Assembly, offset_polygon, oriented
from pakete import flag, integer, num

_spec = importlib.util.spec_from_file_location("swpaket_wichtel__lade_back",
                                               os.path.join(os.path.dirname(os.path.abspath(__file__)), "_lade.py"))
_m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_m)
M = _m.markt()
Z, K = M.Z, M.K

UEBERSETZUNG = {"en": {
    "Backstube": "Bakery",
    "Weihnachtsbäckerei im Wichtelformat: Backblech, Backbrett, Teigrolle, Ausstecher, Plätzchen mit Zuckerguss "
    "und Lebkuchenmänner – zum Bemalen und Aufleimen.":
        "Christmas bakery in elf size: baking tray, pastry board, rolling pin, cookie cutters, iced cookies and "
        "gingerbread men – to paint and glue on.",
    "Blechbreite": "Tray width", "Plätzchen": "Cookies", "Ausstecher": "Cookie cutters",
    "Lebkuchenmänner": "Gingerbread men", "Backbrett und Teigrolle": "Pastry board and rolling pin",
}}

INFO = dict(
    label="Backstube", group="Wichtel",
    desc="Weihnachtsbäckerei im Wichtelformat: Backblech, Backbrett, Teigrolle, Ausstecher, Plätzchen mit Zuckerguss "
         "und Lebkuchenmänner – zum Bemalen und Aufleimen.",
    params=[
        num("groesse", "Blechbreite", 42, 25, 150),
        integer("plaetzchen", "Plätzchen", 6, 0, 12),
        integer("maenner", "Lebkuchenmänner", 2, 0, 6),
        flag("ausstecher", "Ausstecher", True),
        flag("brett", "Backbrett und Teigrolle", True),
    ],
)
INFO["params"] = M.mit_massstab("backstube", INFO["params"])
UEBERSETZUNG["en"].update(M.EN)

FORMEN = ["stern", "herz", "tanne", "kreis", "mond", "glocke"]


def _form(art: str, g: float):
    """Plätzchen-/Ausstecherform der Größe ≈ g um (0, 0)."""
    if art == "stern":
        return K.star(0, -g * 0.03, g * 0.52, g * 0.24, 5)
    if art == "herz":
        return Z.herz(0, 0, g)
    if art == "tanne":
        return Z.abrunden([(-g * 0.42, -g * 0.36), (-g * 0.08, -g * 0.36), (-g * 0.08, -g * 0.5), (g * 0.08, -g * 0.5),
                           (g * 0.08, -g * 0.36), (g * 0.42, -g * 0.36), (g * 0.2, -g * 0.05), (g * 0.32, -g * 0.05),
                           (0, g * 0.5), (-g * 0.32, -g * 0.05), (-g * 0.2, -g * 0.05)], g * 0.03, 2)
    if art == "mond":
        f = K.Figur().add(K.circle(0, 0, g * 0.46, 40)).cut(K.circle(g * 0.22, g * 0.14, g * 0.38, 40))
        return f
    if art == "glocke":
        pts = K.spline([(0, g * 0.5), (g * 0.2, g * 0.38), (g * 0.24, g * 0.0), (g * 0.42, -g * 0.36),
                        (0, -g * 0.36), (-g * 0.42, -g * 0.36), (-g * 0.24, g * 0.0), (-g * 0.2, g * 0.38)],
                       closed=True, n=8)
        return K.Figur().add(pts, K.circle(0, -g * 0.42, g * 0.1, 20))
    return K.circle(0, 0, g * 0.46, 40)


def _fig(f):
    return f if isinstance(f, K.Figur) else K.Figur().add(f)


def _kontur(f):
    """Hauptkontur (erste hinzugefügte Fläche) für Zuckerguss."""
    return f.ops[0][1] if isinstance(f, K.Figur) else f


def build(cfg, name="backstube", groesse=42.0, plaetzchen=6, maenner=2, ausstecher=True, brett=True,
          massstab="wichtel", wichtel=70.0):
    if massstab == "wichtel":
        groesse = M.mass("backstube", wichtel, INFO["params"], cfg)["groesse"]
    W = cfg.s(groesse)
    w = Z.wmin(cfg)
    notes = []
    asm = Assembly(name, params=dict(groesse=W))

    # Backblech mit Griffen und hochgezogenem Rand (graviert)
    Hb = W * 0.7
    blech = Z.Figur().add(Z.abrunden(K.rect(-W / 2, -Hb / 2, W, Hb), W * 0.05, 4))
    gb, gh = max(Hb * 0.4, 3 * w + 4), max(W * 0.08, 2 * w + 2.5)      # Griffe an den Schmalseiten
    for sg in (-1, 1):
        blech.add(Z.abrunden(K.rect(min(sg * (W / 2 - 0.6), sg * (W / 2 + gh)), -gb / 2, gh + 0.6, gb), gh * 0.45, 4))
        if gh * 0.36 >= 1.0:                                # Griffloch
            blech.cut(Z.abrunden(K.rect(sg * (W / 2 + gh / 2) - gh * 0.18, -gb / 2 + w * 1.2, gh * 0.36,
                                        gb - w * 2.4), gh * 0.15, 3))
    t = Z.figur_teil(cfg, "backblech", blech, notes)
    rnd = Z.abrunden(K.rect(-W / 2 + 2.0, -Hb / 2 + 2.0, W - 4.0, Hb - 4.0), W * 0.035, 4)
    Z.gravur(t, [(rnd, True)], rand=0.6)
    asm.parts.append(t)

    # Plätzchen
    g = max(W * 0.2, 5 * w)
    for k in range(int(plaetzchen)):
        art = FORMEN[k % len(FORMEN)]
        f = _fig(_form(art, g))
        t = Z.figur_teil(cfg, f"plaetzchen{k + 1}_{art}", f, notes)
        lin = M.zuckerguss(_kontur(f), max(0.8, g * 0.08), max(0.25, g * 0.025), max(1.2, g * 0.12))
        if art in ("kreis", "herz"):
            lin += [(K.circle(0, 0, g * 0.07, 12), True)]
        if art == "tanne":
            lin = [([(-g * 0.25, -g * 0.22), (g * 0.25, -g * 0.12)], False),
                   ([(-g * 0.14, g * 0.06), (g * 0.14, g * 0.16)], False)]
        Z.gravur(t, lin, rand=0.45)
        asm.parts.append(t)

    # Lebkuchenmänner
    gm = max(W * 0.38, 7 * w)
    for k in range(int(maenner)):
        t = Z.figur_teil(cfg, f"lebkuchenmann{k + 1}", M.lebkuchenmann(0, 0, gm), notes)
        Z.gravur(t, M.lebkuchenmann_gravur(0, 0, gm), rand=0.4)
        asm.parts.append(t)

    # Ausstecher: Ringe in Herz-, Stern- und Tannenform
    if ausstecher:
        ga = max(W * 0.42, 10 * w)
        wr = max(w * 1.1, 1.6)
        for art in ("herz", "stern", "tanne"):
            if art == "tanne":                              # Ausstecher ohne Stamm
                aussen = Z.abrunden([(-ga * 0.42, -ga * 0.4), (ga * 0.42, -ga * 0.4), (ga * 0.2, -ga * 0.08),
                                     (ga * 0.32, -ga * 0.08), (0, ga * 0.5), (-ga * 0.32, -ga * 0.08),
                                     (-ga * 0.2, -ga * 0.08)], ga * 0.03, 2)
            else:
                aussen = list(_form(art, ga))
            # Ring = Form minus die um die Wandstärke geschrumpfte Form (im Raster, klappt auch an Spitzen)
            E = Z.E
            xs_, ys_ = [p[0] for p in aussen], [p[1] for p in aussen]
            lw = E.Leinwand((min(xs_) - 3, min(ys_) - 3, max(xs_) + 3, max(ys_) + 3), 0.06)
            voll = lw.flaechen([aussen])
            ring = E._andnot(voll, voll.erode(lw.px_fuer(wr)))
            asm.parts.append(E.teil_aus_raster(f"ausstecher_{art}", lw, ring, cfg.min_web, cfg.kerf, notes))

    # Backbrett mit Griffloch und Teigrolle
    if brett:
        Bb, Hbb = W * 0.95, W * 0.62
        gr = max(W * 0.12, 3 * w + 2)
        f = K.Figur().add(Z.abrunden(K.rect(-Bb / 2, -Hbb / 2, Bb, Hbb), W * 0.06, 4))
        f.add(Z.abrunden(K.rect(Bb / 2 - 1, -gr * 0.6, gr * 1.4, gr * 1.2), gr * 0.5, 5))
        f.cut(K.circle(Bb / 2 + gr * 0.35, 0, max(gr * 0.25, 1.0), 20))
        t = Z.figur_teil(cfg, "backbrett", f, notes)
        Z.gravur(t, M.bretter(-Bb / 2 + 1.5, -Hbb / 2 + 1.5, Bb / 2 - 1.5, Hbb / 2 - 1.5, 3, quer=True), rand=0.7)
        asm.parts.append(t)
        L, d = W * 0.78, max(W * 0.13, 2 * w + 1.5)
        hg, hd = L * 0.16, max(d * 0.45, w + 0.6)
        f = K.Figur().add(Z.abrunden(K.rect(-L / 2, -d / 2, L, d), d * 0.25, 3))
        for sg in (-1, 1):
            f.add(K.rect(min(sg * (L / 2 - 0.5), sg * (L / 2 + hg * 0.55)), -hd / 2, hg * 0.55 + 0.5, hd))
            f.add(K.ellipse(sg * (L / 2 + hg * 0.75), 0, hg * 0.3, hd * 0.75, 0, 24))
        t = Z.figur_teil(cfg, "teigrolle", f, notes)
        Z.gravur(t, [([(-L / 2 + 1.2, d * 0.15), (L / 2 - 1.2, d * 0.15)], False)], rand=0.6)
        asm.parts.append(t)

    asm.notes.append("Alles flach bemalen und aufleimen: Plätzchen aufs Blech, Ausstecher und Teigrolle aufs "
                     "Backbrett, Lebkuchenmänner auf den Tisch oder an den Lebkuchenstand.")
    asm.notes += list(dict.fromkeys(notes))
    return asm
