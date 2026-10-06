"use strict";
/* Página genérica de un módulo generado desde Excel (end_plate, bfp, rodilla).
   Requiere common.js y un script que defina `MODULE` (ver mod_*.js). */
let SPEC=null, S=null, RES=null, seq=0, timer=null;
const ARMADO='ARMADO (flejes soldados)';
const HASC=()=>!!(SPEC&&SPEC.combos);
const SKEY=()=>'xl_'+MODULE.id;

document.title='Conexiones — '+MODULE.title;
document.body.innerHTML=`
<header>
  <div><h1><a href="/" style="color:inherit;text-decoration:none" title="Volver a los módulos">⌂</a> ${MODULE.title}</h1>
  <div class="sub" id="norma"></div></div>
  <span id="badge" class="badge b-na">—</span><div class="sp"></div>
  <button id="btnOpen">Abrir…</button><button id="btnSave">Guardar proyecto</button>
  <button id="btnTheme" title="Tema claro/oscuro">◐</button><button class="pri" id="btnReport">Reporte</button>
  <input type="file" id="fileIn" accept=".json" hidden>
</header>
<nav id="tabs"><button data-t="dis" class="on">Diseño</button><button data-t="car" id="tabCar">Cargas</button>
  <button data-t="mem">Memoria de cálculo</button><button data-t="uni">Unidades</button><button data-t="rep">Reporte</button></nav>
<main><div id="err" class="err"></div>
<section class="tab on" id="t-dis"><div class="grid"><div id="inputs"></div><div>
  <div class="card"><h2>Geometría (se actualiza al mover los parámetros)</h2><div class="two" id="svgs"></div></div>
  <div class="card"><h2>Verificaciones</h2><div style="overflow:auto"><table id="tblChecks"></table></div>
  <div class="note" style="margin-top:6px">Ratio = demanda / capacidad de diseño (o requerido / provisto). Verde ≤ límite · Ámbar entre el límite y 1.00 · Rojo &gt; 1.00.</div></div>
</div></div></section>
<section class="tab" id="t-car"><div class="card"><h2>Solicitaciones (LRFD)</h2><div id="comboNote" class="note" style="margin-bottom:8px"></div>
  <div style="overflow:auto"><table class="cmb" id="tblCombos"></table></div>
  <div style="margin:8px 0"><button id="addCombo">+ Agregar combinación</button></div>
  <p class="note" id="comboHelp"></p></div></section>
<section class="tab" id="t-mem"><div class="card"><h2>Memoria de cálculo detallada</h2><div id="memoria"></div></div></section>
<section class="tab" id="t-uni"><div class="card"><h2>Sistema de unidades</h2>
  <div class="row" style="grid-template-columns:200px 220px"><label>Preajuste</label><select id="preset"></select></div>
  <div class="ucard" id="unitSel"></div>
  <p class="note">Las unidades se aplican a los datos de entrada, resultados, dibujos y reporte. El cálculo es el mismo en cualquier sistema.</p></div></section>
<section class="tab" id="t-rep"><div class="card"><h2>Reporte de diseño</h2>
  <div style="margin-bottom:8px;display:flex;gap:8px;flex-wrap:wrap"><button class="pri" id="repPrint">Imprimir / Guardar PDF</button><button id="repDl">Descargar HTML</button>
  <button id="repDocx">Descargar Word (.docx)</button><label class="note"><input type="checkbox" id="repMem"> incluir memoria detallada</label><span id="repMsg" class="note"></span></div>
  <iframe id="repFrame" title="Reporte"></iframe></div></section>
</main>`;
document.getElementById('svgs').innerHTML=(MODULE.svgs||[]).map(s=>`<div id="${s.id}"></div>`).join('');

