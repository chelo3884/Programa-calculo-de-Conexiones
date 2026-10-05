"use strict";
/* Utilidades compartidas por los módulos: unidades, formato, tema. */
// factor: valor_mostrado = valor_canónico × factor
const UNITS = {
  F:  {label:'Fuerza', opts:{'Tonf':1,'kgf':1000,'kN':9.80665,'N':9806.65,'kip':2.204623}},
  M:  {label:'Momento', opts:{'Tonf·m':1,'kgf·cm':1e5,'kgf·m':1000,'kN·m':9.80665,'N·mm':9.80665e6,'kip·in':86.7976,'kip·ft':7.23313}},
  Ls: {label:'Longitud — perfiles, placas, pernos (canónico mm)', opts:{'mm':1,'cm':.1,'m':.001,'in':1/25.4}},
  Lc: {label:'Longitud — distancias y detalles (canónico cm)', opts:{'mm':10,'cm':1,'m':.01,'in':1/2.54}},
  Lm: {label:'Longitud — luces (canónico m)', opts:{'m':1,'cm':100,'mm':1000,'in':39.3701,'ft':3.28084}},
  S:  {label:'Esfuerzo', opts:{'kgf/cm²':1,'MPa':.0980665,'ksi':1/70.307,'Tonf/m²':10,'psi':14.2233}},
};
const MLLAB = {'Tonf':'Tonf·m/m','kgf':'kgf·cm/cm','kN':'kN·m/m','N':'N·mm/mm','kip':'kip·in/in'};
const AREALAB = {'mm':['mm²',100],'cm':['cm²',1],'m':['m²',1e-4],'in':['in²',1/6.4516]};
const VOLLAB = {'mm':['mm³',1e3],'cm':['cm³',1],'m':['m³',1e-6],'in':['in³',1/16.3871]};
const PRESETS = {
  'Tonf · m · mm (predeterminado)':{F:'Tonf',M:'Tonf·m',Ls:'mm',Lc:'cm',Lm:'m',S:'kgf/cm²'},
  'kgf · cm':{F:'kgf',M:'kgf·cm',Ls:'cm',Lc:'cm',Lm:'m',S:'kgf/cm²'},
  'SI (kN · m · mm · MPa)':{F:'kN',M:'kN·m',Ls:'mm',Lc:'mm',Lm:'m',S:'MPa'},
  'US (kip · in · ksi)':{F:'kip',M:'kip·in',Ls:'in',Lc:'in',Lm:'ft',S:'ksi'},
  'Tonf · m · cm':{F:'Tonf',M:'Tonf·m',Ls:'cm',Lc:'cm',Lm:'m',S:'kgf/cm²'},
};
let units = {...Object.values(PRESETS)[0]};
// factor y etiqueta de unidad para la magnitud q (valores canónicos: Tonf, Tonf·m, mm, cm, m, kgf/cm², cm², cm³, kgf/cm)
function uf(q){
  if(q==='ML'){const u=units.F;return {f:UNITS.F.opts[u],l:MLLAB[u]};}
  if(q==='A'){const [l,f]=AREALAB[units.Lc];return {f,l};}
  if(q==='V'){const [l,f]=VOLLAB[units.Lc];return {f,l};}
  if(q==='FL'){return {f:UNITS.F.opts[units.F]/1000/UNITS.Lc.opts[units.Lc],l:`${units.F}/${units.Lc}`};}
  if(UNITS[q]){const u=units[q];return {f:UNITS[q].opts[u],l:u};}
  return {f:1,l:''};
}
function fmt(v,q){
  if(v===null||v===undefined||v==='')return '—';
  if(typeof v==='string')return v;
  const x=q?v*uf(q).f:v, a=Math.abs(x);
  if(!isFinite(x))return '∞';
  if(a===0)return '0';
  if(a>=1000)return x.toFixed(a>=10000?0:1);
  if(a>=100)return x.toFixed(1);
  if(a>=1)return x.toFixed(2);
  if(a>=0.01)return x.toFixed(3);
  return x.toExponential(2);
}
const rfmt=v=>v===null||v===undefined?'—':v.toFixed(2);
function withU(v,q){const u=uf(q);return fmt(v,q)+(u.l?' '+u.l:'');}
const R6=x=>parseFloat(x.toPrecision(6));
const esc=s=>String(s).replace(/[&<>]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[m]));
function qOfUnit(u){return ({'mm':'Ls','m':'Lm','Tonf':'F','Tonf·m':'M','kgf/cm²':'S','cm':'Lc'})[u]||'';}
function initTheme(){try{const th=localStorage.getItem('cx_theme');if(th)document.documentElement.dataset.theme=th;}catch(e){}}
function toggleTheme(){const r=document.documentElement,dark=getComputedStyle(r).getPropertyValue('--bg').trim()==='#12161c';
  r.dataset.theme=dark?'light':'dark';try{localStorage.setItem('cx_theme',r.dataset.theme);}catch(e){}}
