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


INCH, KIP, KSI = 25.4, 0.45359237, 70.307


def _base(**kw):
    """Entrada base en unidades canónicas (mm, Tonf, kgf/cm²); kw reemplaza secciones completas."""
    inp = {
        "perfil": "ARMADO (flejes soldados)",
        "armado": {"d": 12.7 * INCH, "bf": 12.2 * INCH, "tw": 0.55 * INCH, "tf": 0.9 * INCH},
        "placa": {"acero": "Personalizado", "Fy": 36 * KSI, "N": 22 * INCH, "B": 22 * INCH,
                  "tp": 2 * INCH, "grout": 25},
        "pernos": {"material": "F1554 Gr55", "diam": '1"', "nfila": 2, "eN": 50, "eB": 50,
                   "hef": 500, "arandela_lado": 0, "arandela_t": 0, "arandela_sold": "No", "nv": 4},
        "pedestal": {"fc": 3 * KSI, "Np": 24 * 2.54, "Bp": 24 * 2.54, "fisurado": "Sí",
                     "ref_borde": "No", "hp_usar": "No", "hp_n": 0, "hp_db": 16, "hp_fy": 4200},
        "sold": {"electrodo": "E70XX", "wf": 8, "ww": 6},
        "sismo": {"sismo": "No", "omega0": 1},
        "combos": [],
    }
    inp.update(kw)
    return inp


class TestHSS(unittest.TestCase):
    """AISC Design Examples v15, Ej. K.9: HSS6x6 sobre zapata, Pu = 240 kip, PL 13x13 in A36, f'c = 3 ksi."""

    def test_k9(self):
        inp = _base(
            tipo_col="HSS", perfil_hss="Personalizado", hss={"H": 6 * INCH, "Bc": 6 * INCH, "t": 0.233 * INCH},
            placa={"acero": "Personalizado", "Fy": 36 * KSI, "N": 13 * INCH, "B": 13 * INCH, "tp": 1.25 * INCH, "grout": 25},
            pedestal={"fc": 3 * KSI, "Np": 90 * 2.54, "Bp": 90 * 2.54, "fisurado": "Sí", "ref_borde": "No",
                      "hp_usar": "No", "hp_n": 0, "hp_db": 16, "hp_fy": 4200},
            combos=[{"nombre": "Pu", "P": 240 * KIP, "V": 0, "M": 0}])
        r = calcular(inp)
        c = r["combos"][0]
        self.assertAlmostEqual(r["geom"]["m"] / 2.54, 3.65, places=2)
        self.assertAlmostEqual(r["geom"]["n"] / 2.54, 3.65, places=2)
        self.assertAlmostEqual(c["ratios"]["ap"], 240 / 560, delta=0.002)     # φc·Pp = 560 kips
        self.assertAlmostEqual(c["fp"] / KSI, 1.42, places=2)
        self.assertAlmostEqual(c["tp_req_mm"] / INCH, 1.08, places=2)         # tmin = 1.08 in

    def test_hss_catalogo_y_rectangular(self):
        inp = _base(tipo_col="HSS", perfil_hss="HSS8X8X3/8",
                    combos=[{"nombre": "x", "P": 20, "V": 1, "M": 3}])
        r = calcular(inp)
        g = r["geom"]
        self.assertEqual(g["tipo"], "HSS")
        self.assertAlmostEqual(g["n"], (inp["placa"]["B"] / 10 - 0.95 * 20.32) / 2, places=3)
        self.assertEqual(g["np"], 0.0)               # n' no se usa en HSS
        self.assertIsNotNone(r["resumen"]["ratio_max"])


