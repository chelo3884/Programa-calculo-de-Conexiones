"""Cartela UFM: equilibrio de las fuerzas de interfaz y estados límite de la cartela contra AISC Design Examples v15 (II.C-3)."""
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from gusset.engine import calcular, ufm  # noqa: E402

IN, KIP = 25.4, 0.45359237


def _inp(**kw):
    inp = {"vg_perfil": "ARMADO (flejes soldados)", "vg_E_d": 18 * IN, "vg_E_bf": 7.5 * IN, "vg_E_tw": 0.355 * IN,
           "vg_E_tf": 0.57 * IN, "vg_acero": "A992", "co_perfil": "ARMADO (flejes soldados)", "co_E_d": 14.2 * IN,
           "co_E_bf": 14.6 * IN, "co_E_tw": 0.485 * IN, "co_E_tf": 0.78 * IN, "co_acero": "A992",
           "g_acero": "A36", "g_np": 2, "g_t": 3 / 8 * IN, "g_a": 20 * IN, "g_b": 20 * IN, "g_theta": 45,
           "pn_diam": '1"', "pn_grado": "A325-N (roscas incl.)", "b_n": 5, "b_nl": 2, "b_s": 3 * IN, "b_g": 5.5 * IN,
           "b_le": 2 * IN, "b_tbr": 0.75 * IN, "b_fu": 58 * 70.307, "g_K": 0.65, "g_Lc": 3 * IN,
           "combos": [{"nombre": "T", "P": 40 * KIP}, {"nombre": "C", "P": -40 * KIP}]}
    inp.update(kw)
    return inp


def _cap(res, nombre):
    return next(c for c in res["checks"] if c["nombre"].startswith(nombre))["cap"] / KIP


class TestGusset(unittest.TestCase):
    def test_equilibrio_ufm(self):
        for th, eb, ec, a, b in ((45, 20, 25, 50, 50), (35, 22.8, 18, 60, 45), (60, 30, 15, 40, 70)):
            u = ufm(100.0, th, eb, ec, a, b)
            t = math.radians(th)
            self.assertAlmostEqual(u["Hb"] + u["Hc"], 100 * math.cos(t), places=9)
            self.assertAlmostEqual(u["Vb"] + u["Vc"], 100 * math.sin(t), places=9)
            self.assertAlmostEqual(u["Vc"] / u["Hc"], u["beta"] / ec, places=9)
            self.assertAlmostEqual(u["Hb"] / u["Vb"], u["alpha"] / eb, places=9)

    def test_II_C_3_cartela(self):
        r = calcular(_inp())
        self.assertAlmostEqual(_cap(r, "Whitmore: fluencia"), 473, delta=4)       # lw = 19.4 in, 2 placas
        self.assertAlmostEqual(_cap(r, "Bloque de cortante"), 480, delta=2)
        v = r["vars"]
        self.assertAlmostEqual(v["lw"] / 2.54, 19.4, delta=0.05)

    def test_signo_de_la_carga(self):
        r = calcular(_inp())
        t = next(c for c in r["combos"] if c["nombre"] == "T")
        cmp_ = next(c for c in r["combos"] if c["nombre"] == "C")
        self.assertTrue(t["activo"] and cmp_["activo"])
        nombres = {c["nombre"]: c for c in r["checks"]}
        self.assertEqual(nombres["Whitmore: pandeo en compresión"]["combo"], "C")
        self.assertEqual(nombres["Whitmore: fluencia en tracción"]["combo"], "T")


if __name__ == "__main__":
    unittest.main()
