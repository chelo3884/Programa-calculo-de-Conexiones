"""Motor de cálculo — conexión de momento con placa extrema extendida (4E / 4ES / 8ES).

Evalúa el modelo generado desde END_PLATE_AISC_DG4.xlsx (AISC Design Guide 4, 2.ª ed.;
AISC 358-16 cap. 6; AISC 360-16 J2, J3, J4, J10; LRFD). Ver tools/xl2py.py.

Unidades de ENTRADA y SALIDA (canónicas, igual que la hoja): fuerzas Tonf · momentos Tonf·m ·
dimensiones mm · luz L en m · esfuerzos kgf/cm². Internamente se calcula en kgf y cm.
Cada valor de la memoria lleva una etiqueta `q` de magnitud:
    F fuerza [Tonf] · M momento [Tonf·m] · S esfuerzo [kgf/cm²] · Ls longitud [mm] · Lc longitud [cm]
    A área [cm²] · V módulo [cm³] · FL fuerza/longitud [kgf/cm] · '' adimensional u otras
"""
from __future__ import annotations

import json
import math
import os

from . import xl_model as M

_DIR = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(_DIR, "catalogos.json"), encoding="utf-8") as _f:
    CAT = json.load(_f)
with open(os.path.join(_DIR, "inputs_spec.json"), encoding="utf-8") as _f:
    SPEC = json.load(_f)

NCOMBO = 10

# unidad de la hoja → (magnitud de la interfaz, factor desde kgf/cm a la unidad canónica)
_UNIT = {"cm": ("Lc", 1.0), "mm": ("Ls", 1.0), "kgf": ("F", 1e-3), "kgf·cm": ("M", 1e-5),
         "kgf/cm²": ("S", 1.0), "Tonf·m": ("M", 1.0), "Tonf": ("F", 1.0), "cm²": ("A", 1.0),
         "cm³": ("V", 1.0), "kgf/cm": ("FL", 1.0)}


# ───────────────────────── funciones de hoja de cálculo ─────────────────────────
def _col(letters):
    n = 0
    for ch in letters:
        n = n * 26 + ord(ch) - 64
    return n


def _letters(n):
    s = ""
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def _cat(c1, r1, c2, r2):
    if c1 == c2:
        col = CAT.get(c1, [])
        return [col[r - 1] if r - 1 < len(col) else None for r in range(r1, r2 + 1)]
    out = []
    for c in range(_col(c1), _col(c2) + 1):
        col = CAT.get(_letters(c), [])
        out.append(col[r1 - 1] if r1 - 1 < len(col) else None)
    return out


def _flat(args):
    for a in args:
        if isinstance(a, (list, tuple)):
            yield from _flat(a)
        elif isinstance(a, (int, float)) and not isinstance(a, bool):
            yield a


def _min(*a):
    v = list(_flat(a))
    return min(v) if v else 0


def _max(*a):
    v = list(_flat(a))
    return max(v) if v else 0


