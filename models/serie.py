"""
serie.py – zusammengehörige Serie von Wichtelhäusern.

Aus demselben Generator (wichtelhaus.build) entstehen N Varianten mit unterschiedlicher
Architektur – Dachneigung, Proportionen, Fensterzahl, Tür, Kamin, Anbau – und, wenn gewünscht,
unterschiedlicher Gestaltung (Fensterform, Läden, Wand- und Dachgravur, Zierleiste, Giebel).
Jede Gestaltungsoption ist entweder fest (alle Häuser gleich) oder „zufall“ (je Haus anders).
Der Zufall ist über 'seed' reproduzierbar: gleicher Seed = identische Serie.

Schild-Namen mit Komma trennen: "Anna, Ben, Lea" → Haus 1 bekommt „Anna“, Haus 2 „Ben“ …
"""
from __future__ import annotations

import random
from typing import Dict, List, Optional

from laserforge import Assembly, Config
from models import wichtelhaus

RANDOM = "zufall"
# Auswahl je Haus bei „zufall“ (Mehrfachnennung = häufiger)
POOLS: Dict[str, List[str]] = {
    "fenster": ["rechteck", "rechteck", "rechteck", "bogen", "bogen", "rund", "spitzbogen", "herz", "raute"],
    "sprossen": ["kreuz", "kreuz", "kreuz", "senkrecht", "waagrecht"],
    "fenster_deko": ["rahmen", "rahmen", "laeden", "laeden", "herzlaeden", "blumen", "blumen", "beides", "schnee"],
    "tuer_deko": ["rahmen", "rahmen", "vordach", "vordach", "laternen", "girlande", "kranz"],
    "giebel": ["rundfenster", "rundfenster", "herz", "stern", "uhr", "luke"],
    "wand": ["keine", "keine", "holz", "holz", "ziegel", "ziegel", "stein", "fachwerk", "fachwerk", "schuppen"],
    "dach": ["ziegel", "ziegel", "biber", "biber", "schindel", "schindel", "reet", "schnee", "schnee"],
    "zierleiste": ["keine", "keine", "zuckerguss", "zuckerguss", "eiszapfen", "eiszapfen", "lichterkette",
                   "girlande", "wellen", "punkte"],
    "schild_form": ["rahmen", "rund", "banner", "holz", "geschweift", "oval"],
}
RANDOM_KEYS = list(POOLS)


def variants(n: int, seed: int, base_width: float, base_height: float, base_depth: float) -> List[dict]:
    rng = random.Random(seed)
    pitches = [35.0, 40.0, 45.0, 50.0, 55.0]
    rng.shuffle(pitches)
    fw_cycle = [2, 1, 2, 0, 1]                  # Fensterzahl vorne rotiert → sichtbare Vielfalt
    fw_off = rng.randrange(len(fw_cycle))
    out = []
    for i in range(n):
        v = dict(
            width=round(base_width * rng.uniform(0.85, 1.15), 1),
            depth=round(base_depth * rng.uniform(0.88, 1.12), 1),
            height=round(base_height * rng.uniform(0.85, 1.2), 1),
            pitch=pitches[i % len(pitches)],
            front_windows=fw_cycle[(i + fw_off) % len(fw_cycle)],
            side_windows=rng.choice([1, 1, 2]),
            door=rng.choice(["arched", "arched", "rect", "spitzbogen", "rund"]),
            chimney=rng.random() < 0.6,
            annex=rng.random() < 0.4,
            light=True,
        )
        if i == 0:                      # erste Variante = "Haupthaus" mit Kamin
            v.update(chimney=True, annex=False, front_windows=2)
        if n >= 3 and i == 1:           # mindestens eine Variante mit Anbau
            v["annex"] = True
        out.append(v)
    return out


def styles(n: int, seed: int, style: Dict[str, Optional[str]]) -> List[dict]:
    """Gestaltung je Haus: feste Werte übernehmen, „zufall“ je Haus auswürfeln."""
    rng = random.Random(seed * 31 + 5)
    names = [s.strip() for s in (style.get("schild") or "").split(",")]
    out = []
    for i in range(n):
        st = {}
        for k, v in style.items():
            if k == "schild":
                continue
            if k in POOLS and (v is None or v == RANDOM):
                st[k] = rng.choice(POOLS[k])
            elif v is not None:
                st[k] = v
        if i < len(names) and names[i]:
            st["schild"] = names[i]
        out.append(st)
    return out


def _build_house(cfg: Config, name: str, v: dict, st: dict) -> Assembly:
    """Baut ein Haus; passt ein Schild nicht, weicht erst der Giebel-/Türschmuck, dann der Rahmen."""
    tries = [st]
    if st.get("schild"):
        tries += [dict(st, giebel="keins", tuer_deko="rahmen"),
                  dict(st, giebel="keins", tuer_deko="rahmen", schild_form="ohne")]
    err: Optional[ValueError] = None
    for t in tries:
        try:
            return wichtelhaus.build(cfg, name=name, **v, **t)
        except ValueError as e:
            if "Schild" not in str(e):
                raise
            err = e
    raise ValueError(f"{name}: {err}")


def build(cfg: Config, n: int = 5, name: str = "serie", seed: Optional[int] = None,
          width: Optional[float] = None, height: Optional[float] = None,
          depth: Optional[float] = None, **style) -> List[Assembly]:
    if not (1 <= n <= 50):
        raise ValueError("Serie: n muss zwischen 1 und 50 liegen")
    unknown = set(style) - set(wichtelhaus.STYLE_KEYS)
    if unknown:
        raise TypeError(f"Unbekannte Option(en) {', '.join(sorted(unknown))}")
    seed = cfg.seed if seed is None else seed
    for k in RANDOM_KEYS:                       # ohne Angabe: je Haus auswürfeln
        style.setdefault(k, RANDOM)
    d = wichtelhaus.DEFAULTS
    vs = variants(n, seed, width or d["width"], height or d["height"], depth or d["depth"])
    sts = styles(n, seed, style)
    out = []
    for i, (v, st) in enumerate(zip(vs, sts), 1):
        asm = _build_house(cfg, f"{name}_haus{i:02d}", v, st)
        asm.params.update(series=name, variant=i, seed=seed)
        out.append(asm)
    return out
