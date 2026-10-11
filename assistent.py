"""
Assistent – ein lokales Sprachmodell (Ollama) schlägt Werte für ein Modell vor.

Das Modell liefert nur einen Bauplan als JSON (die Werte der Parameter, bei Filigran ein Ornament-Rezept);
alle Geometrie rechnet Steckwerk selbst. Jeder Vorschlag wird wie eine Eingabe von Hand geprüft:
Zahlen außerhalb des erlaubten Bereichs werden eingegrenzt, unbekannte Auswahlwerte verworfen.

Steckwerk spricht nur mit einem Ollama im eigenen Netz (localhost, 127.x, ::1, private Adressen,
*.local) – Beschreibungen verlassen den Rechner nicht.
"""
from __future__ import annotations

import ipaddress
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

STANDARD_URL = "http://127.0.0.1:11434"
STANDARD_MODELL = "qwen2.5:3b"
TIMEOUT = 180.0
MAX_ANTWORT = 256 * 1024


class AssistentFehler(RuntimeError):
    pass


# --- Einstellungen --------------------------------------------------------------------------------

def _path() -> str:
    import updater
    return os.path.join(updater.data_dir(), "assistent.json")


def settings() -> Dict[str, Any]:
    try:
        with open(_path(), encoding="utf-8") as fh:
            d = json.load(fh)
        d = d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        d = {}
    return dict(an=bool(d.get("an", False)), url=str(d.get("url") or STANDARD_URL),
                modell=str(d.get("modell") or STANDARD_MODELL))


def save_settings(an: Optional[bool] = None, url: Optional[str] = None, modell: Optional[str] = None) -> Dict[str, Any]:
    d = settings()
    if an is not None:
        d["an"] = bool(an)
    if url is not None:
        d["url"] = check_url(url.strip() or STANDARD_URL)
    if modell is not None:
        m = modell.strip()
        if not m or len(m) > 120 or any(c.isspace() for c in m):
            raise AssistentFehler("Modellname ungültig – z. B. qwen2.5:3b")
        d["modell"] = m
    path = _path()
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(d, fh, ensure_ascii=False, indent=1)
    os.replace(tmp, path)
    return d


def check_url(url: str) -> str:
    """Nur Ollama im eigenen Netz zulassen."""
    p = urllib.parse.urlparse(url)
    if p.scheme not in ("http", "https") or not p.hostname:
        raise AssistentFehler("Adresse ungültig – z. B. http://127.0.0.1:11434")
    host = p.hostname.lower()
    ok = host == "localhost" or host.endswith(".local")
    if not ok:
        try:
            ip = ipaddress.ip_address(host)
            ok = ip.is_loopback or ip.is_private or ip.is_link_local
        except ValueError:
            ok = False
    if not ok:
        raise AssistentFehler("Nur ein Ollama auf diesem Rechner oder im eigenen Netz ist erlaubt "
                              "(localhost, 127.0.0.1, 192.168.…, name.local)")
    return url.rstrip("/")


# --- Verbindung -----------------------------------------------------------------------------------

_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))   # nie über einen Proxy


def _call(url: str, path: str, payload: Optional[Dict[str, Any]] = None, timeout: float = 5.0,
          limit: int = MAX_ANTWORT) -> Dict[str, Any]:
    base = check_url(url)
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(base + path, data=data, headers={"Content-Type": "application/json"},
                                 method="POST" if data is not None else "GET")
    try:
        with _opener.open(req, timeout=timeout) as r:
            raw = r.read(limit + 1)
    except urllib.error.HTTPError as e:
        try:
            msg = json.loads(e.read(4096).decode("utf-8", "replace")).get("error", "")
        except Exception:
            msg = ""
        if e.code == 404 and "model" in msg:
            raise AssistentFehler(f"Ollama kennt das Modell nicht – im Terminal: ollama pull {settings()['modell']}")
        raise AssistentFehler(f"Ollama meldet Fehler {e.code}" + (f": {msg}" if msg else ""))
    except (urllib.error.URLError, OSError) as e:
        reason = getattr(e, "reason", e)
        if "timed out" in str(reason):
            raise AssistentFehler("Ollama antwortet nicht rechtzeitig – ein kleineres Modell wählen")
        raise AssistentFehler(f"Ollama ist nicht erreichbar unter {base} – läuft die Ollama-App? ({reason})")
    if len(raw) > limit:
        raise AssistentFehler("Antwort von Ollama zu groß")
    try:
        d = json.loads(raw.decode("utf-8"))
    except ValueError:
        raise AssistentFehler("Antwort von Ollama ist kein JSON")
    if not isinstance(d, dict):
        raise AssistentFehler("Antwort von Ollama unerwartet")
    return d


