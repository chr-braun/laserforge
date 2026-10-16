# Steckwerk-Wiki

Willkommen! Hier steht alles, was wir bisher für **Steckwerk** gebaut haben – vom ersten Wichtelhaus bis zum
KI-Assistenten. Steckwerk hieß bis Version 1.7.0 **Laserforge**; im Repo und in alten Dateinamen taucht der
alte Name deshalb noch auf.

## Was ist Steckwerk?

![Übersicht der Modelle](medien/uebersicht.png)


Steckwerk erzeugt **parametrische, geprüfte Lasercut-SVGs** für Steckmodelle aus Holz, Pappe oder Acryl:
Wichtelhäuser und ganze Serien, Weihnachtszubehör, Christbaumschmuck, Schneeflocken, Schwibbögen und
Steckfahrzeuge mit drehenden Rädern. Über Pakete kommen weitere Modelle dazu (Halloween, Filigran,
Mehrlagig, Weihnachtsdeko …).

Das Besondere: Jede Datei wird **vor dem Schreiben geprüft**. Kerf, Steckverbindungen, Mindeststege und das
fertige SVG werden kontrolliert. Gibt es auch nur einen Fehler, wird nichts geschrieben.

- Reines Python (ab 3.8), nur Standardbibliothek, läuft komplett lokal.
- Bedienung als Mac-App, im Browser, als Konfigurator im Terminal oder per Kommandozeile.
- Deutsch und Englisch.
- Abgestimmt auf deinen **xTool M2** mit **xTool Creative Space** (Rot = Schneiden, Blau = Ritzen).

## Aktueller Stand

| | |
|---|---|
| Programm | Steckwerk **2.5.0** (16.10.2026) |
| Pakete im Update-Kanal | Mehrlagig 1.2.0 · Filigran 1.1.0 · Halloween 1.3.0 · Weihnachtsdeko 1.1.0 · Türschild 1.1.0 · Verzierungen 1.3.0 · Umrandungen 1.0.0 · Wichtel 1.0.0 · Werkstatt 1.0.0 |
| Tests | 1157 grün (Python 3.13; CI zusätzlich 3.9) |
| Repo | `chr-braun/laserforge` (umbenannt in `chr-braun/steckwerk`), Lizenz MIT |

## Seiten

- [Downloads](Downloads.md) – Mac-App und alle Pakete zum Herunterladen

- [Installation](Installation.md) – Mac-App, Weboberfläche, Python
- [Bedienung](Bedienung.md) – Oberfläche, Export, Tastenkürzel, Kommandozeile
- [Material und Laser](Material-und-Laser.md) – xTool M2, Materialprofile, Kerf, Montage
- [Modelle](Modelle.md) – alle eingebauten Vorlagen
- [Gestaltung und Beschriftung](Gestaltung-und-Beschriftung.md) – Fenster, Gravuren, Schriften
- [Eigene Motive](Eigene-Motive.md) – SVG/PNG importieren und platzieren
- [Pakete](Pakete.md) – Erweiterungspakete, alle bisherigen Pakete, eigene bauen
- [KI-Funktionen](KI-Funktionen.md) – Assistent und „Motiv zeichnen“ mit Ollama oder OpenRouter
- [Updates](Updates.md) – Updater und Update-Kanal
- [Entwicklung](Entwicklung.md) – Aufbau des Codes, Tests, Veröffentlichen
- [Versionsverlauf](Versionsverlauf.md) – was wann dazukam
- [Offene Punkte](Offene-Punkte.md) – was noch ansteht
