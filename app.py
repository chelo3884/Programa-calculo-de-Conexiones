#!/usr/bin/env python3
"""Servidor local — Diseño de conexiones metálicas.

Uso:   python3 app.py [--port 8000] [--no-browser]
Sólo usa la biblioteca estándar de Python (sin dependencias).
"""
import argparse
import json
import mimetypes
import os
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from placa_base.engine import CATALOGOS, calcular

WEB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/api/placa_base/catalogos":
            return self._send(200, CATALOGOS)
        if path == "/favicon.ico":
            return self._send(204, b"", "image/x-icon")
        rel = "index.html" if path in ("/", "") else path.lstrip("/")
        full = os.path.normpath(os.path.join(WEB, rel))
        if not full.startswith(WEB + os.sep) or not os.path.isfile(full):
            return self._send(404, {"error": "no encontrado"})
        ctype = mimetypes.guess_type(full)[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype.endswith("javascript"):
            ctype += "; charset=utf-8"
        with open(full, "rb") as fh:
            self._send(200, fh.read(), ctype)

    def do_POST(self):
        if self.path != "/api/placa_base/calc":
            return self._send(404, {"error": "no encontrado"})
        try:
            n = int(self.headers.get("Content-Length", 0))
            datos = json.loads(self.rfile.read(n) or b"{}")
            self._send(200, calcular(datos))
        except (ValueError, KeyError, TypeError, ZeroDivisionError) as exc:
            self._send(400, {"error": f"{type(exc).__name__}: {exc}"})

    def log_message(self, fmt, *args):  # silencioso
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--no-browser", action="store_true")
    a = ap.parse_args()
    srv = ThreadingHTTPServer((a.host, a.port), Handler)
    url = f"http://{a.host}:{a.port}/"
    print(f"Diseño de conexiones — servidor en {url}  (Ctrl+C para salir)")
    if not a.no_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
