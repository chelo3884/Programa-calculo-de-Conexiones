"""Conexiones de momento a HSS (hss_directa, hss_pasante) contra AISC Design Guide 24, Ej. 4.3 y 4.2.

La guía usa AISC 360-05 (agujero estándar de 1 in = 1-1/16 in; Fnv de A325-N = 48 ksi); el programa usa 360-16 (1-1/8 in; 54 ksi),
por eso las resistencias que dependen del agujero o del perno difieren ligeramente y se comparan con tolerancia o con el valor recalculado."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from hss_directa.engine import calcular as calc_dir  # noqa: E402
from hss_pasante.engine import calcular as calc_pas  # noqa: E402

IN, KIP, KFT = 25.4, 0.45359237, 0.138255        # mm/in, Tonf/kip, Tonf·m/kip-ft


def _viga():
    return {"vg_perfil": "ARMADO (flejes soldados)", "vg_E_d": 16.4 * IN, "vg_E_bf": 7.12 * IN, "vg_E_tw": 0.43 * IN,
            "vg_E_tf": 0.715 * IN, "vg_acero": "A992"}


def _c(res, nombre):
    return next(c for c in res["checks"] if c["nombre"].startswith(nombre))


class TestDirecta(unittest.TestCase):
    def _inp(self, **kw):
        d = dict(_viga(), hss_perfil="ARMADO (flejes soldados)", hss_W=10 * IN, hss_D=10 * IN, hss_t=0.465 * IN, hss_acero="A500 Gr B",
                 combos=[{"nombre": "Mn", "M": 88.1 * KFT, "V": 5, "P": (1.2 * 100 + 1.6 * 300) * KIP, "Mc": 0}])
        d.update(kw)
        return d

    def test_ej_4_3(self):
        r = calc_dir(self._inp())
        k12 = _c(r, "K1-2")
        self.assertAlmostEqual(k12["cap"] / KIP, 67.3, delta=0.2)                          # φRn = 67.3 kip
        self.assertAlmostEqual(k12["cap"] / KIP * (16.4 - 0.715) / 12, 88.1, delta=0.3)       # Mn = 88.1 kip-ft
        self.assertEqual(_c(r, "K1-3")["ratio"], None)                                     # Bp = 7.12 < 0.85B: no se revisa
        self.assertEqual(_c(r, "K1-4")["ratio"], None)                                     # bf/B = 0.712 ≠ 1
        lim = {c["nombre"]: c["ratio"] for c in r["checks"] if c["nombre"].startswith("Límite")}
        self.assertTrue(all(v <= 1 for v in lim.values()), lim)                            # todos los límites cumplen
        self.assertAlmostEqual(_c(r, "Límite: 0.25")["ratio"], 0.712, places=3)

    def test_memoria_Mn(self):
        r = calc_dir(self._inp())
        v = next(m for m in r["memoria_global"] if m["sym"] == "φMn,K")["val"]
        self.assertAlmostEqual(v / KFT, 88.1, delta=0.3)                                    # 88.1 kip-ft

    def test_ala_igual_al_hss_activa_paredes_laterales(self):
        r = calc_dir(self._inp(vg_E_bf=10 * IN - 3 * 0.465 * IN))                            # bf = B − 3t (< B): sigue sin paredes laterales
        self.assertIsNone(_c(r, "K1-4")["ratio"])
        r2 = calc_dir(self._inp(vg_E_bf=10 * IN))
        self.assertIsNotNone(_c(r2, "K1-4")["ratio"])
        self.assertIsNotNone(_c(r2, "K1-5")["ratio"])
        self.assertIsNone(_c(r2, "K1-6")["ratio"])
        r3 = calc_dir(self._inp(vg_E_bf=10 * IN, dos_lados="Sí"))
        self.assertIsNotNone(_c(r3, "K1-6")["ratio"])
        self.assertIsNone(_c(r3, "K1-5")["ratio"])


class TestPasante(unittest.TestCase):
    def _inp(self, **kw):
        d = dict(_viga(), hss_perfil="ARMADO (flejes soldados)", hss_W=12 * IN, hss_D=20 * IN, hss_t=0.465 * IN, hss_acero="A500 Gr B",
                 pp_bp=14 * IN, pp_t=0.625 * IN, pp_nb=5, pp_s=3 * IN, pp_g=3.5 * IN, pp_a=3 * IN, pp_lep=1.75 * IN, pp_lef=2 * IN,
                 pn_diam='1"', pp_w=0.5 * IN,
                 combos=[{"nombre": "Ej 4.2", "Mi": 72 * KFT, "Vi": 9.6 * KIP, "Md": 360 * KFT, "Vd": 48 * KIP, "P": 288 * KIP}])
        d.update(kw)
        return d

    def test_ej_4_2(self):
        r = calc_pas(self._inp())
        ty = _c(r, "Fluencia en tracción")
        self.assertAlmostEqual(ty["dem"] / KIP, 254, delta=1.0)                              # Ru = 254 kip
        self.assertAlmostEqual(ty["cap"] / KIP, 283.5, delta=0.6)                            # 0.9·36·8.75
        self.assertAlmostEqual(_c(r, "Compresión")["cap"] / KIP, 283.5, delta=0.6)           # KL/r = 16.7 < 25
        self.assertAlmostEqual(_c(r, "Ruptura en tracción")["cap"] / KIP, 320, delta=5)      # guía: 320 (agujero 1-1/16); aquí 1-1/8
        self.assertAlmostEqual(_c(r, "Corte de los pernos")["cap"] / KIP, 10 * 31.8, delta=1.5)   # Fnv = 54 ksi: 31.8 kip/perno
        self.assertAlmostEqual(_c(r, "Aplastamiento en la placa")["cap"] / KIP, 584, delta=20)
        self.assertAlmostEqual(_c(r, "Aplastamiento en el ala")["cap"] / KIP, 769, delta=30)
        self.assertAlmostEqual(_c(r, "Bloque de cortante de la placa")["cap"] / KIP, 345, delta=12)
        self.assertAlmostEqual(_c(r, "Bloque de cortante del ala")["cap"] / KIP, 461, delta=18)

    def test_equilibrio_y_soldadura(self):
        r = calc_pas(self._inp())
        tr = {m["sym"]: m for m in r["combos"][0]["trace"]}
        self.assertAlmostEqual(tr["Pconn"]["val"] / KIP, 346, delta=0.5)                     # Pconn = 346 kip
        self.assertAlmostEqual(tr["Mconn"]["val"] / KFT, 160, delta=0.5)                     # Mconn = 160 kip-ft
        self.assertAlmostEqual(tr["fw"]["val"] / (453.592 / 2.54), 10.6, delta=0.1)                # 10.6 kip/in de soldadura
        # filete requerido: 7.61/16 in → el de 1/2 in cumple y el de 7/16 in no
        self.assertLess(_c(r, "Soldadura placa")["ratio"], 1)
        r2 = calc_pas(self._inp(pp_w=7 / 16 * IN))
        self.assertGreater(_c(r2, "Soldadura placa")["ratio"], 1)

    def test_longitud_de_placa(self):
        r = calc_pas(self._inp())
        v = next(m for m in r["memoria_global"] if m["sym"] == "Lplaca")["val"]
        self.assertAlmostEqual(v / 2.54, 53.5, delta=0.1)           # 53.5 in (valor de la guía)


if __name__ == "__main__":
    unittest.main()
