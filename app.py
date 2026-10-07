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

from bfp import engine as bfp_engine
from cortante_vc import engine as cortante_vc_engine
from cortante_vv import engine as cortante_vv_engine
from empalme_col import engine as empalme_col_engine
from empalme_viga import engine as empalme_viga_engine
from end_plate import engine as end_plate_engine
from placa_base.engine import CATALOGOS, calcular
from rodilla import engine as rodilla_engine
import autodiseno
import docx_writer
import cargas
import perfiles_usuario
from wuf import engine as wuf_engine
from gusset import engine as gusset_engine
from cortante_hss import engine as hss_engine
from hss_directa import engine as hss_directa_engine
from hss_pasante import engine as hss_pasante_engine
from hss_diafragma import engine as hss_diafragma_engine
from hss_dext import engine as hss_dext_engine
from hss_placalong import engine as hss_placalong_engine
from hss_placasimple import engine as hss_placasimple_engine
from empalme_rhs import engine as empalme_rhs_engine
from hss_diafragma_atornillado import engine as hss_diafragma_atornillado_engine

MODULOS_XL = {"end_plate": end_plate_engine, "bfp": bfp_engine, "rodilla": rodilla_engine,
              "cortante_vv": cortante_vv_engine, "cortante_vc": cortante_vc_engine,
              "empalme_viga": empalme_viga_engine, "empalme_col": empalme_col_engine,
              "wuf": wuf_engine,
              "gusset": gusset_engine,
              "cortante_hss": hss_engine,
              "hss_directa": hss_directa_engine,
              "hss_pasante": hss_pasante_engine,
              "hss_diafragma": hss_diafragma_engine,
              "hss_dext": hss_dext_engine,
              "hss_placalong": hss_placalong_engine,
              "hss_placasimple": hss_placasimple_engine,
              "empalme_rhs": empalme_rhs_engine,
              "hss_diafragma_atornillado": hss_diafragma_atornillado_engine}

WEB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")


def _api_nec(d):
    return {"combos": cargas.generar(d.get("cargas", {}), d["columnas"], float(d.get("omega0", 1) or 1),
                                     d.get("modo_sismo", "E"), bool(d.get("invertir", True)))}


def _api_sap_parse(d):
    t = cargas.parse(d["texto"])
    return {"tabla": t["tabla"], "columnas": t["columnas"], "unidades": t["unidades"], "n": len(t["filas"]),
            "muestra": t["filas"][:6], "mapa": cargas.mapa_sugerido(t["columnas"], d.get("claves", []))}


def _api_sap_import(d):
    return cargas.importar(d["texto"], d.get("mapa", {}), d["claves"], d.get("nombre_col"), d.get("filtro"),
                           d.get("fuerza", "Tonf"), d.get("longitud", "m"), int(d.get("n_max", 10)))


def _api_barrido(nombre, calc, spec, d):
    return autodiseno.barrido(calc, d["inputs"], d["variable"], d["valores"], int(d.get("top", 5)), d.get("lim"))


def _api_auto(nombre, calc, spec, d):
    inp = d["inputs"]
    opciones = {c["name"]: c.get("options") for s in (spec or {}).get("secciones", []) for c in s["campos"]} if spec else None
    if d.get("accion") == "vars":
        return {"variables": autodiseno.variables(nombre, inp, opciones)}
    return autodiseno.buscar(nombre, calc, inp, d.get("nombres"), d.get("lim"), opciones_campo=opciones)


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
        for nombre, eng in MODULOS_XL.items():
            if path == f"/api/{nombre}/spec":
                return self._send(200, eng.SPEC)
        if path == "/api/perfiles":
            return self._send(200, {"perfiles": perfiles_usuario.leer(), "ruta": perfiles_usuario.ruta()})
        if path == "/api/ping":
            return self._send(200, {"app": "conexiones"})
        if path == "/favicon.ico":
            path = "/icon.png"
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
        funciones = {"/api/placa_base/calc": calcular, "/api/nec_combos": _api_nec, "/api/sap_parse": _api_sap_parse,
                     "/api/sap_import": _api_sap_import,
                     "/api/docx": lambda d: docx_writer.build(d["bloques"], d.get("titulo") or "Memoria de cálculo de conexiones metálicas"),
                     "/api/perfiles": lambda d: {"perfiles": perfiles_usuario.guardar(d["perfiles"])},
                     "/api/perfiles_importar": lambda d: {"perfiles": perfiles_usuario.parse_texto(d["texto"])},
                     "/api/placa_base/barrido": lambda d: _api_barrido("placa_base", calcular, None, d), "/api/placa_base/auto": lambda d: _api_auto("placa_base", calcular, None, d)}
        funciones.update({f"/api/{n}/calc": e.calcular for n, e in MODULOS_XL.items()})
        funciones.update({f"/api/{n}/barrido": (lambda d, n=n, e=e: _api_barrido(n, e.calcular, e.SPEC, d))
                          for n, e in MODULOS_XL.items() if n in autodiseno.CONFIG})
        funciones.update({f"/api/{n}/auto": (lambda d, n=n, e=e: _api_auto(n, e.calcular, e.SPEC, d))
                          for n, e in MODULOS_XL.items() if n in autodiseno.CONFIG})
        if self.path not in funciones:
            return self._send(404, {"error": "no encontrado"})
        try:
            n = int(self.headers.get("Content-Length", 0))
            datos = json.loads(self.rfile.read(n) or b"{}")
            res = funciones[self.path](datos)
            if isinstance(res, bytes):
                return self._send(200, res, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            self._send(200, res)
        except (ValueError, KeyError, TypeError, ZeroDivisionError) as exc:
            self._send(400, {"error": f"{type(exc).__name__}: {exc}"})

    def log_message(self, fmt, *args):  # silencioso
        pass


def crear_servidor(host="127.0.0.1", port=8000, buscar_libre=False):
    """Crea el servidor HTTP. Con buscar_libre prueba los puertos siguientes si el indicado está ocupado."""
    ultimo = None
    for p in range(port, port + (20 if buscar_libre else 1)):
        try:
            return ThreadingHTTPServer((host, p), Handler)
        except OSError as exc:
            ultimo = exc
    raise ultimo


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--no-browser", action="store_true")
    a = ap.parse_args()
    srv = crear_servidor(a.host, a.port)
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
