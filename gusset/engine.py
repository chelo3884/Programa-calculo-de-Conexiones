"""Cartela (gusset) para arriostramiento diagonal a viga y columna — Método de Fuerza Uniforme (UFM).

Manual AISC 15.ª ed. Parte 13 (UFM) y Parte 9 (Whitmore, bloque de cortante), AISC 360-16 J2/J3/J4/J10, E3:
  · la diagonal (placa o ángulos) se atornilla a la cartela (1 o 2 placas); las fuerzas en las interfaces
    cartela–viga y cartela–columna salen del UFM:  r = √((α + ec)² + (β + eb)²)
        Hb = (α/r)·P   Vb = (eb/r)·P   Hc = (ec/r)·P   Vc = (β/r)·P         (Hb + Hc = P·cosθ, Vb + Vc = P·senθ)
    α ideal (sin momento en la interfaz de la columna): α = (β̄ + eb)/tanθ − ec     (θ medido desde la horizontal)
    con α y β = b/2 (centro de la interfaz de la columna); si α ≠ a/2 se genera Mb = Vb·(α − a/2) en la viga.
  · cartela: bloque de cortante, ancho de Whitmore (fluencia/pandeo), pernos de la diagonal, soldaduras (elástico) y
    resistencias de viga (alma) y columna (ala/alma) bajo cargas concentradas.
No verifica la diagonal en sí (fluencia, ruptura con rezago de cortante, esbeltez) ni la conexión de la diagonal
a la placa en su lado; tampoco rigidizadores de la viga ni el efecto de la cartela sobre el eje débil de la columna.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import aisc  # noqa: E402
from handmod import (ARMADO, Modulo, campo, perfil, perfiles_columna, perfiles_viga, seccion, spec,  # noqa: E402
                     tabla_combos)

VIGAS, COLS = perfiles_viga(), perfiles_columna()
ACEROS = list(aisc.ACEROS)[:4]
IN, KIP = aisc.IN, aisc.KIP


def _perfil_campos(p, defecto, catalogo, defaults_e):
    return [campo(f"{p}_perfil", "Perfil (catálogo o ARMADO)", defecto, options=[ARMADO] + list(catalogo))] + [
        campo(f"{p}_E_{k}", f"{lab} (armado)", v, "mm", armado_de=f"{p}_perfil")
        for (k, lab), v in zip((("d", "Peralte d"), ("bf", "Ancho de ala bf"), ("tw", "Espesor de alma tw"),
                                ("tf", "Espesor de ala tf")), defaults_e)]


SPEC = spec(
    "CARTELA (GUSSET) DE ARRIOSTRAMIENTO — MÉTODO DE FUERZA UNIFORME",
    "AISC 360-16 (J2, J3, J4, J10, E3)  ·  AISC Manual 15ª ed. Partes 9 y 13  ·  LRFD  ·  Unidades: Tonf, Tonf·m, mm, kgf/cm²",
    [
        seccion("DATOS GENERALES", [campo("DIS_C7", "Proyecto", "Edificio — ejemplo"),
                                    campo("DIS_C8", "Elemento / nudo", "Arriostramiento eje A, nivel 2"),
                                    campo("lim_verde", "Límite verde / amarillo (ratio)", 0.9)]),
        seccion("1. VIGA", _perfil_campos("vg", "VK400X180X6X12", VIGAS, (400, 180, 6, 12)) +
                [campo("vg_acero", "Acero", "A572 Gr50", options=ACEROS),
                 campo("vg_kw", "Filete / radio alma–ala (para k)", 6, "mm")],
                [{"name": f"vg_{k}_mm", "label": lab, "unit": "mm"} for k, lab in (("d", "Peralte d"), ("bf", "Ancho de ala bf"), ("tw", "Espesor de alma tw"), ("tf", "Espesor de ala tf"))]),
        seccion("2. COLUMNA (cartela soldada al ala)", _perfil_campos("co", "HA500X250X10X15", COLS, (500, 250, 10, 15)) +
                [campo("co_acero", "Acero", "A572 Gr50", options=ACEROS),
                 campo("co_kw", "Filete / radio alma–ala (para k)", 6, "mm")],
                [{"name": f"co_{k}_mm", "label": lab, "unit": "mm"} for k, lab in (("d", "Peralte d"), ("bf", "Ancho de ala bf"), ("tw", "Espesor de alma tw"), ("tf", "Espesor de ala tf"))]),
        seccion("3. CARTELA", [
            campo("g_acero", "Acero de cartela", "A36", options=ACEROS),
            campo("g_np", "Número de placas (1 ó 2: diagonal entre placas)", 1, options=[1, 2]),
            campo("g_t", "Espesor de cada placa", 12, "mm"),
            campo("g_a", "Longitud a lo largo de la viga (a)", 500, "mm"),
            campo("g_b", "Longitud a lo largo de la columna (b)", 500, "mm"),
            campo("g_theta", "Ángulo de la diagonal respecto a la horizontal θ", 45, "°"),
            campo("sd_elec", "Electrodo", "E70XX", options=list(aisc.ELECTRODOS)),
            campo("g_wb", "Filete cartela–viga (c/lado)", 8, "mm"),
            campo("g_wc", "Filete cartela–columna (c/lado)", 8, "mm")]),
        seccion("4. DIAGONAL ATORNILLADA A LA CARTELA", [
            campo("pn_grado", "Grado de pernos", "A325-N (roscas incl.)", options=list(aisc.PERNOS)),
            campo("pn_diam", "Diámetro de pernos", '7/8"', options=aisc.DIAMETROS),
            campo("b_n", "Pernos por línea n", 4),
            campo("b_nl", "Líneas de pernos (paralelas a la fuerza)", 2, options=[1, 2, 3]),
            campo("b_s", "Paso s", 76.2, "mm"),
            campo("b_g", "Gramil entre líneas g", 100, "mm"),
            campo("b_le", "Distancia al borde (extremo de la cartela) Le", 38.1, "mm"),
            campo("b_tbr", "Espesor total de la diagonal en el apoyo (alas/placa)", 12, "mm"),
            campo("b_fu", "Fu de la diagonal", 4078, "kgf/cm²"),
            campo("g_K", "Factor K de pandeo de Whitmore", 0.65),
            campo("g_Lc", "Longitud de pandeo Lc (último perno → borde soldado)", 200, "mm")]),
    ],
    combos=tabla_combos([("nombre", "Combinación"), ("P", "P diagonal (Tonf, + tracción / − compresión)")],
                        [{"nombre": "Tracción", "P": 30}, {"nombre": "Compresión", "P": -25}]),
    notas=["UFM: Hb = α/r·P · Vb = eb/r·P · Hc = ec/r·P · Vc = β/r·P; con α = (β̄ + eb)/tanθ − ec (θ desde la horizontal) no hay momento en la interfaz de la columna.",
           "Las soldaduras se verifican con el método elástico por longitud (sin el aumento direccional del 1 + 0.5·sen^1.5θ): conservador.",
           "Si la cartela está bastante fuera de la geometría ideal (α ≠ a/2) aparece el momento Mb en la interfaz de la viga.",
           "No incluye la verificación de la diagonal ni la unión diagonal–cartela en el otro extremo; compruébelas aparte."])


def _tmin_w(t_mm):
    return 3 if t_mm <= 6 else 5 if t_mm <= 13 else 6 if t_mm <= 19 else 8


def ufm(P, theta_deg, eb, ec, a, b):
    """Fuerzas UFM (misma unidad que P): dict(alpha, beta, r, Hb, Vb, Hc, Vc, Mb, Mc)."""
    th = math.radians(theta_deg)
    beta = b / 2
    alpha = (beta + eb) / math.tan(th) - ec
    r = math.hypot(alpha + ec, beta + eb)
    Hb, Vb, Hc, Vc = alpha / r * P, eb / r * P, ec / r * P, beta / r * P
    return dict(alpha=alpha, beta=beta, r=r, Hb=Hb, Vb=Vb, Hc=Hc, Vc=Vc, Mb=Vb * (alpha - a / 2), Mc=0.0)


def global_fn(h, I):
    bd, bbf, btw, btf = perfil(I["vg_perfil"], I, "vg", VIGAS)
    cd, cbf, ctw, ctf = perfil(I["co_perfil"], I, "co", COLS)
    bFy, bFu = aisc.ACEROS[I["vg_acero"]]
    cFy, cFu = aisc.ACEROS[I["co_acero"]]
    gFy, gFu = aisc.ACEROS[I["g_acero"]]
    FEXX = aisc.ELECTRODOS[I["sd_elec"]]
    p = aisc.perno(I["pn_diam"], I["pn_grado"])
    npl, t = int(I["g_np"]), I["g_t"] / 10
    a, b, th = I["g_a"] / 10, I["g_b"] / 10, float(I["g_theta"])
    n, nl, s, g, le = int(I["b_n"]), int(I["b_nl"]), I["b_s"] / 10, I["b_g"] / 10, I["b_le"] / 10
    tbr, bFu_br = I["b_tbr"] / 10, float(I["b_fu"])
    wb, wc = I["g_wb"] / 10, I["g_wc"] / 10
    kb, kc = btf + I["vg_kw"] / 10, ctf + I["co_kw"] / 10
    eb, ec = bd / 2, cd / 2

    h.sec("1. GEOMETRÍA UFM")
    h.v("eb", "Mitad del peralte de la viga", eb, "Lc")
    h.v("ec", "Mitad del peralte de la columna", ec, "Lc")
    beta = h.v("β̄", "Centro de la interfaz de la columna: b/2", b / 2, "Lc")
    alpha_i = h.v("α ideal", "(β̄ + eb)/tanθ − ec", (beta + eb) / math.tan(math.radians(th)) - ec, "Lc")
    h.v("a/2", "Centro de la interfaz de la viga", a / 2, "Lc")

    h.sec("2. DIAGONAL ATORNILLADA A LA CARTELA")
    Lcon = (n - 1) * s
    lw = h.v("lw", "Ancho de Whitmore: (nl − 1)·g + 2·Lcon·tan30°", aisc.ancho_whitmore((nl - 1) * g, Lcon), "Lc")
    Aw = lw * t * npl
    Rwy = h.v("φRn", "Whitmore, fluencia en tracción (J4.1): 0.90·Fy·lw·t·np", aisc.rn_fluencia_traccion(gFy, Aw), "F")
    rg = t / math.sqrt(12)
    KLr = float(I["g_K"]) * I["g_Lc"] / 10 / rg
    Fe = math.pi ** 2 * aisc.E / KLr ** 2
    Fcr = 0.658 ** (gFy / Fe) * gFy if KLr <= 4.71 * math.sqrt(aisc.E / gFy) else 0.877 * Fe
    h.v("KL/r", "Esbeltez de Whitmore: K·Lc / (t/√12)", KLr, "")
    Rwc = h.v("φRn", "Whitmore, compresión (E3): 0.90·Fcr·lw·t·np", 0.90 * Fcr * Aw, "F")
    Agv = 2 * (le + Lcon) * t * npl
    Anv = Agv - 2 * (n - 0.5) * p["dh_net"] * t * npl
    Ant = max(((nl - 1) * g - (nl - 1) * p["dh_net"]) * t * npl, 0.0)
    Rbs = h.v("φRn", "Bloque de cortante de la cartela (J4.3)", aisc.rn_bloque_corte(Agv, Anv, Ant, gFy, gFu), "F") if nl > 1 else None
    r_v = aisc.rn_corte_perno(p["Fnv"], p["Ab"], ns=npl)
    lc_e, lc_i = le - p["dh"] / 2, s - p["dh"]
    t_gus = t * npl                                     # aplastamiento: placas de cartela vs diagonal
    per_e = min(r_v, aisc.rn_aplastamiento(p["db"], t_gus, gFu, lc_e), aisc.rn_aplastamiento(p["db"], tbr, bFu_br, lc_e))
    per_i = min(r_v, aisc.rn_aplastamiento(p["db"], t_gus, gFu, lc_i), aisc.rn_aplastamiento(p["db"], tbr, bFu_br, lc_i))
    Rbolts = h.v("φRn", "Grupo de pernos: nl·[1 de borde + (n − 1) interiores]: mín(corte; aplast.; desgarre)",
                 nl * (per_e + (n - 1) * per_i), "F")

    h.sec("3. INTERFACES (resistencias por longitud y por carga concentrada)")
    VnY_b = aisc.rn_fluencia_corte(gFy, a * t * npl)
    VnY_c = aisc.rn_fluencia_corte(gFy, b * t * npl)
    NnY_b = aisc.rn_fluencia_traccion(gFy, a * t * npl)
    NnY_c = aisc.rn_fluencia_traccion(gFy, b * t * npl)
    MnP_b = 0.90 * gFy * npl * t * a ** 2 / 4
    wcap_b = aisc.rn_filete(FEXX, wb, 1.0)          # φ·0.6·FEXX·0.707·w por cm de línea
    wcap_c = aisc.rn_filete(FEXX, wc, 1.0)
    Rv_wb = h.v("φRn", "Alma de la viga, fluencia local (J10-2) con N = a", aisc.rn_fluencia_local_alma(bFy, btw, kb, a, True), "F")
    Rv_cr = h.v("φRn", "Alma de la viga, aplastamiento (J10-4) con N = a", aisc.rn_aplastamiento_alma(bFy, btw, btf, bd, a, True), "F")
    Rc_fb = h.v("φRn", "Ala de la columna, flexión local (J10-1)", aisc.rn_flexion_local_ala(cFy, ctf), "F")
    Rc_wy = h.v("φRn", "Alma de la columna, fluencia local (J10-2) con N = b", aisc.rn_fluencia_local_alma(cFy, ctw, kc, b, True), "F")
    Rc_cr = h.v("φRn", "Alma de la columna, aplastamiento (J10-4) con N = b", aisc.rn_aplastamiento_alma(cFy, ctw, ctf, cd, b, True), "F")

    G1, G2, G3, G4 = "DIAGONAL → CARTELA", "INTERFAZ CARTELA–VIGA", "INTERFAZ CARTELA–COLUMNA", "DETALLES (requerido / provisto)"
    tg_req = lambda w: aisc.t_min_soporte(FEXX, gFu, w, 2)       # 3.09·D/Fu: cartela soldada por ambos lados
    h.chk(G4, "Espesor de cartela ≥ 3.09·D/Fu (soldada por ambos lados) (filete a la viga)", "Manual Parte 9 · Ec. 9-2", tg_req(wb), t, "Lc")
    h.chk(G4, "Espesor de cartela ≥ 3.09·D/Fu (soldada por ambos lados) (filete a la columna)", "Manual Parte 9 · Ec. 9-2", tg_req(wc), t, "Lc")
    h.chk(G4, "Filete a la viga ≥ mínimo J2.4", "Tabla J2.4", _tmin_w(min(t, btf) * 10) / 10, wb, "Lc")
    h.chk(G4, "Filete a la columna ≥ mínimo J2.4", "Tabla J2.4", _tmin_w(min(t, ctf) * 10) / 10, wc, "Lc")
    h.chk(G4, "Paso s ≥ 3·db", "J3.3", 3 * p["db"], s, "Lc")
    h.chk(G4, "Distancia al borde Le ≥ mínimo", "J3.4", p["edge"], le, "Lc")
    h.chk(G4, "Gramil g ≥ 3·db", "J3.3", 3 * p["db"], g, "Lc", activo=nl > 1)
    h.chk(G4, "Ancho de Whitmore ≤ gramil visible: lw ≤ a", "Geometría", lw, a, "Lc")
    h.chk(G4, "Cartela: a/b entre 0.5 y 2 (compacta)", "Buena práctica", max(0.5 * b / a, a / (2 * b)), 1.0, "", ratio=max(0.5 * b / a, a / (2 * b)))
    ctx = {"derivados": {"vg_d_mm": bd * 10, "vg_bf_mm": bbf * 10, "vg_tw_mm": btw * 10, "vg_tf_mm": btf * 10,
                         "co_d_mm": cd * 10, "co_bf_mm": cbf * 10, "co_tw_mm": ctw * 10, "co_tf_mm": ctf * 10},
           "vars": {"bd": bd, "bbf": bbf, "btw": btw, "btf": btf, "cd": cd, "cbf": cbf, "ctw": ctw, "ctf": ctf,
                    "a": a, "b": b, "th": th, "t": t, "npl": npl, "n": n, "nl": nl, "s": s, "g": g, "le": le,
                    "db": p["db"], "lw": lw, "alpha": alpha_i, "eb": eb, "ec": ec},
           "g": dict(eb=eb, ec=ec, a=a, b=b, th=th, Rwy=Rwy, Rwc=Rwc, Rbs=Rbs, Rbolts=Rbolts, VnY_b=VnY_b, VnY_c=VnY_c,
                     NnY_b=NnY_b, NnY_c=NnY_c, MnP_b=MnP_b, wcap_b=wcap_b, wcap_c=wcap_c, Rv_wb=Rv_wb, Rv_cr=Rv_cr,
                     Rc_fb=Rc_fb, Rc_wy=Rc_wy, Rc_cr=Rc_cr, npl=npl)}
    return ctx


def combo_fn(h, ctx, c, I):
    g = ctx["g"]
    P = float(c.get("P") or 0) * 1e3
    tens = P >= 0
    Pa = abs(P)
    u = ufm(Pa, g["th"], g["eb"], g["ec"], g["a"], g["b"])
    h.sec(f"COMBINACIÓN {c['nombre']}")
    h.v("P", "Fuerza axial de la diagonal (+ tracción)", P, "F")
    h.v("α", "α usada (ideal)", u["alpha"], "Lc")
    h.v("r", "√((α + ec)² + (β + eb)²)", u["r"], "Lc")
    for k, d in (("Hb", "Cortante en la interfaz de la viga (horizontal)"), ("Vb", "Normal en la interfaz de la viga (vertical)"),
                 ("Hc", "Normal en la interfaz de la columna (horizontal)"), ("Vc", "Cortante en la interfaz de la columna (vertical)")):
        h.v(k, d, u[k], "F")
    Mb = h.v("Mb", "Momento en la interfaz de la viga: Vb·(α − a/2)", u["Mb"], "M")
    G1, G2, G3 = "DIAGONAL → CARTELA", "INTERFAZ CARTELA–VIGA", "INTERFAZ CARTELA–COLUMNA"
    h.chk(G1, "Pernos de la diagonal (grupo)", "J3.6 · J3.10", Pa, g["Rbolts"], "F")
    h.chk(G1, "Whitmore: fluencia en tracción", "J4.1", Pa, g["Rwy"], "F", activo=tens)
    h.chk(G1, "Whitmore: pandeo en compresión", "E3", Pa, g["Rwc"], "F", activo=not tens)
    h.chk(G1, "Bloque de cortante de la cartela", "J4.3", Pa, g["Rbs"] or 1.0, "F", activo=tens and g["Rbs"] is not None)
    # interfaz con la viga
    a, b = g["a"], g["b"]
    h.chk(G2, "Cartela: corte horizontal Hb", "J4.2(a)", abs(u["Hb"]), g["VnY_b"], "F")
    ri = abs(u["Vb"]) / g["NnY_b"] + abs(Mb) / g["MnP_b"]
    h.chk(G2, "Cartela: normal Vb + momento Mb (interacción)", "H1", ri, 1.0, "", ratio=ri)
    fb = math.hypot(abs(u["Hb"]) / (2 * a), abs(u["Vb"]) / (2 * a) + 3 * abs(Mb) / a ** 2)
    h.chk(G2, "Soldadura cartela–viga (elástica, por cm)", "J2.4", fb, g["wcap_b"], "FL")
    h.chk(G2, "Alma de la viga: fluencia local", "J10.2", abs(u["Vb"]), g["Rv_wb"], "F")
    h.chk(G2, "Alma de la viga: aplastamiento", "J10.3", abs(u["Vb"]), g["Rv_cr"], "F")
    # interfaz con la columna
    h.chk(G3, "Cartela: corte vertical Vc", "J4.2(a)", abs(u["Vc"]), g["VnY_c"], "F")
    h.chk(G3, "Cartela: normal Hc", "J4.1", abs(u["Hc"]), g["NnY_c"], "F")
    fc = math.hypot(abs(u["Vc"]) / (2 * b), abs(u["Hc"]) / (2 * b))
    h.chk(G3, "Soldadura cartela–columna (elástica, por cm)", "J2.4", fc, g["wcap_c"], "FL")
    h.chk(G3, "Ala de la columna: flexión local (Hc en tracción)", "J10.1", abs(u["Hc"]), g["Rc_fb"], "F", activo=tens)
    h.chk(G3, "Alma de la columna: fluencia local (Hc en compresión)", "J10.2", abs(u["Hc"]), g["Rc_wy"], "F", activo=not tens)
    h.chk(G3, "Alma de la columna: aplastamiento (Hc en compresión)", "J10.3", abs(u["Hc"]), g["Rc_cr"], "F", activo=not tens)


_MOD = Modulo(SPEC, global_fn, combo_fn)
calcular = _MOD.calcular
CAT = _MOD.CAT
