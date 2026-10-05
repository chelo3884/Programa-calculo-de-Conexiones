"use strict";
/* Dibujos y configuración de los empalmes apernados (empalme_viga, empalme_col). Unidades de trabajo: mm. */
const dimH=(x1,x2,y,txt)=>`<path class="dim" d="M${x1} ${y-4}V${y+4}M${x2} ${y-4}V${y+4}M${x1} ${y}H${x2}"/><text class="dt" x="${(x1+x2)/2}" y="${y-5}" text-anchor="middle">${txt}</text>`;
const dimV=(x,y1,y2,txt)=>`<path class="dim" d="M${x-4} ${y1}H${x+4}M${x-4} ${y2}H${x+4}M${x} ${y1}V${y2}"/><text class="dt" transform="translate(${x-6} ${(y1+y2)/2}) rotate(-90)" text-anchor="middle">${txt}</text>`;
const mm=v=>fmt(v,'Ls');
const dia=s=>({'5/8"':15.875,'3/4"':19.05,'7/8"':22.225,'1"':25.4,'1-1/8"':28.575})[s]||20;
const svgOpen=(t,W,H,sc)=>`<svg data-sc="${sc}" data-f="1" viewBox="0 0 ${W} ${H}" role="img" aria-label="${t}"><text x="8" y="16" style="font-weight:700">${t}</text>`;

