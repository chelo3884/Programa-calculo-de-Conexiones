"""Conexión a columna HSS (cortante_hss) contra AISC Design Examples v15, Ej. K.6 (placa simple) y K.7 (placa pasante)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from cortante_hss.engine import calcular  # noqa: E402

IN, KIP = 25.4, 0.45359237


def _inp(**kw):
    inp = {"hss_perfil": "ARMADO (flejes soldados)", "hss_W": 6 * IN, "hss_D": 6 * IN, "hss_t": 0.349 * IN, "co_acero": "A500 Gr C",
           "Ru": 39.0 * KIP, "pl_tp": 5 / 16 * IN, "pl_a": 3 * IN, "pl_Leh": 2 * IN, "pl_w": 0.25 * IN, "n_b": 3,
           "pn_s": 3 * IN, "pn_Lev": 1.25 * IN, "pn_top": 3 * IN, "vg_perfil": "ARMADO (flejes soldados)",
           "DIS_E16": 17.7 * IN, "DIS_E17": 6 * IN, "DIS_E18": 0.3 * IN, "DIS_E19": 0.425 * IN,
           "pn_diam": '3/4"', "pn_grado": "A325-N (roscas incl.)", "pl_acero": "A36"}
    inp.update(kw)
    return inp


def _c(res, nombre):
    return next(c for c in res["checks"] if c["nombre"].startswith(nombre))


class TestHSS(unittest.TestCase):
    def test_K6_placa_simple(self):
        r = calcular(_inp())
        bt = _c(r, "Pared no esbelta")
        self.assertAlmostEqual(bt["dem"], 14.2, delta=0.05)                          # b/t = 14.2
        self.assertAlmostEqual(bt["cap"], 33.7, delta=0.05)                          # 1.40√(E/Fy) = 33.7
        pz = _c(r, "Punzonamiento")
        self.assertAlmostEqual(pz["dem"] / (KIP * 2.54 / 100), 117, delta=0.5)       # 39 kip · 3 in = 117 kip-in
        self.assertAlmostEqual(pz["cap"] / (KIP * 2.54 / 100), 235, delta=1.0)       # 235 kip-in
        tm = _c(r, "Pared del HSS: t")
        self.assertAlmostEqual(tm["dem"] / IN, 0.199, delta=0.002)                   # 3.09·D/Fu

    def test_K7_placa_pasante(self):
        r = calcular(_inp(hss_W=6 * IN, hss_D=4 * IN, hss_t=0.116 * IN, Ru=19.8 * KIP, pl_tp=0.25 * IN,
                          pl_w=3 / 16 * IN, hss_conex="Placa pasante (through-plate)"))
        self.assertEqual(_c(r, "Pared no esbelta")["ratio"], None)                   # pared esbelta: no aplica
        self.assertIsNone(_c(r, "Punzonamiento")["ratio"])
        self.assertAlmostEqual(_c(r, "Placa pasante: fluencia")["cap"] / KIP, 59.2, delta=0.3)
        self.assertAlmostEqual(_c(r, "Placa pasante: ruptura")["cap"] / KIP, 55.0, delta=0.3)
        self.assertAlmostEqual(_c(r, "Placa pasante: fluencia")["dem"] / KIP, 34.7, delta=0.1)   # Vfu = Ru·(B + a)/B = 34.7 kip
        self.assertEqual(_c(r, "Placa pasante: soldadura")["estado"], "CUMPLE")

    def test_catalogo_hss_y_cara(self):
        r1 = calcular(_inp(hss_perfil="HSS6X6X3/8"))
        self.assertIn("co_bt", r1["derivados"])


if __name__ == "__main__":
    unittest.main()
