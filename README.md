# Diseño de conexiones metálicas

Programa en Python (sólo biblioteca estándar) con interfaz HTML interactiva, en la línea de RAM Connection.
Primer módulo: **placa base y pernos de anclaje** (AISC Design Guide 1, AISC 360-16 J2/J8, ACI 318-19 cap. 17, LRFD).

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

    app.py                      servidor local + API (/api/placa_base/calc)
    placa_base/engine.py        motor de cálculo (kgf, cm internamente)
    placa_base/catalogos.json   perfiles, aceros, pernos, diámetros, electrodos (editable)
    web/index.html              interfaz
    tests/                      verificación contra el Excel y contra AISC Design Examples J.6

## Verificación

    python3 -m unittest tests.test_placa_base

* Reproduce las 5 combinaciones de `PLACA_BASE_AISC_DG1.xlsx` (todos los ratios, a 6 decimales).
* Ejemplo AISC J.6 (placa 22×22 in, Pu = 690 kip): m = 4.97 in, n = 6.12 in, n' = 3.11 in, fp = 1.43 ksi, tmin = 1.82 in.

Herramienta de apoyo: la responsabilidad del diseño es del ingeniero que la usa.
