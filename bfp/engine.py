"""Motor de cálculo del módulo 'bfp': evalúa el modelo generado desde la hoja de Excel (tools/xl2py.py, xlcore.py).

Unidades canónicas de entrada y salida: Tonf · Tonf·m · mm · m · kgf/cm².
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
