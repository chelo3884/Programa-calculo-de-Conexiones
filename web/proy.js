"use strict";
/* Proyectos: varios proyectos, cada uno con sus conexiones (copias del reporte y del estado), guardados en el navegador.
   localStorage 'cx_proyectos' = {v:2, activo, proyectos:[{id,nombre,meta,creado,modificado,items:[...]}]}. */
window.Proy=(()=>{
  const KEY='cx_proyectos',VIEJA='cx_proyecto';
  const uid=()=>Date.now().toString(36)+Math.random().toString(36).slice(2,6);
  const hoy=()=>new Date().toISOString();
  let cache=null;
  function leer(){
    if(cache)return cache;
    let P=null;try{P=JSON.parse(localStorage.getItem(KEY)||'null');}catch(e){}
    if(!P||P.v!==2){
      P={v:2,activo:null,proyectos:[]};
      try{const v=JSON.parse(localStorage.getItem(VIEJA)||'null');          // migración del proyecto único anterior
        if(v&&(v.items||[]).length){const p={id:uid(),nombre:(v.meta&&v.meta.proyecto)||'Proyecto 1',meta:v.meta||{},creado:hoy(),modificado:hoy(),items:v.items};
          P.proyectos.push(p);P.activo=p.id;}}catch(e){}
    }
    return cache=P;
  }
  function escribir(){try{localStorage.setItem(KEY,JSON.stringify(cache));return true;}catch(e){return false;}}
  const get=id=>leer().proyectos.find(p=>p.id===id)||null;
  const activo=()=>get(leer().activo);
  function setActivo(id){leer().activo=id;escribir();}
  function crear(nombre){const p={id:uid(),nombre:nombre||'Proyecto nuevo',meta:{proyecto:nombre||''},creado:hoy(),modificado:hoy(),items:[]};
    leer().proyectos.push(p);leer().activo=p.id;escribir();return p;}
  function borrar(id){const P=leer();P.proyectos=P.proyectos.filter(p=>p.id!==id);if(P.activo===id)P.activo=P.proyectos.length?P.proyectos[0].id:null;escribir();}
  function recientes(n){return [...leer().proyectos].sort((a,b)=>(b.modificado||'').localeCompare(a.modificado||'')).slice(0,n||99);}
  function item(pid,iid){const p=get(pid);return p?p.items.find(i=>i.id===iid)||null:null;}
  function guardarItem(pid,it){
    const p=get(pid);if(!p)return false;
    const i=p.items.findIndex(x=>x.id===it.id||(x.modulo===it.modulo&&x.etiqueta===it.etiqueta));
    if(i>=0){it.id=p.items[i].id;p.items[i]=it;}else p.items.push(it);
    p.modificado=hoy();return escribir();
  }
  function quitarItem(pid,iid){const p=get(pid);if(!p)return;p.items=p.items.filter(i=>i.id!==iid);p.modificado=hoy();escribir();}
  function tocar(pid){const p=get(pid);if(p){p.modificado=hoy();escribir();}}
  function peor(p){const o={'NO CUMPLE':3,'CUMPLE AL LÍMITE':2,'CUMPLE':1};return p.items.reduce((a,i)=>(o[i.estado]||0)>(o[a]||0)?i.estado:a,'');}
  // miniatura: primer dibujo SVG de la página, sin textos ni cotas y con colores claros
  const PAL={'--conc':'#e7e2d8','--steelf':'#cfd6df','--steel':'#8d99a8','--grout':'#c9c3b4','--bolt':'#444','--tens':'#d92d20','--comp':'#2e6fd0','--ink':'#1b2430','--mut':'#667085','--card':'#ffffff'};
  function miniatura(idx){
    const svgs=document.querySelectorAll('svg[data-sc]');if(!svgs.length)return '';
    let s=svgs[Math.min(idx||0,svgs.length-1)].outerHTML;
    s=s.replace(/<text\b[\s\S]*?<\/text>/g,'').replace(/<path class="dim"[^>]*\/>/g,'').replace(/\sdata-(sc|f)="[^"]*"/g,'')
       .replace(/var\((--[a-z0-9]+)\)/g,(m,v)=>PAL[v]||'#888');
    return s.replace('<svg ','<svg xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid meet" ');
  }
  function params(){const q=new URLSearchParams(location.search);return {proy:q.get('proy'),item:q.get('item'),nuevo:q.get('nuevo')};}
  return {leer,escribir,get,activo,setActivo,crear,borrar,recientes,item,guardarItem,quitarItem,tocar,peor,miniatura,params,uid};
})();
