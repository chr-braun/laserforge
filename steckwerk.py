"""
steckwerk.py – Kern-Engine von Steckwerk.

Enthält
  * Config            zentrale Parameter (Materialstärke T, Kerf, Farben, Blattgröße …)
  * Geometrie-Helfer  Polygone, Kreisbögen, Bezier, Schnitt- und Abstandstests
  * Kerf-Offset       Polygon-Offset mit Gehrung bzw. Fase an spitzen Ecken
  * Part / Assembly   Bauteile mit Schnittkonturen, Gravur und Steckverbindungs-Features
  * Kantenprofile     Zinken (Fingerverbindung) und Tabs entlang beliebiger Kanten
  * Layout + SVG      Anordnung auf Laserbett-Blättern, LightBurn-kompatibler Export

Konventionen
  * Alle Maße in mm. Modelle konstruieren mit y nach OBEN (Mathe-Konvention);
    erst beim Export wird nach SVG (y nach unten) gespiegelt.
  * Außenkonturen laufen gegen den Uhrzeigersinn (CCW), Löcher im Uhrzeigersinn (CW).
    Damit zeigt die rechte Normale (dy, -dx) jeder Kante immer aus dem Material heraus –
    ein einziger Offset mit +kerf/2 vergrößert Außenkonturen und verkleinert Löcher.
  * Nur Standardbibliothek. PyYAML wird genutzt, falls installiert (sonst Mini-Parser).
"""
from __future__ import annotations

import json
import math
import os
import re
from dataclasses import dataclass, field, fields
from typing import Callable, Dict, List, Optional, Sequence, Tuple

__version__ = "2.2.0"


def migrate_legacy(home: Optional[str] = None) -> List[str]:
    """Bis 1.7 hieß Steckwerk „Laserforge“: dessen Datenordner (Pakete, Motive, Einstellungen)
    einmalig umbenennen, solange es noch keinen Steckwerk-Ordner gibt. Liefert die verschobenen Ordner."""
    home = home or os.path.expanduser("~")
    pairs = [(os.path.join(home, "Library", "Application Support", "Laserforge"),
              os.path.join(home, "Library", "Application Support", "Steckwerk")),
             (os.path.join(home, ".laserforge"), os.path.join(home, ".steckwerk")),
             (os.path.join(home, ".local", "state", "Laserforge"), os.path.join(home, ".local", "state", "Steckwerk"))]
    if os.environ.get("APPDATA") and home == os.path.expanduser("~"):
        pairs.append((os.path.join(os.environ["APPDATA"], "Laserforge"), os.path.join(os.environ["APPDATA"], "Steckwerk")))
    moved = []
    for old, new in pairs:
        if os.path.isdir(old) and not os.path.exists(new):
            try:
                os.rename(old, new)
                moved.append(new)
            except OSError:
                pass
    return moved

Point = Tuple[float, float]
EPS = 1e-6


# ---------------------------------------------------------------------------
# Konfiguration
# ---------------------------------------------------------------------------

class ConfigError(ValueError):
    """Ungültige Parameter (z. B. Kerf größer als Materialstärke)."""


