"""
i18n.py – Übersetzungen für Steckwerk (Deutsch ist die Grundsprache, dazu Englisch).

Schlüssel sind die deutschen Texte selbst: Was hier fehlt, erscheint einfach auf Deutsch.

  tr("Breite", "en")                 → "Width"
  translate_schema(schema, "en")     Modelle, Parameter, Auswahllisten, Hilfetexte
  translate_lines(lines, "en")       Prüfbericht, Hinweise und Fehlermeldungen (Muster mit Platzhaltern)

Pakete können eigene Übersetzungen mitbringen: in einer Modelldatei
  UEBERSETZUNG = {"en": {"Krippe": "Nativity", "Stall mit Stern": "Stable with star"}}
"""
from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Tuple

SPRACHEN = [("de", "Deutsch"), ("en", "English")]
DEFAULT = "de"

EN: Dict[str, str] = {
    "Serie: n muss zwischen 1 und 50 liegen": "Series: n must be between 1 and 50",
    "Sockel-Text": "Base text", "Briefkasten-Text": "Mailbox text", "Serie": "Series",
    # --- Gruppen und Abschnitte ---------------------------------------------------------------------
    "Häuser": "Houses", "Zubehör": "Accessories", "Schmuck": "Ornaments", "Fahrzeuge": "Vehicles",
    "Eigene Motive": "Custom motifs", "Komplett": "Complete sets", "Pakete": "Packages",
    "Fenster und Tür": "Windows and door", "Wände, Dach und Garten": "Walls, roof and garden",
    "Beschriftung": "Lettering", "Gestaltung": "Design",
    # --- Modelle --------------------------------------------------------------------------------------
    "Wichtelhaus": "Gnome house", "Häuser-Serie": "House series", "Tannenbaum": "Fir tree",
    "Schneemann": "Snowman", "Wichtel": "Gnome", "Zaun": "Fence", "Laterne": "Lantern",
    "Briefkasten": "Mailbox", "Zubehör-Set": "Accessory set", "Christbaumschmuck": "Tree ornaments",
    "Schneeflocke": "Snowflake", "Schneeflocken": "Snowflakes", "Steckfahrzeug": "Push-fit vehicle",
    "Zug-Set": "Train set", "Schwibbogen": "Candle arch", "Alle Modelle": "All models",
    "Aufsteller": "Stand-up sign", "Schild": "Sign", "Anhänger": "Tag", "Untersetzer": "Coaster",
    "Silhouette": "Silhouette",
    "Haus mit Satteldach, Fenstern, Tür und Kamin; Wände mit Zinken verbunden. Fenster, Tür, Wand- und Dachgravur, Schilder und Schrift frei gestaltbar.":
        "House with gable roof, windows, door and chimney; walls joined with finger joints. Windows, door, wall and roof engraving, signs and lettering are all customisable.",
    "Mehrere Wichtelhäuser mit zufälligen, reproduzierbaren Varianten – Gestaltung fest oder je Haus gewürfelt.":
        "Several gnome houses with random but reproducible variations – fixed design or rolled per house.",
    "Figur mit Standsockel – auf Wunsch mit Namen.": "Figure on a stand – with a name if you like.",
    "Wichtelfigur mit Mütze und Standsockel – auf Wunsch mit Namen.": "Gnome figure with hat and stand – with a name if you like.",
    "Lattenzaun mit Füßen.": "Picket fence with feet.",
    "Kleine Laterne mit Fenstern und Bügel.": "Small lantern with windows and handle.",
    "Wichtel-Briefkasten auf Pfosten – mit Namensschild und Dachgravur.": "Gnome mailbox on a post – with name plate and roof engraving.",
    "Tannenbaum, Schneemann, Zaun, Laterne, Briefkasten und Wichtel in Standardgröße.":
        "Fir tree, snowman, fence, lantern, mailbox and gnome in standard size.",
    "Anhänger-Konfigurator: Form, Muster, Randstil, Name/Jahr mit Rahmen, Öse – flach oder 3D gesteckt.":
        "Ornament configurator: shape, pattern, edge style, name/year with frame, eyelet – flat or 3D slotted.",
    "Sechszählige Flocken, jede aus ihrem Zufallswert – mit Öse oder 3D gesteckt.":
        "Six-fold snowflakes, each from its own random seed – with eyelet or 3D slotted.",
    "Seitenwände + Querteile mit Tabs; Räder drehen auf einer Vierkantachse aus der Platte. Aufschrift mit Rahmen und Zierlinien.":
        "Side walls and cross pieces with tabs; wheels turn on a square axle cut from the sheet. Lettering with frame and decorative lines.",
    "Lok, Tender und Wagen in passender Größe – mit Kupplungslöchern zum Verbinden.":
        "Locomotive, tender and wagons in matching sizes – with coupling holes to connect them.",
    "Lichterbogen mit Kerzen und Scherenschnitt-Szene (Dorf, Wald, Kirche) – Fenster zum Hinterleuchten.":
        "Candle arch with candles and a paper-cut scene (village, forest, church) – windows to backlight.",
    "Jedes Modell in Standardgröße – gut als Testlauf für neue Material- und Kerf-Einstellungen.":
        "Every model in standard size – a good test run for new material and kerf settings.",
    "Platte mit Standsockel – Motive aus der Bibliothek frei platzieren: ausschneiden oder gravieren.":
        "Plate on a stand – place motifs from the library freely: cut out or engrave.",
    "Hängeschild mit Löchern oder Schraublöchern – Motive frei platzieren, Text darunter.":
        "Hanging sign with holes or screw holes – place motifs freely, text below.",
    "Kleiner Anhänger mit Loch – für Geschenke, Schlüssel oder den Baum.": "Small tag with a hole – for gifts, keys or the tree.",
    "Untersetzer – Motive standardmäßig flächig graviert.": "Coaster – motifs are area-engraved by default.",
    "Das Motiv selbst wird zum Teil – als Figur im Sockel, mit Öse zum Aufhängen oder als freie Form.":
        "The motif itself becomes the part – as a figure in a stand, with an eyelet for hanging, or as a free shape.",
    # --- Material ------------------------------------------------------------------------------------
    "Materialstärke T": "Material thickness T", "Kerf (Schnittbreite)": "Kerf (cut width)",
    "CO2 meist 0.1–0.2, Diode 0.15–0.3": "CO2 usually 0.1–0.2, diode 0.15–0.3",
    "Farbe Schnitt": "Cut colour", "Farbe Gravur": "Engrave colour",
    "LightBurn-Layer 00": "LightBurn layer 00", "LightBurn-Layer 01": "LightBurn layer 01",
    "Zufallsstartwert": "Random seed", "Gleicher Wert = gleiches Ergebnis": "Same value = same result",
    # --- Maße und Mengen -----------------------------------------------------------------------------
    "Breite": "Width", "Breite (Giebelseite)": "Width (gable side)", "Tiefe": "Depth", "Höhe": "Height",
    "Traufhöhe": "Eaves height", "Dachneigung": "Roof pitch", "Länge": "Length", "Länge der Lok": "Locomotive length",
    "Durchmesser": "Diameter", "Größe": "Size", "Größe (Höhe)": "Size (height)",
    "Größe (längere Seite)": "Size (longer side)", "Maßstab": "Scale", "Anzahl": "Count",
    "Anzahl Häuser": "Number of houses", "Anzahl Wagen": "Number of wagons", "Anzahl ohne Text": "Count without text",
    "Grundbreite": "Base width", "Grundhöhe": "Base height", "Grundtiefe": "Base depth",
    "Höhe Kasten": "Box height", "Platte Breite": "Sheet width", "Platte Höhe": "Sheet height",
    "Etagen": "Tiers", "Achsen": "Axles", "Kerzen": "Candles", "Fenster vorne": "Front windows",
    "Fenster je Seite": "Windows per side",
    # --- Optionen ------------------------------------------------------------------------------------
    "Text": "Text", "Aufschrift": "Lettering", "Aufschriften": "Lettering", "Rahmen": "Frame", "Form": "Shape",
    "Muster": "Pattern", "Motiv": "Motif", "Motive": "Motifs", "Szene": "Scene", "Fuß": "Base",
    "Fahrzeug": "Vehicle", "Wagen": "Wagon", "Tender (zur Lok)": "Tender (for the loco)",
    "Tender und Wagen wachsen mit": "Tender and wagons scale along",
    "Kupplungslöcher": "Coupling holes", "Lok, Tender und Wagen mit Draht/Schnur verbinden": "Connect loco, tender and wagons with wire or string",
    "Leer lassen = Standard je Fahrzeug": "Leave empty = default per vehicle",
    "Dach": "Roof", "Kamin": "Chimney", "Anbau": "Annex", "Vordach": "Porch roof", "Tür": "Door",
    "Fensterform": "Window shape", "Fenster ausschneiden": "Cut out windows", "Fenster/Türen": "Windows/doors",
    "Fensterläden": "Shutters", "Fensterschmuck": "Window decoration", "Sprossen": "Glazing bars",
    "Türschmuck": "Door decoration", "Türkranz": "Door wreath", "Wandgravur": "Wall engraving",
    "Dachgravur": "Roof engraving", "Giebelschmuck": "Gable decoration", "Giebeltext": "Gable text",
    "Heuluke": "Hay hatch", "Uhr": "Clock", "Rundfenster": "Round window", "Schneehaube": "Snow cap",
    "Schneekante": "Snow edge", "Eiszapfen": "Icicles", "Lichterkette": "Fairy lights", "Girlande": "Garland",
    "Zierleiste unter dem Dach": "Trim under the roof", "Linie entlang der Traufe – auch auf dem Dach": "Line along the eaves – also on the roof",
    "Vorplatz": "Forecourt", "Bodenplatte vor der Tür wird verlängert": "Base plate is extended in front of the door",
    "Fußmatte": "Doormat", "Text auf der Fußmatte": "Text on the doormat", "Steinweg": "Stone path",
    "Blumenkasten": "Flower box", "Läden und Blumen": "Shutters and flowers", "Läden mit Herz": "Shutters with heart",
    "Lichtloch hinten": "Light hole at the back", "Runder Durchbruch für eine LED-Kerze": "Round opening for an LED candle",
    "Schild über der Tür": "Sign above the door", "Schild um den Text": "Panel around the text",
    "Schild um die Aufschrift": "Panel around the lettering", "Schildform": "Sign shape", "Namensschild": "Name plate",
    "Schriftstil": "Font style", "Schreibweise": "Letter case", "Textrahmen": "Text frame",
    "Zierlinie": "Decorative line", "Zierlinien": "Decorative lines", "Zierrahmen": "Decorative frame",
    "Zierlinie auf dem Bogen": "Decorative line on the arch", "Rahmen und Sims": "Frame and sill",
    "Randstil": "Edge style", "Rand": "Edge", "Aufhängung": "Hanging", "Standsockel": "Stand",
    "Bodenplatte": "Base plate", "Innenformen": "Inner shapes", "Innenformen ausschneiden": "Cut out inner shapes",
    "Innenformen gravieren": "Engrave inner shapes", "Abstand der Flächengravur": "Spacing of area engraving",
    "Linienabstand für „flächig gravieren“": "Line spacing for “area engrave”",
    "In der Vorschau ziehen; x/y = Abstand zur Mitte in mm": "Drag in the preview; x/y = offset from the centre in mm",
    "Text auf dem Sockel": "Text on the stand", "Text auf der Platte": "Text on the plate",
    "Text auf der Rückwand": "Text on the back wall", "Text auf der Sockelleiste": "Text on the base strip",
    "Gravur; Filigran = Durchbrüche": "Engraving; filigree = cut-throughs", "Filigran (Durchbrüche)": "Filigree (cut-throughs)",
    "Linienstil entlang der Seitenkontur – Eiszapfen hängen an den Oberkanten": "Line style along the side outline – icicles hang from the top edges",
    "zum Hinterleuchten mit einer Lichterkette": "to backlight with fairy lights",
    # Auswahlwerte
    "ausschneiden": "cut out", "gravieren": "engrave", "Umriss gravieren": "engrave outline",
    "flächig gravieren": "area engrave", "keine": "none", "keiner": "none", "keins": "none", "nichts": "nothing",
    "nichts (freie Form)": "nothing (free shape)", "normal": "normal", "fett": "bold", "kursiv": "italic",
    "schmal": "narrow", "breit": "wide", "mit Schatten": "with shadow", "GROSSBUCHSTABEN": "CAPITALS",
    "wie eingegeben (groß/klein)": "as typed (upper/lower case)", "rund": "round", "oval": "oval",
    "rund (Hobbit)": "round (hobbit)", "abgerundet": "rounded", "Rechteck": "Rectangle", "Rechteckig": "Rectangular",
    "Rechteck, abgerundet": "Rectangle, rounded", "Quadrat, abgerundet": "Square, rounded", "Achteck": "Octagon",
    "Rundbogen": "Round arch", "Spitzbogen": "Pointed arch", "geschweift": "curved", "Linie": "Line",
    "Doppellinie": "Double line", "gestrichelt": "dashed", "Punkte": "Dots", "Wellen": "Waves",
    "Zickzack": "Zigzag", "Streifen": "Stripes", "Karo": "Diamonds", "Raute": "Rhombus", "Kreuz": "Cross",
    "glatt": "plain", "waagrecht": "horizontal", "senkrecht": "vertical", "abwechselnd": "alternating",
    "Loch": "Hole", "Öse oben": "Eyelet at top", "Öse zum Aufhängen": "Eyelet for hanging",
    "ein Loch oben": "one hole at top", "zwei Löcher oben": "two holes at top", "vier Schraublöcher": "four screw holes",
    "nur Text": "text only", "alles zusammen": "everything together", "Zufall je Haus": "random per house",
    "3D gesteckt": "3D slotted", "Zwei Hälften, über Kreuz gesteckt.": "Two halves, slotted crosswise.",
    "Zwei Hälften mit Kreuzschlitz (ohne Text)": "Two halves with cross slot (no text)",
    "Anhänger/Schild": "Tag/sign", "Banner": "Banner", "Holzbrett": "Wooden board",
    "Fachwerk": "Half-timbered", "Bruchstein": "Rubble stone", "Rauputz": "Rough plaster", "Ziegel": "Bricks",
    "Holzbretter": "Wooden boards", "Biberschwanz": "Beaver-tail tiles", "Holzschindeln": "Wooden shingles",
    "Rundschindeln": "Round shingles", "Reet": "Thatch", "Zuckerguss": "Icing",
    "Tannen": "Fir trees", "Tanne": "Fir tree", "Tannen und Schnee": "Fir trees and snow", "Sterne": "Stars",
    "Sternenhimmel": "Starry sky", "Herzen": "Hearts", "Flocken": "Flakes", "Laternen": "Lanterns",
    "Dorf": "Village", "Wald": "Forest", "Kirche": "Church", "Schlitten": "Sleigh",
    "Lok": "Locomotive", "Personenwagen": "Passenger car", "Güterwagen": "Freight car", "Bus": "Bus",
    "Traktor": "Tractor", "Auto": "Car", "Lkw": "Truck", "Lkw mit Tandemachse hinten": "Truck with rear tandem axle",
    "Kugel": "Bauble", "Stern": "Star", "Herz": "Heart", "Mond": "Moon", "Glocke": "Bell", "Engel": "Angel",
    "Kerze": "Candle", "Geschenk": "Gift", "Lebkuchenmann": "Gingerbread man", "Nikolausstiefel": "Santa boot",
    "Zuckerstange (ohne Text)": "Candy cane (no text)", "Tannenzapfen": "Pine cone",
    "Katze": "Cat", "Fledermaus": "Bat", "Gespenst": "Ghost", "Hexenhut": "Witch hat", "Hexe auf dem Besen": "Witch on a broom",
    "Kürbis": "Pumpkin", "Totenkopf": "Skull", "Baum": "Tree", "Geist": "Ghost", "Hexe": "Witch",
    "Lebkuchen": "Gingerbread", "Schneemann ": "Snowman", "Stiefel": "Boot", "Zapfen": "Pine cone",
    # Hilfetexte
    "Symbole: ♥ ★ ❄ 🎄": "Symbols: ♥ ★ ❄ 🎄", "| = neue Zeile – Symbole: ♥ ★ ❄ 🎄": "| = new line – symbols: ♥ ★ ❄ 🎄",
    "Gravur auf beiden Seiten, | = neue Zeile – Symbole: ♥ ★ ❄ 🎄": "Engraved on both sides, | = new line – symbols: ♥ ★ ❄ 🎄",
    "Komma = je Haus ein Name (Anna, Ben, …); | = neue Zeile – Symbole: ♥ ★ ❄ 🎄":
        "Comma = one name per house (Anna, Ben, …); | = new line – symbols: ♥ ★ ❄ 🎄",
    "Komma = je Name ein Anhänger, | = neue Zeile (z. B. Anna|2026) – Symbole: ♥ ★ ❄ 🎄":
        "Comma = one ornament per name, | = new line (e.g. Anna|2026) – symbols: ♥ ★ ❄ 🎄",
    "mit Komma je Fahrzeug: Lok, Tender, Wagen … – Symbole: ♥ ★ ❄ 🎄": "comma-separated per vehicle: loco, tender, wagon … – symbols: ♥ ★ ❄ 🎄",
    "statt Briefumschlag, z. B. „Post“ – | = neue Zeile – Symbole: ♥ ★ ❄ 🎄": "instead of the envelope, e.g. “Mail” – | = new line – symbols: ♥ ★ ❄ 🎄",
    "unten auf dem Schild – | = neue Zeile – Symbole: ♥ ★ ❄ 🎄": "at the bottom of the sign – | = new line – symbols: ♥ ★ ❄ 🎄",
    "unten auf der Platte – Symbole: ♥ ★ ❄ 🎄": "at the bottom of the plate – symbols: ♥ ★ ❄ 🎄",
    "z. B. Baujahr „Anno 1890“ – Symbole: ♥ ★ ❄ 🎄": "e.g. year built “Anno 1890” – symbols: ♥ ★ ❄ 🎄",
    "z. B. Frohe Weihnacht – Symbole: ♥ ★ ❄ 🎄": "e.g. Merry Christmas – symbols: ♥ ★ ❄ 🎄",
    "z. B. Jahreszahl oder Gruß – Symbole: ♥ ★ ❄ 🎄": "e.g. a year or greeting – symbols: ♥ ★ ❄ 🎄",
    "z. B. ein Name – Symbole: ♥ ★ ❄ 🎄": "e.g. a name – symbols: ♥ ★ ❄ 🎄", "z. B. „Willkommen“": "e.g. “Welcome”",
    # Updates und Meldungen
    "Programm-Updates installiert die Mac-App selbst. Hier bitte von Hand aktualisieren (git pull bzw. neue ZIP).":
        "The Mac app installs program updates itself. Here, please update by hand (git pull or a new ZIP).",
    "Steckwerk läuft noch aus „Downloads“. Erst in den Programme-Ordner installieren.":
        "Steckwerk is still running from “Downloads”. Install it into the Applications folder first.",
    "Für diese Version gibt es kein Mac-Paket im Kanal.": "There is no Mac package for this version in the channel.",
    "GitHub lehnt den Zugangsschlüssel ab – ist er abgelaufen oder fehlt ihm das Leserecht?":
        "GitHub rejects the access key – has it expired or does it lack read permission?",
    "Die Kanal-Adresse muss mit https:// beginnen": "The channel address must start with https://",
    "Der Update-Kanal liefert kein gültiges JSON": "The update channel does not return valid JSON",
    "Das ist kein Steckwerk-Update-Kanal": "This is not a Steckwerk update channel",
    "Der Update-Kanal braucht eine neuere Steckwerk – bitte einmal von Hand aktualisieren":
        "The update channel needs a newer Steckwerk – please update once by hand",
    "Im Update fehlt die Steckwerk.app": "The update does not contain Steckwerk.app",
    "Updates nur am Rechner selbst installieren": "Install updates only on the computer itself",
    "Motiv entfernt": "Motif removed", "Paket entfernt": "Package removed", "Einstellungen gespeichert": "Settings saved",
    "Alle Pakete sind aktuell": "All packages are up to date", "Zugriff verweigert": "Access denied",
    "nicht gefunden": "not found", "Anfrage zu groß": "Request too large",
    # Montagehinweise
    "Band durch die Öse an der oberen Spitze.": "Thread a ribbon through the eyelet at the top point.",
    "Band oder Kordel durch das Loch fädeln.": "Thread a ribbon or cord through the hole.",
    "Platte in den Sockel stecken.": "Push the plate into the stand.",
    "Figur in den Sockel stecken.": "Push the figure into the stand.",
    "an einer Kordel oder mit Schrauben aufhängen.": "hang on a cord or with screws.",
    "Dach am First mit etwas Holzleim verbinden (Firstfuge ist gewollt).": "Join the roof at the ridge with a little wood glue (the ridge gap is intended).",
    "Pfosten in Fußplatte und Kastenboden stecken (ggf. mit Leim fixieren).": "Push the post into the foot plate and box floor (glue if needed).",
    "Seitenwände zwischen Vorder- und Rückwand stecken, dann alle Wände in die Bodenplatte drücken.":
        "Fit the side walls between front and back wall, then press all walls into the base plate.",
    "LED-Teelicht auf die Markierung stellen, Deckel aufstecken, Bügel einstecken.": "Place an LED tea light on the mark, fit the lid, insert the handle.",
    "Bogen mit beiden Zapfen in die Bodenplatte stecken (bei Bedarf leimen). Eine LED-Lichterkette hinter der Szene lässt die Fenster leuchten.":
        "Push the arch with both tenons into the base plate (glue if needed). LED fairy lights behind the scene make the windows glow.",
    "Anbau rechts an das Haus kleben (Vorderkanten bündig).": "Glue the annex to the right of the house (front edges flush).",
    "Kamin von oben in den Schlitz im linken Dach stecken.": "Push the chimney from above into the slot in the left roof.",
    "Teil A (Schlitz oben) von oben auf Teil B (Schlitz unten) schieben.": "Slide part A (slot at top) from above onto part B (slot at bottom).",
    "Zaunfeld mit den Fuß-Tabs in die Leiste stecken; mehrere Felder hintereinander ergeben einen langen Zaun.":
        "Push the fence panel with its foot tabs into the rail; several panels in a row make a long fence.",
    "Querteile in die linke Seitenwand stecken, rechte Seitenwand aufsetzen": "Push the cross pieces into the left side wall, then put on the right side wall",
    "Kupplungslöcher in Front/Heck – Wagen mit einer Draht- oder Schnurschlaufe verbinden (z. B. aufgebogene Büroklammer)":
        "Coupling holes front and back – connect wagons with a loop of wire or string (e.g. an unbent paper clip)",
}

