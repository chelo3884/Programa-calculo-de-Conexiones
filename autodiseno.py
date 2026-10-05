"""Autodiseño: busca la combinación de parámetros discretos de menor costo (≈ masa de acero) con todos los ratios ≤ límite.

Para cada módulo se declara una lista de variables (nombre de campo —con punto para entradas anidadas—, candidatos en
orden de costo creciente) y una función de costo relativo. La búsqueda es «el mejor primero» sobre el retículo de
candidatos: se evalúa cada propuesta con el mismo motor de cálculo de la interfaz, de menor a mayor costo, y se devuelve
la primera que cumple (ratio máx. ≤ límite verde). Si no hay ninguna, se informa la de menor ratio máximo evaluada.
El costo es una referencia relativa (aproximación de la masa de acero en kg), no un presupuesto.
"""
from __future__ import annotations

import copy
import heapq
import math
import time

RHO = 7.85e-6  # kg/mm³
GRUESOS = [6, 8, 10, 12, 16, 19, 22, 25, 32, 38, 45, 50, 57, 63, 76]
FILETES = [4, 5, 6, 8, 10, 12, 14, 16, 19]
DIAMS = ['5/8"', '3/4"', '7/8"', '1"', '1-1/8"', '1-1/4"', '1-3/8"', '1-1/2"']


def _get(d, ruta):
    for k in ruta.split("."):
        d = d[k]
    return d


def _set(d, ruta, v):
    ks = ruta.split(".")
    for k in ks[:-1]:
        d = d[k]
    d[ks[-1]] = v


def _in(txt):
    """'1-1/8"' → 1.125 (pulgadas)."""
    t = str(txt).replace('"', "").strip()
    if "-" in t:
        a, b = t.split("-", 1)
        return float(a) + _in(b)
    if "/" in t:
        n, d = t.split("/")
        return float(n) / float(d)
    return float(t)


def _bolts(n, diam, largo=60.0):
    """Masa de n pernos (kg): vástago + cabeza/tuerca ≈ 2.5 diámetros extra."""
    d = _in(diam) * 25.4
    return n * math.pi / 4 * d * d * (largo + 2.5 * d) * RHO


def _fillet(w, largo):
    return 0.5 * w * w * largo * RHO


def _f(inp, k, d=0.0):
    try:
        return float(inp.get(k, d) or d)
    except (TypeError, ValueError):
        return d


def _abs(inp, k, paso=50, n=5):
    v = _f(inp, k)
    return [v + i * paso for i in range(n)]


# ── costos relativos por módulo ──────────────────────────────────────────────────────────────────────────────
def _c_placa_base(i):
    p, pn, s = i["placa"], i["pernos"], i["sold"]
    n = 2 * int(pn["nfila"])
    da = _in(pn["diam"]) * 25.4
    return (p["N"] * p["B"] * p["tp"] * RHO + _bolts(n, pn["diam"], pn["hef"] * 1.0)
            + _fillet(s["wf"], 2 * i.get("armado", {}).get("bf", 200) * 2) + _fillet(s["ww"], 2 * 300))


def _c_end_plate(i):
    bp, tp = _f(i, "pl_bp", 200), _f(i, "pl_tp")
    nb = {"4E": 4, "4ES": 4, "8ES": 8}.get(i.get("cfg", "4E"), 4) * 2
    return (tp * bp * 600 * RHO + _bolts(nb, i["pn_diam"], tp + 40)
            + _f(i, "st_t") * 150 * 150 * RHO * (2 if i.get("cfg") != "4E" else 0)
            + (_f(i, "cp_t") * 2 * 110 * 250 * RHO * 2 if i.get("cp_usar") == "Sí" else 0)
            + _fillet(_f(i, "sd_wf"), 2 * 180) + _fillet(_f(i, "sd_ww"), 2 * 300))


