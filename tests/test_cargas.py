import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import cargas  # noqa: E402


def _por_nombre(lista):
    return {c["nombre"]: c for c in lista}


class TestNEC(unittest.TestCase):
    def test_solo_D_y_L(self):
        r = _por_nombre(cargas.generar({"D": {"P": 10, "M": 2}, "L": {"P": 5, "M": 1}}, ["P", "M"]))
        self.assertEqual(set(r), {"1.4D", "1.2D+1.6L"})
        self.assertAlmostEqual(r["1.4D"]["P"], 14)
        self.assertAlmostEqual(r["1.2D+1.6L"]["P"], 20.0)
        self.assertAlmostEqual(r["1.2D+1.6L"]["M"], 4.0)

    def test_sismo_signos_y_omega(self):
        c = {"D": {"V": 1.0}, "L": {"V": 0.5}, "E": {"V": 3.0}}
        r = _por_nombre(cargas.generar(c, ["V"], omega0=2.5, modo_sismo="ambos"))
        self.assertAlmostEqual(r["1.2D+L+E"]["V"], 1.2 + 3 + 0.5)
        self.assertAlmostEqual(r["1.2D+L−E"]["V"], 1.2 - 3 + 0.5)
        self.assertAlmostEqual(r["0.9D+Ω0E"]["V"], 0.9 + 7.5)
        self.assertAlmostEqual(r["0.9D−Ω0E"]["V"], 0.9 - 7.5)

    def test_maximos_se_enumeran(self):
        c = {"D": {"P": 10}, "L": {"P": 4}, "Lr": {"P": 2}, "S": {"P": 3}, "W": {"P": 1}}
        r = _por_nombre(cargas.generar(c, ["P"]))
        self.assertAlmostEqual(r["1.2D+1.6L+0.5Lr"]["P"], 12 + 6.4 + 1)
        self.assertAlmostEqual(r["1.2D+1.6L+0.5S"]["P"], 12 + 6.4 + 1.5)
        self.assertAlmostEqual(r["1.2D+L+1.6S"]["P"], 12 + 4.8 + 4)
        self.assertAlmostEqual(r["1.2D+1.6S+0.5W"]["P"], 12 + 4.8 + 0.5)
        self.assertAlmostEqual(r["0.9D−W"]["P"], 9 - 1)

    def test_sin_cargas(self):
        self.assertEqual(cargas.generar({}, ["P"]), [])


SAP_REACC = """TABLE:  Joint Reactions
Joint\tOutputCase\tCaseType\tStepType\tF1\tF2\tF3\tM1\tM2\tM3
Text\tText\tText\tText\tTonf\tTonf\tTonf\tTonf-m\tTonf-m\tTonf-m
12\t1.2D+1.6L\tCombination\t\t0.5\t0\t25.0\t0\t3.2\t0
12\tENVOL\tCombination\tMax\t1.2\t0\t30.0\t0\t5.0\t0
12\tENVOL\tCombination\tMin\t-1.1\t0\t10.0\t0\t-4.0\t0
13\t1.2D+1.6L\tCombination\t\t0.7\t0\t26.0\t0\t3.0\t0
"""

SAP_KN = """Joint,OutputCase,F1,F3,M2
Text,Text,KN,KN,KN-m
1,C1,98.0665,196.133,98.0665
"""


class TestSAP(unittest.TestCase):
    def test_parse_y_sugerencia(self):
        t = cargas.parse(SAP_REACC)
        self.assertEqual(t["tabla"], "Joint Reactions")
        self.assertEqual(len(t["filas"]), 4)
        self.assertEqual(t["unidades"][4], "Tonf")
        m = cargas.mapa_sugerido(t["columnas"], ["P", "V", "M"])
        self.assertEqual((m["P"]["col"], m["V"]["col"], m["M"]["col"]), ("F3", "F1", "M2"))

    def test_importar_con_filtro(self):
        m = cargas.mapa_sugerido(cargas.parse(SAP_REACC)["columnas"], ["P", "V", "M"])
        r = cargas.importar(SAP_REACC, m, ["P", "V", "M"], filtro={"col": "Joint", "valor": "12"})
        nombres = [c["nombre"] for c in r["combos"]]
        self.assertEqual(nombres, ["1.2D+1.6L", "ENVOL Max", "ENVOL Min"])
        self.assertAlmostEqual(r["combos"][1]["P"], 30.0)
        self.assertAlmostEqual(r["combos"][2]["M"], -4.0)

    def test_conversion_kn(self):
        m = cargas.mapa_sugerido(cargas.parse(SAP_KN)["columnas"], ["P", "V", "M"])
        r = cargas.importar(SAP_KN, m, ["P", "V", "M"])
        c = r["combos"][0]
        self.assertAlmostEqual(c["V"], 10.0, places=3)           # 98.0665 kN = 10 Tonf
        self.assertAlmostEqual(c["P"], 20.0, places=3)
        self.assertAlmostEqual(c["M"], 10.0, places=3)           # 98.0665 kN·m = 10 Tonf·m

    def test_signo_y_valor_absoluto(self):
        m = cargas.mapa_sugerido(cargas.parse(SAP_REACC)["columnas"], ["P", "V", "M"])
        m["M"]["abs"] = True
        m["V"]["mult"] = -1
        r = cargas.importar(SAP_REACC, m, ["P", "V", "M"], filtro={"col": "Joint", "valor": "12"})
        self.assertAlmostEqual(r["combos"][2]["M"], 4.0)
        self.assertAlmostEqual(r["combos"][2]["V"], 1.1)

    def test_excel_en_coma_decimal(self):
        txt = "Joint;OutputCase;F1;F3;M2\n1;C1;0,5;12,5;1,25\n"
        m = cargas.mapa_sugerido(cargas.parse(txt)["columnas"], ["P", "V", "M"])
        c = cargas.importar(txt, m, ["P", "V", "M"])["combos"][0]
        self.assertAlmostEqual(c["P"], 12.5)


if __name__ == "__main__":
    unittest.main()
