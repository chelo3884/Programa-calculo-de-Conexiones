"""Catálogo de perfiles del usuario (proveedor local: DIPAC, Novacero, etc.), guardado en un JSON fuera del programa.

Ubicación: la variable de entorno CONEXIONES_DATOS o, si no existe, ~/.conexiones_metalicas/perfiles.json
(así sobrevive a las actualizaciones y al ejecutable). Cada perfil:
    {"nombre", "tipo": "I" | "HSS", "d", "bf", "tw", "tf", "peso", "proveedor"}   dimensiones en mm
    · tipo I:   d = peralte, bf = ancho de ala, tw = espesor de alma, tf = espesor de ala
    · tipo HSS: d = H, bf = B, tf = t de DISEÑO (0.93·tnom en HSS soldado por resistencia eléctrica); tw se ignora
En los módulos se aplican como perfil armado (las dimensiones se copian a los campos manuales).
"""
from __future__ import annotations

import json
import os
import re


def ruta() -> str:
    base = os.environ.get("CONEXIONES_DATOS") or os.path.join(os.path.expanduser("~"), ".conexiones_metalicas")
    return os.path.join(base, "perfiles.json")


def _num(v):
    if v in (None, ""):
        return None
    try:
        return float(str(v).replace(",", "."))
    except ValueError:
        raise ValueError(f"'{v}' no es un número")


def validar(lista):
    """Devuelve la lista limpia o lanza ValueError con el primer problema."""
    out, vistos = [], set()
    for i, p in enumerate(lista, 1):
        nombre = str(p.get("nombre", "")).strip()
        if not nombre:
            raise ValueError(f"Fila {i}: falta el nombre")
        if nombre.lower() in vistos:
            raise ValueError(f"Fila {i}: nombre repetido '{nombre}'")
        vistos.add(nombre.lower())
        tipo = str(p.get("tipo", "I")).strip().upper()
        if tipo not in ("I", "HSS"):
            raise ValueError(f"'{nombre}': tipo debe ser I o HSS")
        d, bf, tw, tf = (_num(p.get(k)) for k in ("d", "bf", "tw", "tf"))
        req = {"d": d, "bf": bf, "tf": tf}
        if tipo == "I":
            req["tw"] = tw
        for k, v in req.items():
            if v is None or v <= 0:
                raise ValueError(f"'{nombre}': falta {k} (mm) o no es positivo")
        if tipo == "HSS":
            tw = tf
        elif tw >= bf or 2 * tf >= d:
            raise ValueError(f"'{nombre}': dimensiones incoherentes (tw ≥ bf o 2·tf ≥ d)")
        out.append({"nombre": nombre, "tipo": tipo, "d": d, "bf": bf, "tw": tw, "tf": tf,
                    "peso": _num(p.get("peso")), "proveedor": str(p.get("proveedor", "") or "").strip()})
    return out


def leer():
    try:
        with open(ruta(), encoding="utf-8") as fh:
            return validar(json.load(fh))
    except (OSError, ValueError, TypeError):
        return []


def guardar(lista):
    limpia = validar(lista)
    os.makedirs(os.path.dirname(ruta()), exist_ok=True)
    tmp = ruta() + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(limpia, fh, ensure_ascii=False, indent=1)
    os.replace(tmp, ruta())
    return limpia


_ALIAS = {"nombre": ("nombre", "perfil", "designacion", "designación"), "tipo": ("tipo",),
          "d": ("d", "h", "peralte", "altura"), "bf": ("bf", "b", "ancho", "ancho de ala"),
          "tw": ("tw", "espesor de alma", "alma"), "tf": ("tf", "t", "espesor", "espesor de ala", "ala"),
          "peso": ("peso", "kg/m", "masa"), "proveedor": ("proveedor", "marca", "fabricante")}


def parse_texto(texto: str):
    """Tabla pegada desde Excel/CSV con encabezados (nombre, tipo, d, bf, tw, tf, peso, proveedor) → lista validada."""
    lineas = [ln for ln in texto.replace("\r", "").split("\n") if ln.strip()]
    if len(lineas) < 2:
        raise ValueError("Pegue la tabla con su fila de encabezados")
    sep = "\t" if "\t" in lineas[0] else (";" if ";" in lineas[0] else ",")
    cab = [c.strip().lower().strip('"') for c in lineas[0].split(sep)]
    idx = {}
    for k, alias in _ALIAS.items():
        for j, c in enumerate(cab):
            if c in alias and k not in idx:
                idx[k] = j
    if "nombre" not in idx:
        raise ValueError("No encuentro la columna 'nombre' (o 'perfil')")
    lista = []
    for ln in lineas[1:]:
        c = [x.strip().strip('"') for x in ln.split(sep)]
        g = lambda k: c[idx[k]] if k in idx and idx[k] < len(c) else ""  # noqa: E731
        p = {k: g(k) for k in _ALIAS}
        if not p["tipo"]:
            p["tipo"] = "I" if p["tw"] else "HSS"
        lista.append(p)
    return validar(lista)
