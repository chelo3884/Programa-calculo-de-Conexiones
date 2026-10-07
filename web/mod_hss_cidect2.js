"use strict";
/* CIDECT 9: placa simple a RHS (hss_placasimple), empalme de columna RHS (empalme_rhs), diafragma pasante atornillado (hss_diafragma_atornillado) */
const ps_w=(x,y,w,h,fill,sw)=>rect(x,y,w,h,fill,sw);
function psElev(RES,S){
  const v=RES.vars,W=480,H=400,m=26,L=v.L,colH=Math.max(L*1.5,v.bd*1.4),ext=Math.max(v.leh+v.a+v.bbf*0.5,12);
  const sc=Math.min((W-2*m)/(v.D*0.6+ext+v.leh+10),(H-2*m)/colH),x0=m+30,cy=H/2,X=a=>x0+a*sc,Y=a=>cy-a*sc;
  let s=svgH(W,H,sc,'ELEVACIÓN (cara de la RHS y placa simple)');
  s+=rect(X(-v.W*0.35),Y(colH/2),v.W*0.35*sc,colH*sc,'var(--steelf)',1.2);
  s+=rect(X(0),Y(L/2),(v.a+v.leh)*sc,L*sc,'var(--steelf)',1.3);
  s+=`<path d="M${X(0)} ${Y(L/2)}V${Y(-L/2)}" stroke="var(--tens)" stroke-width="4"/>`;
  s+=rect(X(v.a*0.4),Y(v.bd/2),(v.a+v.leh+ext)*sc,v.btf*sc,'var(--steel)',.8)+rect(X(v.a*0.4),Y(-v.bd/2+v.btf),(v.a+v.leh+ext)*sc,v.btf*sc,'var(--steel)',.8);
  for(let k=0;k<v.n;k++)s+=`<circle cx="${X(v.a)}" cy="${Y(((v.n-1)/2-k)*v.s)}" r="${Math.max(2.5,v.db/2*sc)}" fill="var(--bolt)" stroke="var(--card)"/>`;
  s+=dimV(X(v.a+v.leh)+14,Y(L/2),Y(-L/2),`Lp = ${c2m(L)}`)+dimH(X(0),X(v.a),Y(-L/2)-6,`a = ${c2m(v.a)}`);
  return s+`<text class="dt" x="${W-8}" y="${H-6}" text-anchor="end">cotas [${uf('Ls').l}] · soldadura en rojo · esquemático</text></svg>`;
}
function psPlan(RES,S){
  const v=RES.vars,W=480,H=400,m=30,ext=v.a+v.leh+25,sc=Math.min((W-2*m)/(v.D+ext),(H-2*m)/(v.W*1.2)),x0=m+v.D*sc*0.5,cy=H/2,X=a=>x0+a*sc,Y=a=>cy-a*sc;
  let s=svgH(W,H,sc,'PLANTA');
  s+=rect(X(-v.D),Y(v.W/2),v.D*sc,v.W*sc,'var(--steelf)',1.2)+rect(X(-v.D+v.t),Y(v.W/2-v.t),(v.D-2*v.t)*sc,(v.W-2*v.t)*sc,'var(--card)',.8);
  s+=rect(X(0),Y(v.btw/2+v.tp),(v.a+v.leh)*sc,v.tp*sc,'var(--steelf)',1.3)+rect(X(v.a*0.5),Y(v.btw/2),(ext-v.a*0.5)*sc,v.btw*sc,'var(--conc)',1);
  s+=`<path d="M${X(0)} ${Y(v.btw/2+v.tp)}h-5" stroke="var(--tens)" stroke-width="3"/>`;
  s+=`<rect x="${X(v.a)-2}" y="${Y(v.btw/2+v.tp+4)}" width="4" height="${(v.btw+2*v.tp+8)*sc*0.8}" fill="var(--bolt)"/>`;
  return s+dimV(X(-v.D)-8,Y(v.W/2),Y(-v.W/2),`B = ${c2m(v.W)}`)+`<text class="dt" x="${W-8}" y="${H-6}" text-anchor="end">esquemático</text></svg>`;
}
const MODULE_PS=Object.assign({},MODULE_BASE,{id:'hss_placasimple',api:'/api/hss_placasimple',title:'Placa simple a cortante — viga W a columna RHS (CIDECT 9 §5.3)',
  comboCols:[],comboHelp:'Vu: cortante mayorado de la viga. Tip: la guía diseña para desarrollar el cortante resistente de la viga (V* = φVn).',
  svgs:[{id:'svgElev',fn:psElev},{id:'svgPlan',fn:psPlan}]});

