"use strict";
/* Configuración del módulo BFP (Bolted Flange Plate) — AISC 358-16 cap. 7 */
const V=(RES,S)=>({...RES.vars,...S});
function dimH(x1,x2,y,txt){return `<path class="dim" d="M${x1} ${y-4}V${y+4}M${x2} ${y-4}V${y+4}M${x1} ${y}H${x2}"/><text class="dt" x="${(x1+x2)/2}" y="${y-5}" text-anchor="middle">${txt}</text>`;}
function dimV(x,y1,y2,txt){return `<path class="dim" d="M${x-4} ${y1}H${x+4}M${x-4} ${y2}H${x+4}M${x} ${y1}V${y2}"/><text class="dt" transform="translate(${x-6} ${(y1+y2)/2}) rotate(-90)" text-anchor="middle">${txt}</text>`;}
const Lm=v=>fmt(v*10,'Ls');
function bfpElev(RES,S){
  const v=V(RES,S),W=440,H=400,m=30;
  const d=v.b_d,tf=v.b_tf,tp=v.p_tp,Lp=v.p_Lp,tc=v.c_tf,sb=(v.setback||0)/10;
  const nr=v.p_nr,colH=d+2*tp+16,beamL=Lp+8;
  const sc=Math.min((W-2*m-60)/(beamL+tc),(H-2*m)/colH);
  const x0=m+40+tc*sc,cy=H/2+6,X=a=>x0+a*sc,Y=a=>cy-a*sc;
  let s=`<svg data-sc="${sc}" data-f="10" viewBox="0 0 ${W} ${H}" role="img" aria-label="Elevación BFP"><text x="8" y="16" style="font-weight:700">ELEVACIÓN</text>`;
  s+=`<rect x="${X(-tc)}" y="${Y(colH/2)}" width="${tc*sc}" height="${colH*sc}" fill="var(--steel)" stroke="var(--ink)" stroke-width="1.2"/><path d="M${X(-tc)} ${Y(colH/2)}H${X(-tc)-26}M${X(-tc)} ${Y(-colH/2)}H${X(-tc)-26}" stroke="var(--mut)" stroke-dasharray="3 3"/>`;
  // viga: alma sombreada + alas
  s+=`<rect x="${X(sb)}" y="${Y(d/2-tf)}" width="${(beamL-sb)*sc}" height="${(d-2*tf)*sc}" fill="var(--conc)" stroke="var(--ink)" stroke-width=".8" opacity=".7"/>`;
  s+=`<g fill="var(--steel)" stroke="var(--ink)" stroke-width="1"><rect x="${X(sb)}" y="${Y(d/2)}" width="${(beamL-sb)*sc}" height="${tf*sc}"/><rect x="${X(sb)}" y="${Y(-d/2+tf)}" width="${(beamL-sb)*sc}" height="${tf*sc}"/></g>`;
  // placas de ala (arriba y abajo) soldadas a la cara de la columna
  s+=`<g fill="var(--steelf)" stroke="var(--ink)" stroke-width="1.2"><rect x="${X(0)}" y="${Y(d/2+tp)}" width="${Lp*sc}" height="${tp*sc}"/><rect x="${X(0)}" y="${Y(-d/2)}" width="${Lp*sc}" height="${tp*sc}"/></g>`;
  // pernos
  const bw=Math.max(2,v.a_db*sc*.9);
  for(let k=0;k<nr;k++){const xb=v.p_S1+k*v.p_s;
    for(const sg of [1,-1]){const y0=sg*(d/2+tp),y1=sg*(d/2-tf);
      s+=`<rect x="${X(xb)-bw/2}" y="${Math.min(Y(y0),Y(y1))-3}" width="${bw}" height="${Math.abs(Y(y0)-Y(y1))+6}" fill="var(--tens)"/>`;}}
  // placa de alma
  const wn=v.w_n,wh=((wn-1)*(v.w_s||75)+2*(v.w_ev||40))/10;
  s+=`<rect x="${X(sb)}" y="${Y(wh/2)}" width="${11*sc}" height="${wh*sc}" fill="var(--grout)" stroke="var(--ink)" stroke-width=".9" opacity=".95"/>`;
  for(let k=0;k<wn;k++)s+=`<circle cx="${X(sb+6)}" cy="${Y(((wn-1)/2-k)*(v.w_s||75)/10)}" r="${Math.max(2.5,(v.a_db||2)*sc*.4)}" fill="var(--bolt)"/>`;
  // rótula plástica y cotas
  const Sh=v.s_Sh;
  if(Sh!=null)s+=`<path d="M${X(Sh)} ${Y(d/2+tp+3)}V${Y(-d/2-tp-3)}" stroke="var(--tens)" stroke-dasharray="5 3" stroke-width="1.2"/><text class="dt" x="${X(Sh)+4}" y="${Y(-d/2-tp-4)}" style="fill:var(--tens)">rótula Sh</text>`;
  s+=dimH(X(0),X(Lp),Y(d/2+tp)-14,`Lp = ${Lm(Lp)}`)+dimH(X(0),X(Sh||0),Y(-d/2-tp)+16,`Sh = ${Lm(Sh||0)}`);
  s+=dimV(X(Lp)+14,Y(d/2),Y(-d/2),`d = ${Lm(d)}`);
  return s+`<text class="dt" x="${W-8}" y="${H-6}" text-anchor="end">cotas [${uf('Ls').l}] · placa de alma esquemática</text></svg>`;
}
function bfpPlan(RES,S){
  const v=V(RES,S),W=440,H=400,m=36;
  const Lp=v.p_Lp,bp=v.p_b,bf=v.b_bf,cbf=v.c_bf,nr=v.p_nr,g=v.p_g;
  const sc=Math.min((W-2*m-30)/(Lp+6),(H-2*m)/Math.max(bp,cbf*.6));
  const x0=m+22,cy=H/2,X=a=>x0+a*sc,Y=a=>cy-a*sc;
  let s=`<svg data-sc="${sc}" data-f="10" viewBox="0 0 ${W} ${H}" role="img" aria-label="Planta BFP"><text x="8" y="16" style="font-weight:700">PLANTA — PLACA DE ALA SUPERIOR</text>`;
  s+=`<rect x="${X(-3)}" y="${Y(cbf*.6)}" width="${3*sc}" height="${cbf*1.2*.6*sc}" fill="var(--steel)" stroke="var(--ink)"/>`;
  s+=`<rect x="${X(0)}" y="${Y(bf/2)}" width="${(Lp+4)*sc}" height="${bf*sc}" fill="none" stroke="var(--mut)" stroke-dasharray="4 3"/>`;
  s+=`<rect x="${X(0)}" y="${Y(bp/2)}" width="${Lp*sc}" height="${bp*sc}" fill="var(--steelf)" stroke="var(--ink)" stroke-width="1.3"/>`;
  const rb=Math.max(3,v.a_db/2*sc);
  for(let k=0;k<nr;k++)for(const sx of [-1,1])s+=`<circle cx="${X(v.p_S1+k*v.p_s)}" cy="${Y(sx*g/2)}" r="${rb}" fill="var(--tens)" stroke="var(--card)"/>`;
  if(v.s_Sh!=null)s+=`<path d="M${X(v.s_Sh)} ${Y(bp/2+1.5)}V${Y(-bp/2-1.5)}" stroke="var(--tens)" stroke-dasharray="5 3" stroke-width="1.2"/>`;
  s+=dimH(X(0),X(v.p_S1),Y(-bp/2)+16,`S1 ${Lm(v.p_S1)}`)+dimH(X(v.p_S1),X(v.p_S1+v.p_s),Y(-bp/2)+30,`s ${Lm(v.p_s)}`)+dimH(X(v.p_S1+(nr-1)*v.p_s),X(Lp),Y(-bp/2)+16,`Le ${Lm(v.p_Le)}`);
  s+=dimV(X(Lp)+14,Y(bp/2),Y(-bp/2),`bp = ${Lm(bp)}`)+dimV(X(Lp)+30,Y(g/2),Y(-g/2),`g = ${Lm(g)}`);
  return s+`<text class="dt" x="${W-8}" y="${H-6}" text-anchor="end">cotas [${uf('Ls').l}] · ${v.n_b} pernos en el ala</text></svg>`;
}
const MODULE={
  id:'bfp', api:'/api/bfp', title:'Conexión BFP (Bolted Flange Plate) — AISC 358-16 cap. 7',
  rebuild:['cp_usar'],
  visible(f,S){const n=f.name;if(n==='cp_t'||n==='cp_b')return S.cp_usar==='Sí';return true;},
  svgs:[{id:'svgElev',fn:bfpElev},{id:'svgPlan',fn:bfpPlan}],
};