def _c_bfp(i):
    L = _f(i, "pl_S1") + (_f(i, "n_b") / 2 - 1) * _f(i, "pl_s") + _f(i, "pl_Le")
    return (2 * _f(i, "pl_tp") * _f(i, "pl_bfp") * L * RHO + _bolts(2 * _f(i, "n_b"), i["pn_diam"], _f(i, "pl_tp") + 20)
            + _f(i, "w_t") * (_f(i, "w_n") * _f(i, "w_s") + 80) * 120 * RHO + _bolts(_f(i, "w_n"), i["w_diam"], 25)
            + _fillet(_f(i, "w_w"), 2 * _f(i, "w_n") * _f(i, "w_s"))
            + (_f(i, "cp_t") * 2 * 110 * 250 * RHO * 2 if i.get("cp_usar") == "Sí" else 0)
            + _f(i, "dp_t") * 400 * 400 * RHO)


def _c_rodilla(i):
    return (_f(i, "pl_tp") * _f(i, "pl_bp") * 600 * RHO + _bolts(8, i["pn_diam"], _f(i, "pl_tp") + 40)
            + (_f(i, "cp_t") * 2 * 110 * 250 * RHO * 2 if i.get("cp_usar") == "Sí" else 0)
            + _f(i, "dp_t") * 400 * 400 * RHO + _fillet(_f(i, "sd_wf"), 360) + _fillet(_f(i, "sd_ww"), 600))


def _c_cortante(i):
    n, s = _f(i, "n_b", 3), _f(i, "pn_s", 75)
    L = 2 * _f(i, "pn_Lev", 35) + (n - 1) * s
    doble = i.get("tipo") == "Doble ángulo apernado"
    placa = (_f(i, "an_t") * 2 * L * (_f(i, "an_lb", 76) + _f(i, "an_ls", 76)) * RHO if doble
             else _f(i, "pl_tp") * L * (_f(i, "pl_a", 65) + _f(i, "pl_Leh", 45)) * RHO)
    return placa + _bolts(n * (2 if doble else 1), i["pn_diam"], 30) + (0 if doble else _fillet(_f(i, "pl_w"), 2 * L))


def _c_wuf(i):
    n, s = _f(i, "pl_n", 3), _f(i, "pl_s", 76)
    L = 2 * _f(i, "pl_lev", 38) + (n - 1) * s
    return (_f(i, "pl_t") * L * 150 * RHO + _bolts(n, i["pn_diam"], 25) + _fillet(_f(i, "pl_w"), 2 * L)
            + (_f(i, "cp_t") * 2 * _f(i, "cp_b", 110) * 250 * RHO * 2 if i.get("cp_usar") == "Sí" else 0)
            + _f(i, "dp_t") * 400 * 400 * RHO)


def _c_gusset(i):
    a, b, t = _f(i, "g_a"), _f(i, "g_b"), _f(i, "g_t")
    n = _f(i, "b_n") * _f(i, "b_nl")
    return (0.5 * a * b * t * _f(i, "g_np", 1) * RHO + _bolts(n, i["pn_diam"], 2 * t)
            + _fillet(_f(i, "g_wb"), 2 * a) + _fillet(_f(i, "g_wc"), 2 * b))


def _c_emp_viga(i):
    return (2 * (_f(i, "pf_to") * _f(i, "pf_bo", 180) + (2 * _f(i, "pf_ti") * _f(i, "pf_bi", 70) if i.get("pf_in") == "Sí" else 0))
            * (2 * _f(i, "fa_n") * _f(i, "fa_s", 75) + 80) * RHO
            + _bolts(8 * _f(i, "fa_n"), i["fa_diam"], 40) + 2 * _f(i, "pw_t") * _f(i, "pw_h") * 200 * RHO
            + _bolts(4 * _f(i, "wa_nr") * _f(i, "wa_nc"), i["wa_diam"], 20))


def _c_emp_col(i):
    return (2 * 2 * _f(i, "pf_t") * _f(i, "pf_b") * (2 * _f(i, "fa_n") * _f(i, "fa_s", 75) + 80) * RHO
            + _bolts(8 * _f(i, "fa_n"), i["fa_diam"], 40) + 4 * _f(i, "pw_t") * _f(i, "pw_b") * 200 * RHO
            + _bolts(4 * _f(i, "wa_nr") * _f(i, "wa_nc"), i["wa_diam"], 20))


