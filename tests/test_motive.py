"""Eigene Motive: SVG/PNG-Import, Bibliothek, Vorlagen (Aufsteller, Schild, Anhänger, Untersetzer, Silhouette)."""
import base64
import json
import math
import struct
import threading
import urllib.error
import urllib.request
import zlib

import pytest

import motive as mt
import service
from cli import run
from steckwerk import Config
from conftest import MATERIALS, assert_cut_ready
from models import motivvorlagen as mv


@pytest.fixture
def bib(tmp_path, monkeypatch):
    monkeypatch.setenv("STECKWERK_MOTIVE", str(tmp_path / "motive"))
    return tmp_path


def png(w, h, fn, rgba=False):
    """Kleines PNG (Graustufe oder RGBA) für die Tests erzeugen."""
    rows = []
    for y in range(h):
        if rgba:
            rows.append(b"\x00" + b"".join(bytes(fn(x, y)) for x in range(w)))
        else:
            rows.append(b"\x00" + bytes(fn(x, y) for x in range(w)))

    def chunk(t, b):
        return struct.pack(">I", len(b)) + t + b + struct.pack(">I", zlib.crc32(t + b) & 0xFFFFFFFF)
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 6 if rgba else 0, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(b"".join(rows)))
            + chunk(b"IEND", b""))


def holes_per_area(m):
    return sorted(len(f["loecher"]) for f in m["flaechen"])


# --------------------------------------------------------------------------------------------------
# SVG
# --------------------------------------------------------------------------------------------------

SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">{}</svg>'


@pytest.mark.parametrize("body, flaechen, loecher", [
    ('<path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09'
     'C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>', 1, [0]),
    ('<path fill-rule="evenodd" d="M50 5a45 45 0 1 0 .01 0zM50 25a25 25 0 1 0 .01 0z"/>', 1, [1]),
    ('<circle cx="30" cy="50" r="25"/><circle cx="65" cy="50" r="25"/>', 1, [0]),            # überlappend
    ('<rect width="100" height="100" fill="#fff"/><circle cx="50" cy="50" r="40"/>'
     '<circle cx="35" cy="40" r="8" fill="white"/><circle cx="65" cy="40" r="8" style="fill:#FFFFFF"/>', 1, [2]),
    ('<g transform="translate(50 50) rotate(45)"><rect x="-20" y="-20" width="40" height="40" rx="5"/></g>', 1, [0]),
    ('<path d="M2 50a40 40 0 1180 0A40 40 0 012 50z"/>', 1, [0]),                           # Bogen-Flags ohne Trenner
    ('<defs><path id="p" d="M0 0h20v20h-20z"/></defs><use href="#p" x="10" y="10"/><use href="#p" x="60" y="60"/>',
     2, [0, 0]),
    ('<polygon points="10,10 90,10 50,90"/><ellipse cx="50" cy="40" rx="10" ry="5" fill="#ffffff"/>', 1, [1]),
])
def test_svg_shapes(body, flaechen, loecher):
    m = mt.svg_to_motif(SVG.format(body).encode())
    assert len(m["flaechen"]) == flaechen
    assert holes_per_area(m) == sorted(loecher)
    assert max(m["w"], m["h"]) == pytest.approx(1.0)
    for f in m["flaechen"]:                                         # Außen gegen, Löcher im Uhrzeigersinn
        assert mt.area(f["aussen"]) > 0 and all(mt.area(h) < 0 for h in f["loecher"])


def test_svg_circle_is_round():
    m = mt.svg_to_motif(SVG.format('<circle cx="50" cy="50" r="40"/>').encode())
    r = [math.hypot(x, y) for x, y in m["flaechen"][0]["aussen"]]
    assert min(r) > 0.495 and max(r) < 0.501


def test_svg_strokes_become_lines():
    m = mt.svg_to_motif(SVG.format('<polyline points="0,0 10,10 20,0" fill="none" stroke="#000"/>').encode())
    assert not m["flaechen"] and len(m["linien"]) == 1