class TestGuiaDG1(unittest.TestCase):
    """AISC Design Guide 1, 2.ª ed. (2006), ejemplos 4.1, 4.6 y 4.7 (W12x96, φc = 0.65)."""

    def test_ej_4_1_axial_A2_igual_A1(self):
        # N = 22 in, B = 20 in, pedestal = placa (A2 = A1), Pu = 700 kips, f'c = 3 ksi → φPp = 729 kips; tmin = 1.60 in
        inp = _base(placa={"acero": "Personalizado", "Fy": 36 * KSI, "N": 22 * INCH, "B": 20 * INCH, "tp": 1.75 * INCH, "grout": 25},
                    pedestal={"fc": 3 * KSI, "Np": 22 * 2.54, "Bp": 20 * 2.54, "fisurado": "Sí", "ref_borde": "No",
                              "hp_usar": "No", "hp_n": 0, "hp_db": 16, "hp_fy": 4200},
                    combos=[{"nombre": "Pu", "P": 700 * KIP, "V": 0, "M": 0}])
        c = calcular(inp)["combos"][0]
        self.assertAlmostEqual(c["ratios"]["ap"], 700 / 729, delta=0.002)
        self.assertAlmostEqual(c["l"] / 2.54, 5.12, places=2)                  # l = n = 5.12 in (λn' = 3.11 no gobierna)
        self.assertAlmostEqual(c["tp_req_mm"] / INCH, 1.60, delta=0.01)

    def test_ej_4_6_momento_pequeno(self):
        # N = B = 19 in, f'c = 4 ksi, Pu = 376 kips, Mu = 940 kip·in, e = 2.5 in ≤ ecrit = 5.02 in, Y = 14 in, fp = 1.41 ksi
        inp = _base(placa={"acero": "Personalizado", "Fy": 36 * KSI, "N": 19 * INCH, "B": 19 * INCH, "tp": 1.5 * INCH, "grout": 25},
                    pernos={"material": "F1554 Gr36", "diam": '3/4"', "nfila": 2, "eN": 1.5 * INCH, "eB": 1.5 * INCH,
                            "hef": 300, "arandela_lado": 0, "arandela_t": 0, "arandela_sold": "No", "nv": 4},
                    pedestal={"fc": 4 * KSI, "Np": 19 * 2.54, "Bp": 19 * 2.54, "fisurado": "Sí", "ref_borde": "No",
                              "hp_usar": "No", "hp_n": 0, "hp_db": 16, "hp_fy": 4200},
                    combos=[{"nombre": "Pu", "P": 376 * KIP, "V": 0, "M": 940 * KIP * 0.0254}])
        c = calcular(inp)["combos"][0]
        self.assertEqual(c["caso"], 1)
        self.assertAlmostEqual(c["ecrit"] / 2.54, 5.02, delta=0.01)
        self.assertAlmostEqual(c["Y"] / 2.54, 14.0, delta=0.01)
        self.assertAlmostEqual(c["fp"] / KSI, 1.41, delta=0.01)
        self.assertAlmostEqual(c["tp_req_mm"] / INCH, 1.37, delta=0.02)        # la guía rige por n: 1.36 in

    def test_ej_4_7_momento_grande(self):
        # N = B = 20 in, Pu = 376 kips, Mu = 3600 kip·in, qmax = 44.2 kip/in → Y = 12.0 in, Tu = 156 kips, tp = 1.90 in.
        # NOTA: la guía imprime f = 8.5 in, pero sus resultados (Y = 19.5 − 7.47, Tu = 156 kips) corresponden a
        # f = 9.5 in, es decir eN = 0.5 in; se usa ese valor para reproducir las cifras publicadas.
        inp = _base(placa={"acero": "Personalizado", "Fy": 36 * KSI, "N": 20 * INCH, "B": 20 * INCH, "tp": 2 * INCH, "grout": 25},
                    pernos={"material": "F1554 Gr36", "diam": '1-1/2"', "nfila": 3, "eN": 0.5 * INCH, "eB": 1.5 * INCH,
                            "hef": 450, "arandela_lado": 0, "arandela_t": 0, "arandela_sold": "No", "nv": 6},
                    pedestal={"fc": 4 * KSI, "Np": 20 * 2.54, "Bp": 20 * 2.54, "fisurado": "Sí", "ref_borde": "No",
                              "hp_usar": "No", "hp_n": 0, "hp_db": 16, "hp_fy": 4200},
                    combos=[{"nombre": "Pu", "P": 376 * KIP, "V": 0, "M": 3600 * KIP * 0.0254}])
        c = calcular(inp)["combos"][0]
        self.assertEqual(c["caso"], 2)
        self.assertAlmostEqual(c["ecrit"] / 2.54, 5.75, delta=0.01)
        self.assertAlmostEqual(c["Y"] / 2.54, 12.0, delta=0.05)
        self.assertAlmostEqual(c["Tu"] / KIP, 156, delta=2)
        self.assertAlmostEqual(c["fp"] / KSI, 2.21, delta=0.01)
        self.assertAlmostEqual(c["tp_req_mm"] / INCH, 1.90, delta=0.01)        # gobierna n = 5.12 in en el lado de apoyo


