"use strict";
/* Configuración del módulo placa extrema (End Plate) — AISC DG4 / AISC 358-16 cap. 6 */
const SISM=S=>String(S.modo).startsWith('Sís');
const V=(RES,S)=>({...RES.vars,...S});
function dimH(x1,x2,y,txt){return `<path class="dim" d="M${x1} ${y-4}V${y+4}M${x2} ${y-4}V${y+4}M${x1} ${y}H${x2}"/><text class="dt" x="${(x1+x2)/2}" y="${y-5}" text-anchor="middle">${txt}</text>`;}
function dimV(x,y1,y2,txt){return `<path class="dim" d="M${x-4} ${y1}H${x+4}M${x-4} ${y2}H${x+4}M${x} ${y1}V${y2}"/><text class="dt" transform="translate(${x-6} ${(y1+y2)/2}) rotate(-90)" text-anchor="middle">${txt}</text>`;}
const Lm=v=>fmt(v*10,'Ls'); // v en cm → unidad de longitud de perfiles
function boltRows(v){ // posiciones y (cm, +arriba) de las filas de pernos respecto al centro de la viga
  const d=v.k_d,tf=v.k_tf,top=[];
  if(v.k_is8===1)top.push(d/2+v.k_pfo+v.k_pb,d/2+v.k_pfo,d/2-tf-v.k_pfi,d/2-tf-v.k_pfi-v.k_pb);
  else top.push(d/2+v.k_pfo,d/2-tf-v.k_pfi);
  return {top,all:[...top,...top.map(y=>-y)]};
}
function epFront(RES,S){
  const v=V(RES,S),W=420,H=420,m=44;
  const sc=Math.min((W-2*m)/Math.max(v.k_bp,v.k_bf+2),(H-2*m)/v.k_Hp);
  const cx=W/2,cy=H/2+6,X=a=>cx+a*sc,Y=a=>cy-a*sc;
  let s=`<svg data-sc="${sc}" data-f="10" viewBox="0 0 ${W} ${H}" role="img" aria-label="Vista frontal"><text x="8" y="16" style="font-weight:700">VISTA FRONTAL DE PLACA</text>`;
  s+=`<rect x="${X(-v.k_bp/2)}" y="${Y(v.k_Hp/2)}" width="${v.k_bp*sc}" height="${v.k_Hp*sc}" fill="var(--steelf)" stroke="var(--ink)" stroke-width="1.4"/>`;
  const d=v.k_d,tf=v.k_tf,bf=v.k_bf,tw=v.k_tw;
  s+=`<g fill="var(--steel)" stroke="var(--ink)" stroke-width="1" opacity=".85"><rect x="${X(-bf/2)}" y="${Y(d/2)}" width="${bf*sc}" height="${tf*sc}"/><rect x="${X(-bf/2)}" y="${Y(-d/2+tf)}" width="${bf*sc}" height="${tf*sc}"/><rect x="${X(-tw/2)}" y="${Y(d/2-tf)}" width="${tw*sc}" height="${(d-2*tf)*sc}"/></g>`;
  if(v.k_is4E!==1){const h=v.k_hst,ts=(v.st_t||10)/10;
    s+=`<g fill="var(--grout)" stroke="var(--ink)" stroke-width=".8"><rect x="${X(-ts/2)}" y="${Y(d/2+h)}" width="${ts*sc}" height="${h*sc}"/><rect x="${X(-ts/2)}" y="${Y(-d/2)}" width="${ts*sc}" height="${h*sc}"/></g>`;}
  const br=boltRows(v),rb=Math.max(3,v.k_db/2*sc);
  for(const y of br.all)for(const sx of [-1,1])s+=`<circle cx="${X(sx*v.k_g/2)}" cy="${Y(y)}" r="${rb}" fill="${y>0?'var(--tens)':'var(--bolt)'}" stroke="var(--card)" stroke-width="1"/>`;
  s+=`<text class="dt" x="${X(0)}" y="${Y(v.k_Hp/2)-6}" text-anchor="middle" style="fill:var(--tens)">filas superiores en tracción</text>`;
  const yb=Y(-v.k_Hp/2)+16;
  s+=dimH(X(-v.k_bp/2),X(v.k_bp/2),yb,`bp = ${Lm(v.k_bp)}`)+dimH(X(-v.k_g/2),X(v.k_g/2),yb+14,`g = ${Lm(v.k_g)}`);
  s+=dimV(X(-v.k_bp/2)-12,Y(v.k_Hp/2),Y(-v.k_Hp/2),`Hp = ${Lm(v.k_Hp)}`);
  s+=dimV(X(v.k_bp/2)+14,Y(br.top[0]),Y(br.top[0]-v.k_pfo),`pfo ${Lm(v.k_pfo)}`);
  return s+`<text class="dt" x="${W-8}" y="${H-6}" text-anchor="end">cotas [${uf('Ls').l}] · ${v.cfg}</text></svg>`;
}
function epSide(RES,S){
  const v=V(RES,S),W=420,H=420,m=36,d=v.k_d,tf=v.k_tf,tp=v.k_tp,Hp=v.k_Hp;
  const colH=Hp+14,beamL=d*1.15,tc=v.k_ctf;
  const sc=Math.min((W-2*m)/(beamL+tp+tc+8),(H-2*m)/colH);
  const xf=60,cy=H/2+4,Yc=a=>cy-a*sc;
  let s=`<svg data-sc="${sc}" data-f="10" viewBox="0 0 ${W} ${H}" role="img" aria-label="Elevación lateral"><text x="8" y="16" style="font-weight:700">ELEVACIÓN LATERAL</text>`;
  const X0=xf,Xc=X0-tc*sc;
  s+=`<rect x="${Xc}" y="${Yc(colH/2)}" width="${tc*sc}" height="${colH*sc}" fill="var(--steel)" stroke="var(--ink)" stroke-width="1.2"/>`;
  s+=`<path d="M${Xc} ${Yc(colH/2)}H${Xc-26}M${Xc} ${Yc(-colH/2)}H${Xc-26}" stroke="var(--mut)" stroke-dasharray="3 3"/>`;
  if(v.cp_usar==='Sí'){const t=v.cp_t/10;for(const y of [d/2-tf/2,-d/2+tf/2])s+=`<rect x="${Xc-26}" y="${Yc(y)-t*sc/2}" width="26" height="${Math.max(2,t*sc)}" fill="var(--grout)" stroke="var(--ink)" stroke-width=".8"/>`;}
  s+=`<rect x="${X0}" y="${Yc(Hp/2)}" width="${tp*sc}" height="${Hp*sc}" fill="var(--steelf)" stroke="var(--ink)" stroke-width="1.3"/>`;
  const xb=X0+tp*sc,Lx=beamL*sc;
  s+=`<rect x="${xb}" y="${Yc(d/2-tf)}" width="${Lx}" height="${(d-2*tf)*sc}" fill="var(--conc)" stroke="var(--ink)" stroke-width=".8" opacity=".7"/>`;
  s+=`<g fill="var(--steel)" stroke="var(--ink)" stroke-width="1"><rect x="${xb}" y="${Yc(d/2)}" width="${Lx}" height="${tf*sc}"/><rect x="${xb}" y="${Yc(-d/2+tf)}" width="${Lx}" height="${tf*sc}"/></g>`;
  if(v.k_is4E!==1){const h=v.k_hst,L=v.k_Lst;
    for(const sg of [1,-1])s+=`<polygon points="${xb},${Yc(sg*d/2)} ${xb},${Yc(sg*(d/2+h))} ${xb+L*sc},${Yc(sg*d/2)}" fill="var(--grout)" stroke="var(--ink)" stroke-width=".9"/>`;}
  const br=boltRows(v),bw=Math.max(2,v.k_db*sc*.8);
  for(const y of br.all){const col=y>0?'var(--tens)':'var(--bolt)';
    s+=`<rect x="${Xc-8}" y="${Yc(y)-bw/2}" width="${(tc+tp)*sc+16}" height="${bw}" fill="${col}"/><rect x="${Xc-12}" y="${Yc(y)-bw*.9}" width="5" height="${bw*1.8}" fill="${col}"/><rect x="${xb+3}" y="${Yc(y)-bw*.9}" width="5" height="${bw*1.8}" fill="${col}"/>`;}
  s+=dimV(xb+Lx+16,Yc(Hp/2),Yc(-Hp/2),`Hp = ${Lm(Hp)}`)+dimV(xb+Lx+34,Yc(d/2),Yc(-d/2),`d = ${Lm(d)}`);
  return s+`<text class="dt" x="${Xc-4}" y="${Yc(Hp/2)-6}" text-anchor="end">tp = ${Lm(tp)}</text></svg>`;
}
const MODULE={
  id:'end_plate', api:'/api/end_plate', title:'Placa extrema extendida (End Plate) — 4E · 4ES · 8ES',
  rebuild:['cfg','modo','cp_usar','dos_lados'],
  visible(f,S){const n=f.name;
    if(n==='cp_t'||n==='cp_b')return S.cp_usar==='Sí';
    if(n==='Mu_op')return S.dos_lados==='Sí';
    if(n==='pl_pb')return S.cfg==='8ES';
    if(n==='st_t'||n==='st_acero')return S.cfg!=='4E';
    if(n==='sis_L'||n==='sis_Vg')return SISM(S);
    if(n==='sd_wf')return !SISM(S);
    return true;},
  comboCols:[{sym:'db,req',label:'db,req ({u})',q:'Ls'},{sym:'Ffu',label:'Ffu ({u})',q:'F'}],
  comboNote:S=>SISM(S)?'<b style="color:var(--warn)">MODO SÍSMICO:</b> la tabla no se usa; la demanda es Mf y Vu por capacidad (resultado en la combinación 1).':'',
  comboHelp:'Se usa |Mu| y |Vu| en la cara de la columna. Las filas con cargas en cero se ignoran. En modo sísmico la demanda es Mf y Vu por capacidad (AISC 358-16 §6.8), con la luz L y Vgrav de la sección 7.',
  svgs:[{id:'svgFront',fn:epFront},{id:'svgSide',fn:epSide}],
};
