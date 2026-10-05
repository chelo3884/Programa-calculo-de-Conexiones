"""Motor de cálculo — conexión simple a cortante, viga secundaria a alma de viga principal.

Evalúa el modelo generado desde CORTANTE_VIGA_VIGA_AISC.xlsx (AISC 360-16 J2, J3, J4; AISC Manual 15.ª ed.
Partes 9 y 10; LRFD). Ver tools/xl2py.py y xlcore.py. Unidades canónicas: Tonf · mm · kgf/cm².
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from xlcore import XlModule  # noqa: E402

from . import xl_model  # noqa: E402

_MOD = XlModule(os.path.dirname(os.path.abspath(__file__)), xl_model)
SPEC = _MOD.SPEC
CAT = _MOD.CAT
calcular = _MOD.calcular
