"use strict";
/* Conexiones de momento a columna HSS: viga W soldada directa (hss_directa) y placa pasante (hss_pasante) */
const dimH=(x1,x2,y,txt)=>`<path class="dim" d="M${x1} ${y-4}V${y+4}M${x2} ${y-4}V${y+4}M${x1} ${y}H${x2}"/><text class="dt" x="${(x1+x2)/2}" y="${y-5}" text-anchor="middle">${txt}</text>`;
const dimV=(x,y1,y2,txt)=>`<path class="dim" d="M${x-4} ${y1}H${x+4}M${x-4} ${y2}H${x+4}M${x} ${y1}V${y2}"/><text class="dt" transform="translate(${x-6} ${(y1+y2)/2}) rotate(-90)" text-anchor="middle">${txt}</text>`;
const c2m=v=>fmt(v*10,'Ls');
const svgH=(W,H,sc,titulo)=>`<svg data-sc="${sc}" data-f="10" viewBox="0 0 ${W} ${H}" role="img" aria-label="${titulo}"><text x="8" y="16" style="font-weight:700">${titulo}</text>`;
const rect=(x,y,w,h,fill,sw)=>`<rect x="${x}" y="${y}" width="${w}" height="${h}" fill="${fill}" stroke="var(--ink)" stroke-width="${sw||1}"/>`;

