"""
Bild-Werkstatt – ein Bildmodell zeichnet ein Motiv, Steckwerk macht daraus Schnittkonturen.

Zwei Quellen:
  * Ollama auf diesem Rechner (z. B. x/z-image-turbo, x/flux2-klein) – kostenlos, nichts verlässt das Netz.
  * OpenRouter (Cloud) – nur mit eigenem Schlüssel; die Beschreibung geht dann an OpenRouter und den Anbieter
    des gewählten Modells. Kosten je Bild werden vorher geschätzt und nachher wie gemeldet mitgezählt.

Das Bild selbst wird hier nicht verarbeitet: die Oberfläche zeigt es an, macht es mit einer Schwelle
schwarz-weiß und übernimmt es über den normalen Motiv-Import (SVG direkt, Rasterbilder als PNG).
"""
from __future__ import annotations

import base64
import json
import os
import ssl
import subprocess
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

import assistent

OPENROUTER = os.environ.get("STECKWERK_OPENROUTER") or "https://openrouter.ai/api/v1"     # zum Testen umlenkbar
KEYCHAIN_KONTO = "openrouter"
MAX_BILD = 24 * 1024 * 1024
TIMEOUT = 300.0
MAX_PROMPT = 600

STANDARD_OLLAMA = "x/z-image-turbo"
STANDARD_OPENROUTER = "black-forest-labs/flux.2-klein-4b"

# Für Lasermotive empfohlen (Reihenfolge = Vorschlag). Preise holt die Oberfläche live von OpenRouter.
EMPFOHLEN = [
    ("black-forest-labs/flux.2-klein-4b", "Am günstigsten, schnell, klare Formen"),
    ("recraft/recraft-v4.1-vector", "Liefert gleich Vektoren (SVG) – die saubersten Kanten"),
    ("recraft/recraft-v4.1", "Grafik- und Illustrationsstil, sehr sauber"),
    ("google/gemini-2.5-flash-image", "Versteht deutsche Beschreibungen gut"),
    ("black-forest-labs/flux.2-pro", "Mehr Details bei Figuren und Szenen"),
    ("openai/gpt-image-1-mini", "Gut bei Symbolen und Schrift-nahen Formen"),
]

STILE = {
    "silhouette": ("Silhouette",
                   "a single solid black silhouette on a pure white background, one connected shape, bold simple "
                   "outline, no inner details"),
    "scherenschnitt": ("Scherenschnitt",
                       "a traditional black paper-cut (Scherenschnitt) on a pure white background, black shapes all "
                       "connected to each other, decorative cut-out openings, no thin lines thinner than the "
                       "white gaps"),
    "linien": ("Strichzeichnung (Gravur)",
               "clean black line art on a pure white background, uniform medium line width, closed shapes, "
               "coloring-book style"),
}
STIL_ENDE = ("Flat 2D stencil for laser cutting, pure black and white only, no gray, no gradients, no shading, "
             "no shadows, no texture, no text, no frame or border, motif centered with white margin.")


class BildFehler(RuntimeError):
    pass


# --- Einstellungen --------------------------------------------------------------------------------

def _path() -> str:
    import updater
    return os.path.join(updater.data_dir(), "bilder.json")


