"""CIDECT 9: placa simple a RHS (ej. 5.3.1), empalme de columna RHS (§11.1.1.2) y unión atornillada con diafragma pasante (§8.2, ej. 8.2.1)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import aisc  # noqa: E402
from hss_diafragma_atornillado.engine import calcular as calc_da  # noqa: E402
from empalme_rhs.engine import calcular as calc_er  # noqa: E402
from hss_placasimple.engine import calcular as calc_ps  # noqa: E402

MPA, KN = 10.1972, 101.972


def _c(r, nombre):
    return next(c for c in r["checks"] if c["nombre"].startswith(nombre))


class TestPlacaSimple(unittest.TestCase):
    def setUp(self):
        self._o = (aisc.ACEROS["A500 Gr C"], aisc.ACEROS["A36"])
        aisc.ACEROS["A500 Gr C"] = (350 * MPA, 450 * MPA)         # RHS grado 350W (fy 350 / fu 450 MPa)
        aisc.ACEROS["A36"] = (300 * MPA, 450 * MPA)                # placa grado 300W

    def tearDown(self):
        aisc.ACEROS["A500 Gr C"], aisc.ACEROS["A36"] = self._o

    def _r(self):
        return calc_ps({"vg_perfil": "ARMADO (flejes soldados)", "vg_E_d": 399, "vg_E_bf": 140, "vg_E_tw": 6.4, "vg_E_tf": 8.8, "vg_acero": "A992",
                        "hss_perfil": "ARMADO (flejes soldados)", "hss_W": 203, "hss_D": 203, "hss_t": 7.95, "hss_acero": "A500 Gr C",
                        "sp_acero": "A36", "sp_t": 10, "sp_n": 4, "sp_s": 70, "sp_lev": 65, "sp_leh": 50, "sp_a": 70, "sp_w": 5, "pn_diam": '7/8"',
                        "pn_grado": "A325-X (roscas excl.)", "combos": [{"nombre": "Ej. 5.3.1", "V": 484 * KN / 1000}]})

    def test_ejemplo_5_3_1(self):
        r = self._r()
        esb = _c(r, "Pared NO esbelta")
        self.assertAlmostEqual(esb["dem"], 21.5, delta=0.1)                       # (203 − 4·7.95)/7.95
        self.assertAlmostEqual(esb["cap"], 33.5, delta=0.1)                       # 1.4√(E/fy)
        tp = _c(r, "Espesor de placa")
        self.assertAlmostEqual(tp["cap"] * 10, 11.93, delta=0.01)                 # tp ≤ (450/300)·7.95 = 11.93 mm
        self.assertEqual(tp["estado"], "CUMPLE")
        pared = _c(r, "Corte de las paredes laterales")
        self.assertAlmostEqual(pared["cap"] * 1000 / KN, 1022, delta=2)           # 2·0.9·340·7.95·0.6·0.350 = 1022 kN

    def test_placa_gruesa_incumple_ec_5_2(self):
        r = calc_ps(dict(self._inp_base(), sp_t=14))
        self.assertEqual(_c(r, "Espesor de placa")["estado"], "NO CUMPLE")

    def _inp_base(self):
        return {"vg_perfil": "ARMADO (flejes soldados)", "vg_E_d": 399, "vg_E_bf": 140, "vg_E_tw": 6.4, "vg_E_tf": 8.8, "vg_acero": "A992",
                "hss_perfil": "ARMADO (flejes soldados)", "hss_W": 203, "hss_D": 203, "hss_t": 7.95, "hss_acero": "A500 Gr C",
                "sp_acero": "A36", "sp_t": 10, "sp_n": 4, "sp_s": 70, "sp_lev": 65, "sp_leh": 50, "sp_a": 70, "sp_w": 5, "pn_diam": '7/8"',
                "pn_grado": "A325-X (roscas excl.)", "combos": [{"nombre": "x", "V": 10}]}


class TestEmpalmeRHS(unittest.TestCase):
    """No hay ejemplo RHS en la guía: recálculo independiente de las ecs. 11.3–11.10 (valores en N, mm, MPa)."""

    def test_formulas_ec_11_3_a_11_10(self):
        T, Nb, a, b, db, dh, p, fy = 35000.0, 80000.0, 40.0, 45.0, 22.0, 24.0, 90.0, 250.0
        a1, b1 = a + db / 2, b - db / 2                          # a' = 51, b' = 34
        rho = b1 / a1
        beta = (1 / rho) * (Nb / T - 1)                         # β' = 1.9, ρ=0.667 → > 1 → α' = 1
        delta = 1 - dh / p
        alfa = 1.0 if beta >= 1 else (1 / delta) * beta / (1 - beta)
        t = (4 * T * b1 / (0.9 * p * fy * (1 + delta * alfa))) ** 0.5
        r = aisc.cidect_empalme_tnec(Nb, T, a, b, db, dh, p, fy)
        self.assertAlmostEqual(r["t"], t, places=9)
        self.assertEqual(r["alfa"], 1.0)
        self.assertAlmostEqual(r["a1"], a1)
        # caso con β' < 1: α' = (1/δ)·β'/(1 − β')
        r2 = aisc.cidect_empalme_tnec(40000.0, T, a, b, db, dh, p, fy)
        b2 = (1 / rho) * (40000 / T - 1)
        self.assertLess(b2, 1.0)
        self.assertAlmostEqual(r2["alfa"], min(1.0, (1 / delta) * b2 / (1 - b2)), places=9)

    def test_a_limitado_a_1_25_b(self):
        r = aisc.cidect_empalme_tnec(80000.0, 35000.0, 100.0, 45.0, 22.0, 24.0, 90.0, 250.0)
        self.assertAlmostEqual(r["a1"], 1.25 * 45 + 11)

    def test_modulo(self):
        I = {"hss_perfil": "ARMADO (flejes soldados)", "hss_W": 200, "hss_D": 200, "hss_t": 8, "hss_acero": "A500 Gr C", "pl_acero": "A36", "pl_B": 360,
             "pl_H": 360, "pl_t": 25, "pn_grado": "A325-N (roscas incl.)", "pn_diam": '7/8"', "pn_nx": 2, "pn_ny": 2, "pn_b": 45, "sd_w": 8,
             "sd_elec": "E70XX", "combos": [{"nombre": "T", "N": 30, "Mx": 0, "My": 0, "V": 0}]}
        r = calc_er(I)
        self.assertEqual(_c(r, "Tracción del perno")["estado"], "CUMPLE")
        self.assertAlmostEqual(_c(r, "Tracción del perno")["dem"], 30 / 8, places=6)         # N/n con 8 pernos
        self.assertEqual(_c(r, "Espesor de la placa")["estado"], "CUMPLE")
        I["pl_t"] = 8
        self.assertEqual(_c(calc_er(I), "Espesor de la placa")["estado"], "NO CUMPLE")


class TestDiafragmaAtornillado(unittest.TestCase):
    """Ejemplo 8.2.1 de la guía (viga 500×200×10×16 SN400B, RHS 400×400×16 S275, M20 10.9)."""

    def setUp(self):
        self._o = (aisc.ACEROS["A992"], aisc.ACEROS["A500 Gr C"])
        aisc.ACEROS["A992"] = (235 * MPA, 400 * MPA)
        aisc.ACEROS["A500 Gr C"] = (275 * MPA, 410 * MPA)

    def tearDown(self):
        aisc.ACEROS["A992"], aisc.ACEROS["A500 Gr C"] = self._o

    def test_ejemplo_8_2_1(self):
        r = calc_da({"vg_perfil": "ARMADO (flejes soldados)", "vg_E_d": 500, "vg_E_bf": 200, "vg_E_tw": 10, "vg_E_tf": 16, "vg_acero": "A992",
                     "Zx": 2130000, "ms_bf": 340, "ms_n": 4, "vg_n": 2, "hss_perfil": "ARMADO (flejes soldados)", "hss_W": 400, "hss_D": 400,
                     "hss_t": 16, "hss_acero": "A500 Gr C", "L": 3800, "sc": 70, "sl": 355, "sb": 180, "Le": 70, "pn_d": 20, "pn_d0": 22,
                     "pn_fub": 1000 * MPA, "pn_e1": 50, "pn_p1": 60, "pn_e2": 50, "nf_e": 2, "nf_i": 4, "nw_m": 2, "yw": 240, "nw_v": 2, "mu": 0.4,
                     "combos": [{"nombre": "Ej", "Vg": 63 * KN / 1000, "Ms": 0}]})
        kNm = lambda c: c * 1000 / KN * 1000                                    # Tonf·m → kN·m
        self.assertAlmostEqual(kNm(_c(r, "Sobrerresistencia")["cap"]) / 1000, 672, delta=1)         # Mb,n* (8.9)
        self.assertAlmostEqual(kNm(_c(r, "Ménsula, modo (a)")["dem"]) / 1000, 741, delta=1)         # Mcf (8.11)
        self.assertAlmostEqual(kNm(_c(r, "Ménsula, modo (a)")["cap"]) / 1000, 1031, delta=1)        # 8.12
        self.assertAlmostEqual(kNm(_c(r, "Ménsula, modo (b)")["cap"]) / 1000, 972, delta=1)         # 8.13 + 8.14
        self.assertAlmostEqual(kNm(_c(r, "Flexión del empalme")["cap"]) / 1000, 751, delta=1)       # Mbs,cf
        cs = _c(r, "Cortante del empalme")
        self.assertAlmostEqual(cs["cap"] * 1000 / KN, 264, delta=1)                                 # 2·132
        self.assertAlmostEqual(cs["dem"] * 1000 / KN, 258, delta=1)                                 # 63 + 741/3.8
        self.assertTrue(all(c["estado"] != "NO CUMPLE" for c in r["checks"]))


if __name__ == "__main__":
    unittest.main()
