# Contexto del proyecto (para continuar el trabajo en local)

Resumen del trabajo hecho hasta ahora, para que una sesión nueva retome sin la conversación anterior. Actualícelo al cerrar cada sesión importante.

## Usuario y preferencias
- Ingeniero estructural en Quito, Ecuador. Trabaja con NEC (2026), SAP2000, AISC. Unidades: **Tonf, Tonf·m, mm, kgf/cm²**.
- Quiere respuestas técnicas directas, con tablas cuando hay números, y que se le corrija citando fuentes normativas.
- Honestidad ante todo: decir qué está verificado contra un ejemplo/norma y qué es criterio propio o esquemático.
- Idioma: español. No crear PR salvo que lo pida. Commits con los trailers que indique el entorno. **Rama de trabajo:** `claude/adoring-heisenberg-7emxab` (repo `chelo3884/Programa-calculo-de-Conexiones`).
- Tras cada cambio: correr `python3 -m unittest discover -s tests` (107 pruebas) y, si toca la interfaz, revisar con Playwright/Chromium.

## Qué es el programa
Programa en Python (servidor HTTP local, sin dependencias externas) con interfaz web para diseñar conexiones de acero, estilo RAM Connection. Se lanza con `python3 app.py` (puerto 8000) o `Iniciar.pyw` / `Iniciar.bat`. Genera reportes (HTML, PDF por impresión, Word .docx), exporta DXF, maneja varios proyectos, importa cargas de SAP2000, genera combinaciones NEC y propone diseños automáticos.
- **Los proyectos del usuario viven en el `localStorage` del navegador** (clave `cx_proyectos`, origen `http://127.0.0.1:8000`), no en la carpeta del programa. Los perfiles locales en `~/.conexiones_metalicas/perfiles.json`. Copiar el código encima no los borra.

## Arquitectura
- `app.py`: rutas `/api/<módulo>/calc|spec|auto|barrido`, `/api/docx`, `/api/perfiles*`, `/api/nec_combos`, `/api/sap_*`. Registro de módulos en `MODULOS_XL`.
- Tres tipos de motor:
  1. **Generados desde Excel** (`xlcore.py` + `<modulo>/xl_model.py`, no editar a mano): end_plate, bfp, rodilla, cortante_vv, cortante_vc (envuelve a vv), empalme_viga, empalme_col. cortante_vv extiende una COPIA del modelo en su `engine.py`.
  2. **Escritos a mano** con `handmod.Modulo` (`SPEC` + `global_fn` + `combo_fn`): wuf, gusset, hss_directa, hss_pasante, hss_diafragma, hss_dext, hss_placalong, hss_placasimple, empalme_rhs, hss_diafragma_atornillado; comunes en `hss_comun.py`. `cortante_hss` reutiliza cortante_vv.
  3. `placa_base/engine.py` (propio).
- `aisc.py`: fórmulas AISC 360-16 y CIDECT 9 (funciones `cidect_*`, `hss_*`).
- `resumen.py`: estado y ratio de la cabecera. **El ratio máx. excluye las comprobaciones geométricas** (grupos «(requerido / provisto)» y «PRECALIFICACIÓN»); si una geométrica > 1, el estado es NO CUMPLE y la cabecera añade «· geometría x.xx». `autodiseno.py` usa `ratio_efectivo` (resistencia ≤ límite y geometría ≤ 1).
- `autodiseno.py` (CONFIG por módulo), `cargas.py` (SAP2000/NEC), `perfiles_usuario.py`, `docx_writer.py`.
- Web (`web/`): una página por módulo cargando `common.js`, `mod_*.js` (dibujos 2D SVG y configuración) y `xlmodule.js` (página genérica); `placa_base.html` es independiente. `modulos.js` es el catálogo (id, categoría, título); miniaturas SVG en `web/thumbs/` (se regeneran con `python3 tools/make_thumbs.py <ruta_chromium>`). Proyectos: `proy.js`, `proyecto.html`; inicio: `index.html`.
- **Vista 3D**: `web/viewer3d.js` (visor propio con z-buffer, sin librerías) y `web/model3d.js` (un modelo esquemático por conexión, `MODEL3D[id]`). Interruptor 2D|3D en todas las páginas.
- Pruebas en `tests/`: ejemplos de guías (CIDECT 9, AISC DG24), fixtures del Excel (`tests/fixtures/*.json`), etc.

