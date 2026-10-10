"""
schneeflocke.py – parametrische Schneeflocken mit sechszähliger Symmetrie.

Jede Flocke entsteht aus einem Seed: Armbreite, Zahl/Lage/Länge der Seitenäste (immer
parallel zum Nachbararm, wie bei echten Eiskristallen), Spitzenform und Mittelloch variieren.
Gleicher Seed = gleiche Flocke. Die Konturen werden direkt aus der Geometrie berechnet
(keine Polygon-Booleans); die Abstandsregeln garantieren, dass sich Äste nie berühren.

  flach   Anhänger mit Öse an der oberen Spitze
  3d      zwei Flocken mit Kreuzschlitz entlang der senkrechten Achse zum Zusammenstecken
"""
from __future__ import annotations

import math
import random
from typing import List, Optional, Tuple

from steckwerk import (Assembly, Config, JointFeature, Part, Point, arc_points, circle, clean,
                        mirror_x, rotate)
from models._shapes import cut_axis_slot

DEFAULTS = dict(size=80.0)
SIN60, COS60 = math.sqrt(3) / 2, 0.5
TIPS = ["spitz", "flach", "raute"]


def _branch(h: float, yb: float, L: float, hb: float) -> Tuple[List[Point], float, float]:
    """Punkte eines rechten Seitenasts (Richtung 30°), plus y-Werte seines Ansatzes am Arm."""
    dx, dy = SIN60, COS60                       # Richtung parallel zum rechten Nachbararm
    t_lo = (h - COS60 * hb) / SIN60
    t_up = (h + COS60 * hb) / SIN60
    p_lo = (h, yb - SIN60 * hb + COS60 * t_lo)
    p_up = (h, yb + SIN60 * hb + COS60 * t_up)
    tip_lo = (COS60 * hb + L * dx, yb - SIN60 * hb + L * dy)
    tip_up = (-COS60 * hb + L * dx, yb + SIN60 * hb + L * dy)
    cap = ((L + hb) * dx, yb + (L + hb) * dy)
    return [p_lo, tip_lo, cap, tip_up, p_up], p_lo[1], p_up[1]


def _arm(h: float, branches, L_arm: float, tip: str, eye: Optional[Tuple[float, float]], tol: float):
    """Ein Arm (Achse +y) vom rechten bis zum linken Innenwinkel."""
    right: List[Point] = [(h, math.sqrt(3) * h)]
    for yb, L, hb in branches:
        pts, _, _ = _branch(h, yb, L, hb)
        right += pts
    if eye:
        cy, re = eye
        y_meet = cy - math.sqrt(re * re - h * h)
        right.append((h, y_meet))
        a0 = math.atan2(y_meet - cy, h)
        top = arc_points(0.0, cy, re, a0, math.pi - a0, tol)[1:-1]
        return right + top + mirror_x(right)
    right.append((h, L_arm))
    if tip == "spitz":
        top = [(0.0, L_arm + 1.8 * h)]
    elif tip == "raute":
        top = [(1.9 * h, L_arm + 1.3 * h), (0.0, L_arm + 3.2 * h), (-1.9 * h, L_arm + 1.3 * h)]
    else:
        top = []
    return right + top + mirror_x(right)


class Flake:
    def __init__(self, R: float, h: float, branches, tip: str, center_hole: float):
        self.R, self.h, self.branches, self.tip, self.center_hole = R, h, branches, tip, center_hole

    def tip_len(self) -> float:
        return {"spitz": 1.8, "raute": 3.2, "flach": 0.0}[self.tip] * self.h

    def outline(self, eye: Optional[Tuple[float, float]] = None, tol: float = 0.05) -> List[Point]:
        L_arm = self.R - self.tip_len()
        pts: List[Point] = []
        for k in range(6):
            arm = _arm(self.h, self.branches, L_arm, self.tip, eye if k == 0 else None, tol)
            pts += rotate(arm, k * math.pi / 3)
        return clean(pts)


