# KI-Funktionen (seit 2.3.0)

Die Idee: Ein Sprachmodell liefert nur einen **Bauplan** – Werte oder ein Bild. Die Geometrie rechnet
Steckwerk selbst und prüft sie wie immer. So geht nichts schief, auch wenn das Modell mal danebenliegt.

## Assistent im Inspektor

![Einstellungen → Assistent](medien/2.3-einstellungen.png)


Du beschreibst kurz, was du willst („zierlicher Stern, 12 cm, sehr fein“), und ein kleines Modell auf
deinem Rechner füllt die Werte des gewählten Modells aus. Steckwerk grenzt jede Zahl ein und verwirft
Unpassendes. **Rückgängig** stellt die alten Werte wieder her.

Einrichten:

1. Ollama installieren (ollama.com).
2. `ollama pull qwen2.5:3b` (oder `qwen2.5:7b`) – die halten sich zuverlässig ans Datenformat.
3. Einstellungen → **Assistent** → einschalten.

Steckwerk spricht nur mit einem Ollama auf diesem Rechner oder im eigenen Netz.

## Motiv zeichnen …

![Motiv zeichnen](medien/2.3-motiv-zeichnen.png)


Unten in der Seitenleiste. Ein Bildmodell zeichnet nach deiner Beschreibung eine Silhouette, einen
Scherenschnitt oder eine Strichzeichnung. Mit dem **Schwellen-Regler** stellst du ein, was schwarz wird.
**Als Motiv übernehmen** legt es in die [Motiv-Bibliothek](Eigene-Motive.md) und setzt es sofort in die
Vorlage (bei Bedarf in die Silhouette).

### Bildquellen

**Ollama (lokal, kostenlos):** `ollama pull x/z-image-turbo`. Bildmodelle laufen in Ollama bisher nur auf
dem Mac und gelten noch als experimentell.

**OpenRouter (mit eigenem Schlüssel):** Schlüssel von openrouter.ai unter Einstellungen → Assistent
eintragen. Er liegt im Schlüsselbund, an OpenRouter geht nur die Beschreibung.

Empfohlene Modelle (Kosten pro Bild geschätzt, Stand Oktober 2026):

| Modell | ca. Kosten | Warum |
|---|---|---|
| FLUX.2 Klein ★ (voreingestellt) | 0,014 $ | günstig, klare Formen |
| Recraft V4.1 Vector ★ | 0,08 $ | liefert direkt SVG, sauberste Kanten |
| Gemini 2.5 Flash Image | 0,04 $ | versteht deutsche Beschreibungen gut |
| Recraft V4.1, FLUX.2 Pro, GPT Image 1 Mini | je nach Modell | weitere Auswahl |

Steckwerk lädt die Preise beim Öffnen frisch, zeigt vor jedem Bild die Schätzung und danach die echten
Kosten und deine Monatssumme. Ein **Monatslimit** kannst du selbst setzen.

## Hinweis

Getestet wurde mit nachgebautem Ollama und OpenRouter. Echte Bilder konnten aus der Cloud-Umgebung nicht
erzeugt werden – der erste echte Test passiert also bei dir am Mac.
