"""Conexión simple a cortante — viga a pared de columna HSS rectangular (placa simple o placa pasante).

Reutiliza la verificación de `cortante_vv` (placa simple: pernos, fluencia/ruptura/bloque de cortante de la placa,
filetes, viga soportada; AISC 360-16 J2-J4, Manual Partes 9 y 10) con la PARED del HSS como soporte (su espesor t y su Fu
reemplazan al alma de la viga principal), y agrega las verificaciones propias de HSS (Manual Parte 10, Design Examples
v15 K.6 y K.7):
  · pared no esbelta: b/t ≤ 1.40·√(E/Fy), b = B − 3t        (placa simple)
  · punzonamiento de la pared (Manual Ec. 10-7a): Ru·e ≤ 0.75·Fu·t·lp²/5   (placa simple)
  · placa pasante: Vfu = Ru·(B + a)/B en la línea de soldadura más cercana, tamaño de filete requerido,
    fluencia y ruptura por corte de las dos paredes del HSS (J4.2)
  · espesor mínimo de pared para los filetes: t ≥ 3.09·D/Fu (Manual Ec. 9-2)
No incluye el doble ángulo (K.3: ángulos soldados al HSS), asientos (K.4/K.5), ni la flexión local de la pared por
fuerzas concentradas (K.1/K.2). El espesor t debe ser el de DISEÑO (0.93·tnom en HSS soldado por resistencia eléctrica).
Unidades canónicas: Tonf · mm · kgf/cm².
"""
import copy
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import aisc  # noqa: E402
from cortante_vv import engine as _vv0  # noqa: E402
from placa_base.engine import CATALOGOS  # noqa: E402
from xlcore import XlModule  # noqa: E402

from cortante_vv import xl_model  # noqa: E402

PERSONALIZADO = "ARMADO (flejes soldados)"   # misma etiqueta que los demás módulos: habilita los campos manuales
HSS = {p["nombre"]: p for p in CATALOGOS["hss"]}
ACEROS_HSS = ["A500 Gr B", "A500 Gr C"]
CONEX = ["Placa simple soldada a la pared", "Placa pasante (through-plate)"]
IN = aisc.IN

# instancia propia del modelo de cortante_vv con los aceros A500 agregados al catálogo (filas libres 9 y 10)
_MOD = XlModule(os.path.dirname(os.path.abspath(_vv0.__file__)), xl_model)
for _i, _n in enumerate(ACEROS_HSS):
    _fy, _fu = aisc.ACEROS[_n]
    _MOD.CAT["G"][8 + _i], _MOD.CAT["H"][8 + _i], _MOD.CAT["I"][8 + _i] = _n, _fy, _fu

_ocultos = {"destaje", "cope_dc", "cope_c", "Ru_op", "tipo"}
SPEC = copy.deepcopy(_MOD.SPEC)
CAT = _MOD.CAT
SPEC["titulo"] = "CONEXIÓN SIMPLE A CORTANTE — VIGA A COLUMNA HSS (PLACA SIMPLE / PASANTE)"
SPEC["norma"] = ("AISC 360-16 (J2, J3, J4)  ·  AISC Manual 15ª ed. Partes 9 y 10  ·  Design Examples K.6 / K.7  ·  LRFD  ·  "
                 "Unidades: Tonf, mm, kgf/cm²  ·  Soporte: pared de HSS")
