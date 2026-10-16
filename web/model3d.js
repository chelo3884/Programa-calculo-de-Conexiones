"use strict";
/* Modelos 3D esquemáticos de cada tipo de conexión: MODEL3D[id](RES,S) → lista de sólidos (ver viewer3d.js).
   Se construyen con las mismas variables que los dibujos 2D. Ejes: x a lo largo de la viga, y transversal, z vertical. */
(function(){
const {C,box,lbox,prismXZ,prismXY,prismYZ,bolt,ibeam,tube,rot,flat}=S3;
const M=window.MODEL3D={};
const dia=s=>({'5/8"':15.875,'3/4"':19.05,'7/8"':22.225,'1"':25.4,'1-1/8"':28.575,'1-1/4"':31.75})[s]||20;
const V=(RES,S)=>({...RES.vars,...S});
const VV=RES=>{const v={...RES.vars},d=RES.derivados||{};if(v.btw==null&&d.vg_tw_mm!=null)v.btw=d.vg_tw_mm/10;return v;};  // btw (cm) si el motor no lo da
const weldBox=(x0,y0,z0,x1,y1,z1)=>box(x0,y0,z0,x1,y1,z1,C.weld,'Soldadura');
const NM={col:'Columna',vig:'Viga',pl:'Placa',pn:'Pernos',rig:'Rigidizadores'};
const I_=(axis,dd,d,bf,tw,tf,a0,a1,cu,cv,name)=>ibeam(axis,dd,d,bf,tw,tf,a0,a1,cu,cv,C.steel,name);
const beamX=(d,bf,tw,tf,x0,x1,zc,name)=>I_('x','v',d,bf,tw,tf,x0,x1,0,zc||0,name||NM.vig);                 // viga a lo largo de x (alas en z)
const colZ=(d,bf,tw,tf,z0,z1,xc,name)=>I_('z','u',d,bf,tw,tf,z0,z1,xc||0,0,name||NM.col);                    // columna a lo largo de z (peralte en x)

/* ───────── Placa extrema (End Plate) ───────── */
function boltRowsEP(v){const d=v.k_d,tf=v.k_tf,top=[];
  if(v.k_is8===1)top.push(d/2+v.k_pfo+v.k_pb,d/2+v.k_pfo,d/2-tf-v.k_pfi,d/2-tf-v.k_pfi-v.k_pb);else top.push(d/2+v.k_pfo,d/2-tf-v.k_pfi);
  return [...top,...top.map(y=>-y)];}
M.end_plate=(RES,S)=>{
  const v=V(RES,S),cd=v.k_cd,cbf=v.k_cbf,ctf=v.k_ctf,ctw=v.k_ctw,d=v.k_d,bf=v.k_bf,tf=v.k_tf,tw=v.k_tw,tp=v.k_tp,Hp=v.k_Hp,bp=v.k_bp,g=v.k_g,db=v.k_db;
  const xf=cd/2,colH=Hp+34,L=Math.max(d*1.6,45),o=[];
  o.push(colZ(cd,cbf,ctw,ctf,-colH/2,colH/2,0));
  o.push(lbox('x',xf,xf+tp,-bp/2,bp/2,-Hp/2,Hp/2,C.plate,NM.pl));
  o.push(beamX(d,bf,tw,tf,xf+tp,xf+tp+L,0));
  o.push(weldBox(xf+tp,-bf/2,d/2,xf+tp+0.7,bf/2,d/2+0.5),weldBox(xf+tp,-bf/2,-d/2-0.5,xf+tp+0.7,bf/2,-d/2));
  if(v.k_is4E!==1){const h=v.k_hst,Ls=v.k_Lst,ts=(v.st_t||10)/10,x0=xf+tp;
    for(const s of [1,-1])o.push(prismXZ([[x0,s*d/2],[x0,s*(d/2+h)],[x0+Ls,s*d/2]],-ts/2,ts/2,C.stiff,NM.rig));}
  if(v.cp_usar==='Sí'){const t=Math.max(v.cp_t/10,0.5);for(const z of [d/2-tf/2,-d/2+tf/2])for(const sy of [1,-1])
    o.push(lbox('z',z-t/2,z+t/2,-cd/2+ctf,cd/2-ctf,sy>0?ctw/2:-cbf/2,sy>0?cbf/2:-ctw/2,C.stiff,NM.rig));}
  const len=ctf+tp+1.5;
  for(const z of boltRowsEP(v))for(const sy of [-1,1])o.push(bolt('x',xf+(tp-ctf)/2,sy*g/2,z,db,len,C.bolt,NM.pn));
  return flat(o);
};

/* ───────── BFP ───────── */
M.bfp=(RES,S)=>{
  const v=V(RES,S),cd=v.c_d,cbf=v.c_bf,ctf=v.c_tf,ctw=v.c_tw,d=v.b_d,bf=v.b_bf,tf=v.b_tf,tw=v.b_tw,tp=v.p_tp,Lp=v.p_Lp,bp=v.p_b,sb=(v.setback||0)/10,o=[];
  const colH=d+2*tp+30,L=Lp+40;
  o.push(colZ(cd,cbf,ctw,ctf,-colH/2,colH/2,-cd/2));
  o.push(beamX(d,bf,tw,tf,sb,L,0));
  for(const s of [1,-1]){o.push(lbox('x',0,Lp,-bp/2,bp/2,s>0?d/2:-d/2-tp,s>0?d/2+tp:-d/2,C.plate,NM.pl));
    o.push(weldBox(-0.5,-bp/2,s>0?d/2:-d/2-tp,0,bp/2,s>0?d/2+tp:-d/2));
    for(let k=0;k<v.p_nr;k++)for(const sy of [-1,1])o.push(bolt('z',v.p_S1+k*v.p_s,sy*v.p_g/2,s*(d/2+tp/2-tf/2),v.a_db,tp+tf+1.2,C.bolt,NM.pn));}
  const wn=v.w_n,ws=(v.w_s||75)/10,wh=((wn-1)*ws+2*(v.w_ev||40)/10),wt=Math.max((v.w_t||10)/10,0.6);
  o.push(lbox('x',sb,sb+11,tw/2,tw/2+wt,-wh/2,wh/2,C.plate,NM.pl));
  for(let k=0;k<wn;k++)o.push(bolt('y',sb+6,wt/2,((wn-1)/2-k)*ws,v.a_db,tw+wt+1,C.bolt,NM.pn));
  return flat(o);
};

/* ───────── WUF (alas soldadas + placa simple de alma) ───────── */
M.wuf=(RES,S)=>{
  const v=RES.vars,o=[],cd=v.cd,cbf=v.cbf,ctf=v.ctf,ctw=v.ctw,bd=v.bd,L=Math.max(bd*1.5,v.L+30);
  o.push(colZ(cd,cbf,ctw,ctf,-bd/2-32,bd/2+32,-cd/2));
  o.push(beamX(bd,v.bbf,v.btw,v.btf,0.0,L,0));
  for(const s of [1,-1])o.push(weldBox(-0.6,-v.bbf/2,s>0?bd/2-v.btf:-bd/2,0,v.bbf/2,s>0?bd/2:-bd/2+v.btf));
  o.push(lbox('x',0,v.leh+6,v.btw/2,v.btw/2+v.tp,-v.L/2,v.L/2,C.plate,NM.pl));
  for(let k=0;k<v.n;k++)o.push(bolt('y',6,v.tp/2,((v.n-1)/2-k)*v.s,v.db,v.btw+v.tp+1,C.bolt,NM.pn));
  if(v.cp)for(const z of [bd/2-v.btf/2,-bd/2+v.btf/2])for(const sy of [1,-1])
    o.push(lbox('z',z-v.cp_t/2,z+v.cp_t/2,-cd+ctf,-ctf,sy>0?ctw/2:-cbf/2,sy>0?cbf/2:-ctw/2,C.stiff,NM.rig));
  return flat(o);
};

/* ───────── Rodilla / cumbrera de galpón (esquemático) ───────── */
function ladoR(cfg,sg,d,tf,pfo,pfi,pb,de){const ext=/Extendida/.test(cfg),dos=/2 filas/.test(cfg),ys=[];let borde;
  if(ext){ys.push(d/2+pfo,d/2-tf-pfi);borde=d/2+pfo+de;}else{ys.push(d/2-tf-pfi);if(dos)ys.push(d/2-tf-pfi-pb);borde=d/2;}
  return {ys:ys.map(y=>sg*y),borde:sg*borde};}
M.rodilla=(RES,S)=>{
  const v=V(RES,S),d=v.b_d,D=RES.derivados,tf=D.vg_tf_mm/10,dB=D.vg_d_mm/10,bf=v.b_bf,tw=v.b_tw,tp=v.p_tp,bp=v.p_bp,th=S.theta||0,rod=String(S.tipo).startsWith('Rodilla');
  const up=ladoR(S.cfg_u,1,d,tf,v.p_pfo,v.p_pfi,v.p_pb,v.p_de),dn=ladoR(S.cfg_d,-1,d,tf,v.p_pfo,v.p_pfi,v.p_pb,v.p_de);
  const Lh=(S.vg_Lh||1500)/10,Lb=Math.max(Lh*1.5,d*2.5),o=[];
  const rafter=(dir)=>{ // viga con cartela (d → dB en Lh), placa y pernos; se gira θ alrededor de y
    const g=[];
    g.push(lbox('x',0,tp,-bp/2,bp/2,dn.borde,up.borde,C.plate,NM.pl));
    const x0=tp,x1=tp+Lh;      // cartela (haunch): el peralte pasa de d a dB en Lh
    for(const sg of [1,-1])g.push(prismXZ([[x0,sg*d/2],[x1,sg*dB/2],[x1,sg*(dB/2-tf)],[x0,sg*(d/2-tf)]],-bf/2,bf/2,C.steel,NM.vig));
    g.push(prismXZ([[x0,-d/2+tf],[x1,-dB/2+tf],[x1,dB/2-tf],[x0,d/2-tf]],-tw/2,tw/2,C.web,NM.vig));
    g.push(I_('x','v',dB,bf,tw,tf,tp+Lh,tp+Lb,0,0,NM.vig));
    for(const [Lx,ys] of [[up,up.ys],[dn,dn.ys]])for(const z of ys)for(const sy of [-1,1])g.push(bolt('x',tp/2-0.5,sy*v.p_g/2,z,v.a_db,tp+v.c_tf+1.5,C.bolt,NM.pn));
    if(dir<0)for(const s of g.flat(Infinity))s.verts=s.verts.map(([x,y,z])=>[-x,y,z]);
    rot(flat(g),'y',-dir*th,[0,0,0]);return g;};
  if(rod){o.push(colZ(v.c_d,v.c_bf,v.c_tw,v.c_tf,-d*1.8,d*1.8+Lh*Math.sin(th*Math.PI/180)*0.5,-v.c_d/2));
    o.push(rafter(1));}
  else{o.push(rafter(1),rafter(-1));}
  return flat(o);
};

/* ───────── Empalme de viga (mm) ───────── */
M.empalme_viga=(RES,S)=>{
  const g=geoViga(RES,S),o=[],half=Math.max(g.xe,g.wxe)+90;
  for(const sg of [-1,1])o.push(beamX(g.d,g.bf,g.tw,g.tf,sg>0?g.gap/2:-half,sg>0?half:-g.gap/2,0));
  for(const s of [1,-1]){
    o.push(lbox('x',-g.xe,g.xe,-g.bo/2,g.bo/2,s>0?g.d/2:-g.d/2-g.to,s>0?g.d/2+g.to:-g.d/2,C.plate,'Placas de ala'));
    if(g.inn)for(const sy of [-1,1])o.push(lbox('x',-g.xe,g.xe,sy>0?g.tw/2+2:-g.tw/2-2-g.bi,sy>0?g.tw/2+2+g.bi:-g.tw/2-2,s>0?g.d/2-g.tf-g.ti:-g.d/2+g.tf,s>0?g.d/2-g.tf:-g.d/2+g.tf+g.ti,C.plate,'Placas de ala'));
    for(let k=0;k<g.n;k++)for(const sx of [-1,1])for(const sy of [-1,1])
      o.push(bolt('z',sx*(g.x1+k*g.s),sy*g.gg/2,s*(g.d/2+(g.to-g.tf-(g.inn?g.ti:0))/2),g.db,g.to+g.tf+(g.inn?g.ti:0)+2,C.bolt,NM.pn));}
  for(const sy of [-1,1])o.push(lbox('x',-g.wxe,g.wxe,sy>0?g.tw/2:-g.tw/2-g.tp,sy>0?g.tw/2+g.tp:-g.tw/2,-g.hp/2,g.hp/2,C.stiff,'Placas de alma'));
  for(const sx of [-1,1])for(let c=0;c<g.nc;c++)for(let r=0;r<g.nr;r++)o.push(bolt('y',sx*(g.wx1+c*g.sh),0,((g.nr-1)/2-r)*g.sv,g.wdb,g.tw+2*g.tp+2,C.bolt,NM.pn));
  return flat(o);
};

/* ───────── Empalme de columna (mm) ───────── */
M.empalme_col=(RES,S)=>{
  const g=geoCol(RES,S),o=[],half=Math.max(g.ye,g.wye)+90,ap=g.tipo==='Placas apernadas',gp=ap?g.gap/2:Math.max(g.gap/2,3);
  o.push(colZ(g.du,g.bfu,g.twu,g.tfu,gp,half,0),colZ(g.dl,g.bfl,g.twl,g.tfl,-half,-gp,0));
  if(!ap){o.push(I_('z','u',Math.max(g.du,g.dl),Math.max(g.bfu,g.bfl),Math.min(g.twu,g.twl),Math.min(g.tfu,g.tfl),-gp,gp,0,0,'Soldadura'));for(const s of flat(o).filter(x=>x.name==='Soldadura'))s.color=C.weld;return flat(o);}
  for(const sx of [-1,1]){const x0=sx>0?g.du/2:-g.du/2-g.t,x1=sx>0?g.du/2+g.t:-g.du/2;
    o.push(lbox('z',-g.ye,g.ye,x0,x1,-g.b/2,g.b/2,C.plate,'Placas de ala'));
    for(let k=0;k<g.n;k++)for(const sy of [-1,1])for(const sz of [-1,1])o.push(bolt('x',sx*(g.du/2-g.tfu/2+g.t/2),sy*g.gg/2,sz*(g.x1+k*g.s),g.db,g.t+g.tfu+2,C.bolt,NM.pn));}
  for(const sy of [-1,1])o.push(lbox('z',-g.wye,g.wye,-g.pwb/2,g.pwb/2,sy>0?g.twu/2:-g.twu/2-g.pwt,sy>0?g.twu/2+g.pwt:-g.twu/2,C.stiff,'Placas de alma'));
  for(let c=0;c<g.nc;c++)for(let r=0;r<g.nr;r++)for(const sz of [-1,1])o.push(bolt('y',(c-(g.nc-1)/2)*g.sh,0,sz*(g.wy1+r*g.sv),g.wdb,g.twu+2*g.pwt+2,C.bolt,NM.pn));
  return flat(o);
};

/* ───────── Cartela de arriostramiento (cm) ───────── */
M.gusset=(RES,S)=>{
  const v=RES.vars,o=[],a=v.a,b=v.b,t=v.t,th=v.th*Math.PI/180,L=Math.max(a,b)*1.4;
  o.push(colZ(v.cd,v.cbf,v.ctw,v.ctf,-v.bd-40,b+40,-v.cd/2));
  o.push(beamX(v.bd,v.bbf,v.btw,v.btf,0,a+30,-v.bd/2));
  o.push(prismXZ([[0,0],[a,0],[a,Math.min(b*0.15,6)],[Math.min(a*0.15,6),b],[0,b]],-t/2,t/2,C.plate,'Cartela'));
  const px=a*0.62,py=b*0.62,dx=Math.cos(th),dz=Math.sin(th),w=9,ex=px+dx*L,ez=py+dz*L,nx=-dz*w/2,nz=dx*w/2;
  for(const s of [1,-1])o.push(prismXZ([[px-nx,py-nz],[px+nx,py+nz],[ex+nx,ez+nz],[ex-nx,ez-nz]],s>0?t/2:-t/2-1.2,s>0?t/2+1.2:-t/2,C.diag,'Diagonal'));
  for(let r=0;r<v.nl;r++)for(let k=0;k<v.n;k++){const off=(r-(v.nl-1)/2)*v.g,al=-k*v.s;
    o.push(bolt('y',px+dx*al-dz*off,0,py+dz*al+dx*off,v.db,t+2.4+1.5,C.bolt,NM.pn));}
  o.push(weldBox(-0.1,-t/2-0.4,0,2,t/2+0.4,0.8));
  return flat(o);
};

/* ───────── Cortante: viga secundaria–principal / columna / HSS (mm) ───────── */
function cortante3d(RES,S,col,hssMode){
  const g=cortGeom(RES,S,col),o=[],top=g.d/2,dbm=g.dbolt||19,Lb=Math.max(g.xplate*1.8,g.d*1.3)+g.set;
  const hss=hssMode&&RES.vars.hss;
  // soporte
  const ptop=top+g.dz,pbot=ptop-g.sd;
  if(hss){const D=hss.D,Wd=hss.W,t=hss.t;o.push(tube('z',D,Wd,t,-g.sd*0.8-60,g.sd*0.8+60,-D/2,0,C.steel,'Columna HSS'));}
  else if(col)o.push(colZ(g.sd,g.sbf,g.stw,g.stf,-g.d/2-120,g.d/2+120,-g.sd/2));
  else o.push(I_('y','u',g.sd,g.sbf,g.stw,g.stf,-Math.max(g.sbf*1.2,160),Math.max(g.sbf*1.2,160),(ptop+pbot)/2,-g.stw/2,'Viga principal'));
  // viga soportada con destaje superior (y doble)
  const x0=g.set,xe=x0+Lb,tf=g.tf,tw=g.tw,dc=g.dc,c=g.c,fl=(z0,z1,xs)=>lbox('x',xs,xe,-g.bf/2,g.bf/2,z0,z1,C.steel,'Viga');
  o.push(fl(top-tf,top,x0+(c>0?c:0)),fl(-top,-top+tf,x0+(c>0&&g.doble_destaje?c:0)));
  const zt=c>0?Math.min(top-tf,top-dc):top-tf;
  if(c>0&&zt<top-tf)o.push(prismXZ([[x0,-top+tf],[xe,-top+tf],[xe,top-tf],[x0+c,top-tf],[x0+c,zt],[x0,zt]],-tw/2,tw/2,C.web,'Viga'));
  else o.push(lbox('x',x0,xe,-tw/2,tw/2,-top+tf,top-tf,C.web,'Viga'));
  // placa o ángulos
  const yb1=top-g.top,ytop=yb1+g.lev,ybot=yb1-(g.n-1)*g.s-g.lev;
  const T=!g.doble&&g.tipo==='Placa simple extendida'&&(!hssMode)&&!col,xs=Math.max(g.set-10,0),yst=ptop-g.stf-2,ysb=pbot+g.stf+2;
  if(g.doble){
    for(const sg of [1,-1]){
      o.push(lbox('x',0,g.lb,sg>0?tw/2:-tw/2-g.t,sg>0?tw/2+g.t:-tw/2,ybot,ytop,C.plate,'Ángulos'));
      o.push(lbox('x',0,g.t,sg>0?tw/2:-g.ls,sg>0?g.ls:-tw/2,ybot,ytop,C.plate,'Ángulos'));
    }
    for(let k=0;k<g.n;k++)o.push(bolt('y',g.gb,0,yb1-k*g.s,dbm,tw+2*g.t+2,C.bolt,'Pernos'));
  }else{
    if(T&&xs>0&&ysb<ybot&&yst>ytop){
      o.push(prismXZ([[0,yst],[xs,yst],[xs,ytop],[g.xplate,ytop],[g.xplate,ybot],[xs,ybot],[xs,ysb],[0,ysb]],tw/2,tw/2+g.tp,C.plate,'Placa'));
      o.push(weldBox(0,tw/2,ysb,3,tw/2+g.tp,ysb+3),weldBox(0,tw/2,yst-3,3,tw/2+g.tp,yst));
    }else o.push(lbox('x',0,g.xplate,tw/2,tw/2+g.tp,ybot,ytop,C.plate,'Placa'));
    if(!hss||hss)o.push(weldBox(-1,tw/2,ybot,2.5,tw/2+g.tp+3,ytop));
    for(let k=0;k<g.n;k++)o.push(bolt('y',g.xbolt,g.tp/2,yb1-k*g.s,dbm,tw+g.tp+2,C.bolt,'Pernos'));
  }
  return flat(o);
}
M.cortante_vv=(RES,S)=>cortante3d(RES,Object.assign({tipo:'Placa simple convencional',destaje:'Sin destaje'},S),false,false);
M.cortante_vc=(RES,S)=>cortante3d(RES,Object.assign({tipo:'Placa simple convencional',destaje:'Sin destaje'},S),true,false);
M.cortante_hss=(RES,S)=>{
  const h=RES.vars.hss||{},S2=Object.assign({tipo:'Placa simple convencional',destaje:'Sin destaje'},S);
  const o=cortante3d(RES,S2,true,true);
  if(h.through){const g=cortGeom(RES,S2,true),yb1=g.d/2-g.top,ytop=yb1+g.lev,ybot=yb1-(g.n-1)*g.s-g.lev;
    o.push(lbox('x',-h.D,0,g.tw/2,g.tw/2+g.tp,ybot,ytop,C.plate,'Placa pasante'));}
  return o;
};

/* ───────── Columnas HSS (cm) ───────── */
M.hss_directa=(RES,S)=>{
  const v=VV(RES),o=[],D=v.D,W=v.W,t=v.t,L=Math.max(v.bd*1.5,45);
  o.push(tube('z',D,W,t,-v.bd/2-40,v.bd/2+40,0,0,C.steel,'Columna HSS'));
  o.push(beamX(v.bd,v.bbf,v.btw,v.btf,D/2+0.3,D/2+L,0));
  for(const s of [1,-1])o.push(weldBox(D/2-0.1,-v.bbf/2,s>0?v.bd/2-v.btf:-v.bd/2,D/2+0.5,v.bbf/2,s>0?v.bd/2:-v.bd/2+v.btf));
  o.push(lbox('x',D/2,D/2+v.a+v.leh,v.btw/2,v.btw/2+v.tp,-v.L/2,v.L/2,C.plate,'Placa de corte'));
  for(let k=0;k<v.n;k++)o.push(bolt('y',D/2+v.a,v.tp/2,((v.n-1)/2-k)*v.s,v.db,v.btw+v.tp+1,C.bolt,NM.pn));
  return flat(o);
};
M.hss_pasante=(RES,S)=>{
  const v=VV(RES),o=[],D=v.D,W=v.W,t=v.t,half=Math.min(v.L/2,110);
  o.push(tube('z',D,W,t,-v.bd/2-45,v.bd/2+45,0,0,C.steel,'Columna HSS'));
  for(const sg of [1,-1])o.push(beamX(v.bd,v.bbf,v.btw,v.btf,sg>0?D/2:-half,sg>0?half:-D/2,0));
  for(const s of [1,-1]){o.push(lbox('x',-half,half,-v.bp/2,v.bp/2,s>0?v.bd/2:-v.bd/2-v.tp,s>0?v.bd/2+v.tp:-v.bd/2,C.plate,'Placa pasante'));
    for(const sg of [1,-1])for(let r=0;r<v.nb;r++)for(const sy of [-1,1])
      o.push(bolt('z',sg*(D/2+v.a+r*v.s),sy*v.g/2,s*(v.bd/2+v.tp/2-v.btf/2),v.db,v.tp+v.btf+1.5,C.bolt,NM.pn));}
  return flat(o);
};
M.hss_diafragma=(RES,S)=>{
  const v=VV(RES),o=[],D=v.D,W=v.W,t=v.t,xr=Math.min(v.L/2,100),we=Math.max(v.w1,v.bbf+2),hc=W/2+v.ws,a=D/2+v.d1*0.6;
  const pts=[[-xr,we/2],[-a,hc],[a,hc],[xr,we/2],[xr,-we/2],[a,-hc],[-a,-hc],[-xr,-we/2]];
  o.push(tube('z',D,W,t,-v.bd/2-v.tp-30,v.bd/2+v.tp+30,0,0,C.steel,'Columna HSS'));
  for(const sg of [1,-1])o.push(beamX(v.bd,v.bbf,v.btw,v.btf,sg>0?D/2:-xr,sg>0?xr:-D/2,0));
  for(const s of [1,-1]){o.push(prismXY(pts,s>0?v.bd/2:-v.bd/2-v.tp,s>0?v.bd/2+v.tp:-v.bd/2,C.plate,'Placa de recorte'));
    for(const sg of [1,-1])for(let r=0;r<v.nb;r++)for(const sy of [-1,1])
      o.push(bolt('z',sg*(D/2+v.d1+r*v.s),sy*v.g/2,s*(v.bd/2+v.tp/2-v.btf/2),v.db,v.tp+v.btf+1.5,C.bolt,NM.pn));}
  return flat(o);
};
M.hss_dext=(RES,S)=>{
  const v=VV(RES),o=[],W=v.W,xe=W/2+v.Ln,y1=W/2+v.hd,tn=Math.tan(v.th*Math.PI/180),xs=Math.max(W/2,xe-(y1-v.bbf/2)/tn);
  const pts=[[-xe,v.bbf/2],[-xs,y1],[xs,y1],[xe,v.bbf/2],[xe,-v.bbf/2],[xs,-y1],[-xs,-y1],[-xe,-v.bbf/2]];
  o.push(tube('z',W,W,v.t,-v.bd/2-v.td-25,v.bd/2+v.td+25,0,0,C.steel,'Columna RHS'));
  for(const sg of [1,-1])o.push(beamX(v.bd,v.bbf,v.btw,v.btf,sg>0?W/2:-xe-45,sg>0?xe+45:-W/2,0));
  for(const s of [1,-1])o.push(prismXY(pts,s>0?v.bd/2:-v.bd/2-v.td,s>0?v.bd/2+v.td:-v.bd/2,C.plate,'Diafragmas externos'));
  return flat(o);
};
M.hss_placalong=(RES,S)=>{
  const v=RES.vars,o=[],th=v.th*Math.PI/180,hpl=v.hp/Math.sin(th),Lx=Math.max(v.hp*1.6,25),x0=v.bc/2;
  o.push(tube('z',v.bc,v.hc,v.tc,-hpl*0.9-20,hpl*0.9+20,0,0,C.steel,'Columna RHS'));
  o.push(lbox('x',x0,x0+Lx,-v.bp/2,v.bp/2,-hpl/2,hpl/2,C.plate,'Placa'));
  if(v.mult===2)o.push(lbox('x',-x0-Lx,-x0,-v.bp/2,v.bp/2,-hpl/2,hpl/2,C.plate,'Placa'));
  for(let k=0;k<v.nb;k++)o.push(bolt('y',x0+Lx*0.55,0,((v.nb-1)/2-k)*v.s,v.db,v.bp+1.5,C.bolt,NM.pn));
  o.push(weldBox(x0-0.1,-v.bp/2-0.5,-hpl/2,x0+0.6,v.bp/2+0.5,hpl/2));
  return flat(o);
};
M.hss_placasimple=(RES,S)=>{
  const v=VV(RES),o=[],D=v.D,t=v.t,L=Math.max(v.bd*1.5,45),a=v.a;
  o.push(tube('z',D,v.W,t,-v.bd/2-45,v.bd/2+45,0,0,C.steel,'Columna RHS'));
  o.push(lbox('x',D/2,D/2+a+v.leh,v.btw/2,v.btw/2+v.tp,-v.L/2,v.L/2,C.plate,'Placa simple'));
  o.push(weldBox(D/2-0.1,v.btw/2,-v.L/2,D/2+0.5,v.btw/2+v.tp+0.5,v.L/2));
  o.push(beamX(v.bd,v.bbf,v.btw,v.btf,D/2+1,D/2+L,0));
  for(let k=0;k<v.n;k++)o.push(bolt('y',D/2+a,v.tp/2,((v.n-1)/2-k)*v.s,v.db,v.btw+v.tp+1,C.bolt,NM.pn));
  return flat(o);
};
M.empalme_rhs=(RES,S)=>{
  const v=RES.vars,o=[],Hc=Math.max(v.B,v.H)*1.1,pos=(Ln,n)=>Array.from({length:n},(_,i)=>-Ln/2+(i+0.5)*Ln/n);
  o.push(tube('z',v.W,v.D,v.t,v.tp,v.tp+Hc,0,0,C.steel,'Columna RHS'),tube('z',v.W,v.D,v.t,-v.tp-Hc,-v.tp,0,0,C.steel,'Columna RHS'));
  o.push(lbox('z',0,v.tp,-v.B/2,v.B/2,-v.H/2,v.H/2,C.plate,'Placas de extremo'),lbox('z',-v.tp,0,-v.B/2,v.B/2,-v.H/2,v.H/2,C.plate,'Placas de extremo'));
  for(const sz of [1,-1])o.push(tube('z',v.W+1.6,v.D+1.6,0.8,sz>0?v.tp:-v.tp-0.8,sz>0?v.tp+0.8:-v.tp,0,0,C.weld,'Soldadura'));
  for(const s of [1,-1]){for(const x of pos(v.B,v.nx))o.push(bolt('z',x,s*(v.D/2+v.b),0,v.db,2*v.tp+1,C.bolt,NM.pn));
    for(const y of pos(v.H,v.ny))o.push(bolt('z',s*(v.W/2+v.b),y,0,v.db,2*v.tp+1,C.bolt,NM.pn));}
  return flat(o);
};
M.hss_diafragma_atornillado=(RES,S)=>{
  const v=RES.vars,o=[],W=v.W,td=Math.max(v.btf*1.4,2),ext=W/2+5,xs=W/2+v.sb,Lsp=2*v.e1+(v.nfe+v.nfi-1)*v.p1,Lb=Lsp+25,d=v.bd;
  o.push(tube('z',W,W,v.t,-d/2-td-35,d/2+td+35,0,0,C.steel,'Columna RHS'));
  for(const s of [1,-1])o.push(lbox('z',s>0?d/2:-d/2-td,s>0?d/2+td:-d/2,-ext,ext,-ext,ext,C.plate,'Diafragmas pasantes'));
  for(const sg of [1,-1]){
    o.push(I_('x','v',d,v.mbf,v.btw,v.btf,sg>0?ext:-xs,sg>0?xs:-ext,0,0,'Ménsula corta'));
    o.push(I_('x','v',d,v.bbf,v.btw,v.btf,sg>0?xs:-xs-Lb,sg>0?xs+Lb:-xs,0,0,NM.vig));
    for(const s of [1,-1]){const tps=1.6,x0=sg>0?xs-8:-xs-Lsp+8;
      o.push(lbox('x',sg>0?xs-8:-xs-Lsp-8+8,sg>0?xs+Lsp+8-8:-xs+8,-v.bbf/2,v.bbf/2,s>0?d/2:-d/2-tps,s>0?d/2+tps:-d/2,C.stiff,'Empalme de viga'));
      for(let k=0;k<v.nfe+v.nfi;k++)for(const sy of [-1,1])o.push(bolt('z',sg*(xs+v.e1+k*v.p1-(sg>0?0:0)),sy*v.bbf*0.28,s*(d/2+tps/2-v.btf/2),v.d,tps+v.btf+1.2,C.bolt,NM.pn));}
    for(const sy of [-1,1])o.push(lbox('x',sg>0?xs-8:-xs-Lsp,sg>0?xs+Lsp:-xs+8,sy>0?v.btw/2:-v.btw/2-0.9,sy>0?v.btw/2+0.9:-v.btw/2,-v.yw-4,v.yw+4,C.stiff,'Empalme de viga'));
  }
  return flat(o);
};

/* ───────── Placa base (cm) ───────── */
M.placa_base=(RES,g)=>{
  const o=[],ped=g.hef+8,tg=Math.max(g.g,0.6),tp=g.tp,colH=g.d*1.6,z0=tg+tp;
  o.push(lbox('z',-ped,0,-g.Np/2,g.Np/2,-g.Bp/2,g.Bp/2,C.conc,'Pedestal'));
  o.push(lbox('z',0,tg,-g.N/2,g.N/2,-g.B/2,g.B/2,C.grout,'Mortero'));
  o.push(lbox('z',tg,tg+tp,-g.N/2,g.N/2,-g.B/2,g.B/2,C.plate,'Placa base'));
  if(g.tipo==='HSS')o.push(tube('z',g.d,g.bf,g.tf,z0,z0+colH,0,0,C.steel,'Columna'));
  else o.push(ibeam('z','u',g.d,g.bf,g.tw,g.tf,z0,z0+colH,0,0,C.steel,'Columna'));
  o.push(S3.tube('z',g.d+1.2,g.bf+1.2,0.6,z0,z0+0.6,0,0,C.weld,'Soldadura'));
  const ys=[];for(let i=0;i<g.nf;i++)ys.push(g.nf>1?-g.xb+i*2*g.xb/(g.nf-1):0);
  for(const sx of [-1,1])for(const y of ys){
    o.push(S3.cyl('z',sx*g.f,y,(tg+tp+3-g.hef)/2,g.da/2,tg+tp+3+g.hef,C.anchor,'Pernos de anclaje',10));
    o.push(S3.cyl('z',sx*g.f,y,-g.hef,g.da,g.da*0.7,C.anchor,'Pernos de anclaje',6));
    o.push(S3.cyl('z',sx*g.f,y,tg+tp+g.da*0.45,g.da*0.95,g.da*0.9,C.anchor,'Pernos de anclaje',6));}
  return flat(o);
};
})();
