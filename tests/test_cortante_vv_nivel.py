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

    def test_extendida_evita_destaje(self):
        r = calcular({"tipo": "Placa simple extendida", "destaje": "Destaje superior", "cope_dc": 30, "pl_a": 130})
        self.assertAlmostEqual(r["derivados"]["setback_ef"], 15 + (180 - 6) / 2)       # holgura + (bfg − twg)/2: el extremo de la viga queda fuera del ala
        self.assertEqual(r["raw"]["global"][20], 0)                                    # destaje superior anulado (c_top)
        self.assertEqual(_c(r, "Destaje superior libra")["estado"], "N/A")
        self.assertEqual(_c(r, "Destaje superior: longitud")["estado"], "N/A")

    def test_convencional_no_cambia_el_extremo(self):
        r = calcular({})
        self.assertEqual(r["derivados"]["setback_ef"], 15)

    def test_placa_en_T(self):
        r = calcular({"tipo": "Placa simple extendida", "pl_a": 150, "pl_w": 8})
        g = r["raw"]["global"]
        self.assertEqual(g[101], 1)                                                   # placa en T
        self.assertAlmostEqual(g[102], 10.2 - 1.0)                                    # xs = setback_ef − 10 mm
        self.assertAlmostEqual(g[103], (40 - 1.2 - 1) - (0 + 2.2), places=6)          # Hs: del borde superior a 10 mm sobre el ala inferior
        # Mu de la lengüeta = Ru·(a − xs), no Ru·a
        self.assertAlmostEqual(g[65], 6000 * (15.0 - 9.2))
        self.assertLess(_c(r, "Placa en T")["ratio"], 1)
        self.assertEqual(_c(calcular({}), "Placa en T")["estado"], "N/A")             # convencional: no aplica


if __name__ == "__main__":
    unittest.main()
