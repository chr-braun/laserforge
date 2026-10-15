"""
_moebel.py – gemeinsame Teile der Wichtelmöbel: Seitenwangen mit Füßen und Ausschnittmotiv, Beine mit
Zapfen oben, Platten mit Schlitzen. Nutzt die Bibliothek „Verzierungen“.

Koordinaten der Wangen/Beine: x = Tiefe (0 … B), y = Höhe (0 = Boden).
"""
from __future__ import annotations

import math
from typing import List, Sequence, Tuple

from pakete import bibliothek

Z = bibliothek("verzierungen")
K = Z.K

OBEN = [("geschwungen", "geschwungen"), ("bogen", "Rundbogen"), ("gerade", "gerade, abgerundet"),
        ("spitz", "Giebel")]
MOTIVE = [("keine", "keins")] + Z.AUSSCHNITTE
EINZUG = 0.3            # Platten zwischen zwei Wangen etwas schmaler, damit nichts klemmt


def tabbreite(cfg, verfuegbar: float, anteil: float = 0.24) -> float:
    """Zapfenbreite: mindestens T + Kerf (+ Luft), höchstens tab_factor · T."""
    return max(cfg.min_tab_width + 0.6, min(cfg.tab_factor * cfg.T, verfuegbar * anteil))


def umriss(B: float, H: float, oben: str) -> List[Tuple[float, float]]:
    """Umriss einer Wange (x 0 … B, y 0 … H) mit gestalteter Oberkante."""
    if oben == "gerade":
        return Z.abrunden([(0, 0), (B, 0), (B, H), (0, H)], min(B, H) * 0.14)
    if oben == "bogen":
        hb = min(B / 2, H * 0.35)
        arc = [(B / 2 + B / 2 * math.cos(a), H - hb + hb * math.sin(a))
               for a in (math.pi * i / 40 for i in range(41))]
        return [(0, 0), (B, 0)] + arc[:-1] + [(0, H - hb)]
    if oben == "spitz":
        hb = min(B * 0.45, H * 0.3)
        return Z.abrunden([(0, 0), (B, 0), (B, H - hb), (B / 2, H), (0, H - hb)], min(B, H) * 0.06)
    # geschwungen: Mitte oben, zu den Seiten mit S-Schwung abfallend, kleine Nasen außen
    hb = min(B * 0.3, H * 0.25)
    rechts = K.bez3((B, H - hb), (B * 0.72, H - hb * 1.05), (B * 0.72, H), (B / 2, H), 20)
    links = K.bez3((B / 2, H), (B * 0.28, H), (B * 0.28, H - hb * 1.05), (0, H - hb), 20)
    return [(0, 0), (B, 0)] + rechts + links[1:]


def wange(cfg, name: str, B: float, H: float, oben: str, motiv: str, notes: List[str],
          schlitze: Sequence[Tuple[str, float, float, float, float, float]] = (),
          motiv_box=None, fuss: bool = True) -> "Z.W.Part":
    """Seitenteil mit Füßen (Bogen unten), Ausschnittmotiv und Schlitzen
    schlitze = [(fid, cx, cy, laenge, pos, winkel)]."""
    T = cfg.T
    fig = Z.Figur().add(umriss(B, H, oben))
    fh = 0.0
    if fuss:
        fb = max(1.6 * T + 1.0, B * 0.18)
        fh = min(H * 0.22, (B - 2 * fb) * 0.45)
        if fh > 1.2 * T + 1.0:
            fig.cut(K.ellipse(B / 2, 0, B / 2 - fb, fh, 0, 64))
    if motiv != "keine" and motiv_box:
        x0, y0, x1, y1 = motiv_box
        g = min(x1 - x0, y1 - y0) * 0.85
        if g >= 3 * Z.wmin(cfg):
            fig.merge(Z.ausschnitt(motiv, (x0 + x1) / 2, (y0 + y1) / 2, g))
    rand = max(2.0, T * 0.8)
    solid = [Z.schlitz_polster(cx, cy, L, T, rand, w) for _, cx, cy, L, _, w in schlitze]
    part = Z.figur_teil(cfg, name, fig, notes, solid=solid, unten_flach=True)
    for fid, cx, cy, L, pos, w in schlitze:
        Z.schlitz(part, fid, cx, cy, L, T, pos, w)
    return part


