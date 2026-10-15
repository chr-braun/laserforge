# Pakete

Mit Paketen kommen neue Modelle in Steckwerk, ohne die App neu zu installieren. Ein Paket ist eine
**`.swpaket`**-Datei (ein ZIP mit Ordner). Ältere `.lfpaket`-Dateien aus Laserforge-Zeiten funktionieren
weiter. Die vollständige Spezifikation steht in [PAKETE.md](https://github.com/chr-braun/steckwerk/blob/main/PAKETE.md) im Repo.

## Laden

- In der App: Einstellungen → **Pakete** → **Paket laden …**, oder bequem über [Updates](Updates.md).
- Kommandozeile: `python3 cli.py --paket-installieren datei.swpaket`, `--pakete`, `--paket-entfernen ID`.

Beim Installieren wird jedes Modell mit Standardwerten gebaut und geprüft. Nur ein komplett
schnittfertiges Paket wird übernommen.

> Pakete enthalten Python-Code, der mit deinen Rechten läuft. Lade nur Pakete aus Quellen, denen du
> vertraust.

## Unsere Pakete

| Paket (ID) | Version | Was drin ist |
|---|---|---|
| **Mehrlagig** (`ebenen`) | 1.2.0 | **Ebenenbild**: Schattenbox mit 3–6 Lagen, Szenen Winterwald, Winterdorf, Spukschloss, Weihnachtsnacht; als Sockel- oder Stapelversion. **Ebenenmotiv**: Motiv aus drei Lagen mit Steckstiften, Öse oder Standfuß. **Aufsteckdeko**: 12 Motive als Kantenreiter, Zapfen, Öse oder Spieß. Seit 1.1.0 auch Weihnachtsmann, Pick-up mit Baum und Nussknacker. |
| **Filigran** (`filigran`) | 1.1.0 | **Spitzenschmuck** (Formen × Spitzenmuster, optional 3D gesteckt; seit 1.1.0 mit eigenen **Muster-Rezepten** aus Bausteinen und **Zufallsmustern** per Startwert), **Medaillon** (Scherenschnitt-Szenen im Rahmen), **Kristallflocke** (jeder Seed eine andere Flocke). Am besten mit den Filigran-Profilen 1,5 / 2 mm. |
| **Weihnachtsdeko** (`weihnacht`) | 1.1.0 | Zierschlitten mit Schnörkelkufen, Steckkrippe (27 Teile, Stall und Figuren), Familienanhänger, Weihnachtsanhänger. |
| **Halloween** (`halloween`) | 1.3.0 | Spukschloss im gotischen Bogen, Kürbislaterne, Grabstein mit Gespenst, Anhänger-Set; seit 1.2.0 Spinnennetz, Skelett (Hampelmann), Fledermausgirlande, Süßigkeitenschale. Komplett zweisprachig. |
| **Türschild** (`tuerschild`) | 1.1.0 | Hängeschild mit Namen und Rahmen – das Beispiel für den Paket-Standard. |
| **Verzierungen** (`verzierungen`) | 1.1.0 | Die gemeinsame **Ornament-Bibliothek** für alle Pakete: Rosetten (Blüte, Mandala, Stern, Sonne, Schneestern), Eckornamente, Bordüren, Kanten, Durchbrüche, Ausschnittmotive (Herz, Stern, Tanne, Blume, Mond, Pilz …), Rahmenformen. Dazu die Modelle **Zierstück** und **Zierleiste**. Seit 1.1.0 auch die Motiv-Figuren und Halloween-Formen. Wird von Mehrlagig, Filigran, Weihnachtsdeko, Halloween und den Paketen unten automatisch mitinstalliert. |
| **Umrandungen** (`umrandungen`) | 1.0.0 | **Bilderrahmen** (9 × 13 bis 15 × 20 cm oder eigenes Maß, schlicht oder filigran, mit Sockel oder Schlüsselloch) und **Zierrahmen** mit Schild und graviertem Text. Braucht Verzierungen. |
| **Wichtelmöbel** (`wichtelmoebel`) | 1.0.0 | **Wichtelbank** mit Lehne, **Wichteltisch** mit bis zu vier Hockern, **Wichtelbett** mit graviertem Kissen und Decke – alles gesteckt. Braucht Verzierungen. |
| **Wichteltür** (`wichteltuer`) | 1.0.0 | **Wichteltür** mit Steinbogen oder Holzrahmen, Türfenster, Stufe und Namensschild, **Wichtelfenster** mit Sprossen, Gardinen, Fensterläden und Blumenkasten. Braucht Verzierungen. |
| **Wichtelzubehör** (`wichtelzubehoer`) | 1.0.0 | **Wichtelleiter** zum Stecken, **Wegweiser** mit eigenen Ortsnamen, **Wäscheleine** mit Mini-Wäsche. Braucht Verzierungen. |

Alle Paketdateien zum Herunterladen findest du unter [Downloads](Downloads.md). Jedes `.swpaket`
enthält den kompletten Quellcode – zum Ändern einfach entpacken.

## Vorschau

![Mehrlagig 1.0](medien/mehrlagig-1.0.png)

![Mehrlagig 1.1 – neue Motive](medien/mehrlagig-1.1-neu.png)

![Filigran](medien/filigran-vorschau.png)

![Filigran 1.1: Muster-Rezepte und Zufallsmuster](medien/filigran-1.1-rezepte.png)

![Weihnachtsdeko: Krippe und Schlitten](medien/weihnachtsdeko-krippe-schlitten.png)

![Weihnachtsdeko: Anhänger](medien/weihnachtsdeko-anhaenger.png)

![Halloween 1.2](medien/halloween-1.2-vorschau-1.png)

![Halloween 1.2](medien/halloween-1.2-vorschau-2.png)

![Verzierungen 1.0](medien/verzierungen-1.0-vorschau.png)

![Umrandungen 1.0](medien/umrandungen-1.0-vorschau.png)

![Wichtelmöbel 1.0](medien/wichtelmoebel-1.0-vorschau.png)

![Wichteltür 1.0](medien/wichteltuer-1.0-vorschau.png)

![Wichtelzubehör 1.0](medien/wichtelzubehoer-1.0-vorschau.png)

## Eigenes Paket bauen

```bash
python3 cli.py --paket-neu krippe --out meine-pakete        # Vorlage mit Beispielmodell
python3 cli.py --paket-pruefen meine-pakete/krippe          # bauen + prüfen
python3 cli.py --paket-packen meine-pakete/krippe --out .   # → krippe-1.0.0.swpaket
```

Ein Paket besteht aus `paket.json` (id, name, version, modelle, optional `steckwerk`-Mindestversion,
`name_en`/`beschreibung_en`) und je Modell einer Python-Datei mit `INFO` (Formular) und `build(cfg, …)`.
Englische Texte kommen über ein `UEBERSETZUNG`-Wörterbuch. Seit 2.4.0 kann ein Paket andere Pakete
nutzen: `"benoetigt": {"verzierungen": "1.0.0"}` in der `paket.json`, dann im Code
`Z = pakete.bibliothek("verzierungen")` – so stehen alle Ornamente und Steck-Werkzeuge zur Verfügung. Bei jeder Änderung die Version erhöhen und
über den [Update-Kanal](Updates.md) veröffentlichen.

## Was wir beim Bauen gelernt haben

Die aufwendigen Pakete (Mehrlagig, Filigran, Weihnachtsdeko, Halloween) zeichnen Figuren als Plus/Minus-
Formen, rastern sie und machen daraus wieder saubere, laserfeste Konturen. Stolperfallen dabei:

- Ein Schnittschlitz über die ganze Breite teilt das Teil, und das kleinere Stück verschwindet still.
- Sehr dünne Überlappungen (unter ca. 1,3 mm) werden aufgemacht.
- Große Ebenenbilder (ca. 300 mm) brauchen etwa eine Minute zum Rechnen.
- Der Engel wirkt in kleinen Größen schwächer.
