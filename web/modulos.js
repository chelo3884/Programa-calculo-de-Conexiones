"use strict";
/* Catálogo de tipos de conexión: usado por la página de inicio, el proyecto y las miniaturas. */
window.MODULOS=[
 {id:'placa_base',cat:'Placas base',titulo:'Placa base y pernos de anclaje',corto:'Placa base',desc:'Columnas I/H y HSS, llave de corte opcional. DG1, ACI 318-19 cap. 17.'},
 {id:'end_plate',cat:'Momento viga–columna',titulo:'Placa extrema extendida (End Plate)',corto:'End plate 4E/4ES/8ES',desc:'DG4 y AISC 358-16 cap. 6: pernos, placa, ala y alma de columna, modo sísmico.'},
 {id:'bfp',cat:'Momento viga–columna',titulo:'BFP — Bolted Flange Plate',corto:'BFP',desc:'AISC 358-16 cap. 7 (SMF/IMF): diseño por capacidad con Mpr.'},
 {id:'wuf',cat:'Momento viga–columna',titulo:'Viga–columna soldada directa (WUF)',corto:'Soldada directa (WUF)',desc:'Alas CJP y placa simple de alma; efectos locales en la columna (J10).'},
 {id:'rodilla',cat:'Momento viga–columna',titulo:'Rodilla y cumbrera de galpón',corto:'Rodilla / cumbrera',desc:'Placa extrema al ala de columna o placa a placa, pendiente θ y cartela.'},
 {id:'hss_directa',cat:'Columnas HSS',titulo:'Momento: viga W soldada a columna HSS',corto:'HSS · soldada directa',desc:'DG24 Ej. 4.3: fluencia local del ala, punzonamiento, paredes laterales. No sísmica.'},
 {id:'hss_pasante',cat:'Columnas HSS',titulo:'Momento: columna HSS con placa pasante',corto:'HSS · placa pasante',desc:'DG24 Ej. 4.2: placa, pernos, bloque de cortante y soldadura perimetral. No sísmica.'},
 {id:'hss_diafragma',cat:'Columnas HSS',titulo:'Momento: HSS con placa de recorte (diafragma externo)',corto:'HSS · diafragma externo',desc:'Placa con recorte alrededor del HSS. Parte de la verificación es criterio propio.'},
 {id:'cortante_hss',cat:'Columnas HSS',titulo:'Cortante viga a columna HSS',corto:'HSS · cortante',desc:'Placa simple o pasante a la pared del HSS (K.6 / K.7).'},
 {id:'cortante_vc',cat:'Cortante',titulo:'Cortante viga–columna',corto:'Cortante viga–columna',desc:'Placa simple o doble ángulo apernado al ala de columna.'},
 {id:'cortante_vv',cat:'Cortante',titulo:'Cortante viga secundaria – viga principal',corto:'Cortante viga–viga',desc:'Placa simple o doble ángulo al alma, con destaje.'},
 {id:'empalme_viga',cat:'Empalmes',titulo:'Empalme de viga apernado',corto:'Empalme de viga',desc:'Placas de ala y alma, deslizamiento crítico o aplastamiento.'},
 {id:'empalme_col',cat:'Empalmes',titulo:'Empalme de columna',corto:'Empalme de columna',desc:'Apernado, PJP o CJP; apoyo por contacto; AISC 341 D2.5.'},
 {id:'gusset',cat:'Arriostramiento',titulo:'Cartela (gusset) de arriostramiento',corto:'Cartela (gusset)',desc:'Método de Fuerza Uniforme, Whitmore, bloque de cortante y soldaduras.'}
];
window.CATEGORIAS=['Placas base','Momento viga–columna','Columnas HSS','Cortante','Empalmes','Arriostramiento'];
window.modulo=id=>window.MODULOS.find(m=>m.id===id)||{id,titulo:id,corto:id,cat:'',desc:''};
