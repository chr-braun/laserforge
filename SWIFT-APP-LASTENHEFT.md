# Steckwerk Desktop – Umsetzungsauftrag für Claude Code (Cloud)

**Für:** Claude Code in der Cloud-Sitzung (Linux-Build-Umgebung, Repo `chr-braun/steckwerk`)
**Von:** pi (Sitzung am Mac von Christian), 17.10.2026
**Status:** Vorschlag – Christian liest das, entscheidet über Start und mergt am Ende selbst.

Christian wünscht sich neben der bestehenden Mac-App (Webserver + Browser) eine
**native macOS-App in SwiftUI ohne Browser**. Diese Datei ist so geschrieben,
dass du (Claude Code) sie ohne weitere Rückfragen umsetzen kannst. Ein paar
Sachen sind bewusst begrenzt – lies Abschnitt 2 (Umgebung) und 8 (Grenzen).

---

## 1. Ziel in einem Satz

Eine **SwiftUI-App „Steckwerk Desktop"**, die die bestehende Python-Engine
als Kindprozess startet und als nativer Client über deren lokale HTTP-API
bedient. **Keine Projektlogik in Swift** – Geometrie, Validator, Pakete,
Updater und KI bleiben in Python.

## 2. Deine Umgebung – was geht, was nicht

- Du arbeitest im Repo, Branch **`claude/project-thread-y7q7zo`** (Arbeitsbranch,
  Stand 2.8.0 + Paket Bewegung). Neuer Unter-Branch dafür: **`claude/swift-desktop`**.
- Deine Sandbox ist **Linux** → du kannst den Swift-Quellcode **schreiben**,
  aber **nicht kompilieren** (SwiftUI/macOS geht nur auf macOS).
  Kompiliert wird über **GitHub Actions auf einem macOS-Runner** (siehe Abschnitt 6)
  – `macos-latest` hat Xcode, SwiftPM reicht völlig.
- **Kein SwiftUI-Vorschau-Gefummel möglich:** du kannst das Fenster nicht sehen.
  Halte die Oberfläche deshalb schlicht, gut strukturiert und baue
  `swift build` + `swift test` in CI ein, damit du Fehler selbst siehst.
- Beachte die Projektregeln aus `UEBERGABE`/`CONTRIBUTING`: Commit-Meldungen auf
  Deutsch, **kein KI-Modellname** im Commit-Text (eine `Co-Authored-By:`-Zeile
  darfst du anhängen), keine Pfade/Tokens in Dateien, nur Python-Stdlib im
  Python-Code (3.9-kompatibel, kein `match`, kein `X | Y`).

## 3. Architektur

```
┌────────────────────────────────┐   HTTP/JSON   ┌──────────────────────────────┐
│  Steckwerk Desktop.app (Swift) │ ────────────► │  webui.py (bestehender Server)│
│  SwiftUI, SwiftPM, macOS 14+   │  127.0.0.1    │  service/validator/pakete/    │
│  startet Engine als Kindprozess│ ◄──────────── │  updater/assistent/bildgen    │
└────────────────────────────────┘               └──────────────────────────────┘
```

- App startet beim ersten Fensteraufruf: `python3 webui.py` mit `--port <frei>`
  als Kindprozess (falls webui.py keinen Port-Parameter hat: Umgebungsvariable
  oder kleines Wrapper-Skript `packaging/swift/bridge_start.py` – aber
  **webui.py selbst nicht umbauen**, außer einem optionalen `--port`-Argument).
- Warten auf `/api/ping` (max. 15 s, dann Fehlerdialog „Engine startet nicht –
  Details“ mit dem letzten Stderr).
- Beenden: App-Fenster zu → `/api/bye` bzw. `/api/quit` senden, Kindprozess
  mit SIGTERM nachziehen (Kill after 3 s). App-Absturz: Engine als
  Waisenprozess vermeiden → Prozessgruppe setzen und bei `applicationWillTerminate`
  aufräumen; zusätzlich beim Start prüfen, ob bereits ein Server läuft
  (`/api/ping`) und diesen dann **nutzen** statt zweiten zu starten.

## 4. Genutzte Endpunkte (existieren alle schon in webui.py)

