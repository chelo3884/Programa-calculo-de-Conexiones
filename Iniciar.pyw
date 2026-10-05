"""Conexiones metálicas — lanzador sin consola.

Doble clic en este archivo (o en el acceso directo creado con Crear_acceso_directo.vbs):
arranca el servidor local, abre el navegador y muestra una ventana pequeña de control.
Cerrar la ventana (o «Detener y salir») apaga el programa.
Necesita Python 3.9 o superior (no requiere instalar librerías).
"""
import os
import sys
import threading
import time
import traceback
import urllib.request
import webbrowser

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
os.chdir(AQUI)

PUERTO = 8000


def _error(msg):
    try:
        import tkinter
        from tkinter import messagebox
        r = tkinter.Tk()
        r.withdraw()
        messagebox.showerror("Conexiones metálicas", msg)
    except Exception:  # sin tkinter: dejar el error en un archivo
        with open(os.path.join(AQUI, "error.log"), "w", encoding="utf-8") as fh:
            fh.write(msg)


def _ya_corriendo(puerto):
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{puerto}/api/ping", timeout=1.5) as r:
            return b'"conexiones"' in r.read()
    except Exception:
        return False


def main():
    # si ya hay una instancia abierta, solo abrir el navegador
    for p in range(PUERTO, PUERTO + 20):
        if _ya_corriendo(p):
            webbrowser.open(f"http://127.0.0.1:{p}/")
            return
    try:
        import app
        srv = app.crear_servidor("127.0.0.1", PUERTO, buscar_libre=True)
    except Exception:
        _error("No se pudo iniciar el servidor:\n\n" + traceback.format_exc())
        return
    url = f"http://127.0.0.1:{srv.server_address[1]}/"
    hilo = threading.Thread(target=srv.serve_forever, daemon=True)
    hilo.start()
    webbrowser.open(url)

    try:
        import tkinter as tk
    except ImportError:          # sin tkinter: servidor sin ventana; se apaga tras 30 min sin uso
        ultimo = [time.time()]
        app.Handler.log_message = lambda self, *a: ultimo.__setitem__(0, time.time())
        while time.time() - ultimo[0] < 1800:
            time.sleep(5)
        return

    raiz = tk.Tk()
    raiz.title("Conexiones metálicas")
    raiz.resizable(False, False)
    try:
        ico = os.path.join(AQUI, "assets", "icono.ico")
        if sys.platform.startswith("win") and os.path.exists(ico):
            raiz.iconbitmap(ico)
        else:
            raiz.iconphoto(True, tk.PhotoImage(file=os.path.join(AQUI, "assets", "icono.png")))
    except Exception:
        pass
    tk.Label(raiz, text="Conexiones metálicas", font=("Segoe UI", 13, "bold"), padx=18, pady=8).pack()
    tk.Label(raiz, text="Programa en ejecución. Se abrió en su navegador:", padx=18).pack()
    enlace = tk.Label(raiz, text=url, fg="#1f4e8c", cursor="hand2", font=("Segoe UI", 10, "underline"))
    enlace.pack()
    enlace.bind("<Button-1>", lambda e: webbrowser.open(url))
    fila = tk.Frame(raiz, pady=12)
    fila.pack()
    tk.Button(fila, text="Abrir en el navegador", command=lambda: webbrowser.open(url), padx=10).pack(side="left", padx=6)
    tk.Button(fila, text="Detener y salir", command=raiz.destroy, padx=10).pack(side="left", padx=6)
    tk.Label(raiz, text="Cierre esta ventana cuando termine de trabajar.", fg="#667085", padx=18, pady=4).pack()
    raiz.protocol("WM_DELETE_WINDOW", raiz.destroy)
    raiz.mainloop()
    srv.shutdown()


if __name__ == "__main__":
    main()
