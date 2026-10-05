"""Motor de cálculo — placa base y pernos de anclaje.

Basado en la hoja PLACA_BASE_AISC_DG1.xlsx (AISC Design Guide 1, 3.ª ed.;
AISC 360-16 J2, J8; ACI 318-19 cap. 17; LRFD).

Unidades de ENTRADA y SALIDA (canónicas):
    fuerzas Tonf · momentos Tonf·m · dimensiones de perfil/placa/perno en mm
    · pedestal y distancias en cm · esfuerzos kgf/cm²
Internamente se calcula en kgf y cm (igual que la hoja de Excel).
La conversión a otros sistemas de unidades la hace la interfaz.

Cada valor del reporte lleva una etiqueta `q` de magnitud:
    F fuerza [Tonf] · M momento [Tonf·m] · ML momento por ancho [Tonf·m/m]
    S esfuerzo [kgf/cm²] · Ls longitud de sección [mm] · Lc longitud [cm]
    A área [cm²] · '' adimensional
"""
from __future__ import annotations

import json
import math
import os

_DIR = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(_DIR, "catalogos.json"), encoding="utf-8") as _f:
    CATALOGOS = json.load(_f)

ARMADO = "ARMADO (flejes soldados)"
PERSONALIZADO = "Personalizado"

# Conversión interna (kgf, cm) → canónica de salida
_OUT = {
    "F": 1e-3,       # kgf → Tonf
    "M": 1e-5,       # kgf·cm → Tonf·m
    "ML": 1e-3,      # kgf·cm/cm → Tonf·m/m
    "S": 1.0,
    "Ls": 10.0,      # cm → mm
    "Lc": 1.0,
    "A": 1.0,
    "FL": 1.0,       # kgf/cm (fuerza por longitud)
    "": 1.0,
}

CASOS = {0: "inactiva", 1: "e ≤ ecrit", 2: "M grande", 3: "Levantamiento"}


def _by_name(lista, nombre, campo="nombre"):
    for it in lista:
        if it[campo] == nombre:
            return it
    raise ValueError(f"'{nombre}' no está en el catálogo")


def _estado(r, lim):
    if r is None:
        return "N/A"
    if r > 1.0:
        return "NO CUMPLE"
    if r > lim:
        return "AL LÍMITE"
    return "CUMPLE"


def _si(v):
    return str(v).strip().lower() in ("sí", "si", "yes", "true", "1")


def _filete_min(t_mm):
    """AISC 360-16 Tabla J2.4 (mm), t = parte unida más delgada."""
    if t_mm <= 6:
        return 3
    if t_mm <= 13:
        return 5
    if t_mm <= 19:
        return 6
    return 8


class _Trace:
    def __init__(self):
        self.rows = []

    def add(self, sec, sym, desc, val, q=""):
        self.rows.append({"sec": sec, "sym": sym, "desc": desc, "val": val, "q": q})