def _read() -> Dict[str, Any]:
    try:
        with open(_path(), encoding="utf-8") as fh:
            d = json.load(fh)
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def _write(d: Dict[str, Any]) -> None:
    path = _path()
    tmp = path + ".tmp"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(d, fh, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def get_key() -> str:
    import updater
    if updater._use_keychain():
        r = subprocess.run(["security", "find-generic-password", "-s", updater.KEYCHAIN, "-a", KEYCHAIN_KONTO, "-w"],
                           capture_output=True, text=True)
        return r.stdout.strip() if r.returncode == 0 else ""
    return str(_read().get("key") or "")


def set_key(key: str) -> None:
    import updater
    key = key.strip()
    if key and (len(key) > 300 or any(c.isspace() for c in key)):
        raise BildFehler("Der Schlüssel sieht nicht richtig aus – bei OpenRouter unter „Keys“ kopieren")
    if updater._use_keychain():
        subprocess.run(["security", "delete-generic-password", "-s", updater.KEYCHAIN, "-a", KEYCHAIN_KONTO],
                       capture_output=True)
        if key:
            r = subprocess.run(["security", "add-generic-password", "-s", updater.KEYCHAIN, "-a", KEYCHAIN_KONTO,
                                "-w", key, "-U"], capture_output=True, text=True)
            if r.returncode != 0:
                raise BildFehler("Schlüssel ließ sich nicht im Schlüsselbund speichern: " + r.stderr.strip())
        return
    d = _read()
    if key:
        d["key"] = key
    else:
        d.pop("key", None)
    _write(d)


def _monat() -> str:
    return time.strftime("%Y-%m")


def settings() -> Dict[str, Any]:
    """Für die Oberfläche – den Schlüssel selbst gibt es nie zurück."""
    d = _read()
    k = d.get("kosten") if isinstance(d.get("kosten"), dict) else {}
    m = k.get(_monat()) if isinstance(k.get(_monat()), dict) else {}
    return dict(quelle=d.get("quelle") if d.get("quelle") in ("ollama", "openrouter") else "ollama",
                ollama_modell=str(d.get("ollama_modell") or STANDARD_OLLAMA),
                openrouter_modell=str(d.get("openrouter_modell") or STANDARD_OPENROUTER),
                key_gesetzt=bool(get_key()), limit=float(d.get("limit") or 0),
                monat=dict(kosten=round(float(m.get("kosten") or 0), 4), bilder=int(m.get("bilder") or 0)),
                stile=[dict(value=k2, label=v[0]) for k2, v in STILE.items()],
                empfohlen=[dict(id=i, warum=w) for i, w in EMPFOHLEN])


def _modellname(m: Any) -> str:
    m = str(m or "").strip()
    if not m or len(m) > 120 or any(c.isspace() for c in m):
        raise BildFehler("Modellname ungültig")
    return m


def save_settings(quelle: Optional[str] = None, ollama_modell: Optional[str] = None,
                  openrouter_modell: Optional[str] = None, key: Optional[str] = None,
                  limit: Optional[float] = None) -> Dict[str, Any]:
    d = _read()
    if quelle is not None:
        if quelle not in ("ollama", "openrouter"):
            raise BildFehler("Quelle unbekannt")
        d["quelle"] = quelle
    if ollama_modell is not None:
        d["ollama_modell"] = _modellname(ollama_modell)
    if openrouter_modell is not None:
        d["openrouter_modell"] = _modellname(openrouter_modell)
    if limit is not None:
        try:
            d["limit"] = max(0.0, min(1000.0, float(limit)))
        except (TypeError, ValueError):
            raise BildFehler("Monatslimit ungültig")
    _write(d)
    if key is not None:
        set_key(key)
    return settings()


def _buchen(kosten: float) -> Dict[str, Any]:
    d = _read()
    k = d.get("kosten") if isinstance(d.get("kosten"), dict) else {}
    m = k.get(_monat()) if isinstance(k.get(_monat()), dict) else {}
    m = dict(kosten=float(m.get("kosten") or 0) + max(0.0, kosten), bilder=int(m.get("bilder") or 0) + 1)
    k[_monat()] = m
    d["kosten"] = {mon: k[mon] for mon in sorted(k)[-12:]}
    _write(d)
    return dict(kosten=round(m["kosten"], 4), bilder=m["bilder"])


# --- Prompt ---------------------------------------------------------------------------------------

def prompt(beschreibung: str, stil: str = "silhouette") -> str:
    beschreibung = " ".join((beschreibung or "").split())
    if not beschreibung:
        raise BildFehler("Beschreibe kurz das Motiv – z. B. „Reh im Sprung“ oder „Eule auf einem Ast“")
    if len(beschreibung) > MAX_PROMPT:
        raise BildFehler(f"Beschreibung bitte kürzer (höchstens {MAX_PROMPT} Zeichen)")
    s = STILE.get(stil) or STILE["silhouette"]
    return f"Motif: {beschreibung}. Style: {s[1]}. {STIL_ENDE}"


# --- OpenRouter -----------------------------------------------------------------------------------

def _https(req: urllib.request.Request, timeout: float, limit: int) -> bytes:
    import updater
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=updater._ssl_context()) as r:
            data = r.read(limit + 1)
    except urllib.error.HTTPError as e:
        try:
            err = json.loads(e.read(8192).decode("utf-8", "replace")).get("error")
            msg = (err.get("message") if isinstance(err, dict) else str(err or "")) or ""
        except Exception:
            msg = ""
        if e.code == 401:
            raise BildFehler("OpenRouter lehnt den Schlüssel ab – unter Einstellungen → Assistent neu eintragen")
        if e.code == 402:
            raise BildFehler("Bei OpenRouter ist kein Guthaben mehr frei – unter openrouter.ai/credits aufladen")
        if e.code == 404:
            raise BildFehler("OpenRouter kennt dieses Modell nicht (mehr) – bitte ein anderes wählen")
        if e.code == 429:
            raise BildFehler("OpenRouter bremst gerade – in einer Minute nochmal versuchen")
        if e.code in (400, 403) and msg:
            raise BildFehler(f"OpenRouter: {msg[:200]}")
        raise BildFehler(f"OpenRouter meldet Fehler {e.code}" + (f": {msg[:200]}" if msg else ""))
    except ssl.SSLError as e:
        raise BildFehler(f"Sichere Verbindung zu OpenRouter fehlgeschlagen ({e.reason or e})")
    except (urllib.error.URLError, OSError) as e:
        reason = getattr(e, "reason", e)
        if "timed out" in str(reason):
            raise BildFehler("OpenRouter antwortet nicht rechtzeitig – nochmal versuchen")
        raise BildFehler(f"Keine Verbindung zu OpenRouter ({reason}). Bist du online?")
    if len(data) > limit:
        raise BildFehler("Antwort zu groß")
    return data


