"""Cortante viga–columna: coherencia con cortante_vv y verificación con AISC Design Examples v15, Ej. II.A-1A."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from cortante_vc.engine import COLUMNAS, calcular  # noqa: E402
from cortante_vv.engine import calcular as calcular_vv  # noqa: E402

INCH, KIP = 25.4, 0.45359237


def _cap(res, nombre):
    return next(c for c in res["checks"] if c["nombre"].startswith(nombre))["cap"]


class TestCortanteVC(unittest.TestCase):
    def test_equivale_a_vv_con_ala_como_soporte(self):
        d, bf, tw, tf = COLUMNAS["HA500X250X10X15"]
        base = {"tipo": "Placa simple convencional", "Ru": 7, "n_b": 4}
        vc = calcular(dict(base, co_perfil="HA500X250X10X15"))
        vv = calcular_vv(dict(base, destaje="Sin destaje", Ru_op=0, vg_nivel="No aplica", vp_perfil="ARMADO (flejes soldados)",
                              DIS_E29=d, DIS_E30=bf, DIS_E31=tf, DIS_E32=tf))
        self.assertEqual(len(vc["checks"]), len(vv["checks"]))
        for a, b in zip(vc["checks"], vv["checks"]):
            self.assertEqual(a["ratio"], b["ratio"])
        # el filete mínimo se verifica contra el ala de la columna (tf = 15 mm)
        n = next(c for c in vc["checks"] if c["nombre"].startswith("Ala de columna: t ≥ tmín"))
        self.assertEqual(n["cap"], 15)

    def test_aisc_ej_II_A_1A(self):
        """W36x231 a ala de W14x90, 8 pernos Ø3/4" A325-N, 2L5x3½x5/16 (SLBB), A36, Ru = 226 kip."""
        inp = {"tipo": "Doble ángulo apernado", "Ru": 226 * KIP,
               "vg_perfil": "ARMADO (flejes soldados)", "DIS_E16": 36.5 * INCH, "DIS_E17": 16.5 * INCH,
               "DIS_E18": 0.76 * INCH, "DIS_E19": 1.26 * INCH, "vg_acero": "A992",
               "co_perfil": "ARMADO (flejes soldados)", "co_E_d": 14 * INCH, "co_E_bf": 14.5 * INCH,
               "co_E_tw": 0.44 * INCH, "co_E_tf": 0.71 * INCH, "co_acero": "A992",
               "pn_grado": "A325-N (roscas incl.)", "pn_diam": '3/4"', "n_b": 8, "pn_s": 3 * INCH, "pn_top": 50,
               "pn_Lev": 1.25 * INCH, "agujero": "STD", "an_acero": "A36", "an_lb": 3.5 * INCH, "an_ls": 5 * INCH,
               "an_t": 5 / 16 * INCH, "an_gb": 2 * INCH, "an_gs": 2.5 * INCH, "setback": 13}
        r = calcular(inp)
        # φrn por perno en doble corte, Manual Tabla 7-1: 35.8 kip
        self.assertAlmostEqual(_cap(r, "Corte en pernos (perno crítico)") / KIP, 35.8, delta=0.1)
        # aplastamiento del alma de la viga, J3.10: 66.7 kip/perno
        self.assertAlmostEqual(_cap(r, "Aplastamiento / desgarre — alma de viga") / KIP, 66.7, delta=0.2)
        # 8 pernos en corte simple en el lado de soporte: 8 × 35.8 = 286 kip
        self.assertAlmostEqual(_cap(r, "Corte en pernos (2n") / KIP, 286.3, delta=1.0)
        # el ala de la columna (0.71 in) es más gruesa que los ángulos: no gobierna el aplastamiento
        self.assertGreater(_cap(r, "Aplastamiento — ala de columna"), _cap(r, "Aplastamiento / desgarre — alas de ángulo"))


if __name__ == "__main__":
    unittest.main()
