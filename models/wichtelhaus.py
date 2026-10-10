"""
wichtelhaus.py – parametrisches Wichtelhaus.

4 Wände mit Zinken, Satteldach (Giebel stecken per Tab im Dach), Sockel-Bodenplatte,
Tür und Fenster als Durchbruch oder Gravur, rückseitiger Licht-Durchbruch für ein
LED-Teelicht/Ballonlicht, optional Kamin und Anbau (für Serien).

Gestaltung (alles optional, siehe Style):
  fenster        rechteck · rund · bogen · spitzbogen · raute · herz · stern
  sprossen       kreuz · senkrecht · waagrecht · keine
  fenster_deko   rahmen · laeden · herzlaeden · blumen · beides · schnee · keine
  door           arched · rect · spitzbogen · rund · none        tuer_deko: rahmen · vordach · laternen ·
                                                                            girlande · kranz · keine
  giebel         rundfenster · herz · stern · uhr · luke · text · keins   (+ giebel_text)
  wand           keine · holz · ziegel · stein · fachwerk · schuppen · putz · sterne · herzen
  dach           ziegel · biber · schindel · reet · schnee · sterne · keine
  zierleiste     keine · linie · doppelt · gestrichelt · punkte · wellen · zickzack · zuckerguss ·
                 eiszapfen · lichterkette · girlande · sterne · herzen  (Giebel, Traufe, Dachkante)
  schild         Text über der Tür (schild_form: rahmen · rund · oval · banner · holz · geschweift · ohne)
  text_hinten    Text auf der Rückwand
  vorplatz       keiner · weg · matte · garten · alles  (+ matte_text) – Bodenplatte wird vorne länger
  schrift        normal · fett · kursiv · schmal · breit · schatten;  schreibweise: gross · normal
"""
from __future__ import annotations

import math
import zlib
from dataclasses import asdict, dataclass, fields
from typing import Optional

from steckwerk import (Assembly, Config, JointFeature, Part, circle, clean, edge_frame, profile_edge,
                        rect, slot_feature, tab_segments)
from models import _deko as dk
from models._box import BoxInfo, build_box
from models._font import CASES, STYLES, unsupported

DEFAULTS = dict(width=80.0, depth=70.0, height=65.0, pitch=45.0)
DOOR_ALIASES = {"square": "rect", "rechteck": "rect", "bogen": "arched", "rundbogen": "arched", "keine": "none"}


@dataclass
class Style:
    fenster: str = "rechteck"
    sprossen: str = "kreuz"
    fenster_deko: str = "rahmen"
    tuer_deko: str = "rahmen"
    giebel: str = "rundfenster"
    giebel_text: str = ""
    wand: str = "keine"
    dach: str = "ziegel"
    zierleiste: str = "keine"
    schild: str = ""
    schild_form: str = "rahmen"
    text_hinten: str = ""
    vorplatz: str = "keiner"
    matte_text: str = ""
    schrift: str = "normal"
    schreibweise: str = "gross"

    def check(self) -> "Style":
        dk.check_choice("Fenster", self.fenster, dk.WINDOW_FORMS)
        dk.check_choice("Sprossen", self.sprossen, dk.MUNTINS)
        dk.check_choice("Fensterschmuck", self.fenster_deko, dk.WINDOW_DECO)
        dk.check_choice("Türschmuck", self.tuer_deko, dk.DOOR_DECO)
        dk.check_choice("Giebel", self.giebel, dk.GABLES)
        dk.check_choice("Wand", self.wand, dk.WALLS)
        dk.check_choice("Dach", self.dach, dk.ROOFS)
        dk.check_choice("Zierleiste", self.zierleiste, dk.TRIMS)
        dk.check_choice("Schildform", self.schild_form, dk.SIGNS)
        dk.check_choice("Vorplatz", self.vorplatz, dk.YARDS)
        if self.schrift not in STYLES:
            raise ValueError(f"Schrift {self.schrift!r} unbekannt – erlaubt: {', '.join(STYLES)}")
        if self.schreibweise not in CASES:
            raise ValueError(f"Schreibweise {self.schreibweise!r} unbekannt – erlaubt: {', '.join(CASES)}")
        for label, t in (("Schild", self.schild), ("Giebeltext", self.giebel_text),
                         ("Text hinten", self.text_hinten), ("Fußmatte", self.matte_text)):
            bad = unsupported(t or "")
            if bad:
                raise ValueError(f"{label}: Zeichen {''.join(bad)!r} gibt es in der Gravurschrift nicht")
        return self

    @classmethod
    def from_kwargs(cls, **kw) -> "Style":
        names = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in kw.items() if k in names and v is not None}).check()