def fussbogen_hoehe(cfg, B: float, H: float) -> float:
    fb = max(1.6 * cfg.T + 1.0, B * 0.18)
    fh = min(H * 0.22, (B - 2 * fb) * 0.45)
    return fh if fh > 1.2 * cfg.T + 1.0 else 0.0


def bein(cfg, name: str, B: float, H: float, motiv: str, notes: List[str], zapfen: Sequence[Tuple[float, str, float]],
         tw: float, schlitze=(), motiv_box=None) -> "Z.W.Part":
    """Tisch-/Hockerbein als Platte (x 0 … B, y 0 … H) mit Füßen unten und Zapfen oben
    zapfen = [(x, fid, pos)]. Wird kopfüber gebaut, damit die Oberkante exakt gerade ist."""
    T = cfg.T
    fb = max(1.6 * T + 1.0, B * 0.18)
    fh = fussbogen_hoehe(cfg, B, H)
    spiegel = lambda p: (p[0], H - p[1])
    fig = Z.Figur().add(Z.abrunden([(0, 0), (B, 0), (B, H), (0, H)], min(B, H) * 0.08))
    # Taille: leicht eingezogene Seiten
    e = min(B * 0.12, 3.0)
    if B - 2 * e > 2 * fb:
        fig.cut(K.ellipse(-B * 0.02, H * 0.55, e, H * 0.28, 0, 40), K.ellipse(B * 1.02, H * 0.55, e, H * 0.28, 0, 40))
    if fh:
        fig.cut(K.ellipse(B / 2, 0, B / 2 - fb, fh, 0, 64))
    if motiv != "keine" and motiv_box:
        x0, y0, x1, y1 = motiv_box
        g = min(x1 - x0, y1 - y0) * 0.85
        if g >= 3 * Z.wmin(cfg):
            fig.merge(Z.ausschnitt(motiv, (x0 + x1) / 2, (y0 + y1) / 2, g))
    rand = max(2.0, T * 0.8)
    solid = [Z.schlitz_polster(cx, cy, L, T, rand, w) for _, cx, cy, L, _, w in schlitze]
    fig = fig.map(spiegel)
    solid = [[spiegel(p) for p in s] for s in solid]
    part = Z.figur_teil(cfg, name, fig, notes, solid=solid, unten_flach=True)
    for x, fid, pos in zapfen:
        Z.zapfen_unten(part, x, tw, T, fid, pos)
    part = Z.abbilden(part, spiegel)
    for fid, cx, cy, L, pos, w in schlitze:
        Z.schlitz(part, fid, cx, cy, L, T, pos, w)
    return part


def platte(cfg, name: str, umr, notes: List[str], schlitze=(), kante: str = "keine",
           kante_ausser=None) -> "Z.W.Part":
    """Platte (Tischplatte, Sitz) mit Schlitzen [(fid, cx, cy, laenge, pos, winkel)] und verzierter Kante."""
    T = cfg.T
    w = Z.wmin(cfg)
    fig = Z.Figur().add(umr)
    if kante != "keine":
        xs, ys = [p[0] for p in umr], [p[1] for p in umr]
        g = max(3.2 * w, min(6.0, min(max(xs) - min(xs), max(ys) - min(ys)) * 0.09))
        fig.merge(Z.kante(umr, kante, g, w, ausser=kante_ausser))
    rand = max(2.0, T * 0.8)
    solid = [Z.schlitz_polster(cx, cy, L, T, rand, wi) for _, cx, cy, L, _, wi in schlitze]
    part = Z.figur_teil(cfg, name, fig, notes, solid=solid)
    for fid, cx, cy, L, pos, wi in schlitze:
        Z.schlitz(part, fid, cx, cy, L, T, pos, wi)
    return part


def text_gravur(part, text: str, cx: float, cy: float, max_w: float, max_h: float, max_cap: float = 8.0):
    if not text.strip():
        return
    try:
        st, _ = Z.text_in_box(text, cx, cy, max_w, max_h, max_cap, 2.5, 0.08)
    except ValueError:
        raise ValueError(f"Der Text „{text.replace('|', ' ')}“ passt nicht drauf – kürzer fassen oder das Möbel größer machen")
    Z.gravur(part, [(s, False) for s in st], rand=0.8)