/* ═════════════ Estado ═════════════ */
function defaultState(){
  const s={};for(const sec of SPEC.secciones)for(const c of sec.campos)s[c.name]=c.default;
  if(HASC())s.combos=SPEC.combos.filas.filter(f=>(f.nombre&&!/^C\d+$/.test(f.nombre))||SPEC.combos.cols.some(c=>c.key!=='nombre'&&f[c.key]!=null&&f[c.key]!==0)).map(f=>({...f}));
  return s;
}
function fieldVisible(f){
  if(f.armado_de&&S[f.armado_de]!==ARMADO)return false;
  return MODULE.visible?MODULE.visible(f,S):true;
}
const unitQ=u=>qOfUnit(u);
const D=k=>RES&&RES.derivados?RES.derivados[k]:null;
const n0=(v,q)=>{if(v==null)return '—';const f=uf(q).f*v;return String(Math.abs(f)>=100?Math.round(f):R6(f));};

/* ═════════════ Entradas ═════════════ */
function renderInputs(){
  const box=document.getElementById('inputs');box.innerHTML='';
  for(const sec of SPEC.secciones){
    const c=document.createElement('div');c.className='card';c.innerHTML=`<h2>${sec.titulo}</h2>`;
    // campos y valores derivados, intercalados por fila de la hoja
    const items=sec.campos.map(f=>({row:f.row,tipo:'campo',f}));
    const grupos={};
    for(const d of (sec.derivados||[])){(grupos[d.row]=grupos[d.row]||[]).push(d);}
    for(const [row,ds] of Object.entries(grupos))items.push({row:+row,tipo:'derivado',ds});
    items.sort((a,b)=>a.row-b.row||(a.tipo==='campo'?-1:1));
    for(const it of items){
      if(it.tipo==='derivado'){
        const hayArmado=sec.campos.some(f=>f.row===it.row&&f.armado_de&&S[f.armado_de]===ARMADO);
        if(hayArmado||(MODULE.hideDerived&&MODULE.hideDerived(it.ds[0].name,S)))continue;
        const q=unitQ(it.ds[0].unit),rr=document.createElement('div');rr.className='row';rr.style.gridTemplateColumns='1fr 215px 0';
        rr.innerHTML=`<label class="note">${it.ds[0].label}</label><input readonly data-ro="${it.ds.map(d=>d.name).join(',')}" data-q="${q}" value="${esc(roText(it.ds,q))}"><span></span>`;c.appendChild(rr);continue;}
      const f=it.f;if(!fieldVisible(f))continue;
      const r=document.createElement('div');r.className='row';
      const q=unitQ(f.unit);
      r.innerHTML=`<label>${(MODULE.labels&&MODULE.labels[f.name])||f.label}</label><span></span><span class="u">${q?uf(q).l:(f.unit||'')}</span>`;
      const holder=r.children[1];let el;
      const rebuild=()=>{if((MODULE.rebuild||[]).includes(f.name)||f.name.endsWith('_perfil'))renderInputs();};
      if(f.options&&typeof f.options[0]==='number'){
        el=document.createElement('input');el.type='number';el.step='any';
        const fac=q?uf(q).f:1;el.value=R6(S[f.name]*fac);const dl='dl_'+f.name;el.setAttribute('list',dl);
        const dlo=document.createElement('datalist');dlo.id=dl;dlo.innerHTML=f.options.map(o=>`<option value="${R6(o*fac)}">`).join('');holder.appendChild(dlo);
        el.oninput=()=>{const v=parseFloat(el.value);if(isNaN(v))return;S[f.name]=v/fac;changed();};
      }else if(f.options){
        el=document.createElement('select');
        const armF=SPEC.secciones.flatMap(x=>x.campos).filter(x=>x.armado_de===f.name);
        const loc=(armF.length&&window.PerfilesLocales)?PerfilesLocales.opciones(f.name.startsWith('hss')?'HSS':'I'):[];
        el.innerHTML=f.options.map(o=>`<option value="${esc(o)}">${esc(o)}</option>`).join('')+
          (loc.length?`<optgroup label="Perfiles locales">${loc.map(o=>`<option value="${esc(o.value)}">${esc(o.text)}</option>`).join('')}</optgroup>`:'');
        el.value=S[f.name];
        el.onchange=()=>{
          if(el.value.startsWith('LOCAL:')){const p=PerfilesLocales.dims(el.value);
            if(p){S[f.name]=ARMADO;const v=f.name.startsWith('hss')?[p.d,p.bf,p.tf]:[p.d,p.bf,p.tw,p.tf];
              armF.forEach((a,i)=>{if(v[i]!=null)S[a.name]=v[i];});}
            renderInputs();changed();return;}
          S[f.name]=el.value;rebuild();changed();};
      }else if(f.kind==='text'){
        el=document.createElement('input');el.type='text';el.value=S[f.name];
        el.oninput=()=>{S[f.name]=el.value;saveLocal();};r.style.gridTemplateColumns='1fr 215px 0';
      }else{
        el=document.createElement('input');el.type='number';el.step='any';
        const fac=q?uf(q).f:1;el.value=R6(S[f.name]*fac);
        el.oninput=()=>{const v=parseFloat(el.value);if(isNaN(v))return;S[f.name]=(f.name==='n_b'||/^(nfila|w_n)$/.test(f.name))?Math.round(v/fac):v/fac;changed();};
      }
      el.dataset.p=f.name;holder.appendChild(el);c.appendChild(r);
    }
    box.appendChild(c);
  }
}
function roText(ds,q){
  const vals=ds.map(d=>{const v=D(d.name);return v==null?'—':(q?n0(v,q):String(R6(v)));});
  const u=q?' '+uf(q).l:(ds[0].unit||'');return vals.join(' / ')+u;
}
function refreshRO(){document.querySelectorAll('#inputs input[data-ro]').forEach(i=>{
  const names=i.dataset.ro.split(','),q=i.dataset.q;
  i.value=names.map(n=>{const v=D(n);return v==null?'—':(q?n0(v,q):String(R6(v)));}).join(' / ')+(q?' '+uf(q).l:'');});}

