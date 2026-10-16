# Changelog

Alle nennenswerten Änderungen an Steckwerk. Versionen folgen dem Schema Haupt.Neben.Fix.

## 2.5.1 – 2026-10-16

- Fehler behoben: Modelle aus Paketen (z. B. „Spitzenschmuck“) ließen sich manchmal nicht laden, mit der Meldung „Bibliothek von verzierungen lässt sich nicht laden … has no attribute Figur“. Ursache war, dass die Oberfläche Pakete gleichzeitig aus mehreren Anfragen lädt. Jetzt wartet jede Anfrage, bis ein Paket fertig geladen ist.
- Wichtel 1.0.1 lädt seine Hilfsmodule ebenfalls geschützt.

## 2.5.0 – 2026-10-16

- Ein Paket je Thema: Alles rund um Wichtel steckt jetzt im Paket **Wichtel** 1.0.0. Die fünf einzelnen
  Pakete Wichtelmöbel, Wichteltür, Wichtelzubehör, Wichtelwelt und Wichtelfiguren räumt Steckwerk beim
  Installieren selbst weg. Dafür gibt es in der `paket.json` die neue Angabe `ersetzt` (siehe PAKETE.md).
- Neu im Paket Wichtel: **Lebkuchenstand** mit gestreifter Markise, Namensschild, Herzgirlande, Theke und
  Pflaster-Grundplatte, dazu Lebkuchenherzen, Lebkuchenmänner und Zuckerstangen.
- Neu: **Kreidetafel** zum Aufstellen und **Backstube** mit Blech, Backbrett, Teigrolle, Ausstechern und
  Plätzchen.
- Neu: **Wichtel-Briefkasten** mit Fähnchen und Briefen, **Gartenzaun** in zwei Lagen, **Werkbank** mit
  Schraubstock und Werkzeug und eine **Wegelaterne**, die über Kreuz gesteckt wird. Alles passt im
  Wichtel-Maßstab zusammen.
- **Verzierungen** 1.3.0 passt die Hinweise zum Wichtel-Maßstab an das neue Paket an.

## Paket-Updates – 2026-10-16

- **Wichtelfiguren** 1.0.0 – der **Schicht-Wichtel**: ein skandinavischer Wichtel aus vier Lagen zum Bemalen
  und Aufeinanderleimen. Tief sitzende Mütze (umgeknickt, spitz oder mit Bommel) mit graviertem Muster
  (Sterne, Herzen, Streifen, Norweger-Zacken), Fellkrempe, dicke Nase, wallender Bart mit gravierten
  Strähnen (lang, rund, lockig oder mit zwei Zipfeln), Fäustlinge, Stiefel und ein dunkler Schattenrand.
  Dazu Laterne, Herz, Stern am Stab, Tannenbaum oder Geschenk, und eine Standplatte mit Namen oder eine Öse
  zum Aufhängen. 60 bis 300 mm hoch.
- **Wichtelwelt** 1.1.0 nimmt im Wichtelzimmer jetzt den Schicht-Wichtel als Figur (ab 60 mm; die einfache
  Steckfigur gibt es weiter unter „Figur“).
- **Werkstatt** 1.0.0 – Passungstest: ein Kamm mit Schlitzen in leicht verschiedenen Breiten und ein Probestück.
  Unter jedem Schlitz steht der Kerf, mit dem genau dieser Schlitz zur Standardbreite wird. Der Wert unter dem
  Schlitz, in dem das Probestück satt sitzt, kommt ins Materialprofil.
- **Wichtel-Maßstab**: Wichtelmöbel, Wichteltür und Wichtelzubehör 1.1.0 richten ihre Maße auf Wunsch nach der
  Größe deiner Wichtelfigur (Standard 70 mm). Dann passen Tür, Fenster, Bank, Tisch, Bett, Leiter, Wegweiser
  und Wäscheleine zusammen. Unter „Maßstab: eigene Maße“ stellst du wie bisher alles selbst ein.
- **Wichtelwelt** 1.0.0 – Wichtelzimmer auf Knopfdruck: Wichtelfigur, Tür, Fenster und Möbel (auf Wunsch auch
  Leiter, Wegweiser und Wäscheleine) im selben Maßstab, mit deinem Namen auf Türschild, Bett und Figur.
- **Verzierungen** 1.2.0 bringt den gemeinsamen Wichtel-Maßstab mit. Ist der Wichtel für die Materialstärke zu
  klein, sagt Steckwerk jetzt, ab welcher Größe es passt.

## Paket-Updates – 2026-10-15