@dataclass
class Config:
    thickness: float = 3.0         # Materialstärke T in mm
    kerf: float = 0.2              # Schnittbreite des Lasers in mm (wird je Seite mit kerf/2 kompensiert)
    units: str = "mm"              # einzige unterstützte Einheit
    scale: float = 1.0             # Maßstab der Modelle (T bleibt unverändert!)
    finger_factor: float = 3.0     # Ziel-Zinkenbreite  = finger_factor * T  (Holzstärken-Skalierung)
    tab_factor: float = 3.0        # Ziel-Tabbreite     = tab_factor * T
    cut_color: str = "#000000"     # LightBurn-Layer 00: Schnitt
    engrave_color: str = "#0000FF" # LightBurn-Layer 01: Gravur
    stroke_width: float = 0.1      # Haarlinie in mm
    sheet_width: float = 400.0     # nutzbares Laserbett / Plattengröße
    sheet_height: float = 300.0
    sheet_margin: float = 5.0      # Rand zum Plattenrand
    part_spacing: float = 4.0      # Abstand zwischen Teilen
    min_segment: float = 0.02      # kürzeres Segment = Doppelknoten
    min_path_length: float = 2.0   # Mindest-Umfang einer Schnittkontur
    min_area: float = 1.0          # Mindestfläche einer Schnittkontur in mm²
    min_web: float = 1.0           # Mindest-Materialsteg zwischen zwei Schnitten
    arc_tolerance: float = 0.05    # max. Sehnenabweichung bei Kreisbögen
    openings: str = "cut"          # Fenster/Türen: "cut" (Durchbruch) oder "engrave" (Gravur)
    seed: int = 7                  # Zufallsstartwert für Serien

    def __post_init__(self):
        self.check()

    def check(self) -> None:
        if self.units != "mm":
            raise ConfigError("Nur 'mm' wird als Einheit unterstützt.")
        if not (0.5 <= self.thickness <= 20):
            raise ConfigError(f"Materialstärke {self.thickness} mm außerhalb 0.5–20 mm.")
        if not (0 <= self.kerf < self.thickness / 2):
            raise ConfigError(f"Kerf {self.kerf} mm muss zwischen 0 und T/2 liegen.")
        if self.scale <= 0:
            raise ConfigError("Maßstab muss > 0 sein.")
        if self.openings not in ("cut", "engrave"):
            raise ConfigError("openings muss 'cut' oder 'engrave' sein.")
        if self.finger_factor < 1.5 or self.tab_factor < 1.5:
            raise ConfigError("finger_factor/tab_factor müssen >= 1.5 sein.")
        for c in (self.cut_color, self.engrave_color):
            if not (isinstance(c, str) and c.startswith("#") and len(c) == 7):
                raise ConfigError(f"Farbe {c!r} muss als #RRGGBB angegeben werden.")
        if self.cut_color.lower() == self.engrave_color.lower():
            raise ConfigError("Schnitt- und Gravurfarbe müssen verschieden sein.")
        if self.sheet_width < 50 or self.sheet_height < 50:
            raise ConfigError("Blatt zu klein (mind. 50 × 50 mm).")

    # abgeleitete Größen -------------------------------------------------
    @property
    def T(self) -> float:
        return self.thickness

    @property
    def kerf_offset(self) -> float:
        """Versatz je Seite: der Laser trägt links und rechts der Linie je kerf/2 ab."""
        return self.kerf / 2.0

    @property
    def min_tab_width(self) -> float:
        """Mindestbreite eines Zinkens/Tabs: T + Kerf."""
        return self.thickness + self.kerf

    def s(self, v: float) -> float:
        """Modellmaß mit dem Maßstab skalieren."""
        return v * self.scale

    # Laden / Speichern -------------------------------------------------
    def to_dict(self) -> dict:
        return {f.name: getattr(self, f.name) for f in fields(self)}

    @classmethod
    def from_dict(cls, data: dict) -> "Config":
        known = {f.name: f for f in fields(cls)}
        unknown = sorted(set(data) - set(known))
        if unknown:
            raise ConfigError(f"Unbekannte Config-Schlüssel: {', '.join(unknown)}")
        kwargs = {}
        for k, v in data.items():
            typ = known[k].type
            if typ in ("float", float):
                v = float(v)
            elif typ in ("int", int):
                v = int(v)
            elif typ in ("str", str):
                v = str(v)
            kwargs[k] = v
        return cls(**kwargs)

    @classmethod
    def load(cls, path: str) -> "Config":
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        if path.endswith(".json"):
            data = json.loads(text)
        else:
            data = _load_yaml(text)
        return cls.from_dict(data or {})

    def updated(self, **overrides) -> "Config":
        d = self.to_dict()
        d.update({k: v for k, v in overrides.items() if v is not None})
        return Config.from_dict(d)


def _load_yaml(text: str) -> dict:
    """YAML laden – mit PyYAML, sonst flacher 'schlüssel: wert'-Parser (reicht für die Config)."""
    try:
        import yaml  # type: ignore
        return yaml.safe_load(text) or {}
    except ImportError:
        pass
    data = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            raise ConfigError(f"Zeile nicht verstanden: {raw!r}")
        key, val = (s.strip() for s in line.split(":", 1))
        if val[:1] in ("'", '"'):                       # in Anführungszeichen: '#' gehört zum Wert
            end = val.find(val[0], 1)
            data[key] = val[1:end] if end > 0 else val[1:]
            continue
        val = re.split(r"\s#", val, 1)[0].strip()      # Kommentar nach Leerzeichen
        try:
            data[key] = json.loads(val)
        except json.JSONDecodeError:
            data[key] = val
    return data


# ---------------------------------------------------------------------------
# Geometrie-Grundlagen
# ---------------------------------------------------------------------------

def dist(a: Point, b: Point) -> float:
    return math.hypot(b[0] - a[0], b[1] - a[1])


def cross(o: Point, a: Point, b: Point) -> float:
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def signed_area(pts: Sequence[Point]) -> float:
    a = 0.0
    n = len(pts)
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        a += x1 * y2 - x2 * y1
    return a / 2.0


def is_ccw(pts: Sequence[Point]) -> bool:
    return signed_area(pts) > 0


def oriented(pts: Sequence[Point], ccw: bool = True) -> List[Point]:
    pts = list(pts)
    return pts if is_ccw(pts) == ccw else pts[::-1]


def perimeter(pts: Sequence[Point], closed: bool = True) -> float:
    n = len(pts)
    tot = sum(dist(pts[i], pts[i + 1]) for i in range(n - 1))
    if closed and n > 1:
        tot += dist(pts[-1], pts[0])
    return tot


def bbox(pts: Sequence[Point]) -> Tuple[float, float, float, float]:
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def translate(pts: Sequence[Point], dx: float, dy: float) -> List[Point]:
    return [(x + dx, y + dy) for x, y in pts]


def rotate(pts: Sequence[Point], ang: float, origin: Point = (0.0, 0.0)) -> List[Point]:
    c, s = math.cos(ang), math.sin(ang)
    ox, oy = origin
    return [(ox + (x - ox) * c - (y - oy) * s, oy + (x - ox) * s + (y - oy) * c) for x, y in pts]


