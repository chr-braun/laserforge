"""
bibliothek.py – „Verzierungen“: gemeinsame Ornamente und Werkzeuge für alle Steckwerk-Pakete.

So nutzt ein anderes Paket die Bibliothek (in paket.json: "benoetigt": {"verzierungen": "1.0.0"}):

    from pakete import bibliothek
    Z = bibliothek("verzierungen")

    fig = Z.Figur().add(Z.K.rect(0, 0, 80, 40))           # eigene Fläche
    fig.merge(Z.vier_ecken(0, 0, 80, 40, 14, "ranke"))    # Eckornamente
    fig.merge(Z.durchbruch(mittellinie, "herzen", 5))     # Herzen ausschneiden
    teil = Z.figur_teil(cfg, "schild", fig, notes)        # → laserfestes Part (Stege, Kerf, Inseln geprüft)

Ornamente (alle als Figur, Maße in mm):
    rosette(r, art, blaetter)            ROSETTEN   bluete · mandala · stern · sonne · schneestern
    ecke(g, art) / vier_ecken(…)         ECKEN      ranke · faecher · herz · blatt · schnoerkel
    bordure(L, h, muster)                BORDUEREN  ranke · wellen · kringel · bogen · zacken · herzen · sterne ·
                                                    perlen · blaetter · tannen · maeander
    kante(poly, muster, g)               KANTEN     Verzierung außen an einer Kontur
    durchbruch(poly, muster, g)          DURCHBRUECHE  Ausschnitte entlang einer Linie
    ranke(L, h), schleife(b), zweig(L, art), herz(…), blatt(…), tropfen(…), spirale(…), kringel(…)
    kartusche(W, H, form)                FORMEN     Rahmenformen (Rechteck, Oval, Bogen, Wappen, Kartusche …)
    ausschnitt(art, cx, cy, g)           AUSSCHNITTE  Herz, Stern, Tanne, Blume, Mond, Pilz … als Loch

Werkzeuge:
    figur_teil(cfg, name, fig, notes)    Figur → laserfestes Teil
    wmin(cfg)                            Mindest-Linienstärke für Ornamente bei dieser Materialstärke
    zapfen_unten, schlitz, schlitz_polster, kante_mit_zapfen, abrunden, entlang
    brett(name, W, H, T, unten=…, rechts=…, oben=…, links=…)   exaktes Brett mit Zapfen an allen Seiten
    abbilden(part, fn) / kopfueber(part)   Teil samt Löchern und Steck-Merkmalen spiegeln/drehen
    gravur(part, linien)                 Linien kollisionsfrei gravieren
    text_in_box(…), textzeilen(…), schablone(…)   Schrift (graviert oder als Schablone geschnitten)
    K (Kurven/Figur), E (Leinwand/Raster), W (alle Werkzeuge)
    F (Weihnachts- und Wintermotive), G (Halloween-Formen)   – ab 1.1.0, gemeinsam für Mehrlagig, Filigran,
                                                            Weihnachtsdeko und Halloween
"""
from __future__ import annotations

import os
import sys
import zlib

_here = os.path.dirname(os.path.abspath(__file__))
VERSION = "1.1.0"


def _lade(name: str):
    import importlib.util
    path = os.path.join(_here, name + ".py")
    key = "swbib_verzierungen_%s_%08x" % (name, zlib.crc32(path.encode()))
    mod = sys.modules.get(key)
    if mod is None or getattr(mod, "__file__", None) != path:
        spec = importlib.util.spec_from_file_location(key, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[key] = mod
        spec.loader.exec_module(mod)
    return mod


K = _lade("_kit")
E = _lade("_ebenen")
W = _lade("_werkzeug")
O = _lade("ornamente")
F = _lade("_figuren")       # Motive: Fichte, Rentier, Engel, Krippe, Weihnachtsmann … (ab 1.1.0)
G = _lade("_grusel")        # Halloween-Formen: Fledermaus, Geist, Kürbis, Spukhaus … (ab 1.1.0)

Figur = K.Figur

# Ornamente
rosette, ranke, ecke, vier_ecken, bordure = O.rosette, O.ranke, O.ecke, O.vier_ecken, O.bordure
kante, durchbruch, schleife, zweig, kartusche = O.kante, O.durchbruch, O.schleife, O.zweig, O.kartusche
herz, blatt, tropfen, raute, spirale, kringel = O.herz, O.blatt, O.tropfen, O.raute, O.spirale, O.kringel
ausschnitt, AUSSCHNITTE = O.ausschnitt, O.AUSSCHNITTE
ROSETTEN, ECKEN, BORDUEREN, KANTEN, DURCHBRUECHE, FORMEN = (O.ROSETTEN, O.ECKEN, O.BORDUEREN, O.KANTEN,
                                                             O.DURCHBRUECHE, O.FORMEN)

# Werkzeuge
figur_teil, wmin, px_fuer = W.figur_teil, W.wmin, W.px_fuer
zapfen_unten, zapfen_kante, kante_mit_zapfen = W.zapfen_unten, W.zapfen_kante, W.kante_mit_zapfen
schlitz, schlitz_polster, gravur = W.schlitz, W.schlitz_polster, W.gravur
brett, abbilden, kopfueber = W.brett, W.abbilden, W.kopfueber
textzeilen, text_in_box, schablone, abrunden, entlang = W.textzeilen, W.text_in_box, W.schablone, W.abrunden, W.entlang


def gespiegelt(fig, achse_x: float = 0.0):
    """Figur an der Senkrechten x = achse_x spiegeln."""
    return fig.map(lambda p: (2 * achse_x - p[0], p[1]))


def gedreht(fig, winkel: float, um=(0.0, 0.0)):
    """Figur um den Punkt um drehen (Bogenmaß)."""
    return fig.map(lambda p: O._rot(p, winkel, um))