## Módulos y su base normativa (todos con README de limitaciones)
Placa base (DG1, ACI 318-19 cap. 17), end plate (DG4/AISC 358), BFP, WUF, rodilla/cumbrera, cortante viga–columna/viga–viga/HSS, empalme de viga y de columna, gusset (UFM), columnas HSS: soldada directa y placa pasante (DG24), placa de recorte (referencia Tedds, limitada), CIDECT 9: diafragmas externos RHS (§8.6), placa longitudinal (§10.1), placa simple a RHS (§5.3), empalme de columna RHS (§11.1.1.2, sin ejemplo en la guía: verificado por recálculo), diafragma pasante atornillado (§8.2, reproduce el ejemplo 8.2.1). La guía CIDECT 9 y DG24 están como PDF en el repo; la CIDECT usa CSA/EC3, la implementación usa AISC 360-16 salvo donde la guía fija el método.

## Decisiones recientes importantes (cortante viga–viga, `cortante_vv`)
- Nivel relativo de vigas: «Ala superior al ras» por defecto (también «Centrada» y «Desnivel manual»). Con alas al ras la soportada necesita destaje superior: dc ≥ tfg − dz + 10 mm y c ≥ (bfg − twg)/2 − holgura + 10 mm (holgura 10 mm = criterio propio).
- Destaje: siempre desde el ala superior hacia abajo (dc medido desde el tope de la viga).
- Posición de la placa: automática, borde superior 10 mm bajo el ala superior de la principal; manual opcional.
- **Placa extendida = placa en T** (sin destaje): tramo ancho soldado al alma de la principal que ocupa todo el alma libre (2 mm de ajuste a las alas, soldable a ellas) y lengüeta con pernos de altura L. El extremo de la viga queda fuera de la punta del ala (holgura + (bfg − twg)/2). `a` automático (extremo + borde del alma). Momento de la lengüeta Ru·(a − xs); filetes del alma con longitud Hs y excentricidad (modelo elástico propio, el Manual no trata esta forma).
- Fixtures del Excel se prueban con `pn_pos="Manual"`, `vg_nivel="No aplica"`, `pl_a_modo="Manual"`.

## Errores resueltos que conviene recordar
- `esc()` en `web/common.js` no escapaba comillas → `value="5/8""` rompía los selects de diámetro (KeyError '5/8'). Corregido.
- Hueco estándar de perno: AISC 2016 vs 2005 (DG24 usa 2005); documentado en pruebas.
- Para matar el servidor usar `fuser -k PORT/tcp` (no `pkill -f`).

## Pendientes / ideas
- CIDECT 9 sin programar: diafragma pasante soldado (§8.1), diafragmas internos (§8.5), fórmulas CHS, placas laterales (8.24–8.27), viga I semirrígida a RHS (6.3.2), asientos (5.8–5.9), uniones en T (5.6).
- Diafragma atornillado: no verifica desgarro en bloque ni sección neta de platabandas, ni soldadura de la ménsula.
- 3D esquemático: rodilla/cumbrera aproximada; placa base sin llave de corte; el 3D no entra en los reportes.
- Placa simple a RHS y placa extendida usan AISC; cortante de placa en T solo con modelo propio.
- Conexiones ya guardadas en proyectos del usuario pueden mostrar otro ratio (cambió el criterio de la cabecera y los campos nuevos de cortante viga–viga); se actualizan al reabrir y guardar.
