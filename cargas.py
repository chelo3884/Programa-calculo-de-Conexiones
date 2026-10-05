"""Herramientas de cargas: combinaciones NEC (LRFD) e importación de resultados de SAP2000.

Todas las cargas se manejan en las unidades canónicas de la interfaz (Tonf · Tonf·m).

COMBINACIONES — se usa la lista LRFD de NEC-SE-CG (Cargas no sísmicas), §3.4.3, que sigue a ASCE 7-10:
    1) 1.4D   2) 1.2D + 1.6L + 0.5·máx(Lr, S, R)   3) 1.2D + 1.6·máx(Lr, S, R) + máx(L, 0.5W)
    4) 1.2D + 1.0W + L + 0.5·máx(Lr, S, R)         5) 1.2D + 1.0E + L + 0.2S
    6) 0.9D + 1.0W                                 7) 0.9D + 1.0E
Estos factores están escritos de memoria de la edición 2015 y NO se pudieron contrastar con la edición vigente de la norma:
el ingeniero debe verificarlos (y los de E con Ω0, ρ y Ev) contra su ejemplar de la NEC antes de usarlos.
"""
from __future__ import annotations

import itertools
import re

CASOS = ("D", "L", "Lr", "S", "R", "W", "E")

# (factores fijos, grupos máx: [(coef, [casos])])
PLANTILLAS = [
    ({"D": 1.4}, []),
    ({"D": 1.2, "L": 1.6}, [(0.5, ["Lr", "S", "R"])]),
    ({"D": 1.2}, [(1.6, ["Lr", "S", "R"]), (1.0, ["L", "W*0.5"])]),
    ({"D": 1.2, "W": 1.0, "L": 1.0}, [(0.5, ["Lr", "S", "R"])]),
    ({"D": 1.2, "E": 1.0, "L": 1.0, "S": 0.2}, []),
    ({"D": 0.9, "W": 1.0}, []),
    ({"D": 0.9, "E": 1.0}, []),
]


def _fmt(c):
    return ("%g" % c)


def _nombre(f):
    partes = []
    for caso in CASOS + ("Ω0E",):
        c = f.get(caso)
        if not c:
            continue
        signo = "−" if c < 0 else ("+" if partes else "")
        mag = abs(c)
        etq = ("" if abs(mag - 1.0) < 1e-12 else _fmt(mag)) + caso
        partes.append(signo + etq)
    return "".join(partes)


def generar(cargas: dict, columnas, omega0: float = 1.0, modo_sismo: str = "E", invertir: bool = True):
    """Genera combinaciones factoradas.

    cargas: {"D": {"P":..,"V":..,"M":..}, "L": {...}, ...} (casos ausentes o en cero se ignoran)
    modo_sismo: "E" (E sin amplificar), "Ω0" (Ω0·E) o "ambos"
    invertir: genera ±W y ±E (el viento y el sismo son reversibles).
    """
    columnas = list(columnas)
    vals = {c: {k: float(cargas.get(c, {}).get(k) or 0.0) for k in columnas} for c in CASOS}
    activo = {c: any(abs(v) > 0 for v in vals[c].values()) for c in CASOS}
    etiq_sismo = {"E": ["E"], "Ω0": ["Ω0E"], "ambos": ["E", "Ω0E"]}[modo_sismo]
    salida, vistos = [], set()
    for fijos, grupos in PLANTILLAS:
        base_fijos = dict(fijos)
        if any(k in base_fijos and not activo[k] for k in ("E", "W")):
            continue
        if grupos and grupos[0][1][0] == "Lr" and grupos[0][0] == 1.6 and not any(activo[c] for c in ("Lr", "S", "R")):
            continue                                    # combinación 3 sin cargas de cubierta/nieve/lluvia: no aporta
        opciones = []
        for coef, casos in grupos:
            alt = []
            for c in casos:
                f = 0.5 if c.endswith("*0.5") else 1.0
                cc = c.split("*")[0]
                if activo[cc]:
                    alt.append((coef * f, cc))
            opciones.append(alt or [None])
        for elec in itertools.product(*opciones):
            f = dict(base_fijos)
            for e in elec:
                if e:
                    f[e[1]] = f.get(e[1], 0.0) + e[0]
            f = {k: v for k, v in f.items() if (activo.get(k) or k == "D" and activo["D"]) and v}
            if not f:
                continue
            for etq_e in (etiq_sismo if "E" in f else [None]):
                for sg_w in ((1, -1) if (invertir and "W" in f) else (1,)):
                    for sg_e in ((1, -1) if (invertir and etq_e) else (1,)):
                        g = dict(f)
                        if "W" in g:
                            g["W"] *= sg_w
                        if etq_e:
                            fe = g.pop("E")
                            g[etq_e] = fe * sg_e
                        clave = tuple(sorted(g.items()))
                        if clave in vistos:
                            continue
                        vistos.add(clave)
                        v = {k: 0.0 for k in columnas}
                        for caso, coef in g.items():
                            if caso == "Ω0E":
                                for k in columnas:
                                    v[k] += coef * omega0 * vals["E"][k]
                            else:
                                for k in columnas:
                                    v[k] += coef * vals[caso][k]
                        if all(abs(x) < 1e-12 for x in v.values()):
                            continue
                        salida.append(dict(nombre=_nombre(g), **{k: round(x, 6) for k, x in v.items()}))
    return salida