/* ═════════════ Cálculo (Python) ═════════════ */
function changed(){saveLocal();clearTimeout(timer);timer=setTimeout(calc,120);}
async function calc(){
  const id=++seq,err=document.getElementById('err');
  try{
    const r=await fetch(MODULE.api+'/calc',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(S)});
    const j=await r.json();if(id!==seq)return;
    if(!r.ok){err.style.display='block';err.textContent='Error de datos: '+j.error;return;}
    err.style.display='none';RES=j;renderAll();
  }catch(e){err.style.display='block';err.textContent='No se pudo contactar el servidor: '+e;}
}
function drawAll(){for(const s of (MODULE.svgs||[])){try{document.getElementById(s.id).innerHTML=s.fn(RES,S);}catch(e){document.getElementById(s.id).innerHTML='<p class="note">Dibujo no disponible para estos datos.</p>';}}}
function renderAll(){
  const b=document.getElementById('badge'),rs=RES.resumen;
  const cls=rs.estado==='CUMPLE'?'b-ok':rs.estado==='CUMPLE AL LÍMITE'?'b-warn':rs.estado==='NO CUMPLE'?'b-bad':'b-na';
  b.className='badge '+cls;
  b.textContent=(rs.estado==='NO CUMPLE'?'✖ ':rs.estado==='SIN CARGAS'?'':rs.estado==='CUMPLE'?'✔ ':'▲ ')+rs.estado+(rs.ratio_max!=null?` — ratio máx. ${rfmt(rs.ratio_max)}`:'');
  refreshRO();renderChecks();if(HASC())renderCombos();renderMemoria();drawAll();
  if(document.getElementById('t-rep').classList.contains('on'))buildReport();
}
function bar(r){if(r==null)return '';const col=r>1?'var(--bad)':r>S.lim_verde?'var(--warn)':'var(--ok)';
  return `<div class="bar"><i style="width:${Math.min(100,r*100)}%;background:${col}"></i></div>`;}
