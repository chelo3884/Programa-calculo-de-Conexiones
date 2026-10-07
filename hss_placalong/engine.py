"""Unión de arriostramiento a columna RHS mediante PLACA LONGITUDINAL (simple o pasante) — CIDECT Design Guide 9, §10.1.1–10.1.2, ecs. 10.1 y 10.2.

Resistencia mayorada de la cara de la RHS (mecanismo de líneas de plastificación), con coeficiente de resistencia implícito 1.0:
    Np* = 2·fc,y·tc² / ((1 − β')·senθ) · ( hp'/bc' + 2·√(1 − β')·√(1 − n²) )
    β' = (bp + 2w)/bc',  bc' = bc − tc,  hp' = hp/senθ + 2w,  n = σc/fc,y (compresión negativa; lado menos desfavorable)
    bp = ESPESOR de la placa, hp = ancho de la placa (perpendicular a la carga), θ = ángulo entre la placa (carga) y el eje de la columna
Servicio (deformación del 1 % de bc): Np,s1% = Np*/(1.5 − 0.9β') clase 1 · /(2.0 − 1.25β') clase 2 · /(2.7 − 2β') clase 3.  Aplicable a bc/tc ≤ 40.
Placa pasante: el doble de Np* y de Np,s1% (§10.1.2).
Verificado con el ejemplo 10.1.1.1 de la guía: RHS 178×178×6.4 (fy 350 MPa), placa 200×10, w = 6, θ = 53.1°, N' = 500 kN → Np* = 133 kN y Np,s1% = 72 kN.
Además se verifican con AISC 360-16 (la guía usa CSA): fluencia y ruptura de la placa, pernos (corte, aplastamiento) y soldadura (2 cordones de longitud hp/senθ).
Límites: no verifica el arriostramiento en sí ni su unión en el otro extremo; el efecto de la excentricidad no se considera.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import aisc  # noqa: E402
import hss_comun as C  # noqa: E402
from handmod import Modulo, campo, seccion, spec, tabla_combos  # noqa: E402

G_C, G_P, G_B, G_W = "CARA DE LA COLUMNA RHS (CIDECT 9 ec. 10.1)", "PLACA LONGITUDINAL", "PERNOS DE LA DIAGONAL", "SOLDADURA PLACA – COLUMNA"
SPEC = spec(
    "ARRIOSTRAMIENTO A COLUMNA RHS CON PLACA LONGITUDINAL (SIMPLE O PASANTE)",
    "CIDECT Design Guide 9 (§10.1.1–10.1.2, ecs. 10.1–10.2)  ·  AISC 360-16 J2, J3, J4  ·  Unidades: Tonf, Tonf·m, mm, kgf/cm²",
    [
        seccion("DATOS GENERALES", [campo("DIS_C7", "Proyecto", "Edificio — ejemplo"), campo("DIS_C8", "Elemento / nudo", "Arriostramiento eje A, nivel 1"),
                                    campo("lim_verde", "Límite verde / amarillo (ratio)", 0.9)]),
        seccion("1. COLUMNA RHS", C.campos_hss(defecto="ARMADO (flejes soldados)", dims=(178, 178, 6.35)) + [
            campo("hss_Ao", "Área de la columna (0 = calcular aprox.)", 0, "mm²"), campo("clase", "Clase de la sección para servicio (1, 2 ó 3)", 2, options=[1, 2, 3])],
                C.derivados_hss()),
        seccion("2. PLACA LONGITUDINAL", [
            campo("pl_tipo", "Tipo", "Simple", options=["Simple", "Pasante (ranurada, ×2)"]),
            campo("pl_acero", "Acero de la placa", "A36", options=C.ACEROS_VIGA),
            campo("pl_tp", "Espesor de la placa bp", 10, "mm"), campo("pl_hp", "Ancho de la placa hp (perpendicular a la carga)", 200, "mm"),
            campo("pl_theta", "Ángulo θ entre la placa (carga) y el eje de la columna", 53.1, "°"),
            campo("pl_w", "Filete placa – columna (c/lado)", 6, "mm"), campo("sd_elec", "Electrodo", "E70XX", options=list(aisc.ELECTRODOS)),
            campo("pl_L", "Longitud libre de la placa a compresión (última fila → soldadura)", 100, "mm")]),
        seccion("3. PERNOS DE LA DIAGONAL (en línea con la carga)", [
            campo("pn_grado", "Grado de pernos", "A325-X (roscas excl.)", options=list(aisc.PERNOS)),
            campo("pn_diam", "Diámetro de pernos", '7/8"', options=aisc.DIAMETROS),
            campo("pn_n", "Número de pernos", 2), campo("pn_ns", "Planos de corte por perno", 2, options=[1, 2]),
            campo("pn_s", "Paso", 70, "mm"), campo("pn_le", "Borde en la dirección de la carga (placa)", 40, "mm")]),
    ],
    combos=tabla_combos([("nombre", "Combinación"), ("N", "N diagonal mayorada (Tonf, + tracción / − compresión)"), ("Ns", "N diagonal de servicio (Tonf)"),
                         ("P", "Pu columna (Tonf) (+) compresión"), ("M", "Mu columna (Tonf·m)")],
                        [{"nombre": "Tracción", "N": 3.0, "Ns": 2.0, "P": 8, "M": 0.3}, {"nombre": "Compresión", "N": -2.5, "Ns": -1.7, "P": 8, "M": 0.3}]),
    notas=["La guía advierte que esta unión solo es adecuada para arriostramientos poco cargados: la cara de la RHS es flexible. Alternativas: placa transversal, pasante o rigidizada.",
           "Ec. 10.1 con φ implícito = 1.0 (la unión se controla por deformación). Debe comprobarse además la carga de servicio (ec. 10.2).",
           "n = σc/fc,y en el lado menos desfavorable de la cara de unión (compresión negativa), con el área de la columna aproximada sin radios si no se indica.",
           "Los estados límite de placa, pernos y soldadura usan AISC 360-16 (la guía usa CSA); no hay que sumarles el efecto de la ec. 10.1."])


def global_fn(h, I):
    I = dict(I)
    hFy = aisc.ACEROS[I["hss_acero"]][0]
    bc, hc_, tc = (lambda W, D, t: (W, D, t))(*C.geom_hss(I))
    pFy, pFu = aisc.ACEROS[I["pl_acero"]]
    FEXX = aisc.ELECTRODOS[I["sd_elec"]]
    p = aisc.perno(I["pn_diam"], I["pn_grado"])
    bp, hp, th, w = I["pl_tp"] / 10, I["pl_hp"] / 10, float(I["pl_theta"]), I["pl_w"] / 10
    nb, ns, s, le = int(I["pn_n"]), int(I["pn_ns"]), I["pn_s"] / 10, I["pn_le"] / 10
    mult = 2 if I["pl_tipo"].startswith("Pasante") else 1
    A, S = aisc.hss_props(bc, hc_, tc)
    if float(I.get("hss_Ao") or 0) > 0:
        A = float(I["hss_Ao"]) / 100
    sn = math.sin(math.radians(th))
    h.sec("1. CARA DE LA RHS (ec. 10.1 y 10.2)")
    bcp = bc - tc
    bet = (bp + 2 * w) / bcp
    h.v("β'", "(bp + 2w)/(bc − tc)", bet, "")
    h.v("hp'", "hp/senθ + 2w", hp / sn + 2 * w, "Lc")
    h.v("bc/tc", "Esbeltez de la pared (límite 40)", bc / tc, "")
    h.v("A", "Área de la columna", A, "A")
    L = hp / sn                                                    # longitud de contacto por cordón
    ctx_g = dict(bc=bc, tc=tc, hFy=hFy, bp=bp, hp=hp, th=th, w=w, A=A, S=S, mult=mult, bet=bet, clase=int(I["clase"]))
    h.sec("2. PLACA")
    Ag = hp * bp
    Rty = h.v("φRn", "Fluencia de la placa: 0.90·Fy·hp·bp (J4.1a)", aisc.rn_fluencia_traccion(pFy, Ag), "F")
    An = (hp - p["dh_net"]) * bp
    Rtr = h.v("φRn", "Ruptura de la placa: 0.75·Fu·mín(An; 0.85Ag), 1 agujero (J4.1b)", aisc.rn_ruptura_traccion(pFu, min(An, 0.85 * Ag)), "F")
    KLr = 1.0 * I["pl_L"] / 10 / (bp / math.sqrt(12))
    Rcp = h.v("φRn", "Compresión de la placa (J4.4), K = 1", aisc.rn_compresion_placa(pFy, Ag, KLr), "F")
    h.sec("3. PERNOS")
    r_v = aisc.rn_corte_perno(p["Fnv"], p["Ab"], ns=ns)
    Rsh = h.v("φRn", "Corte de los pernos: n·φ·Fnv·Ab·ns", nb * r_v, "F")
    lc_e, lc_i = le - p["dh"] / 2, s - p["dh"]
    Rbr = h.v("φRn", "Aplastamiento en la placa: 1 de borde + (n − 1) interiores (J3.10)", aisc.rn_aplastamiento(p["db"], bp, pFu, lc_e) +
              (nb - 1) * aisc.rn_aplastamiento(p["db"], bp, pFu, lc_i), "F")
    h.sec("4. SOLDADURA")
    Rw = h.v("φRn", "Filetes: 2·hp/senθ·φ·0.6·FEXX·0.707·w (sin el aumento por dirección: conservador)" + (" ×2 (pasante)" if mult == 2 else ""),
             mult * 2 * aisc.rn_filete(FEXX, w, L), "F")
    h.chk(C.G_DET, "Límite: bc/tc ≤ 40", "CIDECT 9 §10.1.1 nota (a)", bc / tc, 40, "")
    h.chk(C.G_DET, "Límite: β' < 1", "Ec. 10.1", bet, 1.0, "")
    h.chk(C.G_DET, "Paso ≥ 3·db", "J3.3", 3 * p["db"], s, "Lc", activo=nb > 1)
    h.chk(C.G_DET, "Borde ≥ mínimo", "J3.4", p["edge"], le, "Lc")
    h.chk(C.G_DET, "Filete ≥ mínimo J2.4 para la placa", "Tabla J2.4",
          (3 if bp * 10 <= 6 else 5 if bp * 10 <= 13 else 6 if bp * 10 <= 19 else 8) / 10, w, "Lc")
    ctx = {"derivados": {"hss_W_mm": bc * 10, "hss_D_mm": hc_ * 10, "hss_t_mm": tc * 10, "hss_bt": bc / tc,
                         "vg_d_mm": 0, "vg_bf_mm": 0, "vg_tw_mm": 0, "vg_tf_mm": 0},
           "vars": {"bc": bc, "hc": hc_, "tc": tc, "bp": bp, "hp": hp, "th": th, "w": w, "nb": nb, "s": s, "le": le, "db": p["db"], "mult": mult},
           "g": dict(ctx_g, Rty=Rty, Rtr=Rtr, Rcp=Rcp, Rsh=Rsh, Rbr=Rbr, Rw=Rw)}
    return ctx


def combo_fn(h, ctx, c, I):
    g = ctx["g"]
    N = float(c.get("N") or 0) * 1e3
    Ns = abs(float(c.get("Ns") or 0)) * 1e3
    Pc, Mc = float(c.get("P") or 0) * 1e3, abs(float(c.get("M") or 0)) * 1e5
    h.sec(f"COMBINACIÓN {c['nombre']}")
    fy = g["hFy"]
    # n = σc/fy: compresión negativa; se toma el lado menos desfavorable (menor |n|)
    n_ax = -Pc / (g["A"] * fy)
    n_fl = Mc / (g["S"] * fy)
    n = min((n_ax + n_fl, n_ax - n_fl), key=abs)
    h.v("n", "σc/fc,y en el lado menos desfavorable (compresión negativa)", n, "")
    Np = g["mult"] * aisc.cidect_placa_long_Np(fy, g["tc"], g["bc"], g["bp"], g["hp"], g["th"], g["w"], n)
    h.v("Np*", "Resistencia mayorada de la cara de la RHS (ec. 10.1)" + (" ×2 (pasante)" if g["mult"] == 2 else ""), Np, "F")
    Nps = g["mult"] * aisc.cidect_placa_long_servicio(Np / g["mult"], g["bet"], g["clase"])
    h.v("Np,s1%", "Carga de servicio límite (ec. 10.2)", Nps, "F")
    Na = abs(N)
    h.chk(G_C, "Resistencia mayorada de la cara de la RHS: N ≤ Np*", "CIDECT 9 ec. 10.1", Na, Np, "F")
    h.chk(G_C, "Servicio: Ns ≤ Np,s1%", "CIDECT 9 ec. 10.2", Ns, Nps, "F", activo=Ns > 0)
    h.chk(G_P, "Fluencia de la placa (tracción)", "J4.1(a)", Na, g["Rty"], "F", activo=N >= 0)
    h.chk(G_P, "Ruptura de la placa (tracción)", "J4.1(b)", Na, g["Rtr"], "F", activo=N >= 0)
    h.chk(G_P, "Compresión de la placa", "J4.4", Na, g["Rcp"], "F", activo=N < 0)
    h.chk(G_B, "Corte de los pernos", "J3.6", Na, g["Rsh"], "F")
    h.chk(G_B, "Aplastamiento en la placa", "J3.10", Na, g["Rbr"], "F")
    h.chk(G_W, "Soldadura placa – cara de la columna", "J2.4", Na, g["Rw"], "F")


_MOD = Modulo(SPEC, global_fn, combo_fn)
calcular = _MOD.calcular
CAT = _MOD.CAT
