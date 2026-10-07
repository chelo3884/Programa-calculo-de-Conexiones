"""Cortante viga–viga: nivel relativo de las vigas y destaje requerido por el ala de la viga principal."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from cortante_vv.engine import calcular  # noqa: E402


def _c(r, ini):
    return next(c for c in r["checks"] if c["nombre"].startswith(ini))


class TestNivel(unittest.TestCase):
    def test_alas_al_ras_exige_destaje(self):
        r = calcular({"destaje": "Sin destaje"})                         # viga principal con ala de 12 mm y 180 mm de ancho
        a = _c(r, "Destaje superior libra")
        self.assertEqual(a["estado"], "NO CUMPLE")
        self.assertAlmostEqual(a["dem"], 2.2)                           # tfg − dz + 1 cm = 1.2 + 1.0
        self.assertLess(a["ratio"], 100)                                # ya no explota (÷1e-9)

    def test_destaje_adecuado_cumple(self):
        r = calcular({"cope_dc": 30, "cope_c": 100})
        self.assertNotEqual(_c(r, "Destaje superior libra")["estado"], "NO CUMPLE")
        self.assertNotEqual(_c(r, "Destaje superior: longitud")["estado"], "NO CUMPLE")        # (18 − 0.6)/2 − 1.5 + 1 = 8.2 cm ≤ 10

    def test_centrada_sin_destaje(self):
        r = calcular({"vg_nivel": "Centrada", "destaje": "Sin destaje"})
        self.assertEqual(r["raw"]["global"][100], 5.0)                  # (40 − 30)/2 cm
        self.assertEqual(_c(r, "Destaje superior libra")["estado"], "N/A")

    def test_no_aplica(self):
        r = calcular({"vg_nivel": "No aplica"})
        self.assertEqual(_c(r, "Placa/ángulos bajo el ala")["estado"], "N/A")


if __name__ == "__main__":
    unittest.main()
