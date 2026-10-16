"""Pakete, die andere Pakete brauchen (benoetigt/bibliothek, ab 2.4.0) und die mitgelieferten Paketquellen."""
import json
import os
import sys

import pytest

import pakete
import service
import updater
from steckwerk import Config
from conftest import assert_cut_ready

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "packaging"))
import update_kanal  # noqa: E402
QUELLEN = os.path.join(HERE, "paketquellen")
NEUE = ["verzierungen", "wohnen", "wichtel"]
ALTE_WICHTEL = ["wichtelmoebel", "wichteltuer", "wichtelzubehoer", "wichtelwelt", "wichtelfiguren"]
UMGESTELLT = ["ebenen", "halloween", "weihnacht"]                       # nutzen seit 2026-10-15 die Bibliothek
ALLE = ["verzierungen", "wohnen", "weihnacht", "halloween", "ebenen", "wichtel", "formen"]   # ein Paket je Thema


@pytest.fixture
def inst(tmp_path, monkeypatch):
    monkeypatch.setenv("STECKWERK_PAKETE", str(tmp_path / "inst"))
    monkeypatch.setenv("STECKWERK_DATEN", str(tmp_path / "daten"))
    yield tmp_path
    monkeypatch.delenv("STECKWERK_PAKETE")
    service.reload_pakete()


def test_manifeste():
    for pid in NEUE:
        m = pakete.read_manifest(os.path.join(QUELLEN, pid))
        assert m["id"] == pid and m["name_en"] and m["beschreibung_en"]
        if pid != "verzierungen":
            assert m["benoetigt"]["verzierungen"] in ("1.0.0", "1.1.0", "1.2.0", "1.3.0", "2.0.0")
    for pid in UMGESTELLT:
        m = pakete.read_manifest(os.path.join(QUELLEN, pid))
        assert m["benoetigt"]["verzierungen"] in ("1.1.0", "2.0.0")
        assert not [f for f in os.listdir(os.path.join(QUELLEN, pid)) if f in ("_kit.py", "_ebenen.py", "_figuren.py")]
    assert pakete.read_manifest(os.path.join(QUELLEN, "verzierungen"))["bibliothek"] == "bibliothek"


def test_abhaengigkeit_fehlt_und_entfernen(inst):
    with pytest.raises(pakete.PaketFehler, match="braucht zuerst das Paket"):
        pakete.install(os.path.join(QUELLEN, "wohnen"))
    pakete.install(os.path.join(QUELLEN, "verzierungen"))
    m, _ = pakete.install(os.path.join(QUELLEN, "wohnen"))
    assert m["id"] == "wohnen"
    with pytest.raises(pakete.PaketFehler, match="noch gebraucht von: Wohnen"):
        pakete.remove("verzierungen")
    pakete.remove("wohnen")
    pakete.remove("verzierungen")


def test_bibliothek_laden(inst):
    pakete.install(os.path.join(QUELLEN, "verzierungen"))
    Z = pakete.bibliothek("verzierungen")
    assert Z.VERSION == "2.0.0" and Z.F and Z.G and Z.WM and pakete.bibliothek("verzierungen") is Z
    cfg = Config()
    fig = Z.Figur().add(Z.kartusche(80, 50, "oval"))
    fig.merge(Z.ausschnitt("herz", 0, 25, 16))
    notes = []
    teil = Z.figur_teil(cfg, "probe", fig, notes)
    assert teil.holes and not notes
    b = Z.brett("brett", 40, 20, cfg.T, links=[(10, 6, "l", 1)], rechts=[(10, 6, "r", 2)])
    assert {f.id for f in b.features} == {"l", "r"}
    with pytest.raises(pakete.PaketFehler):
        pakete.bibliothek("gibtsnicht")