def _num(v: Any) -> float:
    try:
        f = float(v)
        return f if f > 0 else 0.0
    except (TypeError, ValueError):
        return 0.0


def schaetzen(pricing: Dict[str, Any]) -> float:
    """Grobe Kosten (USD) für ein Bild mit etwa 1 Megapixel aus OpenRouters Preisangaben je Token.

    Bildmodelle rechnen ~4096 Bild-Token je Megapixel ab, Sprach-Bild-Modelle (Gemini, GPT) ~1300."""
    out = _num(pricing.get("image_output")) or _num(pricing.get("image_token"))
    if not out:
        return 0.0
    llm = _num(pricing.get("prompt")) > 0 or _num(pricing.get("completion")) > 0
    tokens = 1300 if llm else 4096
    return round(out * tokens + _num(pricing.get("prompt")) * 120, 4)


_cache: Dict[str, Any] = {}


def openrouter_modelle(neu: bool = False) -> List[Dict[str, Any]]:
    """Bildmodelle von OpenRouter mit geschätzten Kosten je Bild, Empfehlungen zuerst."""
    if not neu and _cache.get("t", 0) > time.time() - 3600:
        return _cache["m"]
    import updater
    req = urllib.request.Request(OPENROUTER + "/models?output_modalities=image",
                                 headers={"User-Agent": f"Steckwerk/{updater.__version__}"})
    d = json.loads(_https(req, 30, 8 * 1024 * 1024).decode("utf-8"))
    warum = dict(EMPFOHLEN)
    out = []
    for m in d.get("data", []):
        mid = str(m.get("id") or "")
        arch = m.get("architecture") or {}
        if not mid or "image" not in (arch.get("output_modalities") or []) or mid.startswith("openrouter/"):
            continue
        out.append(dict(id=mid, name=str(m.get("name") or mid), kosten=schaetzen(m.get("pricing") or {}),
                        svg="vector" in mid, empfohlen=mid in warum, warum=warum.get(mid, "")))
    reihe = [i for i, _ in EMPFOHLEN]
    out.sort(key=lambda m: (reihe.index(m["id"]) if m["id"] in warum else 99, m["kosten"] or 9, m["id"]))
    _cache.update(t=time.time(), m=out)
    return out


