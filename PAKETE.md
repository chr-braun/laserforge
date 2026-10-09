# Erweiterungspakete – der Laserforge-Paket-Standard (Version 1)

Mit Paketen kommen neue Modelle in Laserforge, ohne dass du die App neu installieren musst.
Ein Paket ist eine Datei mit der Endung **`.lfpaket`**. Technisch ist das ein ZIP mit einem
Ordner darin. Installierte Pakete überstehen jedes Laserforge-Update.

## Paket laden

- **Mac-App / Weboberfläche:** links unten „Erweiterungspakete“ aufklappen, **Paket laden …**
  anklicken und die `.lfpaket`-Datei wählen. Die neuen Modelle erscheinen sofort in der Gruppe
  „Pakete“ (oder in der Gruppe, die das Paket angibt). Mit „entfernen“ ist es wieder weg.
- **Kommandozeile:**

```
python3 cli.py --paket-installieren tuerschild-1.0.0.lfpaket
python3 cli.py --pakete                       # installierte Pakete anzeigen
python3 cli.py --model tuerschild -O "text=Familie|Huber"
python3 cli.py --paket-entfernen tuerschild
```

Beim Installieren wird jedes Modell des Pakets mit seinen Standardwerten gebaut und vom
Validator geprüft. Nur ein Paket, das komplett cut-ready ist, wird übernommen.

> **Sicherheit:** Pakete enthalten Python-Code, der mit deinen Rechten läuft. Lade nur Pakete aus
> einer Quelle, der du vertraust, z. B. deine eigenen.

Installiert wird in den Benutzerordner:

- macOS: `~/Library/Application Support/Laserforge/Pakete`
- Linux/Windows: `~/.laserforge/pakete`

Der Ordner `pakete/` neben dem Programm wird ebenfalls gelesen. Mit der Umgebungsvariable
`LASERFORGE_PAKETE` gibst du eigene Ordner an (mehrere mit `:` getrennt); in den ersten davon
wird dann auch installiert.

## Paket erstellen

```
python3 cli.py --paket-neu krippe --out meine-pakete      # Vorlage mit lauffähigem Beispielmodell
# … meine-pakete/krippe/krippe.py bearbeiten …
python3 cli.py --paket-pruefen meine-pakete/krippe         # bauen + validieren
python3 cli.py --paket-packen meine-pakete/krippe --out .  # → krippe-1.0.0.lfpaket
```

Ein vollständiges Beispiel liegt in `beispiel-pakete/tuerschild/` (fertig gepackt:
`beispiel-pakete/tuerschild-1.0.0.lfpaket`).

### Aufbau

```
krippe/
  paket.json      Steckbrief (Pflicht)
  krippe.py       ein Modell je Datei (Name = Modellname)
  stall.py        … beliebig viele Modelle
  LIES MICH.md    optional
```

### paket.json

| Feld | Pflicht | Bedeutung |
|---|---|---|
| `standard` | – | Version dieses Standards, derzeit `1` |
| `id` | ✓ | eindeutiger Name: Kleinbuchstaben, Ziffern, `_` (2–40 Zeichen) |
| `name` | ✓ | Anzeigename |
| `version` | ✓ | `1.0.0` – bei jeder Änderung erhöhen |
| `modelle` | ✓ | Liste der Modelldateien ohne `.py` |
| `autor` | – | wer es gebaut hat |
| `beschreibung` | – | ein Satz |
| `laserforge` | – | mindestens nötige Laserforge-Version, z. B. `1.5.0` |

### Ein Modell

Jede Modelldatei enthält zwei Dinge:

1. **`INFO`**: das Formular, mit denselben Bausteinen wie die eingebauten Modelle.

```python
from pakete import num, sel, txt, flag, integer
INFO = dict(
    label="Krippe", group="Pakete", desc="Stall mit Stern",
    params=[num("width", "Breite", 160, 80, 400),
            sel("stern", "Stern", [("gross", "groß"), ("klein", "klein")], "gross"),
            txt("text", "Text", "Frohe Weihnacht", section="Schrift und Beschriftung"),
            flag("schnee", "Schnee auf dem Dach", True)])
```

   - `num(key, label, default, min, max)` für Zahl in mm, `integer(...)` für ganze Zahl,
     `sel(key, label, [(wert, anzeige), …], default)` für Auswahl, `txt(...)` für Text und
     `flag(...)` für Schalter.
   - Optional sind `section="…"` (aufklappbare Gruppe), `when={"key": [werte]}` (nur sichtbar,
     wenn …), `help="…"` und `symbols=True` (Symbolknöpfe ♥ ★ ❄ 🎄).
   - Ab Laserforge 1.6.0 gibt es zwei Bausteine für Motive: `motiv(key, label, "stern")` wählt ein
     Motiv aus der Bibliothek (kommt als ID an), `motive(key, label, [...])` erlaubt frei platzierte
     Motive (kommen als Liste von `{id, x, y, groesse, drehung, spiegeln, art}` an). Die fertigen
     Helfer dafür stehen in `models/motivvorlagen.py`: `resolve(...)`, `cut_motifs(...)` und
     `engrave_motifs(...)`. Setze dann `"laserforge": "1.6.0"` in `paket.json`.

2. **`build(cfg, name=..., **parameter)`**: liefert eine `Assembly` oder eine Liste davon.
   - Jeder Parameter aus `INFO` kommt als gleichnamiges Argument an.
   - `cfg.T` ist die Materialstärke, `cfg.s(x)` skaliert ein Maß, `cfg.arc_tolerance` ist die
     Bogengenauigkeit.

### Regeln für cut-ready Teile

- Koordinaten in mm, y nach oben. Die Außenkontur läuft gegen den Uhrzeigersinn; `part.add_hole()`
  dreht Löcher selbst richtig.
- Gravuren über `part.add_engrave(punkte, closed)` oder kollisionsfrei über `models._deko`.
  Beispiele: `Canvas`, `sign` für Text mit Rahmen, `styled_line` für Zierlinien.
- Steckverbindungen werden wie in den eingebauten Modellen über `JointFeature` beschrieben
  (siehe `models/_stand.py` und `models/schwibbogen.py`). Die Teile werden mit
  `asm.connect("teil:feature", "teil:feature")` verbunden. Der Validator prüft dann
  Passung und Kerf.
- Unmögliche Eingaben meldest du mit `raise ValueError("verständlicher Text")`. Der Text erscheint
  so im Programm.
- Was du `asm.notes.append(...)` gibst, landet im Prüfbericht als Montagehinweis.

## Kompatibilität

Neue Laserforge-Versionen lesen alle Pakete mit `standard` ≤ ihrer eigenen Standardversion.
Ein Paket, das eine neuere Laserforge verlangt (`laserforge`), wird mit Hinweis übersprungen. Es
bricht nichts anderes.
