"""Núcleo de evaluación de los modelos generados desde las hojas de Excel (tools/xl2py.py).

Cada módulo (end_plate, bfp, rodilla) tiene un paquete con:
    xl_model.py       filas de fórmulas generadas (DERIVED, GLOBAL, COMBO, CHECKS)
    catalogos.json    hoja CATALOGOS por columna
    inputs_spec.json  campos de entrada para la interfaz
`XlModule(paquete).calcular(entradas)` evalúa el modelo igual que la hoja de Excel.

Unidades de entrada y salida (canónicas, las de la hoja): Tonf · Tonf·m · mm · m · kgf/cm².
Internamente se calcula en kgf y cm. Cada valor lleva una magnitud `q` para convertirlo en la interfaz:
    F fuerza [Tonf] · M momento [Tonf·m] · S esfuerzo [kgf/cm²] · Ls longitud [mm] · Lc longitud [cm]
    A área [cm²] · V módulo [cm³] · FL fuerza/longitud [kgf/cm] · '' adimensional u otras
"""
from __future__ import annotations

import json
import math
import os

# unidad de la hoja → (magnitud de la interfaz, factor desde kgf/cm a la unidad canónica)
_UNIT = {"cm": ("Lc", 1.0), "mm": ("Ls", 1.0), "kgf": ("F", 1e-3), "kgf·cm": ("M", 1e-5),
         "kgf/cm²": ("S", 1.0), "Tonf·m": ("M", 1.0), "Tonf": ("F", 1.0), "cm²": ("A", 1.0),
         "cm³": ("V", 1.0), "kgf/cm": ("FL", 1.0)}
_CHECK_Q = {"Tonf·m": "M", "Tonf": "F", "kgf/cm": "FL", "mm": "Ls", "cm": "Lc", "kgf/cm²": "S", "m": "Lm"}


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


def _iferror(f, g):
    try:
        return f()
    except (ZeroDivisionError, ValueError, TypeError, IndexError, OverflowError):
        return g()


_ERR = (ZeroDivisionError, ValueError, TypeError, IndexError, OverflowError, KeyError)
_CODE: dict = {}


def _code(src):
    c = _CODE.get(src)
    if c is None:
        c = _CODE[src] = compile(src, "<xl>", "eval")
    return c


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


