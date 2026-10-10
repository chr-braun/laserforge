"""
_stand.py – Standsockel für flache Figuren (Schneemann, Wichtel, …).

Die Figur bekommt unten einen Tab (Höhe T), der Sockel einen passenden Slot.
"""
from __future__ import annotations

from typing import Tuple

from steckwerk import Assembly, Config, JointFeature, Part, ellipse, rect, slot_feature
from models._font import unsupported


def stand_base(asm: Assembly, figure: Part, tab_id: str, tab_width: float, cfg: Config,
               rx: float, ry: float, name: str, text: str = "", schrift: str = "normal",
               schreibweise: str = "gross") -> Part:
    """Ovaler Sockel mit mittigem Slot; verbindet figure:tab_id ⇄ sockel:figur0.
    text: Gravur vor der Figur (der Sockel wächst bei Bedarf mit)."""
    T = cfg.T
    rx = max(rx, tab_width / 2 + 3 * T)
    ry = max(ry, T / 2 + 3 * T)
    if text.strip():
        bad = unsupported(text)
        if bad:
            raise ValueError(f"Sockel-Text: Zeichen {''.join(bad)!r} gibt es in der Gravurschrift nicht")
        ry = max(ry, T / 2 + 14.0, 0.45 * rx)
    for _ in range(6):
        base = Part(name, ellipse(0.0, 0.0, rx, ry, n=96))
        feat, hole = slot_feature("figur0", -tab_width / 2, -T / 2, tab_width, T, True, 0.0)
        base.holes.append(hole)
        base.features.append(feat)
        # dezente Schneekante als Gravur
        base.add_engrave(ellipse(0.0, 0.0, rx - 2.0, ry - 2.0, n=96), closed=True)
        if not text.strip() or _base_text(base, text, rx, ry, T, schrift, schreibweise, cfg):
            break
        rx, ry = rx * 1.15, ry * 1.15                  # Sockel etwas größer, erneut versuchen
    else:
        raise ValueError(f"Sockel-Text {text!r} ist zu lang – kürzer fassen oder Schrift „schmal“ wählen")
    asm.parts.append(base)
    asm.connect(f"{figure.name}:{tab_id}", f"{base.name}:figur0")
    return base


def _base_text(base: Part, text: str, rx: float, ry: float, T: float, style: str, case: str,
               cfg: Config) -> bool:
    """Text vorne (−y) zwischen Schneekante und Figur."""
    from models import _deko as dk
    y_top = -T / 2 - 2.0
    cv = dk.Canvas(base, margin=2.8, area=rect(-rx, -ry, 2 * rx, ry + y_top), seed=cfg.seed)
    span = ry + y_top - 2.8
    cands = dk.free_rects(cv, 0.0, y_top - span / 2, [0.9 * span, 0.7 * span, 0.5 * span],
                          [0.0, 0.1 * span, -0.1 * span])
    return dk.sign(cv, text, "ohne", cands, style, case, min_h=2.5, max_cap=min(9.0, 0.5 * span),
                   anchor="mitte", tol=cfg.arc_tolerance) is not None


def bottom_tab(width: float, tab_width: float, T: float) -> list:
    """Segmente für eine Unterkante der Breite width mit mittigem Tab nach unten."""
    a = (width - tab_width) / 2
    return [(a, 0.0), (tab_width, T), (a, 0.0)]


def tab_feature_at(fid: str, x0: float, y0: float, w: float, T: float, pos: float = 0.0) -> JointFeature:
    """Tab nach unten an der Kante y=y0 von x0 bis x0+w."""
    return JointFeature(fid, "tab", w, T, pos=pos,
                        points=[(x0, y0), (x0, y0 - T), (x0 + w, y0 - T), (x0 + w, y0)])