# Prüfbericht, Hinweise, Fehler: Muster (deutscher regulärer Ausdruck → englische Vorlage).
PATTERNS_EN: List[Tuple[str, str]] = [
    (r"^(\S+) liegt außerhalb (\S+)", r"\1 is outside \2"),
    (r"^(.+?) ist keine Zahl$", r"\1 is not a number"), (r"^bitte eine ganze Zahl$", "please enter a whole number"),
    (r"^höchstens (\d+) Zeichen$", r"at most \1 characters"),
    (r"^(.+?) nicht erlaubt – wähle (.+)$", r"\1 not allowed – choose \2"),
    (r"^Motiv (.+?) gibt es nicht – in der Motiv-Bibliothek wählen$", r"Motif \1 does not exist – choose one from the motif library"),
    (r"Zeichen (.+?) gibt es in der Gravurschrift nicht", r"Character \1 is not available in the engraving font"),
    (r"\bGröße muss zwischen (\S+) und (\S+) mm liegen", r"size must be between \1 and \2 mm"),
    (r"\bBreite muss zwischen (\S+) und (\S+) mm liegen", r"width must be between \1 and \2 mm"),
    (r"\bHöhe muss zwischen (\S+) und (\S+) mm liegen", r"height must be between \1 and \2 mm"),
    (r"^(.+): (\d+) Prüfungen OK, (\d+) FEHLER → CUT-READY / OK$", r"\1: \2 checks OK, \3 errors → CUT-READY / OK"),
    (r"^(.+): (\d+) Prüfungen OK, (\d+) FEHLER → NICHT schneiden$", r"\1: \2 checks OK, \3 errors → do NOT cut"),
    (r" – Tab/Slot (.+?) mm \(Slot (.+?)\), Position (.+?) mm", r" – tab/slot \1 mm (slot \2), position \3 mm"),
    (r" – Zinken (.+?) mm auf (.+?) mm, Tiefe (.+?) = T, komplementär", r" – fingers \1 mm over \2 mm, depth \3 = T, complementary"),
    (r" – Achse ⇄ Lager: Ø (.+?) mm um Diagonale (.+?) mm, Spiel (.+?) mm \(dreht frei\), Achsposition", r" – axle ⇄ bearing: Ø \1 mm around diagonal \2 mm, play \3 mm (turns freely), axle position"),
    (r" – Achse ⇄ Rad: Vierkant (.+?) in Nabe (.+?) mm, Pressitz", r" – axle ⇄ wheel: square \1 in hub \2 mm, press fit"),
    (r"Achsposition", "axle position"),
    (r" – Kreuzschlitz (.+?) mm, Breite (.+?) = T", r" – cross slot \1 mm, width \2 = T"),
    (r"Außenkontur geschlossen \((\d+) Knoten\)", r"outline closed (\1 nodes)"),
    (r"(\d+) Teile auf (.+?) mm, keine Überlappung, Abstand ≥", r"\1 parts on \2 mm, no overlap, spacing ≥"),
    (r"liegt außerhalb des Blatts", "lies outside the sheet"), (r"ragt über das Blatt", "extends beyond the sheet"),
    (r" und (.+?) überlappen/zu dicht", r" and \1 overlap/too close"), (r"ist mit nichts verbunden", "is not connected to anything"),
    (r"ist (\d+)× verbunden", r"is connected \1×"), (r": Teil fehlt$", ": part missing"), (r": Feature fehlt$", ": feature missing"),
    (r"^Verbindung\b", "Joint"), (r"\[Verbindung\]", "[joint]"),
    (r"kein gültiges XML", "not valid XML"), (r"unbekannte Linienfarbe", "unknown line colour"),
    (r"ist gefüllt \(fill ≠ none\)", "is filled (fill ≠ none)"),
    # Updates
    (r"^Nicht gefunden: (\S+?)\.? Ist das Repo privat\? .*$", r"Not found: \1. Is the repo private? Then enter a read key under “Updates → Settings”."),
    (r"^Nicht gefunden: (.+)$", r"Not found: \1"),
    (r"^Keine Verbindung zum Update-Server \((.*)\)\. Bist du online\?$", r"No connection to the update server (\1). Are you online?"),
    (r"^Sichere Verbindung fehlgeschlagen \((.*)\)\.$", r"Secure connection failed (\1)."),
    (r"^Der Update-Server antwortet mit Fehler (\d+)$", r"The update server replied with error \1"),
    (r"^(.+): Prüfsumme stimmt nicht – .*$", r"\1: checksum mismatch – download damaged or altered, nothing installed"),
    (r"^„(.+)“ braucht Steckwerk (\S+) – erst das Programm aktualisieren$", r"“\1” needs Steckwerk \2 – update the program first"),
    (r"^Paket '(.+)' gibt es im Update-Kanal nicht$", r"Package '\1' is not in the update channel"),
    (r"^Keine Schreibrechte im Ordner (.+)\.$", r"No write permission in folder \1."),
    (r"^Steckwerk (\S+) ist schon aktuell$", r"Steckwerk \1 is already up to date"),
    (r"^Das Update enthält Version (\S+) statt (\S+) – nichts geändert$", r"The update contains version \1 instead of \2 – nothing changed"),
    (r"^Paket „(.+)“ (\S+) installiert – Modelle: (.+)$", r"Package “\1” \2 installed – models: \3"),
    (r"^Paket „(.+)“ (\S+) installiert$", r"Package “\1” \2 installed"),
    (r"^(\d+) Paket\(e\) installiert: (.+)$", r"\1 package(s) installed: \2"),
    (r"^Steckwerk (\S+) ist installiert und startet gleich neu$", r"Steckwerk \1 is installed and will restart shortly"),
    (r"^Motiv „(.+)“ importiert$", r"Motif “\1” imported"),
    (r"^Paket (\S+) braucht Steckwerk (\S+) – du hast (\S+)$", r"Package \1 needs Steckwerk \2 – you have \3"),
    (r"^Achsen durch die Lagerbohrungen schieben, Räder auf den Vierkant pressen \(≈(.+?) mm Luft zur Seitenwand lassen, bei Bedarf einen Tropfen Leim\)\.$",
     r"Push the axles through the bearing holes, press the wheels onto the square (leave ≈\1 mm clearance to the side wall, a drop of glue if needed)."),
    (r"^Aufhängen: Band oder Draht durch Öse/Loch \(Ø ≥ (.+?) mm\)\.?$", r"Hanging: thread ribbon or wire through the eyelet/hole (Ø ≥ \1 mm)."),
    (r"^FEHLER(\s+)", r"ERROR\1"), (r"^WARNUNG(\s+)", r"WARNING\1"), (r"^HINWEIS(\s+)", r"NOTE\1"),
    (r"(\d+) Teile\b", r"\1 parts"), (r"(\d+) Schnittpfade geschlossen", r"\1 cut paths closed"),
    (r"ohne Überschneidung/Überlappung", "no intersections/overlaps"), (r"(\d+) Gravurpfade", r"\1 engrave paths"),
    (r"Farben ", "colours "), (r"\[Datei ", "[file "), (r"Außenkontur geschlossen", "outline closed"),
    (r"(\d+) Innenschnitte", r"\1 inner cuts"), (r"(\d+) Gravuren", r"\1 engravings"),
    (r"keine Selbstüberschneidung/Überlappung", "no self-intersection/overlap"),
    (r"passt auf kein Blatt", "fits on no sheet"), (r"Blatt", "sheet"),
    (r"Alle (\d+) Modelle cut-ready", r"All \1 models cut-ready"),
    (r"^(Motiv \d+) \((.+?)\) ragt über den Rand oder sitzt zu nah daran – verschieben oder kleiner machen$",
     r"\1 (\2) sticks out over the edge or is too close to it – move it or make it smaller"),
    (r"^Motiv (\d+) \((.+?)\) sitzt zu dicht", r"Motif \1 (\2) is too close"),
    (r"fallen beim Ausschneiden heraus", "fall out when cut"),
    (r"^Motiv (\d+)", r"Motif \1"),
    (r"passt nicht", "does not fit"), (r"zu klein", "too small"), (r"zu groß", "too large"),
    (r"kürzer fassen oder größer machen", "shorten it or make the part larger"),
    (r"Figur in den Sockel stecken\.", "Push the figure into the stand."),
    (r"Platte in den Sockel stecken\.", "Push the plate into the stand."),
    (r"Band oder Kordel durch das Loch fädeln\.", "Thread a ribbon or cord through the hole."),
    (r"an einer Kordel oder mit Schrauben aufhängen\.", "hang on a cord or with screws."),
]

