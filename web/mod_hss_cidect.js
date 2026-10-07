"use strict";
/* CIDECT 9: diafragma externo (hss_dext) y placa longitudinal de arriostramiento a RHS (hss_placalong) */
function dextElev(RES,S){
  const v=RES.vars,W=480,H=400,m=26,half=Math.max(v.W/2+v.Ln+v.bd*0.5,45);
  const colH=v.bd*2.4,sc=Math.min((W-2*m)/(2*half),(H-2*m)/colH),cx=W/2,cy=H/2,X=a=>cx+a*sc,Y=a=>cy-a*sc;
  let s=svgH(W,H,sc,'ELEVACIÓN (a lo largo de la viga)');
  s+=rect(X(-v.W/2),Y(colH/2),v.W*sc,colH*sc,'var(--steelf)',1.2)+rect(X(-v.W/2+v.t),Y(colH/2),(v.W-2*v.t)*sc,colH*sc,'var(--card)',.8);
  const yt=v.bd/2;
  for(const sg of [1,-1]){
    const x0=sg>0?X(v.W/2):X(-v.W/2-(half-v.W/2)),len=(half-v.W/2)*sc;
    s+=`<rect x="${x0}" y="${Y(yt-v.btf)}" width="${len}" height="${(v.bd-2*v.btf)*sc}" fill="var(--conc)" stroke="var(--ink)" opacity=".8"/>`;
    s+=rect(x0,Y(yt),len,v.btf*sc,'var(--steel)')+rect(x0,Y(-yt+v.btf),len,v.btf*sc,'var(--steel)');
    const dx=sg>0?X(v.W/2):X(-v.W/2-v.Ln),dl=v.Ln*sc;
    for(const sy of [1,-1])s+=rect(dx,Y(sy>0?yt+v.td:-yt),dl,v.td*sc,'var(--steelf)',1.3);
    for(const sy of [1,-1])s+=`<rect x="${sg>0?X(v.W/2)-v.t*sc:X(-v.W/2)}" y="${Y(sy>0?yt+v.td:-yt)}" width="${v.t*sc}" height="${v.td*sc}" fill="var(--tens)" opacity=".8"/>`;
  }
  s+=dimV(X(half)-4,Y(yt),Y(-yt),`d = ${c2m(v.bd)}`)+dimH(X(v.W/2),X(v.W/2+v.Ln),Y(yt+v.td)-12,`Lnervio = ${c2m(v.Ln)}`);
  return s+`<text class="dt" x="${W-8}" y="${H-6}" text-anchor="end">cotas [${uf('Ls').l}] · diafragmas externos · esquemático</text></svg>`;
}
function dextPlan(RES,S){
  const v=RES.vars,W=480,H=400,m=30,xe=v.W/2+v.Ln,y1=v.W/2+v.hd,tn=Math.tan(v.th*Math.PI/180),xs=Math.max(v.W/2,xe-(y1-v.bbf/2)/tn);
  const sc=Math.min((W-2*m)/(2*xe+10),(H-2*m)/(2*y1+20)),cx=W/2,cy=H/2,X=a=>cx+a*sc,Y=a=>cy-a*sc;
  let s=svgH(W,H,sc,'PLANTA (diafragma a la altura de las alas)');
  const pts=[[-xe,v.bbf/2],[-xs,y1],[xs,y1],[xe,v.bbf/2],[xe,-v.bbf/2],[xs,-y1],[-xs,-y1],[-xe,-v.bbf/2]];
  s+=`<polygon points="${pts.map(p=>X(p[0])+','+Y(p[1])).join(' ')}" fill="var(--steelf)" stroke="var(--ink)" stroke-width="1.3"/>`;
  s+=rect(X(-v.W/2),Y(v.W/2),v.W*sc,v.W*sc,'var(--card)',1.4)+rect(X(-v.W/2+v.t),Y(v.W/2-v.t),(v.W-2*v.t)*sc,(v.W-2*v.t)*sc,'var(--steel)',.8);
  s+=`<path d="M${X(-v.W/2)} ${Y(v.W/2)}H${X(v.W/2)}V${Y(-v.W/2)}H${X(-v.W/2)}Z" fill="none" stroke="var(--tens)" stroke-width="3"/>`;
  for(const sg of [1,-1])s+=`<rect x="${X(sg>0?xe-0.01:-xe-(xe-v.W/2)*0.6)}" y="${Y(v.bbf/2)}" width="${(xe-v.W/2)*0.6*sc}" height="${v.bbf*sc}" fill="var(--steel)" stroke="var(--ink)" opacity=".7"/>`;
  s+=dimH(X(v.W/2),X(xe),Y(-y1)-8,`Lnervio ${c2m(v.Ln)}`)+dimV(X(-xe)+8,Y(y1),Y(v.W/2),`hd ${c2m(v.hd)}`);
  return s+`<text class="dt" x="${W-8}" y="${H-6}" text-anchor="end">θ = ${v.th}° · soldadura perimetral en rojo · esquemático</text></svg>`;
}
const MODULE_DEXT=Object.assign({},MODULE_BASE,{id:'hss_dext',api:'/api/hss_dext',title:'Viga W – columna RHS con diafragmas externos (CIDECT 9 §8.6)',
  comboCols:[{sym:'Ff',label:'Ff ({u})',q:'F'}],
  comboHelp:'Mu es el momento en la cara de la columna. La verificación de sobrerresistencia (Mj,cf* ≥ α·L/(L − Lnervio)·Mpl) no depende de las combinaciones. φ por combinación: criterio propio.',
  svgs:[{id:'svgElev',fn:dextElev},{id:'svgPlan',fn:dextPlan}]});

