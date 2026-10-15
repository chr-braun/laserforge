"""
Aufsteckdeko – feine Verzierungen zum Aufstecken, Einstecken oder Aufhängen.

Jedes Motiv ist von Hand gezeichnet (Schneeflocke mit Seitenästen, Zierstern, Fichte, Hirsch, Rentier, Eule,
Engel, Schneemann, Kürbis, Fledermaus, Hexe, Katze). Befestigung:

  kantenreiter  Kerbe unten – das Motiv reitet auf einer Plattenkante (Rahmen eines Ebenenbilds, Regalbrett …)
  zapfen        Zapfen unten – passt in jeden Steckwerk-Schlitz, auf Wunsch mit eigenem Standfuß
  oese          Öse oben – zum Aufhängen (Fenster, Baum, Zweig)
  spiess        langer Stecker – für Blumentöpfe, Gestecke und Adventskränze
"""
from __future__ import annotations

import copy
import math
import os
import sys
from typing import List

from steckwerk import Assembly, JointFeature, Part, oriented
from pakete import bibliothek, flag, integer, num, sel

_here = os.path.dirname(os.path.abspath(__file__))


def _sub(name: str):
    import importlib.util
    path = os.path.join(_here, name + ".py")
    key = "swpaket_ebenen_" + name
    mod = sys.modules.get(key)
    if mod is None or getattr(mod, "__file__", None) != path:
        spec = importlib.util.spec_from_file_location(key, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[key] = mod
        spec.loader.exec_module(mod)
    return mod


E = bibliothek("verzierungen").E
F = bibliothek("verzierungen").F
G = bibliothek("verzierungen").G
K = E.K
Figur = K.Figur

MOTIVE = [("zierstern", "Zierstern"), ("schneeflocke", "Schneeflocke"), ("fichte", "verschneite Fichte"),
          ("hirsch", "Hirsch"), ("rentier", "fliegendes Rentier"), ("eule", "Eule auf dem Ast"),
          ("engel", "Engel mit Posaune"), ("schneemann", "Schneemann"), ("kuerbis", "Kürbis mit Gesicht"),
          ("fledermaus", "Fledermaus"), ("hexe", "Hexe auf dem Besen"), ("katze", "Katze"),
          ("weihnachtsmann", "winkender Weihnachtsmann"), ("lkw", "Pick-up mit Tannenbaum"),
          ("nussknacker", "Nussknacker")]
BEFESTIGUNG = [("kantenreiter", "Kerbe zum Aufstecken auf eine Kante"), ("zapfen", "Zapfen zum Einstecken"),
               ("oese", "Öse zum Aufhängen"), ("spiess", "Stecker für Topf und Gesteck")]

INFO = dict(
    label="Aufsteckdeko",
    group="Mehrlagig",
    desc="Feine Verzierungen zum Aufstecken auf eine Kante, zum Einstecken in einen Schlitz, "
         "zum Aufhängen oder als Stecker für Blumentopf und Adventsgesteck.",
    params=[
        sel("motiv", "Motiv", MOTIVE, "schneeflocke"),
        num("groesse", "Größe", 70, 30, 250, help="größte Abmessung des Motivs"),
        sel("befestigung", "Befestigung", BEFESTIGUNG, "kantenreiter"),
        num("kante", "Kantenstärke", 0, 0, 40, help="0 = Materialstärke (passt auf Steckwerk-Teile)",
            when={"befestigung": ["kantenreiter"]}),
        flag("standfuss", "mit eigenem Standfuß", True, when={"befestigung": ["zapfen"]}),
        integer("anzahl", "Anzahl", 1, 1, 24),
    ],
)

UEBERSETZUNG = {"en": {
    "Aufsteckdeko": "Clip-on decorations",
    "Feine Verzierungen zum Aufstecken auf eine Kante, zum Einstecken in einen Schlitz, zum Aufhängen oder als Stecker für Blumentopf und Adventsgesteck.":
        "Fine decorations to clip onto an edge, plug into a slot, hang up, or use as a pick for flower pots and Advent arrangements.",
    "Motiv": "Motif", "Größe": "Size", "größte Abmessung des Motivs": "largest dimension of the motif", "Befestigung": "Mounting",
    "Kantenstärke": "Edge thickness", "0 = Materialstärke (passt auf Steckwerk-Teile)": "0 = material thickness (fits Steckwerk parts)",
    "mit eigenem Standfuß": "with its own stand", "Anzahl": "Quantity",
    "Zierstern": "Ornamental star", "Schneeflocke": "Snowflake", "verschneite Fichte": "Snowy spruce", "Hirsch": "Stag",
    "fliegendes Rentier": "Flying reindeer", "Eule auf dem Ast": "Owl on a branch", "Engel mit Posaune": "Angel with trumpet",
    "Schneemann": "Snowman", "Kürbis mit Gesicht": "Pumpkin with face", "Fledermaus": "Bat",
    "Hexe auf dem Besen": "Witch on a broom", "Katze": "Cat",
    "winkender Weihnachtsmann": "Waving Santa", "Pick-up mit Tannenbaum": "Pick-up with Christmas tree",
    "Nussknacker": "Nutcracker",
    "Kerbe zum Aufstecken auf eine Kante": "Notch to clip onto an edge", "Zapfen zum Einstecken": "Tenon to plug in",
    "Öse zum Aufhängen": "Loop for hanging", "Stecker für Topf und Gesteck": "Pick for pots and arrangements",
}}


def _motiv(motiv: str, h: float, seed: int) -> Figur:
    """Motiv in etwa der Höhe h zeichnen (wird danach exakt eingepasst)."""
    if motiv == "zierstern":
        return F.zierstern(h)
    if motiv == "schneeflocke":
        return F.schneeflocke(h, seed)
    if motiv == "fichte":
        return F.fichte(h, seed, breite=0.6, schnee=True)
    if motiv == "hirsch":
        return F.hirsch(h / 2.3, 2.0)
    if motiv == "rentier":
        return F.rentier_flug(1.6 / (h / 2.2), nase=True).place(0, 0, h / 2.2)
    if motiv == "eule":
        return F.eule(h)
    if motiv == "engel":
        return F.engel(h)
    if motiv == "schneemann":
        return F.schneemann(h, seed)
    if motiv == "kuerbis":
        w = h * 1.1
        k = Figur().add(G.pumpkin(0.0, 0.0, w, h * 0.9))
        return k.cut(*G.pumpkin_face("klassisch", 0.0, h * 0.45, w * 0.74, h * 0.5))
    if motiv == "fledermaus":
        return Figur().add(G.bat_unit(0.4)).place(0, 0, h * 3.0)
    if motiv == "hexe":
        return Figur().add(G.witch_unit()).place(0, 0, h * 2.0)
    if motiv == "katze":
        return Figur().add(G.cat_unit()).place(0, 0, h)
    if motiv == "weihnachtsmann":
        return F.weihnachtsmann(h)
    if motiv == "lkw":
        return F.lkw_baum(h, seed)
    if motiv == "nussknacker":
        return F.nussknacker(h)
    raise ValueError(f"Motiv {motiv!r} unbekannt")


STEHEND = {"fichte", "hirsch", "schneemann", "katze", "engel", "kuerbis", "weihnachtsmann", "lkw", "nussknacker"}


def _einpassen(fig: Figur, h: float) -> Figur:
    """Größte Abmessung auf h bringen, Fuß auf y = 0, Mitte x = 0."""
    x0, y0, x1, y1 = fig.bbox()
    s = h / max(y1 - y0, x1 - x0)
    return fig.map(lambda p: ((p[0] - (x0 + x1) / 2) * s, (p[1] - y0) * s))


def _spitze(fig: Figur, oben: bool):
    """Treffpunkt einer senkrechten Linie durch die Bildmitte mit dem Motiv – von oben (Öse) oder von
    unten (Fuß, Kerbe, Stecker). Liegt dort Luft (z. B. zwischen Hirschbeinen), wird leicht seitlich gesucht."""
    from steckwerk import point_in_polygon
    x0, y0, x1, y1 = fig.bbox()
    polys = [p for s, p in fig.ops if s == "+"]
    w = x1 - x0
    step = max(0.25, (y1 - y0) / 400)
    for dx in (0.0, 0.04, -0.04, 0.08, -0.08, 0.12, -0.12):
        x = (x0 + x1) / 2 + dx * w
        n = int((y1 - y0) / step) + 1
        ys = [y1 - i * step for i in range(n)] if oben else [y0 + i * step for i in range(n)]
        for y in ys:
            # nur kräftige Stellen zählen (nicht ein dünnes Bein oder Geweihende)
            if all(any(point_in_polygon(q, p) for p in polys)
                   for q in ((x, y), (x - 1.5, y), (x + 1.5, y), (x, y + (-2.0 if oben else 2.0)))):
                return x, y
    return (x0 + x1) / 2, (y1 if oben else y0)


def build(cfg, name="aufsteckdeko", motiv="schneeflocke", groesse=70.0, befestigung="kantenreiter", kante=0.0,
          standfuss=True, anzahl=1):
    if motiv not in dict(MOTIVE):
        raise ValueError(f"Motiv {motiv!r} unbekannt")
    if befestigung not in dict(BEFESTIGUNG):
        raise ValueError(f"Befestigung {befestigung!r} unbekannt")
    T = cfg.T
    h = cfg.s(groesse)
    if h < 30:
        raise ValueError("Motiv ist zu klein für feine Details – mindestens 30 mm")
    fig = _einpassen(_motiv(motiv, h, cfg.seed), h)
    x0, _, x1, _ = fig.bbox()
    if motiv in STEHEND and befestigung != "oese":
        # Bodenleiste unter allen Füßen, darunter sitzt die Befestigung
        bl = max(2.5, 0.8 * T, 0.035 * h)
        fig.add(K.stroke([(x0 + 0.08 * (x1 - x0), -bl / 2 + 0.6), (x1 - 0.08 * (x1 - x0), -bl / 2 + 0.6)], bl, bl))
        fig = fig.place(0, bl, 1.0)
    notes: List[str] = []
    asm = Assembly(name, params=dict(motiv=motiv, groesse=h, befestigung=befestigung, kante=kante, anzahl=anzahl))
    tw = max(cfg.tab_factor * T, 8.0)
    flach = False
    if befestigung == "kantenreiter":
        k = float(kante) or T
        tiefe = max(8.0, min(0.15 * h, 16.0), 1.2 * k)
        bw = k + 2 * max(4.0, 1.5 * T)
        bx, by = _spitze(fig, False)
        bx = max(x0 + bw / 2, min(x1 - bw / 2, bx))
        fig.add(K.rect(bx - bw / 2, -tiefe, bw, tiefe + 1.0))
        sw = max(3.0, 1.2 * T)
        fig.add(K.rect(bx - sw, -1.0, 2 * sw, by + 1.0 + max(3.0, 0.06 * h)))
        fig.cut(K.rect(bx - k / 2, -tiefe - 1, k, tiefe - 1.0 + 1))
        fig.cut(K.circle(bx, -2.0, k / 2, 24))                          # runder Kerbgrund
        hinweis = (f"Mit der Kerbe ({k:.1f} mm breit, {tiefe - 2 + k / 2:.0f} mm tief) auf eine Plattenkante stecken – "
                   "z. B. oben auf den Rahmen eines Ebenenbilds.")
    elif befestigung == "zapfen":
        pw = tw + 2 * max(6.0, 2 * T)
        ph = max(5.0, 2 * T)
        bx, by = _spitze(fig, False)
        fig.add(K.rect(bx - pw / 2, -ph, pw, ph + 1.0))
        fig.add(K.rect(bx - max(3.0, 1.2 * T), -1.0, 2 * max(3.0, 1.2 * T), by + max(4.0, 0.08 * h)))
        fig = fig.place(0, ph, 1.0)
        flach = True
        hinweis = f"Zapfen {tw:.0f} × {T:.0f} mm passt in jeden Steckwerk-Schlitz."
    elif befestigung == "oese":
        tx, ty = _spitze(fig, True)
        ro = max(4.0, 0.06 * h)
        ri = max(1.6, ro - max(2.2, cfg.min_web * 2))
        fig.add(K.circle(tx, ty + ro * 0.75, ro, 40))
        fig.add(K.rect(tx - ro * 0.5, ty - ro * 0.6, ro, ro * 1.2))
        fig.cut(K.circle(tx, ty + ro * 0.75, ri, 30))
        hinweis = "An einem Faden oder Draht durch die Öse aufhängen."
    else:
        sw = max(4.0, 1.4 * T)
        L = max(60.0, 0.9 * h)
        bx, by = _spitze(fig, False)
        fig.add([(bx - sw / 2, by + max(3.0, 0.08 * h)), (bx - sw / 2, -L + 2 * sw), (bx, -L),
                 (bx + sw / 2, -L + 2 * sw), (bx + sw / 2, by + max(3.0, 0.08 * h))])
        hinweis = f"Den Stecker ({L:.0f} mm) in Erde, Steckmasse oder Moos stecken."

    teil = E.teil_aus_figur(f"{name}_1", fig, cfg.min_web, cfg.kerf, notes, px=0.06 if h < 90 else 0.09,
                            unten_flach=flach)
    if flach:
        out, tabs = E.zapfen_einsetzen(teil.outline, [tabs_x for tabs_x in [_mitte_unten(teil.outline)]], tw, T)
        if not tabs:
            raise ValueError("Für den Zapfen ist unten zu wenig Platz – Motiv größer wählen")
        teil.outline = out
        if standfuss:
            teil.features.append(JointFeature("z0", "tab", tw, T, pos=0.0, points=tabs[0][2]))
    teile = [teil]
    for i in range(1, int(anzahl)):
        c = copy.deepcopy(teil)
        c.name = f"{name}_{i + 1}"
        teile.append(c)
    asm.parts += teile
    if befestigung == "zapfen" and standfuss:
        fb = max(tw + 30.0, 0.6 * (x1 - x0))
        for i, t in enumerate(teile):
            base, ids = E.sockelplatte(f"{name}_fuss{i + 1}", fb, [0.0], [0.0], tw, T, max(10.0, 0.12 * h))
            asm.parts.append(base)
            asm.connect(f"{t.name}:z0", f"{base.name}:{ids[0]}")
        hinweis = "Motiv mit dem Zapfen in den Standfuß stecken."
    asm.notes.append(f"{name}: {hinweis}")
    asm.notes += notes
    return asm


def _mitte_unten(outline) -> float:
    xs = [x for x, y in outline if y == 0.0]
    return (min(xs) + max(xs)) / 2 if xs else 0.0
