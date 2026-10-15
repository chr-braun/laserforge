"""
Fledermaus-Girlande – Fledermäuse in vier Flügelhaltungen, wahlweise mit Kürbissen und Gespenstern.

Jede Figur hat zwei Löcher auf gleicher Höhe: Faden vorne durch das eine Loch hinein, hinten durch das
andere wieder heraus – so hängt sie gerade und rutscht nicht. Flügelknochen, Blattadern und Laken-
falten sind feine Schlitze, Fältchen und Rippen graviert.
"""
from __future__ import annotations

import os
import sys
from typing import List

from steckwerk import Assembly
from pakete import flag, integer, num, sel

_here = os.path.dirname(os.path.abspath(__file__))


def _sub(name: str):
    import importlib.util
    path = os.path.join(_here, name + ".py")
    key = "swpaket_halloween_" + name
    mod = sys.modules.get(key)
    if mod is None or getattr(mod, "__file__", None) != path:
        spec = importlib.util.spec_from_file_location(key, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[key] = mod
        spec.loader.exec_module(mod)
    return mod


SP = _sub("_spuk")

MISCHUNG = [("fledermaeuse", "nur Fledermäuse"), ("kuerbisse", "Fledermäuse und Kürbisse"),
            ("gespenster", "Fledermäuse und Gespenster"), ("alles", "Fledermäuse, Kürbisse und Gespenster")]
HALTUNG = [("gemischt", "abwechselnd (alle vier)")] + SP.POSEN

INFO = dict(
    label="Fledermaus-Girlande",
    group="Halloween",
    desc="Fledermäuse in vier Flügelhaltungen, auf Wunsch mit Kürbissen und Gespenstern – je zwei Löcher "
         "zum Auffädeln, mit feinen Flügelknochen, Gesichtern und Falten.",
    params=[
        integer("anzahl", "Anzahl Figuren", 7, 1, 24),
        num("groesse", "Größe", 80, 40, 150, help="Spannweite einer Fledermaus in mm"),
        sel("mischung", "Mischung", MISCHUNG, "alles"),
        sel("haltung", "Flügelhaltung", HALTUNG, "gemischt"),
        sel("gesicht", "Kürbisgesicht", [("klassisch", "klassisch"), ("gruselig", "gruselig")], "klassisch",
            when={"mischung": ["kuerbisse", "alles"]}),
        num("loch", "Lochdurchmesser", 3, 1.5, 6, step=0.5, help="für Faden, Schnur oder Draht"),
        flag("augen", "Augen und Gesichter ausschneiden", True),
    ],
)

UEBERSETZUNG = {"en": {
    "Fledermaus-Girlande": "Bat garland",
    "Fledermäuse in vier Flügelhaltungen, auf Wunsch mit Kürbissen und Gespenstern – je zwei Löcher "
    "zum Auffädeln, mit feinen Flügelknochen, Gesichtern und Falten.":
        "Bats in four wing positions, optionally with pumpkins and ghosts – two holes each for threading, "
        "with fine wing bones, faces and folds.",
    "Anzahl Figuren": "Number of figures", "Größe": "Size", "Spannweite einer Fledermaus in mm": "wingspan of a bat in mm",
    "Mischung": "Mix", "nur Fledermäuse": "bats only", "Fledermäuse und Kürbisse": "bats and pumpkins",
    "Fledermäuse und Gespenster": "bats and ghosts", "Fledermäuse, Kürbisse und Gespenster": "bats, pumpkins and ghosts",
    "Flügelhaltung": "Wing position", "abwechselnd (alle vier)": "alternating (all four)",
    "Segeln (Flügel ausgebreitet)": "gliding (wings spread)", "Flügel hoch": "wings up", "Flügel tief": "wings down",
    "In der Kurve (ein Flügel hoch)": "banking (one wing up)", "Kürbisgesicht": "Pumpkin face",
    "klassisch": "classic", "gruselig": "creepy", "Lochdurchmesser": "Hole diameter",
    "für Faden, Schnur oder Draht": "for thread, cord or wire",
    "Augen und Gesichter ausschneiden": "Cut out eyes and faces",
    "Faden vorne durch das linke Loch, hinten zum rechten Loch und dort wieder nach vorne führen – so hängen "
    "alle Figuren gerade. Zwischen den Figuren je einen Knoten setzen, damit nichts verrutscht.":
        "Thread in through the left hole from the front, along the back to the right hole and out to the front again "
        "– this keeps every figure level. Tie a knot between the figures so nothing slides.",
    "Tipp: Schwarz lasierte Fledermäuse, orange Kürbisse und weiße Gespenster vor einem hellen Fenster.":
        "Tip: black-stained bats, orange pumpkins and white ghosts in front of a bright window.",
    "Girlande: Anzahl muss zwischen 1 und 24 liegen": "Garland: number must be between 1 and 24",
    "Girlande: Größe muss zwischen 40 und 150 mm liegen": "Garland: size must be between 40 and 150 mm",
    "Girlande: Lochdurchmesser muss zwischen 1,5 und 6 mm liegen": "Garland: hole diameter must be between 1.5 and 6 mm",
    "Girlande: Loch ist zu groß für so kleine Figuren – Größe erhöhen oder Loch verkleinern":
        "Garland: the hole is too large for such small figures – increase the size or reduce the hole",
}}


def _folge(mischung: str, n: int) -> List[str]:
    extra = {"fledermaeuse": [], "kuerbisse": ["kuerbis"], "gespenster": ["gespenst"],
             "alles": ["kuerbis", "gespenst"]}[mischung]
    out, e = [], 0
    for i in range(n):
        if extra and i % 2 == 1:
            out.append(extra[e % len(extra)])
            e += 1
        else:
            out.append("fledermaus")
    return out


def build(cfg, name: str = "fledermausgirlande", anzahl: int = 7, groesse: float = 80.0, mischung: str = "alles",
          haltung: str = "gemischt", gesicht: str = "klassisch", loch: float = 3.0, augen: bool = True):
    from models import _deko as dk
    anzahl = int(anzahl)
    if not 1 <= anzahl <= 24:
        raise ValueError("Girlande: Anzahl muss zwischen 1 und 24 liegen")
    S = cfg.s(groesse)
    if not 40 <= S <= 150:
        raise ValueError("Girlande: Größe muss zwischen 40 und 150 mm liegen")
    if not 1.5 <= loch <= 6:
        raise ValueError("Girlande: Lochdurchmesser muss zwischen 1,5 und 6 mm liegen")
    dk.check_choice("Mischung", mischung, MISCHUNG)
    dk.check_choice("Flügelhaltung", haltung, HALTUNG)
    dk.check_choice("Kürbisgesicht", gesicht, [("klassisch", ""), ("gruselig", "")])
    if loch > 0.06 * S + 1.0:
        raise ValueError("Girlande: Loch ist zu groß für so kleine Figuren – Größe erhöhen oder Loch verkleinern")
    asm = Assembly(name, params=dict(anzahl=anzahl, groesse=S, mischung=mischung, haltung=haltung, loch=loch))
    notes: List[str] = []
    posen = [p for p, _ in SP.POSEN]
    nb = 0
    for i, art in enumerate(_folge(mischung, anzahl)):
        if art == "fledermaus":
            pose = posen[nb % 4] if haltung == "gemischt" else haltung
            nb += 1
            fig, holes = SP.fledermaus(S, pose, cfg, augen)
            tag = f"fledermaus_{pose}"
        elif art == "kuerbis":
            fig, holes = SP.kuerbis(0.62 * S, cfg, gesicht if augen else "ohne")
            tag = "kuerbis"
        else:
            fig, holes = SP.gespenst(0.70 * S, cfg)
            if not augen:
                fig.ops = [o for o in fig.ops if o[0] == "+"]
            tag = "gespenst"
        part = SP.teil(f"{name}_{i + 1:02d}_{tag}", fig, cfg, notes, [(x, y, loch) for x, y in holes])
        SP.gravur(part, getattr(fig, "gravur", []), cfg.seed + i)
        asm.parts.append(part)
    for t in dict.fromkeys(notes):
        asm.notes.append(t)
    asm.notes.append("Faden vorne durch das linke Loch, hinten zum rechten Loch und dort wieder nach vorne führen – "
                     "so hängen alle Figuren gerade. Zwischen den Figuren je einen Knoten setzen, damit nichts "
                     "verrutscht.")
    asm.notes.append("Tipp: Schwarz lasierte Fledermäuse, orange Kürbisse und weiße Gespenster vor einem hellen Fenster.")
    return asm
