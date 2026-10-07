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
_EXT = "_eq(t_se,1)"                                        # placa extendida: la viga termina fuera del ala de la principal, no hay destaje
_SOLAPA_SUP = f"_or({_NA},{_EXT},(d_dz>=g_tf))"             # sin conflicto entre alas superiores
_SOLAPA_INF = f"_or({_NA},{_EXT},((d_dz+b_d)<=(g_d-g_tf)))"  # sin conflicto entre alas inferiores
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
    (63, 'CHEQUEO', 'Placa/ángulos bajo el ala superior de la viga principal (≥ tfg + 5 mm)', 'Geometría (holgura 10 mm: criterio propio)', 'cm',
     f"(('—') if ({_NA}) else ((g_tf+0.5)))", f"(('—') if ({_NA}) else ((d_dz+e_top)))",
     f"(('N/A') if ({_NA}) else (_min(((g_tf+0.5)/_max((d_dz+e_top),0.01)),99)))", "'—'"),
    (64, 'CHEQUEO', 'Placa/ángulos sobre el ala inferior de la viga principal (≥ tfg + 5 mm)', 'Geometría (holgura 10 mm: criterio propio)', 'cm',
     f"(('—') if ({_NA}) else ((d_dz+e_top+e_L)))", f"(('—') if ({_NA}) else ((g_d-g_tf-0.5)))",
     f"(('N/A') if ({_NA}) else (((d_dz+e_top+e_L)/_max((g_d-g_tf-0.5),0.01))))", "'—'"),
]
xl_model = types.SimpleNamespace(**{k: getattr(_xl0, k) for k in ("NCOMBO", "DERIVED", "COMBO", "RATIO_COL")})
_TT = "((1) if (_and(_eq(t_se,1),(not _eq(vg_nivel,'No aplica')))) else (0))"
_BLOQUE_T = [
    (100, '0. TIPO, GEOMETRÍA Y MATERIALES', 'dz', 'Desnivel: tope de la viga soportada bajo el tope de la viga principal', 'cm', 'd_dz',
     f"((0) if (_or(_eq(vg_nivel,'Ala superior al ras'),{_NA})) else ((((g_d-b_d)/2)) if (_eq(vg_nivel,'Centrada')) else ((vg_dz/10))))"),
    (101, '4. PLACA SIMPLE EXTENDIDA — Manual Parte 10', 'T', '1 = placa extendida en T (tramo ancho soldado a la principal + lengüeta atornillada)', '-', 't_T', _TT),
    (102, '4. PLACA SIMPLE EXTENDIDA — Manual Parte 10', 'xs', 'Ancho del tramo ancho: hasta 10 mm antes del extremo de la viga', 'cm', 'x_xs', "((_max(((setback/10)-1),0)) if (_eq(t_T,1)) else (0))"),
    (103, '4. PLACA SIMPLE EXTENDIDA — Manual Parte 10', 'Hs', 'Altura del tramo ancho: del borde superior de la placa a 10 mm sobre el ala inferior de la principal', 'cm', 'x_Hs',
     "((_max(((g_d-g_tf-1)-(d_dz+e_top)),e_L)) if (_eq(t_T,1)) else (e_L))"),
]
_idx = next(i for i, c in enumerate(_xl0.GLOBAL) if c[0] == 65)
xl_model.GLOBAL = list(_xl0.GLOBAL[:_idx]) + _BLOQUE_T + list(_xl0.GLOBAL[_idx:])
_G2 = []
for _g in xl_model.GLOBAL:
    if _g[0] == 65 and _g[6].strip() == '(k_R*e_xb)':          # Mu de la lengüeta en la unión con el tramo ancho
        _g = _g[:6] + ("((k_R*_max((e_xb-x_xs),0)) if (_eq(t_T,1)) else (k_R*e_xb))",)
    elif _g[0] == 78:                                          # filetes: longitud = altura del tramo ancho en la placa en T
        _g = _g[:6] + (_g[6].replace('*e_L)', '*x_Hs)'),)
    _G2.append(_g)
xl_model.GLOBAL = _G2 + [
    (104, '5. SOLDADURA Y VIGA PRINCIPAL (placa simple)', 'f', 'Placa en T: tensión en los filetes por V y Ru·a (2 filetes de longitud Hs, elástico): √((Ru/2Hs)² + (Ru·a·3/Hs²)²)', 'kgf/cm', 'w_fT',
     "(_sqrt(((k_R/(2*x_Hs))**2)+(((k_R*e_xb*3)/(x_Hs**2))**2)))"),
    (105, '5. SOLDADURA Y VIGA PRINCIPAL (placa simple)', 'q', 'Resistencia por cm de filete: 0.75·0.6·FEXX·0.707·w', 'kgf/cm', 'w_qT',
     "((((0.75*0.6)*w_FEXX)*0.707)*pl_w/10)")]
