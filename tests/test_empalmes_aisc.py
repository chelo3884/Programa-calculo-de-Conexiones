"""Empalmes de viga y de columna: verificación con AISC Design Examples v15.

El PDF no trae un empalme de viga/columna completo; se verifican los estados límite que comparten con los
ejemplos de conexiones con placas de ala y de alma atornilladas:
  · II.B-1  placa de ala atornillada W18x50 (7 in × ¾ in A36, 8 pernos Ø7/8" A325-N, s = 3 in, gramil 4 in)
  · II.A-20 placa simple de alma (12 in × ⅜ in A36, 4 pernos Ø7/8" A325-N, s = 3 in, bordes 1½ in)
  · II.C-3  resistencia al deslizamiento de un perno Ø1" A325 clase A (17.3 kip)
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from empalme_col.engine import calcular as calcular_col  # noqa: E402
from empalme_viga.engine import calcular as calcular_viga  # noqa: E402

INCH, KIP, KIPFT = 25.4, 0.45359237, 0.45359237 * 0.3048   # Tonf por kip; Tonf·m por kip-ft


def _cap(res, nombre):
    return next(c for c in res["checks"] if c["nombre"].startswith(nombre))["cap"]


def _viga(**kw):
    inp = {"vg_perfil": "ARMADO (flejes soldados)", "DIS_E12": 18 * INCH, "DIS_E13": 7.5 * INCH,
           "DIS_E14": 0.355 * INCH, "DIS_E15": 0.57 * INCH, "vg_acero": "A992", "vg_kw": 15, "gap": 10,
           "junta": "Aplastamiento", "dist_M": "No (solo alas)",
           "pf_acero": "A36", "pf_bo": 7 * INCH, "pf_to": 0.75 * INCH, "pf_in": "No", "pf_bi": 70, "pf_ti": 0,
           "fa_grado": "A325-N (roscas incl.)", "fa_diam": '7/8"', "fa_n": 4, "fa_g": 4 * INCH, "fa_s": 3 * INCH,
           "fa_Leb": 1.75 * INCH, "fa_Lep": 1.5 * INCH,
           "pw_acero": "A36", "pw_h": 12 * INCH, "pw_t": 3 / 8 * INCH, "wa_grado": "A325-N (roscas incl.)",
           "wa_diam": '7/8"', "wa_nr": 4, "wa_nc": 1, "wa_sv": 3 * INCH, "wa_sh": 75, "wa_Leb": 1.5 * INCH,
           "wa_Lep": 1.5 * INCH,
           "combos": [{"nombre": "x", "M": 252 * 12 * 0.0254 * KIP, "V": 42 * KIP}]}
    inp.update(kw)
    return inp


class TestEmpalmeVigaAISC(unittest.TestCase):
    def setUp(self):
        self.r = calcular_viga(_viga())
        self.g = self.r["raw"]["global"]

    def test_pernos_de_ala_II_B_1(self):
        # 8 pernos × 24.3 kip (Tabla 7-1) = 194 kip
        self.assertAlmostEqual(_cap(self.r, "Pernos de ala — corte") / KIP, 194.4, delta=0.8)

    def test_placa_de_ala_fluencia_ruptura_II_B_1(self):
        self.assertAlmostEqual(_cap(self.r, "Placas de ala — fluencia") / KIP, 170, delta=0.5)      # φFyAg = 170 kip
        self.assertAlmostEqual(_cap(self.r, "Placas de ala — ruptura") / KIP, 164, delta=1.0)      # φFuAe = 164 kip

    def test_bloque_de_cortante_placa_II_B_1(self):
        self.assertAlmostEqual(_cap(self.r, "Placas de ala — bloque de cortante") / KIP, 320, delta=1.5)   # caso 1

    def test_ruptura_del_ala_de_viga_F13_1(self):
        # φMn = 318 kip-ft; el programa calcula Sx con la fórmula simplificada de la hoja (≈ 1 % menor)
        self.assertAlmostEqual(_cap(self.r, "Viga — agujeros") / KIPFT, 318, delta=318 * 0.015)

    def test_placa_de_alma_II_A_20(self):
        # 2 placas (una por lado): cada una resiste lo del ejemplo (ruptura por corte 78.0 kip, bloque 80.1 kip)
        self.assertAlmostEqual(self.g[69] / 1000 / KIP / 2, 78.0, delta=0.6)
        self.assertAlmostEqual(_cap(self.r, "Placas de alma — bloque") / KIP / 2, 80.1, delta=0.8)
        self.assertAlmostEqual(self.g[68] / 1000 / KIP / 2, 97.2, delta=0.5)                                # fluencia por corte

    def test_deslizamiento_II_C_3(self):
        r = calcular_viga(_viga(junta="Deslizamiento crítico clase A (μ = 0.30)", fa_grado="A325-N (roscas incl.)",
                                fa_diam='1"'))
        self.assertAlmostEqual(r["raw"]["global"][29] / 1000 / KIP, 17.3, delta=0.05)


class TestEmpalmeColumnaAISC(unittest.TestCase):
    def _col(self, **kw):
        inp = {"tipo": "Placas apernadas", "fresado": "No", "sismico": "No", "dist_v": 2000, "gap": 3,
               "cu_perfil": "ARMADO (flejes soldados)", "DIS_E18": 14.2 * INCH, "DIS_E19": 14.6 * INCH,
               "DIS_E20": 0.485 * INCH, "DIS_E21": 0.78 * INCH, "cu_acero": "A992",
               "cl_perfil": "ARMADO (flejes soldados)", "DIS_E26": 14.2 * INCH, "DIS_E27": 14.6 * INCH,
               "DIS_E28": 0.485 * INCH, "DIS_E29": 0.78 * INCH, "cl_acero": "A992",
               "pf_acero": "A36", "pf_b": 7 * INCH, "pf_t": 0.75 * INCH,
               "fa_grado": "A325-N (roscas incl.)", "fa_diam": '7/8"', "junta": "Aplastamiento", "fa_n": 4,
               "fa_g": 4 * INCH, "fa_s": 3 * INCH, "fa_Lec": 1.75 * INCH, "fa_Lep": 1.5 * INCH,
               "combos": [{"nombre": "x", "P": 5, "M": 20, "V": 3}]}
        inp.update(kw)
        return calcular_col(inp)

    def test_placa_de_ala_como_II_B_1(self):
        r = self._col()
        self.assertAlmostEqual(_cap(r, "Pernos de ala — corte") / KIP, 194.4, delta=0.8)
        self.assertAlmostEqual(_cap(r, "Placa de ala — fluencia") / KIP, 170, delta=0.5)
        self.assertAlmostEqual(_cap(r, "Placa de ala — ruptura") / KIP, 164, delta=1.0)
        self.assertAlmostEqual(_cap(r, "Placa de ala — bloque") / KIP, 320, delta=1.5)

    def test_deslizamiento_II_C_3(self):
        r = self._col(junta="Deslizamiento crítico clase A (μ = 0.30)", fa_diam='1"')
        self.assertAlmostEqual(r["raw"]["global"][40] / 1000 / KIP, 17.3, delta=0.05)


if __name__ == "__main__":
    unittest.main()