function renderChecks(){
  const hasCombo=RES.checks.some(c=>c.combo&&c.combo!=='—');
  let h=`<tr><th>Verificación</th><th>Referencia</th><th class="n">Demanda</th><th class="n">Capacidad</th><th>Unidad</th><th class="n">Ratio</th><th></th><th>Estado</th>${hasCombo?'<th>Combo</th>':''}</tr>`,g='';
  for(const c of RES.checks){
    if(c.grupo!==g){g=c.grupo;h+=`<tr class="grp"><td colspan="${hasCombo?9:8}">${g}</td></tr>`;}
    const u=c.q?uf(c.q).l:c.unit;
    h+=`<tr><td>${c.nombre}</td><td class="note">${c.ref}</td><td class="n">${c.dem==null?'—':fmt(c.dem,c.q)}</td><td class="n">${c.cap==null?'—':fmt(c.cap,c.q)}</td>
    <td class="note">${u==='-'?'':u}</td><td class="n"><b>${c.ratio==null?'—':rfmt(c.ratio)}</b></td><td>${bar(c.ratio)}</td>
    <td><span class="st s-${c.estado.replace(' ','-')}">${c.estado}</span></td>${hasCombo?`<td class="note">${c.combo}</td>`:''}</tr>`;
  }
  document.getElementById('tblChecks').innerHTML=h;
}

/* ═════════════ Cargas ═════════════ */
function colInfo(col){ // etiqueta con unidad actual y magnitud de la columna de la tabla de combinaciones
  if(col.key==='nombre')return {q:'',label:col.label};
  const m=col.label.match(/\(([^)]+)\)/);const q=m?unitQ(m[1]):'';
  return {q,label:m&&q?col.label.replace(m[0],`(${uf(q).l})`):col.label};
}
function renderCombos(){
  const cols=SPEC.combos.cols,extra=MODULE.comboCols||[];
  document.getElementById('comboNote').innerHTML=MODULE.comboNote?MODULE.comboNote(S):'';
  document.getElementById('comboHelp').textContent=MODULE.comboHelp||'Las filas con cargas en cero se ignoran.';
  const t=document.getElementById('tblCombos'),res=i=>RES&&RES.combos[i];
  const cell=(rc,x)=>{const v=rc&&rc.activo&&rc.vals[x.sym];if(v&&x.text)return x.text(v.val);return v&&v.val!=null&&typeof v.val!=='boolean'?(typeof v.val==='number'?fmt(v.val,x.q||v.q):v.val):'—';};
  if(t.contains(document.activeElement)&&document.activeElement.tagName==='INPUT'){
    [...t.querySelectorAll('tr')].slice(1).forEach((tr,i)=>{const rc=res(i);if(!rc)return;let k=cols.length+1;
      for(const x of extra)tr.children[k++].textContent=cell(rc,x);
      tr.children[k].innerHTML=rc.activo&&rc.ratio_max!=null?'<b>'+rfmt(rc.ratio_max)+'</b>':'—';});return;}
  let h='<tr><th>#</th>'+cols.map(c=>`<th class="${c.key==='nombre'?'':'n'}">${colInfo(c).label}</th>`).join('')+extra.map(x=>`<th class="n">${x.label.replace('{u}',x.q?uf(x.q).l:'')}</th>`).join('')+'<th class="n">Ratio máx.</th><th></th></tr>';
  S.combos.forEach((cb,i)=>{const rc=res(i);
    h+=`<tr><td>${i+1}</td>`+cols.map(c=>{const ci=colInfo(c);
      return c.key==='nombre'?`<td><input data-i="${i}" data-k="nombre" value="${esc(cb.nombre||'')}"></td>`
        :`<td><input type="number" step="any" data-i="${i}" data-k="${c.key}" value="${R6((cb[c.key]||0)*(ci.q?uf(ci.q).f:1))}"></td>`;}).join('')
      +extra.map(x=>`<td class="n">${cell(rc,x)}</td>`).join('')
      +`<td class="n">${rc&&rc.activo&&rc.ratio_max!=null?'<b>'+rfmt(rc.ratio_max)+'</b>':'—'}</td><td><button data-del="${i}" title="Eliminar">✕</button></td></tr>`;});
  t.innerHTML=h;
}
document.addEventListener('input',e=>{const el=e.target;if(el.dataset.i===undefined||el.dataset.k===undefined)return;
  const c=S.combos[+el.dataset.i],k=el.dataset.k;
  if(k==='nombre')c.nombre=el.value;else{const col=SPEC.combos.cols.find(x=>x.key===k),q=colInfo(col).q;const v=parseFloat(el.value);c[k]=isNaN(v)?0:v/(q?uf(q).f:1);}
  changed();});