def _openrouter(text: str, modell: str, key: str, timeout: float) -> Dict[str, Any]:
    import updater
    body = json.dumps({"model": modell, "prompt": text, "aspect_ratio": "1:1"}).encode("utf-8")
    req = urllib.request.Request(OPENROUTER + "/images", data=body, method="POST", headers={
        "Authorization": "Bearer " + key, "Content-Type": "application/json",
        "User-Agent": f"Steckwerk/{updater.__version__}", "X-Title": "Steckwerk"})
    d = json.loads(_https(req, timeout, MAX_BILD).decode("utf-8"))
    items = d.get("data") or []
    if not items or not isinstance(items[0], dict) or not items[0].get("b64_json"):
        raise BildFehler("OpenRouter hat kein Bild geliefert – Beschreibung umformulieren oder anderes Modell")
    usage = d.get("usage") or {}
    return dict(b64=str(items[0]["b64_json"]), typ=str(items[0].get("media_type") or ""),
                kosten=_num(usage.get("cost")))


# --- Ollama ---------------------------------------------------------------------------------------

def ollama_modelle(url: Optional[str] = None) -> List[str]:
    """Installierte Ollama-Modelle, die nach Bildmodell aussehen."""
    names = assistent.status(url)["modelle"]
    keys = ("image", "flux", "diffusion", "sdxl", "stable", "imagen", "z-image")
    return [n for n in names if any(k in n.lower() for k in keys)]


def _ollama(text: str, modell: str, url: Optional[str], timeout: float) -> Dict[str, Any]:
    payload = {"model": modell, "prompt": text, "stream": False, "width": 1024, "height": 1024}
    d = assistent._call(url or assistent.settings()["url"], "/api/generate", payload, timeout=timeout,
                        limit=MAX_BILD)
    b64 = d.get("image") or (d.get("images") or [None])[0]
    if not b64 and d.get("response"):
        raise BildFehler(f"„{modell}“ ist ein Sprachmodell und zeichnet keine Bilder – im Terminal z. B. "
                         f"„ollama pull {STANDARD_OLLAMA}“ (Ollama-App auf dem Mac, aktuelle Version)")
    if not b64:
        raise BildFehler("Ollama hat kein Bild geliefert – ist die Ollama-App aktuell?")
    return dict(b64=str(b64), typ="", kosten=0.0)


# --- Erzeugen -------------------------------------------------------------------------------------

def _typ(raw: bytes, typ: str) -> str:
    if raw[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if raw[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
        return "image/webp"
    head = raw[:400].lstrip().lower()
    if head.startswith(b"<?xml") or head.startswith(b"<svg") or b"<svg" in head:
        return "image/svg+xml"
    if typ in ("image/png", "image/jpeg", "image/webp", "image/svg+xml"):
        return typ
    raise BildFehler("Das Bildformat wird nicht unterstützt")


def erzeugen(beschreibung: str, stil: str = "silhouette", quelle: Optional[str] = None,
             modell: Optional[str] = None, timeout: float = TIMEOUT) -> Dict[str, Any]:
    """Beschreibung → Bild (Base64) mit Typ und Kosten."""
    s = settings()
    quelle = quelle or s["quelle"]
    text = prompt(beschreibung, stil)
    if quelle == "openrouter":
        key = get_key()
        if not key:
            raise BildFehler("Für OpenRouter fehlt noch der Schlüssel – unter Einstellungen → Assistent eintragen")
        if s["limit"] and s["monat"]["kosten"] >= s["limit"]:
            raise BildFehler(f"Monatslimit von {s['limit']:.2f} $ erreicht – unter Einstellungen → Assistent anheben")
        modell = _modellname(modell or s["openrouter_modell"])
        r = _openrouter(text, modell, key, timeout)
    elif quelle == "ollama":
        modell = _modellname(modell or s["ollama_modell"])
        try:
            r = _ollama(text, modell, None, timeout)
        except assistent.AssistentFehler as e:
            raise BildFehler(str(e).replace("ollama pull " + assistent.settings()["modell"], "ollama pull " + modell))
    else:
        raise BildFehler("Quelle unbekannt")
    b64 = r["b64"].split(",", 1)[1] if r["b64"].startswith("data:") else r["b64"]
    try:
        raw = base64.b64decode(b64, validate=False)
    except (ValueError, TypeError):
        raise BildFehler("Das Bild kam beschädigt an")
    typ = _typ(raw, r["typ"])
    monat = _buchen(r["kosten"]) if quelle == "openrouter" else settings()["monat"]
    return dict(ok=True, bild=base64.b64encode(raw).decode("ascii"), typ=typ, quelle=quelle, modell=modell,
                kosten=round(r["kosten"], 4), monat=monat, prompt=text)
