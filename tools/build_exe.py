#!/usr/bin/env python3
"""Empaqueta el programa en un ejecutable único con PyInstaller (sin consola y con el ícono).

    pip install pyinstaller
    python tools/build_exe.py            # genera dist/ConexionesMetalicas(.exe)

Se ejecuta en el sistema operativo de destino (en Windows genera el .exe).
"""
import os
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sep = os.pathsep
datos = [("web", "web"), ("assets", "assets")]
for paquete in ("placa_base", "end_plate", "bfp", "rodilla", "cortante_vv", "cortante_vc", "empalme_viga", "empalme_col"):
    for archivo in ("catalogos.json", "inputs_spec.json"):
        ruta = os.path.join(paquete, archivo)
        if os.path.exists(os.path.join(RAIZ, ruta)):
            datos.append((ruta, paquete))
cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--onefile", "--windowed",
       "--name", "ConexionesMetalicas", "--icon", os.path.join("assets", "icono.ico"),
       "--hidden-import", "tkinter"]
for origen, destino in datos:
    cmd += ["--add-data", f"{origen}{sep}{destino}"]
cmd.append("Iniciar.pyw")
sys.exit(subprocess.call(cmd, cwd=RAIZ))
