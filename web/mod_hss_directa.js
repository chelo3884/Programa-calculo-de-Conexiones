"use strict";
const MODULE=Object.assign({},MODULE_BASE,{id:'hss_directa',api:'/api/hss_directa',title:'Viga W soldada directa a columna HSS (momento, no sísmica)',
  comboCols:[{sym:'Ff',label:'Ff ({u})',q:'F'},{sym:'Qf',label:'Qf'}],
  comboHelp:'Se usa |Mu| y |Vu| de la viga. Pu y Mu del HSS solo afectan el factor Qf de las paredes laterales. Solo cargas no sísmicas (Design Guide 24).',
  svgs:[{id:'svgElev',fn:(R,S)=>hssElev(R,S,false)},{id:'svgPlan',fn:(R,S)=>hssPlan(R,S,false)}]});