@pytest.mark.parametrize("data, msg", [
    (SVG.format('<text x="0" y="10">Hallo</text>').encode(), "nur Text"),
    (b'<?xml version="1.0"?><!DOCTYPE svg [<!ENTITY a "aaaa">]><svg xmlns="http://www.w3.org/2000/svg"/>', "Entity"),
    (b"<html></html>", "keine SVG"),
    (SVG.format("").encode(), "keine Formen"),
])
def test_svg_errors(data, msg):
    with pytest.raises(mt.MotivFehler, match=msg):
        mt.svg_to_motif(data)


# --------------------------------------------------------------------------------------------------
# PNG
# --------------------------------------------------------------------------------------------------

def _donut(x, y):
    r = math.hypot(x - 60, y - 50)
    return 0 if 15 < r < 40 or (abs(x - 140) < 10 and abs(y - 50) < 30) else 255


def test_png_grayscale_trace():
    m = mt.png_to_motif(png(180, 100, _donut))
    assert holes_per_area(m) == [0, 1]
    m2 = mt.png_to_motif(png(180, 100, lambda x, y: 255 - _donut(x, y)), invert=True)
    assert holes_per_area(m2) == [0, 1]


def test_png_alpha_cutout():
    def px(x, y):
        on = math.hypot(x - 40, y - 40) < 30
        return (200, 30, 30, 255) if on else (255, 255, 255, 0)
    m = mt.png_to_motif(png(80, 80, px, rgba=True))
    assert len(m["flaechen"]) == 1


@pytest.mark.parametrize("data, msg", [
    (b"\xff\xd8\xff\xe0" + b"0" * 20, "JPG"),
    (b"nicht", "keine PNG"),
    (png(20, 20, lambda x, y: 255), "kein Motiv"),
    (png(20, 20, lambda x, y: 0), "umkehren"),
])
def test_png_errors(data, msg):
    with pytest.raises(mt.MotivFehler, match=msg):
        mt.png_to_motif(data)


# --------------------------------------------------------------------------------------------------
# Bibliothek
# --------------------------------------------------------------------------------------------------

def test_library_import_list_remove(bib):
    builtin = len(mt.library())
    assert builtin >= 15 and mt.exists("stern") and mt.load("katze")["eingebaut"]
    m = mt.import_bytes(SVG.format('<circle cx="50" cy="50" r="40"/>').encode(), "Mein Kreis.svg")
    assert m["id"].startswith("mein-kreis-") and m["name"] == "Mein Kreis" and not m["eingebaut"]
    assert len(mt.library()) == builtin + 1
    p = bib / "bild.png"
    p.write_bytes(png(180, 100, _donut))
    m2 = mt.import_file(str(p), name="Donut")
    assert m2["quelle"] == "png"
    mt.remove(m["id"])
    assert not mt.exists(m["id"]) and mt.exists(m2["id"])
    with pytest.raises(mt.MotivFehler, match="Eingebaute"):
        mt.remove("stern")
    with pytest.raises(mt.MotivFehler, match="gibt es nicht"):
        mt.load("../etc/passwd")
    with pytest.raises(mt.MotivFehler, match="Nur SVG"):
        mt.import_bytes(b"GIF89a", "x.gif")


def test_cli_motive(bib, capsys, tmp_path):
    f = tmp_path / "herz.svg"
    f.write_text(SVG.format('<path d="M50 90 L10 40 A20 20 0 0 1 50 25 A20 20 0 0 1 90 40 Z"/>'))
    assert run(["--motiv-import", str(f), "--motiv-name", "Herzchen"]) == 0
    out = capsys.readouterr().out
    mid = out.split("importiert als ")[1].split()[0]
    assert run(["--motive"]) == 0 and mid in capsys.readouterr().out
    assert run(["--model", "motiv_silhouette", "-O", f"motiv={mid}", "--validate"]) == 0
    assert run(["--model", "motiv_aufsteller", "-O", 'motive=[{"id": "%s", "groesse": 50}]' % mid,
                "--validate"]) == 0
    assert run(["--motiv-entfernen", mid]) == 0
    assert run(["--motiv-import", str(tmp_path / "fehlt.svg")]) == 2