- **Verzierungen** 1.1.0 – die Bibliothek bringt jetzt auch die Motiv-Figuren und die Halloween-Formen mit,
  die bisher in mehreren Paketen doppelt steckten.
- **Mehrlagig** 1.2.0, **Halloween** 1.3.0 und **Weihnachtsdeko** 1.1.0 nutzen diese Bibliothek statt eigener
  Kopien. Die Teile bleiben gleich, die Pakete werden kleiner, und Verbesserungen an Ornamenten kommen
  überall gleichzeitig an. Die Quellen liegen jetzt im Repo unter `paketquellen/`.
- **Halloween** 1.3.0 behebt zwei seltene Prüffehler: Beim Spukschloss mit Spinne und beim Kürbis mit Blatt
  konnten bei manchen Größen spitze Zwickel den Kerf-Ausgleich stören.
- **Filigran** 1.1.0 – Muster-Rezepte beim Spitzenschmuck: Unter „Rezept“ stellst du dir aus Bausteinen
  (Blüten, Bögen, Speichen, Zickzack, Perlen, Ranken, Sterne, Tropfen, Herzen) von innen nach außen dein
  eigenes Muster zusammen. „Zufall“ würfelt mit jedem Startwert ein neues Muster und schreibt das Rezept dazu.
  Der Assistent kann Rezepte aus einer Beschreibung vorschlagen.

## 2.4.0 – 2026-10-15

- Pakete können jetzt andere Pakete benutzen: `benoetigt` in der `paket.json` nennt sie mit Mindestversion,
  `bibliothek` bietet eigene Formen und Werkzeuge allen anderen Paketen an. Über **Updates** kommen
  benötigte Pakete automatisch mit, und ein Paket, das andere noch brauchen, lässt sich nicht entfernen.
  Details in PAKETE.md.
- **Verzierungen** 1.0.0 – die gemeinsame Ornament-Bibliothek für alle Pakete (Rosetten, Eckornamente,
  Bordüren, Kanten, Durchbrüche, Ausschnittmotive, Rahmenformen) plus die Modelle Zierstück und Zierleiste.
- **Umrandungen** 1.0.0 – Bilderrahmen (9 × 13 bis 15 × 20 cm oder eigenes Maß, mit Sockel oder
  Schlüsselloch) und Zierrahmen mit Schild und graviertem Text.
- **Wichtelmöbel** 1.0.0 – Bank mit Lehne, Tisch mit Hockern und Bett mit graviertem Kissen und Decke,
  alles gesteckt.
- **Wichteltür** 1.0.0 – Tür mit Steinbogen oder Holzrahmen, Stufe und Namensschild, dazu ein Fenster
  mit Sprossen, Gardinen, Fensterläden und Blumenkasten.
- **Wichtelzubehör** 1.0.0 – Steckleiter, Wegweiser mit eigenen Ortsnamen und Wäscheleine mit Mini-Wäsche.

## 2.3.0 – 2026-10-11

- Aufgeräumte Seitenleiste: ein Suchfeld oben (⌘K oder ⌘F), darunter die zuletzt benutzten Modelle.
  Die Gruppen sind nach „Vorlagen“ und „Aus Paketen“ getrennt, zeigen ihre Anzahl und bleiben
  eingeklappt, bis du sie öffnest. Die Gruppe des gewählten Modells ist immer offen.
- Assistent im Inspektor: Ein kleines Sprachmodell auf deinem Rechner (Ollama, z. B. qwen2.5:3b) macht aus
  einer kurzen Beschreibung passende Werte. Steckwerk grenzt jede Zahl ein und verwirft Unpassendes.
  „Rückgängig“ stellt die alten Werte wieder her. Einschalten unter Einstellungen → Assistent.
- Neu: **Motiv zeichnen …** in der Seitenleiste. Ein Bildmodell zeichnet dein Motiv nach Beschreibung. Mit
  einem Schieberegler stellst du die Schwelle ein, dann landet es als eigenes Motiv in der Bibliothek und
  sofort in der Vorlage.
- Bildquellen: Ollama auf dem Mac (kostenlos, z. B. x/z-image-turbo) oder OpenRouter mit eigenem
  Schlüssel. Für OpenRouter gibt es eine Empfehlungsliste für Lasermotive mit den geschätzten Kosten
  je Bild und den Kosten dieses Monats. Ein Monatslimit lässt sich setzen.
- Der OpenRouter-Schlüssel liegt im Schlüsselbund. An OpenRouter geht nur die Beschreibung.
- Englische Oberfläche: Platzhaltertexte in Eingabefeldern werden jetzt auch übersetzt.