function erElev(RES,S){
  const v=RES.vars,W=480,H=400,m=26,colH=Math.max(v.H*1.8,v.W*1.6),sc=Math.min((W-2*m)/(v.B*1.3),(H-2*m)/colH),cx=W/2,cy=H/2,X=a=>cx+a*sc,Y=a=>cy-a*sc;
  let s=svgH(W,H,sc,'ELEVACIÓN DEL EMPALME');
  const half=colH/2;
  s+=rect(X(-v.W/2),Y(half+v.tp),v.W*sc,(half-v.tp)*sc,'var(--steelf)',1.2)+rect(X(-v.W/2),Y(0),v.W*sc,(half-v.tp)*sc,'var(--steelf)',1.2);
  s+=rect(X(-v.B/2),Y(v.tp),v.B*sc,v.tp*sc,'var(--steel)',1.3)+rect(X(-v.B/2),Y(0),v.B*sc,v.tp*sc,'var(--steel)',1.3);
  for(const sg of [1,-1]){const bx=sg*(v.W/2+v.b);
    s+=`<rect x="${X(bx)-v.db/2*sc}" y="${Y(v.tp*1.8)}" width="${v.db*sc}" height="${v.tp*3.6*sc}" fill="var(--bolt)"/>`;
    s+=`<path d="M${X(sg*v.W/2)} ${Y(v.tp)}l${sg*6} -6h${-sg*6}z" fill="var(--tens)"/><path d="M${X(sg*v.W/2)} ${Y(0)}l${sg*6} 6h${-sg*6}z" fill="var(--tens)"/>`;}
  s+=dimH(X(-v.B/2),X(v.B/2),Y(-v.tp-6)+14,`B = ${c2m(v.B)}`)+dimH(X(v.W/2),X(v.W/2+v.b),Y(v.tp*3)-4,`b ${c2m(v.b)}`);
  return s+`<text class="dt" x="${W-8}" y="${H-6}" text-anchor="end">placas de ${c2m(v.tp)} · filetes en rojo · esquemático</text></svg>`;
}
function erPlan(RES,S){
  const v=RES.vars,W=480,H=400,m=30,sc=Math.min((W-2*m)/v.B,(H-2*m)/v.H),cx=W/2,cy=H/2,X=a=>cx+a*sc,Y=a=>cy-a*sc;
  let s=svgH(W,H,sc,'PLANTA DE LA PLACA DE EXTREMO');
  s+=rect(X(-v.B/2),Y(v.H/2),v.B*sc,v.H*sc,'var(--steelf)',1.4)+rect(X(-v.W/2),Y(v.D/2),v.W*sc,v.D*sc,'var(--card)',1.4)+rect(X(-v.W/2+v.t),Y(v.D/2-v.t),(v.W-2*v.t)*sc,(v.D-2*v.t)*sc,'var(--steel)',.8);
  const pos=(L,n)=>Array.from({length:n},(_,i)=>-L/2+(i+0.5)*L/n),r=Math.max(3,v.db/2*sc);
  for(const sg of [1,-1]){for(const x of pos(v.B,v.nx))s+=`<circle cx="${X(x)}" cy="${Y(sg*(v.D/2+v.b))}" r="${r}" fill="var(--bolt)" stroke="var(--card)"/>`;
    for(const y of pos(v.H,v.ny))s+=`<circle cx="${X(sg*(v.W/2+v.b))}" cy="${Y(y)}" r="${r}" fill="var(--bolt)" stroke="var(--card)"/>`;}
  s+=`<path d="M${X(-v.W/2)} ${Y(v.D/2)}H${X(v.W/2)}V${Y(-v.D/2)}H${X(-v.W/2)}Z" fill="none" stroke="var(--tens)" stroke-width="3"/>`;
  s+=dimH(X(-v.B/2),X(v.B/2),Y(-v.H/2)+16,`B = ${c2m(v.B)}`)+dimV(X(-v.B/2)-8,Y(v.H/2),Y(-v.H/2),`H = ${c2m(v.H)}`);
  return s+`<text class="dt" x="${W-8}" y="${H-6}" text-anchor="end">pernos en los 4 lados · esquemático</text></svg>`;
}
const MODULE_ER=Object.assign({},MODULE_BASE,{id:'empalme_rhs',api:'/api/empalme_rhs',title:'Empalme de columna RHS con placas de extremo atornilladas (CIDECT 9 §11.1.1.2)',
  comboCols:[{sym:'T',label:'T perno ({u})',q:'F'},{sym:'t_nec',label:'t nec ({u})',q:'Lc'}],
  comboHelp:'N (+ tracción), Mx, My y V en el empalme. La tracción por perno incluye el momento (grupo elástico, sin contacto: conservador).',
  svgs:[{id:'svgElev',fn:erElev},{id:'svgPlan',fn:erPlan}]});