# --------------------------------------------------------------------------------------------------
# Parameter
# --------------------------------------------------------------------------------------------------

def _info(model, key):
    return next(p for p in service.MODEL_INFO[model]["params"] if p["key"] == key)


def test_coerce_motive():
    info = _info("motiv_aufsteller", "motive")
    v = service.coerce(info, '[{"id": "stern", "x": "1,5", "groesse": 40, "spiegeln": "ja"}]')
    assert v == [dict(id="stern", x=1.5, y=0.0, groesse=40.0, drehung=0.0, spiegeln=True, art="schnitt")]
    assert service.coerce(info, {"id": "herz"})[0]["groesse"] == 50
    for bad, msg in [("[{", "Liste"), ([{"id": "gibtsnicht"}], "gibt es nicht"),
                     ([{"id": "stern", "groesse": 1}], "groesse"), ([{"id": "stern", "art": "laser"}], "Art"),
                     ([{"id": "stern"}] * 13, "höchstens"), ([{"id": "stern", "x": "abc"}], "keine Zahl")]:
        with pytest.raises(ValueError, match=msg):
            service.coerce(info, bad)
    with pytest.raises(ValueError, match="gibt es nicht"):
        service.coerce(_info("motiv_silhouette", "motiv"), "gibtsnicht")


# --------------------------------------------------------------------------------------------------
# Vorlagen
# --------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("model", list(service.VORLAGEN))
@pytest.mark.parametrize("T, kerf", MATERIALS[:4])
def test_templates_default_cut_ready(model, T, kerf):
    cfg = Config(thickness=T, kerf=kerf)
    for asm in service.build_assemblies(model, {}, cfg):
        assert_cut_ready(asm, cfg)


@pytest.mark.parametrize("art", mv.ART_KEYS)
@pytest.mark.parametrize("mid", ["katze", "kuerbis", "schneemann", "fledermaus"])
def test_every_art(art, mid, cfg):
    asm = service.build_assemblies("motiv_aufsteller", {"motive": [{"id": mid, "y": 8, "groesse": 70, "art": art}]},
                                   cfg)[0]
    assert_cut_ready(asm, cfg)
    plate = asm.parts[0]
    base = service.build_assemblies("motiv_aufsteller", {"motive": []}, cfg)[0].parts[0]
    if art == "schnitt":
        assert len(plate.holes) > len(base.holes)
    else:
        assert len(plate.holes) == len(base.holes)
        assert len(plate.engrave) > len(base.engrave) + (20 if art == "flaeche" else 0)


@pytest.mark.parametrize("model, kw", [
    ("motiv_schild", dict(form=f, aufhaengung=a)) for f, _ in mv.FORMEN for a, _ in mv.AUFHAENGUNG
] + [("motiv_anhaenger", dict(form=f, size=s, text="Lea", motive=[{"id": "stern", "y": -s * 0.05, "groesse": s * (0.3 if f == "herz" else 0.45)}])) for f, _ in mv.FORMEN_ANHAENGER for s in (30, 120)]
  + [("motiv_untersetzer", dict(form=f, size=s)) for f, _ in mv.FORMEN_UNTERSETZER for s in (50, 160)]
  + [("motiv_aufsteller", dict(form=f, width=w, height=w, text="Hallo", sockel_text="Anna",
                                       motive=[{"id": "stern", "y": w * 0.1, "groesse": w * 0.4}]))
     for f, _ in mv.FORMEN_AUFSTELLER for w in (40, 200)])
def test_template_variants(model, kw, cfg):
    for asm in service.build_assemblies(model, kw, cfg):
        assert_cut_ready(asm, cfg)


