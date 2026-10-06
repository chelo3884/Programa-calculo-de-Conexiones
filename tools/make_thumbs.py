"""Genera las miniaturas SVG de cada tipo de conexión (web/thumbs/<id>.svg) a partir del dibujo por defecto de cada módulo.

Uso (con Playwright y Chromium instalados):  python3 tools/make_thumbs.py [ruta_de_chromium]
Arranca el servidor en un puerto libre, abre cada página, toma el primer dibujo SVG, resuelve las variables CSS con la paleta clara,
quita textos y cotas y lo guarda como icono.
"""
import os
import re
import sys
import threading

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
import app  # noqa: E402

MODULOS = {"placa_base": 1, "end_plate": 0, "bfp": 0, "rodilla": 0, "wuf": 0, "hss_directa": 0, "hss_pasante": 0, "hss_diafragma": 1,
           "cortante_vc": 0, "cortante_vv": 0, "cortante_hss": 0, "empalme_viga": 0, "empalme_col": 0, "gusset": 0}
PALETA = {"--conc": "#e7e2d8", "--steelf": "#cfd6df", "--steel": "#8d99a8", "--grout": "#c9c3b4", "--bolt": "#444", "--tens": "#d92d20",
          "--comp": "#2e6fd0", "--ink": "#1b2430", "--mut": "#667085", "--card": "#ffffff", "--acc": "#1f4e8c", "--line": "#d9dfe7"}


def limpiar(svg):
    svg = re.sub(r"<text\b.*?</text>", "", svg, flags=re.S)
    svg = re.sub(r'<path class="dim"[^>]*/>', "", svg)
    svg = re.sub(r"\sdata-(sc|f)=\"[^\"]*\"", "", svg)
    svg = re.sub(r"\srole=\"img\"|\saria-label=\"[^\"]*\"", "", svg)
    svg = re.sub(r"var\((--[a-z0-9]+)\)", lambda m: PALETA.get(m.group(1), "#888"), svg)
    return svg


def main():
    from playwright.sync_api import sync_playwright
    srv = app.crear_servidor("127.0.0.1", 0)
    port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    exe = sys.argv[1] if len(sys.argv) > 1 else None
    os.makedirs(os.path.join(RAIZ, "web", "thumbs"), exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()
        pg = b.new_page(viewport={"width": 1400, "height": 900})
        for mod, idx in MODULOS.items():
            pg.goto(f"http://127.0.0.1:{port}/{mod}.html")
            pg.wait_for_selector("svg[data-sc]")
            pg.wait_for_timeout(500)
            svgs = pg.evaluate("[...document.querySelectorAll('svg[data-sc]')].map(s=>s.outerHTML)")
            svg = limpiar(svgs[min(idx, len(svgs) - 1)])
            svg = svg.replace("<svg ", '<svg xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid meet" ', 1)
            with open(os.path.join(RAIZ, "web", "thumbs", mod + ".svg"), "w", encoding="utf-8") as fh:
                fh.write(svg)
            print(mod, len(svg))
        b.close()
    srv.shutdown()


if __name__ == "__main__":
    main()
