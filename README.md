# Diseño de conexiones metálicas

Programa en Python (sólo biblioteca estándar) con interfaz HTML interactiva, en la línea de RAM Connection.

**Módulos:** `/placa_base.html` (placa base y pernos de anclaje) · `/end_plate.html` (placa extrema extendida 4E/4ES/8ES, DG4 y AISC 358-16 cap. 6) · `/bfp.html` (Bolted Flange Plate, AISC 358-16 cap. 7) · `/rodilla.html` (rodilla y cumbrera de galpón, DG16/DG4). La página de inicio `/` los enlaza.

Módulo 1: **placa base y pernos de anclaje** (columnas de perfil I/H y HSS rectangular/cajón) (AISC Design Guide 1, AISC 360-16 J2/J8, ACI 318-19 cap. 17, LRFD).

## Cómo abrirlo (sin usar el cmd)

1. Instale **Python 3.9 o superior** (python.org; en Windows marque *Add Python to PATH*). No hay que instalar librerías.
2. Descomprima **toda** la carpeta del programa (por ejemplo en `C:\\Ingenieria\\Conexiones\\`).
3. Haga doble clic en **`Crear_acceso_directo.vbs`**: crea el icono *Conexiones Metálicas* en el Escritorio y en el menú Inicio.
4. Desde entonces, un doble clic en ese icono abre el programa en el navegador. Aparece una ventana pequeña de control; al cerrarla se apaga el programa.

Alternativas: doble clic directo en `Iniciar.pyw` (mismo efecto, sin crear el icono), `Iniciar.bat` (con consola) o, en macOS/Linux, `Iniciar.command`. Por línea de comandos: `python3 app.py [--port 8000] [--no-browser]`.
Si el programa ya está abierto, un nuevo doble clic solo vuelve a abrir el navegador.

**Ejecutable (.exe) sin instalar Python:** en GitHub, pestaña *Actions → Generar ejecutable de Windows → Run workflow*; al terminar se descarga `ConexionesMetalicas_Windows.zip` (contiene el .exe, con el icono, sin consola). También puede generarse en su PC con `pip install pyinstaller && python tools/build_exe.py`.

Módulos (página de inicio `/`): placa base, placa extrema 4E/4ES/8ES, BFP, rodilla y cumbrera, cortante viga–columna, cortante viga secundaria–viga principal, empalme de viga y empalme de columna.

* Pestaña **Diseño**: parámetros; los dibujos se redibujan al mover cualquier dato; tabla de verificaciones con ratios.
* Pestaña **Cargas** (donde aplica): combinaciones LRFD. **Memoria de cálculo**: todos los pasos intermedios.
* **Unidades**: Tonf·m·mm (predeterminado), kgf·cm, SI, US o selección individual por magnitud.
* **Reporte**: HTML imprimible (Imprimir → Guardar como PDF) o descargable. Guardar / abrir proyecto en `.json`.

## Estructura

    app.py                      servidor local + API (/api/placa_base/calc, /api/end_plate/calc)
    placa_base/engine.py        motor de cálculo (kgf, cm internamente)
    placa_base/catalogos.json   perfiles, aceros, pernos, diámetros, electrodos (editable)
    web/                        index.html (módulos), placa_base.html, end_plate.html, common.js (unidades)
    xlcore.py                   núcleo que evalúa los modelos generados desde Excel
    end_plate/ bfp/ rodilla/    un paquete por módulo (xl_model.py generado con tools/xl2py.py, catálogos, campos de entrada)
    tools/                      xl2py.py (Excel→Python) y make_fixtures.py (casos de prueba con LibreOffice)
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

## Módulos generados desde Excel (end_plate, bfp, rodilla)

* Las fórmulas se **traducen automáticamente** de las hojas de Excel (`python3 tools/xl2py.py "<hoja>.xlsx" <paquete>`), de modo que cada fila de la memoria es la de la hoja (símbolo, descripción, unidad). Para cambiar un criterio, se corrige en el Excel y se regenera.
* Pruebas (`python3 -m unittest discover -s tests`): 38 variantes de las tres hojas (4E/4ES/8ES, sísmico y no sísmico, IMF/SMF, rodilla y cumbrera, cortante con placa simple/extendida/doble ángulo y destaje, configuraciones al ras y extendida, perfiles armados, con y sin rigidizadores) recalculadas con LibreOffice; coinciden todas las filas de CALCULO y la tabla de verificaciones.
* Para regenerar los casos de prueba hace falta LibreOffice Calc: `python3 tools/make_fixtures.py end_plate "END_PLATE_AISC_DG4 (2).xlsx"` (ídem `bfp`, `rodilla`).
* Los rangos de AISC 358-16 Tabla 6.1 del Excel deben confirmarse contra la norma impresa (así lo indica la hoja).
* Los dibujos de BFP y rodilla son esquemáticos; la placa de alma del BFP y la cartela de la rodilla se dibujan sin cotas completas.

