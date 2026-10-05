"""Motor de cálculo — conexión simple a cortante, viga al ALA de una columna.

Misma verificación del lado de la viga que `cortante_vv` (hoja CORTANTE_VIGA_VIGA_AISC: AISC 360-16 J2, J3, J4;
AISC Manual 15.ª ed. Partes 9 y 10), con el ala de la columna como elemento de soporte:
  · el espesor de soporte para aplastamiento/desgarre de los pernos (doble ángulo) y para el filete mínimo
    de la placa (Manual Ec. 9-2/9-3) es el espesor del ALA de la columna (tf) y su Fu;
  · no hay destaje (la viga no necesita rebaje) ni viga opuesta que comparta pernos (Ru_op = 0).
Verificado con AISC Design Examples v15, Ej. II.A-1A (doble ángulo atornillado a ala de columna).

No incluye: flexión local del ala de columna, conexión al alma de la columna ni columnas HSS.
Unidades canónicas: Tonf · mm · kgf/cm².
"""
import copy
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from cortante_vv import engine as _vv  # noqa: E402
from end_plate import engine as _ep  # noqa: E402  (catálogo de perfiles de columna HA / W)

ARMADO = "ARMADO (flejes soldados)"
_C = _ep.CAT
def _col(L, r):
    v = _C.get(L, [])
    return v[r] if r < len(v) else None


COLUMNAS = {_col("G", r): (_col("H", r), _col("I", r), _col("J", r), _col("K", r))
            for r in range(4, 40)
            if _col("G", r) and _col("H", r) is not None and _col("G", r) not in ("Perfil", "ARMADO (flejes soldados)")}

# ── especificación de entradas: la de cortante_vv con la sección de soporte reemplazada ──────────────
CAT = _vv.CAT
_ocultos = {"destaje", "cope_dc", "cope_c", "Ru_op"}
SPEC = copy.deepcopy(_vv.SPEC)
SPEC["titulo"] = "CONEXIÓN SIMPLE A CORTANTE — VIGA AL ALA DE COLUMNA"
SPEC["norma"] = ("AISC 360-16 (J2, J3, J4)  ·  AISC Manual 15ª ed. Partes 9 y 10  ·  LRFD  ·  "
                 "Unidades: Tonf, mm, kgf/cm²  ·  Soporte: ala de columna")
for sec in SPEC["secciones"]:
    sec["campos"] = [c for c in sec["campos"] if c["name"] not in _ocultos]
    if sec["titulo"].startswith("2."):
        sec["titulo"] = "2. COLUMNA (soporte — conexión al ala)"
        sec["campos"] = [
            {"name": "co_perfil", "label": "Perfil (catálogo o ARMADO)", "unit": "", "default": "HA500X250X10X15",
             "row": 28, "options": [ARMADO] + list(COLUMNAS)},
            {"name": "co_E_d", "label": "Peralte d (armado)", "unit": "mm", "default": 500, "row": 29, "armado_de": "co_perfil"},
            {"name": "co_E_bf", "label": "Ancho de ala bf (armado)", "unit": "mm", "default": 250, "row": 30, "armado_de": "co_perfil"},
            {"name": "co_E_tw", "label": "Espesor de alma tw (armado)", "unit": "mm", "default": 10, "row": 31, "armado_de": "co_perfil"},
            {"name": "co_E_tf", "label": "Espesor de ala tf (armado)", "unit": "mm", "default": 15, "row": 32, "armado_de": "co_perfil"},
            {"name": "co_acero", "label": "Acero", "unit": "", "default": "A572 Gr50", "row": 33,
             "options": next(c["options"] for s in _vv.SPEC["secciones"] for c in s["campos"] if c["name"] == "vp_acero")},
        ]
        sec["derivados"] = [
            {"row": 29, "name": "co_d_mm", "label": "Peralte d", "unit": "mm"},
            {"row": 30, "name": "co_bf_mm", "label": "Ancho de ala bf", "unit": "mm"},
            {"row": 31, "name": "co_tw_mm", "label": "Espesor de alma tw", "unit": "mm"},
            {"row": 32, "name": "co_tf_mm", "label": "Espesor de ala tf (soporte)", "unit": "mm"},
        ]
    elif "derivados" in sec:
        sec["derivados"] = [d for d in sec["derivados"] if d["row"] not in (29, 30, 31, 32, 34)]
_RENOMBRAR = (("alma de viga principal", "ala de columna"), ("Alma de viga principal", "Ala de columna"),
              ("viga principal", "columna"), ("VIGA PRINCIPAL", "COLUMNA"), ("twg", "tf col"))


def _ren(t):
    for a, b in _RENOMBRAR:
        t = t.replace(a, b)
    return t


for sec in SPEC["secciones"]:
    for c in sec["campos"]:
        c["label"] = _ren(c["label"])
SPEC["notas"] = [n for n in SPEC.get("notas", [])] + [
    "Soporte = ala de columna: su espesor tf y su Fu reemplazan al alma de la viga principal en el aplastamiento "
    "de los pernos de los ángulos y en el filete mínimo de la placa (Manual Ec. 9-2/9-3).",
    "Sin destaje y sin viga opuesta. No incluye flexión local del ala de columna ni conexión al alma de columna.",
]

def calcular(inp: dict) -> dict:
    co = inp.get("co_perfil", "HA500X250X10X15")
    if co == ARMADO:
        d, bf, tw, tf = (float(inp.get(k, v)) for k, v in (("co_E_d", 500), ("co_E_bf", 250), ("co_E_tw", 10), ("co_E_tf", 15)))
    else:
        d, bf, tw, tf = COLUMNAS[co]
    vv = {k: v for k, v in inp.items() if not k.startswith("co_")}
    vv.update({"destaje": "Sin destaje", "cope_dc": 0, "cope_c": 0, "Ru_op": 0,
               "vp_perfil": ARMADO, "DIS_E29": d, "DIS_E30": bf, "DIS_E31": tf, "DIS_E32": tf,
               "vp_acero": inp.get("co_acero", "A572 Gr50")})
    res = _vv.calcular(vv)
    for c in res["checks"]:
        c["nombre"], c["grupo"], c["ref"] = _ren(c["nombre"]), _ren(c["grupo"]), _ren(c["ref"])
    for m in res["memoria_global"]:
        m["desc"], m["sec"] = _ren(m["desc"]), _ren(m["sec"])
    res["derivados"].update({"co_d_mm": d, "co_bf_mm": bf, "co_tw_mm": tw, "co_tf_mm": tf})
    res["vars"]["columna"] = {"d": d, "bf": bf, "tw": tw, "tf": tf}
    return res