document.addEventListener('click',e=>{if(e.target.dataset.del!==undefined){S.combos.splice(+e.target.dataset.del,1);renderCombos();changed();}});

/* ═════════════ Memoria ═════════════ */
function memoTable(rows){
  let h='',sec='';
  for(const r of rows){
    if(r.sec!==sec){sec=r.sec;h+=`<tr class="grp"><td colspan="4">${esc(sec)}</td></tr>`;}
    const u=r.q?uf(r.q).l:(r.unit==='-'?'':r.unit);
    h+=`<tr><td class="sym">${esc(r.sym)}</td><td>${esc(r.desc)}</td><td class="n">${typeof r.val==='number'?fmt(r.val,r.q):(r.val==null?'—':esc(r.val))}</td><td class="note">${u}</td></tr>`;
  }
  return `<table class="memo"><tr><th>Símbolo</th><th>Descripción</th><th class="n">Valor</th><th>Unidad</th></tr>${h}</table>`;
}
function renderMemoria(){
  let h=`<details open><summary>Parámetros y resistencias${HASC()?' (independientes de la combinación)':''}</summary>${memoTable(RES.memoria_global)}</details>`;
  RES.combos.forEach(c=>{if(c.activo)h+=`<details><summary>${esc(c.nombre)} — ratio máx. ${rfmt(c.ratio_max)}</summary>${memoTable(c.trace)}</details>`;});
  document.getElementById('memoria').innerHTML=h;
}