def test_updater_installiert_abhaengigkeit_mit(inst):
    pakete.install(os.path.join(QUELLEN, "verzierungen"))          # zum Prüfen beim Packen
    paths = [pakete.pack(os.path.join(QUELLEN, pid), str(inst / "pk"))[0] for pid in ("verzierungen", "wichtel")]
    pakete.remove("verzierungen")
    kanal = inst / "kanal"
    update_kanal.build(str(kanal), None, paths, today="2026-10-15")
    feed = json.loads((kanal / "feed.json").read_text())
    assert {p["id"]: p.get("benoetigt") for p in feed["pakete"]}["wichtel"] == {"verzierungen": "1.3.0"}
    os.environ["STECKWERK_UPDATE_KANAL"] = (kanal / "feed.json").as_uri()
    try:
        m = updater.install_paket("wichtel")
        assert m["id"] == "wichtel"
        assert set(updater.installed_pakete()) >= {"verzierungen", "wichtel"}
    finally:
        del os.environ["STECKWERK_UPDATE_KANAL"]


@pytest.mark.parametrize("pid", NEUE + UMGESTELLT)
def test_modelle_cut_ready(inst, pid):
    if pid != "verzierungen":
        pakete.install(os.path.join(QUELLEN, "verzierungen"))
    m, mods = pakete.load_folder(os.path.join(QUELLEN, pid))
    for cfg in (Config(), Config(thickness=4.0, kerf=0.15)):
        for name, mod in mods.items():
            params = {p["key"]: p["default"] for p in mod.INFO["params"]}
            asm = mod.build(cfg, **params)
            for a in asm if isinstance(asm, list) else [asm]:
                assert_cut_ready(a, cfg)


def test_filigran_rezepte(inst):
    pakete.install(os.path.join(QUELLEN, "verzierungen"))
    _, mods = pakete.load_folder(os.path.join(QUELLEN, "weihnacht"))
    FG = mods["spitzenschmuck"].FG
    assert list(FG.rezept_lesen("Blüten, perlen,BÖGEN")) == ["blueten", "perlen", "boegen"]
    with pytest.raises(ValueError, match="kenne"):
        FG.rezept_lesen("blüten, wolken")
    assert FG.rezept_zufall(7) == FG.rezept_zufall(7)
    cfg = Config()
    mod = mods["spitzenschmuck"]
    asm = mod.build(cfg, muster="rezept", rezept="ranken, herzen, zickzack", form="herz")
    assert_cut_ready(asm, cfg)
    asm = mod.build(cfg, muster="zufall", startwert=3, anzahl=2)
    assert len(asm.parts) == 2 and sum("Startwert" in n for n in asm.notes) == 2
    assert_cut_ready(asm, cfg)


@pytest.mark.parametrize("kerf", [0.1, 0.2])
def test_halloween_spitze_zwickel(inst, kerf):
    """Spukschloss mit Spinne und Kürbis mit Blatt: spitze Zwickel überstehen den Kerf-Versatz."""
    pakete.install(os.path.join(QUELLEN, "verzierungen"))
    _, mods = pakete.load_folder(os.path.join(QUELLEN, "halloween"))
    cfg = Config(thickness=3.0, kerf=kerf)
    assert_cut_ready(mods["spukschloss"].build(
        cfg, width=176.49808971447334, szene="friedhof", himmel="nichts", fledermaeuse=1, kuerbisse=1, spinne=True,
        variante=55, rahmen_deko="keine", text="Happy Halloween", schrift="breit", schreibweise="gross"), cfg)
    cfg = Config(thickness=5.0, kerf=kerf)
    assert_cut_ready(mods["kuerbis"].build(cfg, width=119.59090487445758, gesicht="froehlich", rippen=True, blatt=True,
                                           text="BOO!", schrift="normal", schreibweise="gross"), cfg)


