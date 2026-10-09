"""
Modell-Registry von Laserforge.

Jedes Modell-Modul bietet build(cfg, **parameter) -> Assembly (Serie: Liste von Assemblies).
"""
from __future__ import annotations

from models import (briefkasten, fahrzeug, laterne, ornament, schneeflocke, schneemann, schwibbogen, serie,
                    tannenbaum, wichtel, wichtelhaus, zaun)

MODELS = {
    "wichtelhaus": wichtelhaus,
    "tannenbaum": tannenbaum,
    "schneemann": schneemann,
    "zaun": zaun,
    "laterne": laterne,
    "briefkasten": briefkasten,
    "wichtel": wichtel,
    "ornament": ornament,
    "schneeflocke": schneeflocke,
    "fahrzeug": fahrzeug,
    "schwibbogen": schwibbogen,
}

ACCESSORIES = ["tannenbaum", "schneemann", "zaun", "laterne", "briefkasten", "wichtel"]

__all__ = ["MODELS", "ACCESSORIES", "serie"] + list(MODELS)