def mirror_x(pts: Sequence[Point], axis_x: float = 0.0) -> List[Point]:
    """Spiegelt an der senkrechten Achse x = axis_x (Reihenfolge wird umgedreht, Orientierung bleibt)."""
    return [(2 * axis_x - x, y) for x, y in reversed(pts)]


def clean(pts: Sequence[Point], closed: bool = True, eps: float = 1e-9) -> List[Point]:
    """Entfernt aufeinanderfolgende Doppelpunkte und kollineare Zwischenpunkte (gerade Weiterführung).
    Rückläufige 'Spitzen' bleiben bewusst erhalten – die meldet der Validator."""
    out: List[Point] = []
    for p in pts:
        if not out or dist(out[-1], p) > eps:
            out.append((float(p[0]), float(p[1])))
    if closed and len(out) > 1 and dist(out[0], out[-1]) <= eps:
        out.pop()
    changed = True
    while changed and len(out) > 3:
        changed = False
        n = len(out)
        rng = range(n) if closed else range(1, n - 1)
        for i in rng:
            a, b, c = out[i - 1], out[i], out[(i + 1) % n]
            ab, bc = dist(a, b), dist(b, c)
            if ab < eps or bc < eps:
                continue
            if abs(cross(a, b, c)) <= eps * max(ab, bc) and \
                    ((b[0] - a[0]) * (c[0] - b[0]) + (b[1] - a[1]) * (c[1] - b[1])) > 0:
                del out[i]
                changed = True
                break
    return out


def arc_points(cx: float, cy: float, r: float, a0: float, a1: float,
               tol: float = 0.05) -> List[Point]:
    """Kreisbogen von Winkel a0 nach a1 (rad, Richtung durch Vorzeichen), inklusive Endpunkte."""
    sweep = a1 - a0
    if r <= 0:
        return [(cx, cy)]
    step = 2 * math.acos(max(-1.0, min(1.0, 1 - tol / r))) if tol < r else math.pi / 4
    step = max(min(step, math.pi / 8), 1e-3)
    n = max(2, int(math.ceil(abs(sweep) / step)))
    return [(cx + r * math.cos(a0 + sweep * i / n), cy + r * math.sin(a0 + sweep * i / n))
            for i in range(n + 1)]


def circle(cx: float, cy: float, r: float, tol: float = 0.05, ccw: bool = True) -> List[Point]:
    pts = arc_points(cx, cy, r, 0.0, 2 * math.pi, tol)[:-1]
    return pts if ccw else pts[::-1]


def ellipse(cx: float, cy: float, rx: float, ry: float, n: int = 72, ccw: bool = True) -> List[Point]:
    pts = [(cx + rx * math.cos(2 * math.pi * i / n), cy + ry * math.sin(2 * math.pi * i / n))
           for i in range(n)]
    return pts if ccw else pts[::-1]


def rect(x: float, y: float, w: float, h: float, ccw: bool = True) -> List[Point]:
    pts = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
    return pts if ccw else pts[::-1]


def bezier_q(p0: Point, p1: Point, p2: Point, n: int = 24) -> List[Point]:
    """Quadratische Bezierkurve, n Segmente, inklusive Endpunkte."""
    out = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        out.append((u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0],
                    u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1]))
    return out


def arched(cx: float, y0: float, w: float, h: float, tol: float = 0.05, ccw: bool = True) -> List[Point]:
    """Rundbogen-Öffnung (Tür/Fenster): Rechteck mit Halbkreis oben. Gesamthöhe h."""
    r = w / 2.0
    hs = max(h - r, 0.0)
    pts = [(cx - r, y0), (cx + r, y0)]
    pts += arc_points(cx, y0 + hs, r, 0.0, math.pi, tol)
    pts = clean(pts)
    return pts if ccw else pts[::-1]


# --- Schnitt- und Abstandstests -------------------------------------------

def point_seg_dist(p: Point, a: Point, b: Point) -> float:
    ax, ay = a
    dx, dy = b[0] - ax, b[1] - ay
    L2 = dx * dx + dy * dy
    if L2 <= 1e-18:
        return dist(p, a)
    t = max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / L2))
    return math.hypot(p[0] - (ax + t * dx), p[1] - (ay + t * dy))


def segments_cross(a: Point, b: Point, c: Point, d: Point) -> bool:
    """Echte Kreuzung zweier Strecken (innere Punkte, nicht kollinear)."""
    d1, d2 = cross(c, d, a), cross(c, d, b)
    d3, d4 = cross(a, b, c), cross(a, b, d)
    return ((d1 > EPS and d2 < -EPS) or (d1 < -EPS and d2 > EPS)) and \
        ((d3 > EPS and d4 < -EPS) or (d3 < -EPS and d4 > EPS))


def seg_seg_dist(a: Point, b: Point, c: Point, d: Point) -> float:
    if segments_cross(a, b, c, d):
        return 0.0
    return min(point_seg_dist(a, c, d), point_seg_dist(b, c, d),
               point_seg_dist(c, a, b), point_seg_dist(d, a, b))