/* ═════════════ Reporte ═════════════ */
function buildReport(){document.getElementById('repFrame').srcdoc=reportHTML();}
function reportHTML(){
  const rs=RES.resumen,date=new Date().toLocaleDateString('es-EC',{year:'numeric',month:'long',day:'numeric'});
  let inputs='';
  for(const sec of SPEC.secciones){
    const rows=sec.campos.filter(fieldVisible).map(f=>{const q=unitQ(f.unit),v=S[f.name];
      const val=typeof v==='number'?(q?fmt(v,q):R6(v)):esc(v);return `<tr><td>${esc((MODULE.labels&&MODULE.labels[f.name])||f.label)}</td><td class="n"><b>${val}${q?' '+uf(q).l:''}</b></td></tr>`;});
    inputs+=`<h3>${sec.titulo}</h3><table>${rows.join('')}</table>`;
  }
  const hasCombo=RES.checks.some(c=>c.combo&&c.combo!=='—');
  let checks='',g='';
  for(const c of RES.checks){
    if(c.grupo!==g){g=c.grupo;checks+=`<tr class="grp"><td colspan="${hasCombo?8:7}">${g}</td></tr>`;}
    checks+=`<tr><td>${c.nombre}</td><td>${c.ref}</td><td class="n">${c.dem==null?'—':fmt(c.dem,c.q)}</td><td class="n">${c.cap==null?'—':fmt(c.cap,c.q)}</td><td>${c.q?uf(c.q).l:(c.unit==='-'?'':c.unit)}</td>
    <td class="n"><b>${rfmt(c.ratio)}</b></td><td class="s ${c.estado.replace(' ','-')}">${c.estado}</td>${hasCombo?`<td>${c.combo}</td>`:''}</tr>`;}
  let combos='';
  if(HASC()){
    const cols=SPEC.combos.cols,extra=MODULE.comboCols||[];
    combos=`<h3>Solicitaciones</h3><table><tr><th>Combinación</th>${cols.filter(c=>c.key!=='nombre').map(c=>`<th class="n">${colInfo(c).label}</th>`).join('')}${extra.map(x=>`<th class="n">${x.label.replace('{u}',x.q?uf(x.q).l:'')}</th>`).join('')}<th class="n">Ratio máx.</th></tr>`;
    S.combos.forEach((cb,i)=>{const rc=RES.combos[i];if(!rc||!rc.activo)return;
      combos+=`<tr><td>${esc(rc.nombre||cb.nombre)}</td>${cols.filter(c=>c.key!=='nombre').map(c=>{const q=colInfo(c).q;return `<td class="n">${fmt(cb[c.key]||0,q)}</td>`;}).join('')}`
        +extra.map(x=>{const v=rc.vals[x.sym];return `<td class="n">${v&&x.text?x.text(v.val):(v&&typeof v.val==='number'?fmt(v.val,x.q||v.q):'—')}</td>`;}).join('')+`<td class="n">${rfmt(rc.ratio_max)}</td></tr>`;});
    combos+='</table>';
  }
  const memo=rows=>{let h='',sec='';for(const r of rows){if(r.sec!==sec){sec=r.sec;h+=`<tr class="grp"><td colspan="4">${esc(sec)}</td></tr>`;}
    h+=`<tr><td class="m">${esc(r.sym)}</td><td>${esc(r.desc)}</td><td class="n">${typeof r.val==='number'?fmt(r.val,r.q):(r.val==null?'—':esc(r.val))}</td><td>${r.q?uf(r.q).l:(r.unit==='-'?'':r.unit)}</td></tr>`;}return `<table>${h}</table>`;};
  let memos=`<h3>Parámetros y resistencias</h3>${memo(RES.memoria_global)}`;
  RES.combos.forEach(c=>{if(c.activo)memos+=`<h3>${esc(c.nombre)}</h3>${memo(c.trace)}`;});
  const css=`body{font:12px/1.4 "Segoe UI",Arial,sans-serif;color:#111;margin:22px 30px;max-width:980px}
  h1{font-size:19px;margin:0 0 2px;color:#1f4e8c}h2{font-size:14px;border-bottom:2px solid #1f4e8c;padding-bottom:2px;margin:20px 0 8px;color:#1f4e8c}h3{font-size:12.5px;margin:12px 0 4px}
  table{border-collapse:collapse;width:100%;margin-bottom:6px}td,th{border-bottom:1px solid #d5dbe3;padding:3px 6px;text-align:left}th{background:#eef2f7;font-size:11px}
  .n{text-align:right;font-variant-numeric:tabular-nums}.grp td{background:#e8f0fb;font-weight:700;color:#1f4e8c}.m{font-family:Consolas,monospace;white-space:nowrap}
  .s{font-weight:700;white-space:nowrap}.CUMPLE{color:#1a7f4b}.AL-LÍMITE{color:#a76a00}.NO-CUMPLE{color:#b42318}
  .res{padding:8px 12px;border:2px solid;border-radius:8px;font-weight:700;margin:10px 0;display:inline-block}
  .ok{color:#1a7f4b;border-color:#1a7f4b}.wn{color:#a76a00;border-color:#a76a00}.bd{color:#b42318;border-color:#b42318}
  .dr{display:grid;grid-template-columns:1fr 1fr;gap:10px}svg{width:100%;height:auto;background:#fff}
  svg text{fill:#111;font:11px sans-serif}svg .dim{stroke:#667085;stroke-width:.8;fill:none}svg text.dt{fill:#667085;font-size:10.5px}
  .note{color:#555;font-size:11px}.pb{page-break-before:always}.cols{columns:2;column-gap:18px}.cols h3,.cols table{break-inside:avoid}
  @media print{body{margin:10mm}}`;
  const light=t=>t.replaceAll('var(--conc)','#e7e2d8').replaceAll('var(--steelf)','#cfd6df').replaceAll('var(--steel)','#8d99a8').replaceAll('var(--grout)','#c9c3b4')
    .replaceAll('var(--bolt)','#444').replaceAll('var(--tens)','#d92d20').replaceAll('var(--comp)','#2e6fd0').replaceAll('var(--ink)','#111').replaceAll('var(--mut)','#667085').replaceAll('var(--card)','#fff');
  let drawings='';for(const s of (MODULE.svgs||[])){try{drawings+=light(s.fn(RES,S));}catch(e){}}
  const cls=rs.estado==='CUMPLE'?'ok':rs.estado==='NO CUMPLE'?'bd':'wn';
  const notas=(SPEC.notas||[]).filter(n=>!/^Herramienta de apoyo/.test(n)).map(n=>`<li>${esc(n)}</li>`).join('');
  return `<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Reporte — ${esc(S.DIS_C7)}</title><style>${css}</style></head><body>
  <h1>Memoria de cálculo — ${MODULE.title}</h1><div class="note">${esc(SPEC.norma||'')} · ${date}</div>
  <table style="margin-top:8px"><tr><td>Proyecto</td><td><b>${esc(S.DIS_C7)}</b></td><td>Elemento / nudo</td><td><b>${esc(S.DIS_C8)}</b></td></tr></table>
  <div class="res ${cls}">${rs.estado}${rs.ratio_max!=null?' — ratio máximo '+rfmt(rs.ratio_max):''}</div>
  <h2>1. Datos de entrada</h2><div class="cols">${inputs}</div>${combos}
  <h2>2. Geometría</h2><div class="dr">${drawings}</div>
  <h2>3. Resumen de verificaciones</h2>
  <table><tr><th>Verificación</th><th>Referencia</th><th class="n">Demanda</th><th class="n">Capacidad</th><th>Unidad</th><th class="n">Ratio</th><th>Estado</th>${hasCombo?'<th>Combo</th>':''}</tr>${checks}</table>
  <h2 class="pb">4. Memoria detallada</h2>${memos}
  <h2>5. Alcance y supuestos</h2><ul class="note">${notas}<li>Herramienta de apoyo: la responsabilidad del diseño es del ingeniero que la usa.</li></ul></body></html>`;
}
document.getElementById('btnReport').onclick=()=>tab('rep');
document.getElementById('repPrint').onclick=()=>{const f=document.getElementById('repFrame');f.contentWindow.focus();f.contentWindow.print();};
document.getElementById('repDocx').onclick=async()=>{const m=document.getElementById('repMsg');m.textContent='Generando…';
  try{await Docx.descargar(reportHTML(),`Reporte_${MODULE.id}_${String(S.DIS_C8||'').replace(/\W+/g,'_')}`,{memoria:document.getElementById('repMem').checked,titulo:MODULE.title});m.textContent='';}
  catch(e){m.textContent='Error: '+e.message;}};
