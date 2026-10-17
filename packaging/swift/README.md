# Steckwerk Desktop – SwiftUI-App

Native macOS-App für Steckwerk, geschrieben in SwiftUI.

## Voraussetzungen

- macOS 14 oder höher
- Xcode mit Command Line Tools oder Swift 5.9+
- Python 3.9+ (für die Engine)

## Start

```bash
cd packaging/swift
swift build -c release
.build/release/SteckwerkDesktop
```

Oder nach dem Bauen der App:

```bash
open Steckwerk\ Desktop.app
```

## Architektur

Die App startet die Python-Engine (`webui.py`) als Kindprozess und kommuniziert über lokale HTTP-APIs (`/api/schema`, `/api/generate`, etc.).

Die Projektlogik (Geometrie, Validierung, KI, Bilder) bleibt komplett in Python. Swift ist nur der Client.

## Bauen & Testen

```bash
swift build
swift test
./build_app.sh ../dist
```

Das erzeugt `Steckwerk Desktop.app` in `../dist`.

## Sicherheit

Die App ist **unsigniert**. Beim ersten Start:
1. Finder: Rechtsklick → Öffnen
2. Oder in „Datenschutz & Sicherheit" → „Allgemein" → App zulassen

## Struktur

- `Sources/SteckwerkDesktop/` – Swift-Code
  - `Bridge.swift` – HTTP-Client
  - `SteckwerkApp.swift` – @main, App-Delegate
  - `*View.swift` – SwiftUI-Views
  - `Theme.swift` – Farben & Layout
- `Tests/` – Unit-Tests (Schema-Parsing, JSON-Decodierung)
- `Package.swift` – Swift Package Manager-Konfiguration

## Bekannte Grenzen

- Vorschau (Canvas) zeigt SVG als Platzhalter (echtes SVG-Rendering auf Anfrage)
- Motiv-Import nur aus Dateien (nicht aus URL)
- App ist unsigniert (kein Notarisierungs-Support geplant)