def test_passungstest_werte(inst):
    pakete.install(os.path.join(QUELLEN, "verzierungen"))
    _, mods = pakete.load_folder(os.path.join(QUELLEN, "verzierungen"))
    pt = mods["passungstest"]
    w = pt.werte(0.2, 5, 0.05)
    assert [d for d, _ in w] == [-0.1, -0.05, 0.0, 0.05, 0.1]
    assert [k for _, k in w] == [0.3, 0.25, 0.2, 0.15, 0.1]
    assert all(k >= 0 for _, k in pt.werte(0.05, 7, 0.05))           # kein negativer Kerf
    cfg = Config(thickness=3.0, kerf=0.2)
    asm = pt.build(cfg)
    kamm = asm.parts[0]
    breiten = sorted({round(abs(a[0] - b[0]), 4) for a, b in zip(kamm.outline, kamm.outline[1:])
                      if abs(a[1] - b[1]) < 1e-9 and abs(a[1] - min(p[1] for p in kamm.outline if p[1] > 0)) < 1e-9})
    assert 3.0 in breiten and 3.15 in breiten and 2.85 in breiten


def test_wichtel_massstab(inst):
    pakete.install(os.path.join(QUELLEN, "verzierungen"))
    pakete.install(os.path.join(QUELLEN, "wichtel"))
    WM = pakete.bibliothek("verzierungen").WM
    bank = pakete.bibliothek("wichtel", "wichtelbank")
    assert bank.INFO["params"][0]["key"] == "massstab"
    assert {p["key"]: p.get("when") for p in bank.INFO["params"]}["sitzhoehe"] == {"massstab": ["frei"]}
    m = WM.wichtelmass("wichtelbank", 70, bank.INFO["params"])
    assert m["laenge"] == 70 and m["sitzhoehe"] == 23.8
    assert WM.wichtelmass("wichtelbank", 300, bank.INFO["params"])["laenge"] == 200     # Parametergrenze
    cfg = Config(thickness=5.0)
    with pytest.raises(ValueError, match="mindestens 70 mm"):
        bank.build(cfg, wichtel=50)
    asm = bank.build(Config(), massstab="frei", laenge=90)                              # eigene Maße bleiben
    assert asm.params["laenge"] == 90


def test_wichtelzimmer(inst):
    pakete.install(os.path.join(QUELLEN, "verzierungen"))
    _, mods = pakete.load_folder(os.path.join(QUELLEN, "wichtel"))
    cfg = Config()
    out = mods["wichtelzimmer"].build(cfg, wichtel=90, leiter=True, bett=False)
    namen = [a.name for a in out]
    assert namen == ["wichtelfigur", "wichteltuer", "wichtelfenster", "wichtelbank", "wichteltisch",
                     "wichtelleiter"]
    assert out[1].params["hoehe"] == 135.0 and out[3].params["laenge"] == 90.0
    for a in out:
        assert_cut_ready(a, cfg)
    assert "grund" in [p.name for p in out[0].parts]                                    # Schicht-Wichtel
    einfach = mods["wichtelzimmer"].build(cfg, wichtel=90, figur_art="einfach", tuer=False, fenster=False,
                                          bank=False, tisch=False, bett=False)
    assert "grund" not in [p.name for p in einfach[0].parts]
    klein = mods["wichtelzimmer"].build(cfg, wichtel=50, tuer=False, fenster=False, bank=False, tisch=False,
                                        bett=False)
    assert "mindestens 60 mm" in " ".join(klein[0].notes)
    with pytest.raises(ValueError, match="Bank, Tisch und Bett mindestens 75 mm"):
        mods["wichtelzimmer"].build(Config(thickness=5.0), wichtel=40)


@pytest.mark.parametrize("muetze,bart,zubehoer,stand", [
    ("umgeknickt", "lang", "laterne", "sockel"), ("spitz", "rund", "herz", "flach"),
    ("bommel", "lockig", "stern", "oese"), ("umgeknickt", "zwei", "tanne", "sockel"),
    ("spitz", "lang", "geschenk", "oese")])
def test_schichtwichtel(inst, muetze, bart, zubehoer, stand):
    pakete.install(os.path.join(QUELLEN, "verzierungen"))
    _, mods = pakete.load_folder(os.path.join(QUELLEN, "wichtel"))
    for cfg, g in ((Config(), 130), (Config(thickness=4.0, kerf=0.15), 70)):
        asm = mods["schichtwichtel"].build(cfg, groesse=g, muetze=muetze, bart=bart, zubehoer=zubehoer,
                                           stand=stand, name_text="Ida", muster="sterne")
        namen = [p.name for p in asm.parts]
        assert namen[:4] == ["grund", "koerper", "bart", "krempe"] and "faeustling_links" in namen
        assert ("standplatte" in namen) == (stand == "sockel")
        assert sum(len(p.engrave) for p in asm.parts) > 10                              # Strähnen, Muster, Fell
        assert_cut_ready(asm, cfg)