def point_in_polygon(p: Point, poly: Sequence[Point]) -> bool:
    x, y = p
    inside = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y):
            xint = xi + (y - yi) * (xj - xi) / (yj - yi)
            if x < xint:
                inside = not inside
        j = i
    return inside


def dist_to_boundary(p: Point, poly: Sequence[Point], closed: bool = True) -> float:
    n = len(poly)
    m = n if closed else n - 1
    return min(point_seg_dist(p, poly[i], poly[(i + 1) % n]) for i in range(m))


def edges(pts: Sequence[Point], closed: bool = True) -> List[Tuple[Point, Point]]:
    n = len(pts)
    m = n if closed else n - 1
    return [(pts[i], pts[(i + 1) % n]) for i in range(m)]


def min_distance(p1: Sequence[Point], p2: Sequence[Point], limit: float = math.inf,
                 closed1: bool = True, closed2: bool = True) -> float:
    """Kleinster Abstand zweier Polylinien; Segmentpaare weiter als 'limit' werden übersprungen."""
    e2 = [(a, b, min(a[0], b[0]) - limit, max(a[0], b[0]) + limit,
           min(a[1], b[1]) - limit, max(a[1], b[1]) + limit) for a, b in edges(p2, closed2)]
    best = math.inf
    for a, b in edges(p1, closed1):
        x0, x1 = min(a[0], b[0]), max(a[0], b[0])
        y0, y1 = min(a[1], b[1]), max(a[1], b[1])
        for c, d, ex0, ex1, ey0, ey1 in e2:
            if x1 < ex0 or x0 > ex1 or y1 < ey0 or y0 > ey1:
                continue
            dd = seg_seg_dist(a, b, c, d)
            if dd < best:
                best = dd
                if best == 0.0:
                    return 0.0
    return best


