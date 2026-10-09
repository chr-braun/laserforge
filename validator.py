"""
validator.py – Geometrie-Validator von Laserforge.

Prüft, bevor irgendeine Datei geschrieben wird:

  Pro Schnittpfad   geschlossen · Mindestlänge/-fläche · keine Doppelknoten · keine
                    Rückwärts-Spitzen · keine Selbstüberschneidung
  Pro Bauteil       Löcher liegen innerhalb der Außenkontur · keine zwei Schnitte berühren
                    oder kreuzen sich · Mindeststeg (min_web) zwischen Schnitten ·
                    Gravur liegt auf Material (nicht außerhalb, nicht über Löchern)
  Kerf              kompensierte Kontur liegt exakt kerf/2 neben der nominalen –
                    Außenkonturen nach außen, Innenschnitte nach innen
  Steckverbindungen jedes Feature ist genau einmal verbunden · Geometriepunkte liegen
                    wirklich auf der Kontur bzw. bilden ein Loch · Zinken komplementär,
                    gleiche Teilung, Tiefe = T · Tab/Slot 1:1 (Breite, Höhe = T, Position)
                    · Mindestbreite T + Kerf · Kreuzschlitze treffen sich exakt
  Blatt             Teile liegen auf dem Blatt und überlappen nicht

Ergebnis ist ein Report mit OK/FEHLER-Zeilen. Jede Verbindung wird namentlich geloggt.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

from laserforge import (Assembly, Config, JointFeature, Part, Point, Sheet, bbox, dist,
                        dist_to_boundary, edges, min_distance, perimeter, point_in_polygon,
                        point_seg_dist, segments_cross, signed_area)

GEO_EPS = 1e-4      # Toleranz für Geometrievergleiche (mm)
KERF_EPS = 2e-3     # Toleranz der Kerf-Prüfung (mm)


@dataclass
class Entry:
    status: str     # OK | FEHLER | INFO
    scope: str
    message: str

    def line(self) -> str:
        return f"{self.status:<7} [{self.scope}] {self.message}"


@dataclass
class Report:
    title: str = ""
    entries: List[Entry] = field(default_factory=list)

    def ok(self, scope: str, msg: str) -> None:
        self.entries.append(Entry("OK", scope, msg))

    def error(self, scope: str, msg: str) -> None:
        self.entries.append(Entry("FEHLER", scope, msg))

    def info(self, scope: str, msg: str) -> None:
        self.entries.append(Entry("INFO", scope, msg))

    @property
    def errors(self) -> List[Entry]:
        return [e for e in self.entries if e.status == "FEHLER"]

    @property
    def passed(self) -> bool:
        return not self.errors

    def extend(self, other: "Report") -> None:
        self.entries += other.entries

    def summary(self) -> str:
        n_ok = sum(1 for e in self.entries if e.status == "OK")
        verdict = "CUT-READY / OK" if self.passed else "FEHLER – keine Datei geschrieben"
        return f"{self.title}: {n_ok} Prüfungen OK, {len(self.errors)} FEHLER → {verdict}"

    def text(self) -> str:
        return "\n".join([e.line() for e in self.entries] + ["", self.summary()]) + "\n"


# ---------------------------------------------------------------------------
# Einzelpfad
# ---------------------------------------------------------------------------

def check_path(pts: Sequence[Point], closed: bool, cfg: Config) -> List[str]:
    """Fehlerliste für einen Schnittpfad (leer = OK)."""
    errs: List[str] = []
    n = len(pts)
    if not closed:
        errs.append("offene Kontur – Schnittpfade müssen geschlossen sein")
    if n < 3:
        return errs + [f"nur {n} Knoten"]
    if dist(pts[0], pts[-1]) < cfg.min_segment:
        errs.append("Start- und Endknoten doppelt (Kontur doppelt geschlossen)")
    for i, (a, b) in enumerate(edges(pts, True)):
        if dist(a, b) < cfg.min_segment:
            errs.append(f"Doppelknoten/Mini-Segment bei Knoten {i} ({a[0]:.3f}, {a[1]:.3f})")
    seen: Dict[Tuple[int, int], int] = {}
    for i, p in enumerate(pts):
        key = (round(p[0] / GEO_EPS), round(p[1] / GEO_EPS))
        if key in seen and not (i == n - 1 and seen[key] == 0):
            j = seen[key]
            if abs(i - j) > 1:
                errs.append(f"Knoten {j} und {i} liegen aufeinander ({p[0]:.3f}, {p[1]:.3f})")
        seen.setdefault(key, i)
    per = perimeter(pts)
    if per < cfg.min_path_length:
        errs.append(f"Kontur zu kurz ({per:.2f} mm < {cfg.min_path_length} mm)")
    area = abs(signed_area(pts))
    if area < cfg.min_area:
        errs.append(f"Fläche zu klein ({area:.2f} mm² < {cfg.min_area} mm²)")
    # Rückwärts-Spitzen (Kante läuft auf sich selbst zurück)
    for i in range(n):
        a, b, c = pts[i - 1], pts[i], pts[(i + 1) % n]
        ab, bc = dist(a, b), dist(b, c)
        if ab > 0 and bc > 0:
            dot = ((b[0] - a[0]) * (c[0] - b[0]) + (b[1] - a[1]) * (c[1] - b[1])) / (ab * bc)
            if dot < -1 + 1e-9:
                errs.append(f"Spitze/Rückwärtsschnitt bei Knoten {i}")
    # Selbstüberschneidung: nicht benachbarte Kanten dürfen sich nicht berühren
    es = edges(pts, True)
    boxes = [(min(a[0], b[0]), max(a[0], b[0]), min(a[1], b[1]), max(a[1], b[1])) for a, b in es]
    m = len(es)
    found = 0
    for i in range(m):
        x0, x1, y0, y1 = boxes[i]
        a, b = es[i]
        for j in range(i + 2, m):
            if i == 0 and j == m - 1:
                continue
            u0, u1, v0, v1 = boxes[j]
            if x1 < u0 - GEO_EPS or u1 < x0 - GEO_EPS or y1 < v0 - GEO_EPS or v1 < y0 - GEO_EPS:
                continue
            c, d = es[j]
            if segments_cross(a, b, c, d) or min(point_seg_dist(a, c, d), point_seg_dist(b, c, d),
                                                 point_seg_dist(c, a, b), point_seg_dist(d, a, b)) < GEO_EPS:
                found += 1
                if found <= 3:
                    errs.append(f"Selbstüberschneidung zwischen Kante {i} und {j} "
                                f"bei ({a[0]:.2f}, {a[1]:.2f})")
    if found > 3:
        errs.append(f"… insgesamt {found} Selbstüberschneidungen")
    return errs


# ---------------------------------------------------------------------------
# Bauteil
# ---------------------------------------------------------------------------

def check_part(part: Part, cfg: Config, label: str = "") -> List[str]:
    errs: List[str] = []
    pre = f"{label}: " if label else ""
    for e in check_path(part.outline, True, cfg):
        errs.append(pre + "Außenkontur – " + e)
    for k, h in enumerate(part.holes):
        for e in check_path(h, True, cfg):
            errs.append(pre + f"Innenschnitt {k} – " + e)
    if errs:
        return errs
    # Löcher innerhalb der Außenkontur, Stege, keine Überlappung
    paths = [part.outline] + list(part.holes)
    for k, h in enumerate(part.holes):
        if not all(point_in_polygon(p, part.outline) for p in h):
            errs.append(pre + f"Innenschnitt {k} liegt (teilweise) außerhalb der Außenkontur")
    for i in range(len(paths)):
        for j in range(i + 1, len(paths)):
            d = min_distance(paths[i], paths[j], limit=cfg.min_web)
            ni = "Außenkontur" if i == 0 else f"Innenschnitt {i - 1}"
            nj = f"Innenschnitt {j - 1}"
            if d < GEO_EPS:
                errs.append(pre + f"{ni} und {nj} schneiden/berühren sich (überlappende Schnitte)")
            elif d < cfg.min_web - GEO_EPS:
                errs.append(pre + f"Steg zwischen {ni} und {nj} nur {d:.2f} mm (< {cfg.min_web} mm)")
    for k, hi in enumerate(part.holes):
        for l, hj in enumerate(part.holes):
            if k != l and point_in_polygon(hi[0], hj):
                errs.append(pre + f"Innenschnitt {k} liegt in Innenschnitt {l} (Doppelschnitt)")
    # Gravur
    for k, s in enumerate(part.engrave):
        if len(s.points) < 2:
            errs.append(pre + f"Gravur {k} hat weniger als 2 Punkte")
            continue
        outside = [p for p in s.points
                   if not point_in_polygon(p, part.outline) and dist_to_boundary(p, part.outline) > GEO_EPS]
        if outside:
            errs.append(pre + f"Gravur {k} ragt über die Außenkontur ({outside[0][0]:.2f}, {outside[0][1]:.2f})")
        for h in part.holes:
            if any(point_in_polygon(p, h) and dist_to_boundary(p, h) > GEO_EPS for p in s.points):
                errs.append(pre + f"Gravur {k} liegt über einem Durchbruch")
                break
    return errs


def check_kerf(nominal: Part, comp: Part, cfg: Config) -> List[str]:
    """Kompensierte Kontur liegt kerf/2 neben der nominalen: außen größer, Löcher kleiner."""
    d = cfg.kerf_offset
    errs: List[str] = []
    if d <= 0:
        return errs
    pairs = [("Außenkontur", nominal.outline, comp.outline, True)] + \
        [(f"Innenschnitt {k}", h, comp.holes[k], False) for k, h in enumerate(nominal.holes)]
    for label, nom, cmp_, outer in pairs:
        a_nom, a_cmp = abs(signed_area(nom)), abs(signed_area(cmp_))
        if outer and not a_cmp > a_nom:
            errs.append(f"Kerf: {label} wurde nicht nach außen versetzt")
        if not outer and not a_cmp < a_nom:
            errs.append(f"Kerf: {label} wurde nicht nach innen versetzt")
        bad = 0
        for a, b in edges(nom, True):
            mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
            dd = dist_to_boundary(mid, cmp_)
            inside = point_in_polygon(mid, cmp_)
            # Nie näher als kerf/2; bei Kanten, die deutlich länger als der Versatz sind, exakt kerf/2.
            # (Sehr kurze Kanten neben Innenecken liegen geometrisch bedingt etwas weiter weg.)
            if dd < d - KERF_EPS or inside != outer or (dist(a, b) >= 4 * d and abs(dd - d) > KERF_EPS):
                bad += 1
        if bad:
            errs.append(f"Kerf: {label} – {bad} Kanten nicht exakt um {d:.3f} mm versetzt")
    return errs


# ---------------------------------------------------------------------------
# Steckverbindungen
# ---------------------------------------------------------------------------

def _on_outline(part: Part, pts: Sequence[Point]) -> bool:
    return all(dist_to_boundary(p, part.outline) < GEO_EPS for p in pts)


def _is_hole(part: Part, pts: Sequence[Point]) -> bool:
    bx = bbox(pts)
    for h in part.holes:
        hb = bbox(h)
        if len(h) == 4 and all(abs(u - v) < GEO_EPS for u, v in zip(bx, hb)):
            return True
    return False


def _is_round_hole(part: Part, pts: Sequence[Point]) -> bool:
    bx = bbox(pts)
    return any(len(h) > 8 and all(abs(u - v) < GEO_EPS for u, v in zip(bx, bbox(h))) for h in part.holes)


def check_feature_geometry(part: Part, f: JointFeature) -> Optional[str]:
    if f.kind in ("finger", "tab", "halving", "shaft"):
        if not _on_outline(part, f.points):
            return f"{f.kind} '{f.id}' passt nicht zur Kontur (Geometriepunkte liegen nicht auf dem Umriss)"
    elif f.kind in ("slot", "bore_square"):
        if not _is_hole(part, f.points):
            return f"{'Slot' if f.kind == 'slot' else 'Vierkant-Nabe'} '{f.id}' ist kein vorhandener Rechteck-Durchbruch"
    elif f.kind == "bore_round":
        if not _is_round_hole(part, f.points):
            return f"Lagerbohrung '{f.id}' ist kein vorhandener runder Durchbruch"
    else:
        return f"Unbekannter Verbindungstyp {f.kind!r}"
    return None


def check_connection(fa: JointFeature, fb: JointFeature, flip: bool, cfg: Config) -> Tuple[List[str], str]:
    """Liefert (Fehler, Beschreibung) für ein Feature-Paar."""
    T = cfg.T
    minw = cfg.min_tab_width
    errs: List[str] = []
    kinds = {fa.kind, fb.kind}
    if fa.kind == "finger" and fb.kind == "finger":
        sa = list(fa.segments)
        sb = list(reversed(fb.segments)) if flip else list(fb.segments)
        if abs(fa.length - fb.length) > GEO_EPS:
            errs.append(f"Kantenlängen {fa.length:.2f} ≠ {fb.length:.2f} mm")
        if len(sa) != len(sb):
            errs.append(f"Zinkenzahl {len(sa)} ≠ {len(sb)}")
        else:
            for i, ((wa, oa), (wb, ob)) in enumerate(zip(sa, sb)):
                if abs(wa - wb) > GEO_EPS:
                    errs.append(f"Zinken {i}: Breite {wa:.2f} ≠ {wb:.2f} mm")
                if oa == ob:
                    errs.append(f"Zinken {i}: nicht komplementär (beide {'belegt' if oa else 'frei'})")
                if wa < minw - GEO_EPS:
                    errs.append(f"Zinken {i}: Breite {wa:.2f} mm < T + Kerf = {minw:.2f} mm")
        for f in (fa, fb):
            if abs(f.depth - T) > GEO_EPS:
                errs.append(f"Zinkentiefe {f.depth:.2f} mm ≠ T = {T:.2f} mm")
        w = sa[0][0] if sa else 0
        desc = f"Zinken {len(sa)} × {w:.2f} mm auf {fa.length:.2f} mm, Tiefe {fa.depth:.2f} = T, komplementär"
        return errs, desc
    if kinds == {"tab", "slot"}:
        tab, slot = (fa, fb) if fa.kind == "tab" else (fb, fa)
        if abs(tab.length - slot.length) > GEO_EPS:
            errs.append(f"Tabbreite {tab.length:.2f} ≠ Slotlänge {slot.length:.2f} mm")
        if abs(tab.depth - T) > GEO_EPS:
            errs.append(f"Tabhöhe {tab.depth:.2f} mm ≠ T = {T:.2f} mm")
        if abs(slot.depth - T) > GEO_EPS:
            errs.append(f"Slotbreite {slot.depth:.2f} mm ≠ T = {T:.2f} mm")
        if tab.length < minw - GEO_EPS:
            errs.append(f"Tabbreite {tab.length:.2f} mm < T + Kerf = {minw:.2f} mm")
        if tab.pos is None or slot.pos is None or abs(tab.pos - slot.pos) > GEO_EPS:
            errs.append(f"Position Tab {tab.pos} ≠ Slot {slot.pos}")
        return errs, (f"Tab/Slot {tab.length:.2f} × {tab.depth:.2f} mm (Slot {slot.length:.2f} × "
                      f"{slot.depth:.2f}), Position {tab.pos:.2f} mm, 1:1")
    if fa.kind == "halving" and fb.kind == "halving":
        for f in (fa, fb):
            if abs(f.depth - T) > GEO_EPS:
                errs.append(f"Kreuzschlitz '{f.id}' Breite {f.depth:.2f} ≠ T = {T:.2f} mm")
            if f.span is None:
                errs.append(f"Kreuzschlitz '{f.id}' ohne Spanne")
        if fa.span and fb.span:
            if not (abs(fa.span[0] - fb.span[1]) < GEO_EPS or abs(fa.span[1] - fb.span[0]) < GEO_EPS):
                errs.append(f"Kreuzschlitze treffen sich nicht: {fa.span} / {fb.span}")
        total = fa.length + fb.length
        return errs, (f"Kreuzschlitz {fa.length:.2f} + {fb.length:.2f} = {total:.2f} mm, "
                      f"Breite {fa.depth:.2f} = T")
    if kinds in ({"shaft", "bore_square"}, {"shaft", "bore_round"}):
        shaft, bore = (fa, fb) if fa.kind == "shaft" else (fb, fa)
        if abs(shaft.length - T) > GEO_EPS:
            errs.append(f"Achsquerschnitt {shaft.length:.2f} mm ≠ T = {T:.2f} mm (Vierkant aus der Platte)")
        if shaft.span is None or shaft.span[1] - shaft.span[0] < T - GEO_EPS:
            errs.append(f"Achsabschnitt '{shaft.id}' kürzer als die Materialstärke")
        if shaft.pos is None or bore.pos is None or abs(shaft.pos - bore.pos) > GEO_EPS:
            errs.append(f"Achsposition {shaft.pos} ≠ Bohrung {bore.pos}")
        if bore.kind == "bore_square":
            if abs(bore.length - shaft.length) > GEO_EPS:
                errs.append(f"Vierkant-Nabe {bore.length:.2f} mm ≠ Achse {shaft.length:.2f} mm")
            return errs, (f"Achse ⇄ Rad: Vierkant {shaft.length:.2f} × {shaft.length:.2f} mm in Nabe "
                          f"{bore.length:.2f} mm, Pressitz 1:1, Achsposition {shaft.pos:.2f} mm")
        diag = shaft.length * math.sqrt(2)
        if bore.length < diag + 0.3 - GEO_EPS:
            errs.append(f"Lagerbohrung Ø {bore.length:.2f} mm < Achsdiagonale {diag:.2f} + 0.3 mm – Achse klemmt")
        if bore.length > diag + 2.0 + GEO_EPS:
            errs.append(f"Lagerbohrung Ø {bore.length:.2f} mm zu weit (Diagonale {diag:.2f} mm)")
        return errs, (f"Achse ⇄ Lager: Ø {bore.length:.2f} mm um Diagonale {diag:.2f} mm, "
                      f"Spiel {bore.length - diag:.2f} mm (dreht frei), Achsposition {shaft.pos:.2f} mm")
    return [f"Typen passen nicht zusammen: {fa.kind} ⇄ {fb.kind}"], ""


def check_joints(asm: Assembly, cfg: Config, report: Report) -> None:
    parts = {p.name: p for p in asm.parts}
    used: Dict[str, int] = {}
    for p in asm.parts:
        ids = [f.id for f in p.features]
        if len(ids) != len(set(ids)):
            report.error(p.name, "doppelte Feature-IDs")
        for f in p.features:
            used[f"{p.name}:{f.id}"] = 0
            g = check_feature_geometry(p, f)
            if g:
                report.error(p.name, g)
    for c in asm.connections:
        resolved = []
        for ref in (c.a, c.b):
            pname, _, fid = ref.partition(":")
            if pname not in parts:
                report.error("Verbindung", f"{ref}: Teil fehlt")
                break
            try:
                resolved.append(parts[pname].feature(fid))
            except KeyError:
                report.error("Verbindung", f"{ref}: Feature fehlt")
                break
            used[ref] = used.get(ref, 0) + 1
        if len(resolved) != 2:
            continue
        errs, desc = check_connection(resolved[0], resolved[1], c.flip, cfg)
        name = f"{c.a.replace(':', '.')} ⇄ {c.b.replace(':', '.')}"
        if errs:
            for e in errs:
                report.error("Verbindung", f"{name}: {e}")
        else:
            report.ok("Verbindung", f"{name} – {desc}")
    for ref, cnt in used.items():
        if cnt == 0:
            report.error("Verbindung", f"{ref.replace(':', '.')} ist mit nichts verbunden")
        elif cnt > 1:
            report.error("Verbindung", f"{ref.replace(':', '.')} ist {cnt}× verbunden")


# ---------------------------------------------------------------------------
# Baugruppe und Blätter
# ---------------------------------------------------------------------------

def validate_assembly(asm: Assembly, cfg: Config, report: Optional[Report] = None) -> Report:
    report = report or Report(asm.name)
    for p in asm.parts:
        errs = check_part(p, cfg, "nominal")
        comp = p.compensated(cfg.kerf_offset)
        if not errs:
            errs += check_part(comp, cfg, f"kompensiert (kerf {cfg.kerf} mm)")
        if not errs:
            errs += check_kerf(p, comp, cfg)
        if errs:
            for e in errs:
                report.error(p.name, e)
        else:
            w, h = p.size()
            report.ok(p.name, f"{w:.1f} × {h:.1f} mm · Außenkontur geschlossen ({len(p.outline)} Knoten) · "
                              f"{len(p.holes)} Innenschnitte · {len(p.engrave)} Gravuren · "
                              f"keine Selbstüberschneidung/Überlappung · Kerf ±{cfg.kerf_offset:.2f} mm OK")
    check_joints(asm, cfg, report)
    return report


def validate_sheets(sheets: Sequence[Sheet], cfg: Config, report: Report) -> None:
    for sh in sheets:
        scope = f"Blatt {sh.index}"
        bad = False
        boxes = [p.bbox() for p in sh.parts]
        for p, (x0, y0, x1, y1) in zip(sh.parts, boxes):
            if x0 < -GEO_EPS or y0 < -GEO_EPS or x1 > sh.width + GEO_EPS or y1 > sh.height + GEO_EPS:
                report.error(scope, f"{p.name} liegt außerhalb des Blatts")
                bad = True
        lim = cfg.min_web
        for i in range(len(sh.parts)):
            for j in range(i + 1, len(sh.parts)):
                a, b = boxes[i], boxes[j]
                if a[2] + lim < b[0] or b[2] + lim < a[0] or a[3] + lim < b[1] or b[3] + lim < a[1]:
                    continue
                pi, pj = sh.parts[i], sh.parts[j]
                d = min_distance(pi.outline, pj.outline, limit=lim)
                inside = point_in_polygon(pi.outline[0], pj.outline) or point_in_polygon(pj.outline[0], pi.outline)
                if d < lim - GEO_EPS or inside:
                    report.error(scope, f"{pi.name} und {pj.name} überlappen/zu dicht ({d:.2f} mm)")
                    bad = True
        if not bad:
            report.ok(scope, f"{len(sh.parts)} Teile auf {sh.width:.0f} × {sh.height:.0f} mm, "
                             f"keine Überlappung, Abstand ≥ {cfg.min_web} mm")


# ---------------------------------------------------------------------------
# SVG-Datei-Prüfung (unabhängig vom Generator: liest das fertige SVG zurück)
# ---------------------------------------------------------------------------

def _parse_d(d: str):
    """Liest einen Pfad aus M/L/H/V/Z-Befehlen (absolut). Liefert (Punkte, geschlossen)."""
    import re
    toks = re.findall(r"[MLHVZmlhvz]|-?\d*\.?\d+(?:[eE][-+]?\d+)?", d)
    pts: List[Point] = []
    closed = False
    cmd = None
    i = 0
    while i < len(toks):
        t = toks[i]
        if t.isalpha():
            if t not in "MLHVZ":
                raise ValueError(f"Pfadbefehl {t!r} nicht unterstützt (nur absolute M/L/H/V/Z)")
            cmd = t
            i += 1
            if cmd == "Z":
                closed = True
            continue
        if cmd in ("M", "L"):
            pts.append((float(toks[i]), float(toks[i + 1])))
            i += 2
        elif cmd == "H":
            pts.append((float(toks[i]), pts[-1][1]))
            i += 1
        elif cmd == "V":
            pts.append((pts[-1][0], float(toks[i])))
            i += 1
        else:
            raise ValueError("Zahl ohne Pfadbefehl")
    return pts, closed


def validate_svg_text(text: str, cfg: Config, name: str = "SVG", report: Optional[Report] = None) -> Report:
    """Prüft ein fertiges SVG: mm-Einheiten, nur Schnitt-/Gravurfarbe, alle Schnittpfade geschlossen
    und ohne Selbstüberschneidung, Innenschnitte im Teil, keine überlappenden Schnitte zwischen Teilen."""
    import xml.etree.ElementTree as ET
    report = report or Report(name)
    scope = f"Datei {name}"
    try:
        root = ET.fromstring(text)
    except ET.ParseError as e:
        report.error(scope, f"kein gültiges XML: {e}")
        return report
    ns = "{http://www.w3.org/2000/svg}"
    w, h = root.get("width", ""), root.get("height", "")
    if not (w.endswith("mm") and h.endswith("mm")):
        report.error(scope, f"Breite/Höhe nicht in mm ({w!r}, {h!r}) – Maßstab beim Import unsicher")
        return report
    W, H = float(w[:-2]), float(h[:-2])
    vb = [float(v) for v in root.get("viewBox", "0 0 0 0").split()]
    if abs(vb[2] - W) > GEO_EPS or abs(vb[3] - H) > GEO_EPS:
        report.error(scope, "viewBox passt nicht zu den mm-Maßen (1 Einheit ≠ 1 mm)")
    groups: Dict[str, List[List[Point]]] = {}
    n_cut = n_eng = 0
    errors_before = len(report.errors)
    for g in root.iter(ns + "g"):
        for p in g.findall(ns + "path"):
            stroke = (p.get("stroke") or g.get("stroke") or "").lower()
            if (p.get("fill") or g.get("fill") or "none").lower() != "none":
                report.error(scope, f"Pfad in {g.get('id')} ist gefüllt (fill ≠ none)")
            try:
                pts, closed = _parse_d(p.get("d", ""))
            except (ValueError, IndexError) as e:
                report.error(scope, f"{g.get('id')}: {e}")
                continue
            if stroke == cfg.cut_color.lower():
                n_cut += 1
                for e in check_path(pts, closed, cfg):
                    report.error(scope, f"{g.get('id')}: {e}")
                groups.setdefault(g.get("id", "?"), []).append(pts)
            elif stroke == cfg.engrave_color.lower():
                n_eng += 1
            else:
                report.error(scope, f"{g.get('id')}: unbekannte Linienfarbe {stroke!r}")
    if len(report.errors) > errors_before:
        return report
    outlines = []
    for gid, paths in groups.items():
        paths = sorted(paths, key=lambda q: -abs(signed_area(q)))
        outer = paths[0]
        part = Part(gid, outer, paths[1:])
        for e in check_part(part, cfg):
            report.error(scope, f"{gid}: {e}")
        outlines.append((gid, outer, bbox(outer)))
    for gid, outer, (x0, y0, x1, y1) in outlines:
        if x0 < -GEO_EPS or y0 < -GEO_EPS or x1 > W + GEO_EPS or y1 > H + GEO_EPS:
            report.error(scope, f"{gid} ragt über das Blatt")
    lim = cfg.min_web
    for i in range(len(outlines)):
        for j in range(i + 1, len(outlines)):
            (ga, pa, a), (gb, pb, b) = outlines[i], outlines[j]
            if a[2] + lim < b[0] or b[2] + lim < a[0] or a[3] + lim < b[1] or b[3] + lim < a[1]:
                continue
            if min_distance(pa, pb, limit=lim) < lim - GEO_EPS or point_in_polygon(pa[0], pb) \
                    or point_in_polygon(pb[0], pa):
                report.error(scope, f"{ga} und {gb} überlappen/zu dicht")
    if len(report.errors) == errors_before:
        report.ok(scope, f"{W:.0f} × {H:.0f} mm · {len(groups)} Teile · {n_cut} Schnittpfade geschlossen, "
                         f"ohne Überschneidung/Überlappung · {n_eng} Gravurpfade · Farben "
                         f"{cfg.cut_color}/{cfg.engrave_color}")
    return report