## Cortante (cortante_vv y cortante_vc)

* **Viga secundaria a viga principal** (`cortante_vv`): traducido de `CORTANTE_VIGA_VIGA_AISC.xlsx` (placa simple convencional o extendida, doble ángulo apernado, destaje superior o doble). Verificado contra 6 variantes recalculadas con LibreOffice.
* **Viga a ala de columna** (`cortante_vc`): la hoja original solo cubre viga–viga, así que este módulo reutiliza la misma verificación del lado de la viga con el **ala de la columna como soporte** (su tf y su Fu reemplazan al alma de la viga principal en el aplastamiento de los pernos y en el filete mínimo, Manual Ec. 9-2/9-3; sin destaje ni viga opuesta). Verificado con AISC Design Examples v15, Ej. II.A-1A (corte de perno 35.8 kip, aplastamiento 66.7 kip, 8 pernos en corte simple 286 kip). **No incluye** flexión local del ala de columna, conexión al alma de columna ni columnas HSS.

## Empalmes (empalme_viga y empalme_col)

* Traducidos de `EMPALME_VIGA_AISC.xlsx` y `EMPALME_COLUMNA_AISC.xlsx`; verificados contra 12 variantes recalculadas con LibreOffice (apernado con aplastamiento o deslizamiento crítico, con/sin placas interiores, reparto del momento por inercia, PJP/CJP, extremos fresados o no, columnas de distinto peralte con relleno, perfiles armados).
* **Verificación con los AISC Design Examples v15** (`tests/test_empalmes_aisc.py`). El PDF no trae un empalme completo de viga ni de columna, así que se comparan los estados límite que comparten con los ejemplos de placas atornilladas:
  * II.B-1 (placa de ala W18x50, 7×¾ in A36, 8 pernos Ø7/8" A325-N): pernos 194 kip, fluencia de placa 170 kip, ruptura 164 kip, bloque de cortante 320 kip, ruptura del ala de viga F13.1 318 kip-ft (el programa da ~1 % menos porque calcula Sx con la fórmula simplificada de la hoja).
  * II.A-20 (placa de alma 12×⅜ in A36, 4 pernos): ruptura por corte 78.0 kip y bloque de cortante 80.1 kip por placa; fluencia por corte 97.2 kip.
  * II.C-3: deslizamiento crítico de un perno Ø1" A325 clase A = 17.3 kip.
* El grupo de pernos del alma usa el método elástico (conservador); el IC de AISC Tabla 7-6 da resistencias mayores, por lo que ese chequeo no se compara 1 a 1 con el ejemplo.

## Viga–columna soldada directa (wuf)

* Módulo escrito a mano sobre `aisc.py` (biblioteca de estados límite AISC 360-16) y `handmod.py` (estructura de hoja/combinaciones/verificaciones). Alas con soldadura CJP; alma con placa simple soldada a la columna y apernada a la viga (o solo soldada).
* Verifica viga (φMp, φVn), columna (J10.1 flexión local del ala, J10.2 fluencia local del alma, J10.3 aplastamiento, J10.4 pandeo, J10.6 zona de panel, placas de continuidad) y la placa de alma (grupo de pernos, fluencia/ruptura por corte, bloque de cortante, filetes, ruptura del ala de columna).
* Comprobado con AISC Design Examples v15, Ej. II.B-1 (68.9, 73.1, 72.9, 58.8, 70.0, 100.2, 410.7 y 171.1 kip) en `tests/test_wuf.py` y `tests/test_aisc_lib.py`.

## Cartela de arriostramiento (gusset, UFM)

* Módulo escrito a mano (`gusset/`): fuerzas de interfaz por el Método de Fuerza Uniforme (Manual Parte 13), con θ medido desde la horizontal y α = (β̄ + eb)/tanθ − ec; ancho de Whitmore (fluencia/pandeo), bloque de cortante, pernos de la diagonal, soldaduras a viga y columna (método elástico, conservador) y cargas concentradas en viga/columna.
* Comprobado en `tests/test_gusset.py`: equilibrio (Hb + Hc = P·cosθ, Vb + Vc = P·senθ) y estados límite de la cartela del ejemplo II.C-3 (Whitmore 19.4 in, fluencia 473 kip, bloque de cortante 480 kip). **El PDF no trae un ejemplo numérico del UFM**, por eso las fuerzas de interfaz solo se validan por equilibrio y fórmulas del Manual.
* No verifica la diagonal en sí ni su conexión en el otro extremo.
