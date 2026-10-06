"""Piezas comunes de las conexiones de momento viga W – columna HSS rectangular (hss_directa, hss_pasante).

Referencia: AISC Design Guide 24 (2010), cap. 4 y 7 (Tabla 7-2, Ej. 4.2 y 4.3), AISC 360-16 cap. K y J, Manual Parte 10.
La guía y el ejemplo son para cargas NO sísmicas.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aisc  # noqa: E402
from handmod import ARMADO, campo, perfil, perfiles_viga  # noqa: E402
from placa_base.engine import CATALOGOS  # noqa: E402

VIGAS = perfiles_viga()
HSS = {p["nombre"]: p for p in CATALOGOS["hss"]}
ACEROS_VIGA = list(aisc.ACEROS)[:4]
ACEROS_HSS = ["A500 Gr B", "A500 Gr C"]
SI_NO = ["Sí", "No"]
IN, KIP = aisc.IN, aisc.KIP
G_VIGA, G_HSS, G_PL, G_DET = "VIGA", "COLUMNA HSS", "PLACA DE CORTE", "DETALLES (requerido / provisto)"
DIM = [("d", "Peralte d"), ("bf", "Ancho de ala bf"), ("tw", "Espesor de alma tw"), ("tf", "Espesor de ala tf")]


def campos_viga(defecto="W16X40", dims=(400, 180, 6, 12)):
    return ([campo("vg_perfil", "Perfil (catálogo o ARMADO)", defecto, options=[ARMADO] + list(VIGAS))] +
            [campo(f"vg_E_{k}", f"{lab} (armado)", v, "mm", armado_de="vg_perfil") for (k, lab), v in zip(DIM, dims)] +
            [campo("vg_acero", "Acero", "A992", options=ACEROS_VIGA)])


def derivados_viga():
    return [{"name": f"vg_{k}_mm", "label": lab, "unit": "mm"} for k, lab in DIM]


def campos_hss(defecto="HSS10X10X1/2", dims=(254, 254, 11.81)):
    return [campo("hss_perfil", "Perfil HSS (catálogo o ARMADO)", defecto, options=[ARMADO] + list(HSS)),
            campo("hss_cara", "Cara de la conexión (catálogo): dimensión H o B", "B", options=["B", "H"]),
            campo("hss_W", "Ancho de la cara de conexión B (armado)", dims[0], "mm", armado_de="hss_perfil"),
            campo("hss_D", "Profundidad H en la dirección de la viga (armado)", dims[1], "mm", armado_de="hss_perfil"),
            campo("hss_t", "Espesor de DISEÑO t (armado; 0.93·tnom si es soldado)", dims[2], "mm", armado_de="hss_perfil"),
            campo("hss_acero", "Acero", "A500 Gr B", options=ACEROS_HSS)]


def derivados_hss():
    return [{"name": "hss_W_mm", "label": "Ancho de la cara B", "unit": "mm"}, {"name": "hss_D_mm", "label": "Profundidad H", "unit": "mm"},
            {"name": "hss_t_mm", "label": "Espesor de diseño t", "unit": "mm"}, {"name": "hss_bt", "label": "B/t", "unit": ""}]


def geom_hss(I):
    """(W, D, t) en cm: ancho de la cara de conexión, profundidad y espesor de diseño."""
    if I["hss_perfil"] == ARMADO:
        return float(I["hss_W"]) / 10, float(I["hss_D"]) / 10, float(I["hss_t"]) / 10
    h = HSS[I["hss_perfil"]]
    W, D = (h["B"], h["H"]) if I.get("hss_cara", "B") == "B" else (h["H"], h["B"])
    return W / 10, D / 10, h["t"] / 10


def campos_placa_corte(n=3, s=76.2, lev=38.1, leh=50.8, tp=9.5, a=76.2, w=6.35):
    return [campo("sp_acero", "Acero de placa de corte", "A36", options=ACEROS_VIGA),
            campo("sp_t", "Espesor tp", tp, "mm"), campo("sp_n", "Número de pernos n (1 línea vertical)", n),
            campo("sp_s", "Paso vertical s", s, "mm"), campo("sp_lev", "Borde vertical Lev", lev, "mm"),
            campo("sp_leh", "Borde horizontal Leh en la placa", leh, "mm"),
            campo("sp_a", "a — soldadura a línea de pernos (excentricidad)", a, "mm"),
            campo("sp_w", "Filete placa – pared del HSS (c/lado)", w, "mm"),
            campo("pn_grado", "Grado de pernos", "A325-N (roscas incl.)", options=list(aisc.PERNOS)),
            campo("pn_diam", "Diámetro de pernos", '3/4"', options=aisc.DIAMETROS),
            campo("sd_elec", "Electrodo", "E70XX", options=list(aisc.ELECTRODOS))]


def hss_y_viga(I):
    """Propiedades comunes en cm / kgf/cm²."""
    bd, bbf, btw, btf = perfil(I["vg_perfil"], I, "vg", VIGAS)
    W, D, t = geom_hss(I)
    hFy, hFu = aisc.ACEROS[I["hss_acero"]]
    bFy, bFu = aisc.ACEROS[I["vg_acero"]]
    return dict(bd=bd, bbf=bbf, btw=btw, btf=btf, W=W, D=D, t=t, hFy=hFy, hFu=hFu, bFy=bFy, bFu=bFu)


def derivados(P):
    return {"vg_d_mm": P["bd"] * 10, "vg_bf_mm": P["bbf"] * 10, "vg_tw_mm": P["btw"] * 10, "vg_tf_mm": P["btf"] * 10,
            "hss_W_mm": P["W"] * 10, "hss_D_mm": P["D"] * 10, "hss_t_mm": P["t"] * 10, "hss_bt": P["W"] / P["t"]}


def placa_corte_global(h, I, P):
    """Registra las resistencias de la placa de corte (soldada a la pared del HSS, atornillada al alma). Devuelve dict."""
    pFy, pFu = aisc.ACEROS[I["sp_acero"]]
    FEXX = aisc.ELECTRODOS[I["sd_elec"]]
    p = aisc.perno(I["pn_diam"], I["pn_grado"])
    n = int(I["sp_n"])
    s, lev, leh, tp, w, a = I["sp_s"] / 10, I["sp_lev"] / 10, I["sp_leh"] / 10, I["sp_t"] / 10, I["sp_w"] / 10, I["sp_a"] / 10
    L = 2 * lev + (n - 1) * s
    dh, dhn = p["dh"], p["dh_net"]
    h.sec("PLACA DE CORTE (Manual Parte 10 / DG24 Ej. 4.2)")
    r_v = aisc.rn_corte_perno(p["Fnv"], p["Ab"])
    lc_e, lc_i = lev - dh / 2, s - dh
    r_pe = min(r_v, aisc.rn_aplastamiento(p["db"], tp, pFu, lc_e))
    r_pi = min(r_v, aisc.rn_aplastamiento(p["db"], tp, pFu, lc_i))
    r_wi = min(r_v, aisc.rn_aplastamiento(p["db"], P["btw"], P["bFu"], lc_i))
    g = {"L": L, "n": n, "s": s, "lev": lev, "leh": leh, "tp": tp, "w": w, "a": a, "p": p, "pFu": pFu, "FEXX": FEXX}
    g["Rb_pl"] = h.v("φRn", "Pernos en la placa: 1 de borde + (n − 1) interiores", r_pe + (n - 1) * r_pi, "F")
    g["Rb_wb"] = h.v("φRn", "Pernos en el alma de la viga: n·mín(corte; aplast.; desgarre)", n * r_wi, "F")
    g["Rpl_y"] = h.v("φRn", "Placa, fluencia por corte (J4.2a)", aisc.rn_fluencia_corte(pFy, L * tp), "F")
    g["Rpl_r"] = h.v("φRn", "Placa, ruptura por corte (J4.2b)", aisc.rn_ruptura_corte(pFu, (L - n * dhn) * tp), "F")
    Agv = ((n - 1) * s + lev) * tp
    Anv = Agv - (n - 0.5) * dhn * tp
    Ant = (leh - 0.5 * dhn) * tp
    g["Rpl_b"] = h.v("φRn", "Placa, bloque de cortante (J4.3)", aisc.rn_bloque_corte(Agv, Anv, Ant, pFy, pFu), "F")
    g["Rweld"] = h.v("φRn", "Filetes placa–HSS, corte directo: 2·φ·0.6·FEXX·0.707·w·l", 2 * aisc.rn_filete(FEXX, w, L), "F")
    g["Rpun"] = h.v("φRn·e", "Punzonamiento de la pared (Manual Ec. 10-7): φ·Fu·t·lp²/5", 0.75 * P["hFu"] * P["t"] * L ** 2 / 5, "M")
    g["bt"] = (P["W"] - 3 * P["t"]) / P["t"]
    g["bt_lim"] = 1.40 * math.sqrt(aisc.E / P["hFy"])
    h.chk(G_DET, "Pared no esbelta (placa de corte): b/t ≤ 1.40√(E/Fy)", "Manual Parte 10 (K.6)", g["bt"], g["bt_lim"], "")
    h.chk(G_DET, "Pared del HSS: t ≥ 3.09·D/Fu (filetes placa–HSS)", "Manual Ec. 9-2", aisc.t_min_soporte(FEXX, P["hFu"], w, 2), P["t"], "Lc")
    h.chk(G_DET, "Paso s ≥ 3·db", "J3.3", 3 * p["db"], s, "Lc")
    h.chk(G_DET, "Borde vertical Lev ≥ mínimo", "J3.4", p["edge"], lev, "Lc")
    h.chk(G_DET, "Borde horizontal Leh ≥ mínimo", "J3.4", p["edge"], leh, "Lc")
    h.chk(G_DET, "Placa dentro del alma libre: l ≤ d − 2·tf − 2 cm", "Geometría", L, P["bd"] - 2 * P["btf"] - 2.0, "Lc")
    h.chk(G_DET, "Número de pernos 2 ≤ n ≤ 12", "Manual Parte 10", n, 12, "", ratio=max(2 / n, n / 12))
    return g


def placa_corte_combo(h, g, Vu):
    h.chk(G_PL, "Pernos en la placa (grupo)", "J3.6 · J3.10", Vu, g["Rb_pl"], "F")
    h.chk(G_PL, "Pernos en el alma de la viga (grupo)", "J3.6 · J3.10", Vu, g["Rb_wb"], "F")
    h.chk(G_PL, "Placa: fluencia por corte", "J4.2(a)", Vu, g["Rpl_y"], "F")
    h.chk(G_PL, "Placa: ruptura por corte", "J4.2(b)", Vu, g["Rpl_r"], "F")
    h.chk(G_PL, "Placa: bloque de cortante", "J4.3", Vu, g["Rpl_b"], "F")
    h.chk(G_PL, "Filetes placa–pared del HSS", "J2.4", Vu, g["Rweld"], "F")
    h.chk(G_PL, "Punzonamiento de la pared: Vu·a ≤ φFu·t·lp²/5", "Manual Ec. 10-7a", Vu * g["a"], g["Rpun"], "M")
