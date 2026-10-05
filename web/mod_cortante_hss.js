"use strict";
/* Conexión a cortante — viga a columna HSS (placa simple o pasante). Reutiliza la elevación de mod_cortante.js */
function hssPlan(RES,S){
  S=Object.assign({tipo:'Placa simple convencional',destaje:'Sin destaje'},S);const g=cortGeom(RES,S,true),h=RES.vars.hss||{W:g.sbf,D:g.sd,t:g.stf,through:false},W=440,H=420,m=34;
  const xend=Math.max(g.xplate*2.6,120),ys=Math.max(h.W,180)/2;
  const sc=Math.min((W-2*m-70)/(xend+h.D+40),(H-2*m)/(2*ys+20)),x0=m+70+h.D*sc,cy=H/2,X=a=>x0+a*sc,Y=a=>cy-a*sc;
  let s=`<svg data-sc="${sc}" data-f="1" viewBox="0 0 ${W} ${H}" role="img" aria-label="Planta"><text x="8" y="16" style="font-weight:700">PLANTA (corte bajo el ala)</text>`;
  // HSS: rectángulo hueco (cara de conexión en x = 0, ancho W en y)
  s+=`<rect x="${X(-h.D)}" y="${Y(h.W/2)}" width="${h.D*sc}" height="${h.W*sc}" fill="var(--steel)" stroke="var(--ink)" stroke-width="1.2"/>`;
  s+=`<rect x="${X(-h.D+h.t)}" y="${Y(h.W/2-h.t)}" width="${(h.D-2*h.t)*sc}" height="${(h.W-2*h.t)*sc}" fill="var(--card)" stroke="var(--ink)" stroke-width=".8"/>`;
  s+=`<text class="dt" x="${X(-h.D/2)}" y="${Y(-h.W/2)+14}" text-anchor="middle">HSS ${fmt(h.W,'Ls')}×${fmt(h.D,'Ls')}×${fmt(h.t,'Ls')}</text>`;
  const x1=g.set,pt=Math.max(g.tp,3);
  s+=`<rect x="${X(x1)}" y="${Y(g.tw/2)}" width="${(xend-x1)*sc}" height="${g.tw*sc}" fill="var(--conc)" stroke="var(--ink)"/>`;
  s+=`<text class="dt" x="${X(xend)-4}" y="${Y(g.tw/2)-5}" text-anchor="end">alma de viga soportada</text>`;
  const px0=h.through?-h.D+h.t:0;
  s+=`<rect x="${X(px0)}" y="${Y(g.tw/2+pt)}" width="${(g.xplate-px0)*sc}" height="${pt*sc}" fill="var(--steelf)" stroke="var(--ink)" stroke-width="1.3"/>`;
  for(const xx of (h.through?[0,-h.D+h.t]:[0]))s+=`<path d="M${X(xx)} ${Y(g.tw/2+pt)}l${-6} ${-6}v${6}z" fill="var(--tens)"/>`;
  s+=`<rect x="${X(g.xbolt)-2}" y="${Y(g.tw/2+pt+6)}" width="4" height="${(2*pt+g.tw+12)*sc*0.6}" fill="var(--tens)"/>`;
  s+=dimH(X(0),X(g.xbolt),Y(-ys)-4,`a ${mm(g.a)}`)+dimH(X(-h.D),X(0),Y(-ys)-18,`D ${mm(h.D)}`);
  return s+`<text class="dt" x="${W-8}" y="${H-6}" text-anchor="end">${h.through?'placa pasante':'placa simple'} · esquemático · cotas [${uf('Ls').l}]</text></svg>`;
}
const MODULE={id:'cortante_hss',api:'/api/cortante_hss',title:'Conexión simple a cortante — viga a columna HSS',
  rebuild:['hss_perfil','hss_conex'],
  visible(f,S){const n=f.name,cat=S.hss_perfil!==ARMADO;
    if(n==='hss_cara')return cat;
    if(['hss_W','hss_D','hss_t'].includes(n))return !cat;
    return true;},
  comboHelp:'',
  svgs:[{id:'svgElev',fn:(R,S)=>cortElev(R,Object.assign({tipo:'Placa simple convencional',destaje:'Sin destaje'},S),true).replace('ala de columna','pared del HSS').replace('· undefined','· placa simple')},{id:'svgPlan',fn:hssPlan}]};
