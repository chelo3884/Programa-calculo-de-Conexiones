#!/usr/bin/env python3
"""Traduce las fórmulas de una hoja de cálculo de conexión (DISEÑO / CALCULO / CATALOGOS) a un módulo Python.

Uso:  python3 tools/xl2py.py "END_PLATE_AISC_DG4 (2).xlsx" end_plate
      python3 tools/xl2py.py "BFP_AISC358 (2).xlsx" bfp
      python3 tools/xl2py.py "RODILLA_CUMBRERA_GALPON (2).xlsx" rodilla

Genera en el paquete de destino:
    xl_model.py        filas de fórmulas (expresiones Python con comentarios) — NO editar a mano
    catalogos.json     columnas de la hoja CATALOGOS
    inputs_spec.json   campos de entrada (etiqueta, unidad, valor por defecto, opciones) para la interfaz

Cada fila de la hoja CALCULO se convierte en una expresión que lleva su símbolo, descripción y unidad,
de modo que la memoria de cálculo del programa es la misma de la hoja de Excel.
Requiere openpyxl (sólo para regenerar; el programa en uso no lo necesita).
"""
import json
import os
import re
import sys

import openpyxl
from openpyxl.utils import column_index_from_string, get_column_letter

TOKEN = re.compile(r'''\s*(?:
 (?P<str>"(?:[^"]|"")*")|
 (?P<num>\d+\.?\d*(?:[eE][+-]?\d+)?|\.\d+)|
 (?P<ref>(?:(?:'[^']+'|[A-Za-z_0-9ÁÉÍÓÚÑáéíóúñ]+)!)?\$?[A-Z]{1,3}\$?\d+(?::\$?[A-Z]{1,3}\$?\d+)?)(?![A-Za-z0-9_(])|
 (?P<name>[A-Za-z_][A-Za-z0-9_.]*)|
 (?P<op><=|>=|<>|[-+*/^&=<>(),%])
)''', re.X)


def tokenize(s):
    pos, out = 0, []
    while pos < len(s):
        if s[pos:].strip() == "":
            break
        m = TOKEN.match(s, pos)
        if not m:
            raise ValueError(f"token no reconocido en {s[pos:pos+30]!r} de {s!r}")
        pos = m.end()
        kind = m.lastgroup
        out.append((kind, m.group(kind)))
    return out


