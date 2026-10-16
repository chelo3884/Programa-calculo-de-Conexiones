"""Resumen común de resultados: estado y ratio máximo de la cabecera.

Las comprobaciones GEOMÉTRICAS y de detallado (grupos «… (requerido / provisto)» y «PRECALIFICACIÓN …»: bordes, pasos,
filetes mínimos, límites de aplicabilidad) siguen en la tabla de verificaciones, pero NO entran en el ratio máximo de resistencia
de la cabecera. Sí cuentan para el estado: una comprobación geométrica > 1 da «NO CUMPLE».
"""


def es_geom(grupo) -> bool:
    g = str(grupo or "").upper()
    return "(REQUERIDO / PROVISTO)" in g or g.startswith("PRECALIFICACI")


def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and x == x


def resumir(checks, lim, sin_cargas=False, **extra):
    """dict(estado, ratio_max, ratio_geom): ratio_max = máx. de las comprobaciones de resistencia; ratio_geom = máx. de las geométricas."""
    res = [c["ratio"] for c in checks if _num(c.get("ratio")) and not es_geom(c.get("grupo"))]
    geo = [c["ratio"] for c in checks if _num(c.get("ratio")) and es_geom(c.get("grupo"))]
    rmax = max(res) if res else None
    rgeo = max(geo) if geo else None
    peor = max(res + geo) if (res or geo) else None
    if sin_cargas:
        msg = "SIN CARGAS"
    elif peor is not None and peor > 1:
        msg = "NO CUMPLE"
    elif rmax is not None and rmax > lim:
        msg = "CUMPLE AL LÍMITE"
    else:
        msg = "CUMPLE"
    out = {"estado": msg, "ratio_max": rmax, "ratio_geom": rgeo}
    out.update(extra)
    return out


def ratio_efectivo(resumen):
    """Para la búsqueda de diseño: el ratio de resistencia, o el geométrico si éste incumple (> 1)."""
    r = resumen.get("ratio_max")
    g = resumen.get("ratio_geom")
    if g is not None and g > 1 and (r is None or g > r):
        return g
    return r