| Funktion | Endpunkt |
|---|---|
| Modelle/Pakete/Motive/Config | `/api/schema` |
| Bauen + Validieren | `/api/generate` |
| Zip (später, optional) | `/api/zip` |
| Export speichern / Ordner öffnen | `/api/save`, `/api/open-folder` |
| Pakete installieren/entfernen | `/api/paket-installieren`, `/api/paket-entfernen` |
| Updates (App/Pakete) | `/api/update-check`, `/api/update-programm`, `/api/update-paket`, `/api/update-einstellungen` |
| Assistent | `/api/assistent`, `/api/assistent-einstellungen`, `/api/assistent-status` |
| Motiv zeichnen/Importieren | `/api/bild`, `/api/bild-modelle`, `/api/bild-einstellungen`, `/api/motiv-import`, `/api/motiv-entfernen`, `/api/motiv-design` |
| Lifecycle | `/api/ping`, `/api/bye`, `/api/quit` |

Prüfe beim Umsetzen die exakten Request/Response-Felder in `webui.py`
(`service.design/generate`, `bildgen.erzeugen`, …) – dieses Dokument nennt die
Zwecke, nicht jedes JSON-Feld. `/api/schema` liefert `models` (je Modell:
`label`, `desc`, `group`, `params[]` mit `type` ∈ `num, int, select, text,
flag, motiv, motive`, `key`, `label`, `default`, `options[]`, `min`, `max`,
`step`, `unit`, `help`, `section`), `config` (Config-Infos), `motive`,
`pakete`.

## 5. Zu bauende Dateien (alle neu, im Arbeits-Branch `claude/swift-desktop`)

```
packaging/swift/
  Package.swift                  # SwiftPM, macOS 14+, ausführbares Target „SteckwerkDesktop“
  Sources/SteckwerkDesktop/
    SteckwerkApp.swift           # @main, App-Scene, Engine-Lifecycle, Menüleiste
    Bridge.swift                 # HTTP-Client (URLSession), JSON-Codierung, Ping/Retry
    ModelListView.swift          # NavigationSplitView-Sidebar: Gruppen → Modelle
    ParameterForm.swift          # dynamisches Formular aus schema.models[].params
    BuildView.swift              # Bauen/Prüfen-Knopf, Ergebnisstatus, Export-Dialog
    PreviewCanvas.swift          # SwiftUI Canvas: Polylines (Schnitt schwarz,
                                 #  Gravur blau), Blattrahmen, Zoom/Pan (Magnification+Drag)
    ReportView.swift             # Prüfbericht nativ (grün/rot), Montagehinweise
    PackagesView.swift           # Kanal-Liste, Installieren, .swpaket-Dateidialog
    KIView.swift                 # Anbieterwahl Ollama/OpenRouter/ChatGPT, Assistent,
                                 #  Motiv zeichnen → /api/bild + /api/motiv-import
    MaterialView.swift           # T, Kerf, Maßstab, Blatt, Farben
    AppUpdateView.swift          # Update-Check/-Programm
    Theme.swift                  # Farben/Abstände (warm, passend zur Vorschau)
  Tests/SteckwerkDesktopTests/
    SchemaParsingTests.swift     # models/params/config aus /api/schema parsen
    BridgeTests.swift            # URL-Builder, JSON-Decodierung (ohne echten Server)
  build_app.sh                   # baut .app-Bundle: Contents/{Info.plist, MacOS/…}
  README.md                      # Start (⌘-Doppelklick / open), Voraussetzungen
.github/workflows/
  macos-desktop.yml              # macOS-Runner: swift build && swift test;
                                 #  Artifact „Steckwerk-Desktop-macOS.zip“
```

**Info.plist:** `CFBundleName Steckwerk Desktop`, `CFBundleIdentifier
de.steckwerk.desktop`, `LSMinimumSystemVersion 14.0`, `NSHighResolutionCapable`,
`CFBundleIconFile` (erstmal ohne Icon; `make_icon.py`-Ableitung später).

**Menüleiste:** Datei (Exportieren… ⌘E, Ordner öffnen ⌘O), Modell (Bauen &
prüfen ⌘B), Fenster, Hilfe. Einstellungen ⌘, → Material/KI-Anbieter.

## 6. CI (macos-desktop.yml, Kurzskelett)

```yaml
name: macos-desktop
on: [push, pull_request]
jobs:
  build:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v4
      - run: swift --version
      - run: cd packaging/swift && swift build -v
      - run: cd packaging/swift && swift test
      - run: cd packaging/swift && ./build_app.sh ../dist
      - uses: actions/upload-artifact@v4
        with: { name: Steckwerk-Desktop-macOS, path: packaging/dist }
```

Aufpassen: Actions im Repo beachten (bestehende Workflows nicht stören);
Branch „updates“ und Tag-Push **nicht** von CI anfassen.

## 7. UI-Vorgaben (aus dem Lastenheft, das Christian gesehen hat)

- `NavigationSplitView`: Sidebar (Modelle nach `group`, dann Pakete / KI /
  Material als Fußpunkte), Detailbereich rechts.