def test_wichtel_ein_paket_ersetzt_die_alten(inst):
    """Seit 2.5.0: „Wichtel“ ersetzt die fünf einzelnen Wichtel-Pakete – beim Installieren werden sie entfernt,
    liegen sie noch woanders, blendet Steckwerk sie aus."""
    pakete.install(os.path.join(QUELLEN, "verzierungen"))
    m = pakete.read_manifest(os.path.join(QUELLEN, "wichtel"))
    assert sorted(m["ersetzt"]) == sorted(ALTE_WICHTEL)
    for pid in ALTE_WICHTEL:
        assert not os.path.exists(os.path.join(QUELLEN, pid))
    alt = pakete.create("wichtelmoebel", str(inst / "alt"))
    pakete.install(alt)
    assert "wichtelmoebel" in updater.installed_pakete()
    _, lines = pakete.install(os.path.join(QUELLEN, "wichtel"))
    assert any("Entfernt: wichtelmoebel" in l for l in lines)
    have = updater.installed_pakete()
    assert "wichtel" in have and "wichtelmoebel" not in have
    os.environ["STECKWERK_PAKETE"] += os.pathsep + str(inst / "alt")             # alte Kopie an anderem Ort
    assert "wichtelmoebel" not in updater.installed_pakete()
    assert pakete.ersetzte()["wichtelmoebel"] == "wichtel"
    with pytest.raises(pakete.PaketFehler, match="ersetzt"):
        bad = inst / "bad"
        bad.mkdir()
        (bad / "paket.json").write_text(json.dumps(dict(id="x1", name="x", version="1.0.0", modelle=["a"],
                                                         ersetzt="wichtel")))
        (bad / "a.py").write_text("")
        pakete.read_manifest(str(bad))


MARKT = ["lebkuchenstand", "kreidetafel", "backstube", "wichtelpost", "gartenzaun", "werkbank", "wegelaterne"]


@pytest.mark.parametrize("T,kerf,wichtel", [(3.0, 0.2, 70), (4.0, 0.15, 80), (2.0, 0.1, 50), (3.0, 0.2, 140)])
def test_wichtelmarkt(inst, T, kerf, wichtel):
    pakete.install(os.path.join(QUELLEN, "verzierungen"))
    _, mods = pakete.load_folder(os.path.join(QUELLEN, "wichtel"))
    cfg = Config(thickness=T, kerf=kerf)
    for name in MARKT:
        mod = mods[name]
        params = {p["key"]: p["default"] for p in mod.INFO["params"]}
        params["wichtel"] = wichtel
        assert_cut_ready(mod.build(cfg, **params), cfg)


def test_wichtelmarkt_varianten(inst):
    pakete.install(os.path.join(QUELLEN, "verzierungen"))
    _, mods = pakete.load_folder(os.path.join(QUELLEN, "wichtel"))
    cfg = Config()
    stand = mods["lebkuchenstand"].build(cfg, dach="zacken", schmuck="herz", girlande=False, herzen=5,
                                         theke_text="Frisch")
    namen = [p.name for p in stand.parts]
    assert "rahmen" in namen and "grundplatte" in namen and sum(n.startswith("lebkuchenherz") for n in namen) == 5
    assert_cut_ready(stand, cfg)
    for form in ("bogen", "giebel", "gerade"):
        assert_cut_ready(mods["kreidetafel"].build(cfg, form=form, text="Heute|Plätzchen"), cfg)
    for kopf in ("spitz", "rund", "herz"):
        assert_cut_ready(mods["gartenzaun"].build(cfg, kopf=kopf, massstab="frei", laenge=200, hoehe=60), cfg)
    assert_cut_ready(mods["wichtelpost"].build(cfg, dach="rund", briefe=0, name_text=""), cfg)
    assert_cut_ready(mods["wegelaterne"].build(cfg, kopf="rund"), cfg)
    lat = mods["wegelaterne"].build(cfg)
    assert [f.kind for p in lat.parts for f in p.features] == ["halving", "halving"]
    with pytest.raises(ValueError, match="mindestens 70 mm"):
        mods["werkbank"].build(Config(thickness=5.0), wichtel=50)