STYLE_KEYS = [f.name for f in fields(Style)]


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def _seed(cfg: Config, name: str) -> int:
    return (cfg.seed * 7919 + zlib.crc32(name.encode("utf-8"))) & 0x7FFFFFFF


def _hf(form: str) -> float:
    """Höhe/Breite einer Fensterform."""
    return {"bogen": 1.3, "spitzbogen": 1.35, "raute": 1.25, "herz": 0.92}.get(form, 1.0)


SHUTTERS = ("laeden", "herzlaeden", "beides")


def _shutter_fit(deco: str, ws: float, ws_shutter: float) -> str:
    """Fensterläden nur, wenn das Fenster dafür nicht zu sehr schrumpfen muss – sonst Rahmen
    (bei „beides“ bleibt der Blumenkasten)."""
    if deco in SHUTTERS and ws_shutter < max(0.75 * ws, 6.0):
        return "blumen" if deco == "beides" else "rahmen"
    return deco


def _unit(H: float) -> float:
    return _clamp(H / 13.0, 3.2, 6.0)


def _trim_size(H: float) -> float:
    return _clamp(0.075 * H, 3.0, 5.5)


def _band(path, size, side=-1):
    """Fläche einer Zierleiste (zum Freihalten für das Wandmuster)."""
    return list(path) + dk.offset_path(path, side * size)[::-1]


def _gable_trim(cv: dk.Canvas, info: BoxInfo, st: Style, seed: int) -> None:
    if st.zierleiste == "keine" or info.top != "gable":
        return
    W, H, G = info.W, info.H, info.G
    size = _trim_size(H)
    path = dk.offset_path([(0.0, H), (W / 2, H + G), (W, H)], -2.0)
    dk.styled_line(cv, path, st.zierleiste, size, side=-1, seed=seed)
    band = _band(path, size)
    if len(band) >= 3:
        cv.block(band, 0.3)


def _pattern(cv: dk.Canvas, st: Style, box, H: float, seed: int, rails=(), gable=None) -> None:
    dk.wall_pattern(cv, st.wand, box, _unit(H), seed, rails, gable)