class XlModule:
    def __init__(self, pkg_dir, model):
        self.M = model
        with open(os.path.join(pkg_dir, "catalogos.json"), encoding="utf-8") as fh:
            self.CAT = json.load(fh)
        with open(os.path.join(pkg_dir, "inputs_spec.json"), encoding="utf-8") as fh:
            self.SPEC = json.load(fh)
        CAT = self.CAT

        def _cat(c1, r1, c2, r2):
            if c1 == c2:
                col = CAT.get(c1, [])
                return [col[r - 1] if r - 1 < len(col) else None for r in range(r1, r2 + 1)]
            out = []
            for c in range(_col(c1), _col(c2) + 1):
                col = CAT.get(_letters(c), [])
                out.append(col[r1 - 1] if r1 - 1 < len(col) else None)
            return out

        self._base = {"math": math, "_cat": _cat, "_min": _min, "_max": _max, "_isnum": _isnum, "_n": _n,
                      "_count": _count, "_and": _and, "_or": _or, "_sqrt": math.sqrt, "_eq": _eq, "_match": _match,
                      "_index": _index, "_s": _s, "_text": lambda x, f: f"{x:.2f}", "_iferror": _iferror,
                      "abs": abs, "int": int, "round": round, "__builtins__": {}}
        self.NCOMBO = model.NCOMBO

    # ------------------------------------------------------------------------------------------
    def defaults(self):
        d = {}
        for sec in self.SPEC["secciones"]:
            for c in sec["campos"]:
                d[c["name"]] = c["default"]
        return d

    @staticmethod
    def _ev(src, env):
        try:
            return eval(_code(src), env)          # noqa: S307  (expresiones generadas desde la hoja, no del usuario)
        except _ERR:
            return None

    def calcular(self, inp: dict) -> dict:
        M, ev = self.M, self._ev
        env = dict(self._base)
        env.update(self.defaults())
        for k, v in inp.items():
            if k != "combos":
                env[k] = v
        n = self.NCOMBO
        sc = self.SPEC.get("combos")
        if sc:
            filas = list(inp.get("combos", []))[:n]
            filas += [{}] * (n - len(filas))
            for col in sc["cols"]:
                key = col["key"]
                vals = [f.get(key) for f in filas]
                env[col["name"]] = [v if v not in ("",) else None for v in vals]
        lim = float(env.get("lim_verde", 0.9))

        for _r, nm, _lab, _un, code in M.DERIVED:
            env[nm] = ev(code, env)

        mem_global, raw_global = [], {}
        for row, sec, sym, desc, unit, nm, code in M.GLOBAL:
            val = ev(code, env) if code != "None" else None
            env[nm] = val
            env[f"g{row}"] = val
            raw_global[row] = val
            q, v = _tr(unit, val)
            mem_global.append({"row": row, "sec": sec, "sym": sym, "desc": desc, "unit": unit, "q": q, "val": v})

        rows, combos = {}, []
        for idx in range(1, n + 1):
            cenv = dict(env)
            cenv["IDX_"] = idx
            trace, bysym = [], {}
            for row, sec, sym, desc, unit, code in M.COMBO:
                val = ev(code, cenv)
                cenv[f"r{row}"] = val
                rows.setdefault(row, [None] * n)[idx - 1] = val
                q, v = _tr(unit, val)
                trace.append({"row": row, "sec": sec, "sym": sym, "desc": desc, "unit": unit, "q": q, "val": v})
                bysym.setdefault(sym, {"val": v, "q": q, "unit": unit})
            activo = bysym.get("activo", {}).get("val") == 1
            nombre = bysym.get("Combo", {}).get("val")
            combos.append({"idx": idx, "nombre": nombre if isinstance(nombre, str) else "", "activo": bool(activo),
                           "ratio_max": bysym.get("máx.", {}).get("val") if activo else None,
                           "vals": {k: v for k, v in bysym.items() if k not in ("Combo", "activo")},
                           "trace": trace if activo else []})

        env["_row"] = lambda r: rows[r]
        checks, grupo = [], ""
        for row, tipo, nombre, ref, unit, P, Q, S, U in M.CHECKS:
            if tipo == "GRUPO":
                grupo = nombre
                continue
            dem, cap, ratio = ev(P, env), ev(Q, env), ev(S, env)
            env[f"DIS_{M.RATIO_COL}{row}"] = ratio      # la columna "Combo" de la hoja se refiere a la celda de ratio
            combo = ev(U, env)
            checks.append({"fila": row, "grupo": grupo, "nombre": nombre, "ref": ref, "unit": unit,
                           "q": _CHECK_Q.get(unit, ""), "dem": dem if _isnum(dem) else None,
                           "cap": cap if _isnum(cap) else None, "ratio": ratio if _isnum(ratio) else None,
                           "estado": _estado(ratio, lim), "combo": combo if isinstance(combo, str) else "—"})

        ratios = [c["ratio"] for c in checks if c["ratio"] is not None]
        rmax = max(ratios) if ratios else None
        if n and not any(c["activo"] for c in combos):
            msg = "SIN CARGAS"
        elif rmax is not None and rmax > 1:
            msg = "NO CUMPLE"
        elif rmax is not None and rmax > lim:
            msg = "CUMPLE AL LÍMITE"
        else:
            msg = "CUMPLE"

        return {"resumen": {"estado": msg, "ratio_max": rmax}, "checks": checks, "combos": combos,
                "memoria_global": mem_global,
                "vars": {k: v for k, v in env.items() if k[:2] in ("k_", "s_", "p_", "j_", "q_", "r_", "a_", "n_", "b_",
                                                                   "t_", "u_", "w_", "g_", "h_", "c_", "d_", "e_", "f_", "v_",
                                                                   "x_", "y_", "z_", "m_", "l_", "o_", "i_")
                         and _isnum(v)},
                "inputs": {k: env.get(k) for k in self.defaults()},
                "derivados": {nm: env.get(nm) for _r, nm, *_ in M.DERIVED},
                "raw": {"global": raw_global, "rows": rows}}
