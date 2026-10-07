"""Unión SIMPLE a cortante de viga W a columna RHS mediante una sola placa lateral soldada a la cara — CIDECT Design Guide 9, §5.3 y ejemplo 5.3.1.

Criterio propio de la guía (ec. 5.1/5.2, Sherman 1995): para evitar el desgarro de la pared de la RHS por el giro del extremo de la viga, la placa debe ser
más débil que la pared:  φ1·fp,y·tp ≤ 2·φ2·(0.6·fc,u)·tc   (φ1 = 0.9 fluencia, φ2 = 0.75 punzonamiento)   ⇒   tp ≤ (fc,u/fp,y)·tc.
Aplica solo a paredes NO esbeltas:  (bc − 4tc)/tc ≤ 1.4·√(E/fc,y).
Estados límite del ejemplo 5.3.1 (reproducidos con AISC 360-16 en lugar de CSA S16): corte de pernos, aplastamiento, corte de las paredes laterales
(2·φ·Lp·tc·0.6fy, φ = 0.9), ruptura neta por corte y por bloque de cortante de la placa, fluencia por corte de la placa y filetes por ambos lados.
Se reutiliza además la placa de corte del Manual AISC Parte 10 (punzonamiento de la pared, Ec. 10-7a) de `hss_comun`.
No se verifica el momento de la excentricidad sobre la soldadura (la guía tampoco: "no se ha realizado la comprobación del efecto producido por el momento flector
en la soldadura") salvo el punzonamiento del Manual; sí se informa a·V como momento de apoyo.
Límites: columnas CHS (§5.3.2) y placa en el vértice (§5.3.3) no se tratan.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import aisc  # noqa: E402
import hss_comun as C  # noqa: E402
from handmod import Modulo, campo, seccion, spec, tabla_combos  # noqa: E402
from wuf.engine import _cv  # noqa: E402

G_CID = "CRITERIO CIDECT 9 (§5.3)"
G_VIGA = C.G_VIGA
SPEC = spec(
    "UNIÓN SIMPLE VIGA – COLUMNA RHS CON UNA SOLA PLACA A CORTANTE",
    "CIDECT Design Guide 9 (§5.3, ec. 5.2, ej. 5.3.1)  ·  AISC 360-16 J2, J3, J4  ·  Manual AISC Parte 10  ·  Unidades: Tonf, mm, kgf/cm²",
    [
        seccion("DATOS GENERALES", [campo("DIS_C7", "Proyecto", "Edificio — ejemplo"), campo("DIS_C8", "Elemento / nudo", "Viga secundaria eje 2"),
                                    campo("lim_verde", "Límite verde / amarillo (ratio)", 0.9)]),
        seccion("1. VIGA W", C.campos_viga(), C.derivados_viga()),
        seccion("2. COLUMNA RHS", C.campos_hss(defecto="ARMADO (flejes soldados)", dims=(203, 203, 7.95)), C.derivados_hss()),
        seccion("3. PLACA SIMPLE DE CORTE", C.campos_placa_corte(n=4, s=70, lev=65, leh=50, tp=10, a=70, w=5)),
    ],
    combos=tabla_combos([("nombre", "Combinación"), ("V", "Vu viga (Tonf)")], [{"nombre": "1.2D+1.6L", "V": 22.0}]),
    notas=["Ejemplo 5.3.1 de la guía: W410×39 (Grado 350W) a RHS 203×203×8 con placa de 10 mm, 4 pernos M22 A325 y filetes de 5 mm; V* = 484 kN.",
           "La guía usa CSA S16 (φ = 0.67 pernos, 0.9 fluencia, 0.75 rotura); los estados límite se calculan con AISC 360-16, por lo que las capacidades difieren algo.",
           "La unión se considera articulada: la excentricidad de la placa solo se verifica con el punzonamiento (Manual Ec. 10-7a).",
           "Se recomienda arriostrar lateralmente las vigas largas sin arriostrar cerca de la unión (distorsión de la placa por torsión de la viga)."])


def global_fn(h, I):
    P = C.hss_y_viga(I)
    bd, bbf, btw, btf, W, D, t = (P[k] for k in ("bd", "bbf", "btw", "btf", "W", "D", "t"))
    hFy, hFu, bFy = P["hFy"], P["hFu"], P["bFy"]
    pFy, pFu = aisc.ACEROS[I["sp_acero"]]
    tp = I["sp_t"] / 10
    h.sec("1. VIGA")
    laminado = I["vg_perfil"].startswith("W")
    phiv, cv = _cv((bd - 2 * btf) / btw, bFy, laminado)
    phiVn = h.v("φVn", "Cortante del alma de la viga (G2.1)", phiv * 0.6 * bFy * bd * btw * cv, "F")
    h.sec("2. CRITERIO DE LA GUÍA CIDECT 9 (ec. 5.2)")
    esb = (W - 4 * t) / t
    lim = 1.4 * math.sqrt(aisc.E / hFy)
    h.v("(bc−4t)/t", "Esbeltez de la zona plana de la cara de la RHS", esb, "")
    h.v("tp,máx", "Espesor máximo de placa: (fc,u/fp,y)·tc  (ec. 5.2)", hFu / pFy * t, "Lc")
    ctxg = C.placa_corte_global(h, I, P)
    L = ctxg["L"]
    Rwall = h.v("φRn", "Corte de las paredes laterales adyacentes a las soldaduras: 2·0.9·Lp·tc·0.6·fy", 2 * 0.9 * L * t * 0.6 * hFy, "F")
    h.chk(G_CID, "Pared NO esbelta: (bc − 4t)/t ≤ 1.4·√(E/fc,y)", "CIDECT 9 §5.3", esb, lim, "")
    h.chk(G_CID, "Espesor de placa: tp ≤ (fc,u/fp,y)·tc", "CIDECT 9 ec. 5.2", tp, hFu / pFy * t, "Lc")
    ctx = {"derivados": C.derivados(P),
           "vars": {"bd": bd, "bbf": bbf, "btw": btw, "btf": btf, "W": W, "D": D, "t": t, "n": ctxg["n"], "s": ctxg["s"], "lev": ctxg["lev"],
                    "leh": ctxg["leh"], "tp": tp, "w": ctxg["w"], "a": ctxg["a"], "db": ctxg["p"]["db"], "L": L},
           "g": dict(phiVn=phiVn, Rwall=Rwall, gp=ctxg)}
    return ctx


def combo_fn(h, ctx, c, I):
    g = ctx["g"]
    Vu = abs(float(c.get("V") or 0)) * 1e3
    h.sec(f"COMBINACIÓN {c['nombre']}")
    h.v("Vu·a", "Momento de excentricidad sobre la cara de la RHS (informativo)", Vu * g["gp"]["a"], "M")
    h.chk(G_VIGA, "Cortante del alma de la viga", "G2.1", Vu, g["phiVn"], "F")
    h.chk(G_CID, "Corte de las paredes laterales de la RHS (2 planos)", "CIDECT 9 ej. 5.3.1", Vu, g["Rwall"], "F")
    C.placa_corte_combo(h, g["gp"], Vu)


_MOD = Modulo(SPEC, global_fn, combo_fn)
calcular = _MOD.calcular
CAT = _MOD.CAT
