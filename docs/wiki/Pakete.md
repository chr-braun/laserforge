# Pakete

Mit Paketen kommen neue Modelle in Steckwerk, ohne die App neu zu installieren. Ein Paket ist eine
**`.swpaket`**-Datei (ein ZIP mit Ordner). Ältere `.lfpaket`-Dateien aus Laserforge-Zeiten funktionieren
weiter. Die vollständige Spezifikation steht in [PAKETE.md](https://github.com/chr-braun/steckwerk/blob/main/PAKETE.md) im Repo.

## Laden

- In der App: Einstellungen → **Pakete**. Dort siehst du jedes installierte Paket mit Beschreibung und
  seinen Modellen, und darunter alles, was es im Update-Kanal noch gibt – mit **Installieren**-Knopf.
  Eigene Dateien gehen über **Paket laden …**.
- Kommandozeile: `python3 cli.py --paket-installieren datei.swpaket`, `--pakete`, `--paket-entfernen ID`.

![Einstellungen → Pakete: installierte Pakete und der Update-Kanal mit Installieren-Knopf](medien/steckwerk-2.6-paketkatalog.png)

Beim Installieren wird jedes Modell mit Standardwerten gebaut und geprüft. Nur ein komplett
schnittfertiges Paket wird übernommen. „Grundlagen“ kommt automatisch mit.

> Pakete enthalten Python-Code, der mit deinen Rechten läuft. Lade nur Pakete aus Quellen, denen du
> vertraust.

## Unsere Pakete

Seit Steckwerk 2.6.0 gibt es **ein Paket je Thema**, dazu kamen Formen, Schmuck, Verkauf und Bewegung. Alte Einzelpakete räumt Steckwerk beim Installieren
selbst weg (Spalte „ersetzt“). Seit 2.7.0 lädt Steckwerk die alten Einzelpakete gar nicht mehr: Unter
Einstellungen → Pakete steht bei jedem ⏸ und das Themenpaket, in dem es jetzt steckt, mit Knopf zum Installieren.
Danach verschwindet das alte Paket von selbst, oder du entfernst es direkt.

| Paket (ID) | Version | Was drin ist | ersetzt |
|---|---|---|---|
| **Grundlagen** (`verzierungen`) | 2.0.0 | Die Basis für alle anderen Pakete. **Zierstück** und **Zierleiste** mit Rosetten, Ecken, Ranken, Bordüren, Schleifen und Zweigen; **Passungstest**: Kamm mit Schlitzen in verschiedenen Breiten, unter dem Schlitz, in dem das Probestück satt sitzt, steht dein Kerf. Dazu die Ornament-Bibliothek, die alle Pakete nutzen. Kommt automatisch mit. | Verzierungen, Werkstatt |
| **Wohnen** (`wohnen`) | 1.0.0 | **Bilderrahmen** (9 × 13 bis 15 × 20 cm oder eigenes Maß, schlicht oder filigran, mit Sockel oder Schlüsselloch), **Zierrahmen** mit Schild und graviertem Text, **Türschild** mit Namen. | Umrandungen, Türschild |
| **Weihnachten** (`weihnacht`) | 2.0.0 | Zierschlitten mit Schnörkelkufen, Steckkrippe (Stall und Figuren), Familienanhänger, Weihnachtsanhänger, **Spitzenschmuck** (mit Muster-Rezepten und Zufallsmustern), **Scherenschnitt-Medaillon**, **Kristall-Schneeflocken**. Filigranes am besten mit den Profilen 1,5 / 2 mm. | Weihnachtsdeko, Filigran |
| **Halloween** (`halloween`) | 1.3.0 | Spukschloss im gotischen Bogen, Kürbislaterne, Grabstein mit Gespenst, Anhänger-Set, Spinnennetz, Skelett (Hampelmann), Fledermausgirlande, Süßigkeitenschale. | – |
| **Mehrlagig** (`ebenen`) | 1.2.0 | **Ebenenbild**: Schattenbox mit 3–6 Lagen (Winterwald, Winterdorf, Spukschloss, Weihnachtsnacht). **Ebenenmotiv**: Motiv aus drei Lagen mit Steckstiften. **Aufsteckdeko**: Motive als Kantenreiter, Zapfen, Öse oder Spieß. | – |
| **Wichtel** (`wichtel`) | 1.0.1 | **Figur:** Schicht-Wichtel aus vier Lagen zum Bemalen. **Haus:** Wichteltür, Wichtelfenster. **Möbel:** Bank, Tisch mit Hockern, Bett. **Zubehör:** Leiter, Wegweiser, Wäscheleine. **Wichtelzimmer** auf Knopfdruck. **Wichtelmarkt:** Lebkuchenstand, Kreidetafel, Backstube, Briefkasten, Gartenzaun, Werkbank, Wegelaterne. Alles im selben Wichtel-Maßstab. | Wichtelmöbel, Wichteltür, Wichtelzubehör, Wichtelwelt, Wichtelfiguren |
| **Formen** (`formen`) | 1.0.0 | Mathematische Steckskulpturen, jede Kurve exakt berechnet. **Steckkörper**: Kugel, Ei, Linse, Zwiebelturm, Kreisel, Tanne oder Kuppel aus zwei Scharen gekreuzter Rippen (Sliceform), Rippen graviert beschriftet (A1, B1 …), unten auf Wunsch abgeflacht. **Wellenfläche**: Gitter z = f(x, y) als Eierkarton-Welle, Sattel, Hügel, Ringwellen, Dünen, zwei Gipfel oder Kissen. **Stapelvase**: gedrehte Vase oder Windlicht aus gestapelten Lagen (Stern, Vieleck, Blüte, Zahnkranz, Wellenrand), mit Glaseinsatz oder Rundstab. Für 1,5–4 mm Sperrholz oder Graupappe, Stapelvase auch 3–5 mm Pappel. | – |
| **Schmuck** (`schmuck`) | 1.0.0 | **Ohrhänger** als gespiegeltes Paar, angelehnt an das, was auf Atomm für den xTool M2 beliebt ist. Zehn Motive: Lotusblüte, Flügel, Tropfen, Mond, Sonne, Wolke mit Regen, Raute, Waben, Regenbogen, Fächer. Drei Stile: durchbrochen, nur Rahmen oder graviert (zum Ausmalen). Öse für den Biegering, auf Wunsch ein Zwischenteil (Kreis, Stern, Tropfen, Mond). Zu knappe Durchbrüche lässt Steckwerk weg, damit jeder Steg hält. Für 1,5–3 mm Sperrholz, Acryl oder Leder; dazu Ohrhaken und Biegeringe. | – |
| **Verkauf** (`verkauf`) | 1.0.0 | Für Laden und Markt. **Flaschenschild**: Preisschild für den Flaschenhals (Halsloch Standard 33 mm, passt für Weinflaschen) oder an einer Kordel. Oben dein **Logo** aus „Motive importieren“ (flächig, als Umriss graviert oder ausgeschnitten) oder eine Kopfzeile, darunter Produktname (ein senkrechter Strich macht eine neue Zeile), **Preis inkl. MwSt.** und **Grundpreis je Liter**, den Steckwerk selbst ausrechnet (z. B. „0,75 l (17,20 €/l)“). Mit der **Preisliste** (`Name; Preis; Inhalt` je Zeile, Inhalt auch in ml) entstehen alle Schilder auf einmal. Braucht Steckwerk 2.8.0. Für 1,5–3 mm Sperrholz. | – |
| **Bewegung** (`bewegung`) | 1.0.0 | Spielzeug für Kinder, das sich bewegt, alles aus der Platte (auch Wellen und Spindeln). **Hampelmann**: Wichtel, Weihnachtsmann, Rentier, Schneemann oder Skelett, mit Zuggriff (Kugel, Stern, Herz) und gravierten Linien zum Ausmalen. **Kurbeltier**: Kurbelkiste mit 1–3 Tieren (Hase, Frosch, Dino, Küken), Nocken auf einer Vierkantwelle lassen sie hüpfen oder wippen, Fenster vorne und Platz für einen Namen. **Turner**: Akrobat (Affe, Bär, Wichtel) an verdrillter Schnur zwischen zwei Stäben. **Kreisel**: Scheibe mit Spirale, Farbkreis, Sternen oder Blume, auch als Paar. **Balancier-Vogel**: Steckwerk rechnet aus Holzart und Münze, wie viele Münzen unter die Flügel kommen; mit Ständer. Braucht Steckwerk 2.8.0 und Grundlagen. Für Kinderhände 3–4 mm Sperrholz, Kanten anschleifen; bei kleinen Kindern Holznieten statt Klammern, speichelfester Lack. | – |

Alle Paketdateien zum Herunterladen findest du unter [Downloads](Downloads.md). Jedes `.swpaket`
enthält den kompletten Quellcode – zum Ändern einfach entpacken.

## Vorschau

### Mehrlagig

![Mehrlagig 1.0](medien/mehrlagig-1.0.png)

![Mehrlagig 1.1 – neue Motive](medien/mehrlagig-1.1-neu.png)

### Weihnachten

![Weihnachten: Krippe und Schlitten](medien/weihnachtsdeko-krippe-schlitten.png)

![Weihnachten: Anhänger](medien/weihnachtsdeko-anhaenger.png)

![Weihnachten: Spitzenschmuck, Medaillon, Kristallflocke](medien/filigran-vorschau.png)

![Weihnachten: Muster-Rezepte und Zufallsmuster](medien/filigran-1.1-rezepte.png)

### Halloween

![Halloween 1.2](medien/halloween-1.2-vorschau-1.png)

![Halloween 1.2](medien/halloween-1.2-vorschau-2.png)

### Grundlagen

![Grundlagen: Zierstücke und Zierleisten](medien/verzierungen-1.0-vorschau.png)

![Grundlagen: Passungstest](medien/werkstatt-1.0-passungstest.png)

### Wohnen

![Wohnen: Bilderrahmen und Zierrahmen](medien/umrandungen-1.0-vorschau.png)

### Wichtel

![Wichtel: Möbel](medien/wichtelmoebel-1.0-vorschau.png)

![Wichtel: Tür](medien/wichteltuer-1.0-vorschau.png)

![Wichtel: Zubehör](medien/wichtelzubehoer-1.0-vorschau.png)

![Wichtel: Schicht-Wichtel bemalt, vier Varianten](medien/wichtelfiguren-1.0-bemalt.png)

![Wichtel: Schicht-Wichtel, die Teile zum Lasern](medien/wichtelfiguren-1.0-teile.png)

![Wichtel: Wichtelzimmer mit Schicht-Wichtel](medien/wichtelwelt-1.1-zimmer.png)

![Wichtelmarkt: Lebkuchenstand mit Ware](medien/wichtel-1.0-lebkuchenstand.png)

![Wichtelmarkt: Backstube](medien/wichtel-1.0-backstube.png)

![Wichtelmarkt: Werkbank mit Werkzeug](medien/wichtel-1.0-werkbank.png)

![Wichtelmarkt: Wegelaterne, Kreidetafel, Briefkasten, Gartenzaun](medien/wichtel-1.0-markt.png)

### Formen

![Formen: Steckkörper Kugel](medien/formen-1.0-steckkoerper_kugel_7_3d.png)

![Formen: Steckkörper Zwiebelturm](medien/formen-1.0-steckkoerper_zwiebel_7_3d.png)

![Formen: Steckkörper Tanne](medien/formen-1.0-steckkoerper_tanne_7_3d.png)

![Formen: Wellenfläche](medien/formen-1.0-wellenflaeche_welle_3d.png)

![Formen: Stapelvasen](medien/formen-1.0-vasen.png)

### Schmuck

![Schmuck: Ohrhänger durchbrochen](medien/schmuck-1.0-durchbrochen.png)

![Schmuck: Ohrhänger nur Rahmen](medien/schmuck-1.0-rahmen.png)

![Schmuck: Ohrhänger graviert](medien/schmuck-1.0-graviert.png)

### Verkauf

![Verkauf: Flaschenschilder mit Logo, Preis und Grundpreis](medien/verkauf-1.0-flaschenschild.png)

Beispiel für die Preisliste:

```
Grauburgunder 2023; 14,50; 0,75
Winzersekt brut; 11,90; 0,75
Tresterbrand; 24,90; 0,5
```

### Bewegung

![Bewegung: Hampelmänner](medien/bewegung-1.0-hampelmann.png)

![Bewegung: Kurbeltier](medien/bewegung-1.0-kurbeltier.png)

![Bewegung: Turner, Kreisel und Balancier-Vogel](medien/bewegung-1.0-turner-kreisel-vogel.png)

### Wichtel-Maßstab

Jedes Wichtel-Modell hat oben die Auswahl **Maßstab**. Bei „passend zur Wichtelgröße“ gibst du nur die
Höhe deiner Wichtelfigur an (Standard 70 mm, wie die Wichtelfigur in Steckwerk), und alle Maße richten sich
danach. So passen Tür, Möbel und Zubehör zusammen. Bei „eigene Maße“ stellst du alles selbst ein.
Dickeres Holz braucht größere Wichtel: Bei 4 mm ab etwa 60 mm, bei 5 mm ab etwa 75 mm. Steckwerk sagt dir
die genaue Grenze.

## Eigenes Paket bauen

```bash
python3 cli.py --paket-neu krippe --out meine-pakete        # Vorlage mit Beispielmodell
python3 cli.py --paket-pruefen meine-pakete/krippe          # bauen + prüfen
python3 cli.py --paket-packen meine-pakete/krippe --out .   # → krippe-1.0.0.swpaket
```

Ein Paket besteht aus `paket.json` (id, name, version, modelle, optional `steckwerk`-Mindestversion,
`name_en`/`beschreibung_en`) und je Modell einer Python-Datei mit `INFO` (Formular) und `build(cfg, …)`.
Englische Texte kommen über ein `UEBERSETZUNG`-Wörterbuch. Seit 2.8.0 wird ein Textfeld mit `"rows": N` in der Oberfläche mehrzeilig (z. B. für eine Preisliste). Seit 2.5.0 kann ein Paket alte Pakete
ablösen: `"ersetzt": ["altes_paket"]` räumt sie beim Installieren weg. Seit 2.4.0 kann ein Paket andere Pakete
nutzen: `"benoetigt": {"verzierungen": "1.0.0"}` in der `paket.json`, dann im Code
`Z = pakete.bibliothek("verzierungen")` – so stehen alle Ornamente und Steck-Werkzeuge zur Verfügung. Bei jeder Änderung die Version erhöhen und
über den [Update-Kanal](Updates.md) veröffentlichen.

## Was wir beim Bauen gelernt haben

Die aufwendigen Pakete (Mehrlagig, Weihnachten, Halloween) zeichnen Figuren als Plus/Minus-
Formen, rastern sie und machen daraus wieder saubere, laserfeste Konturen. Stolperfallen dabei:

- Ein Schnittschlitz über die ganze Breite teilt das Teil, und das kleinere Stück verschwindet still.
- Sehr dünne Überlappungen (unter ca. 1,3 mm) werden aufgemacht.
- Große Ebenenbilder (ca. 300 mm) brauchen etwa eine Minute zum Rechnen.
- Der Engel wirkt in kleinen Größen schwächer.
