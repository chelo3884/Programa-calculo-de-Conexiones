"""Conexión de momento viga W – columna RHS con DIAFRAGMAS EXTERNOS (CIDECT Design Guide 9, §8.6 y Tabla 8.3).

Resistencia última del ala (Tabla 8.3, ec. 2, Kamba 2001 / Tabuchi et al. 1985; fórmulas de las recomendaciones AIJ):
    Pb,f* = 3.17·(tc/bc)^(2/3)·(td/bc)^(2/3)·((tc + hd)/bc)^(1/3)·bc²·fd,u        (sin coeficiente de resistencia adicional)
    campo de validez: 17 ≤ bc/tc ≤ 67 · 0.07 ≤ hd/bc ≤ 0.4 · 0.75 ≤ td/tc ≤ 2.0 · θ ≤ 30° (45° con placas laterales)
                      (bc/2 + hd)/td ≤ 240/√fd,y   (fd,y en N/mm²)
Momento resistente (ec. 8.22):  Mj,cf* = Pb,f*·(hb − tb,f)
Momento requerido por sobrerresistencia (ec. 8.23, 8.8):  Mcf = L/(L − Lnervio)·α·Mpl,  α = 1.2 recomendado (1.1 en zonas de baja sismicidad, §8.8)

LÍMITES (la guía no trae un ejemplo resuelto de diafragma externo; la fórmula se verifica por recálculo, no contra un ejemplo):
  · La guía las da como resistencias ÚLTIMAS para diseño por capacidad (Mj,cf* ≥ α·Mpl). Para comparar con cargas factoradas por combinación se usa un
    factor φ definido por el usuario (por defecto 0.75: CRITERIO PROPIO, la guía no lo especifica).
  · La sección del diafragma bajo el ala de la viga y el corte del alma son verificaciones propias, no de la guía.
  · Solo columna RHS (la ec. 1 para CHS no está implementada); sin placas laterales (ecs. 8.24–8.27).
  · Los ensayos cubren alas de viga y paredes de columna ≤ 16 mm y diafragmas ≤ 22 mm; se avisa si se supera.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import aisc  # noqa: E402
import hss_comun as C  # noqa: E402
from handmod import Modulo, campo, seccion, spec, tabla_combos  # noqa: E402
from wuf.engine import _cv  # noqa: E402

G_D, G_V = "DIAFRAGMA EXTERNO (CIDECT 9 §8.6)", "VIGA"
SPEC = spec(
    "CONEXIÓN DE MOMENTO VIGA W – COLUMNA RHS CON DIAFRAGMAS EXTERNOS",
    "CIDECT Design Guide 9 (§8.6, Tabla 8.3, ecs. 8.22–8.23)  ·  AISC 360-16 J, G2, F2  ·  Unidades: Tonf, Tonf·m, mm, kgf/cm²",
    [
        seccion("DATOS GENERALES", [campo("DIS_C7", "Proyecto", "Edificio — ejemplo"), campo("DIS_C8", "Elemento / nudo", "Nudo C-2 nivel 3"),
                                    campo("lim_verde", "Límite verde / amarillo (ratio)", 0.9)]),
        seccion("1. VIGA W (igual a ambos lados)", C.campos_viga(defecto="W12X26"), C.derivados_viga()),
        seccion("2. COLUMNA RHS", C.campos_hss(defecto="ARMADO (flejes soldados)", dims=(300, 300, 12)), C.derivados_hss()),
        seccion("3. DIAFRAGMAS EXTERNOS", [
            campo("dx_acero", "Acero del diafragma", "A572 Gr50", options=C.ACEROS_VIGA),
            campo("dx_td", "Espesor del diafragma td", 20, "mm"),
            campo("dx_hd", "hd — saliente del diafragma desde la cara de la columna", 80, "mm"),
            campo("dx_theta", "θ — pendiente del diafragma (≤ 30°)", 28, "°"),
            campo("dx_lner", "Lnervio — cara de la columna → extremo del diafragma", 300, "mm"),
            campo("dx_placas", "Con placas laterales (θ hasta 45°)", "No", options=C.SI_NO),
            campo("dx_sold", "Soldadura diafragma – columna", "CJP", options=["CJP", "Filete"]),
            campo("dx_w", "Filete diafragma – columna (guía: ≈ td/2)", 8, "mm")]),
        seccion("4. SOBRERRESISTENCIA Y CRITERIO", [
            campo("dx_L", "L — cara de la columna → punto de inflexión de la viga", 3.0, "m"),
            campo("dx_alfa", "α — coeficiente de sobrerresistencia (1.2 sísmico; 1.1 baja sismicidad §8.8)", 1.2),
            campo("dx_phi", "φ aplicado a Mj,cf* en las combinaciones (criterio propio)", 0.75)]),
        seccion("5. PLACA SIMPLE DE CORTE", C.campos_placa_corte(n=3, s=80, lev=38.1, leh=50.8, tp=9.5, a=76.2, w=6.35)[:8] + [
            campo("pn_grado", "Grado de pernos", "A325-N (roscas incl.)", options=list(aisc.PERNOS)),
            campo("pn_diam", "Diámetro de pernos", '3/4"', options=aisc.DIAMETROS), campo("sd_elec", "Electrodo", "E70XX", options=list(aisc.ELECTRODOS))]),
    ],
    combos=tabla_combos([("nombre", "Combinación"), ("M", "Mu en la cara de la columna (Tonf·m)"), ("V", "Vu de la viga (Tonf)")],
                        [{"nombre": "1.2D+1.6L", "M": 6, "V": 4}]),
    notas=["CIDECT 9 §8.6: fórmulas de las Recomendaciones AIJ (Japón) para diafragmas externos; los ensayos son con alas soldadas o atornilladas a los diafragmas.",
           "La guía NO trae un ejemplo resuelto de diafragma externo: la ecuación se comprobó por recálculo, no contra un ejemplo impreso.",
           "Pb,f* es una resistencia última sin factor de resistencia: úsela con el requisito de sobrerresistencia Mj,cf* ≥ α·Mpl (diseño por capacidad, ec. 8.8). "
           "El φ por combinación (por defecto 0.75) es un criterio propio.",
           "Soldaduras: la guía recomienda CJP (o filete de ≈ td/2 en el centro del ala, sin soldar los vértices entrantes, con radio ≥ 10 mm) y, en pórticos especiales, "
           "categoría A de exigencia sísmica a la soldadura. No sustituye la precalificación AISC 358."])


def global_fn(h, I):
    P = C.hss_y_viga(I)
    bd, bbf, btw, btf, bc, tc = (P[k] for k in ("bd", "bbf", "btw", "btf", "W", "t"))
    bFy, bFu = P["bFy"], P["bFu"]
    dFy, dFu = aisc.ACEROS[I["dx_acero"]]
    td, hd, th = I["dx_td"] / 10, I["dx_hd"] / 10, float(I["dx_theta"])
    Ln, L = I["dx_lner"] / 10, float(I["dx_L"]) * 100
    h.sec("1. VIGA")
    Zx = bbf * btf * (bd - btf) + btw * (bd - 2 * btf) ** 2 / 4
    Mpl = h.v("Mpl", "Momento plástico de la viga: Fy·Zx", bFy * Zx, "M")
    phiMp = h.v("φMp", "Resistencia a flexión (F2, arriostrada): 0.90·Fy·Zx", 0.9 * bFy * Zx, "M")
    phiv, cv = _cv((bd - 2 * btf) / btw, bFy, I["vg_perfil"].startswith("W"))
    phiVn = h.v("φVn", "Cortante del alma (G2.1)", phiv * 0.6 * bFy * bd * btw * cv, "F")
    h.sec("2. DIAFRAGMA EXTERNO (Tabla 8.3, ec. 2)")
    Pbf = h.v("Pb,f*", "Resistencia última del ala: 3.17·(tc/bc)^(2/3)·(td/bc)^(2/3)·((tc+hd)/bc)^(1/3)·bc²·fd,u", aisc.cidect_dext_Pbf(bc, tc, td, hd, dFu), "F")
    brazo = bd - btf
    Mj = h.v("Mj,cf*", "Momento resistente en la cara de la columna (8.22): Pb,f*·(hb − tb,f)", Pbf * brazo, "M")
    alfa = float(I["dx_alfa"])
    Mreq = h.v("Mcf,req", "Momento requerido por sobrerresistencia (8.23): L/(L − Lnervio)·α·Mpl", L / (L - Ln) * alfa * Mpl, "M") if L > Ln else float("inf")
    v, lim = aisc.cidect_dext_esbeltez(bc, hd, td, dFy)
    h.v("(bc/2+hd)/td", "Esbeltez del saliente del diafragma", v, "")
    # campo de validez y detalles
    th_max = 45.0 if I["dx_placas"] == "Sí" else 30.0
    h.chk(C.G_DET, "Validez: bc/tc ≥ 17", "Tabla 8.3", 17, bc / tc, "")
    h.chk(C.G_DET, "Validez: bc/tc ≤ 67", "Tabla 8.3", bc / tc, 67, "")
    h.chk(C.G_DET, "Validez: hd/bc ≥ 0.07", "Tabla 8.3", 0.07, hd / bc, "")
    h.chk(C.G_DET, "Validez: hd/bc ≤ 0.4", "Tabla 8.3", hd / bc, 0.4, "")
    h.chk(C.G_DET, "Validez: td/tc ≥ 0.75", "Tabla 8.3", 0.75, td / tc, "")
    h.chk(C.G_DET, "Validez: td/tc ≤ 2.0", "Tabla 8.3", td / tc, 2.0, "")
    h.chk(C.G_DET, "Validez: (bc/2 + hd)/td ≤ 240/√fd,y", "Tabla 8.3", v, lim, "")
    h.chk(C.G_DET, "Validez: θ ≤ 30° (45° con placas laterales)", "Tabla 8.3 · §8.6", th, th_max, "")
    h.chk(C.G_DET, "Ensayos: espesor del diafragma ≤ 22 mm", "§8.6 (ensayos RHS)", td * 10, 22, "")
    h.chk(C.G_DET, "Ensayos: ala de viga ≤ 16 mm", "§8.6 (ensayos RHS)", btf * 10, 16, "")
    h.chk(C.G_DET, "Ensayos: pared de la columna ≤ 16 mm", "§8.6 (ensayos RHS)", tc * 10, 16, "")
    tan = math.tan(math.radians(max(th, 1.0)))
    h.chk(C.G_DET, "Lnervio suficiente para la pendiente: ≥ (bc/2 + hd − bf/2)/tanθ", "Geometría", max((bc / 2 + hd - bbf / 2) / tan, 0.0), Ln, "Lc")
    h.chk(C.G_DET, "Lnervio < L (hinge dentro del vano)", "Eq. 8.23", Ln, L, "Lc")
    if I["dx_sold"] == "Filete":
        h.chk(C.G_DET, "Filete diafragma–columna ≈ td/2 (práctica de los ensayos)", "§8.6", td / 2, I["dx_w"] / 10, "Lc")
    # sobrerresistencia (global)
    h.chk(G_D, "Sobrerresistencia: Mj,cf* ≥ L/(L − Lnervio)·α·Mpl", "Ec. 8.8 · 8.22 · 8.23", Mreq, Mj, "M")
    gp = C.placa_corte_global(h, I, P)
    return {"derivados": C.derivados(P), "vars": {"bd": bd, "bbf": bbf, "btw": btw, "btf": btf, "W": bc, "D": bc, "t": tc, "td": td, "hd": hd, "th": th,
                                                    "Ln": Ln, "n": gp["n"], "s": gp["s"], "lev": gp["lev"], "tps": gp["tp"], "a": gp["a"], "db": gp["p"]["db"],
                                                    "L": gp["L"], "leh": gp["leh"], "w": gp["w"]},
            "g": dict(brazo=brazo, phi=float(I["dx_phi"]), Mj=Mj, Pbf=Pbf, phiMp=phiMp, phiVn=phiVn, dFy=dFy, td=td, bbf=bbf, gp=gp)}


def combo_fn(h, ctx, c, I):
    g = ctx["g"]
    Mu, Vu = abs(float(c.get("M") or 0)) * 1e5, abs(float(c.get("V") or 0)) * 1e3
    h.sec(f"COMBINACIÓN {c['nombre']}")
    Ff = h.v("Ff", "Fuerza en el ala: Mu/(d − tf)", Mu / g["brazo"], "F")
    h.chk(G_V, "Flexión de la viga: Mu ≤ φMp", "F2", Mu, g["phiMp"], "M")
    h.chk(G_V, "Cortante del alma de la viga", "G2.1", Vu, g["phiVn"], "F")
    h.chk(G_D, "Mu ≤ φ·Mj,cf* (φ criterio propio)", "Ec. 8.22 (φ propio)", Mu, g["phi"] * g["Mj"], "M")
    h.chk(G_D, "Diafragma bajo el ala: Ff ≤ 0.90·Fyd·td·bf (criterio propio)", "J4.1(a)", Ff, 0.9 * g["dFy"] * g["td"] * g["bbf"], "F")
    C.placa_corte_combo(h, g["gp"], Vu)


_MOD = Modulo(SPEC, global_fn, combo_fn)
calcular = _MOD.calcular
CAT = _MOD.CAT