def _cnt(a, b):
    return list(range(a, b + 1))


# nombre → (etiqueta, candidatos | callable(inp) | None=usar opciones del campo)
CONFIG = {
    "placa_base": (_c_placa_base, [
        ("placa.tp", "Espesor de placa", GRUESOS), ("placa.N", "Largo de placa N", lambda i: _abs_n(i, "placa.N")),
        ("placa.B", "Ancho de placa B", lambda i: _abs_n(i, "placa.B")), ("pernos.diam", "Diámetro de pernos", DIAMS[1:]),
        ("pernos.hef", "Empotramiento hef", [200, 250, 300, 400, 500, 600, 750, 900, 1100]),
        ("pernos.nfila", "Pernos por fila lado (nfila)", [2, 3, 4]), ("sold.wf", "Filete en alas", FILETES),
        ("sold.ww", "Filete en alma", FILETES)]),
    "end_plate": (_c_end_plate, [("pl_tp", "Espesor de placa", GRUESOS[2:]), ("pn_diam", "Diámetro de pernos", DIAMS[1:]),
                                 ("sd_wf", "Filete ala", FILETES), ("sd_ww", "Filete alma", FILETES), ("st_t", "Rigidizador ts", GRUESOS[:11]),
                                 ("cp_t", "Rigidizador de continuidad", GRUESOS[:12])]),
    "bfp": (_c_bfp, [("pl_tp", "Espesor de placa de ala", GRUESOS[3:]), ("n_b", "Pernos por ala", [4, 6, 8, 10, 12, 14, 16]),
                     ("pn_diam", "Diámetro de pernos", DIAMS[1:6]), ("w_t", "Placa de alma", GRUESOS[:11]),
                     ("w_n", "Pernos de alma", [2, 3, 4, 5, 6, 7]), ("w_w", "Filete placa de alma", FILETES),
                     ("cp_t", "Rigidizador de continuidad", GRUESOS[:12]), ("dp_t", "Placa de refuerzo", [0, 6, 8, 10, 12, 16, 19])]),
    "rodilla": (_c_rodilla, [("pl_tp", "Espesor de placa", GRUESOS[2:]), ("pn_diam", "Diámetro de pernos", DIAMS[1:6]),
                             ("sd_wf", "Filete ala", FILETES), ("sd_ww", "Filete alma", FILETES),
                             ("cp_t", "Rigidizador de continuidad", GRUESOS[:12]), ("dp_t", "Placa de refuerzo", [0, 6, 8, 10, 12, 16, 19])]),
    "cortante_vv": (_c_cortante, [("pl_tp", "Espesor de placa", [5, 6, 8, 10, 12, 16, 19, 22, 25]), ("n_b", "Número de pernos", _cnt(2, 12)),
                                  ("pn_diam", "Diámetro de pernos", DIAMS[:5]), ("pl_w", "Filete placa", FILETES),
                                  ("an_t", "Espesor de ángulos", [5, 6, 8, 10, 12, 16])]),
    "gusset": (_c_gusset, [("g_t", "Espesor de cartela", GRUESOS[1:11]), ("g_a", "Longitud a", lambda i: _abs_n(i, "g_a", 50, 7)),
                           ("g_b", "Longitud b", lambda i: _abs_n(i, "g_b", 50, 7)), ("b_n", "Pernos por línea", _cnt(2, 10)),
                           ("b_nl", "Líneas de pernos", [1, 2, 3]), ("pn_diam", "Diámetro de pernos", DIAMS[1:6]),
                           ("g_wb", "Filete a viga", FILETES), ("g_wc", "Filete a columna", FILETES)]),
    "wuf": (_c_wuf, [("pl_t", "Espesor de placa de alma", GRUESOS[:11]), ("pl_n", "Número de pernos", _cnt(2, 10)),
                     ("pn_diam", "Diámetro de pernos", DIAMS[1:6]), ("pl_w", "Filete placa–columna", FILETES),
                     ("cp_t", "Rigidizador de continuidad", GRUESOS[:12]), ("dp_t", "Placa de refuerzo", [0, 6, 8, 10, 12, 16, 19])]),
    "empalme_viga": (_c_emp_viga, [("pf_to", "Placa de ala exterior", GRUESOS[1:11]), ("pf_ti", "Placas interiores", GRUESOS[1:10]),
                                   ("fa_n", "Filas de pernos de ala", _cnt(2, 8)), ("fa_diam", "Diámetro pernos ala", DIAMS[1:6]),
                                   ("pw_t", "Placas de alma", GRUESOS[:10]), ("wa_nr", "Filas pernos de alma", _cnt(2, 8)),
                                   ("wa_diam", "Diámetro pernos alma", DIAMS[1:6])]),
    "empalme_col": (_c_emp_col, [("pf_t", "Placas de ala", GRUESOS[1:11]), ("fa_n", "Filas de pernos de ala", _cnt(2, 8)),
                                 ("fa_diam", "Diámetro pernos ala", DIAMS[1:6]), ("pw_t", "Placas de alma", GRUESOS[:10]),
                                 ("wa_nr", "Filas pernos de alma", _cnt(2, 6)), ("wa_diam", "Diámetro pernos alma", DIAMS[1:6])]),
}
CONFIG["cortante_vc"] = CONFIG["cortante_vv"]
CONFIG["cortante_hss"] = (_c_cortante, [v for v in CONFIG["cortante_vv"][1] if v[0] != "an_t"])


