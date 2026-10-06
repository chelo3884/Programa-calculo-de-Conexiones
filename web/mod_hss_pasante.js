"use strict";
const MODULE=Object.assign({},MODULE_BASE,{id:'hss_pasante',api:'/api/hss_pasante',title:'Viga W – columna HSS con placa pasante (momento, no sísmica)',
  comboCols:[{sym:'Ru',label:'Ru placa ({u})',q:'F'},{sym:'Pconn',label:'Pconn ({u})',q:'F'},{sym:'Mconn',label:'Mconn ({u})',q:'M'}],
  comboHelp:'Mi, Vi: viga izquierda; Md, Vd: viga derecha (signos del ejemplo 4.2: momento de la derecha − izquierda). Pu: axial del HSS superior. Solo cargas no sísmicas.',
  svgs:[{id:'svgElev',fn:(R,S)=>hssElev(R,S,true)},{id:'svgPlan',fn:(R,S)=>hssPlan(R,S,true)}]});
