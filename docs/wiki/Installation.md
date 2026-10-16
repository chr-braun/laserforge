# Installation

## Mac-App (empfohlen)

1. [Steckwerk-2.5.1-macOS.zip](dateien/Steckwerk-2.5.1-macOS.zip) herunterladen (siehe [Downloads](Downloads.md)), entpacken und **Steckwerk** doppelklicken.
2. **Nur beim ersten Start:** macOS blockiert die App, weil sie nicht von Apple signiert ist. Dialog mit
   *Fertig* schließen, dann **Systemeinstellungen → Datenschutz & Sicherheit → Dennoch öffnen**.
   (Bis macOS 14: Rechtsklick auf die App → *Öffnen*.)
3. Steckwerk fragt, ob es sich in den **Programme-Ordner** installieren soll → *Installieren*.

> **Wichtig:** Steckwerk muss im Programme-Ordner liegen. Startest du es direkt aus „Downloads“, verschiebt
> macOS die App in einen temporären Ordner (App Translocation) und löscht ihn später wieder. Seit 1.5.1
> erkennt Steckwerk das und bietet die Installation erneut an.

Steckwerk öffnet sich dann im Standardbrowser. Links unten gibt es **Ordner öffnen** (`Dokumente/Steckwerk`)
und **Beenden**. Schließt du das Fenster, beendet sich Steckwerk nach ein paar Sekunden von selbst.

**Python:** Die App nutzt das Python 3 deines Macs (ab 3.8). Bei dir läuft es mit Homebrew-Python 3.13.
Fehlt Python, bietet die App die Command Line Tools von Apple an.

**Wo liegt was?**

| | Pfad |
|---|---|
| Einstellungen, Pakete, Motive | `~/Library/Application Support/Steckwerk` |
| Protokoll | `~/Library/Logs/Steckwerk.log` |
| Exporte („In Ordner speichern“) | `~/Dokumente/Steckwerk` |

Beim Umstieg von Laserforge auf Steckwerk (2.0.0) wurden Pakete, Motive, Einstellungen und der
Update-Schlüssel automatisch übernommen und die alte `Laserforge.app` ersetzt.

**Deinstallieren:** App in den Papierkorb, optional die Ordner oben löschen.

## Updates

Ab 1.7.0 aktualisiert sich Steckwerk selbst, siehe [Updates](Updates.md). Ausnahme: Von 1.7.0 auf 2.0.0
musste einmal von Hand installiert werden, weil der alte Updater ein Zip mit `Steckwerk.app` nicht kannte.

## Ohne Mac-App (jedes System)

```bash
cd steckwerk
python3 webui.py                 # Weboberfläche auf http://127.0.0.1:8765
python3 cli.py --konfigurator    # Frage-Antwort im Terminal
python3 cli.py --model wichtelhaus --out out
```

Optional: `python3 -m pip install matplotlib pytest pyyaml` für PNG-Vorschau, Tests und YAML-Configs.
Unter Windows gibt es keinen Installer, dort läuft `python steckwerk_app.py` bzw. `python webui.py`.

## Mac-App selbst bauen

```bash
python3 packaging/build_macos.py     # → dist/Steckwerk.app und dist/Steckwerk-<version>-macOS.zip
```
