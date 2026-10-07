"""Módulos CIDECT 9: hss_placalong (ejemplo 10.1.1.1) y hss_dext (Tabla 8.3 ec. 2; sin ejemplo en la guía)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import aisc  # noqa: E402
from hss_dext.engine import calcular as calc_dext  # noqa: E402
from hss_placalong.engine import calcular as calc_pl  # noqa: E402

MPA, KN = 10.1972, 101.972


def _c(r, nombre):
    return next(c for c in r["checks"] if c["nombre"].startswith(nombre))


class TestPlacaLongitudinal(unittest.TestCase):
    def setUp(self):
        self._old = aisc.ACEROS["A500 Gr C"]
        aisc.ACEROS["A500 Gr C"] = (350 * MPA, 450 * MPA)          # grado 350W del ejemplo (fy = 350 MPa)

    def tearDown(self):
        aisc.ACEROS["A500 Gr C"] = self._old

    def _inp(self, **kw):
        d = {"hss_perfil": "ARMADO (flejes soldados)", "hss_W": 178, "hss_D": 178, "hss_t": 6.35, "hss_acero": "A500 Gr C", "hss_Ao": 4250, "clase": 2,
             "pl_acero": "A36", "pl_tp": 10, "pl_hp": 200, "pl_theta": 53.1, "pl_w": 6, "pn_diam": '7/8"', "pn_n": 2,
             "combos": [{"nombre": "Ejemplo 10.1.1.1", "N": 250 * KN / 1000, "Ns": 167 * KN / 1000, "P": 500 * KN / 1000, "M": 0}]}
        d.update(kw)
        return d

    def test_ejemplo_10_1_1_1(self):
        r = calc_pl(self._inp())
        cara = _c(r, "Resistencia mayorada")
        self.assertAlmostEqual(cara["cap"] * 1000 / KN, 133, delta=1.0)                  # Np* = 133 kN
        self.assertEqual(cara["estado"], "NO CUMPLE")                                    # 250 > 133: "no es correcto"
        serv = _c(r, "Servicio")
        self.assertAlmostEqual(serv["cap"] * 1000 / KN, 72, delta=1.0)                   # 72 kN < 167 kN: no cumple
        self.assertGreater(serv["ratio"], 1)
        n = next(m for m in r["combos"][0]["trace"] if m["sym"] == "n")["val"]
        self.assertAlmostEqual(n, -0.336, places=3)

    def test_soldadura_del_ejemplo(self):
        r = calc_pl(self._inp())
        w = _c(r, "Soldadura placa")
        self.assertAlmostEqual(w["cap"] * 1000 / KN, 457, delta=4)                      # 2·(200/sen53.1°)·0.914 = 457 kN (CSA); AISC ≈ igual

    def test_placa_pasante_duplica(self):
        a = _c(calc_pl(self._inp()), "Resistencia mayorada")["cap"]
        b = _c(calc_pl(self._inp(pl_tipo="Pasante (ranurada, ×2)")), "Resistencia mayorada")["cap"]
        self.assertAlmostEqual(b / a, 2.0, places=6)


class TestDiafragmaExterno(unittest.TestCase):
    def _inp(self, **kw):
        d = {"combos": [{"nombre": "c", "M": 6, "V": 4}]}
        d.update(kw)
        return d

    def test_valores_por_defecto_y_formula(self):
        r = calc_dext(self._inp())
        v = {m["sym"]: m["val"] for m in r["memoria_global"]}
        # recálculo independiente de la ec. (2): bc = 30 cm, tc = 1.2, td = 2.0, hd = 8, fd,u = 4570 kgf/cm² (A572 Gr50)
        bc, tc, td, hd, fu = 30.0, 1.2, 2.0, 8.0, 4570.0
        P = 3.17 * (tc / bc) ** (2 / 3) * (td / bc) ** (2 / 3) * ((tc + hd) / bc) ** (1 / 3) * bc ** 2 * fu
        self.assertAlmostEqual(v["Pb,f*"], P / 1000, places=3)                           # Tonf
        self.assertAlmostEqual(v["Mj,cf*"], v["Pb,f*"] * (r["derivados"]["vg_d_mm"] - r["derivados"]["vg_tf_mm"]) / 1000, places=3)

    def test_sobrerresistencia_con_la_ec_8_23(self):
        r = calc_dext(self._inp())
        v = {m["sym"]: m["val"] for m in r["memoria_global"]}
        L, Ln, alfa = 300.0, 30.0, 1.2
        self.assertAlmostEqual(v["Mcf,req"], L / (L - Ln) * alfa * v["Mpl"], places=6)

    def test_campo_de_validez(self):
        ok = calc_dext(self._inp())
        self.assertLessEqual(_c(ok, "Validez: td/tc ≤")["ratio"], 1.0)
        mal = calc_dext(self._inp(dx_td=40))                                              # td/tc = 3.3 > 2.0
        self.assertGreater(_c(mal, "Validez: td/tc ≤")["ratio"], 1.0)
        self.assertGreater(_c(mal, "Ensayos: espesor del diafragma")["ratio"], 1.0)
        thetas = calc_dext(self._inp(dx_theta=40))
        self.assertGreater(_c(thetas, "Validez: θ")["ratio"], 1.0)
        self.assertLessEqual(_c(calc_dext(self._inp(dx_theta=40, dx_placas="Sí")), "Validez: θ")["ratio"], 1.0)


if __name__ == "__main__":
    unittest.main()
