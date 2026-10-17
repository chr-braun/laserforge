# Versionsverlauf

Alles ist zwischen dem 9. und 17. Oktober 2026 entstanden. Die Details stehen im
[CHANGELOG](https://github.com/chr-braun/steckwerk/blob/main/CHANGELOG.md).

| Version | Datum | Was dazukam |
|---|---|---|
| 1.0 / 1.1 | 09.10. | Wichtelhaus, Serie, Zubehör, Christbaumschmuck, Schneeflocken, Steckfahrzeuge; Validator, Weboberfläche, Konfigurator, Mac-App |
| 1.2.0 | 09.10. | Gestaltung und Beschriftung: Fenster, Türen, Gravuren, Zierleisten, Schilder, sechs Schriften |
| 1.3.0 | 09.10. | Acht neue Schmuckformen (Lebkuchenmann, Stiefel, Zuckerstange, Geschenk, Kerze, Engel, Zapfen, Schneemann) |
| 1.4.0 | 09.10. | Schwibbogen mit Dorf, Wald oder Kirche |
| 1.5.0 | 09.10. | Tender, Wagen, Bus, Traktor, Zug-Set; Paket-Standard mit Beispiel „Türschild“ |
| 1.5.1 | 09.10. | Mac-App startet aus „Downloads“ zuverlässig |
| 1.6.0 | 09.10. | Eigene Motive: SVG/PNG-Import, Bibliothek, fünf Motiv-Vorlagen, Platzieren mit der Maus |
| 1.7.0 | 10.10. | Updater: Programm und Pakete direkt in der App aktualisieren |
| **2.0.0** | 10.10. | **Laserforge heißt jetzt Steckwerk**; Pakete als `.swpaket`; Deutsch und Englisch |
| 2.1.0 | 10.10. | Neue Oberfläche im Mac-Stil (Seitenleiste, Werkzeugleiste, Inspektor, Einstellungsfenster) |
| 2.2.0 | 11.10. | Materialprofile für den xTool M2 (10 W / 20 W) mit XCS-Startwerten |
| 2.2.1 | 11.10. | Filigran-Profile Pappel 1,5 und 2 mm |
| 2.3.0 | 11.10. | Ollama-Assistent, „Motiv zeichnen“ mit Ollama/OpenRouter, Seitenleiste mit Suche |
| 2.4.0 | 15.10. | Pakete können andere Pakete benutzen (Bibliothek, automatische Abhängigkeiten) |
| 2.5.0 | 16.10. | Ein Paket je Thema: Pakete können alte Pakete ablösen (`ersetzt`); alle Wichtel im Paket „Wichtel“ |
| 2.5.1 | 16.10. | Fehler behoben: Pakete wurden bei gleichzeitigen Anfragen manchmal halb geladen („has no attribute Figur“) |
| 2.6.0 | 16.10. | Pakete aufgeräumt: sechs Themenpakete; Paketkatalog mit Beschreibung, Modellen und Installieren-Knopf |
| 2.7.0 | 16.10. | Neues Themenpaket Formen; alte Einzelpakete werden nicht mehr geladen, die App zeigt das passende Themenpaket zum Installieren |
| 2.8.0 | 17.10. | Themenpaket Verkauf (Flaschenschild); Schrift kann € % ·; mehrzeilige Textfelder in Paketen |

## Pakete

| Paket | Versionen |
|---|---|
| Türschild (jetzt in Wohnen) | 1.0.0 (09.10.), 1.1.0 zweisprachig (10.10.) |
| Halloween | 1.0.0 (09.10.), 1.1.0 zweisprachig (10.10.), 1.2.0 mit Spinnennetz, Skelett, Fledermausgirlande, Süßigkeitenschale (11.10.), 1.3.0 nutzt Verzierungen, zwei Prüffehler behoben (15.10.) |
| Mehrlagig | 1.0.0 (10.10.), 1.1.0 mit Weihnachtsmann, Pick-up, Nussknacker (11.10.), 1.2.0 nutzt Verzierungen (15.10.) |
| Filigran (jetzt in Weihnachten) | 1.0.0 (11.10.), 1.1.0 Muster-Rezepte und Zufallsmuster (15.10.) |
| **Weihnachten** (früher Weihnachtsdeko) | 1.0.0 (11.10.), 1.1.0 nutzt Verzierungen (15.10.), 2.0.0 mit Filigran zusammengelegt (16.10.) |
| Verzierungen | 1.0.0 Ornament-Bibliothek, Zierstück, Zierleiste (15.10.), 1.1.0 mit Motiv-Figuren und Halloween-Formen für alle (15.10.), 1.2.0 Wichtel-Maßstab (16.10.), 1.3.0 Hinweise fürs Wichtel-Paket (16.10.), **2.0.0 heißt jetzt „Grundlagen“**, mit Passungstest aus Werkstatt (16.10.) |
| Umrandungen (jetzt in Wohnen) | 1.0.0 Bilderrahmen, Zierrahmen (15.10.) |
| **Wohnen** | 1.0.0 Bilderrahmen, Zierrahmen, Türschild in einem Paket (16.10.) |
| Wichtelmöbel (jetzt in Wichtel) | 1.0.0 Bank, Tisch mit Hockern, Bett (15.10.), 1.1.0 Wichtel-Maßstab (16.10.) |
| Wichteltür (jetzt in Wichtel) | 1.0.0 Tür, Fenster (15.10.), 1.1.0 Wichtel-Maßstab (16.10.) |
| Wichtelzubehör (jetzt in Wichtel) | 1.0.0 Leiter, Wegweiser, Wäscheleine (15.10.), 1.1.0 Wichtel-Maßstab (16.10.) |
| Wichtelwelt (jetzt in Wichtel) | 1.0.0 Wichtelzimmer auf Knopfdruck (16.10.) · 1.1.0 mit Schicht-Wichtel (16.10.) |
| Wichtelfiguren (jetzt in Wichtel) | 1.0.0 Schicht-Wichtel aus vier Lagen (16.10.) |
| Werkstatt (jetzt in Grundlagen) | 1.0.0 Passungstest (16.10.) |
| **Wichtel** | 1.0.0 alle Wichtel in einem Paket, neu mit Wichtelmarkt: Lebkuchenstand, Kreidetafel, Backstube, Briefkasten, Gartenzaun, Werkbank, Wegelaterne (16.10.), 1.0.1 lädt sicher bei parallelen Anfragen (16.10.) |
| **Formen** | 1.0.0 Steckkörper, Wellenfläche, Stapelvase (16.10.) |
| **Schmuck** | 1.0.0 Ohrhänger-Paare: zehn Motive, drei Stile, Zwischenteil (16.10.) |
| **Verkauf** | 1.0.0 Flaschenschild mit Logo, Preis, Grundpreis und Preisliste (17.10.) |

## Warum „Steckwerk“?

„Laserforge“ war als Name schon von anderen Produkten belegt und klang nah an Glowforge. Nach einer
Namens- und Markenrecherche fiel die Wahl am 10.10.2026 auf **Steckwerk**. Alte Pakete, Motive und
Einstellungen wurden beim ersten Start automatisch übernommen.
