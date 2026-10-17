# Steckwerk Desktop

Native macOS-App (SwiftUI) für Steckwerk – ohne Browser. Die App startet die bestehende
Python-Engine als Kindprozess und bedient sie über deren lokale HTTP-API auf `127.0.0.1`.
Geometrie, Validator, Pakete, Updates und KI bleiben vollständig in Python; Swift steuert und zeigt an.

## Herunterladen und starten

1. Unter GitHub → Actions → „macOS Desktop“ den letzten erfolgreichen Lauf öffnen und das Artefakt
   **Steckwerk-Desktop-macOS-dmg** laden (darin `Steckwerk-Desktop-macOS.dmg`). Alternativ gibt es
   **Steckwerk-Desktop-macOS** mit derselben App als ZIP.
2. DMG öffnen und `Steckwerk Desktop.app` auf die Verknüpfung *Programme* ziehen.
3. Die App ist **nicht notarisiert** (nur ad hoc signiert). Beim ersten Start meldet macOS, dass der Entwickler
   nicht überprüft werden kann. Dann unter *Systemeinstellungen → Datenschutz & Sicherheit* bei
   „Steckwerk Desktop“ auf **Dennoch öffnen** klicken – nur einmal nötig, wie bei der bisherigen Mac-App.

### Voraussetzungen

- macOS 14 (Sonoma) oder neuer, Apple Silicon oder Intel
- Python ab 3.9 – gesucht wird wie bei der bisherigen Mac-App: Homebrew, python.org, pyenv, MacPorts,
  dann Apples Command Line Tools (`xcode-select --install`). Ein anderes Python über die Umgebungsvariable
  `STECKWERK_PYTHON` angeben.
- Die Engine steckt in der App (`Contents/Resources/engine`). Beim Entwickeln kann sie mit `STECKWERK_ROOT`
  auf einen Repo-Ordner zeigen.

## Bedienung

- **Seitenleiste:** Modelle nach Gruppen, darunter *Pakete*, *KI*, *Material* und *Updates*.
- **Modell:** links das Formular (Abschnitte wie in der Weboberfläche, Zahlen mit Stepper und Einheit,
  Auswahllisten, Schalter, Text, Motiv-Raster), rechts Vorschau und Prüfbericht.
- **Bauen & prüfen** (⌘B): baut über die Engine und zeigt z. B. „0 FEHLER · 8 Teile · 1 Blatt · CUT-READY“.
  Vorschau: Schnitt schwarz, Gravur blau, Blattrahmen; zoomen mit Pinch oder den Lupen, verschieben durch Ziehen,
  Doppelklick setzt zurück.
- **Exportieren** (⌘E): Ordner wählen; geschrieben werden je Baugruppe die Blatt-SVGs und `pruefbericht.txt`.
  Wie überall in Steckwerk nur, wenn der Validator alles als CUT-READY bestätigt.
- **Ordner öffnen** (⌘O): öffnet den Steckwerk-Ordner (Dokumente/Steckwerk).
- **Einstellungen** (⌘,): Material (T, Kerf, Maßstab, Blatt, Farben) und KI-Anbieter.

## KI und Schlüssel

- **Assistent** (Werte-Vorschläge): läuft über **Ollama** auf diesem Rechner.
- **Motiv zeichnen:** Ollama (lokal, kostenlos), **OpenRouter** oder **ChatGPT** (OpenAI-Images-API,
  Modell `gpt-image-1`). Bei OpenRouter und ChatGPT geht die Beschreibung an den Anbieter und kostet Guthaben;
  das Monatslimit gilt für beide.
- **Schlüssel** trägst du unter Einstellungen → KI-Anbieter ein. Die App gibt ihn nur an die lokale Engine weiter,
  die ihn im macOS-Schlüsselbund ablegt. Die App speichert ihn nirgends, zeigt ihn nie wieder an und meldet nur,
  ob einer hinterlegt ist. In dieses Repository gehören keine Schlüssel.
- ChatGPT ist nur für Bilder angebunden. Der Assistent bleibt bei Ollama, damit die Anbieterwahl dort
  einfach und lokal bleibt.

## Aufbau

```
packaging/swift/
  Package.swift              SwiftPM: SteckwerkCore (Bibliothek) + SteckwerkDesktop (App, nur macOS)
  Sources/SteckwerkCore/     ohne Oberfläche, baut und testet auch unter Linux
    EngineClient.swift       HTTP-Client (URLSession), Header X-Steckwerk, Fehlermeldungen der Engine
    EngineLauncher.swift     Python und Engine finden, Kindprozess starten/beenden
    Schema.swift, APIModels.swift, JSONValue.swift   Antworten der Engine
    ParameterLogic.swift     Vorgaben, Sichtbarkeit (when), Abschnitte, Eingabeprüfung, Motiv-Listen
    SheetGeometry.swift      liest die Blatt-SVGs (M/L/Z) für die native Vorschau
    Report.swift             Prüfbericht aufbereiten, Exportdateien
  Sources/SteckwerkDesktop/  SwiftUI-Oberfläche
  Tests/SteckwerkCoreTests/  Unit- und Integrationstests (Fixtures aus echten, bereinigten Antworten)
  bridge_start.py            startet die Engine für die App (nur Standardbibliothek, Python 3.9+)
  build_app.sh               baut das .app-Bundle
```

### Lebenszyklus der Engine

- `bridge_start.py` startet `webui.py` im App-Modus auf einem freien Port und meldet ihn mit
  `STECKWERK_PORT=<port>`. Läuft schon eine Steckwerk-Instanz derselben Version, wird sie mitbenutzt.
- Die Engine endet, wenn die App sich abmeldet (`/api/bye`, `/api/quit`) oder wenn ihre stdin-Leitung zur App
  abreißt – so bleibt auch nach einem Absturz der App kein Waisenprozess zurück. Beim Beenden schickt die App
  zusätzlich SIGTERM und nach 3 s SIGKILL.
- Startet die Engine nicht innerhalb von 15 s, zeigt die App „Engine startet nicht“ mit den letzten Meldungen.

## Entwickeln

```bash
cd packaging/swift
swift build
STECKWERK_ROOT="$(cd ../.. && pwd)" swift test     # inkl. Integrationstest gegen die echte Engine
STECKWERK_ROOT="$(cd ../.. && pwd)" swift run SteckwerkDesktop
./build_app.sh ../dist                              # App-Bundle
"../dist/Steckwerk Desktop.app/Contents/MacOS/SteckwerkDesktop" --self-test
```

Der Selbsttest startet ohne Fenster die eingebaute Engine mit leerem temporärem HOME und eigenen Daten, baut das
Wichtelhaus mit Standardwerten und prüft „0 FEHLER“. Einstellungen und Schlüsselbund berührt er nicht.

Unter Linux bauen und testen nur `SteckwerkCore` und die Tests; die Oberfläche entsteht in CI auf einem
macOS-Runner (`.github/workflows/macos-desktop.yml`), der auch das Artefakt erzeugt.

## Grenzen dieser Version

- Unsigniert/nicht notarisiert; Updates des Programms lädst du als neue App, Paket-Updates gehen in der App.
- Motive platzieren: Liste mit Zahlenfeldern (der grafische Platzierungs-Editor folgt später).
- Oberfläche nur auf Deutsch.