@pytest.mark.parametrize("mid", ["katze", "geist", "glocke", "herz", "hexe", "totenkopf"])
@pytest.mark.parametrize("fuss", [f for f, _ in mv.FUSS])
def test_silhouette(mid, fuss, cfg):
    asms = service.build_assemblies("motiv_silhouette", {"motiv": mid, "fuss": fuss, "size": 110}, cfg)
    assert_cut_ready(asms[0], cfg)
    names = [p.name for p in asms[0].parts]
    assert ("silhouette_sockel" in names) == (fuss == "sockel")


def test_silhouette_inner_shapes_engraved(cfg):
    a = service.build_assemblies("motiv_silhouette", {"motiv": "geist", "innen": "gravur", "fuss": "keiner"}, cfg)[0]
    assert not a.parts[0].holes and len(a.parts[0].engrave) >= 3


def test_friendly_errors(cfg):
    with pytest.raises(ValueError, match="Motiv 1 .*Rand"):
        service.build_assemblies("motiv_anhaenger", {"motive": [{"id": "stern", "x": 25, "groesse": 30}]}, cfg)
    with pytest.raises(ValueError, match="Motiv 2 .*dicht"):
        service.build_assemblies("motiv_schild", {"motive": [{"id": "herz", "groesse": 50},
                                                             {"id": "stern", "x": 10, "groesse": 40}]}, cfg)


def test_islands_note(cfg):
    a = service.build_assemblies("motiv_aufsteller", {"motive": [{"id": "kuerbis", "groesse": 80}]}, cfg)[0]
    assert any("fallen beim Ausschneiden heraus" in n for n in a.notes)


def test_design_view():
    d = service.design({"model": "motiv_schild", "params": {"width": 150, "height": 100}})
    assert d["ok"] and d["cy"] == 50 and d["bbox"][2] == pytest.approx(75, abs=0.5)
    assert len(d["holes"]) == 2 and d["engrave"]
    assert not service.design({"model": "motiv_silhouette"})["ok"]


# --------------------------------------------------------------------------------------------------
# Weboberfläche
# --------------------------------------------------------------------------------------------------

def _post(url, obj):
    req = urllib.request.Request(url, json.dumps(obj).encode(),
                                 {"Content-Type": "application/json", "X-Steckwerk": "1"})
    try:
        return json.load(urllib.request.urlopen(req, timeout=60))
    except urllib.error.HTTPError as e:
        return json.load(e)


def test_webui_motive(bib):
    import webui
    srv = webui.make_server("127.0.0.1", 0, str(bib / "out"), quiet=True)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        base = f"http://127.0.0.1:{srv.server_address[1]}"
        schema = json.load(urllib.request.urlopen(base + "/api/schema", timeout=10))
        assert any(m["id"] == "stern" for m in schema["motive"])
        assert schema["models"]["motiv_aufsteller"]["group"] == "Eigene Motive"
        data = base64.b64encode(png(180, 100, _donut)).decode()
        d = _post(base + "/api/motiv-import", {"filename": "ring.png", "data": data})
        assert d["ok"] and d["id"].startswith("ring-") and any(m["id"] == d["id"] for m in d["motive"])
        g = _post(base + "/api/generate", {"model": "motiv_aufsteller",
                                          "params": {"motive": [{"id": d["id"], "groesse": 60, "art": "umriss"}]}})
        assert g["ok"], g
        bad = _post(base + "/api/motiv-import", {"filename": "x.jpg", "data": base64.b64encode(b"\xff\xd8\xff").decode()})
        assert not bad["ok"] and "JPG" in bad["error"]
        des = _post(base + "/api/motiv-design", {"model": "motiv_anhaenger", "params": {"size": 50}})
        assert des["ok"] and des["outline"]
        r = _post(base + "/api/motiv-entfernen", {"id": d["id"]})
        assert r["ok"] and not any(m["id"] == d["id"] for m in r["motive"])
        assert not _post(base + "/api/motiv-entfernen", {"id": "stern"})["ok"]
    finally:
        srv.shutdown()
        srv.server_close()