function daElev(RES,S){
  const v=RES.vars,W=520,H=400,m=22,half=v.sb+v.p1*5+60,colH=v.bd*1.9;
  const sc=Math.min((W-2*m)/(half+v.W/2+10),(H-2*m)/colH),x0=m+8+v.W/2*sc,cy=H/2,X=a=>x0+a*sc,Y=a=>cy-a*sc;
  let s=svgH(W,H,sc,'ELEVACIÓN (ménsula corta y empalme)');
  s+=rect(X(-v.W/2),Y(colH/2),v.W*sc,colH*sc,'var(--steelf)',1.2)+rect(X(-v.W/2+v.t),Y(colH/2),(v.W-2*v.t)*sc,colH*sc,'var(--card)',.8);
  const yt=v.bd/2,xe=v.W/2+half;
  s+=`<rect x="${X(v.W/2)}" y="${Y(yt-v.btf)}" width="${(half)*sc}" height="${(v.bd-2*v.btf)*sc}" fill="var(--conc)" stroke="var(--ink)" opacity=".8"/>`;
  for(const sy of [1,-1]){
    s+=rect(X(v.W/2),Y(sy>0?yt:-yt+v.btf),half*sc,v.btf*sc,'var(--steel)');
    s+=rect(X(v.W/2-1),Y(sy>0?yt+v.btf*1.2:-yt-0+0),(v.W/2+1)*0+14*sc,v.btf*1.2*sc,'var(--steelf)',1.2);
    const x1=v.sb,x2=v.sb+v.p1*5+30;
    s+=rect(X(v.W/2+x1),Y(sy>0?yt+v.btf*1.0:-yt-v.btf*0.0)-(sy>0?0:-0),(x2-x1)*sc,v.btf*sc,'var(--steelf)',1.2);
    for(let k=0;k<v.nfe+v.nfi;k++)s+=`<circle cx="${X(v.W/2+x1+v.e1+k*v.p1)}" cy="${Y(sy*(yt-v.btf/2))}" r="${Math.max(2.5,v.d/2*sc)}" fill="var(--bolt)" stroke="var(--card)"/>`;
    s+=`<path d="M${X(v.W/2)} ${Y(sy*yt)}l-6 ${-sy*6}v${sy*6}z" fill="var(--tens)"/>`;
  }
  s+=dimH(X(v.W/2),X(v.W/2+v.sc),Y(-yt)+18,`sc = ${c2m(v.sc)}`)+dimH(X(v.W/2),X(v.W/2+v.sl),Y(-yt)+34,`sl = ${c2m(v.sl)}`)+dimV(X(v.W/2+half)+6,Y(yt),Y(-yt),`d = ${c2m(v.bd)}`);
  return s+`<text class="dt" x="${W-8}" y="${H-6}" text-anchor="end">cotas [${uf('Ls').l}] · diafragma pasante + ménsula corta + empalme · esquemático</text></svg>`;
}
function daPlan(RES,S){
  const v=RES.vars,W=480,H=400,m=26,ext=v.sb+v.p1*5+40,sc=Math.min((W-2*m)/(v.W+ext+40),(H-2*m)/(v.W*1.6)),x0=W/2-ext*sc*0.1-(v.W/2)*sc*0.2,cy=H/2,X=a=>x0+a*sc-v.W*sc*0.5*0,Y=a=>cy-a*sc;
  const xd=v.W/2+ext*0.5;
  let s=svgH(W,H,sc,'PLANTA (diafragma pasante a nivel del ala)');
  s+=rect(X(-v.W/2-30),Y(v.W/2+30),(v.W+60)*sc*1,(v.W+60)*sc,'var(--steelf)',1.2)+rect(X(-v.W/2),Y(v.W/2),v.W*sc,v.W*sc,'var(--card)',1.4)+rect(X(-v.W/2+v.t),Y(v.W/2-v.t),(v.W-2*v.t)*sc,(v.W-2*v.t)*sc,'var(--steel)',.8);
  s+=rect(X(v.W/2+30),Y(v.mbf/2),(ext*0.8)*sc,v.mbf*sc,'var(--steel)',1.1)+rect(X(v.W/2+30+v.sc*0),Y(v.btw/2),(ext*0.8)*sc,v.btw*sc,'var(--conc)',1);
  return s+dimV(X(-v.W/2-30)-8,Y(v.W/2+30),Y(-v.W/2-30),`diafragma`)+`<text class="dt" x="${W-8}" y="${H-6}" text-anchor="end">ménsula bf = ${c2m(v.mbf)} · esquemático</text></svg>`;
}
const MODULE_DA=Object.assign({},MODULE_BASE,{id:'hss_diafragma_atornillado',api:'/api/hss_diafragma_atornillado',title:'Unión atornillada con diafragma pasante — viga W a columna RHS (CIDECT 9 §8.2)',
  comboCols:[{sym:'Vbs',label:'Vbs req ({u})',q:'F'}],
  comboHelp:'Vg: cortante gravitacional. Ms: momento de servicio en la cara de la columna para el deslizamiento. La demanda sísmica se deduce de la resistencia de la viga (ec. 8.11).',
  svgs:[{id:'svgElev',fn:daElev},{id:'svgPlan',fn:daPlan}]});
