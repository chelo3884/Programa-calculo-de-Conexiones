import copy
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import autodiseno  # noqa: E402
from end_plate import engine as ep  # noqa: E402
from placa_base.engine import calcular as pb_calc  # noqa: E402
from wuf import engine as wuf  # noqa: E402


def _def(eng):
    d = {c["name"]: c["default"] for s in eng.SPEC["secciones"] for c in s["campos"]}
    return d


class TestAuto(unittest.TestCase):
    def test_wuf_reduce_hasta_el_minimo_que_cumple(self):
        inp = _def(wuf)
        inp.update(pl_t=19, pl_n=8, pl_w=12, combos=[{"nombre": "c", "M": 14, "V": 8}])
        r = autodiseno.buscar("wuf", wuf.calcular, inp, nombres=["pl_t", "pl_n", "pl_w", "pn_diam"])
        self.assertTrue(r["ok"])
        # la propuesta cumple y cuesta menos que la inicial sobredimensionada
        d = copy.deepcopy(inp)
        d.update(r["propuesta"])
        self.assertLessEqual(wuf.calcular(d)["resumen"]["ratio_max"], 0.9 + 1e-9)
        self.assertLess(autodiseno.CONFIG["wuf"][0](d), autodiseno.CONFIG["wuf"][0](inp))
        self.assertLessEqual(r["evaluaciones"], 4000)

    def test_es_optimo_frente_a_fuerza_bruta(self):
        inp = _def(wuf)
        inp.update(combos=[{"nombre": "c", "M": 20, "V": 12}])
        nombres = ["pl_t", "pl_w", "pl_n"]
        r = autodiseno.buscar("wuf", wuf.calcular, inp, nombres=nombres)
        vs = autodiseno.variables("wuf", inp)
        vs = [v for v in vs if v["name"] in nombres]
        costo = autodiseno.CONFIG["wuf"][0]
        mejor = None
        import itertools
        for comb in itertools.product(*[v["cands"] for v in vs]):
            d = copy.deepcopy(inp)
            d.update({v["name"]: x for v, x in zip(vs, comb)})
            if wuf.calcular(d)["resumen"]["ratio_max"] <= 0.9:
                c = costo(d)
                mejor = c if mejor is None else min(mejor, c)
        self.assertTrue(r["ok"])
        self.assertAlmostEqual(r["costo"], round(mejor, 2), places=2)

    def test_end_plate_usa_opciones_del_campo(self):
        inp = _def(ep)
        inp["combos"] = [{"nombre": "c", "M": 30, "V": 12}]
        opts = {c["name"]: c.get("options") for s in ep.SPEC["secciones"] for c in s["campos"]}
        r = autodiseno.buscar("end_plate", ep.calcular, inp, nombres=["pl_tp", "pn_diam"], opciones_campo=opts)
        self.assertIn("propuesta", r)

    def test_placa_base_anidada(self):
        import json
        inp = {"tipo_col": "I", "perfil": "ARMADO (flejes soldados)", "armado": {"d": 350, "bf": 200, "tw": 8, "tf": 12},
               "placa": {"acero": "A36", "Fy": 2530, "N": 600, "B": 400, "tp": 50, "grout": 25},
               "pernos": {"material": "F1554 Gr55", "diam": '1-1/2"', "nfila": 2, "eN": 50, "eB": 50, "hef": 900,
                          "arandela_lado": 70, "arandela_t": 12, "arandela_sold": "Sí", "nv": 4},
               "pedestal": {"fc": 210, "Np": 90, "Bp": 80, "fisurado": "Sí", "ref_borde": "Sí", "hp_usar": "Sí", "hp_n": 4,
                            "hp_db": 16, "hp_fy": 4200},
               "sold": {"electrodo": "E70XX", "wf": 12, "ww": 12}, "sismo": {"sismo": "No", "omega0": 1},
               "corte": {"friccion": "No", "mu": 0.55}, "combos": [{"nombre": "1.2D+1.6L", "P": 12, "V": 1.2, "M": 2.5}]}
        r = autodiseno.buscar("placa_base", pb_calc, inp, nombres=["placa.tp", "sold.wf", "sold.ww", "pernos.diam"])
        self.assertTrue(r["ok"], r)
        self.assertLess(r["propuesta"]["placa.tp"], 50)


if __name__ == "__main__":
    unittest.main()