def decorate_front(part: Part, info: BoxInfo, cfg: Config, windows: int = 2,
                   door: str = "arched", mode: str = "cut", door_mode: Optional[str] = None,
                   gable_window: bool = True, st: Optional[Style] = None, seed: int = 1) -> None:
    st = st or Style()
    W, H, T, G = info.W, info.H, info.T, info.G
    tol = cfg.arc_tolerance
    door = DOOR_ALIASES.get(door, door)
    dk.check_choice("Tür", door, dk.DOORS)
    door_mode = door_mode or mode
    gable = info.top == "gable"
    area = [(T, 0.0), (W - T, 0.0), (W - T, H), (W / 2, H + G), (T, H)] if gable else rect(T, 0, W - 2 * T, H)
    cv = dk.Canvas(part, margin=1.2, area=area, seed=seed)

    # Tür -------------------------------------------------------------------------
    dw, dh = dk.door_size(door, W, H)
    y0 = max(3.0, T)
    door_top = y0
    if door != "none":
        door_top = dk.add_door(cv, door, W / 2, y0, dw, dh, door_mode, st.tuer_deko, tol, seed, with_deco=False)

    # Fenster links/rechts der Tür – Größe passt sich dem Platz zwischen Zinkenkerbe und Tür an
    hf = _hf(st.fenster)

    wdeco = st.fenster_deko

    def window_size(extra):
        nonlocal wdeco
        door_half = dw / 2 + 1.5 + extra if door != "none" else 0.0
        lo = T + cfg.min_web + 2.5                 # Kerbe + Steg + Fensterbank-Überstand
        hi = W / 2 - door_half - cfg.min_web - 2.5
        ws = min(_clamp(min(0.17 * W, 0.26 * H), 8.0, 20.0), hi - lo, (0.62 * H - 4.0) / hf)
        wdeco = _shutter_fit(st.fenster_deko, ws, (hi - lo + 3.0) / 1.9 - 1.0)
        if wdeco in SHUTTERS:
            ws = min(ws, (hi - lo + 3.0) / 1.9 - 1.0)
        return ws, lo, hi

    # Laternen neben der Tür brauchen Platz – Fenster haben aber Vorrang
    ws, lo, hi = window_size(2 * 1.6 + _clamp(0.3 * dw, 3.5, 7.0) + 0.6 if st.tuer_deko == "laternen" else 0.0)
    if ws < 6.0:
        ws, lo, hi = window_size(0.0)
    rails = []
    if ws >= 6.0 and windows > 0:
        cx_l = (lo + hi) / 2
        xs = [W - cx_l] if windows == 1 else [cx_l, W - cx_l]
        cy = 0.6 * H
        for cx in xs:
            dk.add_window(cv, st.fenster, cx, cy, ws, ws * hf, mode, st.sprossen, wdeco, cfg.min_web, tol)
        rails += [cy - ws * hf / 2 - 3.5, cy + ws * hf / 2 + 3.0]
    # Giebel ------------------------------------------------------------------------
    gable_box = None
    if gable and gable_window:
        r = min(0.2 * G, 0.09 * W, 9.0)
        cyg = H + G * 0.36
        tb = (W / 2 - 0.3 * W, H + 0.1 * G, W / 2 + 0.3 * W, H + 0.52 * G)
        gable_box = dk.gable_deco(cv, st.giebel, W / 2, cyg, r, mode, st.giebel_text, st.schrift,
                                  st.schreibweise, tb, tol)
        if st.giebel == "text" and st.giebel_text.strip() and gable_box is None:
            raise ValueError(f"Giebeltext {st.giebel_text!r} passt nicht in den Giebel – kürzer fassen, "
                             f"Schrift „schmal“ wählen oder das Haus breiter machen")
    # Schild über der Tür (hat Vorrang vor Vordach/Kranz/Girlande, die sonst entfallen) -------
    if st.schild.strip():
        top_lim = gable_box[1] - 1.5 if gable_box else (H + 0.5 * G if gable else H - 2.0)
        extra = dk.door_deco_height(st.tuer_deko, dw, door_mode) if door != "none" else 0.0
        tries = [extra, 0.0] if extra else [0.0]
        got = None
        for ex in tries:
            if door != "none":
                cands = [(T + 2.0, door_top + ex + 1.5, W - T - 2.0, top_lim)]
            else:
                cands = [(T + 2.0, max(y0, 0.12 * H), W - T - 2.0, top_lim)]
            if gable and not gable_box:
                cands.append((T + 2.0, H + 0.08 * G, W - T - 2.0, H + 0.62 * G))
            got = dk.sign(cv, st.schild, st.schild_form, cands, st.schrift, st.schreibweise,
                          min_h=2.5, max_cap=_clamp(0.11 * W, 4.0, 10.0),
                          anchor="unten" if door != "none" else "mitte", tol=tol)
            if got:
                break
        if got is None:
            raise ValueError(f"Schild {st.schild!r} passt nicht über die Tür – kürzer fassen, Schrift „schmal“ "
                             f"wählen, Giebel auf „nichts“ stellen oder das Haus größer machen")
    if door != "none":
        dk.door_deco(cv, door, W / 2, y0, dw, dh, door_mode, st.tuer_deko, tol, seed)
    _gable_trim(cv, info, st, seed)
    if gable:
        rails.append(H)
    _pattern(cv, st, (T, 0.0, W - T, H + G if gable else H), H, seed, rails,
             (W / 2, H, H + G) if gable else None)