def clip_segment(p0: Point, p1: Point, poly: Sequence[Point],
                 avoid: Sequence[Sequence[Point]] = ()) -> List[Tuple[Point, Point]]:
    """Teilstücke der Strecke p0→p1, die innerhalb von poly und außerhalb aller 'avoid'-Polygone
    liegen (für Schraffuren/Muster-Gravuren)."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    ts = [0.0, 1.0]
    for pg in [poly] + list(avoid):
        n = len(pg)
        for i in range(n):
            a, b = pg[i], pg[(i + 1) % n]
            ex, ey = b[0] - a[0], b[1] - a[1]
            den = dx * ey - dy * ex
            if abs(den) < 1e-12:
                continue
            t = ((a[0] - p0[0]) * ey - (a[1] - p0[1]) * ex) / den
            u = ((a[0] - p0[0]) * dy - (a[1] - p0[1]) * dx) / den
            if 0.0 < t < 1.0 and -1e-12 <= u <= 1.0 + 1e-12:
                ts.append(t)
    ts.sort()
    out = []
    for t0, t1 in zip(ts, ts[1:]):
        if t1 - t0 < 1e-9:
            continue
        tm = (t0 + t1) / 2
        m = (p0[0] + dx * tm, p0[1] + dy * tm)
        if point_in_polygon(m, poly) and not any(point_in_polygon(m, av) for av in avoid):
            out.append(((p0[0] + dx * t0, p0[1] + dy * t0), (p0[0] + dx * t1, p0[1] + dy * t1)))
    return out


def _seg_intersection(a: Point, b: Point, c: Point, d: Point) -> Optional[Point]:
    den = (b[0] - a[0]) * (d[1] - c[1]) - (b[1] - a[1]) * (d[0] - c[0])
    if abs(den) < 1e-15:
        return None
    t = ((c[0] - a[0]) * (d[1] - c[1]) - (c[1] - a[1]) * (d[0] - c[0])) / den
    return (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]))


def remove_loops(pts: Sequence[Point], max_iter: int = 500) -> List[Point]:
    """Entfernt lokale Schleifen, die beim Nach-innen-Versetzen an engen Rundungen und
    spitzen Ecken entstehen (die kürzere Schleife wird durch den Schnittpunkt ersetzt)."""
    pts = list(pts)
    for _ in range(max_iter):
        n = len(pts)
        if n < 4:
            return pts
        found = False
        for i in range(n):
            a, b = pts[i], pts[(i + 1) % n]
            for k in range(2, n // 2 + 1):
                j = (i + k) % n
                c, d = pts[j], pts[(j + 1) % n]
                if segments_cross(a, b, c, d):
                    p = _seg_intersection(a, b, c, d)
                    if p is None:
                        continue
                    # Schleife = Punkte i+1 … j  →  durch p ersetzen. Entfernt wird die Schleife mit
                    # der kleineren Fläche (nicht die mit weniger Knoten: eine Öse aus vielen
                    # Bogenpunkten darf nicht den ganzen Stern verdrängen).
                    loop_a = [p] + [pts[(i + 1 + m) % n] for m in range(k)]
                    loop_b = [p] + [pts[(j + 1 + m) % n] for m in range(n - k)]
                    if abs(signed_area(loop_a)) <= abs(signed_area(loop_b)):
                        idx = {(i + 1 + m) % n for m in range(k)}
                        keep = [pts[m] for m in range(n) if m not in idx]
                        ins = keep.index(pts[i]) + 1 if pts[i] in keep else 0
                        keep.insert(ins, p)
                    else:
                        keep = loop_a[:]                   # p, i+1 … j
                    pts = keep
                    found = True
                    break
            if found:
                break
        if not found:
            return clean(pts)
    return clean(pts)


def inset_polygon(pts: Sequence[Point], d: float) -> List[Point]:
    """Kontur um d nach innen versetzen (Gravurrand, Musterbereich). Erwartet CCW-Außenkontur.
    Schleifen an engen Rundungen werden entfernt; zu kleine Reste ergeben eine leere Liste."""
    out = remove_loops(offset_polygon(oriented(pts, True), -d, miter_limit=4.0))
    return out if len(out) >= 3 and signed_area(out) > 0 else []


def polygon_ok(pts: Sequence[Point]) -> bool:
    """Schneller Plausibilitätstest: mind. 3 Punkte, Fläche > 0, keine Selbstüberschneidung."""
    if len(pts) < 3 or signed_area(pts) <= 1e-9:
        return False
    es = edges(pts, True)
    m = len(es)
    for i in range(m):
        for j in range(i + 2, m):
            if i == 0 and j == m - 1:
                continue
            if segments_cross(es[i][0], es[i][1], es[j][0], es[j][1]):
                return False
    return True


# ---------------------------------------------------------------------------
# Kerf-Kompensation
# ---------------------------------------------------------------------------

def offset_polygon(pts: Sequence[Point], d: float, miter_limit: float = 2.5) -> List[Point]:
    """Versetzt ein geschlossenes Polygon um d entlang der rechten Kantennormale.

    Bei CCW-Außenkonturen wächst das Teil (d > 0), bei CW-Löchern schrumpft das Loch.
    Sich öffnende Ecken (konvex in Versatzrichtung) bekommen eine Gehrung; ist sie länger
    als miter_limit * d, wird stattdessen eine Fase (zwei Punkte) gesetzt.
    Sich schließende Ecken bekommen den exakten Schnittpunkt der versetzten Kanten.
    """
    pts = clean(pts)
    n = len(pts)
    if abs(d) < 1e-12 or n < 3:
        return list(pts)
    out: List[Point] = []
    for i in range(n):
        p0, p, p1 = pts[i - 1], pts[i], pts[(i + 1) % n]
        l1, l2 = dist(p0, p), dist(p, p1)
        n1 = ((p[1] - p0[1]) / l1, -(p[0] - p0[0]) / l1)
        n2 = ((p1[1] - p[1]) / l2, -(p1[0] - p[0]) / l2)
        k = 1.0 + n1[0] * n2[0] + n1[1] * n2[1]      # = 1 + cos(Knickwinkel)
        turn = cross(p0, p, p1)
        opening = turn * d > 0
        if k < 1e-9:                                   # 180°-Umkehr (Spitze)
            out += [(p[0] + n1[0] * d, p[1] + n1[1] * d), (p[0] + n2[0] * d, p[1] + n2[1] * d)]
            continue
        miter_len = abs(d) * math.sqrt(2.0 / k)
        if opening and miter_len > miter_limit * abs(d):
            out += [(p[0] + n1[0] * d, p[1] + n1[1] * d), (p[0] + n2[0] * d, p[1] + n2[1] * d)]
        else:
            out.append((p[0] + (n1[0] + n2[0]) * d / k, p[1] + (n1[1] + n2[1]) * d / k))
    return _merge_close(clean(out), 0.03)


def _merge_close(pts: List[Point], eps: float) -> List[Point]:
    """Fasst Versatzpunkte zusammen, die näher als eps liegen. Solche Mini-Segmente entstehen,
    wenn eine sehr kurze Kante direkt an einer spitzen Innenecke liegt."""
    changed = True
    while changed and len(pts) > 3:
        changed = False
        for i in range(len(pts)):
            a, b = pts[i], pts[(i + 1) % len(pts)]
            if dist(a, b) < eps:
                m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
                j = (i + 1) % len(pts)
                pts = [m if k == i else q for k, q in enumerate(pts) if k != j]
                changed = True
                break
    return pts


# ---------------------------------------------------------------------------
# Bauteile, Steckverbindungen, Baugruppen
# ---------------------------------------------------------------------------

@dataclass
class Stroke:
    """Gravurlinie (offen oder geschlossen)."""
    points: List[Point]
    closed: bool = False


@dataclass
class JointFeature:
    """Eine Hälfte einer Steckverbindung, beschrieben in Bauteil-Koordinaten.

    kind     finger  – Zinkenkante. segments = [(breite, belegt_eckzone)] in Laufrichtung
             tab     – herausstehende Nase (length = Breite, depth = Höhe)
             slot    – rechteckiges Loch für einen Tab (length = Länge, depth = Breite)
             halving – Kreuzschlitz von der Kante (length = Schlitztiefe, depth = Schlitzbreite)
             shaft   – Abschnitt einer Vierkantachse (length × depth = Querschnitt T × T)
             bore_square – Vierkantloch für den Pressitz einer Achse (length = depth = Kante)
             bore_round  – rundes Lager, in dem eine Vierkantachse dreht (length = Durchmesser)
    pos      gemeinsame Bezugsposition (z. B. 3D-Koordinate der Tab-Mitte) für tab/slot,
             Achsposition für shaft/bore_*
    span     halving: (von, bis) entlang der gemeinsamen Höhenachse; shaft: Abschnitt auf der Achse
    points   nominale Geometriepunkte: müssen auf der Kontur liegen (finger/tab/halving/shaft)
             bzw. die Ecken eines Lochs sein (slot, bore_*). So prüft der Validator die echte Geometrie.
    """
    id: str
    kind: str
    length: float
    depth: float
    segments: List[Tuple[float, bool]] = field(default_factory=list)
    pos: Optional[float] = None
    span: Optional[Tuple[float, float]] = None
    points: List[Point] = field(default_factory=list)


@dataclass
class Part:
    name: str
    outline: List[Point]
    holes: List[List[Point]] = field(default_factory=list)
    engrave: List[Stroke] = field(default_factory=list)
    features: List[JointFeature] = field(default_factory=list)
    note: str = ""

    def __post_init__(self):
        # Orientierung erzwingen (CCW außen, CW Löcher). Bewusst KEIN Bereinigen –
        # fehlerhafte Eingaben sollen im Validator auffallen.
        if len(self.outline) >= 3 and abs(signed_area(self.outline)) > 1e-12:
            self.outline = oriented(self.outline, True)
        self.holes = [oriented(h, False) if len(h) >= 3 and abs(signed_area(h)) > 1e-12 else list(h)
                      for h in self.holes]

    def add_hole(self, pts: Sequence[Point]) -> None:
        self.holes.append(oriented(clean(pts), False))

    def add_engrave(self, pts: Sequence[Point], closed: bool = False) -> None:
        pts = clean(pts, closed=closed)
        if len(pts) >= 2:
            self.engrave.append(Stroke(pts, closed))

    def feature(self, fid: str) -> JointFeature:
        for f in self.features:
            if f.id == fid:
                return f
        raise KeyError(f"{self.name}: Feature {fid!r} fehlt")

    def bbox(self) -> Tuple[float, float, float, float]:
        return bbox(self.outline)

    def size(self) -> Tuple[float, float]:
        x0, y0, x1, y1 = self.bbox()
        return x1 - x0, y1 - y0

    def cut_paths(self) -> List[List[Point]]:
        """Reihenfolge für den Laser: erst Innenschnitte, dann Außenkontur."""
        return list(self.holes) + [self.outline]

    def compensated(self, d: float) -> "Part":
        """Kopie mit Kerf-Kompensation: Außenkontur +d, Löcher -d (rechte Normale)."""
        return Part(self.name, offset_polygon(self.outline, d),
                    [offset_polygon(h, d) for h in self.holes],
                    [Stroke(list(s.points), s.closed) for s in self.engrave],
                    self.features, self.note)

    def transformed(self, fn: Callable[[Sequence[Point]], List[Point]]) -> "Part":
        p = Part(self.name, fn(self.outline), [fn(h) for h in self.holes],
                 [Stroke(fn(s.points), s.closed) for s in self.engrave], self.features, self.note)
        return p


@dataclass
class Connection:
    a: str              # "teil:feature"
    b: str
    flip: bool = False  # Segmentreihenfolge von b umkehren (Kanten laufen gegenläufig)


@dataclass
class Assembly:
    name: str
    parts: List[Part] = field(default_factory=list)
    connections: List[Connection] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    params: Dict = field(default_factory=dict)

    def part(self, name: str) -> Part:
        for p in self.parts:
            if p.name == name:
                return p
        raise KeyError(name)

    def connect(self, a: str, b: str, flip: bool = False) -> None:
        self.connections.append(Connection(a, b, flip))

    def merge(self, other: "Assembly") -> None:
        names = {p.name for p in self.parts}
        clash = names & {p.name for p in other.parts}
        if clash:
            raise ValueError(f"Doppelte Teilnamen: {sorted(clash)}")
        self.parts += other.parts
        self.connections += other.connections
        self.notes += other.notes


# ---------------------------------------------------------------------------
# Kantenprofile: Zinken und Tabs
# ---------------------------------------------------------------------------

def edge_frame(p: Point, q: Point) -> Tuple[float, Callable[[float, float], Point]]:
    """Lokales Kantensystem: t entlang p→q, h entlang der rechten (äußeren) Normale."""
    L = dist(p, q)
    ux, uy = (q[0] - p[0]) / L, (q[1] - p[1]) / L
    nx, ny = uy, -ux

    def at(t: float, h: float) -> Point:
        return (p[0] + ux * t + nx * h, p[1] + uy * t + ny * h)
    return L, at


def profile_edge(p: Point, q: Point, segments: Sequence[Tuple[float, float]]) -> List[Point]:
    """Punkte einer profilierten Kante von p (inkl.) bis vor q.

    segments = [(länge, tiefe)]; tiefe > 0 steht nach außen vor (Tab/Zinken),
    tiefe < 0 ist eine Kerbe nach innen, 0 = glatte Kante. Summe der Längen = |pq|.
    """
    L, at = edge_frame(p, q)
    total = sum(s for s, _ in segments)
    if abs(total - L) > 1e-6:
        raise ValueError(f"Profil-Längen {total:.4f} ≠ Kantenlänge {L:.4f}")
    pts = [p]
    t = 0.0
    for length, depth in segments:
        pts.append(at(t, depth))
        pts.append(at(t + length, depth))
        t += length
    pts.append(q)
    out = clean(pts, closed=False)
    if out and dist(out[-1], q) < 1e-9:
        out.pop()
    return out


def finger_count(length: float, cfg: Config) -> int:
    """Ungerade Zinkenzahl (≥ 3), so dass beide Enden glatt sind (Ecken gehören der Notch-Seite)."""
    n = int(length // (cfg.finger_factor * cfg.T))
    n = max(3, n)
    if n % 2 == 0:
        n -= 1
    while n > 3 and length / n < cfg.min_tab_width:
        n -= 2
    return n


def finger_segments(length: float, n: int, depth: float, phase: str) -> List[Tuple[float, float]]:
    """phase 'notch': ungerade Segmente sind Kerben (−depth), Material besetzt die Ecke bei geraden.
       phase 'tab'  : ungerade Segmente stehen um +depth vor."""
    w = length / n
    sign = -1.0 if phase == "notch" else 1.0
    return [(w, 0.0 if i % 2 == 0 else sign * depth) for i in range(n)]


def finger_feature(fid: str, p: Point, q: Point, segs: Sequence[Tuple[float, float]],
                   phase: str, T: float) -> JointFeature:
    occupied = [(w, (d == 0.0) if phase == "notch" else (d > 0)) for w, d in segs]
    return JointFeature(fid, "finger", dist(p, q), T, occupied, points=profile_edge(p, q, segs))


def tab_centers(length: float, cfg: Config, count: Optional[int] = None,
                inset: float = 0.0) -> Tuple[List[float], float]:
    """Symmetrisch verteilte Tab-Mitten entlang einer Kante und die Tabbreite."""
    usable = length - 2 * inset
    if count is None:
        count = 1 if usable < 50 else (2 if usable < 130 else 3)
    width = min(cfg.tab_factor * cfg.T, usable / (2 * count))
    width = max(width, cfg.min_tab_width)
    centers = [inset + usable * (i + 1) / (count + 1) for i in range(count)]
    return centers, width


def tab_segments(length: float, centers: Sequence[float], width: float,
                 height: float) -> List[Tuple[float, float]]:
    segs: List[Tuple[float, float]] = []
    t = 0.0
    for c in sorted(centers):
        a, b = c - width / 2, c + width / 2
        if a < t - 1e-9 or b > length + 1e-9:
            raise ValueError("Tabs überlappen oder ragen über die Kante")
        if a - t > 1e-9:
            segs.append((a - t, 0.0))
        segs.append((width, height))
        t = b
    if length - t > 1e-9:
        segs.append((length - t, 0.0))
    return segs


def tab_features(prefix: str, p: Point, q: Point, centers: Sequence[float], width: float,
                 height: float, pos_fn: Callable[[float], float]) -> List[JointFeature]:
    _, at = edge_frame(p, q)
    out = []
    for i, c in enumerate(centers):
        a, b = c - width / 2, c + width / 2
        pts = [at(a, 0), at(a, height), at(b, height), at(b, 0)]
        out.append(JointFeature(f"{prefix}{i}", "tab", width, height, pos=pos_fn(c), points=pts))
    return out


def slot_feature(fid: str, x: float, y: float, w: float, h: float, length_along_x: bool,
                 pos: float) -> Tuple[JointFeature, List[Point]]:
    """Rechteckschlitz. Liefert (Feature, Lochpolygon CW)."""
    hole = rect(x, y, w, h, ccw=False)
    length, width = (w, h) if length_along_x else (h, w)
    return JointFeature(fid, "slot", length, width, pos=pos, points=list(hole)), hole


# ---------------------------------------------------------------------------
# Layout auf Blättern
# ---------------------------------------------------------------------------

class LayoutError(RuntimeError):
    pass


@dataclass
class Sheet:
    index: int
    width: float
    height: float
    parts: List[Part] = field(default_factory=list)   # in SVG-Koordinaten (y nach unten)


def _to_sheet(part: Part, x: float, y: float, rot: bool) -> Part:
    """Bauteil (y oben) ins Blatt (y unten) übertragen; optional 90° gedreht."""
    src = part.transformed(lambda pts: rotate(pts, math.pi / 2)) if rot else part
    x0, y0, x1, y1 = src.bbox()

    def fn(pts):
        return [(px - x0 + x, (y1 - py) + y) for px, py in pts]
    return src.transformed(fn)


def layout(parts: Sequence[Part], cfg: Config) -> List[Sheet]:
    """Einfaches Regal-Packing (größte Höhe zuerst), bei Bedarf über mehrere Blätter.
    Teile werden um 90° gedreht, wenn sie sonst nicht auf ein Blatt passen."""
    uw = cfg.sheet_width - 2 * cfg.sheet_margin
    uh = cfg.sheet_height - 2 * cfg.sheet_margin
    gap = cfg.part_spacing
    items = []
    for p in parts:
        w, h = p.size()
        rot = False
        if w > uw + EPS or h > uh + EPS:
            if h <= uw + EPS and w <= uh + EPS:
                rot = True
                w, h = h, w
            else:
                raise LayoutError(f"Teil {p.name} ({w:.1f} × {h:.1f} mm) passt auf kein Blatt "
                                  f"({cfg.sheet_width:.0f} × {cfg.sheet_height:.0f} mm).")
        items.append((p, w, h, rot))
    items.sort(key=lambda it: (-it[2], -it[1]))

    sheets: List[Sheet] = []
    shelves: List[List[float]] = []  # je Blatt: [cursor_x, shelf_y, shelf_h]

    def new_sheet():
        sheets.append(Sheet(len(sheets) + 1, cfg.sheet_width, cfg.sheet_height))
        shelves.append([0.0, 0.0, 0.0])

    new_sheet()
    for p, w, h, rot in items:
        placed = False
        for si, st in enumerate(shelves):
            cx, sy, sh = st
            if cx + w <= uw + EPS and sy + h <= uh + EPS and (h <= sh + EPS or cx == 0.0):
                pass
            elif sy + sh + gap + h <= uh + EPS and w <= uw + EPS:
                sy, cx, sh = sy + sh + gap, 0.0, 0.0
            else:
                continue
            sheets[si].parts.append(_to_sheet(p, cfg.sheet_margin + cx, cfg.sheet_margin + sy, rot))
            shelves[si] = [cx + w + gap, sy, max(sh, h)]
            placed = True
            break
        if not placed:
            new_sheet()
            sheets[-1].parts.append(_to_sheet(p, cfg.sheet_margin, cfg.sheet_margin, rot))
            shelves[-1] = [w + gap, 0.0, h]
    return sheets


# ---------------------------------------------------------------------------
# SVG-Export (LightBurn / xTool Creative Space / Glowforge)
# ---------------------------------------------------------------------------

def _fmt(v: float) -> str:
    s = f"{v:.3f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def path_d(pts: Sequence[Point], closed: bool) -> str:
    d = "M" + " L".join(f"{_fmt(x)},{_fmt(y)}" for x, y in pts)
    return d + (" Z" if closed else "")


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def sheet_to_svg(sheet: Sheet, cfg: Config, title: str, meta: Optional[dict] = None) -> str:
    """Ein Blatt als SVG. Echte mm-Maße (width/height in mm, viewBox in mm) – LightBurn
    importiert damit maßstabsgetreu. Gravur-Layer zuerst, dann Schnitt (innen vor außen)."""
    W, H = sheet.width, sheet.height
    sw = _fmt(cfg.stroke_width)
    desc = {"generator": f"Steckwerk {__version__}", "thickness_mm": cfg.thickness,
            "kerf_mm": cfg.kerf, "kerf_compensated": True, "scale": cfg.scale,
            "layer_cut": cfg.cut_color, "layer_engrave": cfg.engrave_color}
    if meta:
        desc.update(meta)
    out = ['<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
           f'<svg xmlns="http://www.w3.org/2000/svg" '
           f'xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" version="1.1" '
           f'width="{_fmt(W)}mm" height="{_fmt(H)}mm" viewBox="0 0 {_fmt(W)} {_fmt(H)}">',
           f"  <title>{_esc(title)}</title>",
           f"  <desc>{_esc(json.dumps(desc, ensure_ascii=False))}</desc>",
           "  <!-- Layer 'Gravur': stroke " + cfg.engrave_color + " – in LightBurn als Line (Ritzen) "
           "oder Fill einstellen, niedrige Leistung. -->",
           f'  <g id="layer-gravur" inkscape:groupmode="layer" inkscape:label="Gravur" '
           f'stroke="{cfg.engrave_color}" fill="none" stroke-width="{sw}">']
    for p in sheet.parts:
        if p.engrave:
            out.append(f'    <g id="gravur-{_esc(p.name)}">')
            for s in p.engrave:
                out.append(f'      <path d="{path_d(s.points, s.closed)}" stroke="{cfg.engrave_color}" '
                           f'fill="none" stroke-width="{sw}"/>')
            out.append("    </g>")
    out.append("  </g>")
    out.append("  <!-- Layer 'Schnitt': stroke " + cfg.cut_color + " – in LightBurn als Line (Cut), "
               "Innenschnitte stehen vor der Außenkontur. -->")
    out.append(f'  <g id="layer-schnitt" inkscape:groupmode="layer" inkscape:label="Schnitt" '
               f'stroke="{cfg.cut_color}" fill="none" stroke-width="{sw}">')
    for p in sheet.parts:
        out.append(f'    <g id="schnitt-{_esc(p.name)}">')
        for poly in p.cut_paths():
            out.append(f'      <path d="{path_d(poly, True)}" stroke="{cfg.cut_color}" '
                       f'fill="none" stroke-width="{sw}"/>')
        out.append("    </g>")
    out.append("  </g>")
    out.append("</svg>")
    return "\n".join(out) + "\n"


def write_text(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(text)
    os.replace(tmp, path)
