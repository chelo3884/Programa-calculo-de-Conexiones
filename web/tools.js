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
    .tl input[type=radio],.tl input[type=checkbox]{width:auto}.tl .ok{color:var(--ok)}.tl .bad{color:var(--bad)}`;
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

  /* ───────────── Barrido de parámetros ───────────── */
  const COL=['var(--acc)','#e07b00','#2e9e6b','#9b59b6','#c0392b','#808080'];
  async function barrido(){
    abrir('Barrido de parámetros','<p class="note">Cargando variables…</p>');
    try{
      const j=await post(cfg.api+'/auto',{accion:'vars',inputs:cfg.inputs()});
      q('.bd').innerHTML=`<p class="note">Varía un parámetro con todo lo demás fijo y grafica el ratio máximo y el de las verificaciones más críticas, para ver cuánto margen hay y cuándo cambia lo que gobierna.</p>
        <div class="r"><label>Variable <select id="bvar">${j.variables.map((v,i)=>`<option value="${i}">${E(v.label)} (actual: ${E(v.actual)})</option>`).join('')}</select></label>
        <label><input type="radio" name="bmod" value="c" checked> candidatos</label>
        <label><input type="radio" name="bmod" value="r"> rango <input id="bmin" type="number" step="any" style="width:80px"> a <input id="bmax" type="number" step="any" style="width:80px"> en <input id="bn" type="number" value="9" min="3" max="40" style="width:56px"> puntos</label>
        <button class="pri" id="bgo">Calcular</button><span id="bmsg" class="note"></span></div><div id="bres"></div>`;
      const sel=()=>j.variables[+q('#bvar').value];
      const ini=()=>{const v=sel(),num=typeof v.actual==='number';q('#bmin').disabled=q('#bmax').disabled=q('#bn').disabled=!num;
        if(num){q('#bmin').value=Math.max(0,v.actual*0.5);q('#bmax').value=v.actual*1.5;}else q('input[name=bmod][value=c]').checked=true;};
      q('#bvar').onchange=ini;ini();
      q('#bgo').onclick=async()=>{
        const v=sel();let vals=v.cands;
        if(q('input[name=bmod]:checked').value==='r'){const a=parseFloat(q('#bmin').value),b=parseFloat(q('#bmax').value),n=Math.max(3,Math.min(40,parseInt(q('#bn').value)||9));
          if(!(b>a)){q('#bmsg').textContent='El máximo debe ser mayor que el mínimo.';return;}
          vals=Array.from({length:n},(_,i)=>R6(a+(b-a)*i/(n-1)));
          if(Number.isInteger(v.actual))vals=[...new Set(vals.map(Math.round))];}
        q('#bmsg').textContent='Calculando…';
        try{const r=await post(cfg.api+'/barrido',{inputs:cfg.inputs(),variable:v.name,valores:vals,top:5});q('#bmsg').textContent='';grafica(r,v);}
        catch(e){q('#bmsg').innerHTML=`<span class="bad">${E(e.message)}</span>`;}
      };
    }catch(e){q('.bd').innerHTML=`<p class="bad">${E(e.message)}</p>`;}
  }
  function grafica(r,v){
    const W=720,H=300,ml=46,mr=14,mt=14,mb=38,n=r.valores.length;
    const todos=[...r.ratio_max,...r.series.flatMap(s=>s.ratios)].filter(x=>x!=null&&isFinite(x));
    const ymax=Math.max(1.2,Math.min(3,Math.max(...todos)*1.05)),X=i=>ml+(n>1?i*(W-ml-mr)/(n-1):0),Y=y=>mt+(H-mt-mb)*(1-Math.min(y,ymax)/ymax);
    const linea=(arr,col,w,dash)=>{let d='',pen=false;arr.forEach((y,i)=>{if(y==null){pen=false;return;}d+=(pen?'L':'M')+X(i).toFixed(1)+' '+Y(y).toFixed(1);pen=true;});
      return `<path d="${d}" fill="none" stroke="${col}" stroke-width="${w}" ${dash?`stroke-dasharray="${dash}"`:''}/>`;};
    let g=`<svg viewBox="0 0 ${W} ${H}" style="background:var(--card)">`;
    for(let t=0;t<=ymax+1e-9;t+=0.25)g+=`<line x1="${ml}" x2="${W-mr}" y1="${Y(t)}" y2="${Y(t)}" stroke="var(--line)"/><text x="${ml-6}" y="${Y(t)+4}" text-anchor="end" style="font-size:10px;fill:var(--mut)">${t.toFixed(2)}</text>`;
    g+=`<line x1="${ml}" x2="${W-mr}" y1="${Y(1)}" y2="${Y(1)}" stroke="var(--bad)" stroke-dasharray="5 3"/><line x1="${ml}" x2="${W-mr}" y1="${Y(r.lim)}" y2="${Y(r.lim)}" stroke="var(--warn)" stroke-dasharray="2 3"/>`;
    const ia=r.valores.findIndex(x=>x===r.actual);if(ia>=0)g+=`<line x1="${X(ia)}" x2="${X(ia)}" y1="${mt}" y2="${H-mb}" stroke="var(--mut)" stroke-dasharray="3 3"/>`;
    r.series.forEach((s,k)=>g+=linea(s.ratios,COL[k+1],1.3,'4 2'));
    g+=linea(r.ratio_max,COL[0],2.6);
    r.ratio_max.forEach((y,i)=>{if(y!=null)g+=`<circle cx="${X(i)}" cy="${Y(y)}" r="3.5" fill="${y>1?'var(--bad)':y>r.lim?'var(--warn)':'var(--ok)'}"/>`;});
    const paso=Math.ceil(n/12);r.valores.forEach((x,i)=>{if(i%paso===0)g+=`<text x="${X(i)}" y="${H-mb+16}" text-anchor="middle" style="font-size:10px;fill:var(--mut)">${E(typeof x==='number'?R6(x):x)}</text>`;});
    g+=`<text x="${(ml+W-mr)/2}" y="${H-4}" text-anchor="middle" style="font-size:11px;fill:var(--ink)">${E(v.label)}</text></svg>`;
    const leyenda=`<div class="r" style="font-size:12px"><span><b style="color:${COL[0]}">━</b> ratio máximo</span>${r.series.map((s,k)=>`<span><b style="color:${COL[k+1]}">╌</b> ${E(s.nombre)}</span>`).join('')}<span class="bad">┄ 1.00</span><span style="color:var(--warn)">┄ objetivo ${r.lim}</span><span class="note">┆ valor actual</span></div>`;
    const tab=`<table><tr><th>${E(v.label)}</th><th class="n">Ratio máx.</th><th>Gobierna</th><th></th></tr>${r.valores.map((x,i)=>`<tr><td>${E(typeof x==='number'?R6(x):x)}${x===r.actual?' <span class="note">(actual)</span>':''}</td><td class="n"><b>${r.ratio_max[i]==null?'—':r.ratio_max[i].toFixed(2)}</b></td><td class="note">${E(r.gobierna[i]||'')}</td><td><button data-use="${i}">Usar</button></td></tr>`).join('')}</table>`;
    q('#bres').innerHTML=g+leyenda+tab;
    q('#bres').querySelectorAll('[data-use]').forEach(b=>b.onclick=()=>{cfg.apply({[r.variable]:r.valores[+b.dataset.use]});dlg.close();});
  }

  /* ───────────── Perfiles locales ───────────── */
  function locales(){return window.LOCALES||[];}
  // opciones para un selector de perfil: tipo 'I' o 'HSS'
  function opcionesLocales(tipo){return locales().filter(p=>p.tipo===tipo).map(p=>({value:'LOCAL:'+p.nombre,text:'★ '+p.nombre}));}
  function dimsLocal(valor){const n=valor.slice(6),p=locales().find(x=>x.nombre===n);return p||null;}
  window.PerfilesLocales={opciones:opcionesLocales,dims:dimsLocal,cargar:async()=>{try{window.LOCALES=(await (await fetch('/api/perfiles')).json()).perfiles||[];}catch(e){window.LOCALES=[];}}};

  /* ───────────── Proyectos ───────────── */
  const esc2=E;
  function toast(html){
    let t=document.getElementById('toastCx');if(!t){t=document.createElement('div');t.id='toastCx';
      t.style.cssText='position:fixed;right:16px;bottom:16px;background:var(--card);border:1px solid var(--ok);color:var(--ink);padding:10px 14px;border-radius:10px;box-shadow:0 4px 18px rgba(0,0,0,.25);z-index:50;max-width:380px';document.body.appendChild(t);}
    t.innerHTML=html;t.style.display='block';clearTimeout(t._h);t._h=setTimeout(()=>t.style.display='none',6500);
  }
  function proyActual(){const q=Proy.params();return Proy.get(q.proy)||Proy.activo();}
  function etiquetaBoton(){
    const b=document.getElementById('btnProy');if(!b)return;
    const p=proyActual(),q=Proy.params(),it=p&&q.item?Proy.item(p.id,q.item):null;
    b.textContent=p?(it?`Guardar en «${p.nombre}»`:`＋ Agregar a «${p.nombre}»`):'＋ Agregar a un proyecto';
    b.className=it?'pri':'';
    const c=document.getElementById('btnProyCambiar');if(c)c.textContent=p?'Proyecto: '+p.nombre+' ▾':'Elegir proyecto ▾';
  }
  function elegirProyecto(cb){
    const P=Proy.leer();
    abrir('Elegir proyecto',`<p class="note">Las conexiones se guardan dentro de un proyecto; el reporte reúne todas las de un mismo proyecto.</p>
      ${P.proyectos.length?`<table>${Proy.recientes().map(p=>`<tr><td><label><input type="radio" name="pj" value="${p.id}" ${p.id===(proyActual()||{}).id?'checked':''}> <b>${E(p.nombre)}</b></label></td><td class="note">${p.items.length} conexión(es)</td></tr>`).join('')}</table>`:'<p class="note">Aún no hay proyectos.</p>'}
      <div class="r"><label>Nuevo proyecto: <input id="pjNom" placeholder="p. ej. Edificio Quito Norte" style="width:260px"></label></div>`,
      '<button class="pri" id="pjOk">Aceptar</button>');
    q('#pjOk').onclick=()=>{
      const nom=q('#pjNom').value.trim();let pid;
      if(nom){pid=Proy.crear(nom).id;}else{const r=dlg.querySelector('input[name=pj]:checked');if(!r){q('#pjNom').focus();return;}pid=r.value;}
      Proy.setActivo(pid);dlg.close();
      const u=new URL(location.href);u.searchParams.set('proy',pid);u.searchParams.delete('item');history.replaceState(null,'',u);
      etiquetaBoton();if(cb)cb(pid);};
  }
  function guardarEnProyecto(){
    if(!cfg.reporte||!cfg.res())return;
    const q=Proy.params();let p=proyActual();
    if(!p)return elegirProyecto(()=>guardarEnProyecto());
    const previo=q.item?Proy.item(p.id,q.item):null;
    let nombre=previo?previo.etiqueta:prompt('Nombre de esta conexión en «'+p.nombre+'»:',cfg.etiqueta()||cfg.titulo);
    if(nombre===null)return;nombre=(nombre||'').trim()||cfg.titulo;
    const html=cfg.reporte(),st=/<style>([\s\S]*?)<\/style>/.exec(html),bd=/<body>([\s\S]*)<\/body>/.exec(html);
    const R=cfg.res(),cs=(R.checks||[]).filter(c=>c.ratio!=null),gob=cs.reduce((a,c)=>!a||c.ratio>a.ratio?c:a,null);
    const it={id:previo?previo.id:Proy.uid(),modulo:cfg.modulo,titulo:cfg.titulo,etiqueta:nombre,estado:R.resumen.estado,ratio:R.resumen.ratio_max,
      gob:gob?{nombre:gob.nombre,combo:gob.combo}:null,estilo:st?st[1]:'',cuerpo:bd?bd[1]:'',thumb:Proy.miniatura(cfg.miniatura||0),
      guardado:cfg.state(),fecha:new Date().toISOString().slice(0,10)};
    if(!Proy.guardarItem(p.id,it)){alert('No hay espacio en el navegador para guardar otra conexión. Descargue el proyecto (.json) desde la página del proyecto y quite conexiones que ya no necesite.');return;}
    Proy.setActivo(p.id);
    const u=new URL(location.href);u.searchParams.set('proy',p.id);u.searchParams.set('item',it.id);u.searchParams.delete('nuevo');history.replaceState(null,'',u);
    etiquetaBoton();
    toast(`<b>${E(nombre)}</b> ${previo?'actualizada':'agregada'} en «${E(p.nombre)}» (${Proy.get(p.id).items.length} conexión${Proy.get(p.id).items.length>1?'es':''}).<br>
      <a href="/proyecto.html?id=${p.id}">Ver el proyecto</a> · <a href="/#agregar">Agregar otra conexión</a>`);
  }

  function install(c){
    cfg=c;
    const add=document.getElementById('addCombo');
    if(add&&cfg.cols&&cfg.cols.length&&!document.getElementById('btnCargas')){
      const b=document.createElement('button');b.id='btnCargas';b.textContent='Importar SAP2000 / Generar NEC…';b.style.marginLeft='8px';b.onclick=cargas;add.after(b);}
    const th=document.getElementById('btnTheme');
    if(th&&cfg.api&&!document.getElementById('btnBar')){
      const b=document.createElement('button');b.id='btnBar';b.textContent='Barrido';b.title='Gráfica del ratio al variar un parámetro';b.onclick=barrido;th.before(b);}
    if(th&&cfg.reporte&&!document.getElementById('btnProy')){
      const c=document.createElement('button');c.id='btnProyCambiar';c.title='Proyecto al que se agregan las conexiones';c.onclick=()=>elegirProyecto();th.before(c);
      const b=document.createElement('button');b.id='btnProy';b.title='Guardar esta conexión en el proyecto (se incluye en su reporte)';b.onclick=guardarEnProyecto;th.before(b);etiquetaBoton();}
    if(th&&!document.getElementById('btnDxf')){
      const sc=document.createElement('script');sc.src='/dxf.js';document.head.appendChild(sc);
      const b=document.createElement('button');b.id='btnDxf';b.textContent='Exportar DXF';b.title='Dibujos de la página en DXF (mm, 1:1)';
      b.onclick=()=>window.DXF&&DXF.descargar((cfg.archivo||document.title.replace(/[^\w]+/g,'_'))+'.dxf');th.before(b);}
    if(th&&cfg.api&&!document.getElementById('btnAuto')){
      const b=document.createElement('button');b.id='btnAuto';b.textContent='Proponer diseño';b.onclick=auto;th.before(b);}
  }
  return {install,toast,elegirProyecto};
})();
