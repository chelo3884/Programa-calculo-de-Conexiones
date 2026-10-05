"""Marco para módulos de conexión escritos a mano (sin hoja de Excel de origen).

Un módulo define:
  · SPEC            entradas (secciones y campos), tabla de combinaciones y notas — se sirve a la interfaz genérica
  · global_fn(h, I) cálculos independientes de las combinaciones; devuelve un contexto (dict)
  · combo_fn(h, ctx, c, I)  verificaciones por combinación (c = combinación con valores en Tonf / Tonf·m)
`Modulo.calcular(entradas)` devuelve lo mismo que xlcore.XlModule: resumen, checks, combos, memoria_global, vars...

Unidades internas de los cálculos: kgf · cm · kgf/cm²; la salida se entrega en las canónicas de la interfaz:
Tonf · Tonf·m · mm (Ls) · cm (Lc) · kgf/cm² (S).
"""
from __future__ import annotations

import copy
import json
import os

_OUT = {"F": 1e-3, "M": 1e-5, "ML": 1e-3, "S": 1.0, "Ls": 10.0, "Lc": 1.0, "A": 1.0, "FL": 1.0, "": 1.0}
_UNIT = {"F": "Tonf", "M": "Tonf·m", "S": "kgf/cm²", "Ls": "mm", "Lc": "cm", "A": "cm²", "FL": "kgf/cm", "": "-"}
_ERR = (ZeroDivisionError, ValueError, TypeError, KeyError)
ARMADO = "ARMADO (flejes soldados)"


def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def estado(r, lim):
    if not _num(r):
        return "N/A"
    return "NO CUMPLE" if r > 1.0 else ("AL LÍMITE" if r > lim else "CUMPLE")


class Hoja:
    """Registra filas de memoria y verificaciones."""

    def __init__(self):
        self.rows, self.checks, self._sec = [], [], ""

    def sec(self, titulo):
        self._sec = titulo

    def v(self, sym, desc, val, q="", unit=None):
        """Registra un valor de la memoria (val en unidades internas) y lo devuelve sin cambios."""
        out = val * _OUT[q] if _num(val) else val
        self.rows.append({"row": len(self.rows) + 1, "sec": self._sec, "sym": sym, "desc": desc,
                          "unit": unit or _UNIT[q], "q": q, "val": out})
        return val

    def chk(self, grupo, nombre, ref, dem, cap, q="F", ratio=None, activo=True):
        """Registra una verificación demanda/capacidad (unidades internas). activo=False → N/A."""
        if not activo:
            dem = cap = ratio = None
        elif ratio is None:
            ratio = dem / cap if cap else float("inf")
        o = _OUT[q]
        self.checks.append({"grupo": grupo, "nombre": nombre, "ref": ref, "unit": _UNIT[q], "q": q,
                            "dem": dem * o if _num(dem) else None, "cap": cap * o if _num(cap) else None,
                            "ratio": ratio if _num(ratio) else None})


