"""Conexión de momento viga W – columna HSS rectangular con PLACA PASANTE (through-plate), NO sísmica.

AISC Design Guide 24 (2010), cap. 4, Ej. 4.2. Dos placas horizontales atraviesan el HSS (se sueldan a su perímetro) y sobresalen
a cada lado; las alas de las vigas se atornillan a ellas (empalme a traslape, corte simple). El brazo de momento es d + tp (placas
fuera de las alas). Equilibrio del nudo (viga izquierda i, derecha d; Vd − Vi y Md − Mi como en el ejemplo):
        Pconn = Vi + Vd + Ptop        Mconn = [Md − Mi + (H/2)(Vd − Vi)] / 2
Verificaciones por lado: fluencia, ruptura y compresión (J4.4) de la placa, pernos (corte y aplastamiento en placa y ala), bloque
de cortante de placa y ala (J4.3); soldadura placa–HSS por el perímetro bajo Pconn y Mconn (Manual Parte 8), viga (φMp, φVn)
y la placa simple de corte.
Sin diseño sísmico. NOTA: el ejemplo 4.2 de la guía usa Fnv = 48 ksi para A325-N (AISC 360-05); este programa usa 54 ksi (360-16).
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import aisc  # noqa: E402
import hss_comun as C  # noqa: E402
from handmod import Modulo, campo, seccion, spec, tabla_combos  # noqa: E402
from wuf.engine import _cv  # noqa: E402

G_PT, G_PB, G_SD = "PLACA PASANTE", "PERNOS DE LAS ALAS", "SOLDADURA PLACA – HSS"
SPEC = spec(
    "CONEXIÓN DE MOMENTO VIGA W – COLUMNA HSS CON PLACA PASANTE (NO SÍSMICA)",
    "AISC DG24 (cap. 4, Ej. 4.2)  ·  AISC 360-16 J2, J3, J4  ·  AISC Manual Partes 8 y 10  ·  LRFD  ·  Unidades: Tonf, Tonf·m, mm, kgf/cm²",
    [
        seccion("DATOS GENERALES", [campo("DIS_C7", "Proyecto", "Edificio — ejemplo"), campo("DIS_C8", "Elemento / nudo", "Nudo C-2 nivel 3"),
                                    campo("lim_verde", "Límite verde / amarillo (ratio)", 0.9)]),
        seccion("1. VIGA W (igual a ambos lados)", C.campos_viga(), C.derivados_viga()),
        seccion("2. COLUMNA HSS", C.campos_hss(defecto="ARMADO (flejes soldados)", dims=(304.8, 508, 11.81)), C.derivados_hss()),
        seccion("3. PLACA PASANTE Y PERNOS DE LAS ALAS", [
            campo("pp_acero", "Acero de la placa pasante", "A36", options=C.ACEROS_VIGA),
            campo("pp_bp", "Ancho de placa bp", 355.6, "mm"), campo("pp_t", "Espesor tp", 15.875, "mm"),
            campo("pp_nb", "Pernos por fila y por lado", 5), campo("pp_rows", "Filas de pernos por lado", 2, options=[2]),
            campo("pp_s", "Paso s", 80, "mm"), campo("pp_g", "Gramil g entre filas", 88.9, "mm"),
            campo("pp_a", "a — cara del HSS al primer perno", 76.2, "mm"),
            campo("pp_lep", "Borde en la placa (último perno → extremo)", 44.45, "mm"),
            campo("pp_lef", "Borde en el ala (primer perno → extremo de la viga)", 50.8, "mm"),
            campo("pn_grado", "Grado de pernos", "A325-N (roscas incl.)", options=list(aisc.PERNOS)),
            campo("pn_diam", "Diámetro de pernos", '1"', options=aisc.DIAMETROS),
            campo("sd_elec", "Electrodo", "E70XX", options=list(aisc.ELECTRODOS)),
            campo("pp_w", "Filete placa pasante – perímetro del HSS", 12.7, "mm")]),
        seccion("4. PLACA SIMPLE DE CORTE", C.campos_placa_corte(n=3, s=80, lev=38.1, leh=50.8, tp=9.5, a=76.2, w=6.35)[:8]),
    ],
    combos=tabla_combos([("nombre", "Combinación"), ("Mi", "Mu izq. (Tonf·m)"), ("Vi", "Vu izq. (Tonf)"), ("Md", "Mu der. (Tonf·m)"),
                         ("Vd", "Vu der. (Tonf)"), ("P", "Pu HSS sup. (Tonf)")],
                        [{"nombre": "1.2D+1.6L", "Mi": 4, "Vi": 2, "Md": 20, "Vd": 9, "P": 60}]),
    notas=["Alcance de la Design Guide 24: SOLO cargas no sísmicas.",
           "Momentos positivos: Mi y Md producen tracción en el ala superior de su viga (se usa |M| por lado; la placa sirve en los dos sentidos).",
           "La placa simple de corte usa los mismos estados límite del módulo viga–columna soldada (sin verificar contra la Tabla 10-9a).",
           "Pernos de las alas: dos filas por lado en corte simple; el bloque de cortante supone Ubs = 1 como en el ejemplo."])

def global_fn(h, I):
    I = dict(I)
    P = C.hss_y_viga(I)
    bd, bbf, btw, btf, W, D, t = (P[k] for k in ("bd", "bbf", "btw", "btf", "W", "D", "t"))
    ppFy, ppFu = aisc.ACEROS[I["pp_acero"]]
    FEXX = aisc.ELECTRODOS[I["sd_elec"]]
    p = aisc.perno(I["pn_diam"], I["pn_grado"])
    nb, rows = int(I["pp_nb"]), int(I["pp_rows"])
    bp, tp, s, g, a = I["pp_bp"] / 10, I["pp_t"] / 10, I["pp_s"] / 10, I["pp_g"] / 10, I["pp_a"] / 10
    lep, lef, w = I["pp_lep"] / 10, I["pp_lef"] / 10, I["pp_w"] / 10
    dh, dhn = p["dh"], p["dh_net"]
    h.sec("1. VIGA")
    Zx = bbf * btf * (bd - btf) + btw * (bd - 2 * btf) ** 2 / 4
    phiMp = h.v("φMp", "Flexión de la viga: 0.90·Fy·Zx", 0.9 * P["bFy"] * Zx, "M")
    phiv, cv = _cv((bd - 2 * btf) / btw, P["bFy"], I["vg_perfil"].startswith("W"))
    phiVn = h.v("φVn", "Cortante del alma (G2.1)", phiv * 0.6 * P["bFy"] * bd * btw * cv, "F")
    brazo = h.v("d + tp", "Brazo de momento (placas fuera de las alas)", bd + tp, "Lc")
    h.sec("2. PLACA PASANTE")
    Ag = bp * tp
    Rty = h.v("φRn", "Fluencia en tracción: 0.90·Fyp·bp·tp (J4.1a)", aisc.rn_fluencia_traccion(ppFy, Ag), "F")
    An = Ag - rows * dhn * tp
    Ae = min(An, 0.85 * Ag)
    Rtr = h.v("φRn", "Ruptura en tracción: 0.75·Fup·Ae, An = Ag − 2(dh + 1/16)·tp (J4.1b)", aisc.rn_ruptura_traccion(ppFu, Ae), "F")
    r = tp / math.sqrt(12)
    KLr = 1.0 * a / r
    Rcp = h.v("φRn", "Compresión (J4.4), K = 1, L = a", aisc.rn_compresion_placa(ppFy, Ag, KLr), "F")
    h.v("KL/r", "Esbeltez de la placa en la luz libre a", KLr, "")
    h.sec("3. PERNOS DE LAS ALAS (por lado)")
    n_tot = rows * nb
    r_v = aisc.rn_corte_perno(p["Fnv"], p["Ab"])
    Rsh = h.v("φRn", "Corte de los pernos: n·φ·Fnv·Ab (corte simple)", n_tot * r_v, "F")
    lc_pe, lc_pi = lep - dh / 2, s - dh
    lc_fe, lc_fi = lef - dh / 2, s - dh
    Rbp = h.v("φRn", "Aplastamiento en la placa: filas·[1 extremo + (nb − 1) interiores]", rows * (aisc.rn_aplastamiento(p["db"], tp, ppFu, lc_pe) +
              (nb - 1) * aisc.rn_aplastamiento(p["db"], tp, ppFu, lc_pi)), "F")
    Rbf = h.v("φRn", "Aplastamiento en el ala de la viga", rows * (aisc.rn_aplastamiento(p["db"], btf, P["bFu"], lc_fe) +
              (nb - 1) * aisc.rn_aplastamiento(p["db"], btf, P["bFu"], lc_fi)), "F")
    # bloque de cortante placa (el HSS está del lado del primer perno): longitud desde el borde de la placa
    Lgv_p = lep + (nb - 1) * s
    Agv = rows * Lgv_p * tp
    Anv = Agv - rows * (nb - 0.5) * dhn * tp
    Ant = (g - dhn) * tp
    Rbs_p = h.v("φRn", "Bloque de cortante de la placa (J4.3, Ubs = 1)", aisc.rn_bloque_corte(Agv, Anv, Ant, ppFy, ppFu), "F")
    Lgv_f = lef + (nb - 1) * s
    Agv_f = rows * Lgv_f * btf
    Anv_f = Agv_f - rows * (nb - 0.5) * dhn * btf
    Ant_f = (bbf - g - dhn) * btf
    Rbs_f = h.v("φRn", "Bloque de cortante del ala de la viga (J4.3, Ubs = 1)", aisc.rn_bloque_corte(Agv_f, Anv_f, Ant_f, P["bFy"], P["bFu"]), "F")
    L_pl = 2 * (lep + (nb - 1) * s + a) + D
    h.v("Lplaca", "Longitud total de la placa pasante: 2·(Le + (nb − 1)·s + a) + H", L_pl, "Lc")
    h.v("Lhss", "Longitud mínima del segmento de HSS entre placas: d + 1/8 in", bd + 0.125 * aisc.IN, "Lc")
    h.sec("4. SOLDADURA PLACA – HSS (perímetro)")
    Aw = 2 * (W + D)
    Iw = D ** 3 / 6 + W * D ** 2 / 2
    h.v("Aw", "Longitud de soldadura por unidad de garganta: 2(B + H)", Aw, "Lc")
    h.v("Iw", "Inercia por unidad de garganta: H³/6 + B·H²/2", Iw, "")
    cap_w = h.v("φrn", "Resistencia por cm de filete: 0.75·0.6·FEXX·0.707·w", aisc.rn_filete(FEXX, w, 1.0), "FL")
    Isw = None
    # detalles
    h.chk(C.G_DET, "Paso s ≥ 3·db", "J3.3", 3 * p["db"], s, "Lc")
    h.chk(C.G_DET, "Gramil g ≥ 3·db", "J3.3", 3 * p["db"], g, "Lc")
    h.chk(C.G_DET, "Borde en la placa ≥ mínimo", "J3.4", p["edge"], lep, "Lc")
    h.chk(C.G_DET, "Borde en el ala ≥ mínimo", "J3.4", p["edge"], lef, "Lc")
    h.chk(C.G_DET, "Borde transversal en el ala: (bf − g)/2 ≥ mínimo", "J3.4", p["edge"], (bbf - g) / 2, "Lc")
    h.chk(C.G_DET, "Borde transversal en la placa: (bp − g)/2 ≥ mínimo", "J3.4", p["edge"], (bp - g) / 2, "Lc")
    h.chk(C.G_DET, "Placa más ancha que el HSS (soldadura de filete): bp ≥ B + 2w", "DG24 Ej. 4.2", W + 2 * w, bp, "Lc")
    h.chk(C.G_DET, "Ala de la viga cabe en la placa: bf ≤ bp", "Geometría", bbf, bp, "Lc")
    h.chk(C.G_DET, "Pared del HSS: B/t ≤ 35 (referencia K1.3b)", "Tabla 7-2A", W / t, 35, "")
    gp = C.placa_corte_global(h, dict(I, sp_acero=I["sp_acero"]), P)
    return {"derivados": C.derivados(P), "vars": {"bd": bd, "bbf": bbf, "btf": btf, "W": W, "D": D, "t": t, "bp": bp, "tp": tp, "nb": nb,
                                                    "rows": rows, "s": s, "g": g, "a": a, "lep": lep, "lef": lef, "w": w, "db": p["db"],
                                                    "L": L_pl, "n": gp["n"], "tps": gp["tp"]},
            "g": dict(brazo=brazo, tp=tp, phiMp=phiMp, phiVn=phiVn, Rty=Rty, Rtr=Rtr, Rcp=Rcp, Rsh=Rsh, Rbp=Rbp, Rbf=Rbf, Rbs_p=Rbs_p,
                      Rbs_f=Rbs_f, Aw=Aw, Iw=Iw, cap_w=cap_w, D=D, gp=gp)}


def combo_fn(h, ctx, c, I):
    g = ctx["g"]
    Mi, Md = float(c.get("Mi") or 0) * 1e5, float(c.get("Md") or 0) * 1e5
    Vi, Vd = float(c.get("Vi") or 0) * 1e3, float(c.get("Vd") or 0) * 1e3
    Pt = float(c.get("P") or 0) * 1e3
    h.sec(f"COMBINACIÓN {c['nombre']}")
    Pc = h.v("Pconn", "Axial en la conexión: Vi + Vd + Ptop", abs(Vi) + abs(Vd) + Pt, "F")
    Mc = h.v("Mconn", "Momento en la conexión: [Md − Mi + (H/2)(Vd − Vi)]/2", abs(Md - Mi + (g["D"] / 2) * (Vd - Vi)) / 2, "M")
    lado = max((abs(Mi), "izq."), (abs(Md), "der."))
    R = h.v("Ru", "Fuerza máxima en la placa: máx(|Mi|, |Md|)/(d + tp)", max(abs(Mi), abs(Md)) / g["brazo"], "F")
    Vmax = max(abs(Vi), abs(Vd))
    h.chk(C.G_VIGA, "Flexión de la viga: Mu ≤ φMp", "F2", max(abs(Mi), abs(Md)), g["phiMp"], "M")
    h.chk(C.G_VIGA, "Cortante del alma de la viga", "G2.1", Vmax, g["phiVn"], "F")
    h.chk(G_PT, "Fluencia en tracción de la placa", "J4.1(a)", R, g["Rty"], "F")
    h.chk(G_PT, "Ruptura en tracción de la placa", "J4.1(b)", R, g["Rtr"], "F")
    h.chk(G_PT, "Compresión de la placa (pandeo)", "J4.4", R, g["Rcp"], "F")
    h.chk(G_PB, "Corte de los pernos", "J3.6", R, g["Rsh"], "F")
    h.chk(G_PB, "Aplastamiento en la placa", "J3.10", R, g["Rbp"], "F")
    h.chk(G_PB, "Aplastamiento en el ala de la viga", "J3.10", R, g["Rbf"], "F")
    h.chk(G_PB, "Bloque de cortante de la placa", "J4.3", R, g["Rbs_p"], "F")
    h.chk(G_PB, "Bloque de cortante del ala de la viga", "J4.3", R, g["Rbs_f"], "F")
    fw = Pc / g["Aw"] + Mc * (g["D"] / 2) / g["Iw"]
    h.v("fw", "Fuerza por cm de soldadura: Pconn/Aw + Mconn·(H/2)/Iw", fw, "FL")
    h.chk(G_SD, "Soldadura placa – perímetro del HSS (Pconn + Mconn)", "Manual Parte 8 · Ej. 4.2", fw, g["cap_w"], "FL")
    C.placa_corte_combo(h, g["gp"], Vmax)


_MOD = Modulo(SPEC, global_fn, combo_fn)
calcular = _MOD.calcular
CAT = _MOD.CAT