def decorate_side(part: Part, info: BoxInfo, cfg: Config, windows: int = 1, mode: str = "cut",
                  st: Optional[Style] = None, seed: int = 1) -> None:
    st = st or Style()
    Ds, H = info.Ds, info.H
    cv = dk.Canvas(part, margin=1.2, area=rect(0.0, 0.0, Ds, H), seed=seed)
    size = _trim_size(H)
    if st.zierleiste != "keine":
        path = [(0.0, H - 1.6), (Ds, H - 1.6)]
        dk.styled_line(cv, path, st.zierleiste, size, side=-1, seed=seed)
        cv.block(_band(path, size), 0.3)
    rails = []
    if windows > 0:
        hf = max(1.15, _hf(st.fenster))
        ws = min(_clamp(min(0.55 * Ds / windows, 0.3 * H), 8.0, 18.0), Ds / (windows + 1) - 5.0,
                 0.6 * H / hf)
        wdeco = _shutter_fit(st.fenster_deko, ws, (Ds / (windows + 1) - 3.0) / 1.9 - 1.0)
        if wdeco in SHUTTERS:
            ws = min(ws, (Ds / (windows + 1) - 3.0) / 1.9 - 1.0)
        if ws >= 6.0:
            cy = 0.55 * H
            for i in range(windows):
                dk.add_window(cv, st.fenster, Ds * (i + 1) / (windows + 1), cy, ws, ws * hf, mode,
                              st.sprossen, wdeco, cfg.min_web, cfg.arc_tolerance)
            rails += [cy - ws * hf / 2 - 3.5, cy + ws * hf / 2 + 3.0]
    _pattern(cv, st, (0.0, 0.0, Ds, H), H, seed, rails)


def decorate_back(part: Part, info: BoxInfo, cfg: Config, light: bool = True,
                  light_diameter: float = 40.0, mode: str = "cut", st: Optional[Style] = None,
                  seed: int = 1) -> None:
    st = st or Style()
    W, H, T, G = info.W, info.H, info.T, info.G
    tol = cfg.arc_tolerance
    gable = info.top == "gable"
    area = [(T, 0.0), (W - T, 0.0), (W - T, H), (W / 2, H + G), (T, H)] if gable else rect(T, 0, W - 2 * T, H)
    cv = dk.Canvas(part, margin=1.2, area=area, seed=seed)
    d = cy = 0.0
    if light:
        d = min(light_diameter, 0.62 * W, 0.62 * H)
        cy = max(0.42 * H, d / 2 + 5.0)
        cv.add_hole(circle(W / 2, cy, d / 2, tol))
        part.note = f"Licht-Durchbruch Ø {d:.1f} mm für LED-Teelicht/Ballonlicht"
    gable_box = None
    if gable and st.giebel != "keins":
        r = min(0.16 * G, 0.07 * W, 7.0)
        kind = st.giebel if st.giebel in ("rundfenster", "herz", "stern") else "rundfenster"
        if r >= 3.0:
            gable_box = dk.gable_deco(cv, kind, W / 2, H + G * 0.36, r, mode, tol=tol)
    if st.text_hinten.strip():
        top_lim = gable_box[1] - 1.5 if gable_box else (H + 0.55 * G if gable else H - 2.0)
        if light:
            cands = [(T + 2.0, cy + d / 2 + 2.0, W - T - 2.0, top_lim), (T + 2.0, 2.0, W - T - 2.0, cy - d / 2 - 2.0)]
        else:
            cands = [(T + 2.0, 0.25 * H, W - T - 2.0, min(top_lim, 0.85 * H)), (T + 2.0, 2.0, W - T - 2.0, top_lim)]
        got = dk.sign(cv, st.text_hinten, "ohne", cands, st.schrift, st.schreibweise, min_h=2.5,
                      max_cap=_clamp(0.12 * W, 4.0, 12.0), anchor="mitte", tol=tol)
        if got is None:
            raise ValueError(f"Text hinten {st.text_hinten!r} passt nicht auf die Rückwand – kürzer fassen, "
                             f"Lichtloch kleiner machen oder das Haus größer")
    _gable_trim(cv, info, st, seed)
    _pattern(cv, st, (T, 0.0, W - T, H + G if gable else H), H, seed, [H] if gable else [],
             (W / 2, H, H + G) if gable else None)