function hssElev(RES,S,pas){
  const v=RES.vars,W=480,H=400,m=26,colH=Math.max(v.bd*1.9,v.bd+80),half=pas?v.L/2:Math.max(v.bd*1.3,45+v.D);
  const sc=Math.min((W-2*m)/(2*half+0.1),(H-2*m)/colH),cx=W/2,cy=H/2,X=a=>cx+a*sc,Y=a=>cy-a*sc;
  let s=svgH(W,H,sc,'ELEVACIÓN (a lo largo de la viga)');
  // columna HSS: dos paredes (corte), longitud D
  s+=rect(X(-v.D/2),Y(colH/2),v.D*sc,colH*sc,'var(--steelf)',1.2)+rect(X(-v.D/2+v.t),Y(colH/2),(v.D-2*v.t)*sc,colH*sc,'var(--card)',.8);
  const yt=v.bd/2,tpl=pas?v.tp:0;
  for(const sg of [1,-1]){
    const xs=sg*v.D/2,len=pas?half-v.D/2:Math.min(half-v.D/2,v.bd*1.2);
    const x0=sg>0?X(xs):X(xs)-len*sc;
    // ala y alma de la viga (a cada lado si pasante; solo derecha si directa)
    if(!pas&&sg<0)continue;
    s+=`<rect x="${x0}" y="${Y(yt-v.btf)}" width="${len*sc}" height="${(v.bd-2*v.btf)*sc}" fill="var(--conc)" stroke="var(--ink)" opacity=".8"/>`;
    s+=rect(x0,Y(yt),len*sc,v.btf*sc,'var(--steel)')+rect(x0,Y(-yt+v.btf),len*sc,v.btf*sc,'var(--steel)');
    if(pas){
      for(const sy of [1,-1])s+=rect(x0,Y(sy>0?yt+tpl:-yt),len*sc,tpl*sc,'var(--steelf)',1.2);
      for(let r=0;r<v.nb;r++){const bx=sg>0?X(v.D/2+v.a+r*v.s):X(-v.D/2-v.a-r*v.s);
        for(const sy of [1,-1])s+=`<circle cx="${bx}" cy="${Y(sy*(yt+tpl/2-sy*(-v.btf/2)))}" r="${Math.max(2.5,v.db/2*sc)}" fill="var(--bolt)" stroke="var(--card)"/>`;}
    }else{
      s+=`<polygon points="${X(v.D/2)},${Y(yt)} ${X(v.D/2)-6},${Y(yt+0.6)} ${X(v.D/2)-6},${Y(yt-v.btf-0.6)} ${X(v.D/2)},${Y(yt-v.btf)}" fill="var(--tens)" opacity=".85"/>`;
      s+=`<polygon points="${X(v.D/2)},${Y(-yt)} ${X(v.D/2)-6},${Y(-yt-0.6)} ${X(v.D/2)-6},${Y(-yt+v.btf+0.6)} ${X(v.D/2)},${Y(-yt+v.btf)}" fill="var(--tens)" opacity=".85"/>`;
      // placa de corte
      const ph=v.L,px=v.D/2;
      s+=rect(X(px),Y(ph/2),(v.leh+v.a)*sc,ph*sc,'var(--steelf)',1.2);
      for(let k=0;k<v.n;k++)s+=`<circle cx="${X(px+v.a)}" cy="${Y(((v.n-1)/2-k)*v.s)}" r="${Math.max(2.5,v.db/2*sc)}" fill="var(--bolt)" stroke="var(--card)"/>`;
    }
  }
  s+=dimV(X(half)-4,Y(yt),Y(-yt),`d = ${c2m(v.bd)}`);
  if(pas)s+=dimH(X(-half),X(half),Y(-colH/2)+14,`L placa = ${c2m(v.L)}`);
  return s+`<text class="dt" x="${W-8}" y="${H-6}" text-anchor="end">cotas [${uf('Ls').l}] · ${pas?'placa pasante':'soldadura directa'} · esquemático</text></svg>`;
}
function hssPlan(RES,S,pas){
  const v=RES.vars,W=480,H=400,m=26,xr=pas?v.L/2:Math.max(v.bd*1.1,40+v.D/2),span=pas?2*xr:xr+v.D/2;
  const sc=Math.min((W-2*m)/span,(H-2*m)/Math.max(v.W,pas?v.bp:v.bbf)),x0=pas?W/2:m+v.D/2*sc+10,cy=H/2,X=a=>x0+a*sc,Y=a=>cy-a*sc;
  let s=svgH(W,H,sc,'PLANTA (a la altura del ala superior)');
  s+=rect(X(-v.D/2),Y(v.W/2),v.D*sc,v.W*sc,'var(--steelf)',1.2)+rect(X(-v.D/2+v.t),Y(v.W/2-v.t),(v.D-2*v.t)*sc,(v.W-2*v.t)*sc,'var(--card)',.8);
  const sides=pas?[1,-1]:[1];
  for(const sg of sides){
    const ex=sg*(pas?xr:xr),x1=sg*v.D/2;
    if(pas){
      const lo=Math.min(x1,sg*(xr)),w=Math.abs(xr-v.D/2);
      s+=rect(X(sg>0?v.D/2:-xr),Y(v.bp/2),w*sc,v.bp*sc,'var(--steelf)',1.3);
      s+=`<g fill="var(--steel)" stroke="var(--ink)" opacity=".85">`+`<rect x="${X(sg>0?v.D/2+0.1:-xr)}" y="${Y(v.bbf/2)}" width="${(w-0.1)*sc}" height="${v.bbf*sc}"/></g>`;
      for(let r=0;r<v.nb;r++)for(const rr of [1,-1])s+=`<circle cx="${X(sg*(v.D/2+v.a+r*v.s))}" cy="${Y(rr*v.g/2)}" r="${Math.max(2.5,v.db/2*sc)}" fill="var(--bolt)" stroke="var(--card)"/>`;
    }else{
      s+=rect(X(v.D/2),Y(v.bbf/2),(xr-v.D/2)*sc,v.bbf*sc,'var(--steel)',1.2);
      s+=`<rect x="${X(v.D/2)}" y="${Y(v.btw/2)}" width="${(xr-v.D/2)*sc}" height="${v.btw*sc}" fill="var(--conc)" opacity=".6"/>`;
      s+=`<path d="M${X(v.D/2)} ${Y(v.bbf/2)}V${Y(-v.bbf/2)}" stroke="var(--tens)" stroke-width="4"/>`;
    }
  }
  if(pas)s+=dimH(X(-xr),X(xr),Y(-v.bp/2)-6,`placa ${c2m(2*xr)} × ${c2m(v.bp)}`);
  s+=dimV(X(-v.D/2)-8,Y(v.W/2),Y(-v.W/2),`B = ${c2m(v.W)}`);
  return s+`<text class="dt" x="${W-8}" y="${H-6}" text-anchor="end">cotas [${uf('Ls').l}] · esquemático</text></svg>`;
}
const MODULE_BASE={rebuild:['hss_perfil','vg_perfil','dos_lados'],visible(f,S){return f.name==='hss_cara'?S.hss_perfil!==ARMADO:true;}};