class Translator:
    """Fórmula de Excel → expresión Python. `ctx` decide cómo se llaman las referencias a celdas."""

    def __init__(self, names, sheet, col_letter=None, cell_name=None):
        self.names = names              # nombre definido → (hoja, celda)
        self.sheet = sheet              # hoja de la fórmula
        self.col = col_letter           # columna (para filas por combinación)
        self.cell_name = cell_name      # (hoja, celda) → identificador Python

    # -- análisis sintáctico ---------------------------------------------------------------
    def tr(self, formula):
        self.toks = tokenize(formula.lstrip("="))
        self.i = 0
        code = self.cmp()
        if self.i != len(self.toks):
            raise ValueError(f"sobran tokens en {formula!r}")
        return code

    def peek(self):
        return self.toks[self.i] if self.i < len(self.toks) else (None, None)

    def eat(self, val=None):
        t = self.toks[self.i]
        self.i += 1
        if val is not None and t[1] != val:
            raise ValueError(f"se esperaba {val!r}, llegó {t!r}")
        return t

    def cmp(self):
        a = self.cat()
        while self.peek()[1] in ("=", "<>", "<", ">", "<=", ">="):
            op = self.eat()[1]
            b = self.cat()
            a = {"=": f"_eq({a},{b})", "<>": f"(not _eq({a},{b}))"}.get(op, f"({a}{op}{b})")
        return a

    def cat(self):
        a = self.add()
        while self.peek()[1] == "&":
            self.eat()
            a = f"(_s({a})+_s({self.add()}))"
        return a

    def add(self):
        a = self.mul()
        while self.peek()[1] in ("+", "-"):
            op = self.eat()[1]
            a = f"({a}{op}{self.mul()})"
        return a

    def mul(self):
        a = self.pow()
        while self.peek()[1] in ("*", "/"):
            op = self.eat()[1]
            a = f"({a}{op}{self.pow()})"
        return a

    def pow(self):
        a = self.unary()
        while self.peek()[1] == "^":
            self.eat()
            a = f"({a}**{self.unary()})"
        return a

    def unary(self):
        if self.peek()[1] == "-":
            self.eat()
            return f"(-{self.unary()})"
        if self.peek()[1] == "+":
            self.eat()
            return self.unary()
        return self.primary()

    def primary(self):
        kind, val = self.eat()
        if kind == "num":
            return repr(float(val)) if ("." in val or "e" in val.lower()) else val
        if kind == "str":
            return repr(val[1:-1].replace('""', '"'))
        if kind == "op" and val == "(":
            e = self.cmp()
            self.eat(")")
            return f"({e})"
        if kind == "ref":
            return self.ref(val)
        if kind == "name":
            if self.peek()[1] == "(":
                self.eat("(")
                args = []
                if self.peek()[1] != ")":
                    args.append(self.cmp())
                    while self.peek()[1] == ",":
                        self.eat()
                        args.append(self.cmp())
                self.eat(")")
                return self.func(val.upper(), args)
            return self.name(val)
        raise ValueError(f"token inesperado {kind} {val}")

    # -- referencias -------------------------------------------------------------------------
    def name(self, n):
        if n == "IDX_":                                   # nº de la combinación en curso
            return n
        if n not in self.names:
            raise ValueError(f"nombre no definido: {n}")
        sh, cell = self.names[n]
        if ":" in cell:                                   # rango con nombre (cb_nom, cb_M, cb_V)
            return n
        return n

    def ref(self, text):
        sheet = self.sheet
        if "!" in text:
            sheet, text = text.split("!")
            sheet = sheet.strip("'")
        text = text.replace("$", "")
        if ":" in text:
            a, b = text.split(":")
            ca, ra = re.match(r"([A-Z]+)(\d+)", a).groups()
            cb, rb = re.match(r"([A-Z]+)(\d+)", b).groups()
            if sheet == "CATALOGOS":
                return f"_cat({ca!r},{ra},{cb!r},{rb})"
            if sheet == "CALCULO" and ra == rb:
                return f"_row({ra})"
            raise ValueError(f"rango no soportado {sheet}!{text}")
        col, row = re.match(r"([A-Z]+)(\d+)", text).groups()
        return self.cell_name(sheet, col, int(row), self.col)

    def func(self, f, a):
        if f == "IF":
            return f"(({a[1]}) if ({a[0]}) else ({a[2] if len(a) > 2 else 'False'}))"
        simple = {"MIN": "_min", "MAX": "_max", "ABS": "abs", "ISNUMBER": "_isnum", "N": "_n",
                  "MATCH": "_match", "INDEX": "_index", "COUNT": "_count", "AND": "_and", "OR": "_or",
                  "SQRT": "_sqrt", "TAN": "math.tan", "RADIANS": "math.radians", "TEXT": "_text",
                  "SIN": "math.sin", "COS": "math.cos", "ROUND": "round"}
        if f in simple:
            return f"{simple[f]}({','.join(a)})"
        if f == "PI":
            return "math.pi"
        if f == "LEFT":
            return f"_s({a[0]})[:int({a[1]})]"
        if f == "IFERROR":
            return f"_iferror(lambda: {a[0]}, lambda: {a[1]})"
        raise ValueError(f"función no soportada: {f}")



def is_formula(v):
    return isinstance(v, str) and v.startswith("=")


