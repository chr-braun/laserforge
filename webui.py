#!/usr/bin/env python3
"""
webui.py – Weboberfläche für Steckwerk (nur Python-Standardbibliothek).

  python webui.py                  startet auf http://127.0.0.1:8765 und öffnet den Browser
  python webui.py --port 9000      anderer Port
  python webui.py --lan            im Heimnetz erreichbar (z. B. vom Tablet in der Werkstatt)
  python webui.py --out ~/laser    Ordner für „In Ordner speichern“

Als App (Doppelklick, Fenster zu = beendet) startet es steckwerk_app.py.

Die Oberfläche nutzt dieselbe Prüfkette wie die Kommandozeile: Download und Speichern
gibt es nur, wenn der Validator alles als CUT-READY bestätigt hat.

API (JSON; jeder POST braucht den Header X-Steckwerk, damit fremde Webseiten nichts auslösen):
  GET  /api/schema       Modelle, Parameter, Material-Einstellungen
  POST /api/generate     {model, params, config} → Prüfbericht + SVGs
  POST /api/zip          gleiche Anfrage → ZIP (SVGs + Prüfberichte)
  POST /api/save         gleiche Anfrage → schreibt in den Ausgabeordner
  POST /api/motiv-import    {name, filename, data (base64), invert} → Motiv in die Bibliothek
  POST /api/motiv-entfernen {id} → eigenes Motiv löschen
  POST /api/motiv-design    {model, params, config} → Grundform ohne Motive (Platzierungs-Editor)
  POST /api/update-check        → was es Neues gibt (Programm und Pakete aus dem Update-Kanal)
  POST /api/update-paket        {id} oder {alle: true} → Paket(e) aus dem Kanal installieren
  POST /api/update-programm     Mac-App durch die neue Version ersetzen und neu starten (nur App)
  POST /api/update-einstellungen {kanal, token, auto} → Einstellungen ändern (Schlüssel wird nie zurückgegeben)
  POST /api/assistent    {model, beschreibung, params} → Werte-Vorschlag vom lokalen Sprachmodell (Ollama)
  POST /api/assistent-status         {url?} → Ollama erreichbar? installierte Modelle
  POST /api/assistent-einstellungen  {an, url, modell} → Assistent einstellen
  POST /api/bild          {beschreibung, stil, quelle?, modell?} → Motiv-Bild vom Bildmodell (Ollama oder OpenRouter)
  POST /api/bild-modelle  {quelle, neu?} → Bildmodelle der Quelle (OpenRouter mit geschätzten Kosten je Bild)
  POST /api/bild-einstellungen {quelle, ollama_modell, openrouter_modell, key, limit} → Schlüssel wird nie zurückgegeben
  POST /api/ping         {client} → Lebenszeichen eines offenen Fensters
  POST /api/bye          {client} → Fenster wurde geschlossen
  POST /api/open-folder  Ausgabeordner im Finder/Explorer öffnen (nur App)
  POST /api/quit         App beenden (nur App)
"""
from __future__ import annotations

import argparse
import json
import os
import socket
import sys
import threading
import time
import traceback
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable, Dict, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from steckwerk import ConfigError, __version__  # noqa: E402
import service  # noqa: E402

WEB = os.path.join(HERE, "web")
INDEX = os.path.join(WEB, "index.html")
ICON = os.path.join(WEB, "icon.png")
MAX_BODY = 64 * 1024
LOCAL_HOSTS = {"127.0.0.1", "localhost", "[::1]"}