## 2.2.1 – 2026-10-11

- Zwei neue Materialprofile für feine Arbeiten: Pappel-Sperrholz 1,5 mm und 2 mm (Filigran), passend
  zu den Paketen Filigran und Mehrlagig.

## 2.2.0 – 2026-10-11

- Materialprofile für den xTool M2 (10 W und 20 W): Pappel, Linde und Birke 3 mm, Pappel 4 mm, MDF 3 mm,
  Graupappe 2 mm und Acryl schwarz 3 mm. Ein Profil stellt Materialstärke und Kerf ein und färbt die SVG
  für xTool Creative Space: Rot = Schneiden, Blau = Ritzen.
- Zu jedem Profil zeigt Steckwerk Startwerte für XCS (Leistung, Tempo, Durchgänge), auch im Export-Fenster.
- Eigene Profile: aktuelle Werte unter einem Namen sichern und die Laserwerte selbst eintragen.
- Das Material-Menü oben wechselt direkt zwischen den Profilen.

## 2.1.0 – 2026-10-10

- Neue Oberfläche im Mac-Stil, übersichtlicher und aufgeräumt: links eine Seitenleiste mit allen
  Modellen nach Gruppen, oben eine Werkzeugleiste mit Status, Material-Menü, Würfel und **Exportieren…**,
  in der Mitte nur die Platte und rechts der Inspektor mit den Werten des gewählten Modells
  (Größe, Ausstattung mit Schaltern, Motive, Gestaltung zum Aufklappen).
- Prüfbericht und Zusammenbau öffnen sich per Klick auf den Status, der Export als eigenes Fenster
  (ZIP, einzelne Platte als SVG oder in den Steckwerk-Ordner).
- Material, Pakete, Motive, Updates, Sprache, hell/dunkel und Live-Vorschau liegen jetzt im
  Einstellungsfenster (⌘,).
- Tastatur: ⌘, Einstellungen, ⌘E Exportieren, ⌘↩ Vorschau, Esc schließt.
- Systemschrift statt Webschriften – die Oberfläche lädt nichts mehr aus dem Internet.

## 2.0.0 – 2026-10-10

- Neuer Name: Aus Laserforge wird **Steckwerk**. Beim ersten Start übernimmt Steckwerk Pakete, Motive,
  Einstellungen und den Update-Schlüssel automatisch, die alte App im Programme-Ordner wird ersetzt.
- Pakete heißen jetzt `.swpaket`; ältere `.lfpaket`-Dateien und Pakete mit `from laserforge import …`
  funktionieren weiter.
- Deutsch und Englisch: oben rechts die Sprache wählen. Formular, Prüfbericht, Montagehinweise,
  Fehlermeldungen und Update-Hinweise erscheinen dann auf Englisch, die Mac-Dialoge folgen der
  Systemsprache. Eine englische Beschreibung liegt in README.en.md.
- Pakete können englische Texte mitbringen (`UEBERSETZUNG`, siehe PAKETE.md); das Halloween-Paket 1.1.0
  ist komplett zweisprachig.

> Bis Version 1.7.0 hieß das Programm Laserforge.

## 1.7.0 – 2026-10-10

- Updates direkt in Steckwerk: Der neue Bereich „Updates“ zeigt neue Programmversionen und Pakete
  aus dem Update-Kanal. Pakete installierst oder aktualisierst du mit einem Klick, die Mac-App ersetzt
  sich selbst durch die neue Version und startet neu.
- Beim Start prüft Steckwerk automatisch (abschaltbar); gibt es Neues, erscheint oben „Updates“ mit Anzahl.
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

- Mac-App: Startet man Steckwerk direkt aus „Downloads“, zeigte das Fenster nach kurzer Zeit nur
  noch einen Fehler, weil macOS die temporäre Kopie der App entfernt hatte. Steckwerk läuft in
  diesem Fall jetzt im Vordergrund weiter und bietet die Installation erneut an.
- Eine laufende Steckwerk, die ihre Dateien nicht mehr findet, wird beim nächsten Start
  automatisch beendet und neu gestartet.

## 1.5.0 – 2026-10-09

- Neue Fahrzeuge: Tender, Personenwagen, Güterwagen, Bus und Traktor (große Hinterräder).
- Modell „Zug-Set“: Lok, Tender und bis zu 6 Wagen im Maßstab der Lok, Aufschrift je Fahrzeug.
- Kupplungslöcher in Front und Heck von Lok, Tender und Wagen (`kupplung`).
- Erweiterungspakete (`.swpaket`, Standard 1): laden in der App und per `--paket-installieren`,
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
