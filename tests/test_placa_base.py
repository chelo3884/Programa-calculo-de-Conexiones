"""Verificación del motor contra (1) la hoja de Excel original y (2) AISC DG Examples J.6."""
import json
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from placa_base.engine import calcular  # noqa: E402

HERE = os.path.dirname(__file__)

# fila de la hoja CALCULO → clave de ratio del motor
FILAS = {92: "ap", 100: "pc", 101: "pt", 105: "sa", 109: "arr", 112: "pull", 115: "sb",
         119: "vsa", 122: "vcb", 125: "pry", 128: "int", 130: "wf", 131: "ww"}


class TestExcel(unittest.TestCase):
    def test_ratios_vs_excel(self):
        with open(os.path.join(HERE, "fixture_excel_ejemplo.json"), encoding="utf-8") as fh:
            fx = json.load(fh)
        res = calcular(fx["inputs"])
        for i, exp in enumerate(fx["expected_rows"]):
            c = res["combos"][i]
            for fila, key in FILAS.items():
                esperado = exp.get(str(fila), 0.0)
                self.assertAlmostEqual(c["ratios"][key], esperado, places=6,
                                       msg=f"combo {c['nombre']} fila {fila} ({key})")
            self.assertAlmostEqual(c["ratio_max"], exp["132"], places=6)
            self.assertAlmostEqual(c["tp_req_mm"], exp.get("102", 0.0), places=6)


class TestAISCJ6(unittest.TestCase):
    """AISC Design Examples v15, Ej. J.6: W12x96 sobre pedestal, Pu = 690 kips, PL 22x22 A36, f'c = 3 ksi."""

    def test_j6(self):
        inch, kip, ksi = 25.4, 0.45359237, 70.307
        inp = {
            "perfil": "ARMADO (flejes soldados)",
            "armado": {"d": 12.7 * inch, "bf": 12.2 * inch, "tw": 0.55 * inch, "tf": 0.9 * inch},
            "placa": {"acero": "Personalizado", "Fy": 36 * ksi, "N": 22 * inch, "B": 22 * inch,
                      "tp": 2 * inch, "grout": 25},
            "pernos": {"material": "F1554 Gr55", "diam": '1"', "nfila": 2, "eN": 50, "eB": 50,
                       "hef": 500, "arandela_lado": 0, "arandela_t": 0, "arandela_sold": "No", "nv": 4},
            "pedestal": {"fc": 3 * ksi, "Np": 24 * 2.54, "Bp": 24 * 2.54, "fisurado": "Sí",
                         "ref_borde": "No", "hp_usar": "No", "hp_n": 0, "hp_db": 16, "hp_fy": 4200},
            "sold": {"electrodo": "E70XX", "wf": 8, "ww": 6},
            "sismo": {"sismo": "No", "omega0": 1},
            "combos": [{"nombre": "1.2D+1.6L", "P": 690 * kip, "V": 0, "M": 0}],
        }
        r = calcular(inp)
        g = r["geom"]
        self.assertAlmostEqual(g["m"] / 2.54, 4.97, places=2)
        self.assertAlmostEqual(g["n"] / 2.54, 6.12, places=2)
        self.assertAlmostEqual(g["np"] / 2.54, 3.11, places=2)
        c = r["combos"][0]
        self.assertEqual(c["caso"], 1)
        # φc·Pp = 875 kips  → ratio de aplastamiento = 690/875
        self.assertAlmostEqual(c["ratios"]["ap"], 690 / 875, delta=0.002)
        # fpu = 1.43 ksi ; l = 6.12 in ; tmin = 1.82 in
        self.assertAlmostEqual(c["fp"] / ksi, 1.43, places=2)
        self.assertAlmostEqual(c["l"] / 2.54, 6.12, places=2)
        self.assertAlmostEqual(c["tp_req_mm"] / inch, 1.82, places=2)


if __name__ == "__main__":
    unittest.main()
