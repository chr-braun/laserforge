"""Hilfsmodul _tuer.py dieses Pakets laden (eindeutiger Modulname je Ordner)."""
import importlib.util
import os
import sys
import zlib

_here = os.path.dirname(os.path.abspath(__file__))


def tuer():
    path = os.path.join(_here, "_tuer.py")
    key = "swpaket_wichteltuer_tuer_%08x" % zlib.crc32(path.encode())
    mod = sys.modules.get(key)
    if mod is None or getattr(mod, "__file__", None) != path:
        spec = importlib.util.spec_from_file_location(key, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[key] = mod
        spec.loader.exec_module(mod)
    return mod
