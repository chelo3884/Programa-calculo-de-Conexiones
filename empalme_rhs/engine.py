"""Empalme de columna RHS con placas de extremo atornilladas en obra, pernos en los cuatro lados — CIDECT Design Guide 9, §11.1.1.2 (ecs. 11.3–11.10).

Modelo de elementos en T de AISC HSS Connections Manual (1997), modificado por Willibald et al. (2002, 2003):
    Nb* ≥ T (tracción por perno sin palanca)      a' = a + db/2 (a ≤ 1.25b)      b' = b − db/2      ρ = b'/a'
    β' = (1/ρ)·(Nb*/T − 1)      δ = 1 − dh/p      α' = 1 si β' ≥ 1, si no (1/δ)·β'/(1 − β') acotado a [0, 1]
    t_nec = √( 4·T·b' / (φ1·p·fp,y·(1 + δ·α')) ),   φ1 = 0.9
Tracción por perno (criterio propio, la guía solo da N⁺/n): T = N/n + |Mx|·ymáx/Σy² + |My|·xmáx/Σx² (grupo elástico; sin contacto en compresión → conservador).
Pernos: φ·Fnt·Ab sin palanca (la palanca ya está en t_nec), interacción tracción–corte (J3.7) con V/n por perno; aplastamiento en la placa.
Soldadura RHS–placa: filete perimetral; la fuerza axial y el corte se reparten en la longitud total (conservador, sin el factor de dirección).
No hay ejemplo resuelto en la guía para RHS (solo para columna circular): se verificó por recálculo independiente (tests/test_cidect9_conexiones.py).
Límites: no se verifica la RHS (el usuario debe comprobar la columna), ni la placa a flexión por compresión (se asume contacto), ni empalmes soldados (§11.1.3–11.1.4).
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import aisc  # noqa: E402
import hss_comun as C  # noqa: E402
from handmod import Modulo, campo, seccion, spec, tabla_combos  # noqa: E402

G_P, G_B, G_W = "PLACA DE EXTREMO (CIDECT 9 §11.1.1.2)", "PERNOS", "SOLDADURA RHS – PLACA"
SPEC = spec(
    "EMPALME DE COLUMNA RHS — PLACAS DE EXTREMO ATORNILLADAS",
    "CIDECT Design Guide 9 (§11.1.1.2, ecs. 11.3–11.10)  ·  AISC 360-16 J2, J3  ·  Unidades: Tonf, Tonf·m, mm, kgf/cm²",
    [
        seccion("DATOS GENERALES", [campo("DIS_C7", "Proyecto", "Edificio — ejemplo"), campo("DIS_C8", "Elemento / nudo", "Empalme columna C3, nivel 2"),
                                    campo("lim_verde", "Límite verde / amarillo (ratio)", 0.9)]),
        seccion("1. COLUMNA RHS", C.campos_hss(defecto="ARMADO (flejes soldados)", dims=(200, 200, 10)), C.derivados_hss()),
        seccion("2. PLACA DE EXTREMO", [
            campo("pl_acero", "Acero de la placa", "A36", options=C.ACEROS_VIGA),
            campo("pl_B", "Ancho de la placa B (paralelo a la cara B de la RHS)", 360, "mm"),
            campo("pl_H", "Alto de la placa H", 360, "mm"), campo("pl_t", "Espesor de la placa", 19, "mm")]),
        seccion("3. PERNOS (4 lados)", [
            campo("pn_grado", "Grado de pernos", "A325-N (roscas incl.)", options=list(aisc.PERNOS)),
            campo("pn_diam", "Diámetro de pernos", '7/8"', options=aisc.DIAMETROS),
            campo("pn_nx", "Pernos por lado en las caras de ancho B (arriba y abajo)", 2), campo("pn_ny", "Pernos por lado en las caras de alto H (izq. y der.)", 2),
            campo("pn_b", "b — distancia de la cara exterior de la RHS al eje del perno", 45, "mm")]),
        seccion("4. SOLDADURA RHS – PLACA", [campo("sd_w", "Filete (cateto)", 8, "mm"), campo("sd_elec", "Electrodo", "E70XX", options=list(aisc.ELECTRODOS))]),
    ],
    combos=tabla_combos([("nombre", "Combinación"), ("N", "N axial mayorada (Tonf, + tracción)"), ("Mx", "Mx (Tonf·m)"), ("My", "My (Tonf·m)"), ("V", "Vu (Tonf)")],
                        [{"nombre": "Tracción pura", "N": 30.0, "Mx": 0, "My": 0, "V": 0},
                         {"nombre": "Flexión + corte", "N": -20.0, "Mx": 2.0, "My": 0, "V": 3.0}]),
    notas=["Método de la guía CIDECT 9 §11.1.1.2 (modelo AISC modificado, Willibald et al. 2003). La guía solo define la carga por perno N⁺/n; la tracción por momento es criterio propio (grupo elástico).",
           "Las combinaciones sin tracción en ningún perno omiten la verificación de placa y de tracción de pernos. Las placas del empalme deben, en sismo, desarrollar la resistencia de la columna (§11.1.4).",
           "a se toma como (B − ancho de RHS)/2 − b en cada dirección; p = mín(B/nx; H/ny); a limitado a 1.25b.",
           "Distancia b ≥ cateto + db/2 + 10 mm (holgura de llave y soldadura): criterio propio de detallado."])


def _coords(L, n):
    return [-L / 2 + (i + 0.5) * L / n for i in range(n)]


def global_fn(h, I):
    I = dict(I)
    W, D, t = C.geom_hss(I)
    hFy, hFu = aisc.ACEROS[I["hss_acero"]]
    pFy, pFu = aisc.ACEROS[I["pl_acero"]]
    B, H, tp = I["pl_B"] / 10, I["pl_H"] / 10, I["pl_t"] / 10
    nx, ny, b, w = int(I["pn_nx"]), int(I["pn_ny"]), I["pn_b"] / 10, I["sd_w"] / 10
    p = aisc.perno(I["pn_diam"], I["pn_grado"])
    FEXX = aisc.ELECTRODOS[I["sd_elec"]]
    n = 2 * (nx + ny)
    ax, ay = (B - W) / 2 - b, (H - D) / 2 - b
    a = min(ax, ay)
    pit = min(B / nx, H / ny)
    # coordenadas de los pernos respecto al eje de la columna: caras de ancho B (y = ±(D/2 + b)) y caras de alto H (x = ±(W/2 + b))
    xs = [x for x in _coords(B, nx)] * 2 + [s * (W / 2 + b) for s in (1, -1) for _ in range(ny)]
    ys = [s * (D / 2 + b) for s in (1, -1) for _ in range(nx)] + [y for y in _coords(H, ny)] * 2
    sx2, sy2 = sum(x * x for x in xs), sum(y * y for y in ys)
    xm, ym = max(abs(x) for x in xs), max(abs(y) for y in ys)
    h.sec("1. GEOMETRÍA")
    h.v("n", "Número total de pernos 2·(nx + ny)", n, "")
    h.v("a", "Voladizo de la placa más allá de la línea de pernos (mín. de ambas direcciones)", a, "Lc")
    h.v("p", "Paso efectivo por lado: mín(B/nx; H/ny)", pit, "Lc")
    h.v("Σx²", "Σx² del grupo de pernos (cm²)", sx2, "")
    h.v("Σy²", "Σy² del grupo de pernos (cm²)", sy2, "")
    h.sec("2. PERNOS")
    Nb = h.v("Nb*", "Tracción del perno sin palanca: φ·Fnt·Ab (J3.6)", 0.75 * p["Fnt"] * p["Ab"], "F")
    Rv = h.v("φrnv", "Corte por perno: φ·Fnv·Ab", aisc.rn_corte_perno(p["Fnv"], p["Ab"]), "F")
    Rbr = h.v("φrn,ap", "Aplastamiento en la placa (conservador: Lc = a − dh/2)", aisc.rn_aplastamiento(p["db"], tp, pFu, max(a - p["dh"] / 2, 0.1)), "F")
    h.sec("3. SOLDADURA")
    Lw = 2 * (W + D)
    Rw = h.v("φRn", "Filete perimetral exterior: 0.75·0.6·FEXX·0.707·w·2(B+H) de la RHS", aisc.rn_filete(FEXX, w, Lw), "F")
    h.chk(C.G_DET, "Filete ≥ mínimo J2.4 (placa gruesa)", "Tabla J2.4", (3 if tp * 10 <= 6 else 5 if tp * 10 <= 13 else 6 if tp * 10 <= 19 else 8) / 10, w, "Lc")
    h.chk(C.G_DET, "Filete ≤ espesor de la RHS", "Buena práctica", w, t, "Lc")
    h.chk(C.G_DET, "Borde a ≥ mínimo J3.4", "J3.4", p["edge"], a, "Lc")
    h.chk(C.G_DET, "b ≥ cateto + db/2 + 10 mm", "Criterio propio", w + p["db"] / 2 + 1.0, b, "Lc")
    h.chk(C.G_DET, "Paso entre pernos ≥ 3·db", "J3.3", 3 * p["db"], pit, "Lc")
    ctx = {"derivados": {"hss_W_mm": W * 10, "hss_D_mm": D * 10, "hss_t_mm": t * 10, "hss_bt": W / t},
           "vars": {"W": W, "D": D, "t": t, "B": B, "H": H, "tp": tp, "b": b, "a": a, "nx": nx, "ny": ny, "db": p["db"], "w": w, "n": n},
           "g": dict(Nb=Nb, Rv=Rv, Rbr=Rbr, Rw=Rw, n=n, a=a, b=b, db=p["db"], dh=p["dh"], pit=pit, pFy=pFy, tp=tp, sx2=sx2, sy2=sy2, xm=xm, ym=ym, p=p,
                     A=aisc.hss_props(W, D, t)[0], hFy=hFy)}
    return ctx


def combo_fn(h, ctx, c, I):
    g = ctx["g"]
    N = float(c.get("N") or 0) * 1e3
    Mx, My = abs(float(c.get("Mx") or 0)) * 1e5, abs(float(c.get("My") or 0)) * 1e5
    V = abs(float(c.get("V") or 0)) * 1e3
    n = g["n"]
    h.sec(f"COMBINACIÓN {c['nombre']}")
    T = N / n + Mx * g["ym"] / g["sy2"] + My * g["xm"] / g["sx2"]
    h.v("T", "Tracción en el perno más cargado: N/n + Mx·ymáx/Σy² + My·xmáx/Σx²", T, "F")
    tr = T > 0
    r = aisc.cidect_empalme_tnec(g["Nb"], max(T, 1e-6), g["a"], g["b"], g["db"], g["dh"], g["pit"], g["pFy"]) if tr else None
    if tr:
        h.v("a', b'", "a' = a + db/2 (a ≤ 1.25b); b' = b − db/2", r["a1"], "Lc")
        h.v("ρ, β'", "ρ = b'/a'; β' = (Nb*/T − 1)/ρ", r["beta"], "")
        h.v("δ, α'", "δ = 1 − dh/p; α' (efecto palanca, 0..1)", r["alfa"], "")
        h.v("t_nec", "Espesor necesario (ec. 11.10, φ1 = 0.9)", r["t"], "Lc")
    h.chk(G_P, "Espesor de la placa: t ≥ t_nec", "CIDECT 9 ec. 11.10", r["t"] if tr else 0, g["tp"], "Lc", activo=tr)
    h.chk(G_B, "Tracción del perno: T ≤ Nb* (sin palanca)", "CIDECT 9 ec. 11.3 · J3.6", T, g["Nb"], "F", activo=tr)
    frv = V / n / g["p"]["Ab"]
    Fnt1 = min(g["p"]["Fnt"], 1.3 * g["p"]["Fnt"] - g["p"]["Fnt"] / (0.75 * g["p"]["Fnv"]) * frv)
    h.chk(G_B, "Tracción + corte combinados (J3.7): T ≤ φ·F'nt·Ab", "J3.7", T, 0.75 * Fnt1 * g["p"]["Ab"], "F", activo=tr and V > 0)
    h.chk(G_B, "Corte por perno: V/n ≤ φrnv", "J3.6", V / n, g["Rv"], "F", activo=V > 0)
    h.chk(G_B, "Aplastamiento en la placa: V/n", "J3.10", V / n, g["Rbr"], "F", activo=V > 0)
    h.chk(G_W, "Filete perimetral: resultante de N⁺ y V", "J2.4", math.hypot(max(N, 0), V), g["Rw"], "F", activo=max(N, 0) > 0 or V > 0)


_MOD = Modulo(SPEC, global_fn, combo_fn)
calcular = _MOD.calcular
CAT = _MOD.CAT
