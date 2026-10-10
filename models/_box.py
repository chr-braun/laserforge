"""
_box.py – gemeinsamer Kasten-Generator für Wichtelhaus, Anbau, Laterne und Briefkasten.

Aufbau (3D-Koordinaten: x = Breite, y = Tiefe, z = Höhe)
  * vorne/hinten   W × H, bei top='gable' mit Giebeldreieck. Senkrechte Kanten mit Zinken
                   im 'notch'-Modus (Kerben), sie besitzen die Eckwürfel bei geraden Segmenten.
  * links/rechts   (D − 2T) × H, senkrechte Kanten mit Zinken im 'tab'-Modus – exakt komplementär.
  * boden          (W + 2m) × (D + 2m) Sockelplatte; alle Wände stecken mit Tabs in Slots.
  * dach_links/    (D + 2·Überstand) × (Dachschräge + Traufe); die Giebel stecken mit Tabs,
    dach_rechts    senkrecht zur Schräge, durch Slots im Dach (Tab-Höhe = T = Dachstärke).
  * deckel         bei top='slots': flache Platte, Wände stecken oben mit Tabs darin.

Alle Verbindungsmaße sind Vielfache von T (Holzstärken-Skalierung) und werden als
JointFeature an den Teilen hinterlegt, damit der Validator sie 1:1 prüfen kann.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

from steckwerk import (Assembly, Config, JointFeature, Part, Point, bbox, clean, finger_count,
                        finger_feature, finger_segments, profile_edge, rect, slot_feature,
                        tab_centers, tab_features, tab_segments)


@dataclass
class BoxInfo:
    prefix: str
    W: float
    D: float
    H: float
    T: float
    top: str
    pitch: float = 0.0          # rad
    G: float = 0.0              # Giebelhöhe über Traufe
    S: float = 0.0              # Länge der Dachschräge (Traufecke → First)
    overhang: float = 0.0       # Dachüberstand an den Giebeln
    eave: float = 0.0           # Dachüberstand an der Traufe
    base_margin: float = 0.0
    lid_margin: float = 0.0
    front_extra: float = 0.0    # Vorplatz: Bodenplatte ragt vorne so weit zusätzlich hervor

    @property
    def Ds(self) -> float:
        return self.D - 2 * self.T

    def name(self, suffix: str) -> str:
        return f"{self.prefix}_{suffix}"


def _pair_by_pos(asm: Assembly, pa: Part, fa: Sequence[JointFeature], pb: Part,
                 fb: Sequence[JointFeature]) -> None:
    """Tabs und Slots nach ihrer gemeinsamen Position paaren (Validator prüft die Gleichheit)."""
    for a, b in zip(sorted(fa, key=lambda f: f.pos), sorted(fb, key=lambda f: f.pos)):
        asm.connect(f"{pa.name}:{a.id}", f"{pb.name}:{b.id}")


def build_box(prefix: str, W: float, D: float, H: float, cfg: Config, top: str = "gable",
              pitch_deg: float = 45.0, base_margin: Optional[float] = None,
              overhang: Optional[float] = None, eave: Optional[float] = None,
              lid_margin: Optional[float] = None, front_extra: float = 0.0) -> Tuple[Assembly, BoxInfo]:
    T = cfg.T
    if top not in ("gable", "slots", "none"):
        raise ValueError("top muss 'gable', 'slots' oder 'none' sein")
    if min(W, D, H) < 6 * T:
        raise ValueError(f"{prefix}: Maße {W:.1f}×{D:.1f}×{H:.1f} zu klein für T={T} mm")
    info = BoxInfo(prefix, W, D, H, T, top)
    info.base_margin = base_margin if base_margin is not None else max(2 * T, 5.0)
    info.lid_margin = lid_margin if lid_margin is not None else max(T, 3.0)
    info.front_extra = max(0.0, front_extra)
    if top == "gable":
        if not (15 <= pitch_deg <= 65):
            raise ValueError("Dachneigung muss zwischen 15° und 65° liegen")
        info.pitch = math.radians(pitch_deg)
        info.G = (W / 2) * math.tan(info.pitch)
        info.S = (W / 2) / math.cos(info.pitch)
        info.overhang = overhang if overhang is not None else max(4.0, 0.07 * D)
        info.eave = eave if eave is not None else max(5.0, 0.12 * info.S)

    asm = Assembly(prefix, params={"W": W, "D": D, "H": H, "top": top, "pitch_deg": pitch_deg})
    Ds = info.Ds

    # gemeinsame Teilungen ----------------------------------------------------
    n_v = finger_count(H, cfg)
    notch = finger_segments(H, n_v, T, "notch")
    tabz = finger_segments(H, n_v, T, "tab")
    bx_c, bx_w = tab_centers(W, cfg, inset=2 * T)        # Bodentabs vorne/hinten
    by_c, by_w = tab_centers(Ds, cfg, inset=T)           # Bodentabs Seiten
    if top == "gable":
        rs_c, rs_w = tab_centers(info.S, cfg, inset=2.5 * T)   # Dachtabs auf der Schräge
    if top == "slots":
        tx_c, tx_w = tab_centers(W, cfg, inset=2 * T)
        ty_c, ty_w = tab_centers(Ds, cfg, inset=T)

    # Giebelwände vorne/hinten -------------------------------------------------
    walls_xz: Dict[str, Part] = {}
    for side in ("vorne", "hinten"):
        # lokales x → 3D-x
        to3d = (lambda t: t) if side == "vorne" else (lambda t, W=W: W - t)
        feats: List[JointFeature] = []
        pts: List[Point] = []
        p0, p1, p2, p3 = (0.0, 0.0), (W, 0.0), (W, H), (0.0, H)
        pts += profile_edge(p0, p1, tab_segments(W, bx_c, bx_w, T))
        feats += tab_features("boden", p0, p1, bx_c, bx_w, T, to3d)
        pts += profile_edge(p1, p2, notch)
        feats.append(finger_feature("zinken_r", p1, p2, notch, "notch", T))
        if top == "gable":
            peak = (W / 2, H + info.G)
            S = info.S
            pts += profile_edge(p2, peak, tab_segments(S, rs_c, rs_w, T))
            feats += tab_features("dach_r", p2, peak, rs_c, rs_w, T, lambda t: t)
            left_c = sorted(S - c for c in rs_c)
            pts += profile_edge(peak, p3, tab_segments(S, left_c, rs_w, T))
            feats += tab_features("dach_l", peak, p3, left_c, rs_w, T, lambda t, S=S: S - t)
        elif top == "slots":
            c_local = sorted(W - c for c in tx_c)
            pts += profile_edge(p2, p3, tab_segments(W, c_local, tx_w, T))
            feats += tab_features("deckel", p2, p3, c_local, tx_w, T, lambda t, f=to3d: f(W - t))
        else:
            pts.append(p2)
        pts += profile_edge(p3, p0, notch[::-1])
        feats.append(finger_feature("zinken_l", p3, p0, notch[::-1], "notch", T))
        part = Part(info.name(side), clean(pts), features=feats)
        walls_xz[side] = part
        asm.parts.append(part)

    # Seitenwände --------------------------------------------------------------
    walls_yz: Dict[str, Part] = {}
    for side in ("links", "rechts"):
        to3d = lambda t: T + t                              # lokales x → 3D-y
        feats = []
        pts = []
        p0, p1, p2, p3 = (0.0, 0.0), (Ds, 0.0), (Ds, H), (0.0, H)
        pts += profile_edge(p0, p1, tab_segments(Ds, by_c, by_w, T))
        feats += tab_features("boden", p0, p1, by_c, by_w, T, to3d)
        pts += profile_edge(p1, p2, tabz)
        feats.append(finger_feature("zinken_h", p1, p2, tabz, "tab", T))
        if top == "slots":
            c_local = sorted(Ds - c for c in ty_c)
            pts += profile_edge(p2, p3, tab_segments(Ds, c_local, ty_w, T))
            feats += tab_features("deckel", p2, p3, c_local, ty_w, T, lambda t: T + Ds - t)
        else:
            pts.append(p2)
        pts += profile_edge(p3, p0, tabz[::-1])
        feats.append(finger_feature("zinken_v", p3, p0, tabz[::-1], "tab", T))
        part = Part(info.name(side), clean(pts), features=feats)
        walls_yz[side] = part
        asm.parts.append(part)

    vo, hi, li, re = walls_xz["vorne"], walls_xz["hinten"], walls_yz["links"], walls_yz["rechts"]
    asm.connect(f"{vo.name}:zinken_l", f"{li.name}:zinken_v")
    asm.connect(f"{vo.name}:zinken_r", f"{re.name}:zinken_v", flip=True)
    asm.connect(f"{hi.name}:zinken_r", f"{li.name}:zinken_h")
    asm.connect(f"{hi.name}:zinken_l", f"{re.name}:zinken_h", flip=True)

    # Platten mit Slots (Boden, ggf. Deckel) -------------------------------------
    def slotted_plate(pname: str, m: float, tag: str, fe: float = 0.0) -> Part:
        plate = Part(info.name(pname), rect(0, -fe, W + 2 * m, D + 2 * m + fe))
        for wall, y3 in ((vo, 0.0), (hi, D - T)):
            fl = [f for f in wall.features if f.kind == "tab" and f.id.startswith(tag)]
            sl = []
            for f in fl:
                feat, hole = slot_feature(f"{wall.name.split('_')[-1]}_{f.id}", m + f.pos - f.length / 2,
                                          m + y3, f.length, T, True, f.pos)
                plate.holes.append(hole)
                plate.features.append(feat)
                sl.append(feat)
            _pair_by_pos(asm, wall, fl, plate, sl)
        for wall, x3 in ((li, 0.0), (re, W - T)):
            fl = [f for f in wall.features if f.kind == "tab" and f.id.startswith(tag)]
            sl = []
            for f in fl:
                feat, hole = slot_feature(f"{wall.name.split('_')[-1]}_{f.id}", m + x3,
                                          m + f.pos - f.length / 2, T, f.length, False, f.pos)
                plate.holes.append(hole)
                plate.features.append(feat)
                sl.append(feat)
            _pair_by_pos(asm, wall, fl, plate, sl)
        asm.parts.append(plate)
        return plate

    slotted_plate("boden", info.base_margin, "boden", info.front_extra)
    if top == "slots":
        slotted_plate("deckel", info.lid_margin, "deckel")

    # Satteldach ------------------------------------------------------------------
    if top == "gable":
        ov, e, S = info.overhang, info.eave, info.S
        L = D + 2 * ov
        roofs = {}
        for rside in ("links", "rechts"):
            roofs[rside] = Part(info.name(f"dach_{rside}"), rect(0, 0, L, S + e))
            asm.parts.append(roofs[rside])
        # (Wand, lokale Schräge) → Dachseite. hinten ist gespiegelt: lokal links = 3D rechts.
        mapping = [(vo, "dach_l", "links", 0.0), (vo, "dach_r", "rechts", 0.0),
                   (hi, "dach_l", "rechts", D - T), (hi, "dach_r", "links", D - T)]
        for wall, tag, rside, y3 in mapping:
            roof = roofs[rside]
            fl = [f for f in wall.features if f.kind == "tab" and f.id.startswith(tag)]
            sl = []
            for f in fl:
                wname = wall.name.split("_")[-1]
                feat, hole = slot_feature(f"{wname}_{f.id}", ov + y3, e + f.pos - f.length / 2,
                                          T, f.length, False, f.pos)
                roof.holes.append(hole)
                roof.features.append(feat)
                sl.append(feat)
            _pair_by_pos(asm, wall, fl, roof, sl)
        asm.notes.append(f"{prefix}: Dach am First mit etwas Holzleim verbinden (Firstfuge ist gewollt).")

    asm.notes.append(f"{prefix}: Seitenwände zwischen Vorder- und Rückwand stecken, dann alle Wände "
                     f"in die Bodenplatte drücken.")
    return asm, info


# ---------------------------------------------------------------------------
# Dekor-Helfer
# ---------------------------------------------------------------------------

def _subtract(a: float, b: float, blocked: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    segs = [(a, b)]
    for u, v in sorted(blocked):
        nxt = []
        for s, t in segs:
            if v <= s or u >= t:
                nxt.append((s, t))
                continue
            if u > s:
                nxt.append((s, u))
            if v < t:
                nxt.append((v, t))
        segs = nxt
    return [(s, t) for s, t in segs if t - s > 1.0]


def engrave_shingles(part: Part, row: float = 6.0, tile: float = 8.0, margin: float = 2.0,
                     clearance: float = 1.2, skip_top: float = 0.0) -> None:
    """Dachziegel-Gravur (Reihen + versetzte Fugen), spart Slots/Löcher aus."""
    x0, y0, x1, y1 = part.bbox()
    hb = [bbox(h) for h in part.holes]
    y = y0 + margin + row
    k = 0
    while y < y1 - margin - skip_top:
        blocked = [(b[0] - clearance, b[2] + clearance) for b in hb
                   if b[1] - clearance <= y <= b[3] + clearance]
        for s, t in _subtract(x0 + margin, x1 - margin, blocked):
            part.add_engrave([(s, y), (t, y)])
        # senkrechte Fugen zwischen dieser und der vorigen Reihe
        ya, yb_ = y - row, y
        xx = x0 + margin + (tile / 2 if k % 2 else tile)
        while xx < x1 - margin - 1:
            if ya >= y0 + margin - 1e-9 and not any(
                    b[0] - clearance <= xx <= b[2] + clearance and not (yb_ < b[1] - clearance or ya > b[3] + clearance)
                    for b in hb):
                part.add_engrave([(xx, ya), (xx, yb_)])
            xx += tile
        y += row
        k += 1


def window_cross(part: Part, cx: float, cy: float, w: float, h: float, cfg: Config,
                 mode: str = "cut", sill: bool = True) -> None:
    """Sprossenfenster: 4 Scheiben als Durchbruch (cut) oder komplett als Gravur."""
    mull = max(1.6 * cfg.min_web, 0.12 * min(w, h))
    pw, ph = (w - mull) / 2, (h - mull) / 2
    x0, y0 = cx - w / 2, cy - h / 2
    if mode == "cut":
        for ix in range(2):
            for iy in range(2):
                part.add_hole(rect(x0 + ix * (pw + mull), y0 + iy * (ph + mull), pw, ph))
    else:
        part.add_engrave(rect(x0, y0, w, h), closed=True)
        part.add_engrave([(cx, y0), (cx, y0 + h)])
        part.add_engrave([(x0, cy), (x0 + w, cy)])
    if sill:
        part.add_engrave([(x0 - 2, y0 - 1.5), (x0 + w + 2, y0 - 1.5)])
        part.add_engrave([(x0 - 1, y0 + h + 1.5), (x0 + w + 1, y0 + h + 1.5)])
