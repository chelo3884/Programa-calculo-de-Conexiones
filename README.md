# Diseño de conexiones metálicas

Programa en Python (sólo biblioteca estándar) con interfaz HTML interactiva, en la línea de RAM Connection.

**Módulos:** `/placa_base.html` (placa base y pernos de anclaje) · `/end_plate.html` (placa extrema extendida 4E/4ES/8ES, DG4 y AISC 358-16 cap. 6). La página de inicio `/` los enlaza.

Módulo 1: **placa base y pernos de anclaje** (columnas de perfil I/H y HSS rectangular/cajón) (AISC Design Guide 1, AISC 360-16 J2/J8, ACI 318-19 cap. 17, LRFD).

## Uso

    python3 app.py            # abre http://127.0.0.1:8000
    python3 app.py --port 8123 --no-browser

* Pestaña **Diseño**: parámetros de columna, placa, pernos, pedestal, soldadura y sismo; planta y elevación se redibujan al mover cualquier dato; tabla de verificaciones con ratios.
* Pestaña **Cargas**: combinaciones LRFD (Pu +compresión, Vu, Mu). Clic en una fila para dibujarla.
* **Memoria de cálculo**: todos los pasos intermedios (equivalente a la hoja CALCULO del Excel).
* **Unidades**: Tonf·m·mm (predeterminado), kgf·cm, SI, US o selección individual por magnitud.
* **Reporte**: HTML imprimible (Imprimir → Guardar como PDF) o descargable.
* Guardar / abrir proyecto en `.json`.

## Estructura

    app.py                      servidor local + API (/api/placa_base/calc, /api/end_plate/calc)
    placa_base/engine.py        motor de cálculo (kgf, cm internamente)
    placa_base/catalogos.json   perfiles, aceros, pernos, diámetros, electrodos (editable)
    web/                        index.html (módulos), placa_base.html, end_plate.html, common.js (unidades)
    end_plate/                  motor de placa extrema (xl_model.py generado desde el Excel con tools/xl2py.py)
    tools/                      xl2py.py (Excel→Python) y generador de casos de prueba con LibreOffice
    tests/                      verificación contra el Excel y contra AISC Design Examples J.6

## Verificación

    python3 -m unittest tests.test_placa_base

* HSS rectangular: AISC Design Examples K.9 (HSS6x6, PL 13×13 in): m = n = 3.65 in, φcPp = 560 kip, tmin = 1.08 in.
* AISC Design Guide 1, 2.ª ed.: Ej. 4.1 (axial, tmin = 1.60 in), 4.6 (momento pequeño, Y = 14 in) y 4.7 (momento grande, Y = 12.0 in, Tu = 156 kip, tp = 1.90 in).
* Reproduce las 5 combinaciones de `PLACA_BASE_AISC_DG1.xlsx` (todos los ratios, a 6 decimales).
* Ejemplo AISC J.6 (placa 22×22 in, Pu = 690 kip): m = 4.97 in, n = 6.12 in, n' = 3.11 in, fp = 1.43 ksi, tmin = 1.82 in.

Herramienta de apoyo: la responsabilidad del diseño es del ingeniero que la usa.

## Notas de criterio

* **HSS** (DG1 §3.1.3): m y n con líneas de fluencia a 0.95·H y 0.95·Bc; no se usan n' ni λ. Con momento, el brazo del lado traccionado se toma hasta el eje de la pared (igual que el eje del ala en perfiles I); la guía no lo define para HSS, es una extensión de criterio. Las esquinas del HSS se sueldan cuando hay momento o tracción (DG1 §2.4).
* **Catálogo HSS**: los AISC usan t de diseño = 0.93·tnom; los tubos comerciales ('TUBO …') están con espesor nominal, verifique con su proveedor y amplíe `placa_base/catalogos.json`.
* **Fricción** (DG1 §3.5.1, opcional, por defecto desactivada): φ·μ·Pu ≤ 0.2·f'c·Ac con φ = 0.75, solo con Pu > 0 de la misma combinación.
* Ejemplo 4.7 de la Guía: imprime f = 8.5 in pero sus resultados (Y = 12.0 in, Tu = 156 kip) corresponden a f = 9.5 in; la prueba usa f = 9.5 in.
* Brazo del lado traccionado en perfiles I: se usa el eje del ala (texto de DG1 §3.4.3); el Ej. 4.7 usa la cara exterior del ala (menos conservador).

## Módulo placa extrema (End Plate)

* Las fórmulas se **traducen automáticamente** de `END_PLATE_AISC_DG4.xlsx` (`python3 tools/xl2py.py "END_PLATE_AISC_DG4 (2).xlsx" end_plate`), de modo que cada fila de la memoria es la de la hoja (símbolo, descripción, unidad). Para cambiar un criterio, se corrige en el Excel y se regenera.
* Pruebas (`python3 -m unittest tests.test_end_plate`): 8 variantes (4E, 4ES, 8ES, sísmico y no sísmico, con/sin rigidizadores de continuidad, vigas a ambos lados, perfiles armados) recalculadas con LibreOffice; coinciden las filas 5–138 de CALCULO y la tabla de verificaciones.
* Para regenerar los casos de prueba hace falta LibreOffice Calc: `python3 tools/make_end_plate_fixtures.py "END_PLATE_AISC_DG4 (2).xlsx"`.
* Los rangos de AISC 358-16 Tabla 6.1 del Excel deben confirmarse contra la norma impresa (así lo indica la hoja).
