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
| **Mehrlagig** (`ebenen`) | 1.1.0 | **Ebenenbild**: Schattenbox mit 3–6 Lagen, Szenen Winterwald, Winterdorf, Spukschloss, Weihnachtsnacht; als Sockel- oder Stapelversion. **Ebenenmotiv**: Motiv aus drei Lagen mit Steckstiften, Öse oder Standfuß. **Aufsteckdeko**: 12 Motive als Kantenreiter, Zapfen, Öse oder Spieß. Seit 1.1.0 auch Weihnachtsmann, Pick-up mit Baum und Nussknacker. |
| **Filigran** (`filigran`) | 1.0.0 | **Spitzenschmuck** (Formen × Spitzenmuster, optional 3D gesteckt), **Medaillon** (Scherenschnitt-Szenen im Rahmen), **Kristallflocke** (jeder Seed eine andere Flocke). Am besten mit den Filigran-Profilen 1,5 / 2 mm. |
| **Weihnachtsdeko** (`weihnacht`) | 1.0.0 | Zierschlitten mit Schnörkelkufen, Steckkrippe (27 Teile, Stall und Figuren), Familienanhänger, Weihnachtsanhänger. |
| **Halloween** (`halloween`) | 1.2.0 | Spukschloss im gotischen Bogen, Kürbislaterne, Grabstein mit Gespenst, Anhänger-Set; seit 1.2.0 Spinnennetz, Skelett (Hampelmann), Fledermausgirlande, Süßigkeitenschale. Komplett zweisprachig. |
| **Türschild** (`tuerschild`) | 1.1.0 | Hängeschild mit Namen und Rahmen – das Beispiel für den Paket-Standard. |

Die Paketdateien und Vorschaubilder liegen im Projektordner unter `steckwerk/pakete/`. Jedes `.swpaket`
enthält den kompletten Quellcode – zum Ändern einfach entpacken.

## Eigenes Paket bauen

```bash
python3 cli.py --paket-neu krippe --out meine-pakete        # Vorlage mit Beispielmodell
python3 cli.py --paket-pruefen meine-pakete/krippe          # bauen + prüfen
python3 cli.py --paket-packen meine-pakete/krippe --out .   # → krippe-1.0.0.swpaket
```

Ein Paket besteht aus `paket.json` (id, name, version, modelle, optional `steckwerk`-Mindestversion,
`name_en`/`beschreibung_en`) und je Modell einer Python-Datei mit `INFO` (Formular) und `build(cfg, …)`.
Englische Texte kommen über ein `UEBERSETZUNG`-Wörterbuch. Bei jeder Änderung die Version erhöhen und
über den [Update-Kanal](Updates.md) veröffentlichen.

## Was wir beim Bauen gelernt haben

Die aufwendigen Pakete (Mehrlagig, Filigran, Weihnachtsdeko, Halloween) zeichnen Figuren als Plus/Minus-
Formen, rastern sie und machen daraus wieder saubere, laserfeste Konturen. Stolperfallen dabei:

- Ein Schnittschlitz über die ganze Breite teilt das Teil, und das kleinere Stück verschwindet still.
- Sehr dünne Überlappungen (unter ca. 1,3 mm) werden aufgemacht.
- Große Ebenenbilder (ca. 300 mm) brauchen etwa eine Minute zum Rechnen.
- Der Engel wirkt in kleinen Größen schwächer.
