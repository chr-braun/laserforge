"""Hilfsmodule und Nachbarmodelle dieses Pakets laden (eindeutiger Modulname je Ordner)."""
import importlib.util
import os
import sys
import zlib

_here = os.path.dirname(os.path.abspath(__file__))


def modul(name: str):
    """<name>.py aus diesem Paketordner laden (einmal je Ordner, danach aus dem Zwischenspeicher)."""
    path = os.path.join(_here, name + ".py")
    key = "swpaket_wichtel_%s_%08x" % (name, zlib.crc32(path.encode()))
    mod = sys.modules.get(key)
    if mod is None or getattr(mod, "__file__", None) != path:
        spec = importlib.util.spec_from_file_location(key, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[key] = mod
        spec.loader.exec_module(mod)
    return mod


def moebel():
    return modul("_moebel")


def tuer():
    return modul("_tuer")


def markt():
    return modul("_markt")
