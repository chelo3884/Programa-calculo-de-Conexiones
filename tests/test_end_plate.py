"""Verificación del motor de placa extrema contra la hoja de Excel (variantes recalculadas con LibreOffice)."""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from end_plate.engine import calcular  # noqa: E402

HERE = os.path.dirname(__file__)
with open(os.path.join(HERE, "fixture_end_plate.json"), encoding="utf-8") as fh:
    FX = json.load(fh)


def _num(a, b):
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(a - b) <= 1e-7 * max(1.0, abs(b))
    return a == b


class TestEndPlateVsExcel(unittest.TestCase):
    def _run(self, nombre):
        fx = FX[nombre]
        inp = dict(fx["cambios"])
        inp["combos"] = [{"nombre": n, "M": m, "V": v} for n, m, v in fx["combos"]]
        res = calcular(inp)
        raw = res["raw"]
        for r, esperado in fx["global"].items():
            self.assertTrue(_num(raw["global"][int(r)], esperado), f"{nombre} fila global {r}: {raw['global'][int(r)]} ≠ {esperado}")
        for r, vals in fx["rows"].items():
            for j, esperado in enumerate(vals):
                got = raw["rows"][int(r)][j]
                self.assertTrue(_num(got, esperado), f"{nombre} fila {r} combo {j+1}: {got} ≠ {esperado}")
        por_fila = {c["fila"]: c for c in res["checks"]}
        for r, (p, q, s) in fx["checks"].items():
            c = por_fila[int(r)]
            for got, esperado, que in ((c["dem"], p, "demanda"), (c["cap"], q, "capacidad"), (c["ratio"], s, "ratio")):
                if isinstance(esperado, (int, float)):
                    self.assertTrue(_num(got, esperado), f"{nombre} chequeo {r} {que}: {got} ≠ {esperado}")
                else:
                    self.assertIsNone(got, f"{nombre} chequeo {r} {que}: se esperaba N/A")
        return res

    def test_variantes(self):
        for nombre in FX:
            with self.subTest(nombre):
                self._run(nombre)

    def test_resumen_base(self):
        r = self._run("base_4E")
        self.assertEqual(r["resumen"]["estado"], "CUMPLE")
        self.assertAlmostEqual(r["resumen"]["ratio_max"], 0.9, places=6)


if __name__ == "__main__":
    unittest.main()