def _abs_n(i, ruta, paso=50, n=5):
    try:
        v = float(_get(i, ruta))
    except (KeyError, TypeError):
        return []
    return [v + k * paso for k in range(n)]


_DOBLE = lambda i: i.get("tipo") == "Doble ángulo apernado"  # noqa: E731
_CP = lambda i: i.get("cp_usar") == "Sí"  # noqa: E731
APLICA = {
    "end_plate": {"st_t": lambda i: i.get("cfg") != "4E", "cp_t": _CP},
    "bfp": {"cp_t": _CP},
    "rodilla": {"cp_t": _CP},
    "wuf": {"cp_t": _CP},
    "cortante_vv": {"an_t": _DOBLE, "pl_tp": lambda i: not _DOBLE(i), "pl_w": lambda i: not _DOBLE(i)},
    "cortante_vc": {"an_t": _DOBLE, "pl_tp": lambda i: not _DOBLE(i), "pl_w": lambda i: not _DOBLE(i)},
    "empalme_viga": {"pf_ti": lambda i: i.get("pf_in") == "Sí"},
}


def variables(modulo: str, inp: dict, opciones_campo: dict | None = None):
    """Variables disponibles: [{name, label, cands, actual}] (candidatos filtrados a los valores válidos)."""
    costo, vs = CONFIG[modulo]
    out = []
    for name, label, cands in vs:
        if name in APLICA.get(modulo, {}) and not APLICA[modulo][name](inp):
            continue
        try:
            actual = _get(inp, name)
        except (KeyError, TypeError):
            continue
        c = cands(inp) if callable(cands) else list(cands)
        if opciones_campo and name in opciones_campo and opciones_campo[name]:
            c = [x for x in opciones_campo[name] if (x in c or not isinstance(x, (int, float)))] or c
        if actual not in c:
            c = sorted(set(c) | {actual}, key=lambda x: (_in(x) if isinstance(x, str) else x))
        out.append({"name": name, "label": label, "cands": c, "actual": actual})
    return out


