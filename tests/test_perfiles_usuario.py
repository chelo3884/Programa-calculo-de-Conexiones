import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import perfiles_usuario as pu  # noqa: E402


class TestPerfiles(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["CONEXIONES_DATOS"] = self.tmp.name

    def tearDown(self):
        os.environ.pop("CONEXIONES_DATOS", None)
        self.tmp.cleanup()

    def test_guardar_y_leer(self):
        pu.guardar([{"nombre": "IPE-X", "tipo": "I", "d": 300, "bf": 150, "tw": 7, "tf": 10.7},
                    {"nombre": "TC 150x150x4", "tipo": "HSS", "d": 150, "bf": 150, "tf": 3.7}])
        r = pu.leer()
        self.assertEqual([p["nombre"] for p in r], ["IPE-X", "TC 150x150x4"])
        self.assertEqual(r[1]["tw"], 3.7)               # HSS: tw = t

    def test_validaciones(self):
        for mal in ({"nombre": "", "d": 1}, {"nombre": "A", "tipo": "Z"}, {"nombre": "A", "d": 300, "bf": 100, "tw": 120, "tf": 10},
                    {"nombre": "A", "d": 300, "bf": 100, "tw": 6}):
            with self.assertRaises(ValueError):
                pu.validar([mal])
        with self.assertRaises(ValueError):
            pu.validar([{"nombre": "A", "d": 300, "bf": 100, "tw": 6, "tf": 9}] * 2)

    def test_importar_excel_con_coma_decimal_y_tipo_inferido(self):
        txt = "Perfil\tH\tB\tt\ttw\tkg/m\nIPN-200\t200\t90\t11,3\t7,5\t26,2\nTC 100x100x3\t100\t100\t2,8\t\t8.5\n"
        r = pu.parse_texto(txt)
        self.assertEqual(r[0]["tipo"], "I")
        self.assertAlmostEqual(r[0]["tf"], 11.3)
        self.assertEqual(r[1]["tipo"], "HSS")
        self.assertAlmostEqual(r[1]["peso"], 8.5)

    def test_archivo_inexistente(self):
        self.assertEqual(pu.leer(), [])


if __name__ == "__main__":
    unittest.main()
