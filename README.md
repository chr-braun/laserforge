# Laserforge

[![Tests](https://github.com/chr-braun/laserforge/actions/workflows/ci.yml/badge.svg)](https://github.com/chr-braun/laserforge/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/chr-braun/laserforge?label=Mac-App)](https://github.com/chr-braun/laserforge/releases/latest)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
[![Lizenz: MIT](https://img.shields.io/badge/Lizenz-MIT-green)](LICENSE)

Parametrische, **validierte** Lasercut-SVGs für Wichtelhäuser, Weihnachtszubehör, ganze
zusammengehörige Serien, Christbaumschmuck, Schwibbögen, Schneeflocken und Steckfahrzeuge mit drehenden
Rädern – erweiterbar über eigene [Pakete](PAKETE.md).
Cut-ready für CO2- und Diodenlaser (LightBurn, xTool Creative Space, Glowforge).

Neu in 1.2: viele **Gravuren und Beschriftungen** – Fensterformen mit Läden, Blumenkästen und
Schneehauben, Türschmuck, Wand- und Dachgravuren (Fachwerk, Ziegel, Schindeln …), Zierleisten
(Eiszapfen, Lichterkette, Zuckerguss …), Schilder mit Rahmen, sechs Schriftstile mit Groß- und
Kleinbuchstaben und Symbolen ♥ ★ ❄ 🎄 – für Häuser, Serien, Schmuck, Fahrzeuge, Briefkasten und
Figuren. Alles ist auswählbar und wird wie gewohnt vor dem Schreiben geprüft
(siehe [Gestaltung und Beschriftung](#gestaltung-und-beschriftung)).

- Als **Mac-App** zum Doppelklicken (`Laserforge-1.5.1-macOS.zip` unter
  [Releases](https://github.com/chr-braun/laserforge/releases/latest)), als **Weboberfläche** im Browser
  (`python3 webui.py`), als Frage-Antwort-**Konfigurator** im Terminal (`python3 cli.py --konfigurator`)
  oder klassisch per **Kommandozeile**.
- Reines Python (3.8+), nur Standardbibliothek. Kein CAD, keine Cloud – auch die Weboberfläche läuft
  komplett lokal auf deinem Rechner.
- Optional: `PyYAML` (YAML-Configs mit Listen/Verschachtelung, sonst eingebauter Mini-Parser),
  `matplotlib` oder `Pillow` (PNG-Vorschau), `pytest` (Tests).
- Jede Datei wird **vor dem Schreiben** geprüft. Bei einem einzigen Fehler wird gar nichts geschrieben
  (und in der Weboberfläche gibt es keinen Download).

---

## Mac-App

Die einfachste Art, Laserforge zu benutzen – ohne Terminal.

1. `Laserforge-1.5.1-macOS.zip` per Doppelklick entpacken, dann **Laserforge** doppelklicken.
2. **Nur beim allerersten Start:** macOS blockiert Apps, die nicht aus dem App Store kommen
   („Laserforge“ kann nicht geöffnet werden …). Mit *Fertig* schließen, dann
   **Systemeinstellungen → Datenschutz & Sicherheit** → ganz unten bei „Laserforge wurde blockiert“
   auf **Dennoch öffnen** klicken und bestätigen. (Bis macOS 14: Rechtsklick auf die App → *Öffnen*.)
3. Laserforge fragt, ob es sich in den **Programme-Ordner installieren** soll → *Installieren*.
   Ab dann startest du es über Launchpad, Spotlight oder das Dock; die entpackte Kopie kannst du löschen.

Laserforge öffnet sich in deinem Standardbrowser (meist Safari) als Werkbank, genau wie unten unter
*Weboberfläche* beschrieben. Zusätzlich oben rechts: **Ordner öffnen** (zeigt `Dokumente/Laserforge`,
wohin *In Ordner speichern* schreibt) und **Beenden**. Schließt du das Fenster, beendet sich
Laserforge nach ein paar Sekunden von selbst; ein zweiter Doppelklick bei laufender App öffnet nur
ein neues Fenster.

**Python:** Die App nutzt das Python 3 deines Macs (ab 3.8 – Apples *Command Line Tools*, python.org
oder Homebrew). Fehlt es, bietet sie an, die Command Line Tools zu installieren; danach noch einmal
öffnen.

**Updates:** neue Version entpacken, öffnen, *Installieren* – die alte wird ersetzt, deine Dateien und
Einstellungen bleiben.

**Deinstallieren:** Laserforge aus dem Programme-Ordner in den Papierkorb ziehen. Einstellungen liegen in
`~/Library/Application Support/Laserforge`, das Protokoll in `~/Library/Logs/Laserforge.log`.

**Selbst bauen** (z. B. nach eigenen Änderungen am Code; läuft auf jedem System):

```bash
python3 packaging/build_macos.py        # → dist/Laserforge.app und dist/Laserforge-<version>-macOS.zip
python3 packaging/make_icon.py          # nur für ein neues Symbol (braucht Pillow)
```

Die Kommandozeile steckt auch in der App:
`python3 /Applications/Laserforge.app/Contents/Resources/laserforge/cli.py --help`

## Setup

```bash
cd laserforge
python3 webui.py                                       # Weboberfläche – keine Installation nötig
python3 cli.py --model wichtelhaus --out out           # oder direkt per Kommandozeile

# optional
python3 -m pip install matplotlib pytest pyyaml        # PNG-Vorschau, Tests, YAML-Komfort
```

Alle Befehle werden **im Ordner `laserforge/`** ausgeführt.

## Weboberfläche

```bash
python3 webui.py                    # startet http://127.0.0.1:8765 und öffnet den Browser
python3 webui.py --port 9000        # anderer Port, falls 8765 belegt ist
python3 webui.py --lan              # im Heimnetz erreichbar, z. B. vom Tablet am Laser
python3 webui.py --out ~/laser      # Ordner für „In Ordner speichern“ (Default ./out)
```

Beenden mit `Strg+C`. Die Seite (`web/index.html`) braucht kein Internet; nur die Schriften kommen
von Google Fonts und fallen offline auf Systemschriften zurück.

- **Links:** Modell wählen (Wichtelhaus, Serie, Zubehör, Christbaumschmuck, Schneeflocken,
  Steckfahrzeug, „Alle Modelle“), darunter die passenden Parameter. Unter **Material & Laser**:
  Materialstärke, Kerf, Maßstab, Fenster schneiden/gravieren, Blattgröße, Layerfarben.
- **Gestaltung:** Bei Haus, Serie, Schmuck, Fahrzeug, Briefkasten und Figuren stehen unter den Maßen
  aufklappbare Gruppen (*Fenster und Tür*, *Wände, Dach und Garten*, *Beschriftung* …); die Kopfzeile
  zeigt, wie viele Optionen du geändert hast. *Gestaltung würfeln* wählt alles zufällig – gut zum
  Ideensammeln. Bei Textfeldern fügen die kleinen Knöpfe ♥ ★ ❄ 🎄 die Symbole ein, `|` eine neue Zeile.
- **Live** an: jede Änderung rechnet nach einer halben Sekunde neu. Aus: mit *Erzeugen* oder
  `Strg+Enter`.
- **Rechts:** maßstäbliche Vorschau je Blatt mit mm-Lineal (Holz = Material, schwarz = Schnitt,
  blau = Gravur; Teilname per Maus-Hover), darunter Hinweise zum Zusammenbau und der komplette
  Prüfbericht (Filter „nur Fehler“).
- **Status:** grün *CUT-READY* → *SVG laden*, *Alles als ZIP* (SVGs + Prüfberichte) und
  *In Ordner speichern* sind aktiv. Rot *Fehler – keine Datei* → die Fehler stehen oben in Klartext,
  Downloads sind gesperrt. *Eingabe prüfen* → ein Wert liegt außerhalb des erlaubten Bereichs.
- Die letzte Einstellung merkt sich der Browser.

`--lan` macht die Oberfläche für alle Geräte in deinem Netz erreichbar (ohne Passwort) – nur im
eigenen Heimnetz verwenden.

## Konfigurator im Terminal

```bash
python3 cli.py --konfigurator
```

Fragt Modell, Maße, Optionen, Material und Ausgabeordner Schritt für Schritt ab (Enter = Vorschlag
übernehmen) und zeigt am Ende den gleichwertigen Kommandozeilen-Befehl zum Wiederverwenden.
Die Frage „Gestaltung und Beschriftung anpassen?“ öffnet die Gestaltungsoptionen; mit Enter bleibt
alles beim Standard.

## Schnellstart Kommandozeile

```bash
python3 cli.py --model wichtelhaus --preview --out out
```

Ergebnis in `out/wichtelhaus/`:

| Datei | Inhalt |
|---|---|
| `wichtelhaus.svg` | Schnittdatei, echte mm-Maße, Layer Schnitt (schwarz) + Gravur (blau) |
| `wichtelhaus.png` | Vorschau (Holz hellbraun, Schnitt schwarz, Gravur blau) |
| `pruefbericht.txt` | kompletter Validator-Report, alle Parameter, Montagehinweise |

Passen die Teile nicht auf ein Blatt, entstehen `…_blatt1.svg`, `…_blatt2.svg` usw.

## Alle Beispiele

```bash
# Wichtelhaus mit Standardmaßen (80 × 70 mm Grundfläche, 65 mm Traufhöhe, 45° Dach)
python3 cli.py --model wichtelhaus --out out

# 4 mm Pappel-Sperrholz, Diodenlaser mit 0.15 mm Kerf, größeres Haus mit steilem Dach
python3 cli.py --model wichtelhaus --thickness 4 --kerf 0.15 --width 100 --depth 85 --height 80 --pitch 55

# Fenster und Tür nur gravieren statt ausschneiden, ohne Kamin, mit Anbau
python3 cli.py --model wichtelhaus --openings engrave --no-chimney --annex

# eckige Tür, 2 Fenster vorne, 3 je Seite, ohne Licht-Durchbruch hinten
python3 cli.py --model wichtelhaus --door rect --front-windows 2 --side-windows 3 --no-light

# Serie: 5 Häuser mit variierender Architektur, reproduzierbar über den Seed
python3 cli.py --model wichtelhaus --series 5 --seed 42 --out out/serie
python3 cli.py --model serie --series 3 --preview --out out        # gleichwertig

# Zubehör einzeln
python3 cli.py --model tannenbaum --height 140 --tiers 5
python3 cli.py --model schneemann --height 70
python3 cli.py --model zaun --width 200 --height 50
python3 cli.py --model laterne --width 60 --height 90
python3 cli.py --model briefkasten --pitch 30
python3 cli.py --model wichtel --height 80

# alles Zubehör auf einmal, 80 % Größe
python3 cli.py --model zubehoer --scale 0.8 --preview

# Christbaumschmuck: Herzen mit Namen (Komma = je Name ein Anhänger, | = neue Zeile)
python3 cli.py --model ornament --shape herz --pattern punkte --text "Anna|2026,Ben|2026,Lea|2026"

# 4 filigrane Kugeln, je zwei Hälften zum Zusammenstecken (3D)
python3 cli.py --model ornament --shape kugel --pattern filigran --3d --count 4

# Schneeflocken: 8 verschiedene mit 90 mm, Seed bestimmt die Form
python3 cli.py --model schneeflocke --count 8 --size 90 --seed 3
python3 cli.py --model schneeflocke --size 120 --3d                # 3D gesteckt

# Gestaltung: jede Option per -O NAME=WERT (Liste je Modell: --options)
python3 cli.py --model wichtelhaus --options
python3 cli.py --model wichtelhaus -O fenster=herz -O fenster_deko=herzlaeden -O wand=fachwerk \
    -O zierleiste=eiszapfen -O schild="Villa Wichtel" -O schild_form=banner -O vorplatz=alles
python3 cli.py --model serie -n 4 -O schild="Anna, Ben, Lea, Tom" -O dach=schnee   # Rest je Haus gewürfelt
python3 cli.py --model ornament --shape kugel --pattern tannen --text "Mia" -O rand_stil=lichterkette -O textrahmen=holz
python3 cli.py --model fahrzeug --vehicle lok --text "Polarexpress" -O textrahmen=banner -O zierlinie=sterne
python3 cli.py --model briefkasten -O text="Fam. Huber" -O schild_form=geschweift -O dach=schnee
python3 cli.py --model schneemann -O text="Frosty ❄" -O schrift=kursiv

# Steckfahrzeuge
python3 cli.py --model fahrzeug --vehicle auto
python3 cli.py --model fahrzeug --vehicle lkw --axles 3 --length 180
python3 cli.py --model fahrzeug --vehicle lok --length 180 --text "Polarexpress"
python3 cli.py --model fahrzeug --vehicle schlitten --width 70

# wirklich alles: Haus, Zubehör, 3er-Serie, Schmuck, Flocken, alle vier Fahrzeuge
python3 cli.py --model alle --preview --out out

# eigene Config (YAML oder JSON), CLI-Werte überschreiben sie
python3 cli.py --config laserforge.yaml --model alle

# kleineres Laserbett (z. B. xTool M1: 385 × 300)
python3 cli.py --model wichtelhaus --sheet 385x300

# nur prüfen, nichts schreiben
python3 cli.py --model alle --validate

# fertige (auch nachträglich bearbeitete) SVGs prüfen
python3 cli.py --check-svg out/wichtelhaus/wichtelhaus.svg
```

Exit-Code `0` = alles cut-ready, `2` = Fehler (nichts geschrieben).

Fertige Beispiele (SVG, PNG-Vorschau, Prüfbericht) liegen in `examples/` – Übersicht aller Modelle in
`examples/uebersicht.png`, Gestaltungsbeispiele in `examples/gestaltung.png` und den Ordnern
`*_gestaltet`, `*_mit_namen`, `*_mit_rahmen`. Die neuen Schmuckformen zeigt `examples/neue_formen.png`.

### Alle Optionen

| Option | Bedeutung | Default |
|---|---|---|
| `--model`, `-m` | `wichtelhaus` `serie` `tannenbaum` `schneemann` `wichtel` `zaun` `laterne` `briefkasten` `zubehoer` `ornament` `schneeflocke` `fahrzeug` `alle` | `wichtelhaus` |
| `--konfigurator` | interaktiv im Terminal abfragen | – |
| `--thickness`, `-t` | Materialstärke T in mm | 3.0 |
| `--kerf`, `-k` | Schnittbreite in mm | 0.2 |
| `--scale` | Maßstab der Modelle (T bleibt gleich) | 1.0 |
| `--width` / `--height` / `--depth` | Hauptmaße in mm (je Modell, siehe unten) | modellabhängig |
| `--length` | Länge Fahrzeug in mm | je Fahrzeug |
| `--size` | Ornament: Höhe, Schneeflocke: Durchmesser (mm) | 70 / 80 |
| `--pitch` | Dachneigung in Grad (15–65) | 45 (Briefkasten 35) |
| `--openings` | Fenster/Türen `cut` oder `engrave` | `cut` |
| `--door` | Tür `arched` (Rundbogen), `rect`, `spitzbogen`, `rund` (Hobbit), `none` | `arched` |
| `--front-windows`, `--side-windows` | Fenster vorne (0–4) / je Seite (0–3) | 2 / 1 |
| `--no-light`, `--no-chimney`, `--annex` | Wichtelhaus-Optionen | Licht + Kamin an, kein Anbau |
| `--series`, `-n` | Anzahl Varianten | 5 |
| `--seed` | Zufallsstartwert (Serie, Schmuck, Flocken) | 7 |
| `--tiers` | Etagen des Tannenbaums (2–8) | 4 |
| `--shape` | Ornament: `stern` `kugel` `herz` `glocke` `baum` `mond` `anhaenger` `lebkuchen` `stiefel` `zuckerstange` `geschenk` `kerze` `engel` `zapfen` `schneemann` `schneeflocke` | `stern` |
| `--pattern` | Ornament: `sterne` `punkte` `streifen` `flocken` `herzen` `tannen` `karo` `wellen` (Gravur), `filigran` (Durchbrüche), `keins` | `sterne` |
| `--text` | Ornament/Fahrzeug: Text; Komma = je Name ein Anhänger, `\|` = neue Zeile | – |
| `--hanger` | Ornament: `oese` (Öse oben) oder `loch` | `oese` |
| `--no-rand` | Ornament ohne gravierte Randlinie | Rand an |
| `--3d` | Ornament/Schneeflocke als zwei Hälften mit Kreuzschlitz | flach |
| `--count` | Anzahl Ornamente ohne Text (1–30) bzw. Schneeflocken (1–60) | 1 / 3 |
| `--vehicle` | `auto` `lkw` `lok` `schlitten` | `auto` |
| `--axles` | Lkw: 2 oder 3 Achsen | 2 |
| `--option`, `-O` | Gestaltungsoption `NAME=WERT`, mehrfach möglich (siehe unten) | – |
| `--options` | alle Optionen des gewählten Modells mit erlaubten Werten anzeigen | – |
| `--sheet` | Blattgröße `BxH` in mm | 400x300 |
| `--cut-color`, `--engrave-color` | Layerfarben `#RRGGBB` | `#000000`, `#0000FF` |
| `--config`, `-c` | YAML/JSON-Config | – |
| `--out`, `-o` | Ausgabeordner | `out` |
| `--validate` | nur prüfen | – |
| `--preview` | PNG je Blatt | – |
| `--check-svg DATEI…` | vorhandene SVGs prüfen | – |
| `--quiet`, `-q` | nur Zusammenfassung | – |

## Modelle

| Modell | Teile | Maße |
|---|---|---|
| **wichtelhaus** | Vorder-/Rückgiebel, 2 Seitenwände (Zinken), Sockel-Bodenplatte, 2 Dachplatten, Kamin, optional Anbau (eigener kleiner Kasten) | Breite (Giebelseite) 80, Traufhöhe 65, Tiefe 70 |
| **serie** | N Wichtelhäuser: Dachneigung 35–55°, Proportionen ±15 %, 0–2 Fenster vorne, 1–2 je Seite, Rund-/Rechtecktür, Kamin, Anbau | Basis = Wichtelhaus-Maße |
| **tannenbaum** | 2 Silhouetten mit Kreuzschlitz → freistehender 3D-Baum, gravierte Kugeln, Stern | Höhe 110, Breite 0.72 × Höhe |
| **schneemann** | Figur aus 3 Kreisen + Zylinder, ovaler Sockel | Höhe 60 |
| **zaun** | Staketenzaun-Feld (Riegelfelder als Innenschnitte), Steckleiste | Länge 120, Höhe 45 |
| **laterne** | 4 Wände mit Rundbogenfenstern, Boden, Deckel mit Lüftung, Tragebügel | Breite 50 (Tiefe = Breite), Höhe 70 |
| **briefkasten** | Kasten mit Satteldach + Briefschlitz, Pfosten, Fußplatte | 40 × 50 × 32, Pfosten 55 |
| **wichtel** | Figur mit Zipfelmütze, Bart, Füßen, ovaler Sockel | Höhe 70 |
| **ornament** | Christbaumschmuck-Konfigurator: 15 Formen × 10 Muster, 12 Randstile, Name/Jahr mit oder ohne Rahmen (Größe passt sich an), Öse oder Loch; flach oder 3D aus zwei gesteckten Hälften | Höhe 30–200, Default 70 |
| **schneeflocke** | sechszählige Flocken, jede aus ihrem Seed: Arme, Seitenäste, Spitzen, Mittelloch, Gravurlinien; Öse an einer Armspitze; optional 3D gesteckt | Ø 30–250, Default 80 (3D: bei 4 mm ab 38, bei 6 mm ab 58) |
| **schwibbogen** | Lichterbogen: Bogen mit 1–11 Kerzen, Scherenschnitt-Szene (Dorf, Wald, Kirche) mit ausgeschnittenen Fenstern, Zierlinie auf dem Bogen, Text auf der Sockelleiste; Bodenplatte mit 2 Schlitzen | Breite 120–600, Default 240 (Höhe ≈ 0.73 × Breite) |
| **zug** | Zug-Set: Lok + Tender + 0–6 Wagen (Personen-/Güterwagen oder abwechselnd) im Maßstab der Lok, Kupplungslöcher, Aufschrift je Fahrzeug mit Komma | Lok 150 lang, Rest wächst mit |
| **fahrzeug** | Steckfahrzeug: 2 gespiegelte Seitenwände, Querteile (Boden, Dach, Front, Heck …) mit Tabs, Vierkantachsen, Räder | Auto 120 × 60, Lkw 150 × 64 (2 oder 3 Achsen), Lok 150 × 60 (3 Achsen, Speichenräder, Schornstein), Schlitten 140 × 64 (Kufen, ohne Räder) |

Das Zubehör ist auf das Standard-Wichtelhaus abgestimmt (Traufhöhe 65 mm). Mit `--scale` wächst alles
gemeinsam, die Materialstärke bleibt dabei unverändert. Fahrzeuge sind mindestens 80 mm (Auto),
90 mm (Schlitten) bzw. 100 mm (Lkw, Lok) lang; die Breite darf höchstens 80 % der Länge sein.

## Neue Schmuckformen (ab 1.3.0)

![Neue Schmuckformen](examples/neue_formen.png)

`lebkuchen` (mit Gesicht und Knöpfen), `stiefel` (Nikolausstiefel mit Umschlag), `zuckerstange` (mit Ringeln,
ohne Text), `geschenk` (Schleife, Band ohne Text), `kerze` (mit Flamme), `engel` (Flügel mit Federn),
`zapfen` (Tannenzapfen mit Schuppen) und `schneemann` (Gesicht, Möhrennase). Alle kombinierbar mit Muster,
Randstil, Text und Rahmen; 3D-gesteckt gehen Lebkuchenmann, Engel, Zapfen und Schneemann.

## Schwibbogen (ab 1.4.0)

![Schwibbogen](examples/schwibbogen.png)

```
python3 cli.py --model schwibbogen -O szene=kirche -O kerzen=9 -O bogen_deko=herzen -O "text=Glück auf!"
```

Optionen: `szene` (`dorf` `wald` `kirche`), `kerzen` (1–11), `fenster` (ausschneiden an/aus),
`bogen_deko` (alle Randstile oder `keine`), `text`, `schrift`, `schreibweise`. Ab etwa 280 mm Breite
braucht es ein größeres Blatt (`--sheet`). Mit einer LED-Lichterkette hinter der Szene leuchten die Fenster.

## Zug-Set, Bus und Traktor (ab 1.5.0)

![Zug, Bus und Traktor](examples/zug_bus_traktor.png)

Neue Fahrzeuge: `tender`, `personenwagen`, `gueterwagen`, `bus`, `traktor` (große Hinterräder).
Lok, Tender und Wagen haben Kupplungslöcher in Front und Heck (`-O kupplung=false` schaltet sie ab).
Verbunden wird mit einer Draht- oder Schnurschlaufe. Das ganze Set auf einmal:

```
python3 cli.py --model zug -O wagen=3 -O "text=Polar,,Post,Nordpol"
```

## Erweiterungspakete (ab 1.5.0)

Neue Modelle lassen sich als **`.lfpaket`** nachladen: in der App unter „Erweiterungspakete →
Paket laden …“ oder mit `python3 cli.py --paket-installieren datei.lfpaket`. Eigene Pakete legst du
mit `--paket-neu`, `--paket-pruefen` und `--paket-packen` an. Den Standard und eine Anleitung findest du
in **[PAKETE.md](PAKETE.md)**, ein Beispiel in `beispiel-pakete/`.

## Gestaltung und Beschriftung

![Gestaltungsbeispiele](examples/gestaltung.png)

Alle Optionen gibt es in der Weboberfläche (aufklappbare Gruppen), im Konfigurator und per
`-O NAME=WERT`. `python3 cli.py --model <modell> --options` listet sie mit allen erlaubten Werten.
Was nicht passt, wird ausgelassen oder gemeldet – nie halb gezeichnet: Gravuren halten Abstand zu
Kanten, Durchbrüchen, Slots und zueinander, Schilder suchen sich die größte freie Fläche.

**Wichtelhaus und Serie**

| Option | Werte |
|---|---|
| `door` | `arched` Rundbogen, `rect`, `spitzbogen`, `rund` (Hobbit), `none` |
| `tuer_deko` | `rahmen`, `vordach`, `laternen`, `girlande`, `kranz` (Türkranz), `keine` |
| `fenster` | `rechteck`, `rund`, `bogen`, `spitzbogen`, `raute`, `herz`, `stern` |
| `sprossen` | `kreuz`, `senkrecht`, `waagrecht`, `keine` |
| `fenster_deko` | `rahmen` (Rahmen + Sims), `laeden`, `herzlaeden`, `blumen` (Blumenkasten), `beides`, `schnee` (Schneehaube), `keine` |
| `wand` | `keine`, `holz` (Bretter mit Astlöchern), `ziegel`, `stein` (Bruchstein), `fachwerk`, `schuppen`, `putz`, `sterne`, `herzen` |
| `dach` | `ziegel`, `biber`, `schindel`, `reet`, `schnee` (Schneekante), `sterne`, `keine` |
| `zierleiste` | Linie unter dem Dach und an der Traufe: `keine` oder ein Linienstil (s. u.) |
| `giebel` | `rundfenster`, `herz`, `stern`, `uhr`, `luke` (Heuluke), `text` (mit `giebel_text`), `keins` |
| `vorplatz` | `keiner`, `weg` (Steinweg), `matte` (Fußmatte, Text `matte_text`), `garten` (Tannen + Schnee), `alles` – die Bodenplatte wird dafür nach vorne verlängert |
| `schild` | Schild über der Tür; `schild_form` = `rahmen`, `rund`, `oval`, `banner`, `holz`, `geschweift`, `ohne` |
| `text_hinten` | Text auf der Rückwand (z. B. Gruß oder Jahreszahl) |
| `schrift`, `schreibweise` | Schriftstil und Groß-/Kleinschreibung für alle Texte des Hauses |

Bei der **Serie** steht jede Gestaltungsoption standardmäßig auf `zufall` – jedes Haus bekommt
dann seine eigene Fensterform, Wand, Zierleiste usw., reproduzierbar über `--seed`. Ein fester Wert
gilt für alle Häuser. Beim Schild trennt ein Komma die Namen: `-O schild="Anna, Ben, Lea"`.
Passt ein Name nicht über eine Tür, weicht erst Giebel- und Türschmuck, dann der Rahmen.

**Linienstile** (Zierleiste, Ornament-Rand, Fahrzeug-Zierlinie): `linie`, `doppelt`, `gestrichelt`,
`punkte`, `wellen`, `zickzack`, `zuckerguss`, `eiszapfen`, `lichterkette`, `girlande`, `sterne`,
`herzen`. Eiszapfen, Lichterkette und Girlande hängen immer nach unten.

**Weitere Modelle**

| Modell | Optionen |
|---|---|
| `ornament` | `rand_stil` (Linienstil des Rands), `textrahmen` (Schildform um den Text, Standard `ohne`), `pattern` mit `herzen`, `tannen`, `karo`, `wellen` (neu) |
| `fahrzeug` | `textrahmen` um die Aufschrift, `zierlinie` entlang der Seitenkontur (Eiszapfen nur an den Oberkanten) |
| `briefkasten` | `text` = Namensschild statt Briefumschlag, `schild_form`, `dach` (wie beim Haus) |
| `schneemann`, `wichtel` | `text` vorne auf dem Sockel (der Sockel wächst bei Bedarf mit) |
| alle mit Text | `schrift`, `schreibweise` |

**Schrift:** einlinige Gravurschrift mit A–Z, Ä Ö Ü ß, a–z, ä ö ü, Ziffern, `- + . , : ; ! ? & ' " ( ) / * = # °`
und den Symbolen ♥ ★ ❄ 🎄 (❤ ☆ ❅ werden automatisch umgesetzt). Stile: `normal`, `fett` (doppelte Linie),
`kursiv`, `schmal`, `breit`, `schatten`. Schreibweise: `gross` (GROSSBUCHSTABEN, Standard) oder
`normal` (wie eingegeben). `|` erzwingt eine neue Zeile; ist ein Text in einem Schild zu lang,
bricht Laserforge ihn selbst an Leerzeichen um, bevor die Schrift kleiner als 2.5 mm würde.

## So importierst du's in LightBurn

1. **Datei → Importieren** (`Strg+I` / `⌘+I`) und die `.svg` wählen. Die Datei enthält echte mm-Maße
   (`width="400mm"`, `viewBox` in mm), LightBurn übernimmt den Maßstab 1:1.
   *Kontrolle:* Beim Standard-Wichtelhaus ist die Bodenplatte **92 × 82 mm** (Sollmaß + Kerf 0.2).
   Stimmt das nicht, in LightBurns Einstellungen die SVG-Import-Optionen (Einheiten/DPI) prüfen –
   die Datei selbst ist in mm angelegt.
2. LightBurn sortiert nach Farbe automatisch in Layer:
   - **00 Schwarz = Schnitt** → Modus *Line*, Leistung/Geschwindigkeit für Durchschnitt deines Materials.
   - **01 Blau = Gravur** → Modus *Line* mit wenig Leistung (Ritzen). Die Gravur besteht aus Linien,
     nicht aus Flächen – auch Namen und Aufschriften (einlinige Schrift).
3. Unter *Optimierungseinstellungen* „Innenformen zuerst schneiden" aktivieren (die Datei listet
   Innenschnitte ohnehin vor der Außenkontur).
4. **Nicht** zusätzlich LightBurns Kerf-Offset einschalten – die Kompensation steckt schon in der Datei.
   Wenn du lieber in LightBurn kompensierst: Datei mit `--kerf 0` erzeugen.
5. Reihenfolge: Gravur-Layer vor den Schnitt-Layer ziehen, damit sich nichts verschiebt.

**xTool Creative Space:** SVG importieren, Objekte nach Farbe auswählen, Schwarz → *Schneiden*,
Blau → *Ritzen* (Score). **Glowforge:** SVG hochladen; die Farben landen als getrennte Schritte –
Schwarz auf *Cut*, Blau auf *Score* stellen.

## Kerf richtig einstellen

Der Laser trägt links und rechts der Linie je **kerf/2** ab. Laserforge versetzt deshalb:

- **Außenkonturen um +kerf/2 nach außen** (das Teil wird in der Datei größer),
- **Innenschnitte (Fenster, Slots, Bohrungen) um kerf/2 nach innen** (das Loch wird in der Datei kleiner),

sodass nach dem Schnitt exakt das Sollmaß übrig bleibt – bei jeder Materialstärke. Ein Tab mit
9 mm Sollbreite wird mit 9.2 mm gezeichnet, sein Slot mit 8.8 mm; beides wird nach dem Schnitt 9 mm.

Kerf messen: ein 20 × 20 mm-Quadrat schneiden, messen; `kerf = 20 − gemessen`. Steckverbindungen
zu locker → Kerf erhöhen; zu stramm → Kerf verringern (0.02-mm-Schritte).

## Der Validator

Läuft bei jedem Aufruf automatisch (Kommandozeile, Konfigurator und Weboberfläche), in dieser Reihenfolge:

1. **Pro Schnittpfad:** geschlossen · Mindestumfang/-fläche · keine Doppelknoten · keine
   Rückwärts-Spitzen · keine Selbstüberschneidung (auch Berührung).
2. **Pro Bauteil:** Löcher liegen in der Außenkontur · keine Schnitte kreuzen/berühren sich ·
   Mindeststeg `min_web` zwischen allen Schnitten · Gravur liegt auf Material, nicht über Löchern.
   Das Ganze zweimal: nominal und kerf-kompensiert.
3. **Kerf:** jede Kante der kompensierten Kontur liegt genau kerf/2 neben der nominalen, außen größer,
   Löcher kleiner.
4. **Steckverbindungen:** jedes Verbindungs-Feature ist genau einmal verbunden; seine Geometriepunkte
   liegen wirklich auf der Kontur bzw. bilden ein vorhandenes Loch; Zinken haben gleiche Teilung,
   sind komplementär, Tiefe = T; Tab ↔ Slot 1:1 (Breite gleich, Höhe = Slotbreite = T, gleiche
   Position); jede Breite ≥ T + Kerf; Kreuzschlitze treffen sich exakt. Fahrzeuge zusätzlich:
   **Achse ⇄ Rad** Vierkant T × T im Vierkantloch 1:1 (Pressitz), **Achse ⇄ Lager** rundes Loch
   mindestens Diagonale + 0.3 mm (dreht frei, klemmt nicht), höchstens + 2 mm (schlackert nicht).
   **Jede Verbindung wird geloggt.**
5. **Blatt:** Teile liegen auf dem Blatt und überlappen nicht.
6. **Fertige SVG-Datei:** wird zurückgelesen und unabhängig vom Generator geprüft (mm-Einheiten,
   nur die zwei Layerfarben, keine Füllung, alle Schnittpfade geschlossen und überschneidungsfrei,
   keine überlappenden Teile).

Auszug aus einem Prüfbericht:

```
OK      [wichtelhaus_vorne] 80.0 × 108.0 mm · Außenkontur geschlossen (45 Knoten) · 10 Innenschnitte · …
OK      [Verbindung] wichtelhaus_vorne.zinken_l ⇄ wichtelhaus_links.zinken_v – Zinken 7 × 9.29 mm auf 65.00 mm, Tiefe 3.00 = T, komplementär
OK      [Verbindung] wichtelhaus_vorne.dach_l0 ⇄ wichtelhaus_dach_links.vorne_dach_l0 – Tab/Slot 9.00 × 3.00 mm (Slot 9.00 × 3.00), Position 28.28 mm, 1:1
OK      [Datei wichtelhaus.svg] 400 × 300 mm · 8 Teile · 41 Schnittpfade geschlossen, …
wichtelhaus: 27 Prüfungen OK, 0 FEHLER → CUT-READY / OK
```

Passt etwas nicht (z. B. ein Name ist für den Anhänger zu lang, ein Fahrzeug zu schmal, eine
3D-Schneeflocke zu klein für die Materialstärke), kommt eine Meldung in Klartext mit dem Grenzwert,
statt dass eine wacklige Datei entsteht.

## Montage

**Wichtelhaus**

1. Seitenwände zwischen Vorder- und Rückgiebel stecken (Zinken).
2. Den Kasten mit den unteren Tabs in die Sockelplatte drücken.
3. Die beiden Dachplatten auf die Giebel setzen – die Giebel-Tabs gehen senkrecht durch die Slots.
   Am First einen Tropfen Holzleim (die kleine Firstfuge ist konstruktionsbedingt).
4. Kamin von oben in den Schlitz im linken Dach stecken.
5. LED-Teelicht von hinten durch den runden Licht-Durchbruch (Ø 40 mm) stellen.

**Steckfahrzeuge**

1. Alle Querteile (Boden, Dach, Front, Heck, Ladefläche …) mit ihren Tabs in die linke Seitenwand
   stecken, dann die rechte Seitenwand aufsetzen.
2. Vierkantachsen durch die runden Lagerbohrungen beider Seitenwände schieben – sie drehen dort frei.
3. Räder auf die Vierkant-Enden pressen und dabei ≈ 0.8 mm Luft zur Seitenwand lassen. Sitzt ein Rad
   zu locker, einen Tropfen Leim; geht es zu stramm, Kerf um 0.02 mm verringern.
4. Schlitten: Kufen-Seitenwände und Querteile stecken – fertig, keine Achsen.

**Schwibbogen**

1. Den Bogen mit seinen beiden Zapfen in die Schlitze der Bodenplatte stecken, bei Bedarf leimen.
2. Eine LED-Lichterkette hinter die Szene legen – die Fenster leuchten.

**Christbaumschmuck und Schneeflocken**

- Flach: Band oder Draht durch Öse/Loch (Ø ≥ 3.5 mm).
- 3D: Teil B (Schlitz unten, mit Öse) von oben auf Teil A (Schlitz oben) schieben, bis die Kanten
  bündig sind.

## Tests

```bash
python3 -m pip install pytest
python3 -m pytest -q
```

Auf GitHub laufen die Tests bei jedem Push automatisch (Python 3.9 und 3.12, Linux und macOS). Ein
Tag `v<version>` baut die Mac-App und legt das Release an – siehe [CONTRIBUTING.md](CONTRIBUTING.md)
und [CHANGELOG.md](CHANGELOG.md).

Abgedeckt: jede Gestaltungsoption jedes Modells (`tests/test_gestaltung.py`: alle Fensterformen,
Türen, Wand-/Dachmuster, Linienstile, Schildformen, Schriftstile …), Geometrie/Engine (Offset, Profile, Config, SVG, Layout), Validator (jede Prüfung mit
Positiv- und Negativfall, Kerf für verschiedene Werte, Tab/Slot-, Zinken- und Achs-Matching,
SVG-Dateiprüfung), je ein Modul pro Modell (mehrere Materialstärken/Kerfs/Größen, alle Ornament-Formen
und -Muster, viele Schneeflocken-Seeds, alle Fahrzeuge), Einlinien-Schrift, Serie (Vielfalt,
Reproduzierbarkeit, viele Seeds), CLI und Konfigurator (schreibt nur bei Erfolg), Weboberfläche
(alle API-Endpunkte, Fehlerfälle, ZIP, Schutz gegen fremde Webseiten) und App-Betrieb (eine Instanz,
Selbst-Beenden, Installation, Mac-Paket, Startskript mit und ohne Python).

## Aufbau

```
laserforge/
├── laserforge.py      Engine: Config, Geometrie, Kerf-Offset, Part/Assembly, Zinken/Tabs, Layout, SVG
├── validator.py       Geometrie-, Verbindungs-, Blatt- und SVG-Datei-Prüfung → OK/FEHLER-Report
├── service.py         gemeinsame Schicht für CLI, Konfigurator und Web: Parameter-Schema, Prüfen, Erzeugen, ZIP
├── cli.py             Kommandozeile (argparse) und --konfigurator
├── webui.py           lokaler Webserver (nur Standardbibliothek)
├── laserforge_app.py  App-Betrieb: eine Instanz, Browserfenster, Selbst-Beenden, Mac-Installation
├── web/index.html     Weboberfläche (ein File, kein Build-Schritt), web/icon.png Symbol
├── preview.py         PNG-Vorschau (matplotlib → Pillow → keine)
├── laserforge.yaml    Beispiel-Config mit allen Schlüsseln
├── models/
│   ├── _box.py        gemeinsamer Kasten: Zinkenwände, Giebel, Satteldach, Platten mit Slots
│   ├── _stand.py      Sockel für flache Figuren
│   ├── _shapes.py     Formen und Muster für Schmuck (Stern, Herz, Glocke …, Filigran, Kreuzschlitz)
│   ├── _font.py       Einlinien-Schrift: Groß/klein, Umlaute, Symbole, 6 Stile, Zeilenumbruch
│   ├── _deko.py       Gestaltungs-Baukasten: Zeichenfläche mit Aussparungen, Linienstile, Fenster,
│   │                  Türen, Giebel, Wand-/Dachmuster, Schilder, Vorplatz
│   ├── wichtelhaus.py, tannenbaum.py, schneemann.py, zaun.py,
│   ├── laterne.py, briefkasten.py, wichtel.py
│   ├── serie.py       Varianten-Generator
│   ├── ornament.py    Christbaumschmuck-Konfigurator
│   ├── schneeflocke.py
│   └── fahrzeug.py    Auto, Lkw, Lok, Schlitten
├── packaging/
│   ├── build_macos.py Mac-App + ZIP bauen
│   ├── make_icon.py   App-Symbol zeichnen
│   └── macos/         Startskript, Symbol (icns), LIES MICH
├── tests/             pytest
└── examples/          erzeugte Beispiele (SVG, PNG, Prüfbericht)
```

**Eigenes Modell ergänzen:** in `models/` ein Modul mit `build(cfg, **parameter) -> Assembly` anlegen.
Konturen außen gegen den Uhrzeigersinn, y nach oben, Maße in mm. Für jede Steckverbindung an beiden
Teilen ein `JointFeature` hinterlegen und mit `asm.connect("teilA:feature", "teilB:feature")`
verbinden – dann prüft der Validator sie automatisch. Zum Schluss in `models/__init__.py` in
`MODELS` eintragen und in `service.py` unter `MODEL_INFO` die Parameter beschreiben – dann erscheint
es automatisch in Weboberfläche und Konfigurator.

## Grenzen

- Nur mm; Pfade bestehen aus Geraden (Bögen werden mit `arc_tolerance` = 0.05 mm angenähert).
- Die Dachplatten treffen sich am First stumpf – bitte leimen.
- Sehr dickes Material bei sehr kleinen Modellen wird abgelehnt (Meldung „zu klein für T") statt
  eine wacklige Datei zu erzeugen.
- Fahrzeugräder sitzen per Pressitz auf der Vierkantachse – wie stramm genau, hängt von deinem
  Material und Kerf ab. Die Achse dreht in der Seitenwand; die Fahrzeuge sind Deko und Spielzeug für
  den Tisch, keine belastbare Mechanik.
- Texte werden in einliniger Blockschrift graviert (siehe [Schrift](#gestaltung-und-beschriftung));
  andere Zeichen (z. B. €) werden vorher mit Namen gemeldet. Sehr lange Texte auf kleinen Teilen
  werden abgelehnt statt unleserlich klein graviert (mindestens 2.5 mm Schrifthöhe).
- Die Weboberfläche ist für deinen eigenen Rechner bzw. dein Heimnetz gedacht (kein Login).
- Die Mac-App ist nicht von Apple signiert (dafür bräuchte es ein kostenpflichtiges Entwicklerkonto);
  deshalb die einmalige Freigabe unter *Datenschutz & Sicherheit*. Eine Windows-Version gibt es nicht
  als Installer – dort läuft `python laserforge_app.py` bzw. `python webui.py`.