def design(R: float, cfg: Config, rng: random.Random, three_d: bool) -> Flake:
    """Zufälliger, aber kollisionsfreier Entwurf.

    Ast i (Höhe y_i, Länge L_i) an Arm 0 und Ast j am Nachbararm bilden eine Raute; sie treffen
    sich nur, wenn L_i ≳ y_j und L_j ≳ y_i. Mit L_i < y_i − Rand (für jeden Ast) ist das für
    alle Paare ausgeschlossen – damit dürfen äußere Äste lang werden."""
    T, web = cfg.T, max(cfg.min_web, 1.2)
    h_min = (T / 2 + max(2.0, 0.7 * T)) if three_d else 1.5
    if three_d and R < 4.0 * h_min:
        raise ValueError(f"3D-Schneeflocke bei {T:g} mm Material erst ab {2 * 4.0 * h_min:.0f} mm Durchmesser")
    h = max(h_min, rng.uniform(0.05, 0.075) * R)
    tip = rng.choice(TIPS)
    L_arm = R - {"spitz": 1.8, "raute": 3.2, "flach": 0.0}[tip] * h
    hb = max(1.0, rng.uniform(0.55, 0.85) * h)
    t_up = (h + COS60 * hb) / SIN60                          # Astansatz an der Armkante
    side = hb + (hb + web + 0.6) / SIN60                     # Rand zum Ast des Nachbararms
    gap = (2 * hb + web + 0.6) / SIN60                       # Mindestabstand paralleler Äste
    y_min = max((h + hb + web + 0.4) / SIN60, math.sqrt(3) * h + 2 * hb + 1.5,
                t_up + 3.0 + side, 0.22 * R)
    y_max = L_arm - hb - 2.5 * h
    n = rng.choice([1, 2, 2, 3, 3])
    ys: List[float] = []
    if y_max > y_min:
        for i in range(n):
            f = (i + 0.5 + rng.uniform(-0.25, 0.25)) / n
            y = y_min + f * (y_max - y_min)
            if all(abs(y - o) >= gap for o in ys):
                ys.append(y)
    ys.sort()
    branches = []
    for y in ys:
        L = min((y - side) * rng.uniform(0.55, 0.95), 0.42 * R, (L_arm - y) * 1.6)
        if L >= t_up + 1.8:
            branches.append((y, L, hb))
    hole = 0.0
    if not three_d and rng.random() < 0.6:
        hole = min(1.45 * h, (2 * h - web - 0.8) / SIN60)
    return Flake(R, h, branches, tip, hole if hole > 1.2 else 0.0)


def _decorate(part: Part, fl: Flake, three_d: bool, tol: float, stop0: Optional[float] = None) -> None:
    """Gravierte Mittellinien; stop0 = Ende der Linie im oberen Arm (vor dem Ösenloch)."""
    h, R = fl.h, fl.R
    L_arm = R - fl.tip_len()
    r0 = (fl.center_hole + 1.2) if fl.center_hole else 1.2 * h
    for k in range(6):
        if three_d and k in (0, 3):
            continue
        ang = k * math.pi / 3
        end = min(L_arm - 0.8, stop0) if (k == 0 and stop0) else L_arm - 0.8
        if end > r0 + 2.0:
            part.add_engrave(rotate([(0.0, r0 + 0.8), (0.0, end)], ang))
        for yb, L, hb in fl.branches:
            t_up = (h + COS60 * hb) / SIN60
            for sx in (1, -1):
                a = (sx * SIN60 * (t_up + 0.6), yb + COS60 * (t_up + 0.6))
                b = (sx * SIN60 * (L - 0.3), yb + COS60 * (L - 0.3))
                part.add_engrave(rotate([a, b], ang))
    if not three_d and not fl.center_hole:
        ring = [(1.05 * h * math.cos(math.pi / 2 + k * math.pi / 3),
                 1.05 * h * math.sin(math.pi / 2 + k * math.pi / 3)) for k in range(6)]
        part.add_engrave(ring, closed=True)


