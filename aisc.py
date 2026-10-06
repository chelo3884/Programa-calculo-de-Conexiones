"""Fórmulas de AISC 360-16 / Manual 15.ª ed. para los módulos escritos a mano.

Unidades internas: kgf · cm · kgf/cm² (igual que las hojas de Excel). Las funciones devuelven resistencias de
diseño φRn (LRFD). Cada función cita el artículo de la especificación; las pruebas (tests/test_aisc_lib.py)
las comparan con los AISC Design Examples v15.
"""
from __future__ import annotations

import math

E = 2.04e6            # kgf/cm² (29 000 ksi)
KSI = 70.307          # kgf/cm² por ksi
KIP = 453.592         # kgf por kip
IN = 2.54             # cm por in

# ── materiales ─────────────────────────────────────────────────────────────────────────────────────────
ACEROS = {            # nombre: (Fy, Fu) kgf/cm²
    "A36": (2530, 4080), "A572 Gr50": (3515, 4570), "A992": (3515, 4570), "A588 Gr50": (3515, 4920),
    "A500 Gr B": (3234, 4078), "A500 Gr C": (3515, 4359),
}
ELECTRODOS = {"E60XX": 4220, "E70XX": 4920}
# pernos: grado → (Fnt, Fnv) kgf/cm² (Tabla J3.2) y pretensión mínima Tb por diámetro [kip] (Tabla J3.1)
PERNOS = {
    "A325-N (roscas incl.)": (6328, 3797), "A325-X (roscas excl.)": (6328, 4781),
    "A490-N (roscas incl.)": (7945, 4781), "A490-X (roscas excl.)": (7945, 5906),
}
DIAMETROS = ["5/8\"", "3/4\"", "7/8\"", "1\"", "1-1/8\"", "1-1/4\""]
_DB_IN = {"5/8\"": 0.625, "3/4\"": 0.75, "7/8\"": 0.875, "1\"": 1.0, "1-1/8\"": 1.125, "1-1/4\"": 1.25}
_EDGE_IN = {"5/8\"": 0.875, "3/4\"": 1.0, "7/8\"": 1.125, "1\"": 1.25, "1-1/8\"": 1.5, "1-1/4\"": 1.625}   # J3.4 (borde cizallado)
_TB_KIP = {"A325": [19, 28, 39, 51, 56, 71], "A490": [24, 35, 49, 64, 80, 102]}


def db_in(diam):
    return _DB_IN[diam]


def perno(diam, grado):
    """Propiedades de un perno: dict(db, Ab, dh, edge, Fnt, Fnv, Tb) en cm, cm², kgf/cm², kgf."""
    d = _DB_IN[diam]
    fam = "A490" if grado.startswith("A490") else "A325"
    tb = _TB_KIP[fam][DIAMETROS.index(diam)] * KIP
    fnt, fnv = PERNOS[grado]
    return {"db": d * IN, "Ab": math.pi * (d * IN) ** 2 / 4, "dh": (d + (1 / 16 if d < 1 else 1 / 8)) * IN,
            "dh_net": (d + (1 / 16 if d < 1 else 1 / 8) + 1 / 16) * IN, "edge": _EDGE_IN[diam] * IN,
            "Fnt": fnt, "Fnv": fnv, "Tb": tb}


# ── pernos (J3) ────────────────────────────────────────────────────────────────────────────────────────
def rn_corte_perno(Fnv, Ab, ns=1.0, phi=0.75):
    """J3.6: φ·Fnv·Ab·ns."""
    return phi * Fnv * Ab * ns


def rn_deslizamiento(mu, Tb, ns=1.0, hf=1.0, Du=1.13, phi=1.0):
    """J3.8(a), resistencia al nivel de resistencia: φ·μ·Du·hf·Tb·ns (agujeros estándar)."""
    return phi * mu * Du * hf * Tb * ns