/* ───────────── Empalme de viga ───────────── */
function geoViga(RES,S){
  const D=RES.derivados,g={};
  g.d=D.vg_d_mm;g.bf=D.vg_bf_mm;g.tw=D.vg_tw_mm;g.tf=D.vg_tf_mm;g.gap=S.gap;
  g.n=S.fa_n;g.s=S.fa_s;g.leb=S.fa_Leb;g.lep=S.fa_Lep;g.gg=S.fa_g;g.db=dia(S.fa_diam);
  g.bo=S.pf_bo;g.to=S.pf_to;g.inn=S.pf_in==='Sí';g.bi=S.pf_bi;g.ti=S.pf_ti;
  g.x1=g.gap/2+g.leb;g.xe=g.x1+(g.n-1)*g.s+g.lep;           // desde el eje del empalme: 1.er perno y extremo de placa
  g.hp=S.pw_h;g.tp=S.pw_t;g.nr=S.wa_nr;g.nc=S.wa_nc;g.sv=S.wa_sv;g.sh=S.wa_sh;g.wle=S.wa_Leb;g.wlp=S.wa_Lep;g.wdb=dia(S.wa_diam);
  g.wx1=g.gap/2+g.wle;g.wxe=g.wx1+(g.nc-1)*g.sh+g.wlp;
  return g;
}
function vigaElev(RES,S){
  const g=geoViga(RES,S),W=460,H=380,m=24,xe=Math.max(g.xe,g.wxe);
  const half=xe+30,sc=Math.min((W-2*m)/(2*half),(H-2*m-30)/(g.d+2*g.to+30)),cx=W/2,cy=H/2+8,X=a=>cx+a*sc,Y=a=>cy-a*sc;
  let s=svgOpen('ELEVACIÓN DEL EMPALME',W,H,sc),top=g.d/2;
  for(const sg of [-1,1]){const x0=sg>0?g.gap/2:-half,x1=sg>0?half:-g.gap/2;
    s+=`<rect x="${X(x0)}" y="${Y(top-g.tf)}" width="${(x1-x0)*sc}" height="${(g.d-2*g.tf)*sc}" fill="var(--conc)" stroke="var(--ink)" stroke-width=".8" opacity=".8"/>`;
    s+=`<g fill="var(--steel)" stroke="var(--ink)"><rect x="${X(x0)}" y="${Y(top)}" width="${(x1-x0)*sc}" height="${g.tf*sc}"/><rect x="${X(x0)}" y="${Y(-top+g.tf)}" width="${(x1-x0)*sc}" height="${g.tf*sc}"/></g>`;
    // placas de alma
    const px0=sg>0?g.gap/2:-g.wxe,px1=sg>0?g.wxe:-g.gap/2;
    s+=`<rect x="${X(px0)}" y="${Y(g.hp/2)}" width="${(px1-px0)*sc}" height="${g.hp*sc}" fill="var(--grout)" stroke="var(--ink)" stroke-width=".9" opacity=".92"/>`;
    for(let c=0;c<g.nc;c++)for(let r=0;r<g.nr;r++)s+=`<circle cx="${X(sg*(g.wx1+c*g.sh))}" cy="${Y(((g.nr-1)/2-r)*g.sv)}" r="${Math.max(2.5,g.wdb/2*sc)}" fill="var(--bolt)"/>`;
  }
  // placas de ala exteriores (arriba y abajo) y pernos
  s+=`<g fill="var(--steelf)" stroke="var(--ink)" stroke-width="1.2"><rect x="${X(-g.xe)}" y="${Y(top+g.to)}" width="${2*g.xe*sc}" height="${g.to*sc}"/><rect x="${X(-g.xe)}" y="${Y(-top)}" width="${2*g.xe*sc}" height="${g.to*sc}"/></g>`;
  for(let k=0;k<g.n;k++)for(const sx of [-1,1])for(const sy of [1,-1]){
    const bx=X(sx*(g.x1+k*g.s)),y0=sy*(top+g.to),y1=sy*(top-g.tf-(g.inn?g.ti:0));
    s+=`<rect x="${bx-Math.max(1.5,g.db*sc/2)}" y="${Math.min(Y(y0),Y(y1))-2}" width="${Math.max(3,g.db*sc)}" height="${Math.abs(Y(y0)-Y(y1))+4}" fill="var(--tens)"/>`;}
  s+=dimH(X(-g.gap/2),X(g.gap/2),Y(-top-g.to)+14,`gap ${mm(g.gap)}`)+dimH(X(0),X(g.xe),Y(top+g.to)-12,`½ placa = ${mm(g.xe)}`);
  s+=dimV(X(-half)+4,Y(top),Y(-top),`d = ${mm(g.d)}`);
  return s+`<text class="dt" x="${W-8}" y="${H-6}" text-anchor="end">cotas [${uf('Ls').l}] · eje del empalme al centro</text></svg>`;
}
function vigaPlan(RES,S){
  const g=geoViga(RES,S),W=460,H=380,m=26,half=g.xe+20;
  const ext=Math.max(g.bo,g.bf);
  const sc=Math.min((W-2*m)/(2*half),(H-2*m-30)/ext),cx=W/2,cy=H/2,X=a=>cx+a*sc,Y=a=>cy-a*sc;
  let s=svgOpen('PLANTA — ALA SUPERIOR',W,H,sc);
  s+=`<rect x="${X(-half)}" y="${Y(g.bf/2)}" width="${(half-g.gap/2)*sc}" height="${g.bf*sc}" fill="var(--steel)" stroke="var(--ink)" opacity=".55"/><rect x="${X(g.gap/2)}" y="${Y(g.bf/2)}" width="${(half-g.gap/2)*sc}" height="${g.bf*sc}" fill="var(--steel)" stroke="var(--ink)" opacity=".55"/>`;
  s+=`<rect x="${X(-g.xe)}" y="${Y(g.bo/2)}" width="${2*g.xe*sc}" height="${g.bo*sc}" fill="var(--steelf)" stroke="var(--ink)" stroke-width="1.3" opacity=".9"/>`;
  if(g.inn)for(const sy of [-1,1])s+=`<rect x="${X(-g.xe)}" y="${Y(sy*(g.tw/2+2)+(sy>0?g.bi:0))}" width="${2*g.xe*sc}" height="${g.bi*sc}" fill="none" stroke="var(--mut)" stroke-dasharray="4 3"/>`;
  const rb=Math.max(3,g.db/2*sc);
  for(let k=0;k<g.n;k++)for(const sx of [-1,1])for(const sy of [-1,1])s+=`<circle cx="${X(sx*(g.x1+k*g.s))}" cy="${Y(sy*g.gg/2)}" r="${rb}" fill="var(--tens)" stroke="var(--card)"/>`;
  s+=dimH(X(g.gap/2),X(g.x1),Y(-g.bo/2)+16,`Leb ${mm(g.leb)}`)+dimH(X(g.x1),X(g.x1+g.s),Y(-g.bo/2)+30,`s ${mm(g.s)}`)+dimV(X(g.xe)+14,Y(g.bo/2),Y(-g.bo/2),`bo = ${mm(g.bo)}`)+dimV(X(g.xe)+30,Y(g.gg/2),Y(-g.gg/2),`g = ${mm(g.gg)}`);
  return s+`<text class="dt" x="${W-8}" y="${H-6}" text-anchor="end">cotas [${uf('Ls').l}]${g.inn?' · placas interiores (trazo)':''}</text></svg>`;
}