_COL_CAMPOS = [
    {"name": "hss_perfil", "label": "Perfil HSS (catálogo o ARMADO)", "unit": "", "default": "HSS6X6X3/8",
     "row": 28, "options": [PERSONALIZADO] + list(HSS)},
    {"name": "hss_cara", "label": "Cara de la conexión (catálogo)", "unit": "", "default": "H", "row": 29, "options": ["H", "B"]},
    {"name": "hss_W", "label": "Ancho de la cara de conexión (armado)", "unit": "mm", "default": 152.4, "row": 30, "armado_de": "hss_perfil"},
    {"name": "hss_D", "label": "Profundidad en la dirección de la placa (armado)", "unit": "mm", "default": 152.4, "row": 31, "armado_de": "hss_perfil"},
    {"name": "hss_t", "label": "Espesor de diseño t (armado)", "unit": "mm", "default": 8.86, "row": 32, "armado_de": "hss_perfil"},
    {"name": "co_acero", "label": "Acero", "unit": "", "default": "A500 Gr C", "row": 33, "options": ACEROS_HSS},
    {"name": "hss_conex", "label": "Tipo de conexión", "unit": "", "default": CONEX[0], "row": 34, "options": CONEX},
]
for sec in SPEC["secciones"]:
    sec["campos"] = [c for c in sec["campos"] if c["name"] not in _ocultos]
    if sec["titulo"].startswith("2."):
        sec["titulo"] = "2. COLUMNA HSS (soporte)"
        sec["campos"] = _COL_CAMPOS
        sec["derivados"] = [
            {"row": 30, "name": "co_bf_mm", "label": "Ancho de la cara W", "unit": "mm"},
            {"row": 31, "name": "co_d_mm", "label": "Profundidad D", "unit": "mm"},
            {"row": 32, "name": "co_tf_mm", "label": "Espesor de diseño t", "unit": "mm"},
            {"row": 33, "name": "co_bt", "label": "b/t  (b = W − 3t)", "unit": ""},
        ]
    elif sec["titulo"].startswith("TIPO"):
        pass
    elif "derivados" in sec:
        sec["derivados"] = [d for d in sec["derivados"] if d["row"] not in (29, 30, 31, 32, 34)]
    for c in sec["campos"]:
        for a, b in (("alma de viga principal", "pared del HSS"), ("viga principal", "columna HSS")):
            c["label"] = c["label"].replace(a, b)
    if sec["titulo"].startswith("4."):
        sec["titulo"] = "4. PLACA SIMPLE / PASANTE"
    if sec["titulo"].startswith("5."):
        sec["campos"] = []
SPEC["secciones"] = [s for s in SPEC["secciones"] if s["campos"] or s.get("derivados")]
SPEC["notas"] = [
    "Soporte = pared del HSS: su espesor de diseño t y su Fu reemplazan al alma de la viga principal en el filete mínimo (Manual Ec. 9-2/9-3).",
    "Placa simple: la pared no debe ser esbelta (b/t ≤ 1.40√(E/Fy)) y se verifica el punzonamiento (Manual Ec. 10-7). Si la pared es esbelta, use placa pasante.",
    "Placa pasante: la placa atraviesa el HSS y se suelda a las dos paredes; la parte de la viga se trata como placa simple (AISC no tiene reglas específicas, ver K.7).",
    "No incluye doble ángulo, asientos ni flexión local de la pared por cargas concentradas (K.1, K.2, K.4, K.5).",
]
_RENOMBRAR = (("alma de viga principal", "pared del HSS"), ("Alma de viga principal", "Pared del HSS"),
              ("viga principal", "columna HSS"), ("VIGA PRINCIPAL", "COLUMNA HSS"))


def _ren(t):
    for a, b in _RENOMBRAR:
        t = t.replace(a, b)
    return t


def _geom(inp):
    p = inp.get("hss_perfil", "HSS6X6X3/8")
    if p == PERSONALIZADO:
        return (float(inp.get("hss_W", 152.4)), float(inp.get("hss_D", 152.4)), float(inp.get("hss_t", 8.86)))
    h = HSS[p]
    return (h["H"], h["B"], h["t"]) if inp.get("hss_cara", "H") == "H" else (h["B"], h["H"], h["t"])


def _chk(res, grupo, nombre, ref, dem, cap, q="F", activo=True, lim=0.9):
    ratio = dem / cap if activo and cap else None
    est = "N/A" if ratio is None else ("NO CUMPLE" if ratio > 1 else ("AL LÍMITE" if ratio > lim else "CUMPLE"))
    res["checks"].append({"fila": len(res["checks"]) + 1, "grupo": grupo, "nombre": nombre, "ref": ref,
                          "unit": {"F": "Tonf", "M": "Tonf·m", "": "-"}[q], "q": q,
                          "dem": dem if activo else None, "cap": cap if activo else None, "ratio": ratio,
                          "estado": est, "combo": "—"})