class Session:
    """Lebenszeichen der offenen Browserfenster – damit sich die App von selbst beendet.

    Jedes Fenster meldet sich alle 30 s per /api/ping. Schließt das letzte Fenster (/api/bye),
    endet die App nach `grace` Sekunden (ein Neuladen der Seite meldet sich vorher wieder).
    Ohne jede Anfrage endet sie nach `idle_limit` Sekunden.
    """

    def __init__(self, idle_limit: float = 20 * 60, grace: float = 10.0,
                 clock: Callable[[], float] = time.monotonic):
        self.idle_limit, self.grace, self.clock = idle_limit, grace, clock
        self.clients: Dict[str, float] = {}
        self.last_activity = clock()
        self.closed_at: Optional[float] = None
        self.quit_requested = False
        self._lock = threading.Lock()

    def touch(self, client: Optional[str] = None) -> None:
        with self._lock:
            now = self.clock()
            self.last_activity = now
            if client:
                self.clients[client] = now
                self.closed_at = None

    def bye(self, client: Optional[str]) -> None:
        with self._lock:
            self.last_activity = self.clock()
            self.clients.pop(client or "", None)
            if not self.clients:
                self.closed_at = self.clock()

    def request_quit(self) -> None:
        self.quit_requested = True

    def should_quit(self) -> Optional[str]:
        """Grund zum Beenden oder None."""
        with self._lock:
            now = self.clock()
            if self.quit_requested:
                return "über „Beenden“ in der Oberfläche"
            for c, t in list(self.clients.items()):
                if now - t > self.idle_limit:          # Fenster ohne Abschied verschwunden
                    del self.clients[c]
            if not self.clients and self.closed_at is not None and now - self.closed_at >= self.grace:
                return "alle Fenster geschlossen"
            if now - self.last_activity >= self.idle_limit:
                return f"{self.idle_limit / 60:.0f} Minuten nicht benutzt"
            return None


