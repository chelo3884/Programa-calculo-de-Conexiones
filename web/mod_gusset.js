"use strict";
/* Cartela de arriostramiento (UFM) */
const dimH=(x1,x2,y,txt)=>`<path class="dim" d="M${x1} ${y-4}V${y+4}M${x2} ${y-4}V${y+4}M${x1} ${y}H${x2}"/><text class="dt" x="${(x1+x2)/2}" y="${y-5}" text-anchor="middle">${txt}</text>`;
const dimV=(x,y1,y2,txt)=>`<path class="dim" d="M${x-4} ${y1}H${x+4}M${x-4} ${y2}H${x+4}M${x} ${y1}V${y2}"/><text class="dt" transform="translate(${x-6} ${(y1+y2)/2}) rotate(-90)" text-anchor="middle">${txt}</text>`;
const cm2mm=v=>fmt(v*10,'Ls');
function gusElev(RES,S){
  const v=RES.vars,W=480,H=420,m=30,ext=Math.max(v.a,v.b)*1.5;
  const sc=Math.min((W-2*m-20)/(v.a+ext*0.5+v.cd/2),(H-2*m)/(v.b+ext*0.5+v.bd)),x0=W-m-20-(v.a+ext*0.5)*sc,yb=H-m-10-(v.bd)*sc;
  const X=q=>x0+q*sc,Y=q=>yb-q*sc;               // origen: cara de la columna (x) y ala superior de la viga (y)
  let s=`<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Elevación"><text x="8" y="16" style="font-weight:700">ELEVACIÓN DE LA CARTELA</text>`;
  const cw=Math.max(v.cd/2,12);
  s+=`<rect x="${X(-cw)}" y="${Y(v.b+ext*0.5)}" width="${cw*sc}" height="${(v.b+ext*0.5+v.bd)*sc}" fill="var(--steel)" stroke="var(--ink)" stroke-width="1.2"/>`;
  s+=`<rect x="${X(0)}" y="${Y(0)}" width="${(v.a+ext*0.5)*sc}" height="${v.bd*sc}" fill="var(--conc)" stroke="var(--ink)" opacity=".7"/>`;
  s+=`<rect x="${X(0)}" y="${Y(0)}" width="${(v.a+ext*0.5)*sc}" height="${v.btf*sc}" fill="var(--steel)" stroke="var(--ink)"/>`;
  s+=`<polygon points="${X(0)},${Y(0)} ${X(v.a)},${Y(0)} ${X(v.a)},${Y(Math.min(v.b*0.15,6))} ${X(Math.min(v.a*0.15,6)+0)},${Y(v.b)} ${X(0)},${Y(v.b)}" fill="var(--steelf)" stroke="var(--ink)" stroke-width="1.4" opacity=".9"/>`;
  // diagonal
  const th=v.th*Math.PI/180,dx=Math.cos(th),dy=Math.sin(th),L=Math.max(v.a,v.b)*1.3;
  const px=v.a*0.62,py=v.b*0.62-0.0;                                   // punto ancla sobre la cartela
  s+=`<line x1="${X(px)}" y1="${Y(py)}" x2="${X(px+dx*L)}" y2="${Y(py+dy*L)}" stroke="var(--tens)" stroke-width="6" opacity=".55"/>`;
  // pernos
  const nb=v.n,bx0=px-dx*(0),by0=py;
  for(let r=0;r<v.nl;r++)for(let k=0;k<nb;k++){const off=(r-(v.nl-1)/2)*v.g,al=-k*v.s;
    s+=`<circle cx="${X(bx0+dx*al-dy*off)}" cy="${Y(by0+dy*al+dx*off)}" r="${Math.max(2.5,v.db/2*sc)}" fill="var(--bolt)" stroke="var(--card)"/>`;}
  s+=dimH(X(0),X(v.a),Y(0)+20,`a = ${cm2mm(v.a)}`)+dimV(X(-cw)-8,Y(v.b),Y(0),`b = ${cm2mm(v.b)}`);
  s+=`<text class="dt" x="${X(v.a*0.1)}" y="${Y(v.b)-8}">θ = ${fmt(v.th,'')}°  ·  α ideal = ${cm2mm(v.alpha)} ${uf('Ls').l}</text>`;
  return s+`<text class="dt" x="${W-8}" y="${H-6}" text-anchor="end">esquemático · cotas [${uf('Ls').l}]</text></svg>`;
}
const MODULE={id:'gusset',api:'/api/gusset',title:'Cartela (gusset) de arriostramiento — Método de Fuerza Uniforme',
  rebuild:['b_nl','g_np'],
  visible(f,S){return true;},
  comboCols:[{sym:'Hb',label:'Hb ({u})',q:'F'},{sym:'Vb',label:'Vb ({u})',q:'F'},{sym:'Hc',label:'Hc ({u})',q:'F'},{sym:'Vc',label:'Vc ({u})',q:'F'}],
  comboHelp:'P positivo = tracción, negativo = compresión. Las filas con P = 0 se ignoran.',
  svgs:[{id:'svgElev',fn:gusElev}]};
