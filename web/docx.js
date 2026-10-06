"use strict";
/* Convierte los reportes HTML en un documento Word (.docx): el HTML se transforma en bloques (títulos, párrafos, tablas, imágenes PNG de
   los dibujos) y el servidor los empaqueta con docx_writer.py. */
window.Docx=(()=>{
  const SVG_CSS='text{fill:#111;font:11px sans-serif}.dim{stroke:#667085;stroke-width:.8;fill:none}text.dt{fill:#667085;font-size:10.5px}';
  const COL={CUMPLE:'1a7f4b','AL-LÍMITE':'a76a00','NO-CUMPLE':'b42318'};
  const tx=e=>(e.textContent||'').replace(/\s+/g,' ').trim();

  async function svgPng(svg){
    const c=svg.cloneNode(true);c.setAttribute('xmlns','http://www.w3.org/2000/svg');
    const vb=(c.getAttribute('viewBox')||'0 0 440 400').split(/[ ,]+/).map(Number),w=vb[2],h=vb[3];
    c.setAttribute('width',w*2);c.setAttribute('height',h*2);
    const st=document.createElementNS('http://www.w3.org/2000/svg','style');st.textContent=SVG_CSS;c.insertBefore(st,c.firstChild);
    const url=URL.createObjectURL(new Blob([new XMLSerializer().serializeToString(c)],{type:'image/svg+xml;charset=utf-8'}));
    try{
      const img=new Image();img.src=url;await img.decode();
      const cv=document.createElement('canvas');cv.width=w*2;cv.height=h*2;const g=cv.getContext('2d');
      g.fillStyle='#fff';g.fillRect(0,0,cv.width,cv.height);g.drawImage(img,0,0,cv.width,cv.height);
      return {png:cv.toDataURL('image/png'),w:cv.width,h:cv.height};
    }finally{URL.revokeObjectURL(url);}
  }
  function tabla(t){
    const filas=[...t.querySelectorAll('tr')],out=[],largo=[],palabra=[];
    for(const tr of filas){
      const celdas=[...tr.children].filter(c=>/^t[dh]$/i.test(c.tagName)),grp=tr.classList.contains('grp'),cab=celdas.some(c=>c.tagName==='TH');
      const fila=celdas.map((c,i)=>{
        const o={text:tx(c)};const cl=[...c.classList];
        if(cab){o.b=true;o.bg='eef2f7';}
        if(grp){o.b=true;o.bg='e8f0fb';o.color='1f4e8c';}
        if(cl.includes('n'))o.al='right';
        const e=cl.find(k=>COL[k]);if(e){o.color=COL[e];o.b=true;o.sz=7;}
        if(c.querySelector('b,strong')&&tx(c.querySelector('b,strong'))===o.text)o.b=true;
        const sp=parseInt(c.getAttribute('colspan')||'1');if(sp>1)o.span=sp;
        if(!sp||sp===1){largo[i]=Math.max(largo[i]||0,Math.min(o.text.length,38));palabra[i]=Math.max(palabra[i]||0,Math.min(14,...o.text.split(' ').map(w=>w.length)));}
        return o;});
      out.push(fila);
    }
    const n=Math.max(...out.map(r=>r.reduce((a,c)=>a+(c.span||1),0)),1);
    return {t:'table',rows:out,w:Array.from({length:n},(_,i)=>Math.max(Math.min(largo[i]||6,30),(palabra[i]||4)+8,7))};
  }
  async function bloques(html,opt){
    opt=opt||{};const memoria=!!opt.memoria;
    const d=new DOMParser().parseFromString(html,'text/html'),out=[];let omitir=false,primero=true;
    async function recorre(el){
      for(const n of [...el.children]){
        const tag=n.tagName.toLowerCase(),cl=n.classList;
        if(tag==='style'||tag==='script'||tag==='title')continue;
        if(/^h[1-3]$/.test(tag)){
          const txt=tx(n);
          if(tag==='h2'){omitir=!memoria&&/memoria detallada/i.test(txt);}
          else if(tag==='h1')omitir=false;
          if(omitir)continue;
          if(cl.contains('pb')&&!primero)out.push({t:'pb'});
          out.push({t:'h',n:+tag[1],text:txt});primero=false;continue;}
        if(omitir)continue;
        if(cl.contains('conn')||cl.contains('cover')){if(!primero&&cl.contains('conn'))out.push({t:'pb'});omitir=false;}
        if(tag==='table'){out.push(tabla(n));primero=false;continue;}
        if(tag==='ul'){out.push({t:'ul',items:[...n.children].map(tx)});continue;}
        if(tag==='svg'){out.push({t:'imgs',items:[await svgPng(n)],cm:11});continue;}
        if(tag==='img'&&/^data:image\/png/.test(n.getAttribute('src')||'')){out.push({t:'imgs',items:[{png:n.getAttribute('src')}],cm:4.5});continue;}
        if(cl.contains('dr')){const its=[];for(const s of n.querySelectorAll('svg'))its.push(await svgPng(s));if(its.length)out.push({t:'imgs',items:its,cm:17});continue;}
        if(cl.contains('res')){const k=cl.contains('ok')?'1a7f4b':cl.contains('bd')?'b42318':'a76a00';out.push({t:'p',text:tx(n),b:true,color:k,sz:12});continue;}
        if(cl.contains('firma')){const im=n.querySelector('img');if(im&&/^data:image\/png/.test(im.getAttribute('src')||''))out.push({t:'imgs',items:[{png:im.getAttribute('src')}],cm:4.5});
          out.push({t:'p',text:tx(n),sz:9,color:'444444'});continue;}
        if(n.children.length&&!(tag==='p'||cl.contains('note')||cl.contains('sub'))){await recorre(n);continue;}
        const t=tx(n);if(t)out.push({t:'p',text:t,sz:cl.contains('note')||cl.contains('sub')?(cl.contains('sub')?12:8.5):10,color:cl.contains('note')?'667085':null,b:tag==='b'});
      }
    }
    await recorre(d.body);return out;
  }
  async function descargar(html,nombre,opt){
    const bl=await bloques(html,opt);
    const r=await fetch('/api/docx',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({bloques:bl,titulo:(opt&&opt.titulo)||'Memoria de cálculo de conexiones metálicas'})});
    if(!r.ok){let m='no se pudo generar el documento';try{m=(await r.json()).error||m;}catch(e){}throw new Error(m);}
    const blob=await r.blob(),a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=nombre.replace(/[^\w.\-ñÑáéíóúÁÉÍÓÚ]+/g,'_')+'.docx';
    document.body.appendChild(a);a.click();a.remove();
  }
  return {bloques,descargar};
})();
