"use strict";
/* Configuración del módulo rodilla / cumbrera de galpón con placa extrema — DG16 / DG4 / AISC 358-16 */
const V=(RES,S)=>({...RES.vars,...S});
function dimH(x1,x2,y,txt){return `<path class="dim" d="M${x1} ${y-4}V${y+4}M${x2} ${y-4}V${y+4}M${x1} ${y}H${x2}"/><text class="dt" x="${(x1+x2)/2}" y="${y-5}" text-anchor="middle">${txt}</text>`;}
function dimV(x,y1,y2,txt){return `<path class="dim" d="M${x-4} ${y1}H${x+4}M${x-4} ${y2}H${x+4}M${x} ${y1}V${y2}"/><text class="dt" transform="translate(${x-6} ${(y1+y2)/2}) rotate(-90)" text-anchor="middle">${txt}</text>`;}
const Lm=v=>fmt(v*10,'Ls');
// filas de pernos (y en cm respecto al centro de la viga) y borde de placa según la configuración de cada lado
function lado(cfg,sg,d,tf,pfo,pfi,pb,de){
  const ext=/Extendida/.test(cfg),dos=/2 filas/.test(cfg);
  const ys=[];let borde;
  if(ext){ys.push(d/2+pfo,d/2-tf-pfi);borde=d/2+pfo+de;}
  else{ys.push(d/2-tf-pfi);if(dos)ys.push(d/2-tf-pfi-pb);borde=d/2;}
  return {ys:ys.map(y=>sg*y),borde:sg*borde,ext};
}
function rodFront(RES,S){
  const v=V(RES,S),W=420,H=420,m=44;
  const d=v.b_d,tf=(S.vg_perfil==='ARMADO (flejes soldados)'?S.DIS_E21:RES.derivados.vg_tf_mm)/10,bf=v.b_bf,tw=v.b_tw;
  const up=lado(S.cfg_u,1,d,tf,v.p_pfo,v.p_pfi,v.p_pb,v.p_de),dn=lado(S.cfg_d,-1,d,tf,v.p_pfo,v.p_pfi,v.p_pb,v.p_de);
  const top=up.borde,bot=dn.borde,Hp=top-bot;
  const sc=Math.min((W-2*m)/Math.max(v.p_bp,bf+2),(H-2*m)/Hp),cx=W/2,cy=H/2+4+((top+bot)/2)*sc,X=a=>cx+a*sc,Y=a=>cy-a*sc;
  let s=`<svg data-sc="${sc}" data-f="10" viewBox="0 0 ${W} ${H}" role="img" aria-label="Vista frontal"><text x="8" y="16" style="font-weight:700">VISTA FRONTAL DE PLACA</text>`;
  s+=`<rect x="${X(-v.p_bp/2)}" y="${Y(top)}" width="${v.p_bp*sc}" height="${Hp*sc}" fill="var(--steelf)" stroke="var(--ink)" stroke-width="1.4"/>`;
  s+=`<g fill="var(--steel)" stroke="var(--ink)" stroke-width="1" opacity=".85"><rect x="${X(-bf/2)}" y="${Y(d/2)}" width="${bf*sc}" height="${tf*sc}"/><rect x="${X(-bf/2)}" y="${Y(-d/2+tf)}" width="${bf*sc}" height="${tf*sc}"/><rect x="${X(-tw/2)}" y="${Y(d/2-tf)}" width="${tw*sc}" height="${(d-2*tf)*sc}"/></g>`;
  const rb=Math.max(3,v.a_db/2*sc);
  for(const [L,col] of [[up,'var(--tens)'],[dn,'var(--bolt)']])for(const y of L.ys)for(const sx of [-1,1])s+=`<circle cx="${X(sx*v.p_g/2)}" cy="${Y(y)}" r="${rb}" fill="${col}" stroke="var(--card)"/>`;
  s+=dimH(X(-v.p_bp/2),X(v.p_bp/2),Y(bot)+16,`bp = ${Lm(v.p_bp)}`)+dimH(X(-v.p_g/2),X(v.p_g/2),Y(bot)+30,`g = ${Lm(v.p_g)}`);
  s+=dimV(X(-v.p_bp/2)-12,Y(top),Y(bot),`Hp = ${Lm(Hp)}`);
  s+=`<text class="dt" x="${X(0)}" y="${Y(top)-6}" text-anchor="middle">${esc(S.cfg_u)}</text><text class="dt" x="${X(0)}" y="${Y(bot)+58}" text-anchor="middle">${esc(S.cfg_d)}</text>`;
  return s+`<text class="dt" x="${W-8}" y="${H-6}" text-anchor="end">cotas [${uf('Ls').l}]</text></svg>`;
}
function rodEsquema(RES,S){
  const v=V(RES,S),W=440,H=420,th=(S.theta||0)*Math.PI/180,rod=String(S.tipo).startsWith('Rodilla');
  const d=v.b_d,Lh=(S.vg_Lh||1500)/10,dsin=v.b_d_perfil||0;
  const dBeam=(S.vg_perfil==='ARMADO (flejes soldados)'?S.DIS_E18:RES.derivados.vg_d_mm)/10;
  const L=Math.max(Lh*1.6,2.2*d),sc=Math.min((W-80)/(rod?L+30:2*L),(H-120)/(Math.max(L*Math.sin(th),0)+d+60));
  const ox=rod?90:W/2,oy=H-70;
  const col=`<rect x="${ox-(v.c_d)*sc}" y="${oy-(d+130)*sc}" width="${v.c_d*sc}" height="${(d+130)*sc+40}" fill="var(--steel)" stroke="var(--ink)" opacity=".8"/>`;
  const beam=(dir)=>{ // viga inclinada con cartela: de la placa (en el origen) hacia la derecha/izquierda
    const pts=(x,dd)=>[[x,0],[x,dd]];
    const Lc=Math.min(Lh,L),steps=[[0,d],[Lc,dBeam],[L,dBeam]];
    const top=steps.map(([x,dd])=>[dir*x*sc,-(dd/2)*sc]),bot=steps.map(([x,dd])=>[dir*x*sc,(dd/2)*sc]);
    const poly=[...top,...bot.reverse()].map(p=>p.join(',')).join(' ');
    return `<g transform="translate(${ox} ${oy-d/2*sc}) rotate(${-dir*S.theta})"><polygon points="${poly}" fill="var(--conc)" stroke="var(--ink)" stroke-width="1.2" opacity=".9"/><rect x="${-v.p_tp*sc*(dir>0?1:0)}" y="${-d/2*sc-(v.p_pfo||0)*sc*0}" width="${v.p_tp*sc}" height="${d*sc}" fill="var(--steelf)" stroke="var(--ink)" transform="translate(${dir<0?0:0} 0)"/></g>`;};
  let s=`<svg data-sc="${sc}" data-f="10" viewBox="0 0 ${W} ${H}" role="img" aria-label="Esquema"><text x="8" y="16" style="font-weight:700">ESQUEMA (${rod?'RODILLA':'CUMBRERA'}, θ = ${S.theta}°)</text>`;
  if(rod)s+=col;
  s+=beam(1);if(!rod)s+=beam(-1);
  s+=`<text class="dt" x="${ox+30}" y="${oy+60}">cartela: d = ${Lm(d)} → ${Lm(dBeam)} en ${Lm(Lh)} · esquemático</text></svg>`;
  return s;
}
const MODULE={
  id:'rodilla', api:'/api/rodilla', title:'Rodilla y cumbrera de galpón con placa extrema',
  rebuild:['tipo','cp_usar','cfg_u','cfg_d'],
  visible(f,S){const n=f.name;if(n==='cp_t'||n==='cp_b')return S.cp_usar==='Sí';
    if(n==='sd_wf'||n==='sd_ww')return true;return true;},
  comboCols:[{sym:'arriba',label:'Lado en tracción',q:'',text:v=>v===1?'superior':'inferior'}],
  comboHelp:'Mu (−) = tracción en el ala superior; Pu (+) = tracción. Momento reversible: cada lado usa su configuración. Las filas con cargas en cero se ignoran.',
  svgs:[{id:'svgFront',fn:rodFront},{id:'svgEsq',fn:rodEsquema}],
};
