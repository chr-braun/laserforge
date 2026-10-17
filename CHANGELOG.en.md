# Changelog (English)

Notable changes to Steckwerk. The German [CHANGELOG.md](CHANGELOG.md) has the full history.

## 2.8.0 – 2026-10-17

- New theme package **Shop** 1.0.0 with the bottle tag: a price tag that hangs on the bottle neck or on a cord, with your logo (from "Import motifs") or a header line, price incl. VAT and the unit price per litre, which Steckwerk works out itself. A price list makes all tags at once.
- The font now also knows €, % and the middle dot ·.
- Text fields in packages can have several lines.

## 2.7.0 – 2026-10-16

- New theme package **Shapes** 1.0.0 with mathematical slot-together sculptures: slice body (sphere, egg, lens, onion dome, spinning top, fir tree or dome from crossed ribs), wave surface (egg-crate wave, saddle, hill, ripples, dunes, two peaks, cushion) and stacked vase (twisted vase or lantern from stacked layers, with a glass insert or dowel).
- Steckwerk no longer loads old single packages (Filigree, Borders, Workshop and the five elf packages). Settings → Packages shows for each one which theme package it now belongs to, with a button to install it. After that the old package disappears by itself, or you remove it directly.

## 2.6.0 – 2026-10-16

- Packages tidied up, now there is one package per theme: Basics, Home, Christmas, Halloween, Layered and Elves. Steckwerk removes the old single packages on its own when installing.
- Basics 2.0.0 (formerly Ornaments) now also contains the fit test from Workshop. Home 1.0.0 bundles picture frames, ornamental frames and the door sign. Christmas 2.0.0 brings Christmas decor and Filigree together.
- Settings → Packages is now a catalog: every package is shown with its description and models, and anything from the update channel that is still missing can be added straight away with "Install".

## 2.5.1 – 2026-10-16

- Fixed: package models (e.g. "Lace ornament") sometimes failed to load with "library of verzierungen cannot be loaded … has no attribute Figur". The interface loads packages from several requests at once; now each request waits until a package has finished loading.
- Elves 1.0.1 loads its helper modules the same protected way.

## 2.5.0 – 2026-10-16

- One package per theme: everything about elves now lives in the **Elves** package 1.0.0. Steckwerk
  removes the five separate packages on its own when installing it: elf furniture, elf door, elf
  accessories, elf world and elf figures. This uses the new `ersetzt` entry in `paket.json` (see PAKETE.md).
- New in the Elves package: **gingerbread stall** with striped awning, name sign, heart garland, counter and
  cobblestone base, plus gingerbread hearts, gingerbread men and candy canes.
- New: standing **chalkboard** and **bakery** with tray, pastry board, rolling pin, cookie cutters and cookies.
- New: **elf mailbox** with flag and letters, two-layer **garden fence**, **workbench** with vice and tools
  and a **lantern post** that slots together crosswise. Everything fits together in the elf scale.
- **Ornaments** 1.3.0 updates the elf-scale hints for the new package.

## Package updates – 2026-10-16

- **Elf figures** 1.0.0 – the **layered gnome**: a Scandinavian gnome in four layers to paint and glue
  together. Low hat (folded, pointed or with pompom) with engraved pattern (stars, hearts, stripes, Nordic
  zigzag), fur brim, big nose, flowing beard with engraved strands (long, round, curly or forked), mittens,
  boots and a dark shadow border. With lantern, heart, star on a stick, fir tree or present, and a base with
  name or a loop for hanging. 60 to 300 mm tall.
- **Elf world** 1.1.0 now uses the layered gnome as the figure in the elf room (from 60 mm; the simple
  slot-together figure is still available under "Figure").
- **Werkstatt** 1.0.0 – fit test: a comb with slots of slightly different widths and a test piece. Under each
  slot is the kerf that turns exactly this slot into the standard width. The value under the slot where the
  test piece sits snugly goes into the material profile.
- **Elf scale**: elf furniture, elf door and elf accessories 1.1.0 can size themselves to your elf figure
  (default 70 mm). Door, window, bench, table, bed, ladder, signpost and clothesline then fit together.
  With “Scale: custom sizes” you set everything yourself as before.
- **Wichtelwelt** 1.0.0 – an elf room at the push of a button: elf figure, door, window and furniture (optionally
  ladder, signpost and clothesline) in one scale, with your name on the door sign, bed and figure.
- **Verzierungen** 1.2.0 carries the shared elf scale. If the elf is too small for the material thickness,
  Steckwerk now says from which size it fits.

## Package updates – 2026-10-15

- **Verzierungen** 1.1.0 – the library now also carries the motif figures and the Halloween shapes that
  used to be duplicated across several packages.
- **Mehrlagig** 1.2.0, **Halloween** 1.3.0 and **Weihnachtsdeko** 1.1.0 use this library instead of their own
  copies. The parts stay the same, the packages get smaller, and ornament improvements reach every package
  at once. The sources now live in the repo under `paketquellen/`.
