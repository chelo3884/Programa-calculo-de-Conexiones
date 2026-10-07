"""Unión viga – columna RHS ATORNILLADA con diafragmas pasantes y ménsula corta (empalme de viga en obra) — CIDECT Design Guide 9, §8.2 y ejemplo 8.2.1.

Criterios de la guía (origen japonés, AIJ / FEMA 350; empalme según Eurocódigo 3, γMb = 1.0 al aplastamiento, γ = 1.25 al corte del perno):
  8.9   Mb,n* = (bf − n/2·dh)·tf·(hb − tf)·fu + (hb − 2tf − x)·x·tw·fy ,  x = (hb − 2tf)/2 − (n·dh/2)·(tf·fu)/(tw·fy)   (sección neta, última fila)
  8.10  Mb,n* ≥ 1.2·Mpl  (sobrerresistencia de la viga)
  8.11  Mcf = L/(L − sl)·Mb,n*   (demanda en la cara de la columna; sl = última fila de pernos a la cara)
  8.12  Mj,cf* = L/(L − sc)·Mb,n* de la ménsula (primera fila de pernos, a sc de la cara)
  8.13/8.14  Mj,cf* = Mb,f,u + Mb,w,u, con Mb,f,u = (bf − n·dh)·tf·(hb − tf)·fu y Mb,w,u = m·Wpl,w,n·fy + Le·tw·(hb − 2tf)·fu/√3,
             m = 4·tf/(hb − 2tf)·√((bc − 2tc)·fc,y/(tw·fb,y))  (ec. 8.5; se limita a m ≤ 1, criterio propio)
  Empalme: Mbs = Σ Fb·brazo, Mbs,cf = L/(L − 180)·Mbs ≥ Mcf; cortante Vbs = Vg + Mcf/L ≤ nº de pernos centrales · Fb,alma.
Aplastamiento del perno (EC3 Tabla 3.4): Fb = k1·αb·fu·d·t, αb = mín(e1/(3d0); p1/(3d0) − 1/4; fub/fu; 1), k1 = mín(2.8·e2/d0 − 1.7; 2.5).
Reproduce el ejemplo 8.2.1 (672, 741, 1031, 781, 191, 972, 716, 751 kN·m; 264 kN y 258 kN). Verificación de deslizamiento (EC3 3.9) para servicio: criterio propio, la guía solo la menciona.
No incluye: desgarro en bloque de las platabandas (la guía da valores EC3 del ejemplo), sección neta de las platabandas, soldaduras de la ménsula al diafragma,
la relación columna fuerte–viga débil, ni el espesor y la flexión del diafragma (§8.1, Tabla 8.3 con diafragma externo, en el módulo hss_dext).
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import aisc  # noqa: E402
import hss_comun as C  # noqa: E402
from handmod import Modulo, campo, seccion, spec, tabla_combos  # noqa: E402

G_V, G_M, G_S = "VIGA (sección neta)", "MÉNSULA CORTA", "EMPALME DE VIGA (EC3)"
SPEC = spec(
    "UNIÓN ATORNILLADA CON DIAFRAGMA PASANTE — VIGA W A COLUMNA RHS (MÉNSULA CORTA + EMPALME)",
    "CIDECT Design Guide 9 (§8.2, ecs. 8.9–8.14, ej. 8.2.1)  ·  Eurocódigo 3 (pernos)  ·  Unidades: Tonf, Tonf·m, mm, kgf/cm²",
    [
        seccion("DATOS GENERALES", [campo("DIS_C7", "Proyecto", "Edificio — ejemplo"), campo("DIS_C8", "Elemento / nudo", "Pórtico sísmico eje B"),
                                    campo("lim_verde", "Límite verde / amarillo (ratio)", 0.9)]),
        seccion("1. VIGA W Y MÉNSULA CORTA (mismo perfil y acero)", [dict(c, default="A36") if c["name"] == "vg_acero" else c for c in C.campos_viga(defecto="ARMADO (flejes soldados)", dims=(500, 200, 10, 16))] + [
            campo("ms_bf", "Ancho de ala de la ménsula corta (con cartelas)", 340, "mm"),
            campo("ms_n", "Orificios en la primera fila de la ménsula (n de 8.9 y 8.13)", 4),
            campo("vg_n", "Orificios en la última fila de la viga (n de 8.9)", 2),
            campo("Zx", "Módulo plástico de la viga Zx (0 = calcular)", 0, "mm³")], C.derivados_viga()),
        seccion("2. COLUMNA RHS", C.campos_hss(defecto="ARMADO (flejes soldados)", dims=(400, 400, 16)), C.derivados_hss()),
        seccion("3. GEOMETRÍA DEL NUDO", [
            campo("L", "L: de la cara de la columna al punto de inflexión", 3800, "mm"),
            campo("sc", "sc: cara de la columna → primera fila de pernos (ménsula)", 70, "mm"),
            campo("sl", "sl: cara de la columna → última fila de pernos (viga)", 355, "mm"),
            campo("sb", "Cara de la columna → inicio de las platabandas de empalme (para Mbs,cf)", 180, "mm"),
            campo("Le", "Le: longitud de soldadura horizontal ménsula–diafragma", 70, "mm")]),
        seccion("4. EMPALME DE VIGA (pernos de alta resistencia, a doble cortante)", [
            campo("pn_d", "Diámetro nominal del perno d", 20, "mm"), campo("pn_d0", "Diámetro del orificio d0", 22, "mm"),
            campo("pn_fub", "Resistencia última del perno fub", 10197, "kgf/cm²"),
            campo("pn_e1", "Distancia al borde e1 (dirección de la fuerza)", 50, "mm"), campo("pn_p1", "Paso entre pernos p1", 60, "mm"),
            campo("pn_e2", "Distancia al borde transversal e2", 50, "mm"),
            campo("nf_e", "Pernos del ala controlados por e1 (primeros)", 2), campo("nf_i", "Pernos del ala controlados por p1 (interiores)", 4),
            campo("nw_m", "Pernos del alma que aportan momento (más alejados)", 2), campo("yw", "Brazo de esos pernos del alma", 240, "mm"),
            campo("nw_v", "Pernos centrales del alma que resisten el cortante", 2),
            campo("mu", "Coeficiente de rozamiento μ (servicio, resistente al deslizamiento)", 0.4)]),
    ],
    combos=tabla_combos([("nombre", "Combinación"), ("Vg", "Cortante gravitacional en la unión Vg (Tonf)"),
                         ("Ms", "Momento de servicio en la cara de la columna (Tonf·m)")],
                        [{"nombre": "Sismo + gravedad", "Vg": 6.42, "Ms": 20.0}]),
    notas=["Alcance: pórticos con diafragmas pasantes y ménsula corta soldada en taller; el empalme de viga se hace en obra con pernos pretensados. Origen: pruebas japonesas (Ochi et al. 1998, Kurobane 2002).",
           "La demanda de momento en la cara de la columna (8.11) se deduce de la resistencia de la viga (diseño por capacidad); no depende de cargas externas. Vg es el cortante gravitacional.",
           "La guía usa el Eurocódigo 3 para el empalme (corte con γ = 1.25; aplastamiento sin factor, para permitir su elongación) y fluencia equilibrada: viga → ménsula → empalme.",
           "El módulo plástico de una viga armada se calcula sin radios de acuerdo (el ejemplo usa el del perfil laminado: 2130 cm³ vs. 2096 cm³).",
           "No se verifican el desgarro en bloque ni la sección neta de las platabandas, ni la soldadura de la ménsula (ver docstring)."])


def _fb(d, d0, t, fu, fub, e1, p1, e2, interior):
    k1 = min(2.8 * e2 / d0 - 1.7, 2.5)
    ab = min((p1 / (3 * d0) - 0.25) if interior else e1 / (3 * d0), fub / fu, 1.0)
    return k1 * ab * fu * d * t


def global_fn(h, I):
    I = dict(I)
    bd, bbf, btw, btf = C.perfil(I["vg_perfil"], I, "vg", C.VIGAS)
    bFy, bFu = aisc.ACEROS[I["vg_acero"]]
    W, D, t = C.geom_hss(I)
    hFy, hFu = aisc.ACEROS[I["hss_acero"]]
    mbf, mn, vn = I["ms_bf"] / 10, int(I["ms_n"]), int(I["vg_n"])
    L, sc, sl, sb, Le = (I[k] / 10 for k in ("L", "sc", "sl", "sb", "Le"))
    d, d0, fub, e1, p1, e2 = I["pn_d"] / 10, I["pn_d0"] / 10, I["pn_fub"], I["pn_e1"] / 10, I["pn_p1"] / 10, I["pn_e2"] / 10
    Zx = float(I["Zx"] or 0) / 1000 or (bbf * btf * (bd - btf) + btw * (bd - 2 * btf) ** 2 / 4)
    hw = bd - 2 * btf
    h.sec("1. SECCIÓN NETA DE LA VIGA (ec. 8.9, última fila de pernos)")

    def mbn(bw, n):
        x = hw / 2 - n * d0 / 2 * btf * bFu / (btw * bFy)
        return (bw - n / 2 * d0) * btf * (bd - btf) * bFu + (hw - x) * x * btw * bFy, x
    Mpl = h.v("Mpl", "Momento plástico de la viga: Zx·Fy", Zx * bFy, "M")
    Mbn, x1 = mbn(bbf, vn)
    h.v("x", "Profundidad auxiliar x de la ec. 8.9", x1, "Lc")
    h.v("Mb,n*", "Capacidad en la sección neta (8.9)", Mbn, "M")
    Mcf = h.v("Mcf", "Demanda en la cara de la columna: L/(L − sl)·Mb,n* (8.11)", L / (L - sl) * Mbn, "M")
    h.sec("2. MÉNSULA CORTA (ecs. 8.12–8.14)")
    Mbn_s, x2 = mbn(mbf, int(mn))
    Mj1 = h.v("Mj,cf* (a)", "Modo (a): área neta en la 1ª fila: L/(L − sc)·Mb,n* (8.12)", L / (L - sc) * Mbn_s, "M")
    Mbfu = h.v("Mb,f,u", "Alas: (bf − n·dh)·tf·(hb − tf)·fu (8.13)", (mbf - mn * d0) * btf * (bd - btf) * bFu, "M")
    m = min(4 * btf / hw * math.sqrt((W - 2 * t) * hFy / (btw * bFy)), 1.0)
    h.v("m", "Coeficiente m (ec. 8.5, ≤ 1)", m, "")
    Mbwu = h.v("Mb,w,u", "Alma: m·Wpl,w,n·fy + Le·tw·(hb − 2tf)·fu/√3 (8.14)", m * btw * hw ** 2 / 4 * bFy + Le * btw * hw * bFu / math.sqrt(3), "M")
    Mj2 = h.v("Mj,cf* (b)", "Modo (b): Mb,f,u + Mb,w,u (8.13 + 8.14)", Mbfu + Mbwu, "M")
    h.sec("3. EMPALME DE LA VIGA (EC3)")
    Vb = h.v("Vb*", "Corte del perno por plano (no roscado): 0.6·fub·A/1.25", 0.6 * fub * math.pi * d ** 2 / 4 / 1.25, "F")
    Fe_f = h.v("Fb,ala,e", "Aplastamiento en ala, controla e1", _fb(d, d0, btf, bFu, fub, e1, p1, e2, False), "F")
    Fi_f = h.v("Fb,ala,i", "Aplastamiento en ala, controla p1", _fb(d, d0, btf, bFu, fub, e1, p1, e2, True), "F")
    Fe_w = h.v("Fb,alma,e", "Aplastamiento en alma, controla e1", _fb(d, d0, btw, bFu, fub, e1, p1, e2, False), "F")
    Fi_w = h.v("Fb,alma,i", "Aplastamiento en alma, controla p1", _fb(d, d0, btw, bFu, fub, e1, p1, e2, True), "F")
    nfe, nfi, nwm, yw, nwv = int(I["nf_e"]), int(I["nf_i"]), int(I["nw_m"]), I["yw"] / 10, int(I["nw_v"])
    Mbs = h.v("Mbs", "Momento resistido por el empalme: (Σ Fb,ala)(hb − tf) + Σ Fb,alma·brazo", (nfe * Fe_f + nfi * Fi_f) * (bd - btf) + nwm * Fe_w * yw, "M")
    Mbscf = h.v("Mbs,cf", "En la cara de la columna: L/(L − sb)·Mbs", L / (L - sb) * Mbs, "M")
    Vbs = h.v("Vbs*", "Cortante del empalme: n·Fb,alma (pernos centrales)", nwv * Fi_w, "F")
    h.sec("4. VERIFICACIONES GLOBALES")
    h.chk(G_V, "Sobrerresistencia de la viga: Mb,n* ≥ 1.2·Mpl", "CIDECT 9 ec. 8.10", 1.2 * Mpl, Mbn, "M")
    h.chk(G_M, "Ménsula, modo (a) área neta 1ª fila: Mcf ≤ Mj,cf*", "CIDECT 9 ec. 8.12", Mcf, Mj1, "M")
    h.chk(G_M, "Ménsula, modo (b) rotura alas + alma: Mcf ≤ Mb,f,u + Mb,w,u", "CIDECT 9 ecs. 8.13–8.14", Mcf, Mj2, "M")
    h.chk(G_S, "Flexión del empalme en la cara de la columna: Mcf ≤ Mbs,cf", "CIDECT 9 §8.2.1 / EC3", Mcf, Mbscf, "M")
    gov = max(Fe_f, Fi_f, Fe_w, Fi_w)
    h.chk(G_S, "No debe romper el perno: Fb máx. ≤ 2·Vb* (doble cortante)", "CIDECT 9 §8.2", gov, 2 * Vb, "F")
    h.chk(C.G_DET, "Distancia al borde e1 ≥ 1.2·d0", "EC3 Tabla 3.3", 1.2 * d0, e1, "Lc")
    h.chk(C.G_DET, "Paso p1 ≥ 2.2·d0", "EC3 Tabla 3.3", 2.2 * d0, p1, "Lc")
    h.chk(C.G_DET, "Distancia transversal e2 ≥ 1.2·d0", "EC3 Tabla 3.3", 1.2 * d0, e2, "Lc")
    h.chk(C.G_DET, "Última fila de pernos más lejos de la cara que la primera: sl > sc", "Geometría", sc, sl, "Lc")
    As = 0.784 * math.pi * d ** 2 / 4          # sección resistente ≈ 0.784·A (M20: 245 mm²)
    ctx = {"derivados": {"vg_d_mm": bd * 10, "vg_bf_mm": bbf * 10, "vg_tw_mm": btw * 10, "vg_tf_mm": btf * 10,
                         "hss_W_mm": W * 10, "hss_D_mm": D * 10, "hss_t_mm": t * 10, "hss_bt": W / t},
           "vars": {"bd": bd, "bbf": bbf, "btw": btw, "btf": btf, "W": W, "D": D, "t": t, "mbf": mbf, "L": L, "sc": sc, "sl": sl, "sb": sb,
                    "e1": e1, "p1": p1, "d": d, "nfe": nfe, "nfi": nfi, "nwm": nwm, "nwv": nwv, "yw": yw},
           "g": dict(Mcf=Mcf, L=L, Vbs=Vbs, d=d, fub=fub, As=As, bd=bd, btf=btf, nf=nfe + nfi, mu=float(I["mu"]), Mbscf=Mbscf, Mbs=Mbs, sb=sb)}
    return ctx


def combo_fn(h, ctx, c, I):
    g = ctx["g"]
    Vg = abs(float(c.get("Vg") or 0)) * 1e3
    Ms = abs(float(c.get("Ms") or 0)) * 1e5
    h.sec(f"COMBINACIÓN {c['nombre']}")
    Vreq = h.v("Vbs", "Cortante requerido en el empalme: Vg + Mcf/L", Vg + g["Mcf"] / g["L"], "F")
    h.chk(G_S, "Cortante del empalme: Vg + Mcf/L ≤ n·Fb,alma", "CIDECT 9 §8.2.1", Vreq, g["Vbs"], "F")
    # deslizamiento en servicio (EC3 3.9): dos planos, Fp,C = 0.7·fub·As, γM3 = 1.25
    Fs = 2 * g["mu"] * 0.7 * g["fub"] * g["As"] / 1.25
    Mservicio = Ms * g["L"] / (g["L"] - g["sb"])
    Fala = Mservicio / (g["bd"] - g["btf"])
    h.v("Fala,s", "Fuerza de servicio en el ala del empalme: Ms·L/(L − sb)/(hb − tf)", Fala, "F")
    h.chk(G_S, "Deslizamiento en servicio (EC3 3.9, 2 planos): Fala,s ≤ n·Fs,Rd", "EC3 3.9 · criterio propio", Fala, g["nf"] * Fs, "F", activo=Ms > 0)


_MOD = Modulo(SPEC, global_fn, combo_fn)
calcular = _MOD.calcular
CAT = _MOD.CAT
