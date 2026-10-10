"""Gemeinsame Test-Helfer: Projektordner in den Importpfad, Validierungs-Assert."""
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from steckwerk import Config, layout  # noqa: E402
from validator import validate_assembly, validate_sheets  # noqa: E402


def check(asm, cfg):
    """Validiert Baugruppe + Blattlayout und gibt den Report zurück."""
    rep = validate_assembly(asm, cfg)
    sheets = layout([p.compensated(cfg.kerf_offset) for p in asm.parts], cfg)
    validate_sheets(sheets, cfg, rep)
    return rep


def assert_cut_ready(asm, cfg):
    rep = check(asm, cfg)
    assert rep.passed, "\n" + "\n".join(e.line() for e in rep.errors)
    return rep


@pytest.fixture
def cfg():
    return Config()


# Materialstärken/Kerfs, mit denen jedes Modell funktionieren muss
MATERIALS = [(3.0, 0.2), (2.0, 0.1), (4.0, 0.15), (6.0, 0.3), (3.0, 0.0)]
