"use strict";
/* Conexión viga–columna con alas soldadas (CJP) y placa simple de alma */
const dimH=(x1,x2,y,txt)=>`<path class="dim" d="M${x1} ${y-4}V${y+4}M${x2} ${y-4}V${y+4}M${x1} ${y}H${x2}"/><text class="dt" x="${(x1+x2)/2}" y="${y-5}" text-anchor="middle">${txt}</text>`;
const dimV=(x,y1,y2,txt)=>`<path class="dim" d="M${x-4} ${y1}H${x+4}M${x-4} ${y2}H${x+4}M${x} ${y1}V${y2}"/><text class="dt" transform="translate(${x-6} ${(y1+y2)/2}) rotate(-90)" text-anchor="middle">${txt}</text>`;
const cm2mm=v=>fmt(v*10,'Ls');
function wufElev(RES,S){
  const v=RES.vars,W=460,H=400,m=26,colH=v.bd+60,Lb=Math.max(v.bd*1.2,v.L+25);
  const sc=Math.min((W-2*m-30)/(Lb+v.ctf+20),(H-2*m)/colH),x0=m+40+v.ctf*sc,cy=H/2+4,X=a=>x0+a*sc,Y=a=>cy-a*sc;
  let s=`<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Elevación"><text x="8" y="16" style="font-weight:700">ELEVACIÓN</text>`;
  s+=`<rect x="${X(-v.ctf)}" y="${Y(colH/2)}" width="${v.ctf*sc}" height="${colH*sc}" fill="var(--steel)" stroke="var(--ink)" stroke-width="1.2"/>`;
  s+=`<path d="M${X(-v.ctf)} ${Y(colH/2)}H${X(-v.ctf)-24}M${X(-v.ctf)} ${Y(-colH/2)}H${X(-v.ctf)-24}" stroke="var(--mut)" stroke-dasharray="3 3"/>`;
  if(v.cp){const t=Math.max(v.cp_t,0.5);for(const y of [v.bd/2-v.btf/2,-v.bd/2+v.btf/2])s+=`<rect x="${X(-v.ctf)-24}" y="${Y(y)-t*sc/2}" width="24" height="${Math.max(2,t*sc)}" fill="var(--grout)" stroke="var(--ink)" stroke-width=".8"/>`;}
  // viga
  s+=`<rect x="${X(0)}" y="${Y(v.bd/2-v.btf)}" width="${Lb*sc}" height="${(v.bd-2*v.btf)*sc}" fill="var(--conc)" stroke="var(--ink)" stroke-width=".8" opacity=".8"/>`;
  s+=`<g fill="var(--steel)" stroke="var(--ink)"><rect x="${X(0)}" y="${Y(v.bd/2)}" width="${Lb*sc}" height="${v.btf*sc}"/><rect x="${X(0)}" y="${Y(-v.bd/2+v.btf)}" width="${Lb*sc}" height="${v.btf*sc}"/></g>`;
  // soldaduras CJP (triángulos) y agujeros de acceso
  for(const sg of [1,-1]){s+=`<polygon points="${X(0)},${Y(sg*v.bd/2)} ${X(-0.6)},${Y(sg*(v.bd/2+0.5))} ${X(-0.6)},${Y(sg*(v.bd/2-v.btf-0.5))} ${X(0)},${Y(sg*(v.bd/2-v.btf))}" fill="var(--tens)" opacity=".85"/>`;
    s+=`<circle cx="${X(0)+8}" cy="${Y(sg*(v.bd/2-v.btf))+sg*4}" r="6" fill="var(--card)" stroke="var(--mut)"/>`;}
  // placa simple
  const pw=v.leh+6,ph=v.L;
  s+=`<rect x="${X(0)}" y="${Y(ph/2)}" width="${pw*sc}" height="${ph*sc}" fill="var(--steelf)" stroke="var(--ink)" stroke-width="1.3" opacity=".92"/>`;
  for(let k=0;k<v.n;k++)s+=`<circle cx="${X(6)}" cy="${Y(((v.n-1)/2-k)*v.s)}" r="${Math.max(2.5,v.db/2*sc)}" fill="var(--bolt)" stroke="var(--card)"/>`;
  s+=dimV(X(pw)+14,Y(ph/2),Y(-ph/2),`l = ${cm2mm(ph)}`)+dimV(X(Lb)+4,Y(v.bd/2),Y(-v.bd/2),`d = ${cm2mm(v.bd)}`);
  return s+`<text class="dt" x="${W-8}" y="${H-6}" text-anchor="end">cotas [${uf('Ls').l}] · placa esquemática · soldadura CJP (rojo)</text></svg>`;
}
function wufPlan(RES,S){
  const v=RES.vars,W=460,H=400,m=30,span=Math.max(v.cd,v.cbf)+60;
  const sc=Math.min((W-2*m)/(v.cbf+40),(H-2*m)/(v.cd+v.bd*0.9)),cx=W/2,cy=H/2,X=a=>cx+a*sc,Y=a=>cy-(a+v.cd/2)*sc;
  let s=`<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Planta"><text x="8" y="16" style="font-weight:700">PLANTA (corte a la altura del ala superior)</text>`;
  const yc=-v.bd*0.45; // columna abajo, viga hacia arriba
  s+=`<g fill="var(--steel)" stroke="var(--ink)"><rect x="${X(-v.cbf/2)}" y="${Y(yc)}" width="${v.cbf*sc}" height="${v.ctf*sc}"/><rect x="${X(-v.cbf/2)}" y="${Y(yc-v.cd+v.ctf)}" width="${v.cbf*sc}" height="${v.ctf*sc}"/><rect x="${X(-v.ctw/2)}" y="${Y(yc-v.ctf)}" width="${v.ctw*sc}" height="${(v.cd-2*v.ctf)*sc}"/></g>`;
  if(v.cp)for(const sx of [-1,1])s+=`<rect x="${X(sx>0?v.ctw/2:-v.ctw/2-v.cp_b)}" y="${Y(yc-v.ctf)}" width="${v.cp_b*sc}" height="${(v.cd-2*v.ctf)*sc}" fill="var(--grout)" stroke="var(--ink)" opacity=".5"/>`;
  const L=v.bd*0.9;
  s+=`<rect x="${X(-v.bbf/2)}" y="${Y(yc+L)}" width="${v.bbf*sc}" height="${L*sc}" fill="var(--steelf)" stroke="var(--ink)" stroke-width="1.2"/>`;
  s+=`<rect x="${X(-v.btw/2)}" y="${Y(yc+L)}" width="${v.btw*sc}" height="${L*sc}" fill="var(--steel)" opacity=".4"/>`;
  s+=`<path d="M${X(-v.bbf/2)} ${Y(yc)}H${X(v.bbf/2)}" stroke="var(--tens)" stroke-width="4"/>`;
  s+=`<text class="dt" x="${X(0)}" y="${Y(yc)+16}" text-anchor="middle" style="fill:var(--tens)">soldadura CJP del ala</text>`;
  s+=dimH(X(-v.bbf/2),X(v.bbf/2),Y(yc+L)-8,`bbf = ${cm2mm(v.bbf)}`)+dimV(X(v.cbf/2)+14,Y(yc),Y(yc-v.cd),`dc = ${cm2mm(v.cd)}`);
  return s+`<text class="dt" x="${W-8}" y="${H-6}" text-anchor="end">esquemático · cotas [${uf('Ls').l}]</text></svg>`;
}
const MODULE={id:'wuf',api:'/api/wuf',title:'Conexión viga–columna soldada directa (CJP) — alas soldadas y placa simple de alma',
  rebuild:['cp_usar','dos_lados'],
  visible(f,S){const n=f.name;if(n==='cp_t'||n==='cp_b')return S.cp_usar==='Sí';if(n==='Mu_op')return S.dos_lados==='Sí';return true;},
  comboCols:[{sym:'Ffu',label:'Ffu ({u})',q:'F'}],
  comboHelp:'Se usa |Mu| y |Vu| en la cara de la columna (convención de signos indiferente). Las filas con cargas en cero se ignoran.',
  svgs:[{id:'svgElev',fn:wufElev},{id:'svgPlan',fn:wufPlan}]};