# ─────────────────────────────── importación de SAP2000 ───────────────────────────────
_F = {"tonf": 1.0, "tonf-m": 1.0, "kn": 1 / 9.80665, "n": 1 / 9806.65, "kgf": 1e-3, "kip": 0.45359237, "lb": 4.5359237e-4,
      "lbf": 4.5359237e-4}
_L = {"m": 1.0, "cm": 0.01, "mm": 0.001, "in": 0.0254, "ft": 0.3048}
_FUERZA = {"F1", "F2", "F3", "P", "V2", "V3", "V", "FX", "FY", "FZ"}
_MOMENTO = {"M1", "M2", "M3", "T", "MX", "MY", "MZ", "M"}
_UN_RE = re.compile(r"^(?P<f>tonf|kn|n|kgf|kip|lbf|lb)(?:\s*[-·*/]\s*(?P<l>m|cm|mm|in|ft))?$", re.I)
_TEXTO = {"text", "unitless", "yes/no", "degrees", "radians", ""}


def _split(linea, sep):
    if sep == "\t":
        return [c.strip() for c in linea.split("\t")]
    if sep == " ":
        return [c.strip() for c in re.split(r"\s{2,}", linea.strip())]
    return [c.strip().strip('"') for c in linea.split(sep)]


def _sep(lineas):
    for sep in ("\t", ";", ","):
        if any(sep in ln for ln in lineas[:3]):
            return sep
    return " "


def _num(s, decimal_coma):
    s = s.strip().replace(" ", "")
    if decimal_coma:
        s = s.replace(".", "").replace(",", ".") if s.count(",") == 1 and s.count(".") > 0 else s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def _txt(v):
    if isinstance(v, float) and v == int(v):
        v = int(v)
    return str(v).strip()


def parse(texto: str) -> dict:
    """Lee una tabla de SAP2000 (Excel pegado, CSV o TSV): devuelve nombre, columnas, unidades y filas (dicts)."""
    lineas = [ln for ln in texto.replace("\r", "").split("\n") if ln.strip()]
    tabla = ""
    if lineas and lineas[0].upper().lstrip().startswith("TABLE:"):
        tabla = lineas[0].split(":", 1)[1].strip()
        lineas = lineas[1:]
    if len(lineas) < 2:
        raise ValueError("No hay datos: pegue la tabla con su fila de encabezados")
    sep = _sep(lineas)
    cab = _split(lineas[0], sep)
    if len(cab) < 2:
        raise ValueError("No se reconoce el separador de columnas (use tabulaciones, ; o ,)")
    resto = lineas[1:]
    unidades = None
    segunda = _split(resto[0], sep)
    if len(segunda) == len(cab) and all((c.lower() in _TEXTO or _UN_RE.match(c)) for c in segunda) and \
            any(_UN_RE.match(c) or c.lower() in _TEXTO - {""} for c in segunda):
        unidades = segunda
        resto = resto[1:]
    coma = sep != ","
    filas = []
    for ln in resto:
        c = _split(ln, sep)
        if len(c) < len(cab):
            c += [""] * (len(cab) - len(c))
        fila = {}
        for k, v in zip(cab, c):
            n = _num(v, coma)
            fila[k] = n if n is not None and not re.search(r"[A-Za-z]", v) else v
        filas.append(fila)
    return {"tabla": tabla, "columnas": cab, "unidades": unidades, "filas": filas, "sep": sep}