_compiled: Dict[str, List[Tuple["re.Pattern[str]", str]]] = {"en": [(re.compile(p), r) for p, r in PATTERNS_EN]}
_extra: Dict[str, Dict[str, str]] = {"en": {}}


def norm(lang: Any) -> str:
    lang = str(lang or "").lower()[:2]
    return lang if lang in dict(SPRACHEN) else DEFAULT


def add(lang: str, table: Dict[str, str]) -> None:
    """Übersetzungen ergänzen (z. B. aus einem Paket)."""
    if isinstance(table, dict):
        _extra.setdefault(norm(lang), {}).update({str(k): str(v) for k, v in table.items()})


def tr(text: str, lang: str) -> str:
    lang = norm(lang)
    if lang == DEFAULT or not isinstance(text, str):
        return text
    return _extra.get(lang, {}).get(text) or EN.get(text) or text


def tr_line(text: str, lang: str) -> str:
    """Satz mit Zahlen/Namen: erst exakt, dann alle passenden Muster anwenden."""
    lang = norm(lang)
    if lang == DEFAULT or not isinstance(text, str):
        return text
    exact = tr(text, lang)
    if exact != text:
        return exact
    head, sep, rest = text.partition(": ")                 # „teil: Montagehinweis.“
    if sep and tr(rest, lang) != rest:
        return tr(head, lang) + sep + tr(rest, lang)
    rest_clean = rest.rstrip(".")
    if sep and tr(rest_clean, lang) != rest_clean:
        return tr(head, lang) + sep + tr(rest_clean, lang) + "."
    if sep and not head.startswith(("OK", "FEHLER", "WARNUNG")) and "[" not in head:
        done = _apply(rest, lang)
        if done != rest:
            return tr(head, lang) + sep + done
    return _apply(text, lang)