document.getElementById('repDl').onclick=()=>{const blob=new Blob([reportHTML()],{type:'text/html'});const a=document.createElement('a');
  a.href=URL.createObjectURL(blob);a.download=`Reporte_${MODULE.id}_${String(S.DIS_C8||'').replace(/\W+/g,'_')}.html`;a.click();};

/* ═════════════ Unidades, proyecto, pestañas ═════════════ */
function renderUnits(){
  const ps=document.getElementById('preset');
  ps.innerHTML='<option value="">Personalizado</option>'+Object.keys(PRESETS).map(k=>`<option>${k}</option>`).join('');
  const m=Object.keys(PRESETS).find(k=>JSON.stringify(PRESETS[k])===JSON.stringify(units));ps.value=m||'';
  ps.onchange=()=>{if(ps.value){units={...PRESETS[ps.value]};unitsChanged();}};
  const box=document.getElementById('unitSel');box.innerHTML='';
  for(const q of Object.keys(UNITS)){const d=document.createElement('div');d.innerHTML=`<label class="note">${UNITS[q].label}</label>`;
    const s=document.createElement('select');s.innerHTML=Object.keys(UNITS[q].opts).map(o=>`<option>${o}</option>`).join('');s.value=units[q];
    s.onchange=()=>{units[q]=s.value;unitsChanged();};d.appendChild(s);box.appendChild(d);}
}
function unitsChanged(){saveLocal();renderUnits();renderInputs();if(RES)renderAll();}
function saveLocal(){try{localStorage.setItem(SKEY(),JSON.stringify({S,units}));}catch(e){}}
document.getElementById('btnSave').onclick=()=>{const blob=new Blob([JSON.stringify({tipo:MODULE.id,version:1,S,units},null,1)],{type:'application/json'});
  const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=`${MODULE.id}_${String(S.DIS_C8||'proyecto').replace(/\W+/g,'_')}.json`;a.click();};