- Formular: Zahlen mit Steppern und Einheiten-Suffix, `Picker` für select,
  `Toggle` für flag, `TextEditor` für mehrzeiliges text, Motiv-Auswahl als
  Grid mit Thumbnails (aus `schema.motive`). `section` → eigene `Section`.
- Vorschau: erstes Blattplan nativ zeichnen; wenn `/api/generate` die Polylines
  nicht liefert, die Blattgeometrie aus dem generierten SVG parsen ist
  **nicht** nötig – nimm was `service.process()`/`generate()` an Geometrie
  zurückgibt; reicht nur die Teileliste, zeichne Teile nebeneinander und
  beschrifte „Vorschau“.
- Farben: warm (Hintergrund #f5f2ec, Karten weiß, Akzent Bernstein #b45309),
  Dunkelmodus über Systemfarben (`.background(.background)` etc.).
- Statusanzeige (Engine „lädt/läuft/gestoppt“) im ToolbarItem.

## 8. Grenzen des Auftrags (nicht tun)

1. **webui.py nur minimal anfassen:** erlaubt ist ausschließlich ein optionaler
   `--port`-Parameter (oder ENV), falls nicht schon vorhanden. Alles andere an
   Engine-Dateien: nicht umbauen.
2. **Eine kleine Python-Änderung IST Teil des Auftrags:** `bildgen.py` um
   dritten KI-Anbieter **„chatgpt“** erweitern (OpenAI-Images-API
   `POST {basis}/images/generations`, Modellstandard `gpt-image-1`,
   Antwort `b64_json`; Basis fest `https://api.openai.com/v1`, Key über den
   bestehenden Schlüssel-Mechanismus; Monatslimit wie bei OpenRouter). Regeln:
   nur Stdlib, 3.9-kompatibel, Fehler als `BildFehler` mit deutschem Text,
   Settings-Feld `quelle` erweitern („chatgpt“ zusätzlich zu „ollama“,
   „openrouter“) und `/api/bild-einstellungen` weiterreichen. Zusätzlich
   `assistent`-Anbieterwahl erweitern, dass Chat/Assistent auch über
   OpenAI-kompatible Basen laufen kann — **aber nur, wenn es sauber bleibt**
   (sonst: Assistent bleibt Ollama/OpenRouter, ChatGPT nur für Bilder; das
   wäre ok und bitte so dokumentieren).
3. Keine Tags, keine Releases, kein Push auf „updates“, kein Merge nach main –
   **PR auf den Arbeitsbranch `claude/project-thread-y7q7zo`**, CI muss grün sein.
4. macOS-Schlüsselbund der Python-Seite (`security`-CLI) nicht umbauen.
5. Die Web-Oberfläche (`web/index.html`) nicht anfassen – sie bleibt Fallback.

## 9. Definition of Done

- [ ] `swift build` und `swift test` grün (lokal in CI auf macOS-Runner)
- [ ] App startet auf macOS, zeigt Modelle aus `/api/schema`, baut
      „wichtelhaus“ mit Standardwerten, zeigt „0 FEHLER“ und zeichnet Vorschau
- [ ] Export schreibt SVG + Prüfbericht (Ordnerwahl nativ)
- [ ] Paket installieren aus Kanal + lokale .swpaket-Datei
- [ ] Assistent liefert Werte für ein Modell (Ollama; OpenRouter mit Key)
- [ ] `bildgen`-Erweiterung „chatgpt“ mit Stdlib-Tests (Mock-Antwort)
- [ ] App-Update-Check zeigt „Steckwerk Desktop“-Version
- [ ] README (Start, Voraussetzungen, Keys) + CI-Artefakt-Zip
- [ ] PR-Beschreibung: Screenshots der laufenden App (vom macOS-Runner nicht
      möglich → von Christian oder weglassen), Liste der neuen Dateien,
      Hinweis auf unsignierte App

## 10. Backlog (nicht in diesem Auftrag)

Motiv-Platzierungs-Editor nativ (V2), Passungstest-Assistent, EN-Lokalisierung,
Notarisierung, iCloud-Export, Kugel-Animation in der Vorschau.

---

## Anhang A – Begriffe für Christian (Kurzform)

- **Engine** = der Python-Teil (steckwerk.py & Co.), wie heute.
- **Bridge** = die lokale HTTP-Verbindung zwischen App und Engine.
- **SwiftPM** = Bauwerkzeug für Swift (im Command Line Tools enthalten).
- Die App ist anfangs **unsigniert** → einmalige Freigabe unter
  „Datenschutz & Sicherheit“, genau wie die heutige Mac-App.
