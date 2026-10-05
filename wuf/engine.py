"""Conexión de momento viga–columna con alas soldadas directamente (CJP) y placa simple de alma.

Procedimiento del Manual AISC 15.ª ed. Parte 12 y Design Examples v15, Ej. II.B-3 (alas con soldadura de
penetración completa) y II.B-1 (placa simple de alma y revisión de la columna bajo fuerzas concentradas):
  · las alas de la viga se sueldan a tope (CJP) al ala de la columna y transmiten Ffu = Mu/(d − tf);
  · el alma se une con una placa simple soldada a la columna y atornillada al alma, para el corte;
    el momento excéntrico lo toman las alas (no se considera en el grupo de pernos);
  · columna: flexión local del ala (J10.1), fluencia local (J10.2), aplastamiento (J10.3), pandeo del alma
    (J10.5, vigas a ambos lados), zona de panel (J10.6) y rigidizadores de continuidad (J10.8).
No incluye: requisitos de precalificación sísmica AISC 358 cap. 9 (WUF-W), pandeo lateral de la viga ni
flexión en el eje débil.
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
SI_NO = ["Sí", "No"]
IN, KIP = aisc.IN, aisc.KIP


def _perfil_campos(p, titulo_perfil, defecto, catalogo, defaults_e):
    return [campo(f"{p}_perfil", "Perfil (catálogo o ARMADO)", defecto, options=[ARMADO] + list(catalogo))] + [
        campo(f"{p}_E_{k}", f"{lab} (armado)", v, "mm", armado_de=f"{p}_perfil")
        for (k, lab), v in zip((("d", "Peralte d"), ("bf", "Ancho de ala bf"), ("tw", "Espesor de alma tw"),
                                ("tf", "Espesor de ala tf")), defaults_e)]


SPEC = spec(
    "CONEXIÓN DE MOMENTO VIGA–COLUMNA CON ALAS SOLDADAS DIRECTAMENTE (CJP)",
    "AISC 360-16 (J2, J3, J4, J10)  ·  AISC Manual 15ª ed. Parte 12  ·  Design Examples II.B-3 / II.B-1  ·  LRFD  ·  Unidades: Tonf, Tonf·m, mm, kgf/cm²",
    [
        seccion("DATOS GENERALES", [campo("DIS_C7", "Proyecto", "Edificio — ejemplo"),
                                    campo("DIS_C8", "Elemento / nudo", "Pórtico eje B, nivel 2"),
                                    campo("lim_verde", "Límite verde / amarillo (ratio)", 0.9)]),
        seccion("1. VIGA", _perfil_campos("vg", "Viga", "VK400X180X6X12", VIGAS, (400, 180, 6, 12)) +
                [campo("vg_acero", "Acero", "A572 Gr50", options=ACEROS)],
                [{"name": n, "label": "d / bf / tw / tf", "unit": "mm"} for n in ("vg_d_mm", "vg_bf_mm", "vg_tw_mm", "vg_tf_mm")]),
        seccion("2. COLUMNA (conexión al ala)",
                _perfil_campos("co", "Columna", "HA500X250X10X15", COLS, (500, 250, 10, 15)) +
                [campo("co_acero", "Acero", "A572 Gr50", options=ACEROS),
                 campo("co_kw", "Filete / radio alma–ala (para k)", 6, "mm"),
                 campo("co_dtop", "Tope de columna → ala superior de viga", 1000, "mm"),
                 campo("dos_lados", "Vigas a ambos lados (columna interior)", "No", options=SI_NO),
                 campo("Mu_op", "Mu viga opuesta (suma en zona de panel)", 0, "Tonf·m"),
                 campo("Pu_col", "Pu de la columna (compresión)", 20, "Tonf"),
                 campo("cp_usar", "Rigidizadores de continuidad", "Sí", options=SI_NO),
                 campo("cp_t", "Rigidizador: espesor", 15, "mm"),
                 campo("cp_b", "Rigidizador: ancho (c/lado)", 110, "mm"),
                 campo("dp_t", "Placa de refuerzo del alma (doubler): espesor", 0, "mm")],
                [{"name": n, "label": "d / bf / tw / tf", "unit": "mm"} for n in ("co_d_mm", "co_bf_mm", "co_tw_mm", "co_tf_mm")]),
        seccion("3. PLACA SIMPLE DE ALMA", [
            campo("pl_acero", "Acero de placa", "A36", options=ACEROS),
            campo("pl_t", "Espesor de placa tp", 9.5, "mm"),
            campo("pl_n", "Número de pernos n (1 línea vertical)", 3),
            campo("pl_s", "Paso vertical s", 76.2, "mm"),
            campo("pl_lev", "Borde vertical Lev (placa y alma)", 38.1, "mm"),
            campo("pl_leh", "Borde horizontal Leh en la placa", 50.8, "mm"),
            campo("pn_grado", "Grado de pernos", "A325-N (roscas incl.)", options=list(aisc.PERNOS)),
            campo("pn_diam", "Diámetro de pernos", '7/8"', options=aisc.DIAMETROS),
            campo("sd_elec", "Electrodo", "E70XX", options=list(aisc.ELECTRODOS)),
            campo("pl_w", "Filete placa–columna (c/lado)", 6.35, "mm")]),
    ],
    combos=tabla_combos([("nombre", "Combinación"), ("M", "Mu (Tonf·m)"), ("V", "Vu (Tonf)")],
                        [{"nombre": "1.2D+1.6L", "M": 14, "V": 8}, {"nombre": "1.2D+1.0E+L", "M": 20, "V": 11}]),
    notas=["Alas: soldadura de penetración completa (CJP) con agujeros de acceso; el metal de aporte desarrolla el ala de la viga.",
           "Alma: placa simple soldada a la columna y atornillada al alma; el momento excéntrico lo toman las alas.",
           "Columna: J10.1 flexión local del ala, J10.2 fluencia local, J10.3 aplastamiento y J10.6 zona de panel; con rigidizadores de continuidad se verifica J10.8.",
           "No incluye la precalificación sísmica de AISC 358 cap. 9 (WUF-W): detallado, ensayos ni diseño por capacidad."])


def _cv(h_tw, Fy, laminado):
    """G2.1: (φv, Cv1) para alma sin rigidizar (kv = 5.34)."""
    if laminado and h_tw <= 2.24 * math.sqrt(aisc.E / Fy):
        return 1.0, 1.0
    lim = 1.10 * math.sqrt(5.34 * aisc.E / Fy)
    return 0.90, (1.0 if h_tw <= lim else lim / h_tw)


def global_fn(h, I):
    G = "PLACA SIMPLE DE ALMA"
    bd, bbf, btw, btf = perfil(I["vg_perfil"], I, "vg", VIGAS)
    cd, cbf, ctw, ctf = perfil(I["co_perfil"], I, "co", COLS)
    bFy, bFu = aisc.ACEROS[I["vg_acero"]]
    cFy, cFu = aisc.ACEROS[I["co_acero"]]
    pFy, pFu = aisc.ACEROS[I["pl_acero"]]
    FEXX = aisc.ELECTRODOS[I["sd_elec"]]
    p = aisc.perno(I["pn_diam"], I["pn_grado"])
    kw = float(I["co_kw"]) / 10
    k = ctf + kw
    n = int(I["pl_n"])
    s, lev, leh = I["pl_s"] / 10, I["pl_lev"] / 10, I["pl_leh"] / 10
    tp, w = I["pl_t"] / 10, I["pl_w"] / 10
    L = 2 * lev + (n - 1) * s

    h.sec("1. GEOMETRÍA Y MATERIALES")
    Zx = bbf * btf * (bd - btf) + btw * (bd - 2 * btf) ** 2 / 4
    h.v("Zx", "Módulo plástico de la viga: bf·tf·(d − tf) + tw·(d − 2tf)²/4", Zx, "")
    phiMp = h.v("φMp", "Resistencia a flexión de la viga (arriostrada): 0.90·Fy·Zx", 0.9 * bFy * Zx, "M")
    laminado = I["vg_perfil"].startswith("W")
    phiv, cv = _cv((bd - 2 * btf) / btw, bFy, laminado)
    phiVn = h.v("φVn", "Cortante del alma de la viga (G2.1): φv·0.6·Fy·d·tw·Cv", phiv * 0.6 * bFy * bd * btw * cv, "F")
    h.v("k", "Distancia k de la columna: tf + filete", k, "Lc")
    Ac = 2 * cbf * ctf + (cd - 2 * ctf) * ctw
    h.v("Ac", "Área de la columna ≈ 2·bf·tf + (d − 2tf)·tw", Ac, "A")
    Py = h.v("Py", "Fyc·Ac", cFy * Ac, "F")

    h.sec("2. COLUMNA — FUERZAS CONCENTRADAS (J10)")
    N = btf                                                       # longitud de apoyo: espesor del ala soldada
    dtop = I["co_dtop"] / 10
    cp = I["cp_usar"] == "Sí"
    twz = ctw + I["dp_t"] / 10
    interior_y = dtop >= cd
    interior_c = dtop >= cd / 2
    chk_ala = bbf > 0.15 * cbf
    Rfb = h.v("φRn", "Flexión local del ala (J10-1): 0.90·6.25·tf²·Fyc", aisc.rn_flexion_local_ala(cFy, ctf), "F")
    Rwy = h.v("φRn", "Fluencia local del alma (J10-2/3): 1.0·(5k + N | 2.5k + N)·Fyc·tw", aisc.rn_fluencia_local_alma(cFy, ctw, k, N, interior_y), "F")
    Rwc = h.v("φRn", "Aplastamiento del alma (J10-4/5)", aisc.rn_aplastamiento_alma(cFy, ctw, ctf, cd, N, interior_c), "F")
    Rwb = h.v("φRn", "Pandeo del alma (J10-8), vigas a ambos lados", aisc.rn_pandeo_alma(cFy, ctw, cd - 2 * k, interior_c), "F")
    Rpz = h.v("φRv", "Zona de panel (J10.6): 0.90·0.6·Fyc·dc·(tw + doubler)", aisc.rn_zona_panel(cFy, cd, twz, I["Pu_col"] * 1000, Py), "F")
    Rcp = h.v("φRn", "Rigidizadores de continuidad (J10.8): 0.90·Fyc·2·b·t", 0.9 * cFy * 2 * I["cp_b"] / 10 * I["cp_t"] / 10, "F")

    h.sec("3. PLACA SIMPLE DE ALMA (Manual Parte 10 / II.B-1)")
    dh, dhn = p["dh"], p["dh_net"]
    r_v = aisc.rn_corte_perno(p["Fnv"], p["Ab"])
    lc_e, lc_i = lev - dh / 2, s - dh
    r_pe = min(r_v, aisc.rn_aplastamiento(p["db"], tp, pFu, lc_e))
    r_pi = min(r_v, aisc.rn_aplastamiento(p["db"], tp, pFu, lc_i))
    r_wi = min(r_v, aisc.rn_aplastamiento(p["db"], btw, bFu, lc_i))
    Rb_pl = h.v("φRn", "Grupo de pernos en la placa: 1 perno de borde + (n − 1) interiores, mín(corte; aplast.; desgarre)", r_pe + (n - 1) * r_pi, "F")
    Rb_wb = h.v("φRn", "Grupo de pernos en el alma de la viga: n·mín(corte; aplast.; desgarre)", n * r_wi, "F")
    Rpl_y = h.v("φRn", "Placa, fluencia por corte (J4.2a): 1.0·0.6·Fy·l·tp", aisc.rn_fluencia_corte(pFy, L * tp), "F")
    Rpl_r = h.v("φRn", "Placa, ruptura por corte (J4.2b): 0.75·0.6·Fu·(l − n·dh,n)·tp", aisc.rn_ruptura_corte(pFu, (L - n * dhn) * tp), "F")
    Agv = ((n - 1) * s + lev) * tp
    Anv = Agv - (n - 0.5) * dhn * tp
    Ant = (leh - 0.5 * dhn) * tp
    Rpl_b = h.v("φRn", "Placa, bloque de cortante (J4.3)", aisc.rn_bloque_corte(Agv, Anv, Ant, pFy, pFu), "F")
    Rweld = h.v("φRn", "Filetes placa–columna, corte directo: 2·0.75·0.6·FEXX·0.707·w·l", 2 * aisc.rn_filete(FEXX, w, L), "F")
    Rcf = h.v("φRn", "Ruptura por corte del ala de la columna en los filetes (J4.2b): 0.75·0.6·Fu·2·l·tf", aisc.rn_ruptura_corte(cFu, 2 * L * ctf), "F")

    G1, G2, G3, G4 = "VIGA", "COLUMNA — FUERZAS CONCENTRADAS", "PLACA SIMPLE DE ALMA", "DETALLES (requerido / provisto)"
    # verificaciones sin carga (geometría)
    tmin_w = max(5 / 8 * tp, (3 if min(tp, btw) * 10 <= 6 else 5 if min(tp, btw) * 10 <= 13 else 6 if min(tp, btw) * 10 <= 19 else 8) / 10)
    h.chk(G4, "Filete ≥ máx(5/8·tp ; mínimo J2.4)", "Manual Parte 10 · Tabla J2.4", tmin_w, w, "Ls")
    h.chk(G4, "Paso s ≥ 3·db", "J3.3", 3 * p["db"], s, "Lc")
    h.chk(G4, "Borde vertical Lev ≥ mínimo", "J3.4", p["edge"], lev, "Lc")
    h.chk(G4, "Borde horizontal Leh ≥ mínimo", "J3.4", p["edge"], leh, "Lc")
    h.chk(G4, "Rotación: mín(tp ; tw) ≤ db/2 + 1/16 in", "Manual Tabla 10-9", min(tp, btw), p["db"] / 2 + IN / 16, "Lc")
    h.chk(G4, "Placa dentro del alma libre: l ≤ d − 2·tf − 2 cm", "Geometría", L, bd - 2 * btf - 2.0, "Lc")
    h.chk(G4, "Número de pernos 2 ≤ n ≤ 12", "Manual Parte 10", n, 12, "", ratio=max(2 / n, n / 12))
    if cp:
        h.chk(G2, "Rigidizadores: b + tcw/2 ≥ bbf/3", "J10.8", bbf / 3 - ctw / 2, I["cp_b"] / 10, "Lc")
        h.chk(G2, "Rigidizadores: t ≥ tbf/2", "J10.8", btf / 2, I["cp_t"] / 10, "Lc")
    ctx = {"derivados": {"vg_d_mm": bd * 10, "vg_bf_mm": bbf * 10, "vg_tw_mm": btw * 10, "vg_tf_mm": btf * 10,
                 "co_d_mm": cd * 10, "co_bf_mm": cbf * 10, "co_tw_mm": ctw * 10, "co_tf_mm": ctf * 10},
           "vars": {"bd": bd, "bbf": bbf, "btw": btw, "btf": btf, "cd": cd, "cbf": cbf, "ctw": ctw, "ctf": ctf,
                    "L": L, "n": n, "s": s, "lev": lev, "leh": leh, "tp": tp, "db": p["db"], "w": w, "cp": cp,
                    "cp_t": I["cp_t"] / 10, "cp_b": I["cp_b"] / 10},
           "g": dict(bd=bd, btf=btf, phiMp=phiMp, phiVn=phiVn, Rfb=Rfb, Rwy=Rwy, Rwc=Rwc, Rwb=Rwb, Rpz=Rpz, Rcp=Rcp,
                     Rb_pl=Rb_pl, Rb_wb=Rb_wb, Rpl_y=Rpl_y, Rpl_r=Rpl_r, Rpl_b=Rpl_b, Rweld=Rweld, Rcf=Rcf,
                     chk_ala=chk_ala, cp=cp, dos=I["dos_lados"] == "Sí")}
    return ctx


def combo_fn(h, ctx, c, I):
    g = ctx["g"]
    Mu = abs(float(c.get("M") or 0)) * 1e5
    Vu = abs(float(c.get("V") or 0)) * 1e3
    Mop = abs(float(I["Mu_op"] or 0)) * 1e5 if g["dos"] else 0.0
    h.sec(f"COMBINACIÓN {c['nombre']}")
    Ffu = h.v("Ffu", "Fuerza en el ala: Mu/(d − tbf)", Mu / (g["bd"] - g["btf"]), "F")
    h.v("Mu", "Momento", Mu, "M")
    h.v("Vu", "Cortante", Vu, "F")
    G1, G2, G3 = "VIGA", "COLUMNA — FUERZAS CONCENTRADAS", "PLACA SIMPLE DE ALMA"
    h.chk(G1, "Flexión de la viga: Mu ≤ φMp (arriostrada)", "F2", Mu, g["phiMp"], "M")
    h.chk(G1, "Cortante del alma de la viga", "G2.1", Vu, g["phiVn"], "F")
    cp = g["cp"]
    h.chk(G2, "Flexión local del ala de la columna", "J10.1", Ffu, g["Rfb"], "F", activo=g["chk_ala"] and not cp)
    h.chk(G2, "Fluencia local del alma", "J10.2", Ffu, g["Rwy"], "F", activo=not cp)
    h.chk(G2, "Aplastamiento del alma (crippling)", "J10.3", Ffu, g["Rwc"], "F", activo=not cp)
    h.chk(G2, "Pandeo del alma en compresión", "J10.5", Ffu, g["Rwb"], "F", activo=not cp and g["dos"])
    Fsu = max(0.0, Ffu - min(g["Rfb"] if g["chk_ala"] else 1e30, g["Rwy"], g["Rwc"], g["Rwb"] if g["dos"] else 1e30))
    h.chk(G2, "Rigidizadores de continuidad: Fsu ≤ φRn", "J10.8", Fsu, g["Rcp"], "F", activo=cp)
    Vpz = h.v("Vpz", "Cortante en zona de panel: (Mu + Mu,op)/(d − tbf)", (Mu + Mop) / (g["bd"] - g["btf"]), "F")
    h.chk(G2, "Zona de panel (corte)", "J10.6", Vpz, g["Rpz"], "F")
    h.chk(G3, "Pernos en la placa (grupo)", "J3.6 · J3.10", Vu, g["Rb_pl"], "F")
    h.chk(G3, "Pernos en el alma de la viga (grupo)", "J3.6 · J3.10", Vu, g["Rb_wb"], "F")
    h.chk(G3, "Placa: fluencia por corte", "J4.2(a)", Vu, g["Rpl_y"], "F")
    h.chk(G3, "Placa: ruptura por corte", "J4.2(b)", Vu, g["Rpl_r"], "F")
    h.chk(G3, "Placa: bloque de cortante", "J4.3", Vu, g["Rpl_b"], "F")
    h.chk(G3, "Filetes placa–columna", "J2.4", Vu, g["Rweld"], "F")
    h.chk(G3, "Ala de la columna: ruptura por corte en los filetes", "J4.2(b)", Vu, g["Rcf"], "F")


_MOD = Modulo(SPEC, global_fn, combo_fn)
calcular = _MOD.calcular
CAT = _MOD.CAT