def calcular(inp: dict) -> dict:
    W, D, t = _geom(inp)                                   # mm
    acero = inp.get("co_acero", "A500 Gr C")
    Fy, Fu = aisc.ACEROS[acero]
    vv = {k: v for k, v in inp.items() if not k.startswith(("hss_", "co_"))}
    vv.update({"tipo": "Placa simple convencional", "destaje": "Sin destaje", "cope_dc": 0, "cope_c": 0, "Ru_op": 0,
               "vp_perfil": "ARMADO (flejes soldados)", "DIS_E29": D, "DIS_E30": W, "DIS_E31": t, "DIS_E32": t,
               "vp_acero": acero})
    res = _MOD.calcular(vv)
    for c in res["checks"]:
        c["nombre"], c["grupo"], c["ref"] = _ren(c["nombre"]), _ren(c["grupo"]), _ren(c["ref"])
    for m in res["memoria_global"]:
        m["desc"], m["sec"] = _ren(m["desc"]), _ren(m["sec"])
    res["checks"] = [c for c in res["checks"] if not c["grupo"].startswith("DOBLE ÁNGULO")]
    lim = float(inp.get("lim_verde", 0.9))
    through = inp.get("hss_conex", CONEX[0]) == CONEX[1]
    Ru = float(inp.get("Ru", 6)) * 1000                      # kgf
    tc, Wc, Dc = t / 10, W / 10, D / 10
    a = float(inp.get("pl_a", 65)) / 10
    Lp = res["vars"]["e_L"]                                              # cm
    FEXX = aisc.ELECTRODOS.get(inp.get("sd_elec", "E70XX"), 4920)
    w = float(inp.get("pl_w", 6)) / 10
    G = "COLUMNA HSS"
    bt = (Wc - 3 * tc) / tc
    lim_bt = 1.40 * math.sqrt(aisc.E / Fy)
    _chk(res, G, "Pared no esbelta: b/t ≤ 1.40√(E/Fy)", "Manual Parte 10 (K.6)", bt, lim_bt, "", not through, lim)
    cap_p = 0.75 * Fu * tc * Lp ** 2 / 5
    _chk(res, G, "Punzonamiento de la pared: Ru·e ≤ φFu·t·lp²/5", "Manual Ec. 10-7a", Ru * a / 1e5, cap_p / 1e5, "M", not through, lim)
    if through:
        Vfu = Ru * (Dc + a) / Dc
        wcap = 2 * aisc.rn_filete(FEXX, w, Lp)
        _chk(res, G, "Placa pasante: soldadura (línea más cercana a los pernos)", "Manual Ec. 8-2 · K.7", Vfu / 1e3, wcap / 1e3, "F", True, lim)
        _chk(res, G, "Placa pasante: fluencia por corte de las 2 paredes", "J4.2(a)", Vfu / 1e3,
             aisc.rn_fluencia_corte(Fy, 2 * tc * Lp) / 1e3, "F", True, lim)
        _chk(res, G, "Placa pasante: ruptura por corte de las 2 paredes", "J4.2(b)", Vfu / 1e3,
             aisc.rn_ruptura_corte(Fu, 2 * tc * Lp) / 1e3, "F", True, lim)
    for i, c in enumerate(res["checks"], 1):
        c["fila"] = i
    ratios = [c["ratio"] for c in res["checks"] if c["ratio"] is not None]
    rmax = max(ratios) if ratios else None
    res["resumen"] = {"estado": "NO CUMPLE" if rmax and rmax > 1 else ("CUMPLE AL LÍMITE" if rmax and rmax > lim else "CUMPLE"),
                      "ratio_max": rmax}
    res["derivados"].update({"co_bf_mm": W, "co_d_mm": D, "co_tw_mm": t, "co_tf_mm": t, "co_bt": bt})
    res["vars"]["hss"] = {"W": W, "D": D, "t": t, "through": through}
    return res
