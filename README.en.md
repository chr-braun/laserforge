# Steckwerk

[![Tests](https://github.com/chr-braun/steckwerk/actions/workflows/ci.yml/badge.svg)](https://github.com/chr-braun/steckwerk/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/chr-braun/steckwerk?label=Mac%20app)](https://github.com/chr-braun/steckwerk/releases/latest)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
[![License: MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)

[Deutsch](README.md) · **English**

Parametric, **validated** laser-cut SVGs for gnome houses, Christmas accessories, matching house series,
tree ornaments, candle arches, snowflakes and slot-together vehicles with turning wheels – extensible
with your own [packages](PAKETE.md). Cut-ready for CO2 and diode lasers (LightBurn, xTool Creative
Space, Glowforge).

- A **Mac app** you just double-click (`Steckwerk-2.2.1-macOS.zip` under
  [Releases](https://github.com/chr-braun/steckwerk/releases/latest)), a **web interface** in your browser
  (`python3 webui.py`), a question-and-answer **configurator** in the terminal or the plain
  **command line**.
- **German and English:** pick the language in Settings (⌘,) under *General*. Forms, check reports, assembly
  notes, error messages and update notes switch along; the Mac dialogs follow your system language.
- Pure Python (3.8+), standard library only. No CAD, no cloud – the web interface runs entirely on your
  own computer.
- Every file is **checked before it is written**. If there is a single error, nothing is written (and the
  web interface offers no download).

> Until version 1.7.0 the program was called Laserforge. Steckwerk 2.0.0 takes over your packages,
> motifs and settings automatically.

---

## Mac app

1. Unzip `Steckwerk-2.2.1-macOS.zip` and double-click **Steckwerk**.
2. **First start only:** macOS blocks apps that don't come from the App Store. Close the message with
   *Done*, then go to **System Settings → Privacy & Security** and click **Open Anyway** next to
   “Steckwerk was blocked”. (Up to macOS 14: right-click the app → *Open*.)
3. Steckwerk offers to **install itself into the Applications folder** → *Install*. From then on start it
   from Launchpad, Spotlight or the Dock; you can delete the unzipped copy.

Steckwerk opens in your default browser. Bottom left: **Open folder** (shows
`Documents/Steckwerk`, where *Save to folder* writes) and **Quit**. Close the window and Steckwerk quits
by itself after a few seconds.

**Python:** the app uses your Mac's Python 3 (3.8 or newer – Apple's *Command Line Tools*, python.org or
Homebrew). If it's missing, the app offers to install the Command Line Tools; open it again afterwards.

**Uninstall:** drag Steckwerk from Applications to the Trash. Settings live in
`~/Library/Application Support/Steckwerk`, the log in `~/Library/Logs/Steckwerk.log`.

## Without the Mac app

```bash
cd steckwerk
python3 webui.py                                    # web interface at http://127.0.0.1:8765
python3 webui.py --lan                              # reachable in your home network, e.g. from a tablet
python3 cli.py --model wichtelhaus --out out        # or straight from the command line
python3 -m pip install matplotlib pytest pyyaml     # optional: PNG preview, tests, YAML configs
```

On Windows and Linux, `python steckwerk_app.py` starts the same app as on the Mac.

The command line and the terminal configurator speak German; model names and option keys are German
words (`wichtelhaus` = gnome house, `schneeflocke` = snowflake, `-O schild="…"` = sign text).
`python3 cli.py --model wichtelhaus --options` lists every option of a model.

## Web interface

Since 2.1.0 the interface is laid out like a Mac app, light or dark like your system:

- **Sidebar (left):** every model by group; groups fold away. **Settings** (⌘,) at the bottom.
- **Toolbar (top):** model name with group and part count, the status (green *Cut-ready*, red on
  errors – click it for the check report and assembly notes), the material menu (quick thickness
  switch), the dice (*Randomise design*) and **Export…** (⌘E): everything as ZIP, only the sheet shown
  as SVG, or save to the Steckwerk folder.
- **Middle:** true-to-scale preview per sheet with a mm ruler (wood = material, black = cut,
  blue = engrave); a segmented control switches between sheets.
- **Inspector (right):** only the current model's values – *Size*, *Features*, *Motifs* and *Design*
  with collapsible groups. *Default* resets the model.
- **Settings:** *Material* (thickness, kerf, scale, cut or engrave windows, sheet size, layer colours),
  *Packages*, *Motifs*, *Updates* and *General* (language, light/dark, live preview). Esc closes.
- **Live preview** on: every change recalculates after half a second. Off: *Preview* or ⌘↩.

## Models

| Model | What you get |
|---|---|
| **wichtelhaus** | Gnome house with gable roof, windows, door and chimney; walls joined with finger joints, optional annex |
| **serie** | A series of gnome houses with varying architecture, reproducible via seed |
| **tannenbaum, schneemann, zaun, laterne, briefkasten, wichtel** | Accessories: tree, snowman, fence, lantern, mailbox, gnome – matched to the standard house |
| **ornament** | Tree ornament configurator: 23 shapes × 10 patterns, 12 border styles, name/year, flat or 3D |
| **schneeflocke** | Six-fold snowflakes, each one grown from its seed; optional 3D |
| **schwibbogen** | Candle arch with 1–11 candles and a paper-cut scene (village, forest, church) |
| **zug, fahrzeug** | Train set and slot-together vehicles (car, truck, locomotive, sleigh, bus, tractor) with turning wheels |
| **Own motifs** | Upload SVG or PNG and make stands, signs, pendants, coasters or silhouettes from them |

## Packages and updates

New models arrive as **`.swpaket`** packages: *Settings → Packages → Load package …* in the app. How to

build your own is described in [PAKETE.md](PAKETE.md) (German), including how to ship English texts
with a package (`UEBERSETZUNG`).

Under **Updates**, Steckwerk shows new program versions and packages from the update channel; one click
installs them. The Mac app checks the download's checksum, replaces itself and restarts. Your settings,
packages and motifs stay.

## Importing into LightBurn

1. **File → Import** the `.svg`. It carries real mm dimensions, LightBurn keeps the scale 1:1.
2. Layers by colour: **black = cut** (*Line* mode, full cut), **blue = engrave** (*Line* mode, low power –
   engravings are lines, including single-stroke lettering).
3. Enable “cut inner shapes first”.
4. **Don't** enable LightBurn's kerf offset – the compensation is already in the file. If you prefer to
   compensate in LightBurn, generate with `--kerf 0`.

**xTool Creative Space:** black → *Cut*, blue → *Score*. **Glowforge:** black → *Cut*, blue → *Score*.

## Kerf

The laser removes **kerf/2** on each side of the line. Steckwerk therefore grows outer contours by
kerf/2 and shrinks holes and slots by kerf/2, so the part ends up at its nominal size. Measure your kerf
by cutting a 20 × 20 mm square: `kerf = 20 − measured`. Joints too loose → raise kerf; too tight → lower it.

## The validator

Runs on every call: closed paths, no self-intersections, holes inside the outline, minimum web between
all cuts, engravings only on material, every tab against its slot (fit and kerf), all parts on the sheet.
Only when everything passes is a file written.

## Limits

- mm only; arcs are approximated with lines (0.05 mm tolerance).
- Lettering is engraved in a single-stroke font; unsupported characters are reported by name.
- The web interface is meant for your own computer or home network (no login).
- The Mac app isn't signed by Apple, hence the one-time approval under *Privacy & Security*.

## License

[MIT](LICENSE)