def _apply(text: str, lang: str) -> str:
    for rx, rep in _compiled.get(lang, []):
        text = rx.sub(rep, text)
    return text


def translate_lines(lines: Iterable[str], lang: str) -> List[str]:
    return [tr_line(l, lang) for l in lines]


_KEYS = ("label", "desc", "help", "section", "unit_label", "placeholder")


def translate_schema(obj: Any, lang: str) -> Any:
    """Kopie des Schemas mit übersetzten Anzeigetexten (Werte/Schlüssel bleiben gleich)."""
    if norm(lang) == DEFAULT:
        return obj
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if k in _KEYS and isinstance(v, str):
                out[k] = tr(v, lang)
            elif k == "groups" and isinstance(v, list):
                out[k] = v                                    # Schlüssel bleiben deutsch, Anzeige über group_labels
                out["group_labels"] = {g: tr(g, lang) for g in v}
            elif k == "name" and isinstance(v, str) and obj.get("eingebaut"):
                out[k] = tr(v, lang)                          # eingebaute Motive
            elif k in ("motive", "pakete", "vehicle_defaults", "flaechen", "linien"):
                out[k] = translate_schema(v, lang) if k in ("motive",) else v
            else:
                out[k] = translate_schema(v, lang)
        return out
    if isinstance(obj, list):
        return [translate_schema(v, lang) for v in obj]
    return obj


_LINE_KEYS = ("error", "message", "summary", "grund", "fehler")
_LIST_KEYS = ("notes", "errors", "warnings")


def localize(obj: Any, lang: str) -> Any:
    """API-Antwort übersetzen: Meldungen, Prüfbericht, Hinweise (SVG und Werte bleiben unverändert)."""
    if norm(lang) == DEFAULT:
        return obj
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if k in _LINE_KEYS and isinstance(v, str):
                out[k] = tr_line(v, lang)
            elif k == "report" and isinstance(v, str):
                out[k] = "\n".join(tr_line(l, lang) for l in v.split("\n"))
            elif k in _LIST_KEYS and isinstance(v, list):
                out[k] = [tr_line(x, lang) if isinstance(x, str) else localize(x, lang) for x in v]
            elif obj.get(k + "_" + lang):                         # Text bringt eigene Übersetzung mit
                out[k] = obj[k + "_" + lang]
            elif k in ("svg", "params", "config", "flaechen", "linien"):
                out[k] = v
            else:
                out[k] = localize(v, lang)
        return out
    if isinstance(obj, list):
        return [localize(v, lang) for v in obj]
    return obj
