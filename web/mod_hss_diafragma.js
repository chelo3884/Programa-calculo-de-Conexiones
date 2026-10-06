"use strict";
/* Placa de recorte (diafragma externo) en columna HSS */
function diaPlan(RES,S){
  const v=RES.vars,W=480,H=400,m=26,xr=v.L/2,ancho=v.W+2*v.ws;
  const sc=Math.min((W-2*m)/(2*xr),(H-2*m)/ancho),cx=W/2,cy=H/2,X=a=>cx+a*sc,Y=a=>cy-a*sc;
  let s=svgH(W,H,sc,'PLANTA (placa de recorte a la altura del ala superior)');
  const we=Math.max(v.w1,v.bbf+2),hc=v.W/2+v.ws;
  const pts=[[-xr,we/2],[-(v.D/2+v.d1*0.6),hc],[v.D/2+v.d1*0.6,hc],[xr,we/2],[xr,-we/2],[v.D/2+v.d1*0.6,-hc],[-(v.D/2+v.d1*0.6),-hc],[-xr,-we/2]];
  s+=`<polygon points="${pts.map(p=>X(p[0])+','+Y(p[1])).join(' ')}" fill="var(--steelf)" stroke="var(--ink)" stroke-width="1.3"/>`;
  s+=rect(X(-v.D/2),Y(v.W/2),v.D*sc,v.W*sc,'var(--card)',1.4)+rect(X(-v.D/2+v.t),Y(v.W/2-v.t),(v.D-2*v.t)*sc,(v.W-2*v.t)*sc,'var(--steel)',.8);
  s+=`<path d="M${X(-v.D/2)} ${Y(v.W/2)}H${X(v.D/2)}V${Y(-v.W/2)}H${X(-v.D/2)}Z" fill="none" stroke="var(--tens)" stroke-width="3"/>`;
  for(const sg of [1,-1]){
    s+=`<rect x="${X(sg>0?v.D/2+1:-xr)}" y="${Y(v.bbf/2)}" width="${(xr-v.D/2-1)*sc}" height="${v.bbf*sc}" fill="none" stroke="var(--ink)" stroke-dasharray="4 3" opacity=".6"/>`;
    for(let r=0;r<v.nb;r++)for(const rr of [1,-1])s+=`<circle cx="${X(sg*(v.D/2+v.d1+r*v.s))}" cy="${Y(rr*v.g/2)}" r="${Math.max(2.5,v.db/2*sc)}" fill="var(--bolt)" stroke="var(--card)"/>`;
  }
  s+=dimV(X(-xr)+10,Y(hc),Y(-hc),`B + 2ws = ${c2m(ancho)}`)+dimH(X(-xr),X(xr),Y(-hc)-10,`placa ${c2m(2*xr)}`);
  return s+`<text class="dt" x="${W-8}" y="${H-6}" text-anchor="end">soldadura perimetral en rojo · esquemático · cotas [${uf('Ls').l}]</text></svg>`;
}
const MODULE=Object.assign({},MODULE_BASE,{id:'hss_diafragma',api:'/api/hss_diafragma',title:'Viga W – columna HSS con placa de recorte / diafragma externo (momento, no sísmica)',
  comboCols:[{sym:'Pr',label:'Pr placa ({u})',q:'F'}],
  comboHelp:'Se usa el mismo |Mu| y |Vu| en las vigas de ambos lados. Solo cargas no sísmicas. La transferencia placa → HSS es un criterio simplificado propio.',
  svgs:[{id:'svgElev',fn:(R,S)=>hssElev(R,S,true)},{id:'svgPlan',fn:diaPlan}]});