/* ───────────── Empalme de columna ───────────── */
function geoCol(RES,S){
  const D=RES.derivados,g={};
  g.du=D.cu_d_mm;g.bfu=D.cu_bf_mm;g.twu=D.cu_tw_mm;g.tfu=D.cu_tf_mm;g.dl=D.cl_d_mm;g.bfl=D.cl_bf_mm;g.twl=D.cl_tw_mm;g.tfl=D.cl_tf_mm;
  g.gap=S.gap;g.b=S.pf_b;g.t=S.pf_t;g.n=S.fa_n;g.s=S.fa_s;g.lec=S.fa_Lec;g.lep=S.fa_Lep;g.gg=S.fa_g;g.db=dia(S.fa_diam);
  g.fill=D.fill_t||0;g.tipo=S.tipo;
  g.x1=g.gap/2+g.lec;g.ye=g.x1+(g.n-1)*g.s+g.lep;
  g.pwb=S.pw_b;g.pwt=S.pw_t;g.nr=S.wa_nr;g.nc=S.wa_nc;g.sv=S.wa_sv;g.sh=S.wa_sh;g.wle=S.wa_Le;g.wdb=dia(S.wa_diam);
  g.wy1=g.gap/2+g.wle;g.wye=g.wy1+(g.nr-1)*g.sv+g.wle;
  return g;
}
function colElev(RES,S){
  const g=geoCol(RES,S),W=460,H=420,m=24,half=Math.max(g.ye,g.wye)+40,dmax=Math.max(g.du,g.dl);
  const sc=Math.min((W-2*m-20)/(dmax+2*(g.t+4)),(H-2*m)/(2*half)),cx=W/2,cy=H/2,X=a=>cx+a*sc,Y=a=>cy-a*sc;
  let s=svgOpen(g.tipo==='Placas apernadas'?'ELEVACIÓN DEL EMPALME':'ELEVACIÓN — EMPALME SOLDADO',W,H,sc);
  const col=(d,tf,tw,y0,y1)=>`<rect x="${X(-d/2)}" y="${Y(y1)}" width="${d*sc}" height="${(y1-y0)*sc}" fill="var(--conc)" opacity=".75" stroke="var(--ink)" stroke-width=".8"/><g fill="var(--steel)" stroke="var(--ink)"><rect x="${X(-d/2)}" y="${Y(y1)}" width="${tf*sc}" height="${(y1-y0)*sc}"/><rect x="${X(d/2-tf)}" y="${Y(y1)}" width="${tf*sc}" height="${(y1-y0)*sc}"/></g>`;
  s+=col(g.du,g.tfu,g.twu,g.gap/2,half)+col(g.dl,g.tfl,g.twl,-half,-g.gap/2);
  if(g.tipo==='Placas apernadas'){
    for(const sx of [-1,1]){const xo=sx*(g.du/2)+(sx>0?0:-g.t);
      s+=`<rect x="${X(sx>0?g.du/2:-g.du/2-g.t)}" y="${Y(g.ye)}" width="${g.t*sc}" height="${2*g.ye*sc}" fill="var(--steelf)" stroke="var(--ink)" stroke-width="1.2"/>`;}
    const wxo=Math.min(g.du,g.dl)/2-Math.max(g.tfu,g.tfl)-4;
    s+=`<rect x="${X(-g.pwb/2)}" y="${Y(g.wye)}" width="${g.pwb*sc}" height="${2*g.wye*sc}" fill="var(--grout)" stroke="var(--ink)" stroke-width=".9" opacity=".92"/>`;
    for(let r=0;r<g.nr;r++)for(const sy of [-1,1])for(let c=0;c<g.nc;c++)s+=`<circle cx="${X((c-(g.nc-1)/2)*g.sh)}" cy="${Y(sy*(g.wy1+r*g.sv))}" r="${Math.max(2.5,g.wdb/2*sc)}" fill="var(--bolt)"/>`;
    for(let k=0;k<g.n;k++)for(const sy of [-1,1])for(const sx of [-1,1]){
      const yy=sy*(g.x1+k*g.s),xa=sx>0?g.du/2-g.tfu:-g.du/2-g.t,xb=sx>0?g.du/2+g.t:-g.du/2+g.tfu,h=Math.max(3,g.db*sc);
      s+=`<rect x="${X(xa)}" y="${Y(yy)-h/2}" width="${(xb-xa)*sc}" height="${h}" fill="var(--tens)"/>`;}
    s+=dimV(X(g.du/2)+g.t*sc+14,Y(g.ye),Y(-g.ye),`placa = ${mm(2*g.ye)}`)+dimV(X(g.du/2)+g.t*sc+30,Y(g.gap/2+g.lec),Y(g.gap/2+g.lec+(g.n-1)*g.s),`${g.n-1}×s ${mm(g.s)}`);
  }else{
    s+=`<path d="M${X(-dmax/2)} ${Y(0)}H${X(dmax/2)}" stroke="var(--tens)" stroke-width="3"/><text class="dt" x="${X(0)}" y="${Y(0)-8}" text-anchor="middle" style="fill:var(--tens)">${esc(g.tipo)}</text>`;
  }
  s+=dimH(X(-g.du/2),X(g.du/2),Y(half)-4,`du = ${mm(g.du)}`)+dimH(X(-g.dl/2),X(g.dl/2),Y(-half)+16,`dl = ${mm(g.dl)}`);
  return s+`<text class="dt" x="${W-8}" y="${H-6}" text-anchor="end">cotas [${uf('Ls').l}] · gap ${mm(g.gap)}</text></svg>`;
}
function colSeccion(RES,S){
  const g=geoCol(RES,S),W=460,H=420,m=30,d=g.du,bf=g.bfu;
  const sc=Math.min((W-2*m)/(bf+2*g.t+40),(H-2*m)/(d+2*g.t+30)),cx=W/2,cy=H/2,X=a=>cx+a*sc,Y=a=>cy-a*sc;
  let s=svgOpen('SECCIÓN DE LA COLUMNA (superior)',W,H,sc);
  s+=`<g fill="var(--steel)" stroke="var(--ink)"><rect x="${X(-bf/2)}" y="${Y(d/2)}" width="${bf*sc}" height="${g.tfu*sc}"/><rect x="${X(-bf/2)}" y="${Y(-d/2+g.tfu)}" width="${bf*sc}" height="${g.tfu*sc}"/><rect x="${X(-g.twu/2)}" y="${Y(d/2-g.tfu)}" width="${g.twu*sc}" height="${(d-2*g.tfu)*sc}"/></g>`;
  if(g.tipo==='Placas apernadas'){
    s+=`<g fill="var(--steelf)" stroke="var(--ink)" stroke-width="1.2"><rect x="${X(-g.b/2)}" y="${Y(d/2+g.t)}" width="${g.b*sc}" height="${g.t*sc}"/><rect x="${X(-g.b/2)}" y="${Y(-d/2)}" width="${g.b*sc}" height="${g.t*sc}"/></g>`;
    for(const sy of [1,-1])for(const sx of [-1,1])s+=`<circle cx="${X(sx*g.gg/2)}" cy="${Y(sy*(d/2+g.t/2))}" r="${Math.max(3,g.db/2*sc)}" fill="var(--tens)" stroke="var(--card)"/>`;
    for(const sx of [-1,1])s+=`<rect x="${X(sx*(g.twu/2+g.pwt/2)-g.pwt/2)}" y="${Y(g.pwb/2)}" width="${g.pwt*sc}" height="${g.pwb*sc}" fill="var(--grout)" stroke="var(--ink)" stroke-width=".9"/>`;
    s+=dimH(X(-g.b/2),X(g.b/2),Y(-d/2-g.t)+16,`b = ${mm(g.b)}`)+dimH(X(-g.gg/2),X(g.gg/2),Y(-d/2-g.t)+30,`g = ${mm(g.gg)}`);
  }
  s+=dimV(X(bf/2)+14,Y(d/2),Y(-d/2),`d = ${mm(d)}`);
  return s+`<text class="dt" x="${W-8}" y="${H-6}" text-anchor="end">esquemático · cotas [${uf('Ls').l}]</text></svg>`;
}
const MODULO_EMPALME={
  viga:{id:'empalme_viga',api:'/api/empalme_viga',title:'Empalme de viga apernado — placas de ala y de alma',
    rebuild:['pf_in','junta','dist_M'],
    visible(f,S){const n=f.name;if(n==='pf_bi'||n==='pf_ti')return S.pf_in==='Sí';return true;},
    comboCols:[{sym:'Ff',label:'Ff ({u})',q:'F'}],
    svgs:[{id:'svgElev',fn:vigaElev},{id:'svgPlan',fn:vigaPlan}]},
  col:{id:'empalme_col',api:'/api/empalme_col',title:'Empalme de columna — apernado, PJP o CJP',
    rebuild:['tipo','junta','fresado','sismico'],
    visible(f,S){const n=f.name,ap=S.tipo==='Placas apernadas';
      if(['pf_acero','pf_b','pf_t','fa_grado','fa_diam','junta','fa_n','fa_g','fa_s','fa_Lec','fa_Lep','pw_acero','pw_b','pw_t','wa_grado','wa_diam','wa_nr','wa_nc','wa_sv','wa_sh','wa_Le'].includes(n))return ap;
      if(n==='sd_elec'||n==='E_f'||n==='E_w')return !ap;
      return true;},
    comboCols:[{sym:'T',label:'T ala ({u})',q:'F'},{sym:'C',label:'C ala ({u})',q:'F'}],
    svgs:[{id:'svgElev',fn:colElev},{id:'svgSec',fn:colSeccion}]},
};