class Handler(BaseHTTPRequestHandler):
    server_version = "Steckwerk"
    out_dir = "out"
    quiet = False
    lan = False                      # True: Zugriff aus dem Heimnetz erlaubt
    app = False                      # True: läuft als App (Beenden, Ordner öffnen)
    session: Optional[Session] = None
    open_folder: Optional[Callable[[str], None]] = None
    bundle: Optional[str] = None     # Pfad der Mac-App (für Programm-Updates)

    def _schema(self) -> dict:
        import updater
        try:
            upd = updater.settings()
        except Exception:                                        # pragma: no cover – Updates sind optional
            upd = {}
        import i18n
        import assistent
        try:
            ki = assistent.settings()
            import bildgen
            ki["bilder"] = bildgen.settings()
        except Exception:                                        # pragma: no cover – Assistent ist optional
            ki = {}
        s = dict(i18n.translate_schema(service.schema(), getattr(self, "lang", "de")), mode="server", app=self.app,
                 assistent=ki,
                 bundle=bool(self.bundle), updates=upd, out_dir=os.path.abspath(os.path.expanduser(self.out_dir)),
                 lang=getattr(self, "lang", "de"), sprachen=[dict(value=v, label=l) for v, l in i18n.SPRACHEN])
        if "group_labels" not in s:
            s["group_labels"] = {g: g for g in s.get("groups", [])}
        return s

    def _assistent(self, path: str, req: dict) -> None:
        import assistent
        try:
            if path == "/api/assistent-einstellungen":
                if self.lan:
                    return self._json({"ok": False, "error": "Nur am Rechner selbst änderbar"}, 403)
                d = assistent.save_settings(an=req.get("an"), url=req.get("url"), modell=req.get("modell"))
                self._json({"ok": True, "assistent": d})
            elif path == "/api/assistent-status":
                self._json(assistent.status(req.get("url") or None))
            elif path == "/api/assistent":
                model = str(req.get("model") or "")
                if model not in service.MODEL_INFO:
                    return self._json({"ok": False, "error": f"Unbekanntes Modell {model!r}"}, 400)
                aktuell = req.get("params") if isinstance(req.get("params"), dict) else {}
                self._json(assistent.vorschlag(service.MODEL_INFO[model], str(req.get("beschreibung") or ""), aktuell))
            else:
                self._json({"error": "nicht gefunden"}, 404)
        except assistent.AssistentFehler as e:
            self._json({"ok": False, "error": str(e)})

    def _bild(self, path: str, req: dict) -> None:
        import assistent
        import bildgen
        try:
            if path == "/api/bild-einstellungen":
                if self.lan:
                    return self._json({"ok": False, "error": "Nur am Rechner selbst änderbar"}, 403)
                d = bildgen.save_settings(quelle=req.get("quelle"), ollama_modell=req.get("ollama_modell"),
                                          openrouter_modell=req.get("openrouter_modell"), key=req.get("key"),
                                          limit=req.get("limit"))
                self._json({"ok": True, "bilder": d})
            elif path == "/api/bild-modelle":
                if req.get("quelle") == "openrouter":
                    self._json({"ok": True, "modelle": bildgen.openrouter_modelle(bool(req.get("neu")))})
                else:
                    self._json({"ok": True, "modelle": bildgen.ollama_modelle()})
            elif path == "/api/bild":
                quelle = req.get("quelle") or None
                if self.lan and (quelle or bildgen.settings()["quelle"]) == "openrouter":
                    return self._json({"ok": False, "error": "Kostenpflichtige Bilder nur am Rechner selbst"}, 403)
                self._json(bildgen.erzeugen(str(req.get("beschreibung") or ""), str(req.get("stil") or "silhouette"),
                                            quelle, req.get("modell") or None))
            else:
                self._json({"error": "nicht gefunden"}, 404)
        except (bildgen.BildFehler, assistent.AssistentFehler) as e:
            self._json({"ok": False, "error": str(e)})

    # --- Hilfen --------------------------------------------------------------
    def _send(self, status: int, body: bytes, ctype: str, extra=None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _json(self, obj, status: int = 200) -> None:
        lang = getattr(self, "lang", "de")
        if lang != "de":
            import i18n
            obj = i18n.localize(obj, lang)
        self._send(status, json.dumps(obj, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def _body(self, limit: int = MAX_BODY):
        n = int(self.headers.get("Content-Length") or 0)
        if n > limit:
            raise ValueError("Anfrage zu groß")
        raw = self.rfile.read(n) if n else b"{}"
        data = json.loads(raw.decode("utf-8") or "{}")
        if not isinstance(data, dict):
            raise ValueError("JSON-Objekt erwartet")
        return data

    def _host_ok(self) -> bool:
        """Schutz gegen DNS-Rebinding: lokal nur Anfragen an 127.0.0.1/localhost annehmen."""
        if self.lan:
            return True
        host = self.headers.get("Host", "")
        if not host:
            return True
        name = host[: host.find("]") + 1] if host.startswith("[") else host.split(":")[0]
        return name.lower() in LOCAL_HOSTS

    def _touch(self, client: Optional[str] = None) -> None:
        if self.session:
            self.session.touch(client)

    def log_message(self, fmt, *args):
        if not self.quiet:
            sys.stderr.write("  %s %s\n" % (self.command, self.path))

    # --- Routen --------------------------------------------------------------
    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        if not self._host_ok():
            return self._json({"error": "Zugriff verweigert"}, 403)
        self._touch()
        path, _, query = self.path.partition("?")
        import i18n
        from urllib.parse import parse_qs
        self.lang = i18n.norm((parse_qs(query).get("lang") or ["de"])[0])
        if path in ("/", "/index.html"):
            with open(INDEX, "rb") as fh:
                self._send(200, fh.read(), "text/html; charset=utf-8")
        elif path == "/api/schema":
            self._json(self._schema())
        elif path in ("/favicon.ico", "/favicon.png", "/icon.png"):
            if os.path.exists(ICON):
                with open(ICON, "rb") as fh:
                    self._send(200, fh.read(), "image/png")
            else:
                self._send(204, b"", "image/png")
        else:
            self._json({"error": "nicht gefunden"}, 404)

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        if not self._host_ok() or not self.headers.get("X-Steckwerk"):
            return self._json({"ok": False, "error": "Zugriff verweigert"}, 403)
        try:
            big = path in ("/api/paket-installieren", "/api/motiv-import")
            req = self._body(30 * 1024 * 1024 if big else MAX_BODY)
            import i18n
            self.lang = i18n.norm(req.pop("lang", "de"))
            client = str(req.get("client") or "")[:64] or None
            out = os.path.expanduser(self.out_dir)
            if path == "/api/ping":
                self._touch(client)
                self._json({"ok": True, "app": "steckwerk", "version": __version__, "pid": os.getpid(),
                            "files": os.path.exists(INDEX)})
            elif path == "/api/bye":
                if self.session:
                    self.session.bye(client)
                self._json({"ok": True})
            elif path == "/api/quit" and self.app and self.session:
                self.session.request_quit()
                self._json({"ok": True})
            elif path == "/api/open-folder" and self.app and self.open_folder:
                self._touch()
                os.makedirs(out, exist_ok=True)
                try:
                    self.open_folder(os.path.abspath(out))
                except OSError as e:
                    return self._json({"ok": False, "error": f"Ordner lässt sich nicht öffnen: {e}"})
                self._json({"ok": True, "out_dir": os.path.abspath(out)})
            elif path in ("/api/paket-installieren", "/api/paket-entfernen"):
                import base64
                import pakete
                self._touch()
                try:
                    if path == "/api/paket-installieren":
                        m, _ = pakete.install(data=base64.b64decode(str(req.get("data") or "")))
                        msg = f"Paket „{m['name']}“ {m['version']} installiert – Modelle: {', '.join(m['modelle'])}"
                    else:
                        pakete.remove(str(req.get("id") or ""))
                        msg = "Paket entfernt"
                except (pakete.PaketFehler, ValueError) as e:
                    return self._json({"ok": False, "error": str(e)}, 400)
                service.reload_pakete()
                self._json({"ok": True, "message": msg, "schema": self._schema()})
            elif path.startswith("/api/update-"):
                self._touch()
                self._update(path, req)
            elif path in ("/api/motiv-import", "/api/motiv-entfernen"):
                import base64
                import motive
                self._touch()
                try:
                    if path == "/api/motiv-import":
                        m = motive.import_bytes(base64.b64decode(str(req.get("data") or "")),
                                                str(req.get("filename") or "motiv"), str(req.get("name") or ""),
                                                bool(req.get("invert")))
                        msg = f"Motiv „{m['name']}“ importiert"
                        new_id = m["id"]
                    else:
                        motive.remove(str(req.get("id") or ""))
                        msg, new_id = "Motiv entfernt", None
                except (motive.MotivFehler, ValueError) as e:
                    return self._json({"ok": False, "error": str(e)}, 400)
                self._json({"ok": True, "message": msg, "id": new_id,
                            "motive": [motive.summary(x) for x in motive.library()]})
            elif path.startswith("/api/bild"):
                self._touch()
                self._bild(path, req)
            elif path.startswith("/api/assistent"):
                self._touch()
                self._assistent(path, req)
            elif path == "/api/motiv-design":
                self._touch()
                self._json(service.design(req))
            elif path == "/api/generate":
                self._touch()
                self._json(service.generate(req))
            elif path == "/api/zip":
                self._touch()
                results, cfg = service.run_request(req, preview_on_error=False)
                data = service.zip_results(results, cfg)
                name = "steckwerk_" + "".join(c for c in str(req.get("model", "modell")) if c.isalnum()) + ".zip"
                self._send(200, data, "application/zip", {"Content-Disposition": f'attachment; filename="{name}"'})
            elif path == "/api/save":
                self._touch()
                results, cfg = service.run_request(req, preview_on_error=False)
                written, _ = service.write_results(results, cfg, out, bool(req.get("preview")))
                self._json({"ok": True, "out_dir": os.path.abspath(out), "files": written})
            else:
                self._json({"error": "nicht gefunden"}, 404)
        except (ConfigError, ValueError, RuntimeError) as e:
            self._json({"ok": False, "error": str(e)}, 400)
        except OSError as e:
            self._json({"ok": False, "error": f"Speichern nicht möglich: {e}"}, 500)
        except Exception as e:                                   # pragma: no cover – Schutznetz
            traceback.print_exc()
            self._json({"ok": False, "error": f"Interner Fehler: {e}"}, 500)


    def _update(self, path: str, req: dict) -> None:
        import pakete
        import updater
        if self.lan and path != "/api/update-check":
            return self._json({"ok": False, "error": "Updates nur am Rechner selbst installieren"}, 403)
        try:
            if path == "/api/update-check":
                d = updater.check(self.bundle)
                d["einstellungen"] = updater.settings()
                return self._json(d)
            if path == "/api/update-einstellungen":
                tok = req.get("token")
                s = updater.save_settings(req.get("kanal") if "kanal" in req else None,
                                          None if tok is None else str(tok),
                                          req.get("auto") if "auto" in req else None)
                return self._json({"ok": True, "einstellungen": s, "message": "Einstellungen gespeichert"})
            if path == "/api/update-paket":
                feed = updater.load_feed()
                if req.get("alle"):
                    done = updater.install_alle_pakete(feed)
                    msg = (f"{len(done)} Paket(e) installiert: " + ", ".join(m["name"] for m in done)) if done \
                        else "Alle Pakete sind aktuell"
                else:
                    m = updater.install_paket(str(req.get("id") or ""), feed)
                    msg = f"Paket „{m['name']}“ {m['version']} installiert"
                service.reload_pakete()
                return self._json({"ok": True, "message": msg, "schema": self._schema()})
            if path == "/api/update-programm" and self.app:
                target, version = updater.install_program(self.bundle or "")
                updater.restart(target)
                if self.session:
                    threading.Timer(0.5, self.session.request_quit).start()
                return self._json({"ok": True, "version": version,
                                   "message": f"Steckwerk {version} ist installiert und startet gleich neu"})
            self._json({"error": "nicht gefunden"}, 404)
        except (updater.UpdateFehler, pakete.PaketFehler) as e:
            err = {"ok": False, "error": str(e)}
            if path == "/api/update-check":
                err["einstellungen"] = updater.settings()
            self._json(err, 400)


def lan_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return "127.0.0.1"


def make_server(host: str = "127.0.0.1", port: int = 8765, out_dir: str = "out", quiet: bool = False,
                app: bool = False, session: Optional[Session] = None,
                open_folder: Optional[Callable[[str], None]] = None, bundle: Optional[str] = None):
    attrs = {"bundle": bundle, "out_dir": out_dir, "quiet": quiet, "lan": host not in ("127.0.0.1", "localhost", "::1"),
             "app": app, "session": session,
             "open_folder": staticmethod(open_folder) if open_folder else None}
    handler = type("SteckwerkHandler", (Handler,), attrs)
    return ThreadingHTTPServer((host, port), handler)


def main(argv=None) -> int:
    from steckwerk import migrate_legacy
    migrate_legacy()
    ap = argparse.ArgumentParser(prog="webui", description="Weboberfläche für Steckwerk")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--lan", action="store_true", help="im Heimnetz freigeben (0.0.0.0)")
    ap.add_argument("--out", default="out", help="Ordner für 'In Ordner speichern' (Default ./out)")
    ap.add_argument("--no-browser", action="store_true", help="Browser nicht automatisch öffnen")
    ap.add_argument("--quiet", action="store_true", help="keine Zugriffe protokollieren")
    a = ap.parse_args(argv)
    host = "0.0.0.0" if a.lan else "127.0.0.1"
    try:
        srv = make_server(host, a.port, a.out, a.quiet)
    except OSError as e:
        print(f"Port {a.port} ist belegt ({e}). Anderen wählen: python webui.py --port 8800")
        return 1
    url = f"http://127.0.0.1:{a.port}/"
    print(f"Steckwerk-Weboberfläche läuft: {url}")
    if a.lan:
        print(f"Im Heimnetz: http://{lan_ip()}:{a.port}/")
    print(f"Speicherordner: {os.path.abspath(a.out)}\nBeenden mit Strg+C.")
    if not a.no_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nBeendet.")
    finally:
        srv.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
