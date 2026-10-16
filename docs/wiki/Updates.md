# Updates (seit 1.7.0)

## Für dich als Nutzer

![Updates in den Einstellungen](medien/updates.png)


Unter **Updates** (links unten in der Seitenleiste) zeigt Steckwerk neue Programmversionen und Pakete.

- Pakete installierst oder aktualisierst du mit einem Klick.
- Eine neue Programmversion lädt die Mac-App herunter, prüft sie über die Prüfsumme, ersetzt sich selbst
  im Programme-Ordner und startet neu. Einstellungen, Pakete und Motive bleiben.
- Beim Start prüft Steckwerk automatisch (abschaltbar). Gibt es Neues, steht die Anzahl am Eintrag.

Kommandozeile:

```bash
python3 cli.py --update-pruefen
python3 cli.py --update-paket halloween     # oder „alle“
python3 cli.py --update-schluessel <token>  # Lese-Schlüssel speichern („-“ = löschen)
python3 cli.py --update-kanal <URL>         # anderen Kanal nutzen
```

### Privates Repo

Solange das Repo privat ist, braucht Steckwerk einen **GitHub-Lese-Schlüssel**: auf GitHub unter
Settings → Developer settings → Fine-grained tokens einen Schlüssel nur für dieses Repo mit
„Contents: Read-only“ anlegen und in Steckwerk unter Updates → Einstellungen eintragen. Er liegt im
Schlüsselbund. Ist das Repo öffentlich, geht es ohne Schlüssel.

## Für dich als Herausgeber

Der Update-Kanal ist der Branch **`updates`** im Repo: `feed.json`, die neueste Mac-App und die Pakete.

```bash
python3 packaging/build_macos.py --out dist
git worktree add ../kanal updates
python3 packaging/update_kanal.py ../kanal --mac dist/Steckwerk-<version>-macOS.zip --paket meinpaket-1.0.0.swpaket
cd ../kanal && git add -A && git commit -m "Kanal: <version>" && git push origin updates
```

Die Update-Hinweise kommen aus `CHANGELOG.md` (deutsch) und `CHANGELOG.en.md` (englisch).
**Wichtig:** Jede neue Version und jedes Paket-Update muss in den Kanal, sonst sieht die App es nicht.

Aktueller Inhalt: Steckwerk 2.7.0, Grundlagen 2.0.0, Wohnen 1.0.0, Weihnachten 2.0.0,
Halloween 1.3.0, Mehrlagig 1.2.0, Wichtel 1.0.1, Formen 1.0.0, Schmuck 1.0.0.