def mapa_sugerido(columnas, claves):
    """Sugiere qué columna de SAP2000 alimenta cada columna de la tabla de combinaciones (P, V, M)."""
    cs = {c.upper(): c for c in columnas}
    if "F3" in cs:                               # Joint Reactions
        pref = {"P": ["F3"], "V": ["F1", "F2"], "M": ["M2", "M1"]}
    else:                                        # Element Forces – Frames
        pref = {"P": ["P"], "V": ["V2", "V3"], "M": ["M3", "M2"]}
    mapa = {}
    for k in claves:
        for cand in pref.get(k, []):
            if cand in cs:
                mapa[k] = {"col": cs[cand], "mult": 1.0, "abs": False}
                break
    return mapa


def _factor(unidad, defecto):
    """Factor a Tonf (fuerza) o Tonf·m (momento) según el token de unidad ('Tonf-m', 'kN', ...)."""
    f_def, l_def = defecto
    if unidad:
        m = _UN_RE.match(unidad.strip())
        if m:
            f = _F[m.group("f").lower()]
            l = _L[m.group("l").lower()] if m.group("l") else None
            return f, l
    return _F[f_def.lower()], None


def importar(texto, mapa, claves, nombre_col=None, filtro=None, fuerza="Tonf", longitud="m", n_max=10):
    """Convierte la tabla de SAP2000 en combinaciones [{nombre, P, V, M}] en Tonf y Tonf·m.

    mapa: {clave: {"col": nombre de columna SAP, "mult": ±1, "abs": bool}}
    filtro: {"col": nombre de columna, "valor": texto exacto}  (p. ej. Joint = 12)
    """
    t = parse(texto)
    cols = t["columnas"]
    un = dict(zip(cols, t["unidades"] or [""] * len(cols)))
    avisos = []
    if nombre_col is None:
        nombre_col = next((c for c in cols if c.lower() in ("outputcase", "output case", "combo", "case")), cols[0])
    paso = next((c for c in cols if c.lower() == "steptype"), None)
    L = _L[longitud.lower()]
    factores = {}
    for k in claves:
        if k not in mapa or not mapa[k].get("col"):
            continue
        c = mapa[k]["col"]
        if c not in cols:
            raise ValueError(f"La columna '{c}' no existe en la tabla")
        f, l = _factor(un.get(c), (fuerza, longitud))
        if c.upper() in _MOMENTO:
            l = l if l else L
            f = f * l
        elif c.upper() not in _FUERZA and k.upper() == "M":
            f = f * (l if l else L)
        factores[k] = f
        if not un.get(c):
            avisos.append(f"'{c}': sin unidad en la tabla; se supone {fuerza}" + (f"·{longitud}" if k.upper() == "M" or c.upper() in _MOMENTO else ""))
    filas = t["filas"]
    if filtro and filtro.get("col"):
        filas = [r for r in filas if _txt(r.get(filtro["col"], "")) == _txt(filtro.get("valor", ""))]
    salida, usados = [], {}
    for r in filas:
        nom = _txt(r.get(nombre_col, "")) or "C"
        if paso and str(r.get(paso, "")).strip() in ("Max", "Min"):
            nom += " " + str(r[paso]).strip()
        v = {}
        for k, f in factores.items():
            x = r.get(mapa[k]["col"])
            x = float(x) if isinstance(x, (int, float)) else 0.0
            x *= float(mapa[k].get("mult", 1.0)) * f
            v[k] = abs(x) if mapa[k].get("abs") else x
        usados[nom] = usados.get(nom, 0) + 1
        if usados[nom] > 1:
            nom = f"{nom} #{usados[nom]}"
        salida.append(dict(nombre=nom, **{k: round(x, 6) for k, x in v.items()}))
    if len(salida) > n_max:
        avisos.append(f"Hay {len(salida)} filas y la tabla admite {n_max}: se tomaron las {n_max} de mayor |M|+|V|+|P|")
        salida.sort(key=lambda c: -sum(abs(c.get(k, 0)) for k in claves))
        salida = salida[:n_max]
    if not salida:
        avisos.append("Ninguna fila coincide con el filtro")
    return {"combos": salida, "avisos": avisos}