def _isnum(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _n(x):
    return x if _isnum(x) else (1 if x is True else 0)


def _count(*a):
    return len(list(_flat(a)))


def _and(*a):
    return all(bool(x) for x in a)


def _or(*a):
    return any(bool(x) for x in a)


def _sqrt(x):
    return math.sqrt(x)


def _eq(a, b):
    if a is None:
        a = "" if isinstance(b, str) else 0
    if b is None:
        b = "" if isinstance(a, str) else 0
    if isinstance(a, str) and isinstance(b, str):
        return a.lower() == b.lower()
    return a == b


def _match(x, rng, kind=0):
    for i, v in enumerate(rng):
        if _eq(v, x):
            return i + 1
    raise ValueError("#N/A")


def _index(rng, n):
    return rng[int(n) - 1]


def _s(x):
    return "" if x is None else str(x)


def _text(x, fmt):
    return f"{x:.2f}"


def _iferror(f, g):
    try:
        return f()
    except (ZeroDivisionError, ValueError, TypeError, IndexError, OverflowError):
        return g()


_BASE = {"math": math, "_cat": _cat, "_min": _min, "_max": _max, "_isnum": _isnum, "_n": _n,
         "_count": _count, "_and": _and, "_or": _or, "_sqrt": _sqrt, "_eq": _eq, "_match": _match,
         "_index": _index, "_s": _s, "_text": _text, "_iferror": _iferror, "abs": abs, "int": int,
         "__builtins__": {}}
_ERR = (ZeroDivisionError, ValueError, TypeError, IndexError, OverflowError, KeyError)
_CODE: dict = {}


def _code(src):
    c = _CODE.get(src)
    if c is None:
        c = _CODE[src] = compile(src, "<xl>", "eval")
    return c


def _ev(src, env):
    try:
        return eval(_code(src), env)          # noqa: S307  (expresiones generadas desde la hoja, no del usuario)
    except _ERR:
        return None


def defaults():
    d = {}
    for sec in SPEC["secciones"]:
        for c in sec["campos"]:
            d[c["name"]] = c["default"]
    return d


def _estado(r, lim):
    if not _isnum(r):
        return "N/A"
    if r > 1.0:
        return "NO CUMPLE"
    if r > lim:
        return "AL LÍMITE"
    return "CUMPLE"


def _tr(unit, val):
    q, f = _UNIT.get(unit, ("", 1.0))
    return q, (val * f if _isnum(val) else val)


def calcular(inp: dict) -> dict:
    env = dict(_BASE)
    env.update(defaults())
    for k, v in inp.items():
        if k != "combos":
            env[k] = v
    combos_in = list(inp.get("combos", []))[:NCOMBO]
    combos_in += [{}] * (NCOMBO - len(combos_in))
    env["cb_nom"] = [c.get("nombre") or None for c in combos_in]
    env["cb_M"] = [c.get("M") for c in combos_in]
    env["cb_V"] = [c.get("V") for c in combos_in]
    lim = float(env.get("lim_verde", 0.9))

    for _r, nm, _lab, _un, code in M.DERIVED:
        env[nm] = _ev(code, env)

    mem_global, sec = [], ""
    raw_global, raw_combo = {}, {}
    for row, sym, desc, unit, nm, code in M.GLOBAL:
        if sym == "SECCION":
            sec = desc
            continue
        val = _ev(code, env) if code and code != repr(None) else None
        if nm.startswith("g") and nm[1:].isdigit():
            env[nm] = val
        else:
            env[nm] = val
            env[f"g{row}"] = val
        raw_global[row] = val
        q, v = _tr(unit, val)
        mem_global.append({"row": row, "sec": sec, "sym": sym, "desc": desc, "unit": unit, "q": q, "val": v})

    # filas por combinación
    rows: dict = {}
    combos = []
    for idx in range(1, NCOMBO + 1):
        cenv = dict(env)
        cenv["IDX_"] = idx
        trace = []
        for row, sym, desc, unit, code in M.COMBO:
            val = _ev(code, cenv)
            cenv[f"r{row}"] = val
            rows.setdefault(row, [None] * NCOMBO)[idx - 1] = val
            q, v = _tr(unit, val)
            trace.append({"row": row, "sec": "8. COMBINACIÓN", "sym": sym, "desc": desc, "unit": unit, "q": q, "val": v})
        activo = cenv.get("r111") == 1
        nombre = cenv.get("r110")
        combos.append({"idx": idx, "nombre": nombre if isinstance(nombre, str) else "", "activo": bool(activo),
                       "ratio_max": cenv.get("r138") if activo else None,
                       "Mu": (cenv.get("r112") or 0) / 1e5, "Vu": (cenv.get("r113") or 0) / 1e3,
                       "db_req": cenv.get("r114"), "Ffu": (cenv.get("r115") or 0) / 1e3,
                       "trace": trace if activo else []})

    env["_row"] = lambda n: rows[n]
    checks, grupo = [], ""
    for row, tipo, nombre, ref, unit, P, Q, S, U in M.CHECKS:
        if tipo == "GRUPO":
            grupo = nombre
            continue
        dem, cap, ratio = _ev(P, env), _ev(Q, env), _ev(S, env)
        env[f"DIS_S{row}"] = ratio              # la columna "Combo" de la hoja se refiere a la celda de ratio
        combo = _ev(U, env)
        q = {"Tonf·m": "M", "Tonf": "F", "kgf/cm": "FL", "mm": "Ls", "cm": "Lc"}.get(unit, "")
        checks.append({"fila": row, "grupo": grupo, "nombre": nombre, "ref": ref, "unit": unit, "q": q,
                       "dem": dem if _isnum(dem) else None, "cap": cap if _isnum(cap) else None,
                       "ratio": ratio if _isnum(ratio) else None,
                       "estado": _estado(ratio, lim), "combo": combo if isinstance(combo, str) else "—"})

    ratios = [c["ratio"] for c in checks if c["ratio"] is not None]
    activos = any(c["activo"] for c in combos)
    rmax = max(ratios) if ratios else None
    if not activos:
        msg = "SIN CARGAS"
    elif rmax is not None and rmax > 1:
        msg = "NO CUMPLE"
    elif rmax is not None and rmax > lim:
        msg = "CUMPLE AL LÍMITE"
    else:
        msg = "CUMPLE"

    keep = ("k_d", "k_bf", "k_tw", "k_tf", "k_cd", "k_cbf", "k_ctw", "k_ctf", "k_bp", "k_tp", "k_g", "k_pfo",
            "k_pfi", "k_pb", "k_de", "k_Hp", "k_db", "k_dh", "k_Lst", "k_hst", "k_is4E", "k_is8", "k_seis",
            "k_Yp", "k_Yc", "k_sh", "k_s", "k_sc", "k_Mnp", "k_phin", "k_phiMpl", "k_phiMcf", "k_wtC", "k_wtD")
    varsd = {k: env.get(k) for k in keep}
    varsd["cp_usar"] = env.get("cp_usar")
    varsd["cp_t"] = env.get("cp_t")
    varsd["cp_b"] = env.get("cp_b")
    varsd["st_t"] = env.get("st_t")
    varsd["cfg"] = env.get("cfg")
    derivados = {nm: env.get(nm) for _r, nm, *_ in M.DERIVED}
    raw = {"global": raw_global, "rows": rows}
    for c in checks:
        c["raw_dem"], c["raw_cap"] = c["dem"], c["cap"]
    return {"resumen": {"estado": msg, "ratio_max": rmax}, "checks": checks, "combos": combos, "raw": raw,
            "memoria_global": mem_global, "vars": varsd, "derivados": derivados}
