# Changelog

Alle nennenswerten Änderungen an Laserforge. Versionen folgen dem Schema Haupt.Neben.Fix.

## 1.7.0 – 2026-10-10

- Updates direkt in Laserforge: Der neue Bereich „Updates“ zeigt neue Programmversionen und Pakete
  aus dem Update-Kanal. Pakete installierst oder aktualisierst du mit einem Klick, die Mac-App ersetzt
  sich selbst durch die neue Version und startet neu.
- Beim Start prüft Laserforge automatisch (abschaltbar); gibt es Neues, erscheint oben „Updates“ mit Anzahl.
- Jede Datei wird vor dem Installieren über ihre Prüfsumme kontrolliert.
- Für ein privates GitHub-Repo trägst du einmal einen Lese-Schlüssel ein; er liegt auf dem Mac im Schlüsselbund.
- Kommandozeile: `--update-pruefen`, `--update-paket ID|alle`, `--update-schluessel`, `--update-kanal`.
- Für Herausgeber: `packaging/update_kanal.py` baut den Update-Kanal (feed.json + Dateien).

## 1.6.0 – 2026-10-09

- Eigene Motive: SVG- und PNG-Dateien hochladen (PNG wird automatisch nachgezeichnet, auf Wunsch mit
  umgekehrten Farben). Die Motive landen in einer Motiv-Bibliothek, 19 Motive sind schon dabei.
- Neue Vorlagen in der Gruppe „Eigene Motive“: Aufsteller mit Sockel, Schild, Anhänger, Untersetzer
  und Silhouette (das Motiv selbst als Umriss, mit Sockel, Öse oder ohne Fuß).
- Motive in der Vorschau mit der Maus verschieben, an der Ecke skalieren, am Punkt drehen; dazu
  Felder für Größe, Drehung und Spiegeln. Je Motiv: ausschneiden, Umriss gravieren oder flächig gravieren.
- Klare Meldungen, wenn ein Motiv über den Rand ragt, zu dicht an einem anderen sitzt oder zu feine
  Stellen hat; herausfallende Inseln werden im Prüfbericht genannt.
- Kommandozeile: `--motive`, `--motiv-import DATEI`, `--motiv-entfernen ID`.
- Pakete können Motive über `motiv(...)` und `motive(...)` aus `pakete.py` nutzen.

## 1.5.1 – 2026-10-09

- Mac-App: Startet man Laserforge direkt aus „Downloads“, zeigte das Fenster nach kurzer Zeit nur
  noch einen Fehler, weil macOS die temporäre Kopie der App entfernt hatte. Laserforge läuft in
  diesem Fall jetzt im Vordergrund weiter und bietet die Installation erneut an.
- Eine laufende Laserforge, die ihre Dateien nicht mehr findet, wird beim nächsten Start
  automatisch beendet und neu gestartet.

## 1.5.0 – 2026-10-09

- Neue Fahrzeuge: Tender, Personenwagen, Güterwagen, Bus und Traktor (große Hinterräder).
- Modell „Zug-Set“: Lok, Tender und bis zu 6 Wagen im Maßstab der Lok, Aufschrift je Fahrzeug.
- Kupplungslöcher in Front und Heck von Lok, Tender und Wagen (`kupplung`).
- Erweiterungspakete (`.lfpaket`, Standard 1): laden in der App und per `--paket-installieren`,
  erstellen mit `--paket-neu`, `--paket-pruefen`, `--paket-packen`. Spezifikation in PAKETE.md,
  Beispielpaket „Türschild“.

## 1.4.0 – 2026-10-09

- Neues Modell Schwibbogen: Szene Dorf, Wald oder Kirche, 1–11 Kerzen, ausgeschnittene Fenster
  zum Hinterleuchten, Zierlinie auf dem Bogen, Text auf der Sockelleiste, Bodenplatte.

## 1.3.0 – 2026-10-09

- Acht neue Schmuckformen: Lebkuchenmann, Nikolausstiefel, Zuckerstange, Geschenk, Kerze, Engel,
  Tannenzapfen, Schneemann – mit gravierten Details; vier davon auch als 3D-Steckversion.

## 1.2.0 – 2026-10-09

- Gestaltung und Beschriftung: Fensterformen, Sprossen, Läden, Türschmuck, Giebel, Wand- und
  Dachgravuren, Zierleisten, Schilder mit Rahmen, sechs Schriftstile mit Kleinbuchstaben,
  Umlauten und Symbolen, automatischer Zeilenumbruch.
- Texte auf Briefkasten, Figurensockeln, Fahrzeugen und Schmuck; Zierlinien für Fahrzeuge.
- Weboberfläche mit aufklappbaren Gruppen und „Gestaltung würfeln“; Kommandozeile mit `-O`/`--options`.
- Mac-App erkennt ältere Versionen und bietet „Ersetzen“ an.

## 1.1.0 und früher

- Wichtelhaus, Serie, Zubehör, Christbaumschmuck, Schneeflocken und Steckfahrzeuge.
- Validator, Weboberfläche, Konfigurator und Mac-App.