def test_updater_wichtel_loest_alte_pakete_ab(inst):
    """Wer noch Wichtelmöbel & Co. hat, bekommt „Wichtel“ als Update angeboten; danach sind die alten weg."""
    pakete.install(os.path.join(QUELLEN, "verzierungen"))
    paths = [pakete.pack(os.path.join(QUELLEN, pid), str(inst / "pk"))[0] for pid in ("verzierungen", "wichtel")]
    pakete.install(pakete.create("wichtelmoebel", str(inst / "alt")))
    kanal = inst / "kanal"
    update_kanal.build(str(kanal), None, paths, today="2026-10-16")
    feed = json.loads((kanal / "feed.json").read_text())
    assert sorted({p["id"]: p for p in feed["pakete"]}["wichtel"]["ersetzt"]) == sorted(ALTE_WICHTEL)
    os.environ["STECKWERK_UPDATE_KANAL"] = (kanal / "feed.json").as_uri()
    try:
        info = {p["id"]: p for p in updater.check()["pakete"]}
        assert info["wichtel"]["status"] == "update" and info["wichtel"]["ersetzt"] == ["wichtelmoebel"]
        done = updater.install_alle_pakete()
        assert [m["id"] for m in done] == ["wichtel"]
        have = updater.installed_pakete()
        assert "wichtel" in have and "wichtelmoebel" not in have
    finally:
        del os.environ["STECKWERK_UPDATE_KANAL"]


def test_pakete_parallel_laden(inst):
    """Die Web-Oberfläche lädt Pakete aus mehreren Threads – kein Thread darf ein halb geladenes Modul sehen."""
    import threading
    for pid in ("verzierungen", "weihnacht", "halloween"):
        pakete.install(os.path.join(QUELLEN, pid))
    fehler = []

    def lauf():
        fehler.extend(err for _, _, _, err in pakete.discover() if err)
    for _ in range(3):
        for k in [k for k in sys.modules if k.startswith(("swbib_", "swpaket_"))]:
            del sys.modules[k]
        ts = [threading.Thread(target=lauf) for _ in range(4)]
        [t.start() for t in ts]
        [t.join() for t in ts]
    assert fehler == []


def test_ein_paket_je_thema():
    """Jedes Thema hat genau ein Paket; die zusammengelegten alten Pakete stehen in „ersetzt“."""
    assert sorted(d for d in os.listdir(QUELLEN) if os.path.isfile(os.path.join(QUELLEN, d, "paket.json"))) == sorted(ALLE)
    ersetzt = {}
    for pid in ALLE:
        m = pakete.read_manifest(os.path.join(QUELLEN, pid))
        assert m["beschreibung"] and m["beschreibung_en"] and m["name_en"]
        for r in m.get("ersetzt") or []:
            ersetzt[r] = pid
    assert ersetzt == {"filigran": "weihnacht", "umrandungen": "wohnen", "tuerschild": "wohnen",
                       "werkstatt": "verzierungen", **{a: "wichtel" for a in ALTE_WICHTEL}}


def test_zusammenlegen_entfernt_alte_pakete(inst):
    pakete.install(os.path.join(QUELLEN, "verzierungen"))
    pakete.install(os.path.join(HERE, "beispiel-pakete", "tuerschild-1.1.0.swpaket"))
    m, lines = pakete.install(os.path.join(QUELLEN, "wohnen"))
    have = {p for p in os.listdir(pakete.install_dir())}
    assert "wohnen" in have and "tuerschild" not in have
    assert any("tuerschild" in l for l in lines)
