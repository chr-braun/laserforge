# Entwicklung

## Wie Steckwerk entstanden ist

Steckwerk wurde komplett in der Cloud gebaut (mit Claude) und liegt im Repo `chr-braun/laserforge`
(inzwischen umbenannt in `chr-braun/steckwerk`). Eine Arbeitskopie mit allen Mac-Zips und Paketen liegt
im Projektordner. Der Code muss mit Python 3.8/3.9 laufen, weil das Python von Apples Command Line Tools
3.9 ist, und nutzt nur die Standardbibliothek.

## Aufbau

```
steckwerk.py      Engine: Config, Geometrie, Kerf-Offset, Bauteile, Zinken/Tabs, Layout, SVG
laserforge.py     Kompatibilitäts-Alias für alte Pakete (from laserforge import …)
validator.py      Geometrie-, Verbindungs-, Blatt- und SVG-Prüfung
service.py        gemeinsame Schicht für CLI, Konfigurator und Web (MODEL_INFO = Formulare)
cli.py            Kommandozeile und --konfigurator
webui.py          lokaler Webserver; web/index.html ist die ganze Oberfläche (ohne Build-Schritt)
steckwerk_app.py  App-Betrieb: eine Instanz, Browserfenster, Selbst-Beenden, Mac-Installation
i18n.py           Deutsch/Englisch (deutsche Texte sind die Schlüssel)
motive.py         SVG-Parser, PNG-Nachzeichner, Motiv-Bibliothek
pakete.py         Paket-Standard: laden, prüfen, packen
updater.py        Update-Kanal lesen, Prüfsummen, Installieren
assistent.py      Ollama-Assistent (nur localhost/eigenes Netz)
bildgen.py        Motiv zeichnen: Ollama und OpenRouter, Kostenschätzung, Monatslimit
models/           alle Modelle; _deko.py = Gestaltungs-Baukasten, _font.py = Einlinien-Schrift
packaging/        build_macos.py, make_icon.py, update_kanal.py
tests/            pytest
```

## Eigenes Modell ergänzen

1. In `models/` ein Modul mit `build(cfg, **parameter) -> Assembly` anlegen (mm, y nach oben, Außenkontur
   gegen den Uhrzeigersinn).
2. Für jede Steckverbindung an beiden Teilen ein `JointFeature` anlegen und mit
   `asm.connect("teilA:feature", "teilB:feature")` verbinden – der Validator prüft sie dann automatisch.
3. In `models/__init__.py` unter `MODELS` und in `service.py` unter `MODEL_INFO` eintragen. Optionen mit
   `section` landen in aufklappbaren Gruppen, `when` blendet sie bedingt ein.
4. Neue Gravuren immer über `_deko.Canvas`, dann kommen sie nie auf Schnitte.
5. Neue deutsche Oberflächentexte brauchen einen englischen Eintrag (`EN_UI`/`EN_RX` in
   `web/index.html` bzw. `i18n.py`).
6. Neue Python-Datei auf oberster Ebene? Dann in `packaging/build_macos.py` unter `CODE_FILES` eintragen
   (ein Test passt darauf auf).

## Tests

```bash
python3 -m pip install pytest
python3 -m pytest -q
```

Stand 2.8.0: 1267 Tests, grün auf Python 3.13 (CI zusätzlich 3.9). Auf GitHub laufen sie bei jedem Push (Python 3.9 und
3.12, Linux und macOS). Abgedeckt sind jede Gestaltungsoption, Engine, Validator (positiv und negativ),
jedes Modell, CLI, Weboberfläche, App-Betrieb, Pakete, Motive, Updater und der Assistent (mit
nachgebautem Ollama/OpenRouter-Server).

Oberfläche testen: `python3 webui.py --port 8799 --no-browser` und Screenshots mit Playwright.

## Neue Version veröffentlichen

1. Version und `CHANGELOG.md` / `CHANGELOG.en.md` pflegen, Tests grün.
2. Auf `main` pushen.
3. Mac-App bauen: `python3 packaging/build_macos.py --out dist`.
4. In den [Update-Kanal](Updates.md) stellen.

Ein Tag `v<version>` soll per GitHub Actions die Mac-App bauen und ein Release anlegen
(`.github/workflows/release.yml`). Aus der Cloud brach der Tag-Push bisher ab, deshalb verteilen wir die
Versionen über den Update-Kanal und die Zips im Projektordner.

## Ideen und Fehler melden

Im Repo gibt es Vorlagen für Issues („Fehler“ und „Idee“) und eine PR-Vorlage, dazu `CONTRIBUTING.md`.
