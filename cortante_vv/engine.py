"""Motor de cálculo — conexión simple a cortante, viga secundaria a alma de viga principal.

Evalúa el modelo generado desde CORTANTE_VIGA_VIGA_AISC.xlsx (AISC 360-16 J2, J3, J4; AISC Manual 15.ª ed.
Partes 9 y 10; LRFD). Ver tools/xl2py.py y xlcore.py. Unidades canónicas: Tonf · mm · kgf/cm².
"""
import os
import sys
import types

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from xlcore import XlModule  # noqa: E402

from . import xl_model as _xl0  # noqa: E402

# El modelo generado (xl_model.py) no se edita: se extiende una COPIA con el nivel relativo de las vigas y sus comprobaciones.
# `cortante_hss` y `cortante_vc` siguen usando el modelo original / desactivan estas verificaciones (vg_nivel = "No aplica").
NIVELES = ["Ala superior al ras", "Centrada", "Desnivel manual"]
_NA = "_eq(vg_nivel,'No aplica')"
_SOLAPA_SUP = f"_or({_NA},(d_dz>=g_tf))"                   # sin conflicto entre alas superiores
_SOLAPA_INF = f"_or({_NA},((d_dz+b_d)<=(g_d-g_tf)))"        # sin conflicto entre alas inferiores
_NUEVOS = [
    (60, 'CHEQUEO', 'Destaje superior libra el ala superior de la viga principal: dc ≥ tfg − dz + 10 mm', 'Geometría (holgura 10 mm: criterio propio)', 'cm',
     f"(('—') if ({_SOLAPA_SUP}) else ((g_tf-d_dz+1)))", f"(('—') if ({_SOLAPA_SUP}) else (c_top))",
     f"(('N/A') if ({_SOLAPA_SUP}) else (_min(((g_tf-d_dz+1)/_max(c_top,0.01)),99)))", "'—'"),
    (61, 'CHEQUEO', 'Destaje superior: longitud c ≥ (bfg − twg)/2 − holgura + 10 mm', 'Geometría (holgura 10 mm: criterio propio)', 'cm',
     f"(('—') if ({_SOLAPA_SUP}) else (((g_bf-g_tw)/2-(setback/10)+1)))", f"(('—') if ({_SOLAPA_SUP}) else (c_c))",
     f"(('N/A') if ({_SOLAPA_SUP}) else (_min((((g_bf-g_tw)/2-(setback/10)+1)/_max(c_c,0.01)),99)))", "'—'"),
    (62, 'CHEQUEO', 'Destaje inferior libra el ala inferior de la viga principal (si se solapan)', 'Geometría (holgura 10 mm: criterio propio)', 'cm',
     f"(('—') if ({_SOLAPA_INF}) else ((d_dz+b_d-(g_d-g_tf)+1)))", f"(('—') if ({_SOLAPA_INF}) else (c_bot))",
     f"(('N/A') if ({_SOLAPA_INF}) else (_min(((d_dz+b_d-(g_d-g_tf)+1)/_max(c_bot,0.01)),99)))", "'—'"),
    (63, 'CHEQUEO', 'Placa/ángulos bajo el ala superior de la viga principal (≥ tfg + 10 mm)', 'Geometría (holgura 10 mm: criterio propio)', 'cm',
     f"(('—') if ({_NA}) else ((g_tf+1)))", f"(('—') if ({_NA}) else ((d_dz+e_top)))",
     f"(('N/A') if ({_NA}) else (_min(((g_tf+1)/_max((d_dz+e_top),0.01)),99)))", "'—'"),
    (64, 'CHEQUEO', 'Placa/ángulos sobre el ala inferior de la viga principal (≥ tfg + 10 mm)', 'Geometría (holgura 10 mm: criterio propio)', 'cm',
     f"(('—') if ({_NA}) else ((d_dz+e_top+e_L)))", f"(('—') if ({_NA}) else ((g_d-g_tf-1)))",
     f"(('N/A') if ({_NA}) else (((d_dz+e_top+e_L)/_max((g_d-g_tf-1),0.01))))", "'—'"),
]
xl_model = types.SimpleNamespace(**{k: getattr(_xl0, k) for k in ("NCOMBO", "DERIVED", "COMBO", "RATIO_COL")})
xl_model.GLOBAL = list(_xl0.GLOBAL) + [
    (100, '0. TIPO, GEOMETRÍA Y MATERIALES', 'dz', 'Desnivel: tope de la viga soportada bajo el tope de la viga principal', 'cm', 'd_dz',
     f"((0) if (_or(_eq(vg_nivel,'Ala superior al ras'),{_NA})) else ((((g_d-b_d)/2)) if (_eq(vg_nivel,'Centrada')) else ((vg_dz/10))))")]
xl_model.CHECKS = []
for _c in _xl0.CHECKS:
    if _c[0] == 48 and _c[1] == 'CHEQUEO':       # el ratio explotaba (÷1e-9) cuando la placa quedaba al ras del tope de la viga
        _c = (_c[0], _c[1], 'Placa/ángulos libran el ala de la viga soportada: ztop ≥ tf + k (sin destaje) | dc (con destaje)', _c[3], _c[4], _c[5], _c[6],
              f"_min({_c[7]},99)", _c[8])
    xl_model.CHECKS.append(_c)
xl_model.CHECKS += _NUEVOS

_MOD = XlModule(os.path.dirname(os.path.abspath(__file__)), xl_model)
SPEC = _MOD.SPEC
for _s in SPEC["secciones"]:
    if any(c["name"] == "setback" for c in _s["campos"]):
        _i = next(i for i, c in enumerate(_s["campos"]) if c["name"] == "setback") + 1
        _r = max(c["row"] for c in _s["campos"])
        _s["campos"][_i:_i] = [
            {"name": "vg_nivel", "label": "Nivel de la viga soportada respecto a la principal", "unit": "", "default": NIVELES[0], "row": _r + 1, "options": NIVELES},
            {"name": "vg_dz", "label": "Desnivel manual: tope de la soportada bajo el tope de la principal", "unit": "mm", "default": 0, "row": _r + 2}]
SPEC["notas"] = list(SPEC.get("notas", [])) + [
    "Nivel de las vigas: lo usual es alinear las alas superiores (desnivel 0): la soportada necesita destaje superior para librar el ala de la principal "
    "(dc ≥ tfg + 10 mm y c ≥ (bfg − twg)/2 − holgura + 10 mm). Con «Centrada» la placa debe quedar entre las alas de la principal."]
CAT = _MOD.CAT
calcular = _MOD.calcular