def main(xlsx, outdir):
    wb = openpyxl.load_workbook(xlsx)
    dis, cal, cat = wb["DISEÑO"], wb["CALCULO"], wb["CATALOGOS"]
    names = {n: (d.attr_text.split("!")[0].strip("'"), d.attr_text.split("!")[1].replace("$", ""))
             for n, d in wb.defined_names.items()}
    cell2name = {(sh, cell): n for n, (sh, cell) in names.items() if ":" not in cell}

    # filas de CALCULO por combinación = las que tienen fórmula también en la columna E
    combo_rows = {r for r in range(1, cal.max_row + 1) if is_formula(cal.cell(row=r, column=5).value)}
    ncombo = 0
    for r in combo_rows:
        for c in range(5, cal.max_column + 1):
            if is_formula(cal.cell(row=r, column=c).value):
                ncombo = max(ncombo, c - 3)

    def cell_name(sheet, col, row, combo_col):
        if sheet == "DISEÑO":
            return cell2name.get((sheet, f"{col}{row}"), f"DIS_{col}{row}")
        if sheet == "CALCULO":
            if row in combo_rows:
                return f"r{row}"
            return cell2name.get((sheet, f"{col}{row}"), f"g{row}")
        raise ValueError(sheet)

    os.makedirs(outdir, exist_ok=True)

    # ── catálogos ─────────────────────────────────────────────────────────────
    catd = {}
    for col in range(1, cat.max_column + 1):
        L = get_column_letter(col)
        vals = [cat.cell(row=r, column=col).value for r in range(1, cat.max_row + 1)]
        if any(v is not None for v in vals):
            catd[L] = vals
    json.dump(catd, open(os.path.join(outdir, "catalogos.json"), "w", encoding="utf-8"), ensure_ascii=False)

    # ── entradas de DISEÑO (bloque izquierdo, columnas B-E) ──────────────────────────
    validations = {}
    for dv in dis.data_validations.dataValidation:
        for rng in str(dv.sqref).split():
            if ":" in rng:
                (c1, r1), (c2, r2) = [re.match(r"([A-Z]+)(\d+)", x).groups() for x in rng.split(":")]
                for rr in range(int(r1), int(r2) + 1):
                    validations[f"{c1}{rr}"] = dv.formula1
            else:
                validations[rng] = dv.formula1

    def opts(formula):
        m = re.match(r"CATALOGOS!\$([A-Z]+)\$(\d+):\$[A-Z]+\$(\d+)", formula or "")
        if not m:
            return None
        L, a, b = m.group(1), int(m.group(2)), int(m.group(3))
        return [v for v in catd[L][a - 1:b] if v is not None]

    sections, cur, derived = [], None, []
    for r in range(6, dis.max_row + 1):
        b = dis.cell(row=r, column=2).value
        c = dis.cell(row=r, column=3).value
        e = dis.cell(row=r, column=5).value
        if b is None and c is None:
            continue
        if b is not None and c is None and e is None and not str(b).startswith("Celdas"):
            cur = {"titulo": str(b), "campos": []}
            sections.append(cur)
            continue
        if cur is None or b is None:
            continue
        unidad = dis.cell(row=r, column=4).value or ""
        for col, v in (("C", c), ("E", e)):
            if v is None or str(v) in ("valor", "Armado (mm)"):
                continue
            nm = cell_name("DISEÑO", col, r, None)
            if is_formula(v):
                derived.append((r, nm, str(b), unidad, v))
                cur.setdefault("derivados", []).append({"row": r, "name": nm, "label": str(b), "unit": unidad})
            elif col == "C":
                campo = {"name": nm, "label": str(b), "unit": unidad, "default": v, "row": r}
                o = opts(validations.get(f"C{r}"))
                if o:
                    campo["options"] = o
                elif isinstance(v, str):
                    campo["kind"] = "text"
                cur["campos"].append(campo)
            elif is_formula(c):                      # constante en E con fórmula en C → entrada "armado"
                m = re.search(r'IF\((\w+)="ARMADO', c)
                cur["campos"].append({"name": nm, "label": f"{b} (armado)", "unit": "mm", "default": v, "row": r,
                                      "armado_de": m.group(1) if m else None})

    # tabla de combinaciones (nombres cb_*)
    cb = {}
    for n, (sh, cell) in names.items():
        if n.startswith("cb_") and sh == "DISEÑO":
            m = re.match(r"([A-Z]+)(\d+):([A-Z]+)(\d+)", cell)
            cb[n] = (m.group(1), int(m.group(2)), int(m.group(4)))
    combos = None
    if cb:
        r1 = min(v[1] for v in cb.values())
        r2 = max(v[2] for v in cb.values())
        cols = []
        for n, (L, a, b) in sorted(cb.items(), key=lambda kv: column_index_from_string(kv[1][0])):
            lab = dis[f"{L}{a - 1}"].value
            key = {"cb_nom": "nombre"}.get(n, n[3:])
            cols.append({"name": n, "key": key, "label": str(lab).replace("\n", " ") if lab else key})
        filas = []
        for r in range(r1, r2 + 1):
            fila = {}
            for n, (L, a, b) in cb.items():
                fila[{"cb_nom": "nombre"}.get(n, n[3:])] = dis[f"{L}{r}"].value
            filas.append(fila)
        combos = {"cols": cols, "filas": filas, "n": r2 - r1 + 1}
    spec = {"secciones": sections, "combos": combos}

    # ── traducción ───────────────────────────────────────────────────────────────
    def T(formula, sheet, col=None):
        return Translator(names, sheet, col, cell_name).tr(formula)

    out = ['"""Modelo generado por tools/xl2py.py — NO editar a mano (regenerar desde la hoja de Excel)."""', ""]
    out.append(f"NCOMBO = {ncombo}\n")
    out.append("DERIVED = [  # (fila, nombre, etiqueta, unidad, expresión)  — fórmulas de la hoja DISEÑO")
    for r, nm, lab, un, f in derived:
        out.append(f"    ({r}, {nm!r}, {lab!r}, {un!r}, {T(f, 'DISEÑO')!r}),")
    out.append("]\n")

    glob, comb, sec = [], [], ""
    for r in range(4, cal.max_row + 1):
        v = cal.cell(row=r, column=4).value
        a, b, c = (cal.cell(row=r, column=k).value for k in (1, 2, 3))
        if r in combo_rows:
            tpl = re.sub(r"INDEX\((cb_[A-Za-z]+),1\)", r"INDEX(\1,IDX)", v)
            tpl = re.sub(r"IF\(1=1,", "IF(IDX=1,", tpl)
            ok = True
            for j in range(2, ncombo + 1):
                col = get_column_letter(3 + j)
                esperado = cal.cell(row=r, column=3 + j).value
                gen = re.sub(r"\bD(\d{2,3})\b", lambda m: f"{col}{m.group(1)}", tpl.replace("IDX", str(j)))
                if gen != esperado:
                    ok = False
            if not ok:
                raise ValueError(f"fila {r} de CALCULO no sigue el patrón por combinación")
            comb.append((r, sec, str(a), str(b), str(c or ""), T(tpl.replace("IDX", "IDX_"), "CALCULO", "D")))
            continue
        if v is None:
            if a and not b:
                sec = str(a)
            continue
        nm = cell_name("CALCULO", "D", r, None)
        code = T(v, "CALCULO") if is_formula(v) else repr(v)
        glob.append((r, sec, str(a), str(b), str(c or ""), nm, code))
    out.append("GLOBAL = [  # (fila, sección, símbolo, descripción, unidad, nombre, expresión)  — hoja CALCULO")
    for g in glob:
        out.append(f"    {g!r},")
    out.append("]\n")
    out.append("COMBO = [  # (fila, sección, símbolo, descripción, unidad, expresión); IDX_ = nº de combinación")
    for g in comb:
        out.append(f"    {g!r},")
    out.append("]\n")

    # ── tabla de verificaciones (columnas N..U de DISEÑO) ─────────────────────────────
    hdr = next(r for r in range(1, 20) if dis.cell(row=r, column=14).value == "Verificación")
    col_of = {}
    for c in range(14, 24):
        lab = str(dis.cell(row=hdr, column=c).value or "")
        for key, pref in (("ref", "Referencia"), ("dem", "Demanda"), ("cap", "Capacidad"), ("estado", "Estado"), ("combo", "Combo")):
            if lab.startswith(pref):
                col_of[key] = c
    first = hdr + 1
    est = dis.cell(row=first + 1, column=col_of["estado"]).value
    ratio_col = column_index_from_string(re.search(r"ISNUMBER\(([A-Z]+)\d+\)", est).group(1))
    unit_col = next(c for c in (col_of["cap"] + 1, col_of["cap"] + 2) if c != ratio_col)
    checks, notas, grupo_nota = [], [], False
    blank = 0
    for r in range(first, dis.max_row + 1):
        n = dis.cell(row=r, column=14).value
        if n is None:
            blank += 1
            if blank >= 2 and not grupo_nota:
                pass
            continue
        blank = 0
        if str(n).upper().startswith("ALCANCE"):
            grupo_nota = True
            continue
        if grupo_nota:
            notas.append(str(n).lstrip("• ").strip())
            continue
        P = dis.cell(row=r, column=col_of["dem"]).value
        if P is None:
            checks.append((r, "GRUPO", str(n), "", "", None, None, None, None))
            continue
        cell = lambda c: dis.cell(row=r, column=c).value
        tr = lambda f: T(f, "DISEÑO") if is_formula(f) else repr(f)
        checks.append((r, "CHEQUEO", str(n), str(cell(col_of["ref"]) or ""), str(cell(unit_col) or ""),
                       tr(P), tr(cell(col_of["cap"])), tr(cell(ratio_col)),
                       tr(cell(col_of["combo"])) if "combo" in col_of and cell(col_of["combo"]) is not None else "'—'"))
    out.append(f"RATIO_COL = {get_column_letter(ratio_col)!r}  # columna de ratio de la tabla de verificaciones")
    out.append(f"DEM_COL, CAP_COL = {get_column_letter(col_of['dem'])!r}, {get_column_letter(col_of['cap'])!r}")
    out.append("CHECKS = [  # (fila, tipo, nombre, referencia, unidad, demanda, capacidad, ratio, combo)")
    for g in checks:
        out.append(f"    {g!r},")
    out.append("]\n")
    spec["notas"] = notas
    spec["titulo"] = str(dis["B2"].value or "")
    spec["norma"] = str(dis["B3"].value or "")
    json.dump(spec, open(os.path.join(outdir, "inputs_spec.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    with open(os.path.join(outdir, "xl_model.py"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(out))
    open(os.path.join(outdir, "__init__.py"), "a").close()
    print(f"{len(derived)} derivadas · {len(glob)} globales · {len(comb)} por combinación (x{ncombo}) · {len(checks)} chequeos")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
