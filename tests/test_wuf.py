"""Viga–columna soldada directa (wuf): capacidades contra AISC Design Examples v15, Ej. II.B-1 / II.B-3.
W18x50 (A992) a ala de W14x99 (A992); placa simple PL 3/8 in A36, 3 pernos Ø7/8" A325-N, s = 3 in, Lev = 1½ in,
Leh = 2 in, filetes de ¼ in; Mu = 252 kip-ft, Vu = 42 kip."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from wuf.engine import calcular  # noqa: E402

IN, KIP = 25.4, 0.45359237


def _inp(**kw):
    inp = {"vg_perfil": "ARMADO (flejes soldados)", "vg_E_d": 18 * IN, "vg_E_bf": 7.5 * IN, "vg_E_tw": 0.355 * IN,
           "vg_E_tf": 0.57 * IN, "vg_acero": "A992",
           "co_perfil": "ARMADO (flejes soldados)", "co_E_d": 14.2 * IN, "co_E_bf": 14.6 * IN, "co_E_tw": 0.485 * IN,
           "co_E_tf": 0.78 * IN, "co_acero": "A992", "co_kw": (1.38 - 0.78) * IN, "co_dtop": 1500, "cp_usar": "No",
           "Pu_col": 0, "pl_acero": "A36", "pl_t": 3 / 8 * IN, "pl_n": 3, "pl_s": 3 * IN, "pl_lev": 1.5 * IN,
           "pl_leh": 2 * IN, "pl_w": 0.25 * IN,
           "combos": [{"nombre": "1.2D+1.6L", "M": 252 * 12 * 0.0254 * KIP, "V": 42 * KIP}]}
    inp.update(kw)
    return inp


def _cap(res, nombre):
    return next(c for c in res["checks"] if c["nombre"].startswith(nombre))["cap"] / KIP


class TestWUF(unittest.TestCase):
    def setUp(self):
        self.r = calcular(_inp())

    def test_placa_simple_II_B_1(self):
        self.assertAlmostEqual(_cap(self.r, "Pernos en la placa"), 68.8, delta=0.3)          # 1·20.2 + 2·24.3
        self.assertAlmostEqual(_cap(self.r, "Pernos en el alma"), 72.9, delta=0.4)           # 3·24.3
        self.assertAlmostEqual(_cap(self.r, "Placa: fluencia"), 73.0, delta=0.3)
        self.assertAlmostEqual(_cap(self.r, "Placa: ruptura"), 58.7, delta=0.3)
        self.assertAlmostEqual(_cap(self.r, "Placa: bloque"), 69.9, delta=0.4)
        self.assertAlmostEqual(_cap(self.r, "Filetes placa"), 100, delta=0.6)
        self.assertAlmostEqual(_cap(self.r, "Ala de la columna: ruptura"), 410, delta=1.5)

    def test_columna_J10_II_B_1(self):
        self.assertAlmostEqual(_cap(self.r, "Flexión local del ala"), 171, delta=0.6)

    def test_rigidizadores_desactivan_chequeos_J10(self):
        r = calcular(_inp(cp_usar="Sí", cp_t=15, cp_b=110))
        sin = {c["nombre"]: c for c in r["checks"]}
        self.assertIsNone(sin["Flexión local del ala de la columna"]["ratio"])
        self.assertIsNotNone(sin["Rigidizadores de continuidad: Fsu ≤ φRn"]["ratio"])

    def test_combinacion_gobernante_y_estado(self):
        r = calcular(_inp(combos=[{"nombre": "bajo", "M": 5, "V": 2}, {"nombre": "alto", "M": 30, "V": 10}]))
        zp = next(c for c in r["checks"] if c["nombre"].startswith("Zona de panel"))
        self.assertEqual(zp["combo"], "alto")


if __name__ == "__main__":
    unittest.main()
