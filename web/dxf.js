"use strict";
/* Exporta los dibujos SVG de la página a DXF (R12, ASCII). Los SVG llevan data-sc (px por unidad de dibujo) y
   data-f (mm por unidad de dibujo), de modo que el DXF sale en milímetros reales (1 unidad = 1 mm). */
window.DXF=(()=>{
  const LAYERS={ACERO:7,PERNOS:1,SOLDADURA:6,CONCRETO:8,COTAS:3,TEXTO:2,GEOM:4,TITULO:5};
  const esc=t=>String(t).replace(/[^\x20-\x7e]/g,c=>'\\U+'+c.charCodeAt(0).toString(16).toUpperCase().padStart(4,'0'));
  const f4=v=>(Math.round(v*1e4)/1e4).toString();
  function layerOf(el){
    const cls=el.getAttribute('class')||'',fill=(el.getAttribute('fill')||'')+(el.getAttribute('style')||''),st=el.getAttribute('stroke')||'';
    if(el.tagName==='text')return cls.includes('dt')?'COTAS':(el.getAttribute('style')||'').includes('700')?'TITULO':'TEXTO';
    if(cls.includes('dim'))return 'COTAS';
    if(fill.includes('--bolt'))return 'PERNOS';
    if(fill.includes('--tens'))return 'SOLDADURA';
    if(fill.includes('--conc')||fill.includes('--grout'))return 'CONCRETO';
    if(fill.includes('--steel')||st.includes('--steel'))return 'ACERO';
    return 'GEOM';
  }
  function pathPts(d){ // devuelve polilíneas [[x,y],...] con M L H V l h v z (m relativo)
    const out=[];let cur=[],x=0,y=0,sx=0,sy=0;
    const tk=d.match(/[a-zA-Z]|-?\d*\.?\d+(?:e-?\d+)?/g)||[];let i=0,cmd='';
    const num=()=>parseFloat(tk[i++]);
    while(i<tk.length){
      if(/[a-zA-Z]/.test(tk[i]))cmd=tk[i++];
      switch(cmd){
        case 'M':case 'm':{const a=num(),b=num();x=cmd==='m'?x+a:a;y=cmd==='m'?y+b:b;sx=x;sy=y;if(cur.length>1)out.push(cur);cur=[[x,y]];cmd=cmd==='m'?'l':'L';break;}
        case 'L':case 'l':{const a=num(),b=num();x=cmd==='l'?x+a:a;y=cmd==='l'?y+b:b;cur.push([x,y]);break;}
        case 'H':case 'h':{const a=num();x=cmd==='h'?x+a:a;cur.push([x,y]);break;}
        case 'V':case 'v':{const a=num();y=cmd==='v'?y+a:a;cur.push([x,y]);break;}
        case 'Z':case 'z':{cur.push([sx,sy]);x=sx;y=sy;break;}
        default:i++;                       // comandos no soportados (arcos, curvas): se omiten
      }
    }
    if(cur.length>1)out.push(cur);return out;
  }
  function entidades(svg,dx,dy,ymax){
    const sc=parseFloat(svg.dataset.sc),f=parseFloat(svg.dataset.f||1);
    if(!isFinite(sc)||sc<=0)return {txt:'',w:0};
    const k=f/sc,X=x=>f4(dx+x*k),Y=y=>f4(dy+(ymax-y)*k);
    const vb=svg.viewBox.baseVal;let e='';
    const line=(a,b,l)=>{e+=`0\nLINE\n8\n${l}\n10\n${X(a[0])}\n20\n${Y(a[1])}\n11\n${X(b[0])}\n21\n${Y(b[1])}\n`;};
    const poly=(pts,l)=>{for(let i=0;i<pts.length-1;i++)line(pts[i],pts[i+1],l);};
    for(const el of svg.querySelectorAll('*')){
      const t=el.tagName,l=layerOf(el),n=a=>parseFloat(el.getAttribute(a));
      if(el.closest('defs'))continue;
      if(t==='rect'){const x=n('x'),y=n('y'),w=n('width'),h=n('height');if(!(w>0&&h>0))continue;
        poly([[x,y],[x+w,y],[x+w,y+h],[x,y+h],[x,y]],l);}
      else if(t==='line')line([n('x1'),n('y1')],[n('x2'),n('y2')],l);
      else if(t==='circle'){const r=n('r');e+=`0\nCIRCLE\n8\n${l}\n10\n${X(n('cx'))}\n20\n${Y(n('cy'))}\n40\n${f4(r*k)}\n`;}
      else if(t==='polygon'||t==='polyline'){const p=(el.getAttribute('points')||'').trim().split(/[\s,]+/).map(parseFloat),pts=[];
        for(let i=0;i+1<p.length;i+=2)pts.push([p[i],p[i+1]]);if(t==='polygon'&&pts.length)pts.push(pts[0]);poly(pts,l);}
      else if(t==='path'){for(const pl of pathPts(el.getAttribute('d')||''))poly(pl,l);}
      else if(t==='text'){
        const tf=el.getAttribute('transform')||'',tr=/translate\(([-\d.]+)[ ,]+([-\d.]+)\)/.exec(tf),ro=/rotate\(([-\d.]+)\)/.exec(tf);
        const x=tr?parseFloat(tr[1]):n('x'),y=tr?parseFloat(tr[2]):n('y');if(!isFinite(x)||!isFinite(y))continue;
        const txt=el.textContent.trim();if(!txt)continue;
        const h=(l==='TITULO'?12:10.5)*k,anc=el.getAttribute('text-anchor'),ang=ro?-parseFloat(ro[1]):0;
        const j=anc==='middle'?1:anc==='end'?2:0;
        e+=`0\nTEXT\n8\n${l}\n10\n${X(x)}\n20\n${Y(y)}\n40\n${f4(h)}\n1\n${esc(txt)}\n`+(ang?`50\n${f4(ang)}\n`:'')+(j?`72\n${j}\n11\n${X(x)}\n21\n${Y(y)}\n`:'');
      }
    }
    return {txt:e,w:vb.width*k,h:vb.height*k};
  }
  function build(svgs){
    let ents='',dx=0;
    for(const svg of svgs){
      const vb=svg.viewBox.baseVal,k=parseFloat(svg.dataset.f||1)/parseFloat(svg.dataset.sc);
      const r=entidades(svg,dx,0,vb.height);ents+=r.txt;dx+=r.w+200;
    }
    const lay=Object.entries(LAYERS).map(([n,c])=>`0\nLAYER\n2\n${n}\n70\n0\n62\n${c}\n6\nCONTINUOUS\n`).join('');
    return `0\nSECTION\n2\nHEADER\n9\n$ACADVER\n1\nAC1009\n0\nENDSEC\n0\nSECTION\n2\nTABLES\n0\nTABLE\n2\nLTYPE\n70\n1\n0\nLTYPE\n2\nCONTINUOUS\n70\n0\n3\nSolid line\n72\n65\n73\n0\n40\n0\n0\nENDTAB\n0\nTABLE\n2\nLAYER\n70\n${Object.keys(LAYERS).length}\n${lay}0\nENDTAB\n0\nENDSEC\n0\nSECTION\n2\nENTITIES\n${ents}0\nENDSEC\n0\nEOF\n`;
  }
  function descargar(nombre){
    const svgs=[...document.querySelectorAll('svg[data-sc]')];
    if(!svgs.length){alert('No hay dibujos para exportar.');return;}
    const blob=new Blob([build(svgs).replace(/\n/g,'\r\n')],{type:'application/dxf'});
    const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=nombre||'conexion.dxf';document.body.appendChild(a);a.click();a.remove();
  }
  return {build,descargar};
})();