xl_model.CHECKS = []
for _c in _xl0.CHECKS:
    if _c[0] == 48 and _c[1] == 'CHEQUEO':       # el ratio explotaba (÷1e-9) cuando la placa quedaba al ras del tope de la viga
        # sin destaje la placa debe librar el ala y el filete (ztop ≥ tf + k); con destaje el alma ya no está ahí (lo gobierna «borde vertical en alma»)
        _c = (_c[0], _c[1], 'Placa/ángulos libran el ala de la viga soportada: ztop ≥ tf + k (sin destaje)', _c[3], _c[4],
              f"(({_c[5]}) if ({_NA}) else (((b_k) if ((c_top<=0)) else (0))))", _c[6],
              f"(({_c[7]}) if ({_NA}) else (_min((((b_k) if ((c_top<=0)) else (0))/_max(e_top,0.01)),99)))", _c[8])
    xl_model.CHECKS.append(_c)
    if _c[0] == 28:
        xl_model.CHECKS.append((66, 'CHEQUEO', 'Placa en T: filetes al alma de la principal con excentricidad a (grupo de 2 filetes, elástico)', 'J2.4 · criterio propio', 'kgf/cm',
                                "(('—') if (_eq(t_T,0)) else (w_fT))", "(('—') if (_eq(t_T,0)) else (w_qT))",
                                "(('N/A') if (_eq(t_T,0)) else ((w_fT/_max(w_qT,1e-09))))", "'—'"))
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
POS_AUTO = "Automática: 10 mm bajo el ala de la viga principal"
POS_MAN = "Manual (tope de viga → primer perno)"
for _s in SPEC["secciones"]:
    if any(c["name"] == "pn_top" for c in _s["campos"]):
        _i = next(i for i, c in enumerate(_s["campos"]) if c["name"] == "pn_top")
        _s["campos"][_i:_i] = [{"name": "pn_pos", "label": "Posición vertical de la placa / ángulos", "unit": "", "default": POS_AUTO,
                               "row": _s["campos"][_i]["row"] - 1, "options": [POS_AUTO, POS_MAN]}]
SPEC["notas"].append("Placa extendida: se usa para NO destajar la viga soportada; el extremo de la viga queda fuera de la punta del ala de la principal, "
                     "es decir a (bfg − twg)/2 + holgura del alma, y `a` debe ser mayor que ese valor más el borde de la viga (Manual Parte 10, placa extendida).")
SPEC["notas"].append("Placa en T (extendida): tramo ancho soldado a la principal entre sus alas (hasta 10 mm del ala inferior) y una lengüeta de altura L con los pernos. "
                     "Momento de la lengüeta = Ru·(a − xs) en la unión con el tramo ancho; filetes con longitud Hs y excentricidad a (grupo elástico, criterio propio: el Manual Parte 10 no trata esta forma). "
                     "El alma de la soportada debe tener borde ≥ 2·db: aumente `a` por encima de (bfg − twg)/2 + holgura + 2·db.")
SPEC["notas"].append("Posición automática: el borde superior de la placa queda 10 mm bajo la cara inferior del ala superior de la viga principal "
                     "(y no más arriba que el destaje / ala de la soportada); el primer perno se deduce como ztop + Lev.")
CAT = _MOD.CAT


def calcular(inp: dict) -> dict:
    inp = dict(inp)
    nivel = inp.get("vg_nivel", NIVELES[0])
    ext = inp.get("tipo") == "Placa simple extendida" and nivel != "No aplica"
    auto = str(inp.get("pn_pos", POS_AUTO)).startswith("Autom") and nivel != "No aplica"
    set_ef = None
    if ext:
        inp["destaje"] = "Sin destaje"            # la placa extendida existe precisamente para no destajar la viga soportada
    if ext or auto:
        d = _MOD.calcular(dict(inp, pn_top=0))["derivados"]
        dz = {"Centrada": (d["vp_d_mm"] - d["vg_d_mm"]) / 2, "Desnivel manual": float(inp.get("vg_dz", 0) or 0)}.get(nivel, 0.0)
        if ext and (dz < d["vp_tf_mm"] or dz + d["vg_d_mm"] > d["vp_d_mm"] - d["vp_tf_mm"]):
            # las alas se solapan en altura: el extremo de la viga debe quedar fuera de la punta del ala de la principal
            set_ef = float(inp.get("setback", 15) or 0) + (d["vp_bf_mm"] - d["vp_tw_mm"]) / 2
            inp["setback"] = set_ef
    if auto:
        kw = float(inp.get("vg_kw", 5) or 0)
        dc = 0.0 if inp.get("destaje", "Destaje superior") == "Sin destaje" else float(inp.get("cope_dc", 30) or 0)
        e_top = max(d["vp_tf_mm"] + 10 - dz, 0.0 if dc > 0 else d["vg_tf_mm"] + kw)            # mm bajo el tope de la viga soportada
        inp["pn_top"] = e_top + float(inp.get("pn_Lev", 35) or 0)
    res = _MOD.calcular(inp)
    res["derivados"]["pn_top_ef"] = inp.get("pn_top", 70)
    res["derivados"]["setback_ef"] = set_ef if set_ef is not None else inp.get("setback", 15)
    return res
