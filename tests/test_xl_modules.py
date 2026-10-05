"""Verificación de los módulos generados desde Excel (end_plate, bfp, rodilla).

Cada variante de tests/fixtures/<módulo>.json es una copia de la hoja de Excel con entradas modificadas y
recalculada con LibreOffice Calc (tools/make_fixtures.py). Se comparan todas las filas de CALCULO y la tabla
de verificaciones (demanda, capacidad y ratio).
"""
import importlib
import json
import os
import sys
import unittest

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, ROOT)
HERE = os.path.dirname(__file__)


def _igual(got, esperado):
    if esperado is None:
        return got is None or got == ""
    if esperado == "ERR":
        return got is None
    if isinstance(esperado, (int, float)) and isinstance(got, (int, float)) and not isinstance(got, bool):
        return abs(got - esperado) <= 1e-7 * max(1.0, abs(esperado))
    if isinstance(esperado, bool) or isinstance(got, bool):
        return bool(got) == bool(esperado)
    return got == esperado


class _Base:
    modulo = None

    @classmethod
    def setUpClass(cls):
        cls.eng = importlib.import_module(f"{cls.modulo}.engine")
        with open(os.path.join(HERE, "fixtures", f"{cls.modulo}.json"), encoding="utf-8") as fh:
            cls.FX = json.load(fh)

    def _run(self, nombre):
        fx = self.FX[nombre]
        inp = dict(fx["cambios"])
        inp["combos"] = fx["combos"]
        res = self.eng.calcular(inp)
        raw = res["raw"]
        for r, esperado in fx["global"].items():
            self.assertTrue(_igual(raw["global"].get(int(r)), esperado), f"{nombre} fila global {r}: {raw['global'].get(int(r))} ≠ {esperado}")
        for r, vals in fx["rows"].items():
            for j, esperado in enumerate(vals):
                got = raw["rows"][int(r)][j]
                self.assertTrue(_igual(got, esperado), f"{nombre} fila {r} combo {j + 1}: {got} ≠ {esperado}")
        por_fila = {c["fila"]: c for c in res["checks"]}
        for r, (p, q, s) in fx["checks"].items():
            c = por_fila[int(r)]
            for got, esperado, que in ((c["dem"], p, "demanda"), (c["cap"], q, "capacidad"), (c["ratio"], s, "ratio")):
                if isinstance(esperado, (int, float)) and not isinstance(esperado, bool):
                    self.assertTrue(_igual(got, esperado), f"{nombre} chequeo {r} {que}: {got} ≠ {esperado}")
                else:
                    self.assertIsNone(got, f"{nombre} chequeo {r} {que}: se esperaba N/A, llegó {got}")
        return res

    def test_variantes(self):
        for nombre in self.FX:
            with self.subTest(nombre):
                self._run(nombre)


class TestEndPlate(_Base, unittest.TestCase):
    modulo = "end_plate"

    def test_resumen_base(self):
        r = self._run("base_4E")
        self.assertEqual(r["resumen"]["estado"], "CUMPLE")
        self.assertAlmostEqual(r["resumen"]["ratio_max"], 0.9, places=6)


class TestBFP(_Base, unittest.TestCase):
    modulo = "bfp"


class TestRodilla(_Base, unittest.TestCase):
    modulo = "rodilla"


class TestCortanteVV(_Base, unittest.TestCase):
    modulo = "cortante_vv"


class TestEmpalmeColumna(_Base, unittest.TestCase):
    modulo = "empalme_col"


class TestEmpalmeViga(_Base, unittest.TestCase):
    modulo = "empalme_viga"


if __name__ == "__main__":
    unittest.main()
