"use strict";
/* Visor 3D sin dependencias: rasterizador con z-buffer (proyección ortográfica) + órbita con el ratón.
   S3  = constructores de sólidos (cajas, prismas, cilindros, perfiles I y tubos), todo en las unidades del módulo.
   V3D = visor: V3D.mount(contenedor) → {set(escena), destroy()}.  Escena = lista de sólidos {tris, edges, color, name}.
   Ejes globales: x horizontal (a lo largo de la viga), y horizontal transversal, z vertical (arriba). */
(function(){
const C={steel:'#8d99a8',web:'#a3adbb',plate:'#bcc8da',stiff:'#a9b79a',bolt:'#3b4048',weld:'#d92d20',conc:'#d8d2c4',grout:'#bdb7a6',anchor:'#555b66',diag:'#d9a441'};
// ── mapeo local (a: a lo largo del eje, u, v) → global; ciclo x→(y,z), y→(z,x), z→(x,y)
const MAP={x:(a,u,v)=>[a,u,v],y:(a,u,v)=>[v,a,u],z:(a,u,v)=>[u,v,a]};
function solid(name,color,verts,tris,edges){return {name,color,verts,tris,edges:edges||[]};}
// caja alineada con los ejes globales
function box(x0,y0,z0,x1,y1,z1,color,name){
  const X=[Math.min(x0,x1),Math.max(x0,x1)],Y=[Math.min(y0,y1),Math.max(y0,y1)],Z=[Math.min(z0,z1),Math.max(z0,z1)];
  const v=[];for(const z of Z)for(const y of Y)for(const x of X)v.push([x,y,z]);        // índice = x + 2y + 4z
  const q=[[0,1,3,2],[4,5,7,6],[0,1,5,4],[2,3,7,6],[0,2,6,4],[1,3,7,5]],t=[];
  for(const f of q)t.push([f[0],f[1],f[2]],[f[0],f[2],f[3]]);
  const e=[[0,1],[1,3],[3,2],[2,0],[4,5],[5,7],[7,6],[6,4],[0,4],[1,5],[2,6],[3,7]];
  return solid(name,color,v,t,e);
}
// caja en el marco local de un eje
function lbox(axis,a0,a1,u0,u1,v0,v1,color,name){
  const m=MAP[axis],p=m(a0,u0,v0),q=m(a1,u1,v1);return box(p[0],p[1],p[2],q[0],q[1],q[2],color,name);
}
function area(p){let s=0;for(let i=0;i<p.length;i++){const a=p[i],b=p[(i+1)%p.length];s+=a[0]*b[1]-b[0]*a[1];}return s/2;}
function inTri(p,a,b,c){const d=(p0,p1,p2)=>(p0[0]-p2[0])*(p1[1]-p2[1])-(p1[0]-p2[0])*(p0[1]-p2[1]);
  const d1=d(p,a,b),d2=d(p,b,c),d3=d(p,c,a);return !((d1<0||d2<0||d3<0)&&(d1>0||d2>0||d3>0));}
function earcut(P){ // triangulación por recorte de orejas de un polígono simple (índices)
  const n=P.length,idx=[...Array(n).keys()];if(area(P)<0)idx.reverse();
  const out=[];let g=0;
  while(idx.length>3&&g++<500){let cut=false;
    for(let i=0;i<idx.length;i++){const a=P[idx[(i+idx.length-1)%idx.length]],b=P[idx[i]],c=P[idx[(i+1)%idx.length]];
      if((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])<=1e-12)continue;
      let ok=true;for(const j of idx){const p=P[j];if(p===a||p===b||p===c)continue;if(inTri(p,a,b,c)){ok=false;break;}}
      if(ok){out.push([idx[(i+idx.length-1)%idx.length],idx[i],idx[(i+1)%idx.length]]);idx.splice(i,1);cut=true;break;}}
    if(!cut)break;}
  if(idx.length===3)out.push([idx[0],idx[1],idx[2]]);
  return out;
}
// prisma: polígono (u,v) en el plano ⟂ al eje, extruido de a0 a a1
function prism(axis,poly,a0,a1,color,name){
  const m=MAP[axis],n=poly.length,verts=[],tris=[],edges=[];
  for(const p of poly)verts.push(m(a0,p[0],p[1]));for(const p of poly)verts.push(m(a1,p[0],p[1]));
  const T=earcut(poly);for(const t of T){tris.push([t[0],t[1],t[2]],[n+t[0],n+t[1],n+t[2]]);}
  for(let i=0;i<n;i++){const j=(i+1)%n;tris.push([i,j,n+j],[i,n+j,n+i]);edges.push([i,j],[n+i,n+j],[i,n+i]);}
  return solid(name,color,verts,tris,edges);
}
// cilindro (n lados) centrado en (cx,cy,cz) con eje global
function cyl(axis,cx,cy,cz,r,len,color,name,seg){
  seg=seg||12;const verts=[],tris=[],edges=[],m=MAP[axis];
  const c=axis==='x'?[cy,cz,cx]:axis==='y'?[cz,cx,cy]:[cx,cy,cz];            // (u,v,a) locales del centro
  for(let k=0;k<2;k++){const a=c[2]+(k?len/2:-len/2);for(let i=0;i<seg;i++){const t=2*Math.PI*i/seg;verts.push(m(a,c[0]+r*Math.cos(t),c[1]+r*Math.sin(t)));}}
  for(let i=0;i<seg;i++){const j=(i+1)%seg;tris.push([i,j,seg+j],[i,seg+j,seg+i]);edges.push([i,j],[seg+i,seg+j]);}
  for(let i=1;i<seg-1;i++){tris.push([0,i,i+1],[seg,seg+i,seg+i+1]);}
  return solid(name,color,verts,tris,edges);
}
// perno: vástago + cabeza + tuerca (hexágonos aproximados), eje global, centro y longitud del vástago
function bolt(axis,cx,cy,cz,db,len,color,name){
  const out=[],h=db*0.65,off=len/2+h/2,P={x:[1,0,0],y:[0,1,0],z:[0,0,1]}[axis];
  out.push(cyl(axis,cx,cy,cz,db/2,len,color||C.bolt,name,10));
  for(const s of [-1,1])out.push(cyl(axis,cx+P[0]*s*off,cy+P[1]*s*off,cz+P[2]*s*off,db*0.9,h,color||C.bolt,name,6));
  return out;
}
// perfil I: eje del miembro, dirección del peralte ('u' o 'v' del marco local), centro (cu,cv) en el plano transversal
function ibeam(axis,depthDir,d,bf,tw,tf,a0,a1,cu,cv,color,name){
  const o=[];const du=depthDir==='u';
  const fl=(s)=>{const dc=s*(d/2-tf/2);return du?lbox(axis,a0,a1,cu+dc-tf/2,cu+dc+tf/2,cv-bf/2,cv+bf/2,color,name):lbox(axis,a0,a1,cu-bf/2,cu+bf/2,cv+dc-tf/2,cv+dc+tf/2,color,name);};
  o.push(fl(1),fl(-1));
  o.push(du?lbox(axis,a0,a1,cu-d/2+tf,cu+d/2-tf,cv-tw/2,cv+tw/2,C.web,name):lbox(axis,a0,a1,cu-tw/2,cu+tw/2,cv-d/2+tf,cv+d/2-tf,C.web,name));
  return o;
}
// tubo rectangular hueco: wu en u, wv en v, espesor t
function tube(axis,wu,wv,t,a0,a1,cu,cv,color,name){
  return [lbox(axis,a0,a1,cu-wu/2,cu+wu/2,cv-wv/2,cv-wv/2+t,color,name),lbox(axis,a0,a1,cu-wu/2,cu+wu/2,cv+wv/2-t,cv+wv/2,color,name),
          lbox(axis,a0,a1,cu-wu/2,cu-wu/2+t,cv-wv/2+t,cv+wv/2-t,color,name),lbox(axis,a0,a1,cu+wu/2-t,cu+wu/2,cv-wv/2+t,cv+wv/2-t,color,name)];
}
// rotación de sólidos alrededor de un eje global por un pivote (grados)
function rot(list,axis,deg,pv){
  const c=Math.cos(deg*Math.PI/180),s=Math.sin(deg*Math.PI/180),[px,py,pz]=pv||[0,0,0];
  for(const sd of list)sd.verts=sd.verts.map(([x,y,z])=>{x-=px;y-=py;z-=pz;let r;
    if(axis==='y')r=[x*c+z*s,y,-x*s+z*c];else if(axis==='x')r=[x,y*c-z*s,y*s+z*c];else r=[x*c-y*s,x*s+y*c,z];
    return [r[0]+px,r[1]+py,r[2]+pz];});
  return list;
}
const flat=a=>a.flat(Infinity).filter(Boolean);
const prismXZ=(pts,y0,y1,c,n)=>prism('y',pts.map(([x,z])=>[z,x]),y0,y1,c,n);   // polígono en el plano x–z, extruido en y
const prismXY=(pts,z0,z1,c,n)=>prism('z',pts,z0,z1,c,n);                       // polígono en el plano x–y, extruido en z
const prismYZ=(pts,x0,x1,c,n)=>prism('x',pts,x0,x1,c,n);                       // polígono en el plano y–z, extruido en x
window.S3={C,box,lbox,prism,prismXZ,prismXY,prismYZ,cyl,bolt,ibeam,tube,rot,flat};

/* ═════════════ Visor ═════════════ */
function mat(yaw,pitch){ // rotación mundo→vista: primero yaw (z), luego pitch (x)
  const cy=Math.cos(yaw),sy=Math.sin(yaw),cp=Math.cos(pitch),sp=Math.sin(pitch);
  return (x,y,z)=>{const a=x*cy-y*sy,b=x*sy+y*cy;return [a,b*cp-z*sp,b*sp+z*cp];};  // [derecha, profundidad(+lejos), arriba]
}
function hex(c){const n=parseInt(c.slice(1),16);return [(n>>16)&255,(n>>8)&255,n&255];}
function mount(box){
  box.innerHTML=`<div class="v3-bar"><button data-v="iso" class="on">Isométrica</button><button data-v="front">Frente</button><button data-v="side">Lateral</button><button data-v="top">Planta</button>
    <span class="v3-sp"></span><button data-v="fit" title="Ajustar al encuadre">⤢</button></div>
    <div class="v3-wrap"><canvas class="v3-cv"></canvas></div><div class="v3-leg"></div>
    <div class="v3-hint">Arrastre: girar · Mayús + arrastre (o botón derecho): desplazar · Rueda: acercar · Doble clic: restablecer · Esquemático</div>`;
  const cv=box.querySelector('canvas'),leg=box.querySelector('.v3-leg'),ctx=cv.getContext('2d');
  let scene=[],yaw=-0.6,pitch=0.5,zoom=1,panx=0,pany=0,W=0,H=0,center=[0,0,0],rad=1,raf=0,fitted=false;
  function resize(){const r=box.querySelector('.v3-wrap').getBoundingClientRect();W=Math.max(300,Math.floor(r.width||640));H=Math.round(Math.min(560,W*0.72));
    cv.width=W;cv.height=H;cv.style.height=H+'px';}
  function limpiar(){scene=scene.filter(s=>s.verts.every(v=>v.every(x=>isFinite(x))));}
  function bounds(){let mn=[1e18,1e18,1e18],mx=[-1e18,-1e18,-1e18];for(const s of scene)for(const v of s.verts)for(let i=0;i<3;i++){mn[i]=Math.min(mn[i],v[i]);mx[i]=Math.max(mx[i],v[i]);}
    if(mn[0]>mx[0]){mn=[-1,-1,-1];mx=[1,1,1];}
    center=[(mn[0]+mx[0])/2,(mn[1]+mx[1])/2,(mn[2]+mx[2])/2];rad=Math.hypot(mx[0]-mn[0],mx[1]-mn[1],mx[2]-mn[2])/2||1;}
  function css(v,d){return getComputedStyle(document.documentElement).getPropertyValue(v).trim()||d;}
  function draw(){
    raf=0;if(!W)resize();
    const R=mat(yaw,pitch),sc=Math.min(W,H)*0.46/rad*zoom,ox=W/2+panx,oy=H/2+pany;
    ctx.fillStyle='#ffffff';ctx.fillStyle=css('--card','#ffffff');const bgs=ctx.fillStyle;
    const bg=bgs[0]==='#'?hex(bgs):(bgs.match(/\d+/g)||[255,255,255]).slice(0,3).map(Number);
    const img=ctx.createImageData(W,H),px=new Uint32Array(img.data.buffer),zb=new Float32Array(W*H).fill(1e30);
    const bgc=(255<<24)|(bg[2]<<16)|(bg[1]<<8)|bg[0];px.fill(bgc);
    const lin=[],tr=[];
    for(const s of scene){
      const V=s.verts.map(([x,y,z])=>{const r=R(x-center[0],y-center[1],z-center[2]);return [ox+r[0]*sc,oy-r[2]*sc,r[1]*sc];});   // z: profundidad (menor = más cerca)
      const base=hex(s.color);
      for(const t of s.tris){
        const a=V[t[0]],b=V[t[1]],c=V[t[2]];
        const ux=b[0]-a[0],uy=b[1]-a[1],uz=b[2]-a[2],vx=c[0]-a[0],vy=c[1]-a[1],vz=c[2]-a[2];
        let nx=uy*vz-uz*vy,ny=uz*vx-ux*vz,nz=ux*vy-uy*vx;const nl=Math.hypot(nx,ny,nz)||1;nx/=nl;ny/=nl;nz/=nl;
        if(nz>0){nx=-nx;ny=-ny;nz=-nz;}                       // normal hacia la cámara (menor z = más cerca)
        const dif=Math.max(0,nx*(-0.4)+ny*(-0.5)+nz*(-0.75));   // luz fija arriba-izquierda-frente (coords. de pantalla)
        const sh=0.45+0.55*Math.min(1,dif/0.8);
        const col=(255<<24)|(Math.min(255,base[2]*sh)<<16)|(Math.min(255,base[1]*sh)<<8)|Math.min(255,base[0]*sh);
        tr.push([a,b,c,col]);
      }
      for(const e of s.edges)lin.push([V[e[0]],V[e[1]]]);
    }
    const eps=rad*sc*0.004;
    for(const [a,b,c,col] of tr){
      const x0=Math.max(0,Math.floor(Math.min(a[0],b[0],c[0]))),x1=Math.min(W-1,Math.ceil(Math.max(a[0],b[0],c[0])));
      const y0=Math.max(0,Math.floor(Math.min(a[1],b[1],c[1]))),y1=Math.min(H-1,Math.ceil(Math.max(a[1],b[1],c[1])));
      const den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1]);if(Math.abs(den)<1e-9)continue;
      for(let y=y0;y<=y1;y++)for(let x=x0;x<=x1;x++){
        const px_=x+0.5,py_=y+0.5;
        const l1=((b[1]-c[1])*(px_-c[0])+(c[0]-b[0])*(py_-c[1]))/den,l2=((c[1]-a[1])*(px_-c[0])+(a[0]-c[0])*(py_-c[1]))/den,l3=1-l1-l2;
        if(l1<-1e-6||l2<-1e-6||l3<-1e-6)continue;
        const z=l1*a[2]+l2*b[2]+l3*c[2],i=y*W+x;
        if(z<zb[i]){zb[i]=z;px[i]=col;}
      }
    }
    // aristas con prueba de profundidad
    const ink=(255<<24)|(40<<16)|(32<<8)|28;
    for(const [a,b] of lin){
      const n=Math.ceil(Math.max(Math.abs(b[0]-a[0]),Math.abs(b[1]-a[1])));if(n<1||n>4000)continue;
      for(let k=0;k<=n;k++){const t=k/n,x=Math.round(a[0]+(b[0]-a[0])*t),y=Math.round(a[1]+(b[1]-a[1])*t);
        if(x<0||y<0||x>=W||y>=H)continue;const z=a[2]+(b[2]-a[2])*t,i=y*W+x;if(z<=zb[i]+eps){px[i]=ink;}}
    }
    ctx.putImageData(img,0,0);
    // gizmo de ejes
    const g=[['x','#d92d20'],['y','#2e9e4f'],['z','#2e6fd0']],v={x:[1,0,0],y:[0,1,0],z:[0,0,1]};
    ctx.font='11px system-ui,sans-serif';ctx.lineWidth=2;
    for(const [k,col] of g){const r=R(...v[k]);ctx.strokeStyle=col;ctx.fillStyle=col;ctx.beginPath();ctx.moveTo(40,H-34);ctx.lineTo(40+r[0]*24,H-34-r[2]*24);ctx.stroke();ctx.fillText(k,40+r[0]*29-3,H-34-r[2]*29+4);}
  }
  const redraw=()=>{if(!raf)raf=requestAnimationFrame(draw);};
  function legend(){const seen=new Map();for(const s of scene)if(s.name&&!seen.has(s.name))seen.set(s.name,s.color);
    leg.innerHTML=[...seen].map(([n,c])=>`<span><i style="background:${c}"></i>${n}</span>`).join('');}
  const views={iso:[-0.6,0.5],front:[0,0],side:[-Math.PI/2,0],top:[0,Math.PI/2-0.001]};
  function setView(k){[yaw,pitch]=views[k];panx=pany=0;zoom=1;box.querySelectorAll('.v3-bar button[data-v]').forEach(b=>b.classList.toggle('on',b.dataset.v===k));redraw();}
  box.querySelector('.v3-bar').onclick=e=>{const b=e.target.closest('button');if(!b)return;if(b.dataset.v==='fit'){panx=pany=0;zoom=1;redraw();}else setView(b.dataset.v);};
  let drag=null;
  cv.addEventListener('contextmenu',e=>e.preventDefault());
  cv.addEventListener('pointerdown',e=>{cv.setPointerCapture(e.pointerId);drag={x:e.clientX,y:e.clientY,pan:e.shiftKey||e.button===2||e.button===1};});
  cv.addEventListener('pointermove',e=>{if(!drag)return;const dx=e.clientX-drag.x,dy=e.clientY-drag.y;drag.x=e.clientX;drag.y=e.clientY;
    if(drag.pan){panx+=dx;pany+=dy;}else{yaw-=dx*0.008;pitch=Math.max(-1.55,Math.min(1.55,pitch+dy*0.008));box.querySelectorAll('.v3-bar button[data-v]').forEach(b=>b.classList.remove('on'));}
    redraw();});
  cv.addEventListener('pointerup',()=>{drag=null;});
  cv.addEventListener('wheel',e=>{e.preventDefault();zoom=Math.max(0.2,Math.min(12,zoom*Math.exp(-e.deltaY*0.0012)));redraw();},{passive:false});
  cv.addEventListener('dblclick',()=>setView('iso'));
  const ro=typeof ResizeObserver!=='undefined'?new ResizeObserver(()=>{if(box.offsetParent){resize();redraw();}}):null;if(ro)ro.observe(box);
  return {
    set(sc){scene=sc||[];limpiar();bounds();legend();resize();redraw();},
    redraw(){resize();redraw();},
    destroy(){if(ro)ro.disconnect();box.innerHTML='';},
  };
}
window.V3D={mount};
})();
