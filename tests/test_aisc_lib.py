"""aisc.py contra los AISC Design Examples v15 (resultados en kip, in; φ = LRFD)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import aisc  # noqa: E402
from aisc import IN, KIP, KSI  # noqa: E402


def kip(x):
    return x / KIP


class TestAISC(unittest.TestCase):
    def test_perno_tabla_7_1_y_J3_8(self):
        p = aisc.perno('7/8"', "A325-N (roscas incl.)")
        self.assertAlmostEqual(kip(aisc.rn_corte_perno(p["Fnv"], p["Ab"])), 24.3, delta=0.1)          # II.A-20, II.B-1
        p1 = aisc.perno('1"', "A325-N (roscas incl.)")
        self.assertAlmostEqual(kip(aisc.rn_corte_perno(p1["Fnv"], p1["Ab"])), 31.8, delta=0.1)        # II.C-3
        self.assertAlmostEqual(kip(aisc.rn_deslizamiento(0.30, p1["Tb"])), 17.3, delta=0.05)          # II.C-3 (Tb = 51 kip)
        self.assertAlmostEqual(p1["dh"] / IN, 1.125, places=3)                                         # dh = 1-1/8 in

    def test_aplastamiento_y_desgarre_II_A_20(self):
        p = aisc.perno('7/8"', "A325-N (roscas incl.)")
        Fu = 58 * KSI
        lc = 1.5 * IN - p["dh"] / 2
        self.assertAlmostEqual(kip(aisc.rn_aplastamiento(p["db"], 3 / 8 * IN, Fu, lc)), 20.2, delta=0.1)
        self.assertAlmostEqual(kip(aisc.rn_aplastamiento(p["db"], 3 / 8 * IN, Fu, 10)), 34.3, delta=0.1)   # 2.4·d·t·Fu

    def test_placa_II_A_20(self):
        Fy, Fu, t, l = 36 * KSI, 58 * KSI, 3 / 8 * IN, 12 * IN
        p = aisc.perno('7/8"', "A325-N (roscas incl.)")
        self.assertAlmostEqual(kip(aisc.rn_fluencia_corte(Fy, l * t)), 97.2, delta=0.1)
        self.assertAlmostEqual(kip(aisc.rn_ruptura_corte(Fu, (l - 4 * (p["dh"] + 1 / 16 * IN)) * t)), 78.0, delta=0.4)
        # bloque de cortante: n = 4, leh = lev = 1½ in, s = 3 in
        lev, leh, s = 1.5 * IN, 1.5 * IN, 3 * IN
        dh = p["dh"] + 1 / 16 * IN
        Agv = (lev + 3 * s) * t
        Anv = Agv - (3.5) * dh * t
        Ant = (leh - 0.5 * dh) * t
        self.assertAlmostEqual(kip(aisc.rn_bloque_corte(Agv, Anv, Ant, Fy, Fu)), 80.1, delta=0.5)

    def test_bloque_de_cortante_placa_de_ala_II_B_1_caso_3(self):
        Fy, Fu, t = 36 * KSI, 58 * KSI, 0.75 * IN
        dh = (15 / 16 + 1 / 16) * IN
        Agv = (3 * 3 + 1.5) * IN * t
        Anv = Agv - 3.5 * dh * t
        Ant = (4 * IN + 1.5 * IN - 1.5 * dh) * t                                              # gramil + leh − 1.5·dh,net
        self.assertAlmostEqual(kip(aisc.rn_bloque_corte(Agv, Anv, Ant, Fy, Fu)), 258, delta=1.5)

    def test_J10_columna_W14x99_II_B_1(self):
        Fy, tf, tw, k, d = 50 * KSI, 0.780 * IN, 0.485 * IN, 1.38 * IN, 14.2 * IN
        N = 0.75 * IN
        self.assertAlmostEqual(kip(aisc.rn_flexion_local_ala(Fy, tf)), 171, delta=0.6)
        self.assertAlmostEqual(kip(aisc.rn_fluencia_local_alma(Fy, tw, k, N)), 186, delta=0.8)
        self.assertAlmostEqual(kip(aisc.rn_aplastamiento_alma(Fy, tw, tf, d, N)), 233, delta=1.5)

    def test_filete_II_B_1_y_gusset_II_C_1(self):
        # Manual Ec. 8-2: 1.392 kip/in por dieciseisavo (E70, θ = 0): placa 9 in con filete ¼ por ambos lados = 100 kip
        w = 0.25 * IN
        self.assertAlmostEqual(kip(2 * aisc.rn_filete(70 * KSI, w, 9 * IN)), 100, delta=0.6)
        # θ = 90°: factor 1.50 (II.B-1: 2 filetes de 7 in a ala de columna)
        self.assertAlmostEqual(kip(aisc.rn_filete(70 * KSI, w, 1 * IN, 90)) / kip(aisc.rn_filete(70 * KSI, w, 1 * IN, 0)), 1.5, places=3)
        # II.C-1: tmín = 6.19·D/Fu = 0.427 in (D = 4, Fu = 58 ksi, filete a una cara del gusset)
        self.assertAlmostEqual(aisc.t_min_soporte(70 * KSI, 58 * KSI, 0.25 * IN, lados=1) / IN, 0.427, delta=0.003)
        # K.6: 3.09·D/Fu = 0.199 in (HSS, Fu = 62 ksi, placa por ambos lados)
        self.assertAlmostEqual(aisc.t_min_soporte(70 * KSI, 62 * KSI, 0.25 * IN, lados=2) / IN, 0.199, delta=0.002)

    def test_whitmore_y_gusset_II_C_3(self):
        lw = aisc.ancho_whitmore(5.5 * IN, 4 * 3 * IN)          # gramil 5½ in, 4 pasos de 3 in → lw = 19.4 in
        self.assertAlmostEqual(lw / IN, 19.4, delta=0.05)
        Fy, t = 36 * KSI, 3 / 8 * IN
        self.assertAlmostEqual(kip(aisc.rn_fluencia_traccion(Fy, 2 * lw * t)), 473, delta=3.5)    # el ejemplo redondea Ag = 14.6 in²

    def test_gusset_bloque_de_cortante_II_C_3(self):
        Fy, Fu, t = 36 * KSI, 58 * KSI, 3 / 8 * IN
        dh = 1.125 * IN
        Agv = 2 * 2 * (2 * IN + 4 * 3 * IN) * t
        Anv = Agv - 2 * 2 * (4.5) * (dh + 1 / 16 * IN) * t
        Ant = 2 * (5.5 * IN - (dh + 1 / 16 * IN)) * t
        self.assertAlmostEqual(kip(aisc.rn_bloque_corte(Agv, Anv, Ant, Fy, Fu)), 480, delta=2)

    def test_zona_de_panel_y_pandeo_formulas(self):
        # J10-9: 0.9·0.6·Fy·dc·tw (Pr ≤ 0.4Py)
        Fy, d, tw = 50 * KSI, 14.2 * IN, 0.485 * IN
        self.assertAlmostEqual(kip(aisc.rn_zona_panel(Fy, d, tw)), 0.9 * 0.6 * 50 * 14.2 * 0.485, delta=0.5)
        self.assertLess(aisc.rn_zona_panel(Fy, d, tw, Pr=0.8, Py=1.0), aisc.rn_zona_panel(Fy, d, tw))


if __name__ == "__main__":
    unittest.main()


class TestHSSDG24(unittest.TestCase):
    """AISC Design Guide 24, Ej. 4.3: W16x57 soldada a HSS10x10x1/2 (t = 0.465 in, A500 Gr B, Fy = 46 ksi)."""

    def test_flujo_placa_K1_2(self):
        B, t, bf, tf = 10 * IN, 0.465 * IN, 7.12 * IN, 0.715 * IN
        Rn = aisc.hss_flujo_placa(46 * KSI, t, B, bf, 50 * KSI, tf, phi=1.0)
        self.assertAlmostEqual(Rn / KIP, 70.8, delta=0.15)
        self.assertAlmostEqual(aisc.hss_flujo_placa(46 * KSI, t, B, bf, 50 * KSI, tf) / KIP, 67.3, delta=0.15)

    def test_punzonamiento_no_aplica_pero_formula(self):
        # fórmula K1-3 con el mismo ejemplo (referencia numérica propia, no impresa en la guía)
        B, t, bf, tf = 10 * IN, 0.465 * IN, 9 * IN, 0.715 * IN
        Bep = min(10 * bf / (B / t), bf)
        self.assertAlmostEqual(aisc.hss_punzonamiento(46 * KSI, t, B, bf, tf), 0.95 * 0.6 * 46 * KSI * t * (2 * tf + 2 * Bep), places=3)

    def test_compresion_placa_J4_4(self):
        # DG24 Ej. 4.2: PL 5/8 x 14, KL/r = 16.7 < 25 → φFyAg = 0.9·36·8.75 = 283.5 kip
        Ag = 14 * 0.625 * IN ** 2
        self.assertAlmostEqual(aisc.rn_compresion_placa(36 * KSI, Ag, 16.7) / KIP, 283.5, delta=0.5)
