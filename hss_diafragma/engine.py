"""Conexión de momento viga W – columna HSS con PLACA DE RECORTE (diafragma externo / collar), NO sísmica.

Fuente: «HSS column – cutout plate wide-flange beam moment connection (AISC360-10)», cálculo Tedds de P. Stewart and Associates
(544846613-HSS-WIDE-FLANGE-EXTERNAL-DIAPHRAGM-CONNECTION.pdf). Dos placas con un recorte del tamaño del HSS rodean la columna (arriba y
abajo de las alas); las alas de las vigas se atornillan a ellas. Fuerza en la placa: Pr = Mr/(d + tp).

IMPORTANTE — límites del documento fuente (ver README):
  · Solo contiene: compresión y tracción de la placa, corte y aplastamiento de pernos y bloque de cortante. NO verifica la soldadura de la placa al HSS
    ni la pared del HSS, que son lo esencial de un diafragma externo.
  · Su hoja MULTIPLICA por 2.00 (el Ω de ASD) las resistencias de aplastamiento y bloque de cortante en lugar de aplicar φ = 0.75 (o dividir entre Ω): sus
    «PASS» en esos puntos están inflados ×2.67. Aquí se aplica φ = 0.75.
  · Su bloque de cortante usa un solo plano de cortante con dos filas de pernos (conservador); aquí se usan los dos planos como en DG24 Ej. 4.2.
  · Su área de tracción cuenta el ancho del recorte (B + 2·ws); aquí solo se cuentan las dos franjas de ancho ws junto al HSS. Con eso (y con su propia
    compresión, que ella misma marca FAIL) el ejemplo del documento no cumple.
Verificaciones propias, NO respaldadas por esa fuente (criterio simplificado, contrastar con CIDECT DG9 / AIJ): soldadura de la placa al perímetro del HSS y
corte de las dos paredes del HSS paralelas a la viga.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import aisc  # noqa: E402
import hss_comun as C  # noqa: E402
from handmod import Modulo, campo, seccion, spec, tabla_combos  # noqa: E402
from wuf.engine import _cv  # noqa: E402

G_PL, G_PB, G_TR = "PLACA DE RECORTE", "PERNOS DE LAS ALAS", "TRANSFERENCIA AL HSS (criterio propio)"
HOYOS = ["AISC 360-16 (Ø1: agujero 1-1/8 in)", "AISC 360-10 (Ø1: agujero 1-1/16 in)"]
SPEC = spec(
    "CONEXIÓN DE MOMENTO VIGA W – COLUMNA HSS CON PLACA DE RECORTE (DIAFRAGMA EXTERNO, NO SÍSMICA)",
    "Ej. Tedds «HSS cutout plate» (AISC 360-10)  ·  AISC 360-16 D2, E3, J3, J4  ·  LRFD  ·  Unidades: Tonf, Tonf·m, mm, kgf/cm²",
    [
        seccion("DATOS GENERALES", [campo("DIS_C7", "Proyecto", "Edificio — ejemplo"), campo("DIS_C8", "Elemento / nudo", "Nudo C-2 nivel 3"),
                                    campo("lim_verde", "Límite verde / amarillo (ratio)", 0.9)]),
        seccion("1. VIGA W (igual a ambos lados)", C.campos_viga(defecto="W12X26"), C.derivados_viga()),
        seccion("2. COLUMNA HSS", C.campos_hss(), C.derivados_hss()),
        seccion("3. PLACA DE RECORTE", [
            campo("pr_acero", "Acero de la placa", "A36", options=C.ACEROS_VIGA),
            campo("pr_t", "Espesor tp", 19.05, "mm"), campo("pr_ws", "ws — franja de placa junto al HSS", 76.2, "mm"),
            campo("pr_w1", "Ancho de placa en la primera fila de pernos", 203.2, "mm"),
            campo("pr_d1", "d1 — cara del HSS a la primera fila de pernos", 101.6, "mm"),
            campo("pr_nb", "Pernos por fila y por lado", 4), campo("pr_s", "Paso s", 80, "mm"), campo("pr_g", "Gramil g entre filas", 88.9, "mm"),
            campo("pr_le", "Le — borde en la placa (última fila → extremo)", 44.45, "mm"),
            campo("pr_lef", "Borde en el ala (primera fila → extremo de la viga)", 101.6, "mm"),
            campo("pn_grado", "Grado de pernos", "A325-N (roscas incl.)", options=list(aisc.PERNOS)),
            campo("pn_diam", "Diámetro de pernos", '1"', options=aisc.DIAMETROS),
            campo("agujero", "Agujero estándar según", HOYOS[0], options=HOYOS),
            campo("sd_elec", "Electrodo", "E70XX", options=list(aisc.ELECTRODOS)),
            campo("pr_w", "Filete placa – perímetro del HSS", 12.7, "mm")]),
        seccion("4. PLACA SIMPLE DE CORTE", C.campos_placa_corte(n=3, s=80, lev=38.1, leh=50.8, tp=9.5, a=76.2, w=6.35)[:8]),
    ],
    combos=tabla_combos([("nombre", "Combinación"), ("M", "Mu de cada viga (Tonf·m)"), ("V", "Vu de cada viga (Tonf)")],
                        [{"nombre": "1.2D+1.6L", "M": 8, "V": 4}]),
    notas=["Alcance: SOLO cargas no sísmicas. Se asume el mismo momento en las vigas de ambos lados (reversible).",
           "Esta es la parte verificable con el documento fuente; la transferencia placa → HSS se verifica con un criterio simplificado propio (ver README).",
           "El documento fuente usa Ω = 2.00 como multiplicador en aplastamiento y bloque de cortante: aquí se usa φ = 0.75.",
           "La opción de agujero permite reproducir el ejemplo (AISC 360-10: 1-1/16 in para Ø1)."])


def _dh(p, I):
    if I["agujero"] == HOYOS[1] and I["pn_diam"] == '1"':
        dh = p["db"] + aisc.IN / 16
        return dh, dh + aisc.IN / 16
    return p["dh"], p["dh_net"]


def global_fn(h, I):
    P = C.hss_y_viga(I)
    bd, bbf, btw, btf, W, D, t = (P[k] for k in ("bd", "bbf", "btw", "btf", "W", "D", "t"))
    pFy, pFu = aisc.ACEROS[I["pr_acero"]]
    FEXX = aisc.ELECTRODOS[I["sd_elec"]]
    p = aisc.perno(I["pn_diam"], I["pn_grado"])
    dh, dhn = _dh(p, I)
    nb, rows = int(I["pr_nb"]), 2
    tp, ws, w1, d1, s, g = I["pr_t"] / 10, I["pr_ws"] / 10, I["pr_w1"] / 10, I["pr_d1"] / 10, I["pr_s"] / 10, I["pr_g"] / 10
    le, lef, w = I["pr_le"] / 10, I["pr_lef"] / 10, I["pr_w"] / 10
    h.sec("1. VIGA")
    Zx = bbf * btf * (bd - btf) + btw * (bd - 2 * btf) ** 2 / 4
    phiMp = h.v("φMp", "Flexión de la viga: 0.90·Fy·Zx", 0.9 * P["bFy"] * Zx, "M")
    phiv, cv = _cv((bd - 2 * btf) / btw, P["bFy"], I["vg_perfil"].startswith("W"))
    phiVn = h.v("φVn", "Cortante del alma (G2.1)", phiv * 0.6 * P["bFy"] * bd * btw * cv, "F")
    brazo = h.v("d + tp", "Brazo de momento", bd + tp, "Lc")
    h.sec("2. PLACA DE RECORTE")
    A_str = 2 * ws * tp
    h.v("Astr", "Área de las dos franjas junto al HSS: 2·ws·tp", A_str, "A")
    blim = 0.45 * math.sqrt(aisc.E / pFy)
    h.v("ws/tp", "Esbeltez de la franja (Tabla B4.1a)", ws / tp, "")
    Rc = h.v("φRn", "Compresión de las franjas (E3, no esbelta): 0.90·Fy·Astr", 0.9 * pFy * A_str, "F")
    Rty = h.v("φRn", "Fluencia en tracción de las franjas: 0.90·Fy·Astr", aisc.rn_fluencia_traccion(pFy, A_str), "F")
    Ag1 = w1 * tp
    An1 = Ag1 - 2 * dhn * tp
    Rty1 = h.v("φRn", "Fluencia en tracción en la 1.ª fila: 0.90·Fy·w1·tp", aisc.rn_fluencia_traccion(pFy, Ag1), "F")
    Rtr1 = h.v("φRn", "Ruptura en tracción en la 1.ª fila: 0.75·Fu·min(An; 0.85Ag)", aisc.rn_ruptura_traccion(pFu, min(An1, 0.85 * Ag1)), "F")
    h.sec("3. PERNOS DE LAS ALAS (por lado)")
    r_v = aisc.rn_corte_perno(p["Fnv"], p["Ab"])
    Rsh = h.v("φRn", "Corte de los pernos: filas·nb·φ·Fnv·Ab", rows * nb * r_v, "F")
    lc_pe, lc_i = le - dh / 2, s - dh
    lc_fe = lef - dh / 2
    Rbp = h.v("φRn", "Aplastamiento en la placa (φ = 0.75)", rows * (aisc.rn_aplastamiento(p["db"], tp, pFu, lc_pe) +
              (nb - 1) * aisc.rn_aplastamiento(p["db"], tp, pFu, lc_i)), "F")
    Rbf = h.v("φRn", "Aplastamiento en el ala de la viga (φ = 0.75)", rows * (aisc.rn_aplastamiento(p["db"], btf, P["bFu"], lc_fe) +
              (nb - 1) * aisc.rn_aplastamiento(p["db"], btf, P["bFu"], lc_i)), "F")
    Lgv = le + (nb - 1) * s
    Agv = rows * Lgv * tp
    Rbs_p = h.v("φRn", "Bloque de cortante de la placa (φ = 0.75, Ubs = 1)", aisc.rn_bloque_corte(
        Agv, Agv - rows * (nb - 0.5) * dhn * tp, (g - dhn) * tp, pFy, pFu), "F")
    Lgv_f = lef + (nb - 1) * s
    Agv_f = rows * Lgv_f * btf
    Rbs_f = h.v("φRn", "Bloque de cortante del ala de la viga (φ = 0.75, Ubs = 1)", aisc.rn_bloque_corte(
        Agv_f, Agv_f - rows * (nb - 0.5) * dhn * btf, (bbf - g - dhn) * btf, P["bFy"], P["bFu"]), "F")
    L_pl = D + 2 * (d1 + (nb - 1) * s + le)
    h.v("Lplaca", "Longitud total de la placa: H + 2·(d1 + (nb − 1)·s + Le)", L_pl, "Lc")
    h.sec("4. TRANSFERENCIA AL HSS (criterio propio, no de la fuente)")
    Lw = 2 * (W + D)
    Rw = h.v("φRn", "Soldadura de la placa al perímetro del HSS: φ·0.6·FEXX·0.707·w·2(B + H) (θ = 0°, un cordón)", aisc.rn_filete(FEXX, w, Lw), "F")
    Rsy = h.v("φRn", "Corte de las 2 paredes del HSS paralelas a la viga (J4.2a): 1.0·0.6·Fy·2·t·H", aisc.rn_fluencia_corte(P["hFy"], 2 * t * D), "F")
    Rsr = h.v("φRn", "Ruptura por corte de las 2 paredes (J4.2b): 0.75·0.6·Fu·2·t·H", aisc.rn_ruptura_corte(P["hFu"], 2 * t * D), "F")
    h.chk(C.G_DET, "Franja junto al HSS no esbelta: ws/tp ≤ 0.45√(E/Fy)", "Tabla B4.1a", ws / tp, blim, "")
    h.chk(C.G_DET, "Paso s ≥ 3·db", "J3.3", 3 * p["db"], s, "Lc")
    h.chk(C.G_DET, "Gramil g ≥ 3·db", "J3.3", 3 * p["db"], g, "Lc")
    h.chk(C.G_DET, "Borde en la placa ≥ mínimo", "J3.4", p["edge"], le, "Lc")
    h.chk(C.G_DET, "Borde en el ala ≥ mínimo", "J3.4", p["edge"], lef, "Lc")
    h.chk(C.G_DET, "Borde transversal en el ala: (bf − g)/2 ≥ mínimo", "J3.4", p["edge"], (bbf - g) / 2, "Lc")
    h.chk(C.G_DET, "Borde transversal en la placa: (w1 − g)/2 ≥ mínimo", "J3.4", p["edge"], (w1 - g) / 2, "Lc")
    h.chk(C.G_DET, "Ala de la viga cabe en la placa: bf ≤ w1", "Geometría", bbf, w1, "Lc")
    gp = C.placa_corte_global(h, I, P)
    return {"derivados": C.derivados(P), "vars": {"bd": bd, "bbf": bbf, "btf": btf, "W": W, "D": D, "t": t, "tp": tp, "ws": ws, "w1": w1,
                                                    "d1": d1, "nb": nb, "s": s, "g": g, "le": le, "L": L_pl, "db": p["db"], "n": gp["n"], "tps": gp["tp"],
                                                    "a": d1, "lev": gp["lev"], "leh": gp["leh"], "w": gp["w"]},
            "g": dict(brazo=brazo, phiMp=phiMp, phiVn=phiVn, Rc=Rc, Rty=Rty, Rty1=Rty1, Rtr1=Rtr1, Rsh=Rsh, Rbp=Rbp, Rbf=Rbf, Rbs_p=Rbs_p,
                      Rbs_f=Rbs_f, Rw=Rw, Rsy=Rsy, Rsr=Rsr, gp=gp)}


def combo_fn(h, ctx, c, I):
    g = ctx["g"]
    M, V = abs(float(c.get("M") or 0)) * 1e5, abs(float(c.get("V") or 0)) * 1e3
    h.sec(f"COMBINACIÓN {c['nombre']}")
    R = h.v("Pr", "Fuerza en la placa: Mr/(d + tp)", M / g["brazo"], "F")
    h.chk(C.G_VIGA, "Flexión de la viga: Mu ≤ φMp", "F2", M, g["phiMp"], "M")
    h.chk(C.G_VIGA, "Cortante del alma de la viga", "G2.1", V, g["phiVn"], "F")
    h.chk(G_PL, "Compresión de las franjas junto al HSS", "E3", R, g["Rc"], "F")
    h.chk(G_PL, "Fluencia en tracción de las franjas junto al HSS", "D2(a)", R, g["Rty"], "F")
    h.chk(G_PL, "Fluencia en tracción en la primera fila de pernos", "D2(a)", R, g["Rty1"], "F")
    h.chk(G_PL, "Ruptura en tracción en la primera fila de pernos", "D2(b)", R, g["Rtr1"], "F")
    h.chk(G_PB, "Corte de los pernos", "J3.6", R, g["Rsh"], "F")
    h.chk(G_PB, "Aplastamiento en la placa", "J3.10", R, g["Rbp"], "F")
    h.chk(G_PB, "Aplastamiento en el ala de la viga", "J3.10", R, g["Rbf"], "F")
    h.chk(G_PB, "Bloque de cortante de la placa", "J4.3", R, g["Rbs_p"], "F")
    h.chk(G_PB, "Bloque de cortante del ala de la viga", "J4.3", R, g["Rbs_f"], "F")
    h.chk(G_TR, "Soldadura placa – perímetro del HSS", "J2.4", R, g["Rw"], "F")
    h.chk(G_TR, "Corte de las 2 paredes del HSS: fluencia", "J4.2(a)", R, g["Rsy"], "F")
    h.chk(G_TR, "Corte de las 2 paredes del HSS: ruptura", "J4.2(b)", R, g["Rsr"], "F")
    C.placa_corte_combo(h, g["gp"], V)


_MOD = Modulo(SPEC, global_fn, combo_fn)
calcular = _MOD.calcular
CAT = _MOD.CAT