def decorate_roof(part: Part, info: BoxInfo, st: Optional[Style] = None, seed: int = 1) -> None:
    st = st or Style()
    x0, y0, x1, y1 = part.bbox()
    cv = dk.Canvas(part, margin=1.2, hole_margin=1.0, seed=seed)
    start = y0
    if st.zierleiste != "keine":
        size = _trim_size(info.H)
        yp = y0 + 1.4 + size
        path = [(x0, yp), (x1, yp)]
        dk.styled_line(cv, path, st.zierleiste, size, side=-1, seed=seed)
        cv.block(_band(path, size), 0.3)
        start = yp + 0.6
    dk.roof_pattern(cv, st.dach, (x0, start, x1, y1), 6.0, seed)


def decorate_base(part: Part, info: BoxInfo, cfg: Config, door: str, st: Style, seed: int) -> None:
    if st.vorplatz == "keiner" or info.front_extra <= 0:
        return
    m, F = info.base_margin, info.front_extra
    x0, _, x1, _ = part.bbox()
    cv = dk.Canvas(part, margin=1.2, area=rect(x0, -F, x1 - x0, F + m - 0.6), seed=seed)
    dw, _ = dk.door_size(DOOR_ALIASES.get(door, door), info.W, info.H)
    dk.yard(cv, st.vorplatz, m + info.W / 2, m, F + m, dw, (x0 + 1.5, x1 - 1.5), st.matte_text,
            st.schrift, st.schreibweise, seed)


def add_chimney(asm: Assembly, info: BoxInfo, cfg: Config, along: float = 0.68,
                up: float = 0.3) -> Part:
    """Kamin: Platte parallel zum Giebel, Unterkante in Dachneigung, Tab senkrecht zur
    Schräge durch einen Slot im linken Dach (gleiches Prinzip wie die Giebel-Tabs)."""
    T, a = cfg.T, info.pitch
    roof = asm.part(info.name("dach_links"))
    cw = max(12.0, 0.16 * info.W)
    Lb = cw / math.cos(a)
    hc = max(10.0, 0.2 * info.H)
    top = cw * math.tan(a) + hc
    tw = max(cfg.min_tab_width, min(cfg.tab_factor * T, 0.5 * Lb))
    p0, p1 = (0.0, 0.0), (cw, cw * math.tan(a))
    rim, rh = 1.5, 3.5
    pts = profile_edge(p0, p1, tab_segments(Lb, [Lb / 2], tw, T))
    pts += [p1, (cw, top), (cw + rim, top), (cw + rim, top + rh), (-rim, top + rh), (-rim, top), (0.0, top)]
    u0 = info.eave + up * info.S                       # tiefe Ecke auf der Dachplatte
    pos = u0 + Lb / 2
    _, at = edge_frame(p0, p1)
    tab = JointFeature("dach0", "tab", tw, T, pos=pos,
                       points=[at(Lb / 2 - tw / 2, 0), at(Lb / 2 - tw / 2, T),
                               at(Lb / 2 + tw / 2, T), at(Lb / 2 + tw / 2, 0)])
    ch = Part(info.name("kamin"), clean(pts), features=[tab])
    # Ziegel-Gravur
    y = 4.0
    k = 0
    while y < top - 2.0:
        xmax = min(cw, y / math.tan(a)) - 1.0
        if xmax - 1.0 > 2.0:
            ch.add_engrave([(1.0, y), (xmax, y)])
            x = 1.0 + (3.5 if k % 2 else 7.0)
            while x < xmax - 1.0 and y + 4.0 < top - 0.5:
                ch.add_engrave([(x, y), (x, min(y + 4.0, top - 1.0))])
                x += 7.0
        y += 4.0
        k += 1
    asm.parts.append(ch)
    yc = along * info.D
    feat, hole = slot_feature("kamin0", info.overhang + yc, pos - tw / 2, T, tw, False, pos)
    roof.holes.append(hole)
    roof.features.append(feat)
    asm.connect(f"{ch.name}:dach0", f"{roof.name}:kamin0")
    asm.notes.append(f"{info.prefix}: Kamin von oben in den Schlitz im linken Dach stecken.")
    return ch