def rn_aplastamiento(db, t, Fu, Lc, phi=0.75):
    """J3.10: φ·mín(1.2·Lc·t·Fu ; 2.4·db·t·Fu) (deformación en servicio considerada)."""
    return phi * min(1.2 * Lc * t * Fu, 2.4 * db * t * Fu)


# ── elementos (J4) ─────────────────────────────────────────────────────────────────────────────────────
def rn_fluencia_traccion(Fy, Ag, phi=0.90):
    return phi * Fy * Ag                                   # J4.1(a)


def rn_ruptura_traccion(Fu, Ae, phi=0.75):
    return phi * Fu * Ae                                   # J4.1(b)


def rn_fluencia_corte(Fy, Agv, phi=1.00):
    return phi * 0.6 * Fy * Agv                            # J4.2(a)


def rn_ruptura_corte(Fu, Anv, phi=0.75):
    return phi * 0.6 * Fu * Anv                            # J4.2(b)


def rn_bloque_corte(Agv, Anv, Ant, Fy, Fu, Ubs=1.0, phi=0.75):
    """J4.3: φ·mín(0.6·Fu·Anv + Ubs·Fu·Ant ; 0.6·Fy·Agv + Ubs·Fu·Ant)."""
    return phi * min(0.6 * Fu * Anv + Ubs * Fu * Ant, 0.6 * Fy * Agv + Ubs * Fu * Ant)


# ── soldaduras (J2) ────────────────────────────────────────────────────────────────────────────────────
def rn_filete(FEXX, w, L, theta_deg=0.0, phi=0.75):
    """J2.4 / Manual 8: φ·0.6·FEXX·(1 + 0.5·sen^1.5 θ)·0.707·w·L  (w, L en cm)."""
    k = 1.0 + 0.50 * math.sin(math.radians(theta_deg)) ** 1.5
    return phi * 0.6 * FEXX * k * 0.707 * w * L


def t_min_soporte(FEXX, Fu, w, lados=2):
    """Manual Ec. 9-2 / 9-3: espesor mínimo del soporte para desarrollar los filetes (w en cm).
    lados = 1 (filete en una cara del soporte: 6.19·D/Fu) o 2 (placa soldada por ambas caras: 3.09·D/Fu)."""
    return (0.707 * w * FEXX / Fu) * (1.0 if lados == 2 else 2.0)


# ── concentración de fuerzas en columnas (J10) ────────────────────────────────────────────────────────────────
def rn_flexion_local_ala(Fyf, tf, phi=0.90):
    return phi * 6.25 * tf ** 2 * Fyf                      # J10-1


def rn_fluencia_local_alma(Fyw, tw, k, N, interior=True, phi=1.00):
    """J10-2 / J10-3: (5k + N)·Fyw·tw lejos del extremo; (2.5k + N)·Fyw·tw cerca del extremo."""
    return phi * (5 * k + N if interior else 2.5 * k + N) * Fyw * tw


def rn_aplastamiento_alma(Fyw, tw, tf, d, N, interior=True, phi=0.75):
    """J10-4 (≥ d/2 del extremo) y J10-5a/b (< d/2)."""
    q = math.sqrt(E * Fyw * tf / tw)
    if interior:
        return phi * 0.80 * tw ** 2 * (1 + 3 * (N / d) * (tw / tf) ** 1.5) * q
    f = (1 + 3 * (N / d) * (tw / tf) ** 1.5) if N / d <= 0.2 else (1 + (4 * N / d - 0.2) * (tw / tf) ** 1.5)
    return phi * 0.40 * tw ** 2 * f * q


def rn_pandeo_alma(Fyw, tw, h, interior=True, phi=0.90):
    """J10-8: 24·tw³·√(E·Fyw)/h (×0.5 cerca del extremo)."""
    return phi * 24 * tw ** 3 * math.sqrt(E * Fyw) / h * (1.0 if interior else 0.5)