function plElev(RES,S){
  const v=RES.vars,W=480,H=400,m=26,h=Math.max(v.hp*2.2,v.bc*2.4);
  const sc=Math.min((W-2*m)/(v.bc*3+h*0.8),(H-2*m)/(h*1.6)),cx=W*0.34,cy=H/2,X=a=>cx+a*sc,Y=a=>cy-a*sc;
  let s=svgH(W,H,sc,'ELEVACIÓN');
  const colH=h*1.5;
  s+=rect(X(-v.bc/2),Y(colH/2),v.bc*sc,colH*sc,'var(--steelf)',1.2)+rect(X(-v.bc/2+v.tc),Y(colH/2),(v.bc-2*v.tc)*sc,colH*sc,'var(--card)',.8);
  const th=v.th*Math.PI/180,L=h*0.95,hpl=v.hp/Math.sin(th),x0=v.bc/2,y0=-hpl/2;
  // placa: borde vertical soldado a la cara (x0), y= −hp'/2..hp'/2; extremo libre inclinado a θ respecto de la columna
  const dx=Math.cos(th)*L,dy=Math.sin(th)*L;
  s+=`<polygon points="${X(x0)},${Y(hpl/2)} ${X(x0+dx)},${Y(hpl/2+dy*0)} ${X(x0+dx)},${Y(-hpl/2)} ${X(x0)},${Y(-hpl/2)}" fill="var(--steelf)" stroke="var(--ink)" stroke-width="1.3"/>`;
  s+=`<path d="M${X(x0)} ${Y(hpl/2)}V${Y(-hpl/2)}" stroke="var(--tens)" stroke-width="4"/>`;
  for(let k=0;k<v.nb;k++)s+=`<circle cx="${X(x0+dx*0.55+k*v.s*Math.cos(th)*0)}" cy="${Y(((v.nb-1)/2-k)*v.s)}" r="${Math.max(2.5,v.db/2*sc)}" fill="var(--bolt)" stroke="var(--card)"/>`;
  s+=dimV(X(x0)+12,Y(hpl/2),Y(-hpl/2),`hp' = ${c2m(hpl)}`);
  s+=`<text class="dt" x="${X(x0)+30}" y="${Y(-hpl/2)-12}">θ = ${v.th}°</text>`;
  return s+`<text class="dt" x="${W-8}" y="${H-6}" text-anchor="end">cotas [${uf('Ls').l}] · esquemático</text></svg>`;
}
function plPlan(RES,S){
  const v=RES.vars,W=480,H=400,m=30,ext=v.bc*1.6,sc=Math.min((W-2*m)/(v.bc*2+ext),(H-2*m)/(v.bc*1.4)),cx=W*0.36,cy=H/2,X=a=>cx+a*sc,Y=a=>cy-a*sc;
  let s=svgH(W,H,sc,'SECCIÓN (corte horizontal)');
  s+=rect(X(-v.bc/2),Y(v.hc/2),v.bc*sc,v.hc*sc,'var(--steelf)',1.4)+rect(X(-v.bc/2+v.tc),Y(v.hc/2-v.tc),(v.bc-2*v.tc)*sc,(v.hc-2*v.tc)*sc,'var(--card)',.8);
  const pe=ext;
  s+=rect(X(v.bc/2),Y(v.bp/2),pe*sc,v.bp*sc,'var(--steel)',1.2);
  if(v.mult===2)s+=rect(X(-v.bc/2-pe),Y(v.bp/2),pe*sc,v.bp*sc,'var(--steel)',1.2);
  s+=`<polygon points="${X(v.bc/2)},${Y(v.bp/2)} ${X(v.bc/2)+v.w*sc},${Y(v.bp/2)} ${X(v.bc/2)},${Y(v.bp/2+v.w)}" fill="var(--tens)"/><polygon points="${X(v.bc/2)},${Y(-v.bp/2)} ${X(v.bc/2)+v.w*sc},${Y(-v.bp/2)} ${X(v.bc/2)},${Y(-v.bp/2-v.w)}" fill="var(--tens)"/>`;
  s+=dimV(X(-v.bc/2)-10,Y(v.hc/2),Y(-v.hc/2),`hc = ${c2m(v.hc)}`)+dimH(X(-v.bc/2),X(v.bc/2),Y(-v.hc/2)+20,`bc = ${c2m(v.bc)}`);
  return s+`<text class="dt" x="${W-8}" y="${H-6}" text-anchor="end">placa bp = ${c2m(v.bp)} · soldadura en rojo · esquemático</text></svg>`;
}
const MODULE_PL=Object.assign({},MODULE_BASE,{id:'hss_placalong',api:'/api/hss_placalong',title:'Arriostramiento a columna RHS con placa longitudinal (CIDECT 9 §10.1)',
  comboCols:[{sym:'Np*',label:'Np* ({u})',q:'F'},{sym:'Np,s1%',label:'Np,s1% ({u})',q:'F'}],
  comboHelp:'N: fuerza mayorada de la diagonal (+ tracción, − compresión); Ns: de servicio. Pu y Mu de la columna definen n = σc/fc,y en la ecuación 10.1.',
  svgs:[{id:'svgElev',fn:plElev},{id:'svgPlan',fn:plPlan}]});
