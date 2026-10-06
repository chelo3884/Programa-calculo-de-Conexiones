"""Placa de recorte (diafragma externo) contra el cálculo Tedds «HSS cutout plate» (W10x68 en HSS10x0.500, Mr = 209 kip-ft).

Se comparan las resistencias NOMINALES (las únicas correctas en esa hoja: multiplica por 2.00 en lugar de aplicar φ) y se documenta
que el bloque de cortante de la hoja usa un solo plano de cortante con dos filas de pernos (aquí se usan dos)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from hss_diafragma.engine import HOYOS, calcular  # noqa: E402

IN, KIP, KFT = 25.4, 0.45359237, 0.138255


def _inp(**kw):
    d = {"vg_perfil": "ARMADO (flejes soldados)", "vg_E_d": 10.4 * IN, "vg_E_bf": 10.1 * IN, "vg_E_tw": 0.47 * IN, "vg_E_tf": 0.77 * IN,
         "vg_acero": "A992", "hss_perfil": "ARMADO (flejes soldados)", "hss_W": 10 * IN, "hss_D": 10 * IN, "hss_t": 0.465 * IN, "hss_acero": "A500 Gr C",
         "pr_acero": "A36", "pr_t": 0.75 * IN, "pr_ws": 2 * IN, "pr_w1": 6 * IN, "pr_d1": 4 * IN, "pr_nb": 4, "pr_s": 3 * IN, "pr_g": 3 * IN,
         "pr_le": 1.75 * IN, "pr_lef": 4 * IN, "pn_diam": '1"', "agujero": HOYOS[1], "pr_w": 0.5 * IN,
         "combos": [{"nombre": "Mr = 209 kip-ft", "M": 209 * KFT, "V": 5}]}
    d.update(kw)
    return d


def _c(r, nombre):
    return next(c for c in r["checks"] if c["nombre"].startswith(nombre))


class TestDiafragma(unittest.TestCase):
    def setUp(self):
        self.r = calcular(_inp())

    def test_demanda_y_pernos(self):
        corte = _c(self.r, "Corte de los pernos")
        self.assertAlmostEqual(corte["dem"] / KIP, 224.9, delta=0.4)                       # Pr_bf = 224.933 kips
        self.assertAlmostEqual(corte["cap"] / KIP, 254.47, delta=0.2)                      # 8 pernos · 31.8 kips

    def test_aplastamiento_nominal(self):
        # nominal de la hoja: 733.88 kip en la placa → φRn = 0.75·733.88 = 550.4 kip
        self.assertAlmostEqual(_c(self.r, "Aplastamiento en la placa")["cap"] / KIP, 0.75 * 733.88, delta=0.5)

    def test_bloque_de_cortante_placa_dos_planos(self):
        # La hoja usa UN plano de cortante (Agv = Le + 3s)·tp = 8.06 in²) con dos filas de pernos; con los dos planos de cortante
        # (como en DG24 Ej. 4.2): Agv = 16.125, Anv = 10.22, Ant = 1.41 in² → Rn = 430 kip, φRn = 322.6 kip.
        cap = _c(self.r, "Bloque de cortante de la placa")["cap"] / KIP
        self.assertAlmostEqual(cap, 0.75 * 430.1, delta=1.5)
        self.assertLess(_c(self.r, "Bloque de cortante de la placa")["ratio"], 1.0)

    def test_franja_comprimida_no_cumple_como_en_la_hoja(self):
        self.assertGreater(_c(self.r, "Compresión de las franjas")["ratio"], 1.0)          # la hoja también reporta FAIL
        self.assertAlmostEqual(_c(self.r, "Franja junto al HSS")["dem"], 2 / 0.75, places=2)

    def test_opcion_de_agujero(self):
        r16 = calcular(_inp(agujero=HOYOS[0]))
        self.assertLess(_c(r16, "Aplastamiento en la placa")["cap"], _c(self.r, "Aplastamiento en la placa")["cap"])


if __name__ == "__main__":
    unittest.main()
