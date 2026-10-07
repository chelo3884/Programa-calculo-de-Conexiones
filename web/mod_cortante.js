"use strict";
/* Dibujos y configuración comunes de las conexiones a cortante (cortante_vv: viga–viga, cortante_vc: viga–columna) */
const dimH=(x1,x2,y,txt)=>`<path class="dim" d="M${x1} ${y-4}V${y+4}M${x2} ${y-4}V${y+4}M${x1} ${y}H${x2}"/><text class="dt" x="${(x1+x2)/2}" y="${y-5}" text-anchor="middle">${txt}</text>`;
const dimV=(x,y1,y2,txt)=>`<path class="dim" d="M${x-4} ${y1}H${x+4}M${x-4} ${y2}H${x+4}M${x} ${y1}V${y2}"/><text class="dt" transform="translate(${x-6} ${(y1+y2)/2}) rotate(-90)" text-anchor="middle">${txt}</text>`;
const mm=v=>fmt(v,'Ls'); // v en mm → unidad de longitud de perfiles
function cortGeom(RES,S,col){
  const D=RES.derivados,doble=S.tipo==='Doble ángulo apernado';
  const g={tipo:S.tipo,doble,n:S.n_b,s:S.pn_s,top:(RES.derivados&&RES.derivados.pn_top_ef!=null?RES.derivados.pn_top_ef:S.pn_top),lev:S.pn_Lev,set:S.setback||0,
    d:D.vg_d_mm,bf:D.vg_bf_mm,tw:D.vg_tw_mm,tf:D.vg_tf_mm,
    dc:(col?0:(S.destaje==='Sin destaje'?0:S.cope_dc)),c:(col?0:(S.destaje==='Sin destaje'?0:S.cope_c)),doble_destaje:S.destaje&&S.destaje.startsWith('Destaje doble'),
    tp:S.pl_tp,a:S.pl_a,leh:S.pl_Leh,lb:S.an_lb,ls:S.an_ls,t:S.an_t,gb:S.an_gb,gs:S.an_gs};
  if(col){g.sd=D.co_d_mm;g.sbf=D.co_bf_mm;g.stw=D.co_tw_mm;g.stf=D.co_tf_mm;}
  else{g.sd=D.vp_d_mm;g.sbf=D.vp_bf_mm;g.stw=D.vp_tw_mm;g.stf=D.vp_tf_mm;}
  g.dbolt=({'5/8"':15.9,'3/4"':19.05,'7/8"':22.2,'1"':25.4,'1-1/8"':28.6,'1-1/4"':31.8})[S.pn_diam]||19;
  g.dz=col?0:(S.vg_nivel==='Centrada'?(g.sd-g.d)/2:S.vg_nivel==='Desnivel manual'?(+S.vg_dz||0):0);
  g.xplate=doble?g.lb:g.a+g.leh; g.xbolt=doble?g.gb:g.a;
  g.L=2*g.lev+(g.n-1)*g.s;
  return g;
}
function cortElev(RES,S,col){
  const g=cortGeom(RES,S,col),W=440,H=420,m=34;
  const xend=Math.max(g.xplate*2.4,g.d*1.1)+g.set,top=g.d/2,sh=Math.min(g.sd,g.d*1.5);
  const ptop=top+g.dz,pbot=ptop-g.sd;                       // viga principal en sección: tope = tope de la soportada + dz
  const ymax=col?sh/2+10:Math.max(top,ptop)+10,ymin=col?-sh/2-10:Math.min(-top,pbot)-10;
  const sc=Math.min((W-2*m-90)/(xend+40),(H-2*m-10)/(ymax-ymin));
  const x0=m+78,cy=H/2+4+(ymax+ymin)/2*sc,X=a=>x0+a*sc,Y=a=>cy-a*sc;
  let s=`<svg data-sc="${sc}" data-f="1" viewBox="0 0 ${W} ${H}" role="img" aria-label="Elevación"><text x="8" y="16" style="font-weight:700">ELEVACIÓN</text>`;
  if(col){ // columna: ala vertical con el alma hacia atrás
    s+=`<rect x="${X(-g.stf)}" y="${Y(sh/2+10)}" width="${g.stf*sc}" height="${(sh+20)*sc}" fill="var(--steel)" stroke="var(--ink)" stroke-width="1.2"/>`;
    s+=`<text class="dt" x="${X(-g.stf)-4}" y="${Y(sh/2+10)+10}" text-anchor="end">ala de columna</text>`;
  }else{   // viga principal en sección (peralte real): alma (vertical) y alas
    s+=`<rect x="${X(-g.stw)}" y="${Y(ptop)}" width="${g.stw*sc}" height="${g.sd*sc}" fill="var(--steel)" stroke="var(--ink)" stroke-width="1.2"/>`;
    s+=`<rect x="${X(-g.sbf/2-g.stw/2)}" y="${Y(ptop)}" width="${g.sbf*sc}" height="${g.stf*sc}" fill="var(--steel)" stroke="var(--ink)" opacity=".7"/><rect x="${X(-g.sbf/2-g.stw/2)}" y="${Y(pbot+g.stf)}" width="${g.sbf*sc}" height="${g.stf*sc}" fill="var(--steel)" stroke="var(--ink)" opacity=".7"/>`;
    s+=`<text class="dt" x="${X(-g.stw)-4}" y="${Y(ptop)+10}" text-anchor="end">viga principal</text>`;
    if(Math.abs(g.dz)>0.5)s+=dimV(X(-g.sbf/2-g.stw/2)-12,Y(ptop),Y(top),`dz ${mm(g.dz)}`);
  }
  // viga soportada: alma + alas, con destaje
  const x1=g.set;
  s+=`<rect x="${X(x1)}" y="${Y(top-g.tf)}" width="${(xend-x1)*sc}" height="${(g.d-2*g.tf)*sc}" fill="var(--conc)" stroke="var(--ink)" stroke-width=".8" opacity=".8"/>`;
  s+=`<g fill="var(--steel)" stroke="var(--ink)" stroke-width="1"><rect x="${X(x1+g.c)}" y="${Y(top)}" width="${(xend-x1-g.c)*sc}" height="${g.tf*sc}"/><rect x="${X(x1+(g.doble_destaje?g.c:0))}" y="${Y(-top+g.tf)}" width="${(xend-x1-(g.doble_destaje?g.c:0))*sc}" height="${g.tf*sc}"/></g>`;
  if(g.c>0){ // zona rebajada
    s+=`<rect x="${X(x1)}" y="${Y(top-g.dc)}" width="${g.c*sc}" height="${g.dc*sc}" fill="var(--card)" stroke="var(--mut)" stroke-dasharray="3 2"/>`;
    s+=dimV(X(x1)-10,Y(top),Y(top-g.dc),`dc ${mm(g.dc)}`)+dimH(X(x1),X(x1+g.c),Y(top)-8,`c ${mm(g.c)}`);}
  // placa o ángulos
  const yb1=top-g.top,ytop=yb1+g.lev,ybot=yb1-(g.n-1)*g.s-g.lev;
  s+=`<rect x="${X(0)}" y="${Y(ytop)}" width="${g.xplate*sc}" height="${(ytop-ybot)*sc}" fill="var(--steelf)" stroke="var(--ink)" stroke-width="1.3" opacity=".92"/>`;
  const rb=Math.max(3,(g.doble?19:19)/2*sc);
  for(let k=0;k<g.n;k++)s+=`<circle cx="${X(g.xbolt)}" cy="${Y(yb1-k*g.s)}" r="${rb}" fill="var(--bolt)" stroke="var(--card)"/>`;
  if(g.doble)s+=`<text class="dt" x="${X(g.xplate/2)}" y="${Y(ytop)+13}" text-anchor="middle">2 ángulos</text>`;
  s+=dimV(X(g.xplate)+16,Y(ytop),Y(ybot),`L = ${mm(g.L)}`);
  if(g.n>1)s+=dimV(X(g.xbolt)+14,Y(yb1),Y(yb1-g.s),`s ${mm(g.s)}`);
  s+=dimH(X(0),X(g.xbolt),Y(ybot)+16,g.doble?`gb ${mm(g.xbolt)}`:`a ${mm(g.a)}`);
  s+=dimV(X(xend)+0,Y(top),Y(-top),`d = ${mm(g.d)}`);
  return s+`<text class="dt" x="${W-8}" y="${H-6}" text-anchor="end">cotas [${uf('Ls').l}] · ${esc(g.tipo)}</text></svg>`;
}
function cortPlan(RES,S,col){
  const g=cortGeom(RES,S,col),W=440,H=420,m=34;
  const xend=Math.max(g.xplate*(g.doble?2.6:1.7),120),ys=Math.max(g.sbf,2*g.lb+g.tw,180)/2;
  const sc=Math.min((W-2*m-70)/(xend+60),(H-2*m)/(2*ys+20)),x0=m+70+60*0,cy=H/2,X=a=>x0+a*sc,Y=a=>cy-a*sc;
  let s=`<svg data-sc="${sc}" data-f="1" viewBox="0 0 ${W} ${H}" role="img" aria-label="Planta"><text x="8" y="16" style="font-weight:700">PLANTA (corte bajo el ala)</text>`;
  const ts=col?g.stf:g.stw;
  s+=`<rect x="${X(-ts)}" y="${Y(ys)}" width="${ts*sc}" height="${2*ys*sc}" fill="var(--steel)" stroke="var(--ink)" stroke-width="1.2"/>`;
  if(col)s+=`<rect x="${X(-ts-60)}" y="${Y(g.stw/2)}" width="${60*sc}" height="${g.stw*sc}" fill="var(--steel)" stroke="var(--ink)" opacity=".5"/>`;
  else s+=`<g fill="var(--steel)" stroke="var(--ink)" opacity=".6"><rect x="${X(-ts-40)}" y="${Y(ys)}" width="${(ts+80)*sc}" height="${g.stf*sc}"/><rect x="${X(-ts-40)}" y="${Y(-ys+g.stf)}" width="${(ts+80)*sc}" height="${g.stf*sc}"/></g>`;
  const x1=g.set;
  s+=`<rect x="${X(x1)}" y="${Y(g.tw/2)}" width="${(xend-x1)*sc}" height="${g.tw*sc}" fill="var(--conc)" stroke="var(--ink)" stroke-width="1"/>`;
  s+=`<text class="dt" x="${X(xend)-4}" y="${Y(g.tw/2)-5}" text-anchor="end">alma de viga soportada</text>`;
  if(g.doble){ // dos ángulos, uno por cada cara del alma
    for(const sg of [1,-1]){
      s+=`<rect x="${X(0)}" y="${Y(sg>0?g.tw/2+g.t:-g.tw/2)}" width="${g.lb*sc}" height="${g.t*sc}" fill="var(--steelf)" stroke="var(--ink)" stroke-width="1.2"/>`;
      s+=`<rect x="${X(0)}" y="${Y(sg>0?g.tw/2+g.ls:-g.tw/2-g.t)}" width="${g.t*sc}" height="${(g.ls-g.tw/2)*sc}" fill="var(--steelf)" stroke="var(--ink)" stroke-width="1.2" transform="translate(0 0)"/>`;}
  }else{
    const ext=g.tipo==='Placa simple extendida',pt=Math.max(g.tp,5);
    // placa soldada al alma de la principal (x = 0), que SALE del alma hasta la línea de pernos y su borde Leh
    s+=`<rect x="${X(0)}" y="${Y(g.tw/2+pt)}" width="${g.xplate*sc}" height="${pt*sc}" fill="${ext?'var(--steel)':'var(--steelf)'}" stroke="var(--ink)" stroke-width="${ext?1.8:1.3}"/>`;
    s+=`<path d="M${X(0)} ${Y(g.tw/2+pt)}l${-7} ${-7}v${7}z M${X(0)} ${Y(g.tw/2)}l${-7} ${7}v${-7}z" fill="var(--tens)"/>`;
    // perno en sección: vástago, cabeza y tuerca
    const bxr=X(g.xbolt),yt=Y(g.tw/2+pt)-3,yb2=Y(-g.tw/2)+3,db=Math.max(g.dbolt||19,6)*sc;
    s+=`<rect x="${bxr-db/2}" y="${yt}" width="${db}" height="${yb2-yt}" fill="var(--bolt)"/>`;
    s+=`<rect x="${bxr-db}" y="${yt-4}" width="${2*db}" height="5" fill="var(--bolt)"/><rect x="${bxr-db}" y="${yb2}" width="${2*db}" height="5" fill="var(--bolt)"/>`;
    s+=`<text class="dt" x="${X(0)+4}" y="${Y(-g.tw/2)+34}">${ext?'placa extendida':'placa'} ${mm(g.xplate)} × tp ${mm(g.tp)}</text>`;
  }
  if(g.doble){const yb=g.tw/2+g.t;s+=`<rect x="${X(g.xbolt)-2}" y="${Y(yb+6)}" width="4" height="${(2*yb+12)*sc}" fill="var(--tens)"/>`;}
  s+=dimH(X(0),X(g.xbolt),Y(-ys)-4,g.doble?`gb ${mm(g.xbolt)}`:`a ${mm(g.a)}${g.tipo==='Placa simple extendida'?(g.a>89?' (extendida: a > 89)':' (a ≤ 89: convencional)'):''}`);
  if(!g.doble)s+=dimH(X(g.xbolt),X(g.xplate),Y(-ys)-18,`Leh ${mm(g.leh)}`);
  return s+`<text class="dt" x="${W-8}" y="${H-6}" text-anchor="end">esquemático · cotas [${uf('Ls').l}]</text></svg>`;
}
function cortanteModule(kind){
  const col=kind==='vc';
  return {
    id:col?'cortante_vc':'cortante_vv', api:'/api/'+(col?'cortante_vc':'cortante_vv'),
    title:col?'Conexión simple a cortante — viga al ala de columna':'Conexión simple a cortante — viga secundaria a viga principal',
    rebuild:['tipo','destaje','vg_nivel','pn_pos','co_perfil','vp_perfil'],
    visible(f,S){const n=f.name,t=S.tipo,doble=t==='Doble ángulo apernado';
      if(['pl_acero','pl_tp','pl_a','pl_Leh','sd_elec','pl_w'].includes(n))return !doble;
      if(['an_acero','an_lb','an_ls','an_t','an_gb','an_gs'].includes(n))return doble;
      if(n==='Ru_op')return doble;
      if(n==='cope_dc'||n==='cope_c')return S.destaje!=='Sin destaje';
      if(n==='vg_dz')return S.vg_nivel==='Desnivel manual';
      if(n==='pn_top'&&S.pn_pos&&S.pn_pos.startsWith('Autom'))return false;
      return true;},
    comboHelp:'',
    svgs:[{id:'svgElev',fn:(R,S)=>cortElev(R,S,col)},{id:'svgPlan',fn:(R,S)=>cortPlan(R,S,col)}],
  };
}