document.getElementById('btnOpen').onclick=()=>document.getElementById('fileIn').click();
document.getElementById('fileIn').onchange=async e=>{const f=e.target.files[0];if(!f)return;
  try{const j=JSON.parse(await f.text());if(!j.S||j.tipo!==MODULE.id)throw new Error('no es un proyecto de este módulo');S={...defaultState(),...j.S};if(j.units)units={...units,...j.units};
    renderUnits();renderInputs();if(HASC())renderCombos();calc();}catch(err){alert('Archivo no válido: '+err.message);}e.target.value='';};
document.getElementById('btnTheme').onclick=toggleTheme;
function tab(t){document.querySelectorAll('nav button').forEach(b=>b.classList.toggle('on',b.dataset.t===t));
  document.querySelectorAll('.tab').forEach(s=>s.classList.toggle('on',s.id==='t-'+t));if(t==='rep'&&RES)buildReport();}
document.getElementById('tabs').onclick=e=>{if(e.target.dataset.t)tab(e.target.dataset.t);};
document.getElementById('addCombo').onclick=()=>{if(S.combos.length>=SPEC.combos.n)return;const c={nombre:'C'+(S.combos.length+1)};for(const col of SPEC.combos.cols)if(col.key!=='nombre')c[col.key]=0;S.combos.push(c);renderCombos();changed();};
(async function init(){
  initTheme();
  for(const u of ['/proy.js','/docx.js','/dxf.js','/tools.js'])await new Promise(ok=>{const sc=document.createElement('script');sc.src=u;sc.onload=ok;sc.onerror=ok;document.head.appendChild(sc);});
  if(window.PerfilesLocales)await PerfilesLocales.cargar();
  SPEC=await (await fetch(MODULE.api+'/spec')).json();
  document.getElementById('norma').textContent=SPEC.norma||'';
  S=defaultState();
  try{
    const q=window.Proy?Proy.params():{},it=q.proy&&q.item?Proy.item(q.proy,q.item):null;
    const st=it?it.guardado:(q.nuevo?null:JSON.parse(localStorage.getItem(SKEY())||'null'));        // «nuevo» = conexión nueva con valores por defecto
    if(st&&st.S){S={...S,...st.S};if(st.units)units={...units,...st.units};}
  }catch(e){}
  if(!HASC()){document.getElementById('tabCar').style.display='none';}
  renderUnits();renderInputs();if(HASC())renderCombos();calc();
  if(window.Tools)Tools.install({
    api:MODULE.api,inputs:()=>S,modulo:MODULE.id,titulo:MODULE.title,reporte:()=>reportHTML(),res:()=>RES,state:()=>({S,units}),
    etiqueta:()=>S.DIS_C8,archivo:'Dibujos_'+MODULE.id,miniatura:0,
    cols:HASC()?SPEC.combos.cols.filter(c=>c.key!=='nombre').map(c=>({key:c.key,label:c.label})):[],nMax:HASC()?SPEC.combos.n:0,
    setCombos(list,modo){const base=modo==='add'?S.combos:[];S.combos=base.concat(list).slice(0,SPEC.combos.n);renderCombos();changed();},
    apply(prop){for(const k in prop)S[k]=prop[k];renderInputs();if(HASC())renderCombos();changed();}});
})();
