"""
Ebenenmotiv – ein Motiv aus drei aufeinandergesteckten Lagen.

  Grundplatte  die Silhouette, rundum um „Rand“ größer – gibt dem Motiv einen Schattenrand
  Motiv        das Motiv mit allen feinen Durchbrüchen
  Auflage      der Kern des Motivs, um „Einzug“ kleiner – hebt die Mitte plastisch heraus

Vierkantstifte (T × T) stecken durch alle drei Lagen und halten sie ohne Leim zusammen.
Am besten wirken die Lagen in drei Tönen (Grund dunkel, Motiv mittel, Auflage hell).
"""
from __future__ import annotations

import os
import sys
from typing import List, Tuple

from steckwerk import Assembly, JointFeature, Part
from pakete import bibliothek, num, sel

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
D = _sub("aufsteckdeko")
K = E.K
Figur = K.Figur

BEFESTIGUNG = [("oese", "Öse zum Aufhängen"), ("standfuss", "Standfuß"), ("keine", "ohne (zum Aufkleben)")]

INFO = dict(
    label="Ebenenmotiv",
    group="Mehrlagig",
    desc="Motiv aus drei Lagen – Grundplatte mit Schattenrand, Motiv mit Durchbrüchen und erhabener Kern –, "
         "zusammengehalten von Vierkantstiften.",
    params=[
        sel("motiv", "Motiv", D.MOTIVE, "zierstern"),
        num("groesse", "Größe", 110, 50, 300, help="größte Abmessung des Motivs"),
        num("rand", "Schattenrand", 3, 2, 12),
        num("einzug", "Einzug der Auflage", 3, 1.5, 10),
        sel("befestigung", "Befestigung", BEFESTIGUNG, "oese"),
    ],
)

UEBERSETZUNG = {"en": {
    "Ebenenmotiv": "Layered motif",
    "Motiv aus drei Lagen – Grundplatte mit Schattenrand, Motiv mit Durchbrüchen und erhabener Kern –, zusammengehalten von Vierkantstiften.":
        "Motif made of three layers – base with shadow border, motif with cut-outs and a raised core – held together by square pegs.",
    "Schattenrand": "Shadow border", "Einzug der Auflage": "Inset of the top layer", "Standfuß": "Stand",
    "ohne (zum Aufkleben)": "none (to glue on)", "Öse zum Aufhängen": "Loop for hanging",
    "Motiv": "Motif", "Größe": "Size", "größte Abmessung des Motivs": "largest dimension of the motif",
    "Befestigung": "Mounting",
}}


def _punkte(lw, r) -> List[Tuple[float, float]]:
    """Gesetzte Pixel eines Rasters als mm-Punkte (ausgedünnt)."""
    out = []
    step = max(1, int(1.0 / lw.px))
    y0 = lw.y_top
    for row in range(0, lw.h, step):
        bits = r.rows[row]
        if not bits:
            continue
        for col in range(0, lw.w, step):
            if bits >> col & 1:
                out.append((lw.x0 + (col + 0.5) * lw.px, y0 - (row + 0.5) * lw.px))
    return out


