"""
zaun.py – Gartenzaun-Segment (Staketenzaun) mit Steckleiste.

Latten mit Spitzen, zwei Querriegel. Die Zwischenräume unter/über den Riegeln sind Teil der
Außenkontur, die Felder zwischen den Riegeln sind Innenschnitte. Zwei Latten haben unten
Tabs, die in die Bodenleiste gesteckt werden.
"""
from __future__ import annotations

from typing import List, Optional

from laserforge import (Assembly, Config, JointFeature, Part, Point, clean, profile_edge, rect,
                        slot_feature)

DEFAULTS = dict(width=120.0, height=45.0)


def build(cfg: Config, name: str = "zaun", width: Optional[float] = None,
          height: Optional[float] = None, picket: float = 8.0, gap: float = 5.0) -> Assembly:
    T = cfg.T
    Lw = cfg.s(width or DEFAULTS["width"])
    Hf = cfg.s(height or DEFAULTS["height"])
    pw, g = cfg.s(picket), cfg.s(gap)
    n = max(3, int((Lw + g) // (pw + g)))
    L = n * pw + (n - 1) * g
    rw = max(0.11 * Hf, 2.5 * cfg.min_web)        # Riegelhöhe
    a1, a2 = 0.2 * Hf, 0.6 * Hf
    hp = Hf - pw / 2                                # Schulter (Spitze darüber)
    xs = [i * (pw + g) for i in range(n)]
    tw = max(cfg.min_tab_width, min(0.62 * pw, cfg.tab_factor * T))
    tab_idx = [1, n - 2] if n >= 5 else [0, n - 1]

    pts: List[Point] = []
    feats = []
    for i, x in enumerate(xs):                      # Unterseite links → rechts
        if i in tab_idx:
            a = (pw - tw) / 2
            pts += profile_edge((x, 0.0), (x + pw, 0.0), [(a, 0.0), (tw, T), (a, 0.0)])
            feats.append(JointFeature(f"fuss{tab_idx.index(i)}", "tab", tw, T, pos=x + pw / 2,
                                      points=[(x + a, 0.0), (x + a, -T), (x + a + tw, -T), (x + a + tw, 0.0)]))
        else:
            pts.append((x, 0.0))
        pts.append((x + pw, 0.0))
        if i < n - 1:
            pts += [(x + pw, a1), (xs[i + 1], a1)]
    for i in range(n - 1, -1, -1):                  # Oberseite rechts → links
        x = xs[i]
        pts += [(x + pw, hp), (x + pw / 2, Hf), (x, hp)]
        if i > 0:
            pts += [(x, a2 + rw), (xs[i - 1] + pw, a2 + rw)]
    fence = Part(f"{name}_feld", clean(pts), features=feats)
    for i in range(n - 1):
        fence.add_hole(rect(xs[i] + pw, a1 + rw, g, a2 - a1 - rw))
    # Holzmaserung auf den Riegeln
    for y in (a1 + rw / 2, a2 + rw / 2):
        fence.add_engrave([(1.0, y), (L - 1.0, y)])

    # Bodenleiste
    m = max(4.0, 2 * T)
    depth = max(12.0, 4 * T)
    strip = Part(f"{name}_leiste", rect(0.0, 0.0, L + 2 * m, depth))
    sl = []
    for f in feats:
        feat, hole = slot_feature(f"{f.id}", m + f.pos - tw / 2, depth / 2 - T / 2, tw, T, True, f.pos)
        strip.holes.append(hole)
        strip.features.append(feat)
        sl.append(feat)
    for k in range(int((L + 2 * m) // 9)):          # Grasbüschel
        x = 4.0 + k * 9.0
        if x + 4.0 > L + 2 * m - 2.0:
            break
        if any(abs(x + 1.5 - (m + f.pos)) < tw / 2 + 3.0 for f in feats):
            continue
        strip.add_engrave([(x, 2.0), (x + 1.5, depth - 3.0), (x + 3.0, 2.0)])

    asm = Assembly(name, params={"width": L, "height": Hf, "pickets": n})
    asm.parts += [fence, strip]
    for a, b in zip(feats, sl):
        asm.connect(f"{fence.name}:{a.id}", f"{strip.name}:{b.id}")
    asm.notes.append(f"{name}: Zaunfeld mit den Fuß-Tabs in die Leiste stecken; mehrere Felder "
                     f"hintereinander ergeben einen langen Zaun.")
    return asm
