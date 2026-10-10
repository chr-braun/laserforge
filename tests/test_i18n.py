"""Sprachwahl: englische Texte für Formular, Prüfbericht, Meldungen und Pakete."""
import json
import re
import threading
import urllib.request

import pytest

import i18n
import service
import webui

GERMAN = re.compile(r"[äöüßÄÖÜ]|\b(und|oder|nicht|mit|der|die|das|Teile?|Platte|Prüfungen|FEHLER)\b")


def _texts(obj, out):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in ("label", "desc", "help", "section") and isinstance(v, str) and v:
                out.add(v)
            elif k not in ("motive", "pakete", "vehicle_defaults", "flaechen", "linien"):
                _texts(v, out)
    elif isinstance(obj, list):
        for v in obj:
            _texts(v, out)
    return out


def test_norm_and_german_unchanged():
    assert i18n.norm("en-US") == "en" and i18n.norm("fr") == "de" and i18n.norm(None) == "de"
    s = service.schema()
    assert i18n.translate_schema(s, "de") is s
    assert i18n.tr("Breite", "de") == "Breite"


def test_schema_fully_translated():
    s = service.schema()
    en = i18n.translate_schema(s, "en")
    missing = sorted(t for t in _texts(s, set()) if i18n.tr(t, "en") == t and GERMAN.search(t))
    assert not missing, missing[:20]
    assert set(en["group_labels"]) == set(s["groups"])                 # Gruppen-Schlüssel bleiben deutsch
    assert all(not GERMAN.search(v) for v in en["group_labels"].values())


def test_report_and_notes_translated():
    res = service.generate({"model": "wichtelhaus"})
    en = i18n.localize(res, "en")
    a = en["assemblies"][0]
    assert "checks OK" in a["summary"] and "Prüfungen" not in a["summary"]
    left = [l for l in a["report"].split("\n") if l.strip() and GERMAN.search(l)]
    assert not left, left[:5]
    assert i18n.localize(res, "de") is res


def test_unknown_sentence_kept():
    assert i18n.tr_line("Ganz neuer Satz 42", "en") == "Ganz neuer Satz 42"


def test_mac_dialog_language(monkeypatch):
    import steckwerk_app
    for code, want in (("en_US", "en"), ("de_DE", "de")):
        monkeypatch.setattr(steckwerk_app, "_LANG", None)
        monkeypatch.setenv("STECKWERK_SPRACHE", code)
        assert steckwerk_app.system_lang() == want
    assert steckwerk_app._t("Installieren", "Install") == "Installieren"


def test_package_translations():
    i18n.add("en", {"Gruselhaus": "Spooky house"})
    assert i18n.tr("Gruselhaus", "en") == "Spooky house" and i18n.tr("Gruselhaus", "de") == "Gruselhaus"


@pytest.fixture
def server(tmp_path):
    srv = webui.make_server("127.0.0.1", 0, str(tmp_path / "out"), quiet=True)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()
    srv.server_close()


def test_webui_language(server):
    de = json.load(urllib.request.urlopen(server + "/api/schema", timeout=10))
    en = json.load(urllib.request.urlopen(server + "/api/schema?lang=en", timeout=10))
    assert de["lang"] == "de" and en["lang"] == "en"
    assert {"value": "en", "label": "English"} in en["sprachen"]
    assert en["groups"] == de["groups"] and en["group_labels"] != {g: g for g in de["groups"]}
    req = urllib.request.Request(server + "/api/generate", json.dumps({"model": "wichtelhaus", "lang": "en"}).encode(),
                                 {"Content-Type": "application/json", "X-Steckwerk": "1"})
    res = json.load(urllib.request.urlopen(req, timeout=60))
    assert "checks OK" in res["assemblies"][0]["summary"]


@pytest.mark.parametrize("de,en", [
    ("Breite: 20 liegt außerhalb 80–320 mm", "Width: 20 is outside 80–320 mm"),
    ("Sockel-Text: Zeichen 'ä' gibt es in der Gravurschrift nicht",
     "Base text: Character 'ä' is not available in the engraving font"),
    ("Schwibbogen: Breite muss zwischen 120 und 600 mm liegen", "Candle arch: width must be between 120 and 600 mm"),
])
def test_input_errors(de, en):
    assert i18n.tr_line(de, "en") == en


def test_own_translation_wins():
    obj = {"hinweise": ["Neu"], "hinweise_en": ["New"], "beschreibung": "Gruselig", "beschreibung_en": ""}
    out = i18n.localize(obj, "en")
    assert out["hinweise"] == ["New"] and out["beschreibung"] == "Gruselig"


def test_package_brings_english(tmp_path, monkeypatch):
    import os
    import pakete
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    monkeypatch.setenv("STECKWERK_PAKETE", str(tmp_path))
    pakete.install(os.path.join(here, "beispiel-pakete", "tuerschild-1.1.0.swpaket"))
    service.reload_pakete()
    try:
        en = i18n.translate_schema(service.schema(), "en")
        assert en["models"]["tuerschild"]["label"] == "Door sign"
        res = i18n.localize(service.generate({"model": "tuerschild"}), "en")
        assert "Hang the sign on a cord through both holes." in res["assemblies"][0]["notes"]
    finally:
        monkeypatch.delenv("STECKWERK_PAKETE")
        service.reload_pakete()
