"""Fórmulas de la guía CIDECT 9 (español) contra su ejemplo 10.1.1.1 y recálculo manual de la ec. (2) de la Tabla 8.3."""
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import aisc  # noqa: E402

MPA = 10.1972     # kgf/cm² por MPa
KN = 101.972      # kgf por kN


class TestCIDECT(unittest.TestCase):
    def test_placa_longitudinal_ejemplo_10_1_1_1(self):
        # RHS 178x178x6.4 (t = 6.35 mm), fy = 350 MPa, placa 200 x 10 mm, w = 6 mm, θ = 53.1°, N' = 500 kN de compresión
        tc, bc, fcy = 0.635, 17.8, 350 * MPA
        n = -500 * KN / 42.5 / fcy                                           # A = 4250 mm²
        self.assertAlmostEqual(n, -0.336, places=3)
        Np = aisc.cidect_placa_long_Np(fcy, tc, bc, bp=1.0, hp=20.0, theta_deg=53.1, w=0.6, n=n)
        self.assertAlmostEqual(Np / KN, 133, delta=1.0)                      # 133 kN
        bet = (1.0 + 1.2) / (bc - tc)
        self.assertAlmostEqual(bet, 0.128, places=3)
        self.assertAlmostEqual(aisc.cidect_placa_long_servicio(Np, bet, 2) / KN, 72, delta=1.0)   # 72 kN (clase 2)

    def test_formula_diafragma_externo_tabla_8_3(self):
        bc, tc, td, hd, fdu = 25.0, 1.2, 1.6, 6.0, 400 * MPA
        P = aisc.cidect_dext_Pbf(bc, tc, td, hd, fdu)
        manual = 3.17 * (0.048) ** (2 / 3) * (0.064) ** (2 / 3) * (0.288) ** (1 / 3) * bc ** 2 * fdu
        self.assertAlmostEqual(P / manual, 1.0, places=9)
        self.assertAlmostEqual(P / KN, 1105, delta=15)                       # orden de magnitud calculado a mano: ≈ 1105 kN
        v, lim = aisc.cidect_dext_esbeltez(bc, hd, td, 235 * MPA)
        self.assertAlmostEqual(lim, 240 / math.sqrt(235), places=6)          # 15.66
        self.assertAlmostEqual(v, (12.5 + 6) / 1.6, places=9)


if __name__ == "__main__":
    unittest.main()
