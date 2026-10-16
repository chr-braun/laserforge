"""
Gemeinsamer Wichtel-Maßstab (ab Verzierungen 1.2.0).

Alle Modelle aus dem Paket „Wichtel“ können ihre Maße aus einer einzigen Angabe
ableiten: der Höhe der Wichtelfigur. Dann passen Tür, Fenster, Bank, Tisch, Bett, Leiter, Wegweiser und
Wäscheleine zueinander und zur Wichtelfigur aus Steckwerk (Standard 70 mm).
"""
from __future__ import annotations

import math
from typing import Any, Dict, List

from pakete import num, sel

STANDARD = 70.0

# Maß je Modell als Vielfaches der Wichtelhöhe (bei 70 mm entstehen die bisherigen Standardmaße)
VERHAELTNIS: Dict[str, Dict[str, float]] = {
    "wichtelbank": dict(laenge=1.0, tiefe=0.37, sitzhoehe=0.34, lehnenhoehe=0.34),
    "wichteltisch": dict(breite=1.0, tiefe=0.66, hoehe=0.57, hockerhoehe=0.34),
    "wichtelbett": dict(laenge=1.15, breite=0.64, liegehoehe=0.26, kopfteil=0.7, fussteil=0.46),
    "wichteltuer": dict(hoehe=1.5, breite=0.86, rahmen_b=0.14),
    "wichtelfenster": dict(breite=0.62, hoehe=0.75, rahmen_b=0.09),
    "wichtelleiter": dict(hoehe=1.43, breite=0.4, abstand=0.21),
    "wegweiser": dict(hoehe=1.57, schild_h=0.16),
    "waescheleine": dict(laenge=1.7, hoehe=0.86, groesse=0.26),
}

# Kleinste sinnvolle Wichtelgröße: Faktor × Materialstärke (darunter werden Sitz, Liegefläche & Co. zu niedrig
# für die Steckverbindungen), mindestens BASIS.
MIN_FAKTOR: Dict[str, float] = dict(wichtelbank=13.5, wichteltisch=14.5, wichtelbett=12.5, wichtelleiter=9.0)
MIN_BASIS: Dict[str, float] = dict(wichtelbett=45.0)


def mindestgroesse(modell: str, T: float) -> float:
    m = max(40.0, MIN_BASIS.get(modell, 40.0), MIN_FAKTOR.get(modell, 0.0) * T)
    return float(math.ceil(m / 5.0 - 1e-9) * 5)


EN = {
    "Maßstab": "Scale", "passend zur Wichtelgröße": "matching the elf size", "eigene Maße": "custom sizes",
    "Wichtelgröße": "Elf size",
    "Höhe der Wichtelfigur – alles aus dem Wichtel-Paket passt dann zusammen":
        "height of the elf figure – everything from the elf package then fits together",
}


def massstab_params() -> List[Dict[str, Any]]:
    return [
        sel("massstab", "Maßstab", [("wichtel", "passend zur Wichtelgröße"), ("frei", "eigene Maße")], "wichtel"),
        num("wichtel", "Wichtelgröße", STANDARD, 40, 160,
            help="Höhe der Wichtelfigur – alles aus dem Wichtel-Paket passt dann zusammen",
            when={"massstab": ["wichtel"]}),
    ]


def mit_massstab(modell: str, params: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Maßstab-Auswahl vor die Parameter setzen; die Maße des Modells nur bei „eigene Maße“ zeigen."""
    keys = set(VERHAELTNIS[modell])
    out = massstab_params()
    for p in params:
        if p["key"] in keys:
            p = dict(p, when=dict(p.get("when") or {}, massstab=["frei"]))
        out.append(p)
    return out


def wichtelmass(modell: str, groesse: float, params: List[Dict[str, Any]], cfg=None) -> Dict[str, float]:
    """Maße für `modell` passend zu einer Wichtelfigur der Höhe `groesse`, in die Grenzen der Parameter
    eingepasst. Mit cfg wird geprüft, ob der Wichtel für diese Materialstärke groß genug ist."""
    if cfg is not None:
        m = mindestgroesse(modell, cfg.T / cfg.scale)
        if float(groesse) < m - 1e-9:
            raise ValueError(f"Bei {cfg.T:g} mm Holz muss der Wichtel dafür mindestens {m:g} mm groß sein – "
                             f"Wichtelgröße erhöhen oder dünneres Holz nehmen")
    grenzen = {p["key"]: (p.get("min"), p.get("max")) for p in params}
    out = {}
    for key, f in VERHAELTNIS[modell].items():
        v = round(f * float(groesse), 1)
        lo, hi = grenzen.get(key, (None, None))
        if lo is not None:
            v = max(v, lo)
        if hi is not None:
            v = min(v, hi)
        out[key] = v
    return out
