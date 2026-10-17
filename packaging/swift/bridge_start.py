#!/usr/bin/env python3
"""
bridge_start.py – startet die Steckwerk-Engine für die native App „Steckwerk Desktop“.

  python3 bridge_start.py --root <Ordner mit webui.py> [--port 0] [--out <Speicherordner>]

Schreibt genau eine Zeile „STECKWERK_PORT=<port>“ auf stdout, sobald der Server bereit ist.
Läuft schon eine Steckwerk-Instanz derselben Version, lautet die Zeile „STECKWERK_PORT=<port> REUSED“
und dieses Skript endet sofort – die App nutzt dann die laufende Instanz mit.

Die eigene Engine endet von selbst, wenn
  * stdin geschlossen wird (App beendet oder abgestürzt – so bleiben keine Waisenprozesse),
  * die App sich mit /api/bye abmeldet oder /api/quit schickt, oder
  * sie längere Zeit gar nichts gehört hat (--idle).

Nur Python-Standardbibliothek, ab Python 3.9. webui.py bleibt unverändert.
"""
from __future__ import annotations

import argparse
import faulthandler
import os
import signal
import sys
import threading
import time
from typing import List, Optional


def _lifeline(session) -> None:
    """Liest stdin bis zum Ende; das Ende heißt: die App gibt es nicht mehr.

    Ungepuffert über den Dateideskriptor – ein gepuffertes stdin hält eine Sperre, an der Python beim
    Beenden sonst abbricht (Fatal Python error: _enter_buffered_busy)."""
    try:
        fd = sys.stdin.fileno()
        while os.read(fd, 4096):
            pass
    except (OSError, ValueError):
        pass
    session.request_quit()


def _schneller_bind() -> None:
    """HTTPServer.server_bind fragt per socket.getfqdn() den Rechnernamen ab. Auf macOS kann diese
    Namensauflösung für 127.0.0.1 viele Sekunden hängen – für einen reinen Loopback-Server ist sie unnötig."""
    import http.server
    import socketserver

    def server_bind(self) -> None:
        socketserver.TCPServer.server_bind(self)
        host, port = self.server_address[:2]
        self.server_name = str(host)
        self.server_port = port

    http.server.HTTPServer.server_bind = server_bind  # type: ignore[method-assign]


def _running_port(steckwerk_app, version: str) -> Optional[int]:
    """Port einer laufenden Steckwerk-Instanz derselben Version, sonst None (andere werden nicht angefasst)."""
    info = steckwerk_app._read_json(steckwerk_app.running_path())
    port = info.get("port")
    if not isinstance(port, int):
        return None
    answer = steckwerk_app.probe(port)
    if answer and answer.get("version") == version and answer.get("files") is not False:
        return port
    return None


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="bridge_start", description="Steckwerk-Engine für Steckwerk Desktop starten")
    ap.add_argument("--root", required=True, help="Ordner mit webui.py")
    ap.add_argument("--port", type=int, default=0, help="0 = freien Port wählen")
    ap.add_argument("--out", help="Speicherordner (Default: Dokumente/Steckwerk)")
    ap.add_argument("--idle", type=float, default=20, help="Minuten ohne Anfrage bis zum Beenden")
    ap.add_argument("--no-reuse", action="store_true", help="eine laufende Steckwerk-Instanz nicht mitbenutzen")
    a = ap.parse_args(argv)
    if hasattr(signal, "SIGUSR1"):
        faulthandler.register(signal.SIGUSR1, all_threads=True)       # Diagnose: wo hängt die Engine?
    print(f"bridge_start: Python {sys.version.split()[0]}", file=sys.stderr, flush=True)

    root = os.path.abspath(a.root)
    if not os.path.isfile(os.path.join(root, "webui.py")):
        print(f"webui.py nicht gefunden in {root}", file=sys.stderr)
        return 2
    sys.path.insert(0, root)
    os.chdir(root)

    import steckwerk_app
    import webui
    from steckwerk import __version__, migrate_legacy

    migrate_legacy()
    if not a.no_reuse:
        port = _running_port(steckwerk_app, __version__)
        if port:
            print(f"STECKWERK_PORT={port} REUSED", flush=True)
            return 0

    _schneller_bind()
    session = webui.Session(idle_limit=a.idle * 60, grace=10.0)
    out = a.out or steckwerk_app.default_out_dir()
    try:
        srv = webui.make_server("127.0.0.1", a.port, out, quiet=True, app=True, session=session,
                                open_folder=steckwerk_app.open_folder)
    except OSError as e:
        print(f"Server ließ sich nicht starten: {e}", file=sys.stderr)
        return 1
    port = srv.server_address[1]

    def watchdog() -> None:
        while True:
            time.sleep(0.25)
            if session.should_quit():
                srv.shutdown()
                return

    threading.Thread(target=_lifeline, args=(session,), daemon=True).start()
    threading.Thread(target=watchdog, daemon=True).start()
    print(f"STECKWERK_PORT={port}", flush=True)
    try:
        srv.serve_forever(poll_interval=0.25)
    finally:
        srv.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
