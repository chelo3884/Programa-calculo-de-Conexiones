"use strict";
/* Herramientas comunes: importar cargas de SAP2000, generar combinaciones NEC y proponer diseño.
   Cada página llama Tools.install({...}) cuando ya cargó su estado; ver xlmodule.js y placa_base.html. */
window.Tools=(()=>{
  const CASOS=['D','L','Lr','S','R','W','E'];
  const NOMBRE_CASO={D:'Carga muerta',L:'Carga viva',Lr:'Viva de cubierta',S:'Nieve / granizo',R:'Lluvia',W:'Viento',E:'Sismo (horizontal)'};
  let cfg=null,dlg=null;
  const post=async(url,body)=>{const r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    const j=await r.json();if(!r.ok)throw new Error(j.error||r.statusText);return j;};
  const q=(s,r=dlg)=>r.querySelector(s);
  const E=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));

  function css(){
    if(document.getElementById('toolsCss'))return;
    const s=document.createElement('style');s.id='toolsCss';
    s.textContent=`dialog.tl{border:1px solid var(--line);border-radius:12px;background:var(--card);color:var(--ink);padding:0;width:min(880px,94vw);max-height:90vh}
    dialog.tl::backdrop{background:rgba(0,0,0,.45)}
    .tl .hd{display:flex;align-items:center;justify-content:space-between;padding:12px 16px;border-bottom:1px solid var(--line)}
    .tl .hd h2{margin:0;font-size:16px}.tl .bd{padding:14px 16px;overflow:auto;max-height:70vh}
    .tl .ft{padding:10px 16px;border-top:1px solid var(--line);display:flex;gap:8px;justify-content:flex-end;flex-wrap:wrap}
    .tl .tb{display:flex;gap:4px;margin-bottom:10px}.tl .tb button.on{background:var(--acc);color:#fff}
    .tl textarea{width:100%;min-height:130px;font:12px ui-monospace,Consolas,monospace;box-sizing:border-box}
    .tl table{font-size:13px}.tl .r{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin:6px 0}
    .tl .warn{background:var(--warnbg);color:var(--warn);padding:8px 10px;border-radius:8px;font-size:12.5px;margin:8px 0}
    .tl .ok{color:var(--ok)}.tl .bad{color:var(--bad)}`;
    document.head.appendChild(s);
  }
  function abrir(titulo,cuerpo,pie){
    css();if(dlg)dlg.remove();
    dlg=document.createElement('dialog');dlg.className='tl';
    dlg.innerHTML=`<div class="hd"><h2>${titulo}</h2><button data-x>✕</button></div><div class="bd">${cuerpo}</div><div class="ft">${pie||''}</div>`;
    document.body.appendChild(dlg);q('[data-x]').onclick=()=>dlg.close();dlg.showModal();return dlg;
  }
  const cols=()=>cfg.cols;
  const fmtv=(v)=>v==null?'':(Math.round(v*1e4)/1e4);

  /* ───────────── Cargas: SAP2000 y NEC ───────────── */
  let preview=[];
  function tablaPrev(list){
    return `<table><tr><th>Combinación</th>${cols().map(c=>`<th class="n">${E(c.label)}</th>`).join('')}</tr>`+
      list.map(r=>`<tr><td>${E(r.nombre)}</td>${cols().map(c=>`<td class="n">${fmtv(r[c.key])}</td>`).join('')}</tr>`).join('')+'</table>';
  }
  function aplicarBotones(){
    const b=q('#applyBox');b.innerHTML=preview.length?`<div class="r"><b>${preview.length} combinaciones</b>
      <button class="pri" data-ap="rep">Reemplazar la tabla</button><button data-ap="add">Agregar a la tabla</button></div>${tablaPrev(preview)}`:'';
    b.querySelectorAll('[data-ap]').forEach(x=>x.onclick=()=>{cfg.setCombos(preview,x.dataset.ap);dlg.close();});
  }
  function cargas(){
    abrir('Cargas — importar de SAP2000 / generar combinaciones NEC',`
      <div class="tb"><button data-t="sap" class="on">Importar de SAP2000</button><button data-t="nec">Generar combinaciones NEC</button></div>
      <div id="p-sap"></div><div id="p-nec" hidden></div><div id="applyBox"></div>`);
    preview=[];
    dlg.querySelectorAll('[data-t]').forEach(b=>b.onclick=()=>{dlg.querySelectorAll('[data-t]').forEach(x=>x.classList.toggle('on',x===b));
      q('#p-sap').hidden=b.dataset.t!=='sap';q('#p-nec').hidden=b.dataset.t!=='nec';preview=[];aplicarBotones();});
    panelSap();panelNec();
  }
  function panelSap(){
    const p=q('#p-sap');
    p.innerHTML=`<p class="note">En SAP2000: <i>Display ▸ Show Tables</i> (p. ej. «Joint Reactions» o «Element Forces – Frames») ▸ <i>Edit ▸ Copy</i>, o exporte a Excel, y pegue aquí
      (con la fila de encabezados y la de unidades). También puede cargar un archivo .csv / .txt.</p>
      <textarea id="sapTxt" placeholder="TABLE:  Joint Reactions&#9;...&#10;Joint&#9;OutputCase&#9;CaseType&#9;StepType&#9;F1&#9;F2&#9;F3&#9;M1&#9;M2&#9;M3"></textarea>
      <div class="r"><input type="file" id="sapFile" accept=".csv,.txt,.tsv,.dat"><button id="sapLeer" class="pri">Leer tabla</button><span id="sapMsg" class="note"></span></div>
      <div id="sapMap"></div>`;
    q('#sapFile').onchange=async e=>{const f=e.target.files[0];if(f){q('#sapTxt').value=await f.text();}};
    q('#sapLeer').onclick=async()=>{
      const m=q('#sapMsg');m.textContent='';
      try{
        const j=await post('/api/sap_parse',{texto:q('#sapTxt').value,claves:cols().map(c=>c.key)});
        mapa(j);m.textContent=`${j.tabla||'Tabla'}: ${j.n} filas, ${j.columnas.length} columnas`+(j.unidades?'':' — sin fila de unidades');
      }catch(e){m.innerHTML=`<span class="bad">${E(e.message)}</span>`;}
    };
  }
  function mapa(j){
    const opt=(sel)=>'<option value="">—</option>'+j.columnas.map(c=>`<option ${c===sel?'selected':''}>${E(c)}</option>`).join('');
    const filas=cols().map(c=>{const m=j.mapa[c.key]||{};
      return `<tr><td>${E(c.label)}</td><td><select data-c="${c.key}">${opt(m.col)}</select></td>
        <td><select data-m="${c.key}"><option value="1">+1</option><option value="-1">−1</option></select></td>
        <td><input type="checkbox" data-a="${c.key}"> |valor|</td></tr>`;}).join('');
    q('#sapMap').innerHTML=`<table><tr><th>Columna de la tabla</th><th>Columna de SAP2000</th><th>Signo</th><th></th></tr>${filas}</table>
      <div class="r"><label>Combinación = columna <select id="sapNom">${opt(j.columnas.find(c=>/case|combo/i.test(c)))}</select></label>
      <label>Filtrar por <select id="sapFcol">${opt('')}</select> = <input id="sapFval" size="8" placeholder="p. ej. 12"></label></div>
      <div class="r"><label>Si la tabla no trae unidades: fuerza <select id="sapF"><option>Tonf</option><option>kN</option><option>kgf</option><option>N</option><option>kip</option><option>lb</option></select>
      longitud <select id="sapL"><option>m</option><option>cm</option><option>mm</option><option>in</option><option>ft</option></select></label>
      <button id="sapImp" class="pri">Convertir</button><span id="sapMsg2" class="note"></span></div>
      <p class="note">Los valores se convierten a Tonf y Tonf·m. Revise el signo de cada columna: en las reacciones de SAP2000 F3 positivo es hacia arriba (compresión en una columna sobre su apoyo).</p>`;
    q('#sapImp').onclick=async()=>{
      const mapa={};cols().forEach(c=>{const col=q(`[data-c="${c.key}"]`).value;if(col)mapa[c.key]={col,mult:+q(`[data-m="${c.key}"]`).value,abs:q(`[data-a="${c.key}"]`).checked};});
      const fc=q('#sapFcol').value;
      try{
        const r=await post('/api/sap_import',{texto:q('#sapTxt').value,claves:cols().map(c=>c.key),mapa,nombre_col:q('#sapNom').value||null,
          filtro:fc?{col:fc,valor:q('#sapFval').value}:null,fuerza:q('#sapF').value,longitud:q('#sapL').value,n_max:cfg.nMax});
        preview=r.combos;q('#sapMsg2').innerHTML=r.avisos.map(a=>`<span class="warn" style="display:block">${E(a)}</span>`).join('');
        aplicarBotones();
      }catch(e){q('#sapMsg2').innerHTML=`<span class="bad">${E(e.message)}</span>`;}
    };
  }
  function panelNec(){
    const p=q('#p-nec');
    p.innerHTML=`<div class="warn"><b>Verifique los factores.</b> Se usan las combinaciones LRFD de la NEC-SE-CG (§3.4.3, basadas en ASCE 7-10):
      1.4D · 1.2D+1.6L+0.5máx(Lr,S,R) · 1.2D+1.6máx(Lr,S,R)+máx(L,0.5W) · 1.2D+1.0W+L+0.5máx(Lr,S,R) · 1.2D+1.0E+L+0.2S · 0.9D+1.0W · 0.9D+1.0E.
      No pude contrastarlas con la edición vigente de la norma: confírmelas con su ejemplar de la NEC (y las que incluyan Ω0, ρ o Ev).</div>
      <p class="note">Ingrese las cargas SIN factorar de cada caso (valores en Tonf y Tonf·m). Los casos en cero se omiten; W y E se invierten (±).</p>
      <table><tr><th>Caso</th>${cols().map(c=>`<th class="n">${E(c.label)}</th>`).join('')}</tr>
      ${CASOS.map(k=>`<tr><td><b>${k}</b> <span class="note">${NOMBRE_CASO[k]}</span></td>${cols().map(c=>`<td><input type="number" step="any" style="width:90px" data-k="${k}" data-c="${c.key}"></td>`).join('')}</tr>`).join('')}</table>
      <div class="r"><label>Sismo: <select id="necModo"><option value="E">E</option><option value="Ω0">Ω0·E (sobrerresistencia)</option><option value="ambos">E y Ω0·E</option></select></label>
      <label>Ω0 <input type="number" step="0.1" value="2.5" id="necO" style="width:70px"></label>
      <label><input type="checkbox" id="necInv" checked> Invertir W y E (±)</label><button id="necGen" class="pri">Generar</button><span id="necMsg" class="note"></span></div>`;
    q('#necGen').onclick=async()=>{
      const cg={};p.querySelectorAll('input[data-k]').forEach(i=>{const v=parseFloat(i.value);if(!isNaN(v)&&v!==0){(cg[i.dataset.k]=cg[i.dataset.k]||{})[i.dataset.c]=v;}});
      try{
        const r=await post('/api/nec_combos',{cargas:cg,columnas:cols().map(c=>c.key),omega0:parseFloat(q('#necO').value)||1,modo_sismo:q('#necModo').value,invertir:q('#necInv').checked});
        preview=r.combos;q('#necMsg').textContent=r.combos.length?'':'No hay cargas: ingrese al menos D.';aplicarBotones();
      }catch(e){q('#necMsg').innerHTML=`<span class="bad">${E(e.message)}</span>`;}
    };
  }

  /* ───────────── Proponer diseño ───────────── */
  let propuesta=null;
  async function auto(){
    abrir('Proponer diseño','<p class="note">Cargando variables…</p>');
    try{
      const j=await post(cfg.api+'/auto',{accion:'vars',inputs:cfg.inputs()});
      const lim=cfg.inputs().lim_verde??0.9;
      q('.bd').innerHTML=`<p class="note">Busca la combinación de menor costo (≈ masa de acero) de las variables marcadas con todos los ratios ≤ el objetivo, usando las cargas de la tabla.
        Las variables no marcadas se mantienen. El costo es una referencia relativa, no un presupuesto.</p>
        <table><tr><th></th><th>Variable</th><th>Actual</th><th>Candidatos</th></tr>${j.variables.map(v=>`<tr><td><input type="checkbox" data-v="${E(v.name)}" checked></td><td>${E(v.label)}</td><td>${E(v.actual)}</td><td class="note">${E(v.cands.join(' · '))}</td></tr>`).join('')}</table>
        <div class="r"><label>Ratio objetivo ≤ <input type="number" id="autoLim" step="0.05" min="0.3" max="1" value="${lim}" style="width:70px"></label><button class="pri" id="autoGo">Buscar</button><span id="autoMsg" class="note"></span></div><div id="autoRes"></div>`;
      q('.ft').innerHTML='';
      q('#autoGo').onclick=async()=>{
        const nombres=[...dlg.querySelectorAll('[data-v]')].filter(x=>x.checked).map(x=>x.dataset.v);
        if(!nombres.length){q('#autoMsg').textContent='Marque al menos una variable.';return;}
        q('#autoMsg').textContent='Buscando…';
        try{
          const r=await post(cfg.api+'/auto',{inputs:cfg.inputs(),nombres,lim:parseFloat(q('#autoLim').value)});
          propuesta=r.propuesta;
          q('#autoMsg').textContent=`${r.evaluaciones} diseños evaluados`;
          q('#autoRes').innerHTML=`<p class="${r.ok?'ok':'bad'}"><b>${E(r.mensaje)}</b> Ratio máx. ${r.ratio_max==null||!isFinite(r.ratio_max)?'—':r.ratio_max.toFixed(2)} · costo relativo ${r.costo}</p>`+
            (r.cambios.length?`<table><tr><th>Variable</th><th>De</th><th>A</th></tr>${r.cambios.map(c=>`<tr><td>${E(c.label)}</td><td>${E(c.de)}</td><td><b>${E(c.a)}</b></td></tr>`).join('')}</table>`:'<p class="note">El diseño actual ya es el de menor costo entre los candidatos.</p>')+
            `<div class="r"><button class="pri" id="autoApply">Aplicar a la conexión</button></div>`;
          q('#autoApply').onclick=()=>{cfg.apply(propuesta);dlg.close();};
        }catch(e){q('#autoMsg').innerHTML=`<span class="bad">${E(e.message)}</span>`;}
      };
    }catch(e){q('.bd').innerHTML=`<p class="bad">${E(e.message)}</p>`;}
  }

  /* ───────────── Reporte de proyecto (varias conexiones) ───────────── */
  const KEY='cx_proyecto';
  const leer=()=>{try{return JSON.parse(localStorage.getItem(KEY)||'null')||{meta:{},items:[]};}catch(e){return {meta:{},items:[]};}};
  function agregarProyecto(){
    if(!cfg.reporte||!cfg.res())return;
    const nombre=prompt('Nombre de esta conexión en el proyecto (si ya existe con el mismo nombre se reemplaza):',cfg.etiqueta()||cfg.titulo);
    if(nombre===null)return;
    const html=cfg.reporte(),st=/<style>([\s\S]*?)<\/style>/.exec(html),bd=/<body>([\s\S]*)<\/body>/.exec(html);
    const R=cfg.res(),cs=(R.checks||[]).filter(c=>c.ratio!=null),gob=cs.reduce((a,c)=>!a||c.ratio>a.ratio?c:a,null);
    const item={id:Date.now().toString(36),modulo:cfg.modulo,titulo:cfg.titulo,etiqueta:nombre.trim()||cfg.titulo,estado:R.resumen.estado,
      ratio:R.resumen.ratio_max,gob:gob?{nombre:gob.nombre,combo:gob.combo}:null,estilo:st?st[1]:'',cuerpo:bd?bd[1]:'',
      guardado:cfg.state(),fecha:new Date().toISOString().slice(0,10)};
    const P=leer(),i=P.items.findIndex(x=>x.modulo===item.modulo&&x.etiqueta===item.etiqueta);
    if(i>=0){item.id=P.items[i].id;P.items[i]=item;}else P.items.push(item);
    try{localStorage.setItem(KEY,JSON.stringify(P));}
    catch(e){alert('No hay espacio en el navegador para guardar otra conexión. Descargue el proyecto desde la página «Proyecto» y vacíelo.');return;}
    abrir('Proyecto',`<p><b>${E(item.etiqueta)}</b> quedó guardada (${P.items.length} conexión${P.items.length>1?'es':''} en el proyecto). Es una copia fija del reporte actual: si cambia el diseño, vuelva a agregarla con el mismo nombre.</p>`,
      '<a class="btn pri" href="/proyecto.html" style="text-decoration:none">Ir al reporte de proyecto</a>');
  }

  function install(c){
    cfg=c;
    const add=document.getElementById('addCombo');
    if(add&&cfg.cols&&cfg.cols.length&&!document.getElementById('btnCargas')){
      const b=document.createElement('button');b.id='btnCargas';b.textContent='Importar SAP2000 / Generar NEC…';b.style.marginLeft='8px';b.onclick=cargas;add.after(b);}
    const th=document.getElementById('btnTheme');
    if(th&&cfg.reporte&&!document.getElementById('btnProy')){
      const b=document.createElement('button');b.id='btnProy';b.textContent='＋ Proyecto';b.title='Agregar esta conexión al reporte de proyecto';b.onclick=agregarProyecto;th.before(b);}
    if(th&&!document.getElementById('btnDxf')){
      const sc=document.createElement('script');sc.src='/dxf.js';document.head.appendChild(sc);
      const b=document.createElement('button');b.id='btnDxf';b.textContent='Exportar DXF';b.title='Dibujos de la página en DXF (mm, 1:1)';
      b.onclick=()=>window.DXF&&DXF.descargar((cfg.archivo||document.title.replace(/[^\w]+/g,'_'))+'.dxf');th.before(b);}
    if(th&&cfg.api&&!document.getElementById('btnAuto')){
      const b=document.createElement('button');b.id='btnAuto';b.textContent='Proponer diseño';b.onclick=auto;th.before(b);}
  }
  return {install};
})();