def rn_zona_panel(Fy, dc, tw, Pr=0.0, Py=1.0, phi=0.90):
    """J10-9 / J10-10 sin efecto del ala de la columna (conservador)."""
    f = 1.0 if Pr <= 0.4 * Py else 1.4 - Pr / Py
    return phi * 0.60 * Fy * dc * tw * f


# ── geometría de gusset ───────────────────────────────────────────────────────────────────────────────────────
def ancho_whitmore(gramil, L, angulo=30.0):
    """Manual Fig. 9-1: lw = g + 2·L·tan 30°."""
    return gramil + 2 * L * math.tan(math.radians(angulo))


# ── elementos en compresión (E3 / J4.4) ───────────────────────────────────────────────────────────────────────
def fcr_compresion(Fy, KLr):
    """E3: esfuerzo crítico de pandeo por flexión."""
    Fe = math.pi ** 2 * E / KLr ** 2
    return 0.658 ** (Fy / Fe) * Fy if KLr <= 4.71 * math.sqrt(E / Fy) else 0.877 * Fe


def rn_compresion_placa(Fy, Ag, KLr, phi=0.90):
    """J4.4: φ·Fy·Ag si KL/r ≤ 25; si no, E3."""
    return phi * (Fy if KLr <= 25 else fcr_compresion(Fy, KLr)) * Ag


# ── placa transversal a HSS rectangular (Spec. K1.3b; DG24 Tabla 7-2) ─────────────────────────────────────────────
def hss_flujo_placa(Fy, t, B, Bp, Fyp, tp, phi=0.95):
    """K1-2: fluencia local de la placa (ala) por distribución desigual: φ·mín(10/(B/t)·Fy·t·Bp ; Fyp·tp·Bp)."""
    return phi * min(10.0 / (B / t) * Fy * t * Bp, Fyp * tp * Bp)


def hss_punzonamiento(Fy, t, B, Bp, tp, phi=0.95):
    """K1-3 (0.85·B ≤ Bp ≤ B − 2t): φ·0.6·Fy·t·(2tp + 2Bep), Bep = 10·Bp/(B/t) ≤ Bp."""
    Bep = min(10.0 * Bp / (B / t), Bp)
    return phi * 0.6 * Fy * t * (2 * tp + 2 * Bep)


def hss_pared_fluencia(Fy, t, N, k=None, phi=1.0):
    """K1-4 (Bp = B): 2·Fy·t·(5k + N), k = radio exterior ≈ 1.5t."""
    k = 1.5 * t if k is None else k
    return phi * 2 * Fy * t * (5 * k + N)


def hss_pared_aplastamiento(Fy, t, H, N, Qf=1.0, phi=0.75):
    """K1-5 (Bp = B, placa a compresión, conexión en T): 1.6·t²·(1 + 3N/(H − 3t))·√(E·Fy)·Qf."""
    return phi * 1.6 * t ** 2 * (1 + 3 * N / (H - 3 * t)) * math.sqrt(E * Fy) * Qf


def hss_pared_pandeo(Fy, t, H, Qf=1.0, phi=0.90):
    """K1-6 (Bp = B, placas a compresión a ambos lados): 48·t³/(H − 3t)·√(E·Fy)·Qf."""
    return phi * 48 * t ** 3 / (H - 3 * t) * math.sqrt(E * Fy) * Qf


def hss_Qf(U, beta, compresion=True):
    """K2-10: Qf = 1 en tracción; 1.3 − 0.4·U/β ≤ 1 en compresión (placa transversal)."""
    return min(1.3 - 0.4 * U / beta, 1.0) if compresion else 1.0


def hss_props(B, H, t):
    """Área y módulo elástico aproximados de un HSS (sin radios de esquina; cm, cm², cm³)."""
    A = 2 * t * (B + H - 2 * t)
    S = (B * H ** 3 - (B - 2 * t) * (H - 2 * t) ** 3) / (6 * H)
    return A, S
