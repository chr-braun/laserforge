# Eigene Motive (seit 1.6.0)

Du kannst eigene Bilder in Steckwerk holen und frei auf den Teilen platzieren.

## Importieren

Einstellungen → Motive → **Motiv hochladen …**

- **SVG** (am besten): gefüllte Flächen werden Konturen, Weiß ist ein Loch, Linien ohne Füllung werden
  Gravur. Text vorher in Pfade umwandeln.
- **PNG**: wird nachgezeichnet. Dunkel = Motiv, hell/transparent = Hintergrund; sonst „Farben umkehren“.
  JPG geht nicht, vorher als PNG speichern.

19 Motive sind schon eingebaut. Seit 2.3.0 kannst du Motive auch von einer KI zeichnen lassen, siehe
[KI-Funktionen](KI-Funktionen.md).

## Vorlagen

Aufsteller mit Sockel, Schild, Anhänger, Untersetzer und **Silhouette** (das Motiv selbst als Umriss, mit
Sockel, Öse oder ohne Fuß).

## Platzieren

- Mit der Maus verschieben, an der Ecke skalieren, am Punkt drehen (Shift = 15°-Schritte).
- Pfeiltasten schieben fein, Entf entfernt.
- Je Motiv: **ausschneiden**, **Umriss gravieren** oder **flächig gravieren**.

Steckwerk meldet, wenn ein Motiv über den Rand ragt, zu dicht an einem anderen sitzt oder zu feine Stellen
hat. Herausfallende Inseln stehen im Prüfbericht.

## Kommandozeile

```bash
python3 cli.py --motiv-import katze.svg --motiv-name "Unsere Katze"
python3 cli.py --motive                  # Bibliothek anzeigen
python3 cli.py --motiv-entfernen ID
python3 cli.py --model motiv_silhouette -O motiv=<id> -O fuss=sockel
```

Eigene Motive liegen unter `~/Library/Application Support/Steckwerk/Motive` (oder `$STECKWERK_MOTIVE`).
Pakete können Motive über `motiv(...)` und `motive(...)` nutzen.