def calcular(inp: dict) -> dict:
    lim = float(inp.get("lim_verde", 0.9))

    # ───────────────────────── 1. Geometría y materiales ─────────────────────────
    tipo = inp.get("tipo_col", "I")          # "I" (perfil I/H) | "HSS" (rectangular / cajón)
    hss = tipo == "HSS"
    if hss:
        perfil = inp.get("perfil_hss", PERSONALIZADO)
        if perfil == PERSONALIZADO:
            h_in = inp["hss"]
            d_mm, bf_mm, tf_mm = float(h_in["H"]), float(h_in["Bc"]), float(h_in["t"])
        else:
            p = _by_name(CATALOGOS["hss"], perfil)
            d_mm, bf_mm, tf_mm = p["H"], p["B"], p["t"]
        tw_mm = tf_mm
    else:
        perfil = inp.get("perfil", ARMADO)
        colin = inp.get("armado", {})
        if perfil == ARMADO:
            d_mm, bf_mm = float(colin["d"]), float(colin["bf"])
            tw_mm, tf_mm = float(colin["tw"]), float(colin["tf"])
        else:
            p = _by_name(CATALOGOS["perfiles"], perfil)
            d_mm, bf_mm, tw_mm, tf_mm = p["d"], p["bf"], p["tw"], p["tf"]
    d, bf, tw, tf = d_mm / 10, bf_mm / 10, tw_mm / 10, tf_mm / 10
    # HSS: d = H (dirección N), bf = Bc (ancho), tf = tw = t (espesor de pared)
    A = 2 * tf * (d + bf - 2 * tf) if hss else 2 * bf * tf + (d - 2 * tf) * tw

    pl = inp["placa"]
    N, B, tp, g = pl["N"] / 10, pl["B"] / 10, pl["tp"] / 10, pl.get("grout", 0) / 10
    if pl.get("acero") == PERSONALIZADO:
        pl_Fy = float(pl["Fy"])
    else:
        pl_Fy = _by_name(CATALOGOS["acero_placa"], pl["acero"])["Fy"]

    pn = inp["pernos"]
    mat = _by_name(CATALOGOS["pernos"], pn["material"])
    fya = mat["fya"]
    futa = min(mat["futa"], 1.9 * fya, 8790)
    dia = _by_name(CATALOGOS["diametros"], pn["diam"])
    da_in, nt = dia["da_in"], dia["hilos"]
    da = da_in * 2.54
    Ase = 0.7854 * (da_in - 0.9743 / nt) ** 2 * 6.4516
    F_tuerca = 1.5 * da_in + 0.125                       # pulg
    ar_lado = float(pn.get("arandela_lado", 0))
    ar_t = float(pn.get("arandela_t", 0))
    b_ar = min(ar_lado, F_tuerca * 25.4 + 2 * ar_t) / 25.4
    Abrg = ((b_ar ** 2 if b_ar > F_tuerca else 0.866 * F_tuerca ** 2)
            - math.pi * da_in ** 2 / 4) * 6.4516
    nf = int(pn["nfila"])
    n_pern = 2 * nf
    f = N / 2 - pn["eN"] / 10
    xb = B / 2 - pn["eB"] / 10
    s_pern = 2 * xb / (nf - 1) if nf > 1 else 0.0
    hef = pn["hef"] / 10
    nv = int(pn.get("nv", n_pern))
    arand_sold = _si(pn.get("arandela_sold", "No"))

    pd = inp["pedestal"]
    fc, Np, Bp = float(pd["fc"]), float(pd["Np"]), float(pd["Bp"])
    fisurado = _si(pd.get("fisurado", "Sí"))
    ref_borde = _si(pd.get("ref_borde", "No"))
    hp_usar = _si(pd.get("hp_usar", "No"))
    hp_n = int(pd.get("hp_n", 0))
    hp_db = pd.get("hp_db", 16)
    hp_fy = float(pd.get("hp_fy", 4200))
    cor = inp.get("corte", {})
    friccion = _si(cor.get("friccion", "No"))
    mu_fr = float(cor.get("mu", 0.55))
    lg = inp.get("llave", {})
    llave = _si(lg.get("usar", "No"))
    lg_b, lg_d, lg_t = float(lg.get("b", 150)) / 10, float(lg.get("d", 60)) / 10, float(lg.get("t", 20)) / 10
    lg_fy, lg_w = float(lg.get("fy", 2530)), float(lg.get("w", 8)) / 10
    sis = inp.get("sismo", {})
    sismo = _si(sis.get("sismo", "No"))
    omega0 = float(sis.get("omega0", 1))
    k_sis = 0.75 if sismo else 1.0

    caF = Np / 2 - f
    caS = Bp / 2 - xb
    caP = Np / 2 + f

    T = _Trace()
    G = "1. GEOMETRÍA Y MATERIALES"
    if hss:
        T.add(G, "H", "HSS: dimensión en la dirección N (del momento)", d, "Lc")
        T.add(G, "Bc", "HSS: dimensión perpendicular", bf, "Lc")
        T.add(G, "t", "HSS: espesor de pared (de diseño)", tf, "Lc")
        T.add(G, "A", "Área del HSS ≈ 2·t·(H + Bc − 2t) (sin radios de esquina)", A, "A")
    else:
        T.add(G, "d", "Peralte de columna", d, "Lc")
        T.add(G, "bf", "Ancho de ala", bf, "Lc")
        T.add(G, "tw", "Espesor de alma", tw, "Lc")
        T.add(G, "tf", "Espesor de ala", tf, "Lc")
        T.add(G, "A", "Área del perfil ≈ 2·bf·tf + (d−2tf)·tw", A, "A")
    T.add(G, "N", "Largo de placa (dir. del momento)", N, "Lc")
    T.add(G, "B", "Ancho de placa", B, "Lc")
    T.add(G, "tp", "Espesor de placa", tp, "Lc")
    T.add(G, "Fy", "Fy de la placa", pl_Fy, "S")
    T.add(G, "da", "Diámetro del perno", da, "Lc")
    T.add(G, "Ase,N", "Área efectiva a tracción = 0.7854·(da−0.9743/nt)²", Ase, "A")
    T.add(G, "futa", "futa (≤ 1.9·fya ; ≤ 8790 kgf/cm²)", futa, "S")
    T.add(G, "Abrg", "Área de apoyo de cabeza/tuerca/arandela − área del vástago", Abrg, "A")
    T.add(G, "f", "Distancia centro de placa → fila de pernos (DG1)", f, "Lc")
    T.add(G, "xb", "Distancia eje de placa → perno extremo (dir. B)", xb, "Lc")
    T.add(G, "s", "Espaciamiento entre pernos de una fila", s_pern, "Lc")
    T.add(G, "hef", "Empotramiento efectivo", hef, "Lc")
    T.add(G, "ca,F", "Fila en tracción → cara frontal del pedestal", caF, "Lc")
    T.add(G, "ca,S", "Perno extremo → cara lateral del pedestal", caS, "Lc")
    T.add(G, "ca,P", "Fila en tracción → cara posterior del pedestal", caP, "Lc")
    T.add(G, "k sis", "Factor sísmico concreto en tracción (ACI §17.10.5.4)", k_sis, "")

    # ───────────────────── 2. Aplastamiento (AISC J8 / DG1) ─────────────────────
    S2 = "2. APLASTAMIENTO — AISC 360-16 J8 / DG1"
    b_raiz = min(2.0, max(1.0, min(Bp / B, Np / N)))
    fpu_max = 0.65 * 0.85 * fc * b_raiz
    qmax = fpu_max * B
    m_ = (N - 0.95 * d) / 2
    n_ = (B - (0.95 if hss else 0.8) * bf) / 2     # HSS: líneas de fluencia a 0.95·H y 0.95·Bc (DG1 §3.1.3)
    np_ = 0.0 if hss else math.sqrt(d * bf) / 4    # n' y λ no se usan en HSS
    x_t = f - d / 2 + tf / 2
    phiMn = 0.9 * pl_Fy * tp ** 2 / 4
    T.add(S2, "√(A2/A1)", "A2 geométricamente similar y concéntrica, 1 ≤ √(A2/A1) ≤ 2", b_raiz, "")
    T.add(S2, "fpu,max", "φc·0.85·f'c·√(A2/A1), φc = 0.65", fpu_max, "S")
    T.add(S2, "qmax", "fpu,max·B", qmax, "F")
    T.add(S2, "m", "(N − 0.95·d)/2" if not hss else "(N − 0.95·H)/2", m_, "Lc")
    if hss:
        T.add(S2, "n", "(B − 0.95·Bc)/2  (HSS: n' y λ no se usan)", n_, "Lc")
    else:
        T.add(S2, "n", "(B − 0.80·bf)/2", n_, "Lc")
        T.add(S2, "n'", "√(d·bf)/4", np_, "Lc")
    T.add(S2, "x", "Brazo lado tracción: f − d/2 + tf/2 (DG1)", x_t, "Lc")
    T.add(S2, "φMn", "0.90·Fy·tp²/4 (por unidad de ancho)", phiMn, "ML")

    # ───────────────────── 3. Pernos — resistencias (ACI 318-19) ─────────────────────
    S3 = "3. PERNOS — RESISTENCIAS (ACI 318-19 Cap. 17)"
    phiNsa = 0.75 * Ase * futa
    phiVsa = 0.65 * 0.6 * Ase * futa * (0.8 if g > 0 else 1.0)
    psi_cN = 1.0 if fisurado else 1.25
    c15 = 1.5 * hef
    # fila en tracción
    t_ned = (caF < c15) + 2 * (caS < c15) + (caP < c15)
    t_camax = max(caF if caF < c15 else 0, caS if caS < c15 else 0, caP if caP < c15 else 0)
    t_h = min(hef, max(t_camax / 1.5, 2 * xb / 3)) if t_ned >= 3 else hef
    t_ANco = 9 * t_h ** 2
    t_ANc = min((2 * xb + 2 * min(1.5 * t_h, caS)) * (min(1.5 * t_h, caF) + min(1.5 * t_h, caP)),
                nf * t_ANco)
    t_psied = min(1, 0.7 + 0.3 * min(caF, caS) / (1.5 * t_h))
    t_Nb = 24 * math.sqrt(fc * 14.2233) * (t_h / 2.54) ** 1.5 * 0.453592
    phiNcb = 0.7 * k_sis * t_ANc / t_ANco * t_psied * psi_cN * t_Nb
    # grupo completo
    g_ned = 2 * (caF < c15) + 2 * (caS < c15)
    g_camax = max(caF if caF < c15 else 0, caS if caS < c15 else 0)
    g_h = min(hef, max(g_camax / 1.5, max(2 * xb, 2 * f) / 3)) if g_ned >= 3 else hef
    g_ANco = 9 * g_h ** 2
    g_ANc = min((2 * xb + 2 * min(1.5 * g_h, caS)) * (2 * f + 2 * min(1.5 * g_h, caF)),
                n_pern * g_ANco)
    g_psied = min(1, 0.7 + 0.3 * min(caF, caS) / (1.5 * g_h))
    Ncb0 = (g_ANc / g_ANco * g_psied * psi_cN * 24 * math.sqrt(fc * 14.2233)
            * (g_h / 2.54) ** 1.5 * 0.453592)
    phiNpn = 0.7 * k_sis * (1.0 if fisurado else 1.4) * 8 * Abrg * fc
    # desprendimiento lateral
    sq_abrg = math.sqrt(Abrg / 6.4516)
    sq_fc = math.sqrt(fc * 14.2233)
    apF = hef > 2.5 * caF
    if nf > 1 and 2 * xb < 6 * caF:
        base = (1 + 2 * xb / (6 * caF)) * 160 * (caF / 2.54) * sq_abrg * sq_fc
    else:
        base = (nf * 160 * (caF / 2.54) * sq_abrg * sq_fc
                * ((1 + min(3, max(1, caS / caF))) / 4 if caS < 3 * caF else 1))
    phiNsbgF = 0.7 * k_sis * base * 0.453592
    apS = hef > 2.5 * caS
    phiNsbS = (0.7 * k_sis * 160 * (caS / 2.54) * sq_abrg * sq_fc
               * ((1 + min(3, max(1, caF / caS))) / 4 if caF < 3 * caS else 1) * 0.453592)
    # hairpins
    As_var = next((v["As"] for v in CATALOGOS["varillas"] if v["nombre"] == hp_db), 0.0)
    As_hp = hp_n * As_var
    phiNnhp = 0.75 * As_hp * hp_fy
    # corte
    psi_cV = 1.4 if not fisurado else (1.2 if ref_borde else 1.0)
    le = min(hef, 8 * da)

    def _vcb(ca1):
        Vb = (min(7 * (le / da) ** 0.2 * math.sqrt(da_in), 9) * sq_fc
              * (ca1 / 2.54) ** 1.5 * 0.453592)
        ratio = min(nf, (2 * xb + 2 * min(1.5 * ca1, caS)) * 1.5 * ca1 / (4.5 * ca1 ** 2))
        phi = 0.7 * ratio * min(1, 0.7 + 0.3 * caS / (1.5 * ca1)) * psi_cV * Vb
        return Vb, ratio, phi

    vA_Vb, vA_r, vA_phi = _vcb(caF)
    vB_Vb, vB_r, vB_phi = _vcb(caP)
    phiVcpg = 0.7 * (2 if hef >= 6.35 else 1) * Ncb0

    T.add(S3, "φNsa", "Acero a tracción por perno: 0.75·Ase·futa (§17.6.1)", phiNsa, "F")
    T.add(S3, "φVsa", "Acero a corte por perno: 0.65·0.6·Ase·futa·(0.8 si grout) (§17.7.1)", phiVsa, "F")
    T.add(S3, "ψc,N", "Fisuración (§17.6.2.5): 1.0 fisurado; 1.25 no fisurado", psi_cN, "")
    T.add(S3, "# bordes", "Fila en tracción: bordes a < 1.5hef", t_ned, "")
    T.add(S3, "h'ef", "hef de cálculo (§17.6.2.1.2: si ≥ 3 bordes → máx(ca,max/1.5 ; s/3) ≤ hef)", t_h, "Lc")
    T.add(S3, "ANco", "9·h'ef²", t_ANco, "A")
    T.add(S3, "ANc", "Área proyectada de la fila (limitada por bordes) ≤ nf·ANco", t_ANc, "A")
    T.add(S3, "ψed,N", "0.7 + 0.3·ca,min/(1.5h'ef) ≤ 1 (§17.6.2.4)", t_psied, "")
    T.add(S3, "Nb", "24·√f'c·h'ef^1.5 (kc = 24, colado en sitio)", t_Nb, "F")
    T.add(S3, "φNcb", "0.70·ksis·(ANc/ANco)·ψed·ψc·Nb — fila en tracción", phiNcb, "F")
    T.add(S3, "h'ef,g", "hef de cálculo, grupo completo (§17.6.2.1.2)", g_h, "Lc")
    T.add(S3, "ANc,g", "Área proyectada del grupo completo ≤ n·ANco", g_ANc, "A")
    T.add(S3, "Ncb0", "(ANc/ANco)·ψed·ψc·Nb — grupo completo, sin ψec", Ncb0, "F")
    T.add(S3, "φNpn", "Extracción por perno: 0.70·ksis·ψc,P·8·Abrg·f'c (§17.6.3)", phiNpn, "F")
    T.add(S3, "aplica F", "Desprendimiento lateral cara frontal: hef > 2.5·ca,F", int(apF), "")
    T.add(S3, "φNsbg,F", "0.70·ksis·Nsbg; Nsb = 160·ca1·√Abrg·√f'c (§17.6.4)", phiNsbgF, "F")
    T.add(S3, "aplica S", "Desprendimiento lateral cara lateral: hef > 2.5·ca,S", int(apS), "")
    T.add(S3, "φNsb,S", "Perno esquinero hacia cara lateral", phiNsbS, "F")
    T.add(S3, "As,hp", "Área de refuerzo de anclaje = ramas·As", As_hp, "A")
    T.add(S3, "φNn,hp", "Refuerzo de anclaje: 0.75·As·fy (§17.5.2.1)", phiNnhp, "F")
    T.add(S3, "ψc,V", "Corte (§17.7.2.5): no fis. 1.4; fis. c/refuerzo borde 1.2; fis. 1.0", psi_cV, "")
    T.add(S3, "le", "min(hef ; 8·da)", le, "Lc")
    T.add(S3, "Vb,F", "Fila frontal (ca1 = ca,F)", vA_Vb, "F")
    T.add(S3, "φVcbg,F", "Fila frontal: 0.70·(Avc/Avco)·ψed,V·ψc,V·Vb", vA_phi, "F")
    T.add(S3, "Vb,P", "Fila posterior (ca1 = ca,P)", vB_Vb, "F")
    T.add(S3, "φVcbg,P", "Fila posterior: 0.70·(Avc/Avco)·ψed,V·ψc,V·Vb", vB_phi, "F")
    T.add(S3, "φVcpg", "Pryout: 0.70·kcp·Ncb0, kcp = 2 (hef ≥ 6.35 cm) (§17.7.3)", phiVcpg, "F")

    # ───────────────────────── 4. Soldadura (AISC J2.4) ─────────────────────────
    S4 = "4. SOLDADURA — AISC 360-16 J2.4"
    so = inp["sold"]
    FEXX = _by_name(CATALOGOS["electrodos"], so["electrodo"])["FEXX"]
    wf, ww = float(so["wf"]), float(so["ww"])
    # I: filete a ambos lados del ala (2bf − tw); HSS: filete exterior en la pared traccionada (Bc)
    Lf = bf if hss else 2 * bf - tw
    phiRf = 0.75 * 0.6 * FEXX * 0.707 * wf / 10 * Lf * 1.5
    phiRw = 0.75 * 0.6 * FEXX * 0.707 * ww / 10 * 2 * (d - 2 * tf)
    T.add(S4, "FEXX", "Resistencia del electrodo", FEXX, "S")
    T.add(S4, "φRn,ala", ("0.75·0.6·FEXX·0.707·w·Bc·1.5 (pared traccionada, θ = 90°, Ec. J2-5)" if hss else "0.75·0.6·FEXX·0.707·w·(2bf − tw)·1.5 (θ = 90°, Ec. J2-5)"), phiRf, "F")
    T.add(S4, "φRn,alma", ("0.75·0.6·FEXX·0.707·w·2(H − 2t) (paredes paralelas al corte, θ = 0°)" if hss else "0.75·0.6·FEXX·0.707·w·2(d − 2tf) (θ = 0°)"), phiRw, "F")

    # ───────────────────── 4b. Llave de corte (DG1 §3.5.2, Ej. 4.9) ─────────────────────
    S4b = "4b. LLAVE DE CORTE — DG1 §3.5.2 / ACI 349 Ap. B"
    sq_fc_l = math.sqrt(fc * 14.2233)
    lg_A = lg_b * lg_d
    phiPbr = 0.80 * fc * lg_A
    phiMl = 0.90 * lg_fy * lg_b * lg_t ** 2 / 4
    lg_ev = Np / 2 - lg_t / 2                                     # lado de la llave → cara del pedestal (llave centrada)
    lg_Wp = min(Bp, lg_b + 2 * (lg_d + lg_ev))
    lg_Av = max(lg_Wp * (lg_d + lg_ev) - lg_b * lg_d, 0.0)
    phiVcs = 4 * 0.75 * sq_fc_l * (lg_Av / 6.4516) * 0.453592
    lg_arm = g + lg_d / 2
    phiRw_l = 0.75 * 0.6 * FEXX * 0.707 * lg_w                    # por cm de soldadura
    if llave:
        T.add(S4b, "A1", "Área embebida de la llave: b·d", lg_A, "A")
        T.add(S4b, "φPbr", "Aplastamiento del concreto: 0.80·f'c·A1 (DG1 Ec. 3.5.2)", phiPbr, "F")
        T.add(S4b, "φMl", "Flexión de la llave: 0.90·Fy·b·t²/4", phiMl, "M")
        T.add(S4b, "Av", "Plano de falla a 45° al borde del pedestal: Wp·(d + e) − b·d", lg_Av, "A")
        T.add(S4b, "φVcs", "Corte del concreto frente a la llave: 4·0.75·√f'c·Av", phiVcs, "F")
        T.add(S4b, "G + d/2", "Brazo del voladizo: grout + d/2", lg_arm, "Lc")
        T.add(S4b, "φrw", "Resistencia de soldadura por longitud: 0.75·0.6·FEXX·0.707·w", phiRw_l, "FL")

    # ───────────────────── 5. Verificación por combinación ─────────────────────
    combos_out = []
    for cb in inp.get("combos", []):
        nombre = str(cb.get("nombre", "")).strip()
        Pu = float(cb.get("P") or 0) * 1000
        Vu = abs(float(cb.get("V") or 0)) * 1000
        Mu = abs(float(cb.get("M") or 0)) * 1e5
        activo = abs(Pu) + Vu + Mu > 0
        r = {}
        tr = _Trace()
        C = "5. COMBINACIÓN"
        tr.add(C, "Pu", "Axial (+ compresión)", Pu, "F")
        tr.add(C, "Vu", "Cortante", Vu, "F")
        tr.add(C, "Mu", "|Momento|", Mu, "M")
        if not activo:
            combos_out.append({"nombre": nombre, "activo": False, "caso": 0, "caso_txt": CASOS[0],
                               "ratios": {}, "ratio_max": None, "trace": _conv(tr.rows)})
            continue
        e = Mu / Pu if Pu > 0 else 0.0
        ecrit = N / 2 - Pu / (2 * qmax)
        if Pu > 0:
            caso = 1 if e <= ecrit else 2
        else:
            caso = 2 if (Mu + Pu * f) > 0 else 3
        K = (f + N / 2) ** 2 - 2 * (Mu + Pu * f) / qmax
        if caso == 1:
            Y = N - 2 * e
        elif caso == 2:
            Y = f + N / 2 - math.sqrt(max(K, 0))
        else:
            Y = 0.0
        fp = Pu / (Y * B) if caso == 1 else (fpu_max if caso == 2 else 0.0)
        if caso == 1:
            r_ap = fp / fpu_max
        elif caso == 2:
            r_ap = 2 * (Mu + Pu * f) / (qmax * (f + N / 2) ** 2)
        else:
            r_ap = 0.0
        dem_ap = fp if caso == 1 else ((Mu + Pu * f) if caso == 2 else 0.0)
        dem_ap_q = "S" if caso == 1 else "M"
        cap_ap = qmax * (f + N / 2) ** 2 / 2 if caso == 2 else fpu_max
        Tu = max(0.0, qmax * Y - Pu) if caso == 2 else (-Pu / 2 + Mu / (2 * f) if caso == 3 else 0.0)
        # λ (solo carga axial)
        lam = 0.0
        if caso == 1 and Mu == 0 and not hss:
            Xx = 4 * d * bf / (d + bf) ** 2 * Pu / (fpu_max * N * B)
            lam = 1.0 if Xx >= 1 else min(1.0, 2 * math.sqrt(Xx) / (1 + math.sqrt(1 - Xx)))
        l_ = max(m_, n_, lam * np_)
        Mpl_c = fp * l_ ** 2 / 2 if Y >= l_ else fp * Y * (l_ - Y / 2)
        Mpl_t = Tu * max(x_t, 0) / B
        r_pc, r_pt = Mpl_c / phiMn, Mpl_t / phiMn
        tp_req = math.sqrt(4 * max(Mpl_c, Mpl_t) / (0.9 * pl_Fy)) * 10   # cm → mm
        Nua = Tu / nf * omega0
        Nua_g = Tu * omega0
        r_sa = Nua / phiNsa
        psi_ec = 1 / (1 + Mu / max(-Pu, 1) / (1.5 * g_h)) if caso == 3 else 1.0
        r_cb = Nua_g / phiNcb
        r_cbg = -Pu * omega0 / (0.7 * k_sis * psi_ec * Ncb0) if caso == 3 else 0.0
        if hp_usar:
            r_arr = Nua_g / phiNnhp if phiNnhp > 0 else float("inf")
            dem_arr, cap_arr = Nua_g, phiNnhp
        else:
            r_arr = max(r_cb, r_cbg)
            if r_cb >= r_cbg:
                dem_arr, cap_arr = Nua_g, phiNcb
            else:
                dem_arr, cap_arr = -Pu * omega0, 0.7 * k_sis * psi_ec * Ncb0
        r_pull = Nua / phiNpn
        r_sbF = Nua_g / phiNsbgF if apF else 0.0
        r_sbS = Nua / phiNsbS if apS else 0.0
        r_sb = max(r_sbF, r_sbS)
        dem_sb, cap_sb = (Nua_g, phiNsbgF) if r_sbF >= r_sbS else (Nua, phiNsbS)
        # DG1 §3.5.1: φVn = φ·µ·Pu ≤ 0.2·f'c·Ac (φ = 0.75), sólo con Pu > 0 de la misma combinación
        Vfr = min(0.75 * mu_fr * Pu, 0.2 * fc * N * B) if (friccion and Pu > 0) else 0.0
        Vua = 0.0 if llave else max(0.0, Vu - Vfr) * omega0
        Vlug = Vu * omega0 if llave else 0.0
        Ml = Vlug * lg_arm
        fv_l = Vlug / (2 * lg_b)
        fm_l = Ml / (lg_b * (lg_t + lg_w))
        f_l = math.hypot(fv_l, fm_l)
        r_vsa = Vua / nv / phiVsa
        r_vA = 0.0 if arand_sold else Vua * nf / n_pern / vA_phi
        r_vB = Vua / vB_phi
        r_vcb = max(r_vA, r_vB)
        dem_vcb, cap_vcb = (Vua * nf / n_pern, vA_phi) if r_vA >= r_vB else (Vua, vB_phi)
        r_pry = Vua / phiVcpg
        r_t = max(r_sa, r_arr, r_pull, r_sb)
        r_v = max(r_vsa, r_vcb, r_pry)
        r_int = r_v if r_t <= 0.2 else (r_t if r_v <= 0.2 else (r_t + r_v) / 1.2)
        Tala = max(0.0, Mu / (d - tf) - Pu * bf * tf / A)
        r_wf = Tala / phiRf
        r_ww = Vu / phiRw
        ratios = {
            "ap": r_ap, "pc": r_pc, "pt": r_pt, "sa": r_sa, "arr": r_arr, "pull": r_pull,
            "sb": r_sb, "vsa": r_vsa, "vcb": r_vcb, "pry": r_pry, "int": r_int,
            "wf": r_wf, "ww": r_ww,
            "lbr": Vlug / phiPbr if llave else 0.0, "lfl": Ml / phiMl if llave else 0.0,
            "lcs": Vlug / phiVcs if llave and phiVcs > 0 else 0.0, "lw": f_l / phiRw_l if llave else 0.0,
        }
        det = {
            "ap": (dem_ap, cap_ap, dem_ap_q), "pc": (Mpl_c, phiMn, "ML"), "pt": (Mpl_t, phiMn, "ML"),
            "sa": (Nua, phiNsa, "F"), "arr": (dem_arr, cap_arr, "F"), "pull": (Nua, phiNpn, "F"),
            "sb": (dem_sb, cap_sb, "F"), "vsa": (Vua / nv, phiVsa, "F"),
            "vcb": (dem_vcb, cap_vcb, "F"), "pry": (Vua, phiVcpg, "F"),
            "int": (r_t, r_v, ""), "wf": (Tala, phiRf, "F"), "ww": (Vu, phiRw, "F"),
            "lbr": (Vlug, phiPbr, "F"), "lfl": (Ml, phiMl, "M"), "lcs": (Vlug, phiVcs, "F"), "lw": (f_l, phiRw_l, "FL"),
        }
        tr.add(C, "e", "Mu/Pu (si Pu > 0)", e, "Lc")
        tr.add(C, "ecrit", "N/2 − Pu/(2·qmax)", ecrit, "Lc")
        tr.add(C, "caso", "1: e ≤ ecrit | 2: momento grande | 3: levantamiento total", caso, "")
        tr.add(C, "Y", "Longitud de apoyo", Y, "Lc")
        tr.add(C, "fp", "Presión de apoyo", fp, "S")
        tr.add(C, "ratio ap", "Aplastamiento", r_ap, "")
        tr.add(C, "Tu", "Tracción en la fila de pernos (caso 3: |Pu|/2 + Mu/2f)", Tu, "F")
        tr.add(C, "λ", "DG1: solo carga axial (Mu = 0): 2√X/(1+√(1−X)) ≤ 1", lam, "")
        tr.add(C, "l", "Voladizo crítico: máx(m ; n ; λn')", l_, "Lc")
        tr.add(C, "Mpl,c", "Lado compresión (DG1 Ec. 4-51a/4-52a)", Mpl_c, "ML")
        tr.add(C, "Mpl,t", "Lado tracción: Tu·x/B (DG1 Ec. 4-62)", Mpl_t, "ML")
        tr.add(C, "tp,req", "Espesor requerido √(4·máx(Mpl)/(0.9·Fy))", tp_req / 10, "Ls")
        tr.add(C, "Nua", "Tracción por perno · Ω0", Nua, "F")
        tr.add(C, "Nua,g", "Tracción de la fila · Ω0", Nua_g, "F")
        tr.add(C, "ψec,N", "Caso 3: 1/(1 + e'N/(1.5h'ef))", psi_ec, "")
        if llave:
            tr.add(C, "Vlug", "Corte tomado por la llave (todo Vu·Ω0; sin fricción ni pernos)", Vlug, "F")
            tr.add(C, "Ml", "Momento en la raíz de la llave: V·(G + d/2)", Ml, "M")
            tr.add(C, "f soldadura", "Resultante por cm: √((V/2b)² + (Ml/(b·(t + w)))²)", f_l, "FL")
        if friccion:
            tr.add(C, "φVfric", "Fricción DG1 §3.5.1: min(0.75·µ·Pu ; 0.2·f'c·N·B)", Vfr, "F")
        tr.add(C, "Vua", "Corte en pernos = (Vu − fricción) · Ω0", Vua, "F")
        tr.add(C, "Nua/φNn", "Máximo en tracción (acero, arrancamiento, extracción, lateral)", r_t, "")
        tr.add(C, "Vua/φVn", "Máximo en corte (acero, arrancamiento, pryout)", r_v, "")
        tr.add(C, "int", "Interacción §17.8: ≤ 0.2 → sin interacción; si no (N+V)/1.2", r_int, "")
        tr.add(C, "Tu,ala", "Fuerza en ala: Mu/(d − tf) − Pu·bf·tf/A", Tala, "F")
        combos_out.append({
            "nombre": nombre, "activo": True, "caso": caso, "caso_txt": CASOS[caso],
            "e": e * _OUT["Lc"], "ecrit": ecrit, "Y": Y, "fp": fp, "Tu": Tu / 1000,
            "l": l_, "tp_req_mm": tp_req,
            "ratios": ratios, "ratio_max": max(ratios.values()),
            "det": {k: {"dem": v[0] * _OUT[v[2]], "cap": v[1] * _OUT[v[2]], "q": v[2]}
                    for k, v in det.items()},
            "trace": _conv(tr.rows),
        })

    # ───────────────────────── Resumen de verificaciones ─────────────────────────
    activos = [c for c in combos_out if c["activo"]]

    def gov(key):
        if not activos:
            return None
        return max(activos, key=lambda c: c["ratios"][key])

    def chk(grupo, nombre, ref, key, unidad_q=None):
        c = gov(key)
        if c is None:
            return dict(grupo=grupo, nombre=nombre, ref=ref, ratio=None, estado="N/A",
                        combo="—", dem=None, cap=None, q="")
        det = c["det"][key]
        return dict(grupo=grupo, nombre=nombre, ref=ref, ratio=c["ratios"][key],
                    estado=_estado(c["ratios"][key], lim), combo=c["nombre"],
                    dem=det["dem"], cap=det["cap"], q=det["q"], caso=c["caso_txt"])

    checks = [
        chk("PLACA BASE Y CONCRETO DE APOYO", "Aplastamiento del concreto", "AISC J8 · DG1", "ap"),
        chk("PLACA BASE Y CONCRETO DE APOYO", "Flexión de placa — lado compresión", "DG1 Ec. 4-51a/4-52a", "pc"),
        chk("PLACA BASE Y CONCRETO DE APOYO", "Flexión de placa — lado tracción", "DG1 Ec. 4-62", "pt"),
        chk("PERNOS DE ANCLAJE — TRACCIÓN", "Acero del perno (por perno)", "ACI §17.6.1", "sa"),
        chk("PERNOS DE ANCLAJE — TRACCIÓN",
            "Refuerzo de anclaje (hairpins)" if hp_usar else "Arrancamiento del concreto (grupo)",
            "ACI §17.5.2.1" if hp_usar else "ACI §17.6.2", "arr"),
        chk("PERNOS DE ANCLAJE — TRACCIÓN", "Extracción por deslizamiento (pullout)", "ACI §17.6.3", "pull"),
    ]
    if apF or apS:
        checks.append(chk("PERNOS DE ANCLAJE — TRACCIÓN", "Desprendimiento lateral (blowout)", "ACI §17.6.4", "sb"))
    else:
        checks.append(dict(grupo="PERNOS DE ANCLAJE — TRACCIÓN", nombre="Desprendimiento lateral (blowout)",
                           ref="ACI §17.6.4", ratio=None, estado="N/A", combo="—", dem=None, cap=None,
                           q="", caso="no aplica (hef ≤ 2.5·ca)"))
    checks += [
        chk("PERNOS DE ANCLAJE — CORTE", "Acero del perno (por perno)", "ACI §17.7.1", "vsa"),
        chk("PERNOS DE ANCLAJE — CORTE", "Arrancamiento del concreto en corte", "ACI §17.7.2", "vcb"),
        chk("PERNOS DE ANCLAJE — CORTE", "Desprendimiento por palanca (pryout)", "ACI §17.7.3", "pry"),
        chk("PERNOS DE ANCLAJE — CORTE", "Interacción tracción – corte", "ACI §17.8", "int"),
        chk("SOLDADURA COLUMNA – PLACA", ("Filete en alas (tracción de ala)" if not hss else "Filete en pared traccionada"), "AISC J2.4 · Ec. J2-5", "wf"),
        chk("SOLDADURA COLUMNA – PLACA", ("Filete en alma (corte)" if not hss else "Filete en paredes paralelas al corte"), "AISC J2.4", "ww"),
    ]
    if llave:
        checks += [
            chk("LLAVE DE CORTE", "Aplastamiento del concreto (0.80·f'c·A1)", "DG1 §3.5.2", "lbr"),
            chk("LLAVE DE CORTE", "Flexión de la llave (voladizo)", "DG1 Ej. 4.9", "lfl"),
            chk("LLAVE DE CORTE", "Corte del concreto frente a la llave", "ACI 349 B.4.5 · DG1 §3.5.2", "lcs"),
            chk("LLAVE DE CORTE", "Soldadura llave–placa (resultante por cm)", "AISC J2.4", "lw"),
        ]
    # geometría y detalles (requerido / provisto) — ratio = requerido / provisto
    ped_ok = max(N / Np, B / Bp)
    sep_prov = min(s_pern, 2 * f) if nf > 1 else 2 * f
    hol_prov = f - d / 2
    bor_prov = min(inp["pernos"]["eN"], inp["pernos"]["eB"]) / 10
    fil_f = _filete_min(min(tf_mm, pl["tp"]))
    fil_w = _filete_min(min(tw_mm, pl["tp"]))
    geo = [
        ("Espaciamiento mínimo 4·da", "ACI §17.9.2", 4 * da, sep_prov, "Lc"),
        ("Placa contenida en el pedestal", "Geometría", max(N, B), Np if N / Np >= B / Bp else Bp, "Lc"),
        ("Holgura perno – cara de columna ≥ 1.5·da", "Práctica (tuerca/llave)", 1.5 * da, hol_prov, "Lc"),
        ("Borde perno – placa ≥ 1.5·da", "Práctica / DG1", 1.5 * da, bor_prov, "Lc"),
        ("Espesor mínimo práctico de placa", "DG1 §2.2 (½\" HSS / ¾\" otros)", 12.7 if hss else 19.05, pl["tp"], "Ls"),
        ("Filete mínimo en alas" if not hss else "Filete mínimo en paredes", "AISC Tabla J2.4", fil_f, wf, "Ls"),
        ("Filete mínimo en alma" if not hss else "Filete mínimo (paredes paralelas al corte)", "AISC Tabla J2.4", fil_w, ww, "Ls"),
    ]
    for nom, ref, req, prov, q in geo:
        rr = req / max(prov, 0.001)
        if q == "Ls":
            dem, cap = req, prov
        else:
            dem, cap = req, prov
        checks.append(dict(grupo="GEOMETRÍA Y DETALLES (requerido / provisto)", nombre=nom, ref=ref,
                           ratio=rr, estado=_estado(rr, lim), combo="—", dem=dem, cap=cap, q=q))
    ratios_all = [c["ratio"] for c in checks if c["ratio"] is not None]
    rmax = max(ratios_all) if ratios_all else None
    if not activos:
        msg = "SIN CARGAS"
    elif rmax > 1:
        msg = "NO CUMPLE"
    elif rmax > lim:
        msg = "CUMPLE AL LÍMITE"
    else:
        msg = "CUMPLE"

    tp_req_max = max((c["tp_req_mm"] for c in activos), default=0.0)
    return {
        "resumen": {"estado": msg, "ratio_max": rmax, "tp_req_mm": tp_req_max},
        "checks": checks,
        "combos": combos_out,
        "memoria_global": _conv(T.rows),
        "geom": {
            "tipo": tipo, "d": d, "bf": bf, "tw": tw, "tf": tf, "N": N, "B": B, "tp": tp, "g": g,
            "f": f, "xb": xb, "nf": nf, "da": da, "hef": hef, "Np": Np, "Bp": Bp,
            "m": m_, "n": n_, "np": np_, "x": x_t, "eN": inp["pernos"]["eN"] / 10,
            "eB": inp["pernos"]["eB"] / 10, "ar_lado": ar_lado / 10, "ar_t": ar_t / 10,
            "caF": caF, "caS": caS, "caP": caP,
        },
        "derivados": {"d_mm": d_mm, "bf_mm": bf_mm, "tw_mm": tw_mm, "tf_mm": tf_mm, "Fy": pl_Fy,
                      "fya": fya, "futa": futa},
    }


def _conv(rows):
    out = []
    for r in rows:
        v = r["val"]
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            v = v * _OUT[r["q"]]
        out.append({**r, "val": v})
    return out
