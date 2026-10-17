# Steckwerk Desktop – macOS SwiftUI App

Eine native macOS-Anwendung für die grafische Gestaltung und Fabrikation mit der Steckwerk-Engine.

## Voraussetzungen

- macOS 14.0 oder neuer
- Xcode Command Line Tools oder vollständiges Xcode
- Python 3.9+ (für die Engine)

## Installation und Start

### Entwicklung

```bash
cd packaging/swift
swift build
swift run SteckwerkDesktop
```

### Bauen des App-Bundles

```bash
cd packaging/swift
./build_app.sh ../dist
open ../dist/Steckwerk\ Desktop.app
```

### Tests

```bash
cd packaging/swift
swift test
```

## Architektur

Die App startet automatisch beim ersten Start einen lokalen Python-Webserver (`webui.py`), der über die Netzwerk-API (`127.0.0.1:5000`) angesprochen wird.

```
SwiftUI App ←→ HTTP/JSON API ←→ Python Engine (webui.py)
```

### API-Endpunkte (alle unter `http://127.0.0.1:5000`)

- `/api/ping` – Verbindungstest
- `/api/schema` – Modelle, Parameter, Konfiguration
- `/api/generate` – Geometrie berechnen
- `/api/save` – SVG/Bericht speichern
- `/api/open-folder` – Ordner im Finder öffnen
- `/api/assistent` – KI-Assistent anfragen
- `/api/bild` – Bild mit KI generieren
- `/api/paket-installieren` – Paket installieren
- `/api/paket-entfernen` – Paket deinstallieren
- `/api/update-check` – Updates prüfen
- `/api/bye` – Sauberer Shutdown

## Konfiguration

### API-Schlüssel

Die App speichert Einstellungen in `UserDefaults`:

- `kiAnbieter` – Standard-KI-Anbieter (ollama, openrouter, chatgpt)
- `openrouterKey` – OpenRouter API-Schlüssel
- `chatgptKey` – ChatGPT/OpenAI API-Schlüssel

### Umgebung

Die Python-Engine wird mit folgenden Variablen gestartet:

- `PYTHONPATH` – erbt vom System
- `--port 5000` – HTTP-Port (fest)

## Signierung

Die App ist anfangs **unsigniert**. Unter macOS müssen Sie sie einmalig freigeben:

1. App starten (Fehler zu erwarten)
2. Systemeinstellungen → Datenschutz & Sicherheit
3. Steckwerk Desktop unter „Programme aus nicht identifizierten Entwicklern" freigeben

## Dateistruktur

```
packaging/swift/
├── Package.swift                           SwiftPM-Manifest
├── Sources/SteckwerkDesktop/               Quellcode
│   ├── SteckwerkApp.swift                  Haupteintrag, App-Lebenszyklus
│   ├── Bridge.swift                        HTTP-Client
│   ├── EngineManager.swift                 Engine-Verwaltung
│   ├── ModelListView.swift                 Sidebar (Modelle)
│   ├── ParameterForm.swift                 Dynamisches Formular
│   ├── PackagesView.swift                  Paketmanager
│   ├── KIView.swift                        KI-Assistenten
│   ├── MaterialView.swift                  Material-Parameter
│   ├── AppUpdateView.swift                 Update-Check
│   ├── PreferencesView.swift               Einstellungen
│   └── Theme.swift                         Design-Konstanten
├── Tests/SteckwerkDesktopTests/
│   ├── SchemaParsingTests.swift            Tests für JSON-Parsing
│   └── BridgeTests.swift                   Tests für HTTP-Client
├── build_app.sh                            App-Bundle-Builder
└── README.md                               Diese Datei
```

## Bekannte Einschränkungen

- SwiftUI-Vorschau (Canvas) funktioniert nicht in der Cloud-Umgebung
- Bildvorschau zeigt nur Schnittlinien (schwarz) und Gravur (blau)
- App ist unsigniert → macOS-Bestätigungsdialog beim ersten Start
- Kein Code-Signing oder Notarisierung (nur für interne Verwendung)

## Fehlerbehebung

### App startet nicht / zeigt „Engine konnte nicht gestartet werden"

1. Python-Installation prüfen: `python3 --version`
2. Repo-Pfad prüfen: Standard ist `~/steckwerk`, sonst Umgebungsvariable `STECKWERK_ROOT` setzen
3. Terminal öffnen, Manual-Test:
   ```bash
   cd /home/user/steckwerk
   python3 webui.py --port 5000
   curl http://127.0.0.1:5000/api/ping
   ```

### Port 5000 schon in Verwendung

```bash
lsof -i :5000
kill -9 <PID>
```

### Swift-Kompilierungsfehler

```bash
cd packaging/swift
swift build clean
swift build -v
```

## Lizenz

Siehe Projekt-ROOT für Lizenzinformationen.
