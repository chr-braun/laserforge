"""Kompatibilität: Bis 1.7 hieß Steckwerk „Laserforge“. Ältere Pakete schreiben noch
`from laserforge import …` – dieses Modul leitet auf steckwerk um."""
import sys

import steckwerk

sys.modules[__name__] = steckwerk