class Modulo:
    def __init__(self, spec, global_fn, combo_fn=None, vars_fn=None):
        self.SPEC = spec
        self.CAT = {}
        self._g, self._c, self._vars = global_fn, combo_fn, vars_fn

    def defaults(self):
        d = {}
        for sec in self.SPEC["secciones"]:
            for c in sec["campos"]:
                d[c["name"]] = c["default"]
        return d

    def calcular(self, inp: dict) -> dict:
        I = self.defaults()
        I.update({k: v for k, v in inp.items() if k != "combos"})
        lim = float(I.get("lim_verde", 0.9))
        gh = Hoja()
        ctx = self._g(gh, I) or {}
        sc = self.SPEC.get("combos")
        combos, agg = [], {}
        order = []
        for ch in gh.checks:
            key = (ch["grupo"], ch["nombre"])
            order.append(key)
            agg[key] = dict(ch, combo="—")
        if sc and self._c:
            filas = list(inp.get("combos", []))[:sc["n"]]
            for idx, f in enumerate(filas, 1):
                activo = any(_num(f.get(c["key"])) and f.get(c["key"]) != 0 for c in sc["cols"] if c["key"] != "nombre")
                nombre = str(f.get("nombre") or f"C{idx}")
                if not activo:
                    combos.append({"idx": idx, "nombre": nombre, "activo": False, "ratio_max": None, "vals": {}, "trace": []})
                    continue
                h = Hoja()
                try:
                    self._c(h, ctx, dict(f, nombre=nombre), I)
                except _ERR:
                    h.chk("ERROR", "No se pudo evaluar la combinación (revise los datos)", "", 0, 1, "", ratio=None)
                rmax = None
                for ck in h.checks:
                    key = (ck["grupo"], ck["nombre"])
                    if key not in agg:
                        agg[key] = dict(ck, combo=nombre)
                        order.append(key)
                    else:
                        a = agg[key]
                        if _num(ck["ratio"]) and (not _num(a["ratio"]) or ck["ratio"] > a["ratio"]):
                            agg[key] = dict(ck, combo=nombre)
                    if _num(ck["ratio"]) and (rmax is None or ck["ratio"] > rmax):
                        rmax = ck["ratio"]
                vals = {r["sym"]: {"val": r["val"], "q": r["q"], "unit": r["unit"]} for r in reversed(h.rows)}
                combos.append({"idx": idx, "nombre": nombre, "activo": True, "ratio_max": rmax, "vals": vals,
                               "trace": h.rows})
        checks = []
        for i, key in enumerate(order, 1):
            a = agg[key]
            a["fila"] = i
            a["estado"] = estado(a["ratio"], lim)
            checks.append(a)
        ratios = [c["ratio"] for c in checks if _num(c["ratio"])]
        rmax = max(ratios) if ratios else None
        if sc and not any(c["activo"] for c in combos):
            msg = "SIN CARGAS"
        elif rmax is not None and rmax > 1:
            msg = "NO CUMPLE"
        elif rmax is not None and rmax > lim:
            msg = "CUMPLE AL LÍMITE"
        else:
            msg = "CUMPLE"
        return {"resumen": {"estado": msg, "ratio_max": rmax}, "checks": checks, "combos": combos,
                "memoria_global": gh.rows, "vars": ctx.get("vars", {}), "inputs": I,
                "derivados": ctx.get("derivados", {}),
                "raw": {"global": {}, "rows": {}}}


# ── ayudas para construir especificaciones ───────────────────────────────────────────────────────────────────────
def campo(name, label, default, unit="", options=None, kind=None, armado_de=None):
    c = {"name": name, "label": label, "unit": unit, "default": default}
    if options is not None:
        c["options"] = list(options)
    elif isinstance(default, str) or kind == "text":
        c["kind"] = "text"
    if armado_de:
        c["armado_de"] = armado_de
    return c


def seccion(titulo, campos, derivados=None):
    return {"titulo": titulo, "campos": campos, "derivados": derivados or []}


def spec(titulo, norma, secciones, combos=None, notas=None):
    """Asigna 'row' consecutivos (orden de pantalla) y arma la especificación."""
    r = 1
    for s in secciones:
        for c in s["campos"]:
            c["row"] = r
            r += 2
        for d in s.get("derivados", []):
            d.setdefault("row", r)
            r += 2
    return {"secciones": secciones, "combos": combos, "notas": notas or [], "titulo": titulo, "norma": norma}


def tabla_combos(cols, filas, n=10):
    """cols: [(key, etiqueta)]; filas: lista de dicts."""
    cc = [{"name": "cb_" + k, "key": k, "label": lab} for k, lab in cols]
    base = [dict(f) for f in filas]
    while len(base) < n:
        base.append({"nombre": f"C{len(base) + 1}"})
    return {"cols": cc, "filas": base, "n": n}


# ── catálogo de perfiles (tomado de las hojas de Excel del repositorio) ──────────────────────────────────────────
_HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(_HERE, "end_plate", "catalogos.json"), encoding="utf-8") as _f:
    _CAT = json.load(_f)


def _col(L, r):
    v = _CAT.get(L, [])
    return v[r] if r < len(v) else None


def perfiles_viga():
    return {_col("A", r): tuple(_col(L, r) for L in "BCDE") for r in range(4, 45)
            if _col("A", r) and _col("B", r) is not None and _col("A", r) not in ("Perfil", ARMADO)}


def perfiles_columna():
    return {_col("G", r): tuple(_col(L, r) for L in "HIJK") for r in range(4, 45)
            if _col("G", r) and _col("H", r) is not None and _col("G", r) not in ("Perfil", ARMADO)}


def perfil(nombre, I, prefijo, catalogo):
    """(d, bf, tw, tf) en cm de un perfil del catálogo o armado (entradas {prefijo}_E_d, _bf, _tw, _tf)."""
    if nombre == ARMADO:
        return tuple(float(I[f"{prefijo}_E_{k}"]) / 10 for k in ("d", "bf", "tw", "tf"))
    return tuple(x / 10 for x in catalogo[nombre])
