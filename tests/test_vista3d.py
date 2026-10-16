"""Visor 3D: todas las conexiones del catálogo tienen modelo 3D y sus páginas cargan el visor."""
import os
import re
import sys
import unittest

RAIZ = os.path.join(os.path.dirname(__file__), "..")
WEB = os.path.join(RAIZ, "web")


class TestVista3D(unittest.TestCase):
    def test_cada_conexion_tiene_modelo(self):
        ids = re.findall(r"\{id:'([a-z_]+)',cat:", open(os.path.join(WEB, "modulos.js"), encoding="utf-8").read())
        modelos = set(re.findall(r"^M\.([a-z_]+)=", open(os.path.join(WEB, "model3d.js"), encoding="utf-8").read(), re.M))
        self.assertGreaterEqual(len(ids), 19)
        self.assertEqual(sorted(set(ids) - modelos), [], "conexiones sin modelo 3D")

    def test_paginas_cargan_el_visor(self):
        ids = re.findall(r"\{id:'([a-z_]+)',cat:", open(os.path.join(WEB, "modulos.js"), encoding="utf-8").read())
        for i in ids:
            t = open(os.path.join(WEB, i + ".html"), encoding="utf-8").read()
            self.assertIn("/viewer3d.js", t, i)
            self.assertIn("/model3d.js", t, i)


if __name__ == "__main__":
    unittest.main()