def status(url: Optional[str] = None) -> Dict[str, Any]:
    """Erreichbarkeit und installierte Modelle."""
    s = settings()
    d = _call(url or s["url"], "/api/tags")
    names = sorted(str(m.get("name") or m.get("model")) for m in d.get("models", []) if isinstance(m, dict))
    return dict(ok=True, modelle=names, modell=s["modell"], vorhanden=s["modell"] in names or
                any(n.split(":")[0] == s["modell"] and n.endswith(":latest") for n in names))


# --- Bauplan-Schema aus den Parametern ------------------------------------------------------------

def _param_schema(p: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    t = p.get("type")
    if p.get("ki_schema"):
        return p["ki_schema"]
    if t == "number":
        return {"type": "number", "minimum": p["min"], "maximum": p["max"]}
    if t == "int":
        return {"type": "integer", "minimum": p["min"], "maximum": p["max"]}
    if t == "select":
        return {"type": "string", "enum": [o["value"] for o in p["options"]]}
    if t == "bool":
        return {"type": "boolean"}
    if t == "text":
        return {"type": "string", "maxLength": int(p.get("maxlength", 80))}
    return None                                           # Motive & Co. wählt der Mensch


def _beschreibung(p: Dict[str, Any], aktuell: Any) -> str:
    t = p.get("type")
    s = f"- {p['key']}: {p['label']}"
    if t in ("number", "int"):
        s += f" ({p['min']:g}–{p['max']:g} {p.get('unit', '')})".replace(" )", ")")
    elif t == "select":
        s += " – " + "; ".join(f"{o['value']} = {o['label']}" for o in p["options"])
    elif t == "bool":
        s += " (ja/nein)"
    if p.get("help"):
        s += f" [{p['help']}]"
    if p.get("ki_hilfe"):
        s += "\n  " + p["ki_hilfe"]
    if aktuell is not None and not p.get("ki_schema"):
        s += f" – aktuell: {json.dumps(aktuell, ensure_ascii=False)}"
    return s


def _antwort_schema(params: List[Dict[str, Any]]) -> Dict[str, Any]:
    props = {}
    for p in params:
        sch = _param_schema(p)
        if sch is not None:
            props[p["key"]] = sch
    return {"type": "object",
            "properties": {"werte": {"type": "object", "properties": props},
                           "hinweis": {"type": "string", "maxLength": 300}},
            "required": ["werte", "hinweis"]}


SYSTEM = (
    "Du stellst ein parametrisches Lasercut-Modell ein (Steckwerk, Holz für einen Diodenlaser). "
    "Antworte ausschließlich mit JSON nach dem vorgegebenen Schema: \"werte\" enthält nur die Parameter, "
    "die du ändern willst, mit erlaubten Werten; \"hinweis\" ist ein kurzer deutscher Satz, was du eingestellt "
    "hast. Maße sind Millimeter. Erfinde keine Parameter. Wenn die Beschreibung zu einem Wert nichts sagt, "
    "lass ihn weg."
)


def _pruefen(params: List[Dict[str, Any]], werte: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """Vorschlag wie eine Eingabe prüfen; Zahlen eingrenzen, Unpassendes verwerfen."""
    out: Dict[str, Any] = {}
    verworfen: List[str] = []
    by_key = {p["key"]: p for p in params}
    for k, v in werte.items():
        p = by_key.get(k)
        if p is None or _param_schema(p) is None:
            continue
        if p.get("ki_schema"):
            if not isinstance(v, str):
                v = json.dumps(v, ensure_ascii=False, separators=(",", ":"))
            if len(v) > int(p.get("maxlength", 80)):
                verworfen.append(p["label"])
                continue
            out[k] = v
            continue
        t = p["type"]
        if t in ("number", "int"):
            try:
                f = float(str(v).replace(",", ".")) if isinstance(v, str) else float(v)
            except (TypeError, ValueError):
                verworfen.append(p["label"])
                continue
            if f != f:
                verworfen.append(p["label"])
                continue
            f = min(max(f, p["min"]), p["max"])
            out[k] = int(round(f)) if t == "int" else round(f, 2)
        elif t == "select":
            vals = [o["value"] for o in p["options"]]
            v = str(v)
            if v not in vals:                             # Modelle schreiben gern das Anzeigelabel
                lab = {o["label"].lower(): o["value"] for o in p["options"]}
                v = lab.get(v.lower(), "")
            if v in vals:
                out[k] = v
            else:
                verworfen.append(p["label"])
        elif t == "bool":
            out[k] = v if isinstance(v, bool) else str(v).strip().lower() in ("1", "true", "ja", "yes")
        elif t == "text":
            v = str(v)[: int(p.get("maxlength", 80))]
            out[k] = v
    return out, verworfen


def vorschlag(model: Dict[str, Any], beschreibung: str, aktuell: Optional[Dict[str, Any]] = None,
              url: Optional[str] = None, modell: Optional[str] = None, timeout: float = TIMEOUT) -> Dict[str, Any]:
    """Beschreibung → geprüfte Werte für das Modell."""
    beschreibung = (beschreibung or "").strip()
    if not beschreibung:
        raise AssistentFehler("Beschreibe kurz, was du möchtest – z. B. „zierlicher Stern, 12 cm, sehr fein“")
    if len(beschreibung) > 600:
        raise AssistentFehler("Beschreibung bitte kürzer (höchstens 600 Zeichen)")
    s = settings()
    params = [p for p in model.get("params", []) if _param_schema(p) is not None]
    if not params:
        raise AssistentFehler("Dieses Modell hat keine Werte, die der Assistent einstellen kann")
    aktuell = aktuell or {}
    liste = "\n".join(_beschreibung(p, aktuell.get(p["key"], p.get("default"))) for p in params)
    user = (f"Modell: {model.get('label')} – {model.get('desc', '')}\n\nParameter:\n{liste}\n\n"
            f"Wunsch: {beschreibung}")
    payload = {"model": modell or s["modell"], "stream": False, "format": _antwort_schema(params),
               "options": {"temperature": 0.3, "num_ctx": 8192},
               "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}]}
    d = _call(url or s["url"], "/api/chat", payload, timeout=timeout)
    text = str((d.get("message") or {}).get("content") or d.get("response") or "")
    try:
        ans = json.loads(text)
    except ValueError:
        start, end = text.find("{"), text.rfind("}")
        try:
            ans = json.loads(text[start:end + 1]) if start >= 0 else None
        except ValueError:
            ans = None
    if not isinstance(ans, dict):
        raise AssistentFehler("Das Sprachmodell hat keinen brauchbaren Bauplan geliefert – nochmal versuchen "
                              "oder ein anderes Modell wählen")
    werte = ans.get("werte") if isinstance(ans.get("werte"), dict) else {
        k: v for k, v in ans.items() if k != "hinweis"}
    out, verworfen = _pruefen(params, werte)
    hinweis = str(ans.get("hinweis") or "")[:300]
    return dict(ok=True, werte=out, hinweis=hinweis, verworfen=verworfen, modell=payload["model"])