def build(cfg: Config, name: str = "wichtelhaus", width: Optional[float] = None,
          depth: Optional[float] = None, height: Optional[float] = None,
          pitch: float = DEFAULTS["pitch"], front_windows: int = 2, side_windows: int = 1,
          door: str = "arched", light: bool = True, light_diameter: float = 40.0,
          chimney: bool = True, annex: bool = False, openings: Optional[str] = None,
          **style) -> Assembly:
    """Erzeugt ein komplettes Wichtelhaus. Maße in mm (vor Maßstab); Gestaltung über die
    Schlüssel von Style (fenster=…, wand=…, schild=… usw.)."""
    unknown = set(style) - set(STYLE_KEYS)
    if unknown:
        raise TypeError(f"Unbekannte Option(en) {', '.join(sorted(unknown))} – erlaubt: {', '.join(STYLE_KEYS)}")
    st = Style.from_kwargs(**style)
    door = DOOR_ALIASES.get(door, door)
    dk.check_choice("Tür", door, dk.DOORS)
    W = cfg.s(width or DEFAULTS["width"])
    D = cfg.s(depth or DEFAULTS["depth"])
    H = cfg.s(height or DEFAULTS["height"])
    mode = openings or cfg.openings
    fe = _clamp(0.4 * D, 18.0, 45.0) if st.vorplatz != "keiner" else 0.0
    asm, info = build_box(name, W, D, H, cfg, top="gable", pitch_deg=pitch, front_extra=fe)
    changed = {k: v for k, v in asdict(st).items() if v != getattr(Style, k)}
    asm.params.update(front_windows=front_windows, side_windows=side_windows, door=door,
                      light=light, chimney=chimney, annex=annex, openings=mode, **changed)
    seed = _seed(cfg, name)
    decorate_front(asm.part(info.name("vorne")), info, cfg, front_windows, door, mode,
                   door_mode="cut" if mode == "cut" else "engrave", st=st, seed=seed)
    decorate_back(asm.part(info.name("hinten")), info, cfg, light, cfg.s(light_diameter), mode, st, seed + 1)
    decorate_side(asm.part(info.name("links")), info, cfg, side_windows, mode, st, seed + 2)
    decorate_side(asm.part(info.name("rechts")), info, cfg, max(side_windows - (1 if annex else 0), 0)
                  if annex else side_windows, mode, st, seed + 3)
    if chimney:
        add_chimney(asm, info, cfg)
    for k, r in enumerate(("dach_links", "dach_rechts")):
        decorate_roof(asm.part(info.name(r)), info, st, seed + 4 + k)
    decorate_base(asm.part(info.name("boden")), info, cfg, door, st, seed + 6)
    if fe:
        asm.notes.append(f"{name}: Bodenplatte mit {fe:.0f} mm Vorplatz – die gravierte Seite nach oben.")
    if annex:
        aW, aD, aH = round(0.48 * W, 1), round(0.72 * D, 1), round(0.62 * H, 1)
        sub, sinfo = build_box(f"{name}_anbau", aW, aD, aH, cfg, top="gable", pitch_deg=pitch)
        sst = Style(**{**asdict(st), "schild": "", "giebel": "keins", "text_hinten": "", "vorplatz": "keiner",
                       "tuer_deko": "rahmen" if st.tuer_deko in ("laternen", "girlande") else st.tuer_deko})
        decorate_front(sub.part(sinfo.name("vorne")), sinfo, cfg, windows=0,
                       door="arched" if door in ("none", "rund") else door,
                       mode=mode, door_mode="engrave", gable_window=False, st=sst, seed=seed + 10)
        decorate_side(sub.part(sinfo.name("rechts")), sinfo, cfg, 1, mode, sst, seed + 11)
        decorate_back(sub.part(sinfo.name("hinten")), sinfo, cfg, False, 0.0, mode, sst, seed + 13)
        for k, r in enumerate(("dach_links", "dach_rechts")):
            decorate_roof(sub.part(sinfo.name(r)), sinfo, sst, seed + 14 + k)
        sub.notes.append(f"{name}: Anbau rechts an das Haus kleben (Vorderkanten bündig).")
        asm.merge(sub)
    return asm