class TestFriccion(unittest.TestCase):
    def test_friccion_reduce_corte_en_pernos(self):
        base = _base(combos=[{"nombre": "x", "P": 100, "V": 20, "M": 0}])
        r0 = calcular(base)["combos"][0]["ratios"]["vsa"]
        con = dict(base, corte={"friccion": "Sí", "mu": 0.55})
        r1 = calcular(con)["combos"][0]["ratios"]["vsa"]
        self.assertGreater(r0, 0)
        self.assertEqual(r1, 0.0)                    # 0.75·0.55·100 = 41 Tonf > 20 Tonf (y ≤ 0.2·f'c·N·B)

    def test_friccion_sin_compresion_no_aporta(self):
        base = _base(combos=[{"nombre": "x", "P": -5, "V": 4, "M": 0}], corte={"friccion": "Sí", "mu": 0.55})
        sin = dict(base, corte={"friccion": "No"})
        self.assertAlmostEqual(calcular(base)["combos"][0]["ratios"]["vsa"],
                               calcular(sin)["combos"][0]["ratios"]["vsa"])


if __name__ == "__main__":
    unittest.main()


class TestLlaveDeCorteDG1(unittest.TestCase):
    """AISC DG1 2.ª ed., Ej. 4.9: llave de corte 9 in de ancho, d = 1.5 in, Fy = 36 ksi, grout 2 in,
    pedestal de 20 in, f'c = 4 ksi, Vu = 36.8 kips (el ejemplo supone la llave de 1 in en el cálculo de Av)."""
    inch, kip, ksi = 25.4, 0.45359237, 70.307

    def _inp(self, t_in):
        inch, kip, ksi = self.inch, self.kip, self.ksi
        return {
            "perfil": "ARMADO (flejes soldados)",
            "armado": {"d": 10.1 * inch, "bf": 8.02 * inch, "tw": 0.35 * inch, "tf": 0.62 * inch},
            "placa": {"acero": "Personalizado", "Fy": 36 * ksi, "N": 14 * inch, "B": 14 * inch, "tp": 1.25 * inch,
                      "grout": 2 * inch},
            "pernos": {"material": "F1554 Gr55", "diam": '3/4"', "nfila": 2, "eN": 50, "eB": 50,
                       "hef": 300, "arandela_lado": 0, "arandela_t": 0, "arandela_sold": "No", "nv": 4},
            "pedestal": {"fc": 4 * ksi, "Np": 20 * 2.54, "Bp": 20 * 2.54, "fisurado": "Sí",
                         "ref_borde": "No", "hp_usar": "No", "hp_n": 0, "hp_db": 16, "hp_fy": 4200},
            "sold": {"electrodo": "E70XX", "wf": 8, "ww": 6},
            "sismo": {"sismo": "No", "omega0": 1},
            "llave": {"usar": "Sí", "b": 9 * inch, "d": 1.5 * inch, "t": t_in * inch, "fy": 36 * ksi, "w": 5 / 16 * inch},
            "combos": [{"nombre": "1.6L", "P": 0, "V": 36.8 * kip, "M": 0}],
        }

    def _cap(self, res, nom):
        c = next(c for c in res["checks"] if c["nombre"].startswith(nom))
        return c["cap"] / self.kip, c["dem"], c["ratio"]

    def test_requerido_y_espesor(self):
        res = calcular(self._inp(1.25))
        cap, dem, _ = self._cap(res, "Aplastamiento del concreto (0.80")
        self.assertAlmostEqual(dem / self.kip, 36.8, places=3)
        self.assertAlmostEqual(36.8 * self.kip * 1000 / (0.8 * 4 * self.ksi), 11.5 * 6.4516, delta=0.5)   # A req'd = 11.5 in²
        # Ml = 36.8·(2 + 1.5/2) = 101.2 kip-in; espesor requerido = 1.18 in → ratio de flexión con t = 1.25 in
        _, _, r = self._cap(res, "Flexión de la llave")
        self.assertAlmostEqual(r, (1.18 / 1.25) ** 2, delta=0.01)

    def test_corte_del_concreto(self):
        res = calcular(self._inp(1.0))
        cap, _, _ = self._cap(res, "Corte del concreto frente a la llave")
        self.assertAlmostEqual(cap, 39.2, delta=0.1)

    def test_soldadura_falla_5_16_y_pasa_3_8(self):
        r1 = calcular(self._inp(1.25))
        self.assertGreater(self._cap(r1, "Soldadura llave")[2], 1.0)
        inp = self._inp(1.25)
        inp["llave"]["w"] = 3 / 8 * self.inch
        self.assertLess(self._cap(calcular(inp), "Soldadura llave")[2], 1.0)

    def test_pernos_no_toman_corte(self):
        res = calcular(self._inp(1.25))
        self.assertEqual(res["combos"][0]["ratios"]["vsa"], 0.0)
