"""
briefkasten.py – Wichtel-Briefkasten auf Pfosten.

Kleiner Kasten mit Satteldach im Stil des Wichtelhauses (gleicher Generator), Briefschlitz
vorne, Brief- und Fähnchen-Gravur, Pfosten mit Tabs oben (in den Kastenboden) und unten
(in die Fußplatte).

Gestaltung: text (Name statt Briefumschlag, z. B. „Post“ oder „Fam. Huber“) mit schild_form,
schrift und schreibweise; dach (Dachgravur wie beim Wichtelhaus).
"""
from __future__ import annotations

from typing import Optional

from steckwerk import (Assembly, Config, JointFeature, Part, clean, profile_edge, rect,
                        slot_feature)
from models import _deko as dk
from models._box import build_box
from models._font import CASES, STYLES, unsupported

DEFAULTS = dict(width=40.0, depth=50.0, height=32.0, post=55.0)


def build(cfg: Config, name: str = "briefkasten", width: Optional[float] = None,
          depth: Optional[float] = None, height: Optional[float] = None,
          post: Optional[float] = None, pitch: float = 35.0, text: str = "", schild_form: str = "rahmen",
          schrift: str = "normal", schreibweise: str = "gross", dach: str = "ziegel") -> Assembly:
    dk.check_choice("Schildform", schild_form, dk.SIGNS)
    dk.check_choice("Dach", dach, dk.ROOFS)
    if schrift not in STYLES:
        raise ValueError(f"Schrift {schrift!r} unbekannt – erlaubt: {', '.join(STYLES)}")
    if schreibweise not in CASES:
        raise ValueError(f"Schreibweise {schreibweise!r} unbekannt – erlaubt: {', '.join(CASES)}")
    bad = unsupported(text)
    if bad:
        raise ValueError(f"Briefkasten-Text: Zeichen {''.join(bad)!r} gibt es in der Gravurschrift nicht")
    T = cfg.T
    W = cfg.s(width or DEFAULTS["width"])
    D = cfg.s(depth or DEFAULTS["depth"])
    H = cfg.s(height or DEFAULTS["height"])
    P = cfg.s(post or DEFAULTS["post"])
    asm, info = build_box(name, W, D, H, cfg, top="gable", pitch_deg=pitch, base_margin=max(T, 3.0))

    front = asm.part(info.name("vorne"))
    sw, sh = 0.56 * W, max(5.0, T + 2.0)
    front.add_hole(rect(W / 2 - sw / 2, 0.62 * H, sw, sh))
    front.add_engrave(rect(W / 2 - sw / 2 - 1.5, 0.62 * H - 1.5, sw + 3.0, sh + 3.0), closed=True)
    if text.strip():                                  # Name/Schild statt Briefumschlag
        cv = dk.Canvas(front, margin=1.6, seed=cfg.seed)
        cv.block_strokes(front.engrave, 0.8)
        top = 0.62 * H - 1.5 - 1.2
        cands = dk.free_rects(cv, W / 2, top / 2 + 0.5, [top - 1.0, 0.8 * top, 0.62 * top], [0.0])
        if dk.sign(cv, text, schild_form, cands, schrift, schreibweise, min_h=2.5, max_cap=0.2 * H,
                   anchor="mitte", tol=cfg.arc_tolerance) is None:
            raise ValueError(f"Briefkasten-Text {text!r} passt nicht unter den Schlitz – kürzer fassen, "
                             f"Schrift „schmal“, Schildform „nur Text“ oder Briefkasten größer machen")
    else:                                             # Briefumschlag-Gravur
        ex, ey, ew, eh = W / 2 - 0.2 * W, 0.18 * H, 0.4 * W, 0.26 * H
        front.add_engrave(rect(ex, ey, ew, eh), closed=True)
        front.add_engrave([(ex, ey + eh), (ex + ew / 2, ey + eh * 0.45), (ex + ew, ey + eh)])
    # Fähnchen-Gravur auf der rechten Seite
    side = asm.part(info.name("rechts"))
    Ds = info.Ds
    fx = 0.7 * Ds
    side.add_engrave([(fx, 0.2 * H), (fx, 0.8 * H)])
    side.add_engrave([(fx, 0.8 * H), (fx - 0.28 * Ds, 0.8 * H), (fx - 0.28 * Ds, 0.62 * H), (fx, 0.62 * H)],
                     closed=False)
    for k, r in enumerate(("dach_links", "dach_rechts")):
        roof = asm.part(info.name(r))
        x0, y0, x1, y1 = roof.bbox()
        dk.roof_pattern(dk.Canvas(roof, margin=1.2, hole_margin=1.0, seed=cfg.seed + k), dach,
                        (x0, y0, x1, y1), 5.0, cfg.seed + k)

    # Pfosten: oben Tab in den Kastenboden, unten Tab in die Fußplatte
    pw = max(10.0, 3 * T)
    tw = max(cfg.min_tab_width, 0.6 * pw)
    a = (pw - tw) / 2
    pts = profile_edge((0.0, 0.0), (pw, 0.0), [(a, 0.0), (tw, T), (a, 0.0)])
    pts += [(pw, 0.0)] + profile_edge((pw, P), (0.0, P), [(a, 0.0), (tw, T), (a, 0.0)]) + [(0.0, P)]
    post_part = Part(info.name("pfosten"), clean(pts), features=[
        JointFeature("unten", "tab", tw, T, pos=0.0, points=[(a, 0), (a, -T), (a + tw, -T), (a + tw, 0)]),
        JointFeature("oben", "tab", tw, T, pos=0.0, points=[(pw - a, P), (pw - a, P + T), (a, P + T), (a, P)])])
    for k in range(3):                                # Maserung
        x = pw * (k + 1) / 4
        post_part.add_engrave([(x, 3.0 + k * 2.0), (x, P - 3.0 - k * 1.5)])
    asm.parts.append(post_part)

    base = asm.part(info.name("boden"))
    m = info.base_margin
    feat, hole = slot_feature("pfosten", m + W / 2 - tw / 2, m + D / 2 - T / 2, tw, T, True, 0.0)
    base.holes.append(hole)
    base.features.append(feat)
    asm.connect(f"{post_part.name}:oben", f"{base.name}:pfosten")

    fs = max(36.0, 0.9 * W)
    foot = Part(info.name("fuss"), rect(0.0, 0.0, fs, fs))
    feat2, hole2 = slot_feature("pfosten", fs / 2 - tw / 2, fs / 2 - T / 2, tw, T, True, 0.0)
    foot.holes.append(hole2)
    foot.features.append(feat2)
    foot.add_engrave(rect(2.0, 2.0, fs - 4.0, fs - 4.0), closed=True)
    asm.parts.append(foot)
    asm.connect(f"{post_part.name}:unten", f"{foot.name}:pfosten")
    for k, v, d in (("text", text, ""), ("schild_form", schild_form, "rahmen"), ("schrift", schrift, "normal"),
                    ("schreibweise", schreibweise, "gross"), ("dach", dach, "ziegel")):
        if v != d:
            asm.params[k] = v
    asm.notes.append(f"{name}: Pfosten in Fußplatte und Kastenboden stecken (ggf. mit Leim fixieren).")
    return asm