def buscar(modulo, calcular, inp, nombres=None, lim=None, max_eval=4000, max_seg=20.0, opciones_campo=None):
    costo, _ = CONFIG[modulo]
    base = copy.deepcopy(inp)
    lim = float(lim if lim is not None else base.get("lim_verde", 0.9))
    vs = [v for v in variables(modulo, base, opciones_campo) if (nombres is None or v["name"] in nombres)]
    if not vs:
        raise ValueError("No hay variables para optimizar")

    def armar(idx):
        d = copy.deepcopy(base)
        for v, k in zip(vs, idx):
            _set(d, v["name"], v["cands"][k])
        return d

    def evaluar(idx):
        d = armar(idx)
        try:
            r = calcular(d)
            rm = r["resumen"].get("ratio_max")
            return d, (math.inf if rm is None else rm), r
        except (ValueError, KeyError, TypeError, ZeroDivisionError):
            return d, math.inf, None

    # monotonía supuesta: el costo crece con el índice; se explora desde el menor
    ini = tuple(0 for _ in vs)
    heap = [(costo(armar(ini)), ini)]
    clave = lambda dd, ix: costo(dd) + 1e-6 * sum(ix)  # noqa: E731 (desempate: menos escalones)
    vistos = {ini}
    n, t0 = 0, time.time()
    mejor = None
    while heap and n < max_eval and time.time() - t0 < max_seg:
        c, idx = heapq.heappop(heap)
        d, rm, r = evaluar(idx)
        n += 1
        if r is not None and (mejor is None or rm < mejor[1]):
            mejor = (d, rm, c, idx, r)
        if rm <= lim and r is not None and r["resumen"]["estado"] != "SIN CARGAS":
            return _respuesta(True, vs, idx, d, rm, c, n, base, lim, r)
        for j in range(len(vs)):
            if idx[j] + 1 < len(vs[j]["cands"]):
                nx = idx[:j] + (idx[j] + 1,) + idx[j + 1:]
                if nx not in vistos:
                    vistos.add(nx)
                    dn = armar(nx)
                    heapq.heappush(heap, (clave(dn, nx), nx))
    # 2) se agotó el presupuesto de evaluaciones: ascenso voraz hasta cumplir y luego poda
    idx = ini
    d, rm, r = evaluar(idx)
    while rm > lim:
        cand = []
        for j in range(len(vs)):
            if idx[j] + 1 < len(vs[j]["cands"]):
                nx = idx[:j] + (idx[j] + 1,) + idx[j + 1:]
                dd, rr, _ = evaluar(nx)
                cand.append((rr, costo(dd), nx))
        if not cand:
            break
        _, _, idx = min(cand)
        d, rm, r = evaluar(idx)
    mejorado = True
    while mejorado and rm <= lim:
        mejorado = False
        for j in range(len(vs)):
            if idx[j] > 0:
                nx = idx[:j] + (idx[j] - 1,) + idx[j + 1:]
                dd, rr, _ = evaluar(nx)
                if rr <= lim and costo(dd) <= costo(d) + 1e-9:
                    idx, d, rm, mejorado = nx, dd, rr, True
    if rm > lim and mejor is not None and mejor[1] < rm:
        d, rm, _c, idx, r = mejor
    resp = _respuesta(rm <= lim, vs, idx, d, rm, costo(d), n, base, lim, None, agotado=bool(heap))
    if rm <= lim:
        resp["mensaje"] = "Se encontró un diseño que cumple (búsqueda voraz: puede no ser el de menor costo)."
    else:
        rr = r if r is not None else calcular(d)
        gob = max((c for c in rr["checks"] if c.get("ratio") is not None), key=lambda c: c["ratio"], default=None)
        resp["mensaje"] = ("Ninguna combinación de las variables marcadas alcanza el ratio objetivo"
                           + (f" (gobierna: {gob['nombre']}, ratio {gob['ratio']:.2f})" if gob else "")
                           + ". Revise otros datos (perfiles, pedestal, cargas) o amplíe las variables.")
    return resp


def _respuesta(ok, vs, idx, d, rm, c, n, base, lim, r, agotado=False):
    cambios = [{"name": v["name"], "label": v["label"], "de": v["actual"], "a": v["cands"][k]}
               for v, k in zip(vs, idx) if v["cands"][k] != v["actual"]]
    return {"ok": ok, "ratio_max": rm, "costo": round(c, 2), "evaluaciones": n, "lim": lim, "cambios": cambios,
            "propuesta": {v["name"]: v["cands"][k] for v, k in zip(vs, idx)},
            "agotado": agotado,
            "mensaje": ("Se encontró un diseño que cumple con el ratio objetivo." if ok else
                        "No se encontró un diseño que cumpla con las variables seleccionadas; se muestra el de menor ratio evaluado.")}
