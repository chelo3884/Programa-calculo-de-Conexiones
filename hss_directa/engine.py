"""Conexión de momento viga W soldada DIRECTAMENTE a la pared de una columna HSS rectangular (NO sísmica).

AISC Design Guide 24 (2010), cap. 4 (Ej. 4.3) y Tabla 7-2; AISC 360-16 §K1.3b. Cada ala de la viga es una placa transversal sobre la
cara del HSS: Ff = Mu/(d − tf) debe resistirse por (la guía solo trae estos estados límite):
  K1-2  fluencia local del ala por distribución desigual   φ = 0.95    10/(B/t)·Fy·t·bf ≤ Fyp·tf·bf
  K1-3  punzonamiento de la pared, si 0.85B ≤ bf ≤ B − 2t   φ = 0.95    0.6·Fy·t·(2tf + 2Bep)
  K1-4  fluencia de las paredes laterales, si bf = B        φ = 1.00    2·Fy·t·(5k + N)
  K1-5  aplastamiento de paredes laterales (compresión), bf = B        φ = 0.75
  K1-6  pandeo de paredes laterales (vigas a ambos lados), bf = B      φ = 0.90
Más la viga (φMp, φVn) y una placa simple para el corte (pernos, placa y soldadura; Manual Parte 10, Ej. K.6 para el punzonamiento).
Límites de aplicabilidad (Tabla 7-2A): 0.25 ≤ bf/B ≤ 1.0, B/t ≤ 35, Fy ≤ 52 ksi, Fy/Fu ≤ 0.8, bf ≤ B − 3t.
No incluye diseño sísmico ni la flexión/axial del HSS como miembro (solo su efecto Qf en las paredes), ni la interacción
entre el corte de la placa y las alas sobre la misma pared.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import aisc  # noqa: E402
import hss_comun as C  # noqa: E402
from handmod import Modulo, campo, seccion, spec, tabla_combos  # noqa: E402
from wuf.engine import _cv  # noqa: E402

KSI = aisc.KSI
SPEC = spec(
    "CONEXIÓN DE MOMENTO VIGA W SOLDADA DIRECTAMENTE A COLUMNA HSS (NO SÍSMICA)",
    "AISC DG24 (cap. 4, Tabla 7-2, Ej. 4.3)  ·  AISC 360-16 K1.3b, J2, J3, J4  ·  LRFD  ·  Unidades: Tonf, Tonf·m, mm, kgf/cm²",
    [
        seccion("DATOS GENERALES", [campo("DIS_C7", "Proyecto", "Edificio — ejemplo"), campo("DIS_C8", "Elemento / nudo", "Pórtico eje B, nivel 2"),
                                    campo("lim_verde", "Límite verde / amarillo (ratio)", 0.9)]),
        seccion("1. VIGA W", C.campos_viga(), C.derivados_viga()),
        seccion("2. COLUMNA HSS", C.campos_hss() + [campo("dos_lados", "Vigas a ambos lados (conexión en cruz)", "No", options=C.SI_NO)],
                C.derivados_hss()),
        seccion("3. SOLDADURA DE LAS ALAS", [
            campo("al_tipo", "Soldadura ala – HSS", "CJP (desarrolla el ala)", options=["CJP (desarrolla el ala)", "Filete"]),
            campo("al_w", "Filete de ala (si no es CJP)", 10, "mm")]),
        seccion("4. PLACA SIMPLE DE CORTE", C.campos_placa_corte()),
    ],
    combos=tabla_combos([("nombre", "Combinación"), ("M", "Mu viga (Tonf·m)"), ("V", "Vu viga (Tonf)"),
                         ("P", "Pu HSS (Tonf) (+) compresión"), ("Mc", "Mu HSS (Tonf·m)")],
                        [{"nombre": "1.2D+1.6L", "M": 3, "V": 4, "P": 40, "Mc": 1}]),
    notas=["Alcance de la Design Guide 24: SOLO cargas no sísmicas. Para pórticos especiales/intermedios a momento use una conexión precalificada (AISC 358).",
           "La guía advierte que esta conexión rara vez desarrolla la resistencia a flexión de la viga W: lo gobierna la pared del HSS (K1-2).",
           "P y Mc (compresión y momento en el HSS) solo intervienen en el factor Qf de las paredes laterales (K1-5 y K1-6, Ec. K2-10 y K2-12).",
           "Alas con CJP: se asume que la soldadura desarrolla el ala (no se verifica). Con filete se verifica Ff contra 2 filetes de longitud bf (conservador).",
           "Área y módulo del HSS aproximados sin radios de esquina; Fc = Fy en U."])


def global_fn(h, I):
    P = C.hss_y_viga(I)
    bd, bbf, btw, btf, W, D, t = (P[k] for k in ("bd", "bbf", "btw", "btf", "W", "D", "t"))
    hFy, hFu, bFy, bFu = P["hFy"], P["hFu"], P["bFy"], P["bFu"]
    FEXX = aisc.ELECTRODOS[I["sd_elec"]]
    beta = bbf / W
    brazo = bd - btf
    h.sec("1. VIGA")
    Zx = bbf * btf * (bd - btf) + btw * (bd - 2 * btf) ** 2 / 4
    phiMp = h.v("φMp", "Flexión de la viga (arriostrada): 0.90·Fy·Zx", 0.9 * bFy * Zx, "M")
    laminado = I["vg_perfil"].startswith("W")
    phiv, cv = _cv((bd - 2 * btf) / btw, bFy, laminado)
    phiVn = h.v("φVn", "Cortante del alma (G2.1)", phiv * 0.6 * bFy * bd * btw * cv, "F")
    h.sec("2. PLACA TRANSVERSAL SOBRE EL HSS (DG24 Tabla 7-2)")
    h.v("β", "bf/B", beta, "")
    h.v("B/t", "Esbeltez de la pared cargada", W / t, "")
    R12 = h.v("φRn", "K1-2: fluencia local del ala: φ·mín(10/(B/t)·Fy·t·bf ; Fyp·tf·bf)", aisc.hss_flujo_placa(hFy, t, W, bbf, bFy, btf), "F")
    punz = 0.85 * W <= bbf <= W - 2 * t
    R13 = h.v("φRn", "K1-3: punzonamiento (aplica si 0.85B ≤ bf ≤ B − 2t)", aisc.hss_punzonamiento(hFy, t, W, bbf, btf), "F") if punz else None
    lado = beta >= 0.999
    R14 = h.v("φRn", "K1-4: fluencia de paredes laterales (bf = B), N = tf", aisc.hss_pared_fluencia(hFy, t, btf), "F") if lado else None
    A, S = aisc.hss_props(W, D, t)
    h.v("A, S", "Área / módulo elástico del HSS (aprox., sin radios)", A, "A")
    h.v("Mf", "Brazo de momento d − tf", brazo, "Lc")
    Rfl = R12 if R13 is None else min(R12, R13)
    h.v("φMn,K", "Momento que transmite la conexión: mín(K1-2, K1-3)·(d − tf)", Rfl * brazo, "M")
    wtype = I["al_tipo"] != "Filete" and I["al_tipo"].startswith("CJP")
    wl = I["al_w"] / 10
    Rwf = None if wtype else aisc.rn_filete(FEXX, wl, 2 * bbf)
    if Rwf:
        h.v("φRn", "Filetes ala–HSS: 2 líneas de longitud bf (θ = 0°, conservador)", Rwf, "F")
    # límites de aplicabilidad
    h.chk(C.G_DET, "Ala sobre la parte plana: bf ≤ B − 3t", "DG24 Ej. 4.3", bbf, W - 3 * t, "Lc")
    h.chk(C.G_DET, "Límite: 0.25 ≤ bf/B ≤ 1.0", "Tabla 7-2A", 0, 1, "", ratio=max(0.25 / beta, beta))
    h.chk(C.G_DET, "Límite: B/t ≤ 35", "Tabla 7-2A (K1.3b)", W / t, 35, "")
    h.chk(C.G_DET, "Límite: Fy del HSS ≤ 52 ksi", "Tabla 7-2A (K1.2)", hFy, 52 * KSI, "S")
    h.chk(C.G_DET, "Límite: Fy/Fu del HSS ≤ 0.8", "Tabla 7-2A (K1.2)", hFy / hFu, 0.8, "")
    h.chk(C.G_DET, "Límite: Fy/Fu de la viga ≤ 0.8", "Tabla 7-2A (K1.2)", bFy / bFu, 0.8, "")
    h.chk(C.G_DET, "Límite: Fy de la viga ≤ 52 ksi", "Tabla 7-2A (K1.2)", bFy, 52 * KSI, "S")
    gp = C.placa_corte_global(h, I, P)
    ctx = {"derivados": C.derivados(P), "vars": {"bd": bd, "bbf": bbf, "btw": btw, "btf": btf, "W": W, "D": D, "t": t, "n": gp["n"],
                                                   "s": gp["s"], "lev": gp["lev"], "leh": gp["leh"], "tp": gp["tp"], "w": gp["w"], "a": gp["a"],
                                                   "db": gp["p"]["db"], "L": gp["L"]},
           "g": dict(brazo=brazo, phiMp=phiMp, phiVn=phiVn, R12=R12, R13=R13, R14=R14, A=A, S=S, hFy=hFy, beta=beta, lado=lado,
                     dos=I["dos_lados"] == "Sí", Rwf=Rwf, gp=gp, btf=btf, W=W, D=D, t=t)}
    return ctx


def combo_fn(h, ctx, c, I):
    g = ctx["g"]
    Mu, Vu = abs(float(c.get("M") or 0)) * 1e5, abs(float(c.get("V") or 0)) * 1e3
    Pu, Mc = float(c.get("P") or 0) * 1e3, abs(float(c.get("Mc") or 0)) * 1e5
    h.sec(f"COMBINACIÓN {c['nombre']}")
    Ff = h.v("Ff", "Fuerza en el ala: Mu/(d − tf)", Mu / g["brazo"], "F")
    U = max(Pu, 0) / (g["A"] * g["hFy"]) + Mc / (g["S"] * g["hFy"])
    Qf = aisc.hss_Qf(U, g["beta"], True)
    h.v("U", "Utilización del HSS: Pr/(A·Fc) + Mr/(S·Fc), Fc = Fy (K2-12)", U, "")
    h.v("Qf", "Factor de esfuerzo en la pared (K2-10): mín(1.3 − 0.4·U/β ; 1)", Qf, "")
    G = C.G_HSS
    h.chk(C.G_VIGA, "Flexión de la viga: Mu ≤ φMp", "F2", Mu, g["phiMp"], "M")
    h.chk(C.G_VIGA, "Cortante del alma de la viga", "G2.1", Vu, g["phiVn"], "F")
    h.chk(G, "K1-2: fluencia local del ala (distribución desigual)", "Spec. K1-2", Ff, g["R12"], "F")
    h.chk(G, "K1-3: punzonamiento de la pared", "Spec. K1-3", Ff, g["R13"] or 1.0, "F", activo=g["R13"] is not None)
    h.chk(G, "K1-4: fluencia de las paredes laterales (bf = B)", "Spec. K1-4", Ff, g["R14"] or 1.0, "F", activo=g["lado"])
    R15 = aisc.hss_pared_aplastamiento(g["hFy"], g["t"], g["D"], g["btf"], Qf)
    R16 = aisc.hss_pared_pandeo(g["hFy"], g["t"], g["D"], Qf)
    h.chk(G, "K1-5: aplastamiento de paredes laterales (ala a compresión, bf = B)", "Spec. K1-5", Ff, R15, "F", activo=g["lado"] and not g["dos"])
    h.chk(G, "K1-6: pandeo de paredes laterales (vigas a ambos lados, bf = B)", "Spec. K1-6", Ff, R16, "F", activo=g["lado"] and g["dos"])
    h.chk(G, "Filetes de las alas al HSS", "J2.4", Ff, g["Rwf"] or 1.0, "F", activo=g["Rwf"] is not None)
    C.placa_corte_combo(h, g["gp"], Vu)


_MOD = Modulo(SPEC, global_fn, combo_fn)
calcular = _MOD.calcular
CAT = _MOD.CAT