- **Halloween** 1.3.0 fixes two rare check failures: in the haunted castle with spider and the pumpkin with leaf,
  sharp wedges could upset the kerf compensation at some sizes.
- **Filigran** 1.1.0 – pattern recipes for the lace ornament: under “Recipe” you combine building blocks
  (petals, arches, spokes, zigzag, pearls, scrolls, stars, drops, hearts) from the inside out into your own
  pattern. “Random” rolls a new pattern for every seed and notes its recipe. The assistant can suggest
  recipes from a description.

## 2.4.0 – 2026-10-15

- Packages can now use other packages: `benoetigt` in `paket.json` lists them with a minimum version,
  `bibliothek` offers a package's own shapes and tools to all other packages. **Updates** installs
  required packages automatically, and a package that others still need cannot be removed.
- **Ornaments** 1.0.0 – the shared ornament library for all packages (rosettes, corner ornaments,
  borders, edges, cut-out rows, cut-out motifs, frame shapes) plus the models Ornament piece and Ornament strip.
- **Frames** 1.0.0 – picture frames (9 × 13 to 15 × 20 cm or custom, with base or keyhole) and ornamental
  frames with a sign and engraved text.
- **Elf furniture** 1.0.0 – bench with backrest, table with stools and a bed with engraved pillow and
  blanket, all slot-together.
- **Elf door** 1.0.0 – door with stone arch or wooden frame, step and name sign, plus a window with
  glazing bars, curtains, shutters and flower box.
- **Elf accessories** 1.0.0 – slot-together ladder, signpost with your own place names and a clothesline
  with tiny laundry.

## 2.3.0 – 2026-10-11

- Tidier sidebar: a search field at the top (⌘K or ⌘F) and your recently used models below it. Groups
  are split into "Templates" and "From packages", show their count and stay collapsed until you open
  them. The selected model's group is always open.
- Assistant in the inspector: a small language model on your computer (Ollama, e.g. qwen2.5:3b) turns a
  short description into matching values. Steckwerk clamps every number and drops anything unsuitable.
  "Undo" restores the previous values. Turn it on under Settings → Assistant.
- New: **Draw a motif …** in the sidebar. An image model draws your motif from a description. A slider
  sets the threshold, then it goes into the library as your own motif and straight into the template.
- Image sources: Ollama on the Mac (free, e.g. x/z-image-turbo) or OpenRouter with your own key. For
  OpenRouter there is a list of models recommended for laser motifs, with the estimated cost per image
  and this month's spending. You can set a monthly limit.
- The OpenRouter key is kept in the Keychain. Only the description is sent to OpenRouter.
- English interface: placeholder texts in input fields are now translated too.

## 2.2.1 – 2026-10-11

- Two new material profiles for delicate work: poplar plywood 1.5 mm and 2 mm (filigree), made for the
  Filigree and Multi-layer packages.

## 2.2.0 – 2026-10-11

- Material profiles for the xTool M2 (10 W and 20 W): poplar, basswood and birch 3 mm, poplar 4 mm, MDF 3 mm,
  grey board 2 mm and black acrylic 3 mm. A profile sets thickness and kerf and colours the SVG for
  xTool Creative Space: red = cut, blue = score.
- Each profile shows starting values for XCS (power, speed, passes), in the export sheet too.
- Your own profiles: save the current values under a name and enter your own laser values.
- The material menu in the toolbar switches straight between profiles.

## 2.1.0 – 2026-10-10

- New Mac-style interface, tidier and easier to find your way around: a sidebar with every model by
  group, a toolbar with status, material menu, dice and **Export…**, the sheet alone in the middle and
  the inspector on the right with only the current model's values (size, features with switches,
  motifs, collapsible design groups).
- Click the status for the check report and assembly notes; export opens its own sheet (ZIP, a single
  sheet as SVG, or save to the Steckwerk folder).
- Material, packages, motifs, updates, language, light/dark and live preview now live in the settings
  window (⌘,).
- Keyboard: ⌘, settings, ⌘E export, ⌘↩ preview, Esc closes.
- System font instead of web fonts – the interface no longer loads anything from the internet.

## 2.0.0 – 2026-10-10

- New name: Laserforge is now **Steckwerk**. On first start Steckwerk takes over your packages, motifs,
  settings and update key automatically, and replaces the old app in the Applications folder.
- German and English: choose the language at the top right. Form, check report, assembly notes, error
  messages and update notes then appear in English; the Mac dialogs follow your system language.
- Packages can bring their own English texts; the Halloween package 1.1.0 is fully bilingual.
- Packages are now called `.swpaket`; older `.lfpaket` files and packages using `from laserforge import …`
  keep working.

> Until version 1.7.0 the program was called Laserforge.

## 1.7.0 – 2026-10-10

- Updates inside the app: new program versions and packages from the update channel, installed with one click.

## 1.6.0 – 2026-10-09

- Own motifs: upload SVG or PNG files and turn them into stands, signs, pendants, coasters or silhouettes.