def build(cfg, name="ebenenmotiv", motiv="zierstern", groesse=110.0, rand=3.0, einzug=3.0, befestigung="oese"):
    if motiv not in dict(D.MOTIVE):
        raise ValueError(f"Motiv {motiv!r} unbekannt")
    if befestigung not in dict(BEFESTIGUNG):
        raise ValueError(f"Befestigung {befestigung!r} unbekannt")
    T = cfg.T
    h = cfg.s(groesse)
    rand, einzug = float(rand), float(einzug)
    fig = D._einpassen(D._motiv(motiv, h, cfg.seed), h)
    x0, y0, x1, y1 = fig.bbox()
    m = rand + 14
    lw = E.Leinwand((x0 - m, y0 - m, x1 + m, y1 + m), px=0.08 if h <= 140 else 0.12)
    notes: List[str] = []
    web, kerf = cfg.min_web, cfg.kerf

    def lagen_bauen(fig, nabe=None):
        if nabe:
            fig = Figur(list(fig.ops)).add(nabe)
        mitte = E.teil_aus_raster(f"{name}_motiv", lw, lw.figur(fig), web, kerf, notes)
        sil = lw.flaechen([mitte.outline])
        voll = E._andnot(sil, lw.flaechen(mitte.holes)) if mitte.holes else sil

        # Grundplatte: Silhouette + Rand, Kerben geglättet
        # runder Versatz: Kreise entlang der Kontur (das Raster-Wachsen wäre achteckig)
        kontur = K.resample(mitte.outline + mitte.outline[:1], max(0.8, rand / 3))
        grund_r = sil.union(lw.flaechen([K.circle(x, y, rand, 20) for x, y in kontur]))
        grund_r = grund_r.close(lw.px_fuer(rand * 0.5))
        hinweis = "Mit Leim oder doppelseitigem Klebeband auf Karte, Box oder Tür setzen."
        flach = False
        if befestigung == "oese":
            tx, ty = D._spitze(fig, True)
            ro = max(4.5, 0.05 * h)
            ri = max(1.8, ro - max(2.5, 2 * web))
            oben = [y for x, y in K.resample(mitte.outline + mitte.outline[:1], 0.5) if abs(x - tx) < ro]
            ty = max(oben + [ty])
            oy = ty + rand + ro * 0.6
            grund_r = grund_r.union(lw.flaechen([K.circle(tx, oy, ro, 40), K.rect(tx - ro * 0.6, ty, ro * 1.2, oy - ty)]))
            grund_r = E._andnot(grund_r, lw.flaechen([K.circle(tx, oy, ri, 30)]))
            hinweis = "An einem Band durch die Öse aufhängen."
        elif befestigung == "standfuss":
            yb = y0 - rand
            grund_r = grund_r.union(lw.flaechen([K.rect(-0.25 * (x1 - x0) - 8, yb - 4, 0.5 * (x1 - x0) + 16, 6)]))
            flach = True
        grund = E.teil_aus_raster(f"{name}_grund", lw, grund_r, web, kerf, notes)

        # Auflage: Kern des Motivs (mit dessen Durchbrüchen), größtes Stück
        # Bei durchbrochenen Motiven (Stern, Flocke) bleibt beim Einziehen kaum etwas übrig – dann liegt
        # das Motiv verkleinert obenauf (Stern auf Stern).
        from steckwerk import signed_area
        auflage = None
        try:
            auf_r = sil.erode(lw.px_fuer(einzug))
            if mitte.holes:                                   # Durchbrüche des Motivs bleiben sichtbar
                auf_r = E._andnot(auf_r, lw.flaechen(mitte.holes))
            auf_r = auf_r.open(lw.px_fuer(1.5))
            auflage = E.teil_aus_raster(f"{name}_auflage", lw, auf_r, web, kerf, [])
            if abs(signed_area(auflage.outline)) < 0.12 * abs(signed_area(mitte.outline)):
                auflage = None
        except ValueError:
            auflage = None
        if auflage is None or nabe:
            cx0, cy0 = (x0 + x1) / 2, (y0 + y1) / 2
            s_k = max(0.35, 1 - 2 * (einzug + 0.18 * (y1 - y0)) / (y1 - y0))
            klein = fig.map(lambda p: (cx0 + (p[0] - cx0) * s_k, cy0 + (p[1] - cy0) * s_k))
            if nabe:
                klein.add(nabe)
            auflage = E.teil_aus_raster(f"{name}_auflage", lw, lw.figur(klein), web, kerf, [])

        # Stiftpositionen: tief im Inneren der Auflage
        frei = lw.flaechen([auflage.outline])
        if auflage.holes:
            frei = E._andnot(frei, lw.flaechen(auflage.holes))
        frei = E._and(frei, voll).erode(lw.px_fuer(T * 0.72 + web + kerf + 0.3))
        kand = _punkte(lw, frei)
        if not kand:
            return None
        cx = sum(p[0] for p in kand) / len(kand)
        cy = sum(p[1] for p in kand) / len(kand)
        a = max(kand, key=lambda p: (p[0] - cx) ** 2 + (p[1] - cy) ** 2)
        b = max(kand, key=lambda p: (p[0] - a[0]) ** 2 + (p[1] - a[1]) ** 2)
        stifte = [a, b] if (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 > (4 * T) ** 2 else [min(kand, key=lambda p: (p[0] - cx) ** 2 + (p[1] - cy) ** 2)]

        return mitte, grund, auflage, stifte, hinweis, flach

    res = lagen_bauen(fig)
    if res is None:
        # durchbrochene Mitte (Stern, Flocke): eine runde Nabe für die Stifte einsetzen
        cx0, cy0 = (x0 + x1) / 2, (y0 + y1) / 2
        res = lagen_bauen(fig, K.circle(cx0, cy0, einzug + 0.8 * T + web + kerf + 0.8, 40))
    if res is None:
        raise ValueError("Für die Steckstifte ist im Motiv zu wenig Platz – größer wählen oder kleineren Einzug")
    mitte, grund, auflage, stifte, hinweis, flach = res
    lagen = [grund, mitte, auflage]
    asm = Assembly(name, params=dict(motiv=motiv, groesse=h, rand=rand, einzug=einzug, befestigung=befestigung))
    if flach:
        # Unterkante der Grundplatte exakt gerade machen und Zapfen in einen Standfuß stecken
        yb = min(p[1] for p in grund.outline)
        grund.outline = [(x, 0.0 if abs(y - yb) < 0.3 else y - yb) for x, y in grund.outline]
        dy = -yb
        for p in (mitte, auflage):
            p.outline = [(x, y + dy) for x, y in p.outline]
            p.holes = [[(x, y + dy) for x, y in hh] for hh in p.holes]
        grund.holes = [[(x, y + dy) for x, y in hh] for hh in grund.holes]
        stifte = [(x, y + dy) for x, y in stifte]
        k = len(grund.outline)
        grund.outline = [p for i, p in enumerate(grund.outline)
                         if not (p[1] == 0.0 and grund.outline[i - 1][1] == 0.0 and grund.outline[(i + 1) % k][1] == 0.0)]
        tw = max(cfg.tab_factor * T, 8.0)
        out, tabs = E.zapfen_einsetzen(grund.outline, [0.0], tw, T)
        if not tabs:
            raise ValueError("Für den Standfuß ist unten zu wenig Platz – Motiv größer wählen")
        grund.outline = out
        grund.features.append(JointFeature("z0", "tab", tw, T, pos=0.0, points=tabs[0][2]))
        fuss, ids = E.sockelplatte(f"{name}_fuss", max(tw + 40, 0.7 * (x1 - x0)), [0.0], [0.0], tw, T, max(12.0, 0.1 * h))
        asm.parts.append(fuss)
        asm.connect(f"{grund.name}:z0", f"{fuss.name}:{ids[0]}")
        hinweis = "Die Grundplatte mit dem Zapfen in den Standfuß stecken."
    for j, (x, y) in enumerate(stifte):
        st = E.stift(f"{name}_stift{j + 1}", 3, T, float(j))
        for k, p in enumerate(lagen):
            E.stiftloch(p, f"b{j}", x, y, T, float(j))
            asm.connect(f"{st.name}:l{k}", f"{p.name}:b{j}")
        asm.parts.append(st)
    asm.parts[:0] = lagen
    asm.notes.append(f"{name}: Grundplatte, Motiv und Auflage übereinanderlegen und die Vierkantstifte "
                     f"({3 * T:.0f} mm) durchdrücken. {hinweis}")
    asm.notes.append(f"{name}: Tipp – die drei Lagen in drei Tönen lasieren (Grund dunkel, Auflage hell).")
    asm.notes += notes
    return asm
