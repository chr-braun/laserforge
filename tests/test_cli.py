"""CLI: schreibt nur validierte Dateien, sonst gar nichts."""
import os

from cli import run


def _files(d):
    return sorted(os.path.relpath(os.path.join(r, f), d) for r, _, fs in os.walk(d) for f in fs)


def test_cli_writes_svg_and_report(tmp_path):
    assert run(["--model", "wichtelhaus", "--out", str(tmp_path), "-q"]) == 0
    files = _files(tmp_path)
    assert "wichtelhaus/wichtelhaus.svg" in files and "wichtelhaus/pruefbericht.txt" in files
    svg = (tmp_path / "wichtelhaus" / "wichtelhaus.svg").read_text()
    assert svg.startswith("<?xml") and "</svg>" in svg
    assert "CUT-READY" in (tmp_path / "wichtelhaus" / "pruefbericht.txt").read_text()


def test_cli_validate_only_writes_nothing(tmp_path):
    assert run(["--model", "zubehoer", "--validate", "--out", str(tmp_path), "-q"]) == 0
    assert _files(tmp_path) == []


def test_cli_error_writes_nothing(tmp_path):
    # Haus passt nicht aufs 60×60-Blatt → FEHLER, und auch das Zubehör wird nicht geschrieben
    assert run(["--model", "alle", "--sheet", "60x60", "--out", str(tmp_path), "-q"]) == 2
    assert _files(tmp_path) == []


def test_cli_bad_parameter(tmp_path):
    assert run(["--model", "wichtelhaus", "--kerf", "5", "--out", str(tmp_path)]) == 2


def test_cli_series_and_preview(tmp_path):
    assert run(["--model", "wichtelhaus", "--series", "3", "--seed", "1", "--preview",
                "--out", str(tmp_path), "-q"]) == 0
    files = _files(tmp_path)
    assert sum(f.endswith(".svg") for f in files) == 3
    import importlib.util
    has_png = any(importlib.util.find_spec(m) for m in ("matplotlib", "PIL"))
    assert sum(f.endswith(".png") for f in files) == (3 if has_png else 0)   # Vorschau ist optional


def test_cli_config_file(tmp_path):
    cfgf = tmp_path / "c.yaml"
    cfgf.write_text("thickness: 4\nkerf: 0.1\n")
    out = tmp_path / "o"
    assert run(["--config", str(cfgf), "--model", "tannenbaum", "--kerf", "0.25", "--out", str(out), "-q"]) == 0
    txt = (out / "tannenbaum" / "pruefbericht.txt").read_text()
    assert "'thickness': 4.0" in txt and "'kerf': 0.25" in txt


def test_cli_check_svg(tmp_path):
    assert run(["--model", "schneemann", "--out", str(tmp_path), "-q"]) == 0
    svg = tmp_path / "schneemann" / "schneemann.svg"
    assert run(["--check-svg", str(svg)]) == 0
    svg.write_text(svg.read_text().replace(" Z", ""))
    assert run(["--check-svg", str(svg)]) == 2


def test_cli_new_models(tmp_path):
    assert run(["--model", "ornament", "--shape", "herz", "--pattern", "punkte", "--text", "Anna,Ben|2026",
                "--out", str(tmp_path), "-q"]) == 0
    assert run(["--model", "schneeflocke", "--count", "3", "--3d", "--out", str(tmp_path), "-q"]) == 0
    assert run(["--model", "fahrzeug", "--vehicle", "lkw", "--axles", "3", "--text", "Express",
                "--out", str(tmp_path), "-q"]) == 0
    files = _files(tmp_path)
    assert {"ornament_herz/ornament_herz.svg", "schneeflocke/schneeflocke.svg", "lkw/lkw.svg"} <= set(files)


def test_cli_new_models_bad_values(tmp_path):
    assert run(["--model", "ornament", "--shape", "raute", "--out", str(tmp_path)]) == 2
    assert run(["--model", "fahrzeug", "--vehicle", "auto", "--length", "50", "--out", str(tmp_path)]) == 2
    assert _files(tmp_path) == []