def _valid(parts: List[Part], cfg: Config) -> bool:
    from validator import check_part
    return all(not check_part(p, cfg) and not check_part(p.compensated(cfg.kerf_offset), cfg) for p in parts)


def make(cfg: Config, name: str, R: float, seed: int, three_d: bool) -> List[Part]:
    tol = cfg.arc_tolerance
    rng = random.Random(seed)
    fl = design(R, cfg, rng, three_d)
    rh = min(max(1.75, 0.05 * R), 3.0)
    re = max(rh + max(2.2, 0.6 * cfg.T), fl.h + 1.2)          # Öse breiter als der Arm
    for attempt in range(8):
        eye_cy = R - fl.tip_len() + re * 0.6 if fl.tip != "flach" else R + re * 0.55
        eye = (eye_cy, re)
        parts: List[Part] = []
        try:
            if not three_d:
                p = Part(name, fl.outline(eye, tol))
                p.add_hole(circle(0.0, eye_cy, rh, tol))
                if fl.center_hole:
                    p.add_hole([(fl.center_hole * math.cos(math.pi / 2 + k * math.pi / 3),
                                 fl.center_hole * math.sin(math.pi / 2 + k * math.pi / 3)) for k in range(6)])
                _decorate(p, fl, False, tol, eye_cy - rh - 1.2)
                parts = [p]
            else:
                top = R + 3 * re
                a_out, a_slot = cut_axis_slot(fl.outline(None, tol), cfg.T, 0.0, True)
                b_out, b_slot = cut_axis_slot(fl.outline(eye, tol), cfg.T, 0.0, False)
                A = Part(f"{name}_a", a_out, features=[
                    JointFeature("kreuz", "halving", R, cfg.T, span=(0.0, top), points=a_slot)])
                B = Part(f"{name}_b", b_out, features=[
                    JointFeature("kreuz", "halving", R, cfg.T, span=(-R, 0.0), points=b_slot)])
                B.add_hole(circle(0.0, eye_cy, rh, tol))
                _decorate(A, fl, True, tol)
                _decorate(B, fl, True, tol, eye_cy - rh - 1.2)
                parts = [A, B]
        except ValueError:
            parts = []
        if parts and _valid(parts, cfg):
            return parts
        # nachschärfen: Äste kürzen, zuletzt ganz weglassen, Mittelloch verkleinern
        fl.branches = [(y, L * 0.82, hb) for y, L, hb in fl.branches
                       if L * 0.82 >= (fl.h + COS60 * hb) / SIN60 + 1.8] if attempt < 6 else []
        fl.center_hole = fl.center_hole * 0.8 if fl.center_hole > 1.5 else 0.0
    return parts            # Validator meldet verbleibende Fehler


def build(cfg: Config, name: str = "schneeflocke", size: Optional[float] = None,
          height: Optional[float] = None, width: Optional[float] = None, count: int = 1,
          seed: Optional[int] = None, three_d: bool = False) -> Assembly:
    """count Flocken (Seed, Seed+1, …). size = Durchmesser Spitze–Spitze in mm."""
    D = cfg.s(size or height or width or DEFAULTS["size"])
    seed = cfg.seed if seed is None else seed
    if not (1 <= count <= 60):
        raise ValueError("count muss zwischen 1 und 60 liegen")
    if D < 30:
        raise ValueError("Schneeflocke zu klein (min. 30 mm)")
    asm = Assembly(name, params=dict(size=D, count=count, seed=seed, three_d=three_d))
    for i in range(count):
        parts = make(cfg, f"flocke_{seed + i:03d}", D / 2, seed + i, three_d)
        asm.parts += parts
        if three_d:
            asm.connect(f"{parts[0].name}:kreuz", f"{parts[1].name}:kreuz")
    asm.notes.append("Schneeflocken: Band durch die Öse an der oberen Spitze.")
    if three_d:
        asm.notes.append("3D: Flocke B (Schlitz unten, mit Öse) von oben in Flocke A (Schlitz oben) schieben.")
    return asm
