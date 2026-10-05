/* NEXO — interfaz sin frameworks. Funciona con file:// (modo demostración).
   Motor de reglas idéntico a backend/rules.py. Sin fetch locales ni CDNs. */
"use strict";

/* ---------- Muestra sintética (idéntica a backend/sample.py) ---------- */
var META = {
  clientes: { nombre: "Clientes", descripcion: "Personas registradas en la tienda de ejemplo. Base para segmentación y contacto.",
    responsable: "Ana Beltrán — Dominio Comercial", dominio: "Comercial",
    columnas: [{nombre:"id",tipo:"texto"},{nombre:"nombre",tipo:"texto"},{nombre:"email",tipo:"correo"}],
    reglas: ["Obligatoriedad en id, nombre y email", "Unicidad en id", "Formato de correo en email"] },
  pedidos: { nombre: "Pedidos", descripcion: "Compras realizadas por los clientes con fecha e importe total.",
    responsable: "Luis Camargo — Dominio Ventas", dominio: "Ventas",
    columnas: [{nombre:"id",tipo:"texto"},{nombre:"cliente_id",tipo:"texto"},{nombre:"fecha",tipo:"fecha"},{nombre:"total",tipo:"número"}],
    reglas: ["Obligatoriedad en id, cliente_id, fecha y total", "Unicidad en id"] },
  productos: { nombre: "Productos", descripcion: "Catálogo de artículos disponibles para la venta.",
    responsable: "María Solís — Dominio Catálogo", dominio: "Catálogo",
    columnas: [{nombre:"id",tipo:"texto"},{nombre:"nombre",tipo:"texto"},{nombre:"precio",tipo:"número"}],
    reglas: ["Obligatoriedad en id, nombre y precio", "Unicidad en id"] }
};
var SAMPLE = {
  clientes: [
    {row_id:"cli-01",id:"CLI-001",nombre:"Lucía Fernández",email:"lucia.fernandez@example.com"},
    {row_id:"cli-02",id:"CLI-002",nombre:"Marco Ruiz",email:"marco.ruiz@example.com"},
    {row_id:"cli-03",id:"CLI-003",nombre:"Sofía Herrera",email:""},
    {row_id:"cli-04",id:"CLI-004",nombre:"Diego Torres",email:"diego.torres@example.com"},
    {row_id:"cli-05",id:"CLI-004",nombre:"Diego Torres (duplicado)",email:"d.torres2@example.com"},
    {row_id:"cli-06",id:"CLI-006",nombre:"   ",email:"carlos.mendez@example.com"},
    {row_id:"cli-07",id:"CLI-007",nombre:"Ana Gómez",email:"ana.gomez@"},
    {row_id:"cli-08",id:"CLI-008",nombre:"Juan Pérez",email:"juan.perez[at]correo.com"},
    {row_id:"cli-09",id:"CLI-009",nombre:"Valeria Castro",email:"valeria.castro@example.com"},
    {row_id:"cli-10",id:"CLI-010",nombre:"Pedro Sánchez",email:"pedro.sanchez@example.com"},
    {row_id:"cli-11",id:"CLI-011",nombre:"Carmen Díaz",email:"carmen.diaz@example.com"},
    {row_id:"cli-12",id:"CLI-012",nombre:"Raúl Ortega",email:"raul.ortega@example.com"}
  ],
  pedidos: [
    {row_id:"ped-01",id:"PED-001",cliente_id:"CLI-001",fecha:"2026-01-10",total:150.5},
    {row_id:"ped-02",id:"PED-002",cliente_id:"CLI-002",fecha:"2026-01-11",total:0},
    {row_id:"ped-03",id:"PED-003",cliente_id:"",fecha:"2026-01-12",total:89.9},
    {row_id:"ped-04",id:"PED-004",cliente_id:"CLI-004",fecha:"2026-01-13",total:210.0},
    {row_id:"ped-05",id:"PED-005",cliente_id:"CLI-007",fecha:"2026-01-20",total:45.0},
    {row_id:"ped-06",id:"PED-006",cliente_id:"CLI-009",fecha:"2026-02-01",total:320.75},
    {row_id:"ped-07",id:"PED-007",cliente_id:"CLI-010",fecha:"2026-02-03",total:15.0},
    {row_id:"ped-08",id:"PED-008",cliente_id:"CLI-012",fecha:"2026-02-05",total:99.99}
  ],
  productos: [
    {row_id:"pro-01",id:"PRO-001",nombre:"Café Molido 500g",precio:85.5},
    {row_id:"pro-02",id:"PRO-002",nombre:"",precio:120.0},
    {row_id:"pro-03",id:"PRO-003",nombre:"Taza Cerámica",precio:45.0},
    {row_id:"pro-04",id:"PRO-004",nombre:"Filtro Papel x40",precio:30.0},
    {row_id:"pro-05",id:"PRO-005",nombre:"Cafetera Prensa 1L",precio:450.0},
    {row_id:"pro-06",id:"PRO-006",nombre:"Termo Acero 750ml",precio:0}
  ]
};

/* ---------- Reglas (idénticas a backend/rules.py) ---------- */
var RULE_CONFIG = {
  clientes: { id:{required:1,unique:1}, nombre:{required:1}, email:{required:1,email:1} },
  pedidos: { id:{required:1,unique:1}, cliente_id:{required:1}, fecha:{required:1}, total:{required:1} },
  productos: { id:{required:1,unique:1}, nombre:{required:1}, precio:{required:1} }
};
var PRIORITY = { required:"Alta", unique:"Alta", email:"Media" };
var RULE_LABEL = { required:"Obligatoriedad", unique:"Unicidad", email:"Formato de correo" };
var RECOMMENDATIONS = {
  "clientes|id|unique":"Unificar las filas con el mismo id de cliente bajo un único registro maestro y redirigir los pedidos afectados antes del próximo análisis.",
  "clientes|nombre|required":"Completar el nombre faltante desde el formulario de alta y marcar el campo como obligatorio en la captura.",
  "clientes|email|required":"Solicitar el correo faltante al responsable comercial y reintentar el envío de comunicaciones.",
  "clientes|email|email":"Corregir los correos con formato inválido validándolos contra el patrón usuario@dominio.extensión.",
  "pedidos|cliente_id|required":"Asignar el cliente correspondiente a cada pedido sin referencia; bloquear el cierre de pedidos sin cliente.",
  "productos|nombre|required":"Completar el nombre del producto desde el catálogo maestro antes de publicarlo."
};
var EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

function isEmpty(v){
  if (v === null || v === undefined) return true;
  if (typeof v === "number" || typeof v === "boolean") return false; /* 0 no es vacío */
  return String(v).trim() === "";
}
function analyzeTables(tables){
  var checks=0, issues=0, groups={}, affected={};
  function addIssue(t,c,r,row,val){
    issues++;
    var k=t+"|"+c+"|"+r;
    if(!groups[k]) groups[k]={count:0,evidence:[]};
    groups[k].count++;
    groups[k].evidence.push({row_id:row.row_id, valor:(val===undefined?null:val), ref:t+":"+row.row_id});
    affected[t+":"+row.row_id]=1;
  }
  Object.keys(RULE_CONFIG).forEach(function(t){
    var cfg=RULE_CONFIG[t], rows=tables[t]||[];
    rows.forEach(function(row){
      Object.keys(cfg).forEach(function(col){
        var val=row[col];
        if(cfg[col].required){ checks++; if(isEmpty(val)) addIssue(t,col,"required",row,val); }
        if(cfg[col].email && !isEmpty(val)){ checks++; if(!EMAIL_RE.test(String(val).trim())) addIssue(t,col,"email",row,val); }
      });
    });
    Object.keys(cfg).forEach(function(col){
      if(!cfg[col].unique) return;
      var counts={}, order=[];
      rows.forEach(function(row){
        var val=row[col];
        if(isEmpty(val)) return;
        checks++;
        var k=String(val).trim();
        counts[k]=(counts[k]||0)+1; order.push(k);
      });
      rows.forEach(function(row){
        var val=row[col];
        if(isEmpty(val)) return;
        if(counts[String(val).trim()]>1) addIssue(t,col,"unique",row,val);
      });
    });
  });
  var findings=Object.keys(groups).sort().map(function(k){
    var p=k.split("|");
    return { tabla:p[0], columna:p[1], regla:p[2], regla_etiqueta:RULE_LABEL[p[2]],
      prioridad:PRIORITY[p[2]], incidencias:groups[k].count,
      recomendacion: RECOMMENDATIONS[k] || "Revisar los valores señalados con el responsable del dato y registrar la decisión en NEXO.",
      evidencias: groups[k].evidence.sort(function(a,b){return String(a.row_id)<String(b.row_id)?-1:1;}),
      estado:"pending", eventos:[] };
  });
  return { comprobaciones:checks, incidencias:issues,
    indice: checks===0?null:Math.round((checks-issues)/checks*100),
    hallazgos:findings, filas_afectadas:Object.keys(affected).length,
    total_registros:(tables.clientes||[]).length+(tables.pedidos||[]).length+(tables.productos||[]).length };
}

/* ---------- Estado y almacenamiento ---------- */
var state = { mode:"demo", serverMode:null, run:null, runs:[], runSeq:0, storage:"local" };
var LS_KEY = "nexo_demo_runs_v1";

function storageOK(){
  try{ localStorage.setItem("__nexo","1"); localStorage.removeItem("__nexo"); return true; }
  catch(e){ return false; }
}
function notice(msg){ var n=document.getElementById("noticeBar"); n.textContent=msg; n.hidden=!msg; }
function toast(msg){ var t=document.getElementById("toast"); t.textContent=msg; t.hidden=false;
  clearTimeout(t._h); t._h=setTimeout(function(){t.hidden=true;},3200); }
function esc(s){ return String(s===null||s===undefined?"":s).replace(/[&<>"']/g,
  function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c];}); }
function showVal(v){
  if(isEmpty(v) && !(typeof v==="number")) return "<em>— (vacío)</em>";
  return "<code>"+esc(v)+"</code>";
}
function $(id){ return document.getElementById(id); }

/* ---------- Navegación por pestañas ---------- */
var tabs = ["observatorio","catalogo","calidad","decisiones","bitacora","agentes","perfil"];
var SECTIONS = {
  observatorio: ["Observatorio", "Estado general de tus datos y último análisis."],
  catalogo: ["Catálogo", "Activos, responsables y estructura."],
  calidad: ["Calidad", "Hallazgos verificados por las reglas."],
  decisiones: ["Decisiones", "Responde las recomendaciones pendientes."],
  bitacora: ["Bitácora", "Historial de ejecuciones y exportaciones."],
  agentes: ["Agentes", "Trabajos de análisis con IA."],
  perfil: ["Mi perfil", "Tu cuenta y sesión."]
};
function entered(){ return $("welcome").hidden; }
function enterApp(){
  $("welcome").hidden=true;
  showTab("observatorio");
}
function closeNav(){
  document.body.classList.remove("nav-open");
  $("navScrim").hidden=true;
  $("menuBtn").setAttribute("aria-expanded","false");
}
function showTab(name){
  tabs.forEach(function(t){
    $("tab-"+t).hidden = (t!==name);
    var b=document.querySelector('[data-tab="'+t+'"]');
    if(b){ if(t===name) b.setAttribute("aria-current","page"); else b.removeAttribute("aria-current"); }
  });
  var meta=SECTIONS[name]||SECTIONS.observatorio;
  $("sectionTitle").textContent=meta[0];
  $("sectionDesc").textContent=meta[1];
  closeNav();
  if(name==="bitacora") renderRuns();
  if(name==="decisiones") renderDecisions();
  if(name==="calidad") renderQuality();
  if(name==="agentes") renderAgents();
  if(name==="perfil") renderProfile();
}
document.querySelectorAll("[data-tab]").forEach(function(b){
  b.addEventListener("click", function(){ showTab(b.getAttribute("data-tab")); });
});
$("menuBtn").addEventListener("click", function(){
  var open=!document.body.classList.contains("nav-open");
  document.body.classList.toggle("nav-open", open);
  $("navScrim").hidden=!open;
  $("menuBtn").setAttribute("aria-expanded", open?"true":"false");
});
$("navScrim").addEventListener("click", closeNav);
document.addEventListener("click", function(e){
  var t=e.target&&e.target.closest?e.target.closest("[data-goto],[data-clear]"):null;
  if(!t) return;
  if(t.hasAttribute("data-goto")) showTab(t.getAttribute("data-goto"));
  if(t.hasAttribute("data-clear")) clearCatalogFilters();
});

/* ---------- Detección de modo ---------- */
function setModeBadge(){
  var b=$("modeBadge"), f=$("footMode");
  if(state.mode==="demo"){
    b.textContent="Modo demostración — datos de ejemplo";
    f.textContent="modo demostración (navegador, sin servidor)";
  } else if(state.serverMode==="mysql"){
    b.textContent="Modo conectado — PHP · Python · MySQL";
    f.textContent="modo conectado (MySQL)";
  } else {
    b.textContent="Modo local — PHP · Python (memoria)";
    f.textContent="modo local (la memoria se pierde al reiniciar)";
  }
}
function detectMode(){
  if(location.protocol==="file:"){ state.mode="demo"; setModeBadge();
    notice(state.storage==="local" ? "" : "Almacenamiento no disponible: los cambios solo durarán durante la sesión.");
    return Promise.resolve();
  }
  return fetch("api.php?action=health", {cache:"no-store"})
    .then(function(r){ return r.json(); })
    .then(function(h){
      if(h && h.status==="ok"){ state.mode="server"; state.serverMode=h.mode||"demo"; }
      else { state.mode="demo"; }
      setModeBadge();
    })
    .catch(function(){ state.mode="demo"; setModeBadge(); });
}

/* ---------- Análisis ---------- */
function apiPost(action, data){
  return fetch("api.php?action="+action, {method:"POST",
    headers:{"Content-Type":"application/json"}, body:JSON.stringify(data||{})})
    .then(function(r){ return r.json().then(function(j){ return {code:r.status, body:j}; }); });
}
function apiGet(action){
  return fetch("api.php?action="+action, {cache:"no-store"})
    .then(function(r){ return r.json().then(function(j){ return {code:r.status, body:j}; }); });
}
function normalizeServerRun(j){
  return { id:j.run_id, modo:j.modo, creado_en:j.creado_en||new Date().toISOString(),
    total_registros:j.total_registros, comprobaciones:j.comprobaciones,
    incidencias:j.incidencias, indice:j.indice, hallazgos:(j.hallazgos||[]).map(function(h,i){
      return { tabla:h.tabla, columna:h.columna, regla:h.regla,
        regla_etiqueta:h.regla_etiqueta||RULE_LABEL[h.regla], prioridad:h.prioridad||PRIORITY[h.regla],
        incidencias:h.incidencias, recomendacion:h.recomendacion, evidencias:h.evidencias||[],
        estado:h.estado||"pending", ultimo_comentario:h.ultimo_comentario||null, eventos:[] }; }) };
}
function saveLocal(run){
  state.runs.push(run);
  if(state.storage==="local"){
    try{ localStorage.setItem(LS_KEY, JSON.stringify(state.runs.slice(-20))); }
    catch(e){ state.storage="session"; notice("Almacenamiento no disponible: los cambios solo durarán durante la sesión."); }
  }
}
function loadLocal(){
  if(!storageOK()){ state.storage="session"; return; }
  try{
    var arr=JSON.parse(localStorage.getItem(LS_KEY)||"[]");
    if(Array.isArray(arr)){ state.runs=arr;
      arr.forEach(function(r){ if(r.id>state.runSeq) state.runSeq=r.id; });
      if(arr.length) state.run=arr[arr.length-1];
    }
  }catch(e){ state.runs=[]; }
}

function runAnalysis(){
  var btn=$("btnAnalyze"), msg=$("analyzeMsg");
  btn.disabled=true; msg.textContent="Analizando con reglas deterministas…";
  function done(run){
    state.run=run; btn.disabled=false;
    msg.textContent="Análisis completado. "+run.comprobaciones+" comprobaciones, "+
      run.incidencias+" incidencias, índice "+(run.indice===null?"sin evaluar":run.indice+"%")+".";
    renderAll(); toast("Análisis completado: índice "+(run.indice===null?"—":run.indice+"%"));
  }
  function fail(err){
    btn.disabled=false; msg.textContent="";
    renderError("observatorio", err);
  }
  if(state.mode==="server"){
    apiPost("analyze", {}).then(function(res){
      if(res.code>=200&&res.code<300&&res.body.run_id!==undefined) done(normalizeServerRun(res.body));
      else fail(res.body.error||"El servicio no pudo completar el análisis.");
    }).catch(function(){ fail("No se pudo contactar al servicio Python. Revisa que esté en marcha."); });
  } else {
    setTimeout(function(){
      try{
        var r=analyzeTables(JSON.parse(JSON.stringify(SAMPLE)));
        state.runSeq++;
        var run={ id:state.runSeq, modo:"demo",
          creado_en:new Date().toISOString().slice(0,19).replace("T"," "),
          total_registros:r.total_registros, comprobaciones:r.comprobaciones,
          incidencias:r.incidencias, indice:r.indice, hallazgos:r.hallazgos };
        saveLocal(run); done(run);
      }catch(e){ fail("Error interno al analizar la muestra."); }
    }, 350);
  }
}
function renderError(where, msg){
  if(where==="observatorio"){ $("analyzeMsg").textContent="Error: "+msg; }
  toast("Error: "+msg);
}

/* ---------- Observatorio ---------- */
function renderObservatory(){
  var r=state.run;
  $("stAssets").textContent="3";
  $("stRows").textContent=r?r.total_registros:"—";
  $("stFindings").textContent=r?r.hallazgos.length:"—";
  var pend=r?r.hallazgos.filter(function(h){return h.estado==="pending";}).length:0;
  $("stPending").textContent=r?pend:"—";
  $("stLast").textContent=r?r.creado_en:"—";
  var arc=$("gaugeArc"), val=$("gaugeVal"), det=$("gaugeDetail");
  if(!r||r.indice===null){
    arc.style.strokeDashoffset=402; val.textContent="—";
    det.textContent=r&&r.indice===null?"Sin comprobaciones: sin evaluar.":"Sin evaluar. Ejecuta el análisis para calcular el índice con las reglas.";
  } else {
    arc.style.strokeDashoffset=Math.round(402*(1-r.indice/100));
    val.textContent=r.indice+"%";
    det.textContent=r.comprobaciones+" comprobaciones · "+r.incidencias+" incidencias.";
  }
  var ok=r?(r.comprobaciones-r.incidencias):0, pct=r&&r.comprobaciones?Math.round(ok/r.comprobaciones*100):0;
  $("meterOk").style.width=pct+"%";
  $("checksLine").textContent=r?(ok+" de "+r.comprobaciones+" comprobaciones correctas ("+pct+"%)."):"Sin datos todavía.";
  var pl=$("prioList");
  if(!r){ pl.innerHTML="<li class='muted'>Sin datos todavía.</li>"; return; }
  var counts={};
  r.hallazgos.forEach(function(h){ counts[h.prioridad]=(counts[h.prioridad]||0)+h.incidencias; });
  pl.innerHTML=Object.keys(counts).sort().map(function(p){
    return "<li><span>Prioridad "+esc(p)+"</span><strong>"+counts[p]+" incidencias</strong></li>";
  }).join("")||"<li class='muted'>Sin hallazgos: todo en regla.</li>";
}

/* ---------- Catálogo ---------- */
var CAT_TABLES=["clientes","pedidos","productos"];
function renderCatalog(){
  var q=($("catSearch").value||"").toLowerCase(), dom=$("catDomain").value, tab=$("catTable").value;
  var box=$("catalogList"); box.innerHTML="";
  var shown=0;
  CAT_TABLES.forEach(function(t){
    var m=META[t], rows=SAMPLE[t];
    if(dom && m.dominio!==dom) return;
    if(tab && t!==tab) return;
    var hay=[m.nombre,m.descripcion,m.responsable,m.dominio,t].join(" ").toLowerCase();
    var rowsHit=rows.filter(function(r){return Object.values(r).join(" ").toLowerCase().indexOf(q)>=0;});
    if(q && hay.indexOf(q)<0 && rowsHit.length===0) return;
    shown++;
    var d=document.createElement("article"); d.className="asset";
    d.innerHTML=
      "<div class='asset-head'><h2>"+esc(m.nombre)+" <code class='asset-tech'>"+esc(t)+"</code></h2>"+
      "<div class='asset-meta'><span>Dominio: <strong>"+esc(m.dominio)+"</strong></span>"+
      "<span>Responsable: <strong>"+esc(m.responsable)+"</strong></span>"+
      "<span><strong>"+rows.length+"</strong> registros</span></div></div>"+
      "<div class='asset-body'><p>"+esc(m.descripcion)+"</p>"+
      "<ul class='cols'>"+m.columnas.map(function(c){return "<li><strong>"+esc(c.nombre)+"</strong> · "+esc(c.tipo)+"</li>";}).join("")+"</ul>"+
      "<details><summary>Reglas aplicables ("+m.reglas.length+")</summary><ul class='rules'>"+m.reglas.map(function(x){return "<li>"+esc(x)+"</li>";}).join("")+"</ul></details>"+
      "<details><summary>Ver datos sintéticos ("+rowsHit.length+" de "+rows.length+")</summary><div class='table-wrap'><table>"+
      "<thead><tr>"+Object.keys(rows[0]).map(function(k){return "<th>"+esc(k)+"</th>";}).join("")+"</tr></thead>"+
      "<tbody>"+rowsHit.slice(0,50).map(function(r){return "<tr>"+Object.keys(rows[0]).map(function(k){
        return "<td>"+(isEmpty(r[k])&&typeof r[k]!=="number"?showVal(r[k]):esc(r[k]))+"</td>";}).join("")+"</tr>";}).join("")+
      "</tbody></table></div></details></div>";
    box.appendChild(d);
  });
  if(!shown) box.innerHTML="<div class='empty-state'><h2>Sin resultados</h2><p>Prueba con «correo» o limpia los filtros.</p><button class='btn' data-clear='1'>Limpiar filtros</button></div>";
  var active=q||dom||tab;
  $("btnClearFilters").hidden=!active;
}
$("btnClearFilters").addEventListener("click", clearCatalogFilters);
function clearCatalogFilters(){
  $("catSearch").value=""; $("catDomain").value=""; $("catTable").value="";
  renderCatalog();
}
function fillCatalogFilters(){
  var doms=[...new Set(CAT_TABLES.map(function(t){return META[t].dominio;}))];
  doms.forEach(function(d){ var o=document.createElement("option"); o.textContent=d; $("catDomain").appendChild(o); });
  CAT_TABLES.forEach(function(t){ var o=document.createElement("option"); o.value=t; o.textContent=t; $("catTable").appendChild(o); });
}

/* ---------- Calidad ---------- */
function filteredFindings(){
  var r=state.run; if(!r) return [];
  var t=$("fTable").value, p=$("fPrio").value, ru=$("fRule").value;
  return r.hallazgos.filter(function(h){
    return (!t||h.tabla===t)&&(!p||h.prioridad===p)&&(!ru||h.regla===ru);
  });
}
function ruleIcon(rule){ return "<span class='rule-dot rule-"+rule+"' aria-hidden='true'></span>"; }
function renderQuality(){
  var w=$("qualityWrap"), r=state.run, sum=$("qualitySummary");
  if(!r){
    sum.hidden=true;
    w.innerHTML="<div class='empty-state'><h2>Todavía no hay resultados de calidad</h2><p>Ejecuta el análisis para verificar los datos con las reglas.</p><button class='btn primary' data-goto='observatorio'>Ir a ejecutar análisis</button></div>";
    return;
  }
  var list=filteredFindings();
  var tot=list.reduce(function(a,h){return a+h.incidencias;},0);
  sum.hidden=false;
  sum.textContent=list.length+" hallazgos · "+tot+" incidencias.";
  if(!list.length){ w.innerHTML="<div class='empty-state'><h2>Sin hallazgos para esos filtros</h2><p>Ajusta tabla, prioridad o tipo de problema.</p></div>"; return; }
  var html="<table><thead><tr><th>Hallazgo</th><th>Tabla · columna</th><th>Prioridad</th><th>Incidencias</th><th>Estado</th><th></th></tr></thead><tbody>";
  list.forEach(function(h,i){
    var idx=r.hallazgos.indexOf(h);
    html+="<tr><td><strong>"+ruleIcon(h.regla)+esc(h.regla_etiqueta)+"</strong></td>"+
      "<td>"+esc(h.tabla)+" · <strong>"+esc(h.columna)+"</strong></td>"+
      "<td><span class='badge "+h.prioridad.toLowerCase()+"'>"+esc(h.prioridad)+"</span></td>"+
      "<td><strong>"+h.incidencias+"</strong></td>"+
      "<td><span class='badge estado'>"+esc(estadoTxt(h.estado))+"</span></td>"+
      "<td><button class='btn' data-ev='"+idx+"'>Ver evidencia</button></td></tr>";
  });
  w.innerHTML=html+"</tbody></table>";
  w.querySelectorAll("[data-ev]").forEach(function(b){
    b.addEventListener("click", function(){ openEvidence(r.hallazgos[+b.getAttribute("data-ev")]); });
  });
}
function estadoTxt(e){ return e==="accept"?"Aceptada":e==="discard"?"Descartada":e==="reopen"?"Reabierta":"Pendiente"; }

/* ---------- Evidencia (cajón lateral) ---------- */
var lastFocus=null;
function openEvidence(h){
  lastFocus=document.activeElement;
  $("drawerTitle").textContent="Evidencia · "+h.tabla+"."+h.columna+" ("+h.regla_etiqueta+")";
  $("drawerBody").innerHTML=
    "<p><span class='badge "+h.prioridad.toLowerCase()+"'>Prioridad: "+esc(h.prioridad)+"</span> "+
    "<strong>"+h.incidencias+" incidencias</strong></p>"+
    "<p><strong>Recomendación:</strong> "+esc(h.recomendacion)+"</p>"+
    h.evidencias.map(function(e){
      return "<div class='ev'><p><strong>"+esc(e.ref)+"</strong> · fila <code>"+esc(e.row_id)+"</code></p>"+
      "<p>Valor: "+showVal(e.valor)+"</p></div>";
    }).join("");
  $("drawer").hidden=false; $("drawerOverlay").hidden=false;
  $("drawerClose").focus();
}
function closeDrawer(){
  $("drawer").hidden=true; $("drawerOverlay").hidden=true;
  if(lastFocus&&lastFocus.focus) lastFocus.focus();
}
$("drawerClose").addEventListener("click", closeDrawer);
$("drawerOverlay").addEventListener("click", closeDrawer);
document.addEventListener("keydown", function(e){ if(e.key==="Escape"&&!$("drawer").hidden) closeDrawer(); });

/* ---------- Decisiones ---------- */
function renderDecisions(){
  var box=$("decList"), r=state.run;
  if(!r){ box.innerHTML="<div class='empty-state'><h2>Sin decisiones pendientes</h2><p>Primero ejecuta un análisis y revisa los hallazgos.</p><button class='btn primary' data-goto='calidad'>Ver hallazgos</button></div>"; return; }
  var pend=r.hallazgos.filter(function(h){return h.estado==="pending";});
  var html="<p class='context-note'>"+pend.length+" pendientes de "+r.hallazgos.length+". Aceptar solo registra tu decisión.</p>";
  html+=r.hallazgos.map(function(h,idx){
    var evs=h.eventos||[];
    var fecha=evs.length?evs[evs.length-1].creado_en:null;
    return "<article class='dec' data-estado='"+esc(h.estado)+"'>"+
    "<h2>"+ruleIcon(h.regla)+esc(h.tabla)+"."+esc(h.columna)+" · "+esc(h.regla_etiqueta)+
    " <span class='badge "+h.prioridad.toLowerCase()+"'>"+esc(h.prioridad)+"</span> "+
    "<span class='badge estado'>"+esc(estadoTxt(h.estado))+"</span></h2>"+
    "<p class='dec-meta'>"+h.incidencias+" incidencias"+
      (h.decidido_por?" · por "+esc(h.decidido_por):"")+
      (fecha?" · "+esc(String(fecha).slice(0,16).replace("T"," ")):"")+"</p>"+
    "<details><summary>Recomendación</summary><p class='small'>"+esc(h.recomendacion)+"</p></details>"+
    (h.ultimo_comentario?"<p><strong>Último comentario:</strong> "+esc(h.ultimo_comentario)+"</p>":"")+
    "<label>Comentario opcional (máx. 1000 caracteres)<textarea maxlength='1000' data-c='"+idx+"' placeholder='Ej. Se deriva al responsable comercial…'></textarea></label>"+
    "<div class='dec-actions'>"+
    "<button class='btn primary' data-a='accept' data-i='"+idx+"'>Aceptar</button>"+
    "<button class='btn danger' data-a='discard' data-i='"+idx+"'>Descartar</button>"+
    "<button class='btn ghost' data-a='reopen' data-i='"+idx+"'>Reabrir</button>"+
    "<button class='btn' data-ev2='"+idx+"'>Ver evidencia</button>"+
    "</div></article>";
  }).join("");
  box.innerHTML=html;
  box.querySelectorAll("[data-a]").forEach(function(b){
    b.addEventListener("click", function(){ decide(+b.getAttribute("data-i"), b.getAttribute("data-a")); });
  });
  box.querySelectorAll("[data-ev2]").forEach(function(b){
    b.addEventListener("click", function(){ openEvidence(r.hallazgos[+b.getAttribute("data-ev2")]); });
  });
}
function decide(idx, accion){
  var r=state.run; if(!r) return;
  var h=r.hallazgos[idx];
  var ta=document.querySelector("textarea[data-c='"+idx+"']");
  var comentario=ta?ta.value.trim():"";
  if(comentario.length>1000){ toast("El comentario supera los 1000 caracteres."); return; }
  function apply(){
    h.estado=accion; h.ultimo_comentario=comentario||null;
    h.eventos.push({accion:accion, comentario:comentario, creado_en:new Date().toISOString()});
    if(state.mode==="demo"&&state.storage==="local"){
      try{ localStorage.setItem(LS_KEY, JSON.stringify(state.runs.slice(-20))); }catch(e){}
    }
    renderAll();
    toast(accion==="accept"?"Recomendación aceptada y registrada (no cambia los datos).":
      accion==="discard"?"Recomendación descartada y registrada.":"Hallazgo reabierto y registrado.");
  }
  if(state.mode==="server"){
    apiPost("decisions", {run_id:r.id, tabla:h.tabla, columna:h.columna, regla:h.regla,
      accion:accion, comentario:comentario}).then(function(res){
      if(res.code>=200&&res.code<300) apply();
      else toast(res.body.error||"No se pudo registrar la decisión.");
    }).catch(function(){ toast("Sin conexión con el servicio Python."); });
  } else apply();
}

/* ---------- Bitácora ---------- */
function renderRuns(){
  if(state.mode==="server"){
    apiGet("runs&limit=20").then(function(res){
      if(res.code>=200&&res.code<300) paintRuns(res.body.runs||[]);
      else $("runsWrap").innerHTML="<p class='empty'>No se pudo cargar el historial: "+esc(res.body.error||"error")+"</p>";
    }).catch(function(){ $("runsWrap").innerHTML="<p class='empty'>Sin conexión con el servicio.</p>"; });
    paintRunSelect([]);
    if(state.run) loadServerRunDetail(state.run.id);
  } else {
    var runs=state.runs.slice(-20).reverse();
    paintRuns(runs.map(function(r){return {id:r.id, modo:r.modo, creado_en:r.creado_en,
      total_registros:r.total_registros, comprobaciones:r.comprobaciones,
      incidencias:r.incidencias, indice:r.indice, hallazgos:r.hallazgos.length};}));
    paintRunSelect(state.runs);
    if(state.run) paintRunDetail(state.run);
  }
}
function paintRuns(items){
  var w=$("runsWrap");
  var card=$("runDetailCard");
  if(!items.length){
    card.hidden=true;
    w.innerHTML="<div class='empty-state'><h2>Todavía no hay ejecuciones</h2><p>Ejecuta tu primer análisis para verlo aquí.</p><button class='btn primary' data-goto='observatorio'>Ir a ejecutar análisis</button></div>";
    syncExport();
    return;
  }
  card.hidden=false;
  w.innerHTML="<table><thead><tr><th>#</th><th>Fecha</th><th>Modo</th><th>Índice</th><th>Incidencias</th><th></th></tr></thead><tbody>"+
    items.map(function(r){
      return "<tr><td><strong>"+r.id+"</strong></td><td>"+esc(r.creado_en)+"</td><td>"+esc(r.modo)+"</td>"+
      "<td>"+(r.indice===null?"Sin evaluar":r.indice+"%")+"</td><td>"+r.incidencias+" / "+r.comprobaciones+"</td>"+
      "<td><button class='btn' data-run='"+r.id+"'>Consultar</button></td></tr>";
    }).join("")+"</tbody></table>";
  w.querySelectorAll("[data-run]").forEach(function(b){
    b.addEventListener("click", function(){
      var id=+b.getAttribute("data-run");
      if(state.mode==="server") loadServerRunDetail(id);
      else { var r=state.runs.filter(function(x){return x.id===id;})[0]; if(r) paintRunDetail(r); }
      $("runSelect").value=String(id);
      syncExport();
    });
  });
}
function paintRunSelect(runs){
  var s=$("runSelect"); s.innerHTML="";
  var ids = state.mode==="server"
    ? (state.run?[state.run.id]:[])
    : runs.map(function(r){return r.id;});
  ids.forEach(function(id){ var o=document.createElement("option"); o.value=id; o.textContent="Ejecución #"+id; s.appendChild(o); });
  if(state.run) s.value=String(state.run.id);
  syncExport();
}
function loadServerRunDetail(id){
  apiGet("run&id="+id).then(function(res){
    if(res.code>=200&&res.code<300){
      var run=res.body.run;
      paintRunDetail({ id:run.id, modo:run.modo, creado_en:String(run.creado_en),
        total_registros:run.total_registros, comprobaciones:run.comprobaciones,
        incidencias:run.incidencias, indice:run.indice, hallazgos:(run.hallazgos||run.hallazgos_detalle||[]).map(function(h){
          return {tabla:h.tabla,columna:h.columna,regla:h.regla,regla_etiqueta:h.regla_etiqueta,
            prioridad:h.prioridad,incidencias:h.incidencias,recomendacion:h.recomendacion,
            evidencias:h.evidencias||[],estado:h.estado||"pending",ultimo_comentario:h.ultimo_comentario||null}; }) });
    }
    else $("runDetail").innerHTML="<p class='empty'>"+esc(res.body.error||"No encontrada.")+"</p>";
  }).catch(function(){ $("runDetail").innerHTML="<p class='empty'>Sin conexión.</p>"; });
}
function paintRunDetail(r){
  var dec=r.hallazgos.filter(function(h){return h.estado!=="pending";}).length;
  $("runDetail").innerHTML="<h2>Ejecución #"+r.id+" · "+esc(r.creado_en)+"</h2>"+
    "<p>Modo <strong>"+esc(r.modo)+"</strong> · "+r.total_registros+" registros · "+
    r.comprobaciones+" comprobaciones · "+r.incidencias+" incidencias · índice "+
    (r.indice===null?"sin evaluar":"<strong>"+r.indice+"%</strong>")+" · "+dec+" decisiones registradas.</p>"+
    "<div class='table-wrap'><table><thead><tr><th>Hallazgo</th><th>Incidencias</th><th>Decisión</th></tr></thead><tbody>"+
    r.hallazgos.map(function(h){return "<tr><td>"+esc(h.tabla)+"."+esc(h.columna)+" ("+esc(h.regla_etiqueta||h.regla)+")</td>"+
      "<td>"+h.incidencias+"</td><td>"+esc(estadoTxt(h.estado))+"</td></tr>";}).join("")+"</tbody></table></div>";
  $("runDetail").dataset.runId=r.id;
  syncExport();
}
function syncExport(){
  var has=!!($("runSelect").value||$("runDetail").dataset.runId);
  $("btnExport").disabled=!has;
  $("btnExport").title=has?"Exportar el análisis seleccionado en JSON":"Sin ejecuciones para exportar";
}
$("btnRefreshRuns").addEventListener("click", renderRuns);
$("runSelect").addEventListener("change", function(){
  var id=+$("runSelect").value; if(!id) return;
  if(state.mode==="server") loadServerRunDetail(id);
  else { var r=state.runs.filter(function(x){return x.id===id;})[0]; if(r) paintRunDetail(r); }
  syncExport();
});
$("btnExport").addEventListener("click", function(){
  var id=+$("runSelect").value||($("runDetail").dataset.runId?+$("runDetail").dataset.runId:0);
  if(!id){ toast("Primero ejecuta o selecciona un análisis."); return; }
  function download(obj){
    var blob=new Blob([JSON.stringify(obj,null,2)],{type:"application/json"});
    var a=document.createElement("a"); a.href=URL.createObjectURL(blob);
    a.download="nexo_ejecucion_"+id+".json"; document.body.appendChild(a); a.click();
    setTimeout(function(){URL.revokeObjectURL(a.href);a.remove();},500);
    toast("Análisis #"+id+" exportado en JSON.");
  }
  if(state.mode==="server"){
    apiGet("run&id="+id).then(function(res){
      if(res.code>=200&&res.code<300) download(res.body.run);
      else toast(res.body.error||"No se pudo exportar.");
    }).catch(function(){ toast("Sin conexión."); });
  } else {
    var r=state.runs.filter(function(x){return x.id===id;})[0];
    if(r) download(r); else toast("Ejecución no encontrada.");
  }
});

/* ---------- Centro de agentes ---------- */
var agState = { status:null, job:null, jobs:[], timer:null };
var AG_STAGES = [["catalogo","Catálogo"],["calidad","Calidad"],["recomendaciones","Recomendaciones"],["cierre","Cierre"]];

function agentBanner(){
  var b=$("aiBanner");
  if(state.mode==="demo"){
    b.textContent="El Centro de agentes necesita PHP y Python en marcha. Aquí solo está disponible la demostración con reglas (sin agentes reales).";
    return;
  }
  var s=agState.status;
  if(!s){ b.textContent="Consultando proveedor…"; return; }
  if(s.stub) b.textContent="Proveedor de prueba activo: los trabajos usan respuestas programadas, NO son IA real.";
  else if(!s.configured) b.textContent="IA sin configurar: falta "+(s.missing||[]).join(", ")+" en el .env del servidor. Puedes probar con el proveedor de prueba.";
  else b.textContent="IA habilitada: "+s.provider+" · "+s.model+". Su uso puede generar cargos según tu plan del proveedor.";
}
function renderAgents(){
  agentBanner();
  if(state.mode==="demo"){
    $("aiStatus").innerHTML="<dt>Estado</dt><dd>No disponible en demostración.</dd>";
    $("agentList").innerHTML="<li class='muted'>Inicia PHP y Python para ver los agentes.</li>";
    $("btnAgentStart").disabled=true;
    return;
  }
  $("btnAgentStart").disabled=false;
  apiGet("agent_status").then(function(res){
    if(res.code>=200&&res.code<300){
      agState.status=res.body;
      var s=res.body;
      $("aiStatus").innerHTML="<dt>Proveedor</dt><dd>"+esc(s.provider)+(s.stub?" (prueba)":"")+"</dd>"+
        "<dt>Modelo</dt><dd>"+esc(s.model)+"</dd>"+
        "<dt>Estado</dt><dd>"+(s.stub?"Proveedor de prueba":(s.configured?"Configurado":"IA sin configurar"))+"</dd>"+
        "<dt>Límites</dt><dd>"+s.limits.max_steps+" pasos · "+s.limits.max_tool_calls+" herramientas · "+s.limits.job_timeout_s+" s por trabajo</dd>";
      $("agentList").innerHTML=(s.agents||[]).map(function(a){
        return "<li><span><strong>"+esc(a.nombre)+"</strong><br><span class='muted small'>"+esc(a.funcion)+"</span></span></li>";
      }).join("");
      agentBanner();
    } else { $("aiBanner").textContent="No se pudo consultar el proveedor: "+(res.body.error||"error"); }
  }).catch(function(){ $("aiBanner").textContent="Sin conexión con el servicio Python."; });
  loadAgentJobs();
}
function loadAgentJobs(){
  apiGet("agent_jobs&limit=20").then(function(res){
    if(res.code>=200&&res.code<300){
      agState.jobs=res.body.jobs||[];
      paintAgentJobs();
    }
  }).catch(function(){});
}
function paintAgentJobs(){
  var w=$("agJobsWrap"), s=$("agJobSelect");
  s.innerHTML="";
  agState.jobs.forEach(function(j){
    var id=j.id!==undefined?j.id:j.ID;
    var o=document.createElement("option"); o.value=id; o.textContent="Trabajo #"+id+" · "+(j.estado||j.ESTADO); s.appendChild(o);
  });
  if(agState.job) s.value=String(agState.job.id);
  if(!agState.jobs.length){ w.innerHTML="<p class='empty'>Aún no hay trabajos.</p>"; return; }
  w.innerHTML="<table><thead><tr><th>#</th><th>Estado</th><th>Proveedor</th><th>Modelo</th><th>Análisis</th><th></th></tr></thead><tbody>"+
    agState.jobs.map(function(j){
      var id=j.id!==undefined?j.id:"?";
      return "<tr><td><strong>"+id+"</strong></td><td><span class='badge estado'>"+esc(j.estado||"?")+"</span></td>"+
      "<td>"+esc(j.proveedor||j.PROVEEDOR||"")+(j.es_prueba||j.stub?" <span class='badge ia'>prueba</span>":"")+"</td>"+
      "<td>"+esc(j.modelo||j.MODELO||"")+"</td><td>"+(j.run_id?"#"+j.run_id:"—")+"</td>"+
      "<td><button class='btn' data-aj='"+id+"'>Ver</button></td></tr>";
    }).join("")+"</tbody></table>";
  w.querySelectorAll("[data-aj]").forEach(function(b){
    b.addEventListener("click", function(){ loadAgentJob(+b.getAttribute("data-aj")); });
  });
}
function loadAgentJob(id){
  apiGet("agent_job&id="+id).then(function(res){
    if(res.code>=200&&res.code<300){ agState.job=res.body.job; $("agJobSelect").value=String(id); paintAgentJob(); }
    else toast(res.body.error||"Trabajo no encontrado.");
  }).catch(function(){ toast("Sin conexión."); });
}
function stageState(job, key){
  var evs=(job.etapas||[]).filter(function(e){return (e.etapa||e.ETAPA)===key;});
  if(evs.some(function(e){return (e.evento||e.EVENTO)==="fin";})) return "done";
  if(evs.length) return "active";
  return "idle";
}
function paintAgentJob(){
  var job=agState.job;
  if(!job) return;
  $("agJobId").textContent="#"+job.id+" · "+job.estado+(job.stub?" · proveedor de prueba":"");
  $("agStages").innerHTML=AG_STAGES.map(function(st){
    var s=stageState(job,st[0]);
    var word=s==="done"?"Completada":s==="active"?"En curso":"Pendiente";
    return "<li class='"+s+"'><strong>"+st[1]+"</strong><span class='stage-state'>"+word+"</span></li>";
  }).join("")+(job.error?"<li><strong>Error ("+esc(job.codigo_error||"")+ "):</strong> "+esc(job.error)+"</li>":"");
  var can=job.estado==="en_ejecucion"||job.estado==="esperando_revision";
  $("btnAgentCancel").disabled=!can;
  // Revisiones pendientes
  var rv=$("agReviews"); rv.innerHTML="";
  (job.revisiones||[]).filter(function(r){return (r.estado||"pendiente")==="pendiente";}).forEach(function(r){
    var d=document.createElement("div"); d.className="review-card";
    d.innerHTML="<h3>Revisión humana solicitada</h3><p>"+esc(r.motivo||"")+"</p>"+
      "<label>Comentario (máx. 1000)<textarea id='agRevComment' maxlength='1000'></textarea></label>"+
      "<div class='dec-actions'><button class='btn primary' id='agApprove'>Aprobar y reanudar</button>"+
      "<button class='btn danger' id='agReject'>Rechazar</button></div>";
    rv.appendChild(d);
    $("agApprove").addEventListener("click", function(){ agentReview(job.id,"approve"); });
    $("agReject").addEventListener("click", function(){ agentReview(job.id,"reject"); });
  });
  // Determinista frente a IA
  var det=job.determinista||null, recs=job.recomendaciones||job.recomendaciones_draft||[];
  var html="";
  if(det) html+="<p><span class='badge det'>Determinista</span> "+det.comprobaciones+" comprobaciones · "+det.incidencias+" incidencias · índice <strong>"+det.indice+"%</strong> (análisis #"+(job.run_id||"—")+")</p>";
  if(recs.length) html+="<table><thead><tr><th>Ref.</th><th>Acción propuesta</th><th>Prioridad</th></tr></thead><tbody>"+
    recs.map(function(r){
      var ref=r.ref_hallazgo||((r.tabla||"")+"."+(r.columna||"")+"."+(r.regla||""));
      return "<tr><td><code>"+esc(ref)+"</code> <span class='badge ia'>IA</span></td><td>"+esc(r.accion||"")+"</td><td>"+esc(r.prioridad||"")+"</td></tr>";
    }).join("")+"</tbody></table>";
  else html+="<p class='muted'>Aún no hay recomendaciones. Las propuestas con la marca IA son del modelo; las cifras deterministas vienen del motor.</p>";
  $("agVerdict").innerHTML=html;
  // Herramientas
  var tools=job.herramientas||[];
  $("agTools").innerHTML=tools.length?"<table><thead><tr><th>Agente</th><th>Herramienta</th><th>Resultado</th><th></th></tr></thead><tbody>"+
    tools.map(function(t){
      return "<tr><td>"+esc(t.agente||t.AGENTE||"")+"</td><td><code>"+esc(t.herramienta||t.HERRAMIENTA||"")+"</code></td>"+
      "<td class='small'>"+esc((t.resumen||t.RESUMEN||"").slice(0,160))+"</td><td>"+((t.ok===1||t.ok===true)?"Correcto":"Error")+"</td></tr>";
    }).join("")+"</tbody></table>":"<p class='empty'>Ninguna todavía.</p>";
  var u=job.uso||{};
  $("agUsage").textContent=u.llamadas_modelo?("Modelo: "+u.llamadas_modelo+" llamadas · "+(u.total||0)+" tokens reportados"+(job.stub?" (prueba, sin costo)":"")+"."):"";
  // Sondeo
  clearInterval(agState.timer);
  if(job.estado==="en_ejecucion"||job.estado==="esperando_revision"){
    agState.timer=setInterval(function(){ loadAgentJob(job.id); }, 2500);
  }
}
function agentReview(id, decision){
  var c=$("agRevComment"), com=c?c.value.trim():"";
  apiPost("agent_review&id="+id, {decision:decision, comentario:com}).then(function(res){
    if(res.code>=200&&res.code<300){ toast(decision==="approve"?"Revisión aprobada; trabajo reanudado.":"Revisión rechazada."); loadAgentJob(id); loadAgentJobs(); }
    else toast(res.body.error||"No se pudo responder.");
  }).catch(function(){ toast("Sin conexión."); });
}
$("btnAgentStart").addEventListener("click", function(){
  if(state.mode==="demo"){ toast("Inicia PHP y Python primero."); return; }
  var btn=$("btnAgentStart"); btn.disabled=true; $("agMsg").textContent="Iniciando trabajo en segundo plano…";
  apiPost("agent_start", {fuente:$("agFuente").value, pedir_revision:$("agReview").checked}).then(function(res){
    btn.disabled=false; $("agMsg").textContent="";
    if(res.code>=200&&res.code<300){
      agState.job={id:res.body.job_id, estado:"en_ejecucion", etapas:[], herramientas:[], revisiones:[]};
      toast("Trabajo #"+res.body.job_id+" iniciado.");
      loadAgentJobs(); loadAgentJob(res.body.job_id);
    } else { toast(res.body.error||"No se pudo iniciar."); $("agMsg").textContent=res.body.error||""; }
  }).catch(function(){ btn.disabled=false; toast("Sin conexión con el servicio Python."); });
});
$("btnAgentCancel").addEventListener("click", function(){
  if(!agState.job) return;
  apiPost("agent_cancel&id="+agState.job.id, {}).then(function(res){
    if(res.code>=200&&res.code<300){ toast("Trabajo cancelado."); loadAgentJob(agState.job.id); }
    else toast(res.body.error||"No se pudo cancelar.");
  }).catch(function(){ toast("Sin conexión."); });
});
$("btnAgentRefresh").addEventListener("click", function(){ if(agState.job) loadAgentJob(agState.job.id); });
$("btnAgentJobs").addEventListener("click", loadAgentJobs);
$("btnAgentRetry").addEventListener("click", function(){
  var id=+$("agJobSelect").value; if(!id){ toast("Selecciona un trabajo."); return; }
  apiPost("agent_retry&id="+id, {}).then(function(res){
    if(res.code>=200&&res.code<300){ toast("Reintento iniciado como trabajo #"+res.body.job_id+"."); loadAgentJobs(); loadAgentJob(res.body.job_id); }
    else toast(res.body.error||"No se pudo reintentar.");
  }).catch(function(){ toast("Sin conexión."); });
});
$("agJobSelect").addEventListener("change", function(){
  var id=+$("agJobSelect").value; if(id) loadAgentJob(id);
});

/* ---------- Autenticación local ---------- */
var NAME_RE = /^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ'’\- ]{2,60}$/;
var EMAIL_RE_CLI = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

function setErr(input, errId, msg){
  var e=$(errId);
  if(!msg){ e.hidden=true; e.textContent=""; if(input) input.removeAttribute("aria-invalid"); return true; }
  e.hidden=false; e.textContent=msg; if(input){ input.setAttribute("aria-invalid","true"); }
  return false;
}
function validNombre(v){
  v=(v||"").replace(/\s+/g," ").trim();
  if(!NAME_RE.test(v)) return "El nombre debe tener entre 2 y 60 letras (se permiten espacios, guiones y apóstrofes).";
  return "";
}
function validEmail(v){
  v=(v||"").trim().toLowerCase();
  if(v.length>160||!EMAIL_RE_CLI.test(v)) return "Escribe un correo válido (ej. usuario@dominio.com).";
  return "";
}
function validPass(v){
  v=v||"";
  if(v.length<8||v.length>72) return "La contraseña debe tener entre 8 y 72 caracteres.";
  var f=[];
  if(!/[a-záéíóúüñ]/.test(v)) f.push("una minúscula");
  if(!/[A-ZÁÉÍÓÚÜÑ]/.test(v)) f.push("una mayúscula");
  if(!/[0-9]/.test(v)) f.push("un número");
  if(f.length) return "La contraseña debe incluir "+f.join(", ")+".";
  return "";
}
function pwScore(v){
  var s=0;
  if(v.length>=8) s++;
  if(v.length>=12) s++;
  if(/[a-z]/.test(v)&&/[A-Z]/.test(v)) s++;
  if(/[0-9]/.test(v)) s++;
  if(/[^A-Za-z0-9]/.test(v)) s++;
  return s;
}
function paintStrength(){
  var v=$("rgPass").value, s=pwScore(v), bar=$("pwBar"), lab=$("pwLabel");
  bar.style.width=(s*20)+"%";
  var txt=v?"Seguridad: "+(s<=2?"débil":s<=3?"aceptable":"fuerte")+" ("+s+" de 5).":"Seguridad: sin evaluar.";
  lab.textContent=txt;
}
function setUser(u){
  state.user=u||null;
  var name=u?u.nombre.split(" ")[0]:"Invitado";
  $("userLabel").textContent=name;
}
function openProfile(){
  var u=state.user;
  $("mAvatar").textContent=u?u.nombre.trim()[0].toUpperCase():"?";
  $("profTitle").textContent=u?u.nombre:"Invitado";
  $("mEmail").textContent=u?u.email:(state.mode==="demo"
    ?"El inicio de sesión necesita PHP y Python en marcha."
    :"Sin sesión iniciada.");
  $("mState").textContent=u
    ?"Sesión activa. Tus decisiones quedarán firmadas con tu nombre."
    :"Exploras como invitado: tus decisiones quedarán sin firma.";
  var A=$("mActions");
  if(!u&&(state.mode==="demo")){
    A.innerHTML="<button class='btn primary' data-p='enter'>Entrar a la aplicación</button>";
  } else if(!u){
    A.innerHTML="<button class='btn primary' data-p='enter'>Entrar a la aplicación</button>"+
      "<button class='btn' data-p='login'>Iniciar sesión</button>"+
      "<button class='btn link' data-p='register'>Crear cuenta</button>";
  } else {
    A.innerHTML="<button class='btn primary' data-p='enter'>Entrar a la aplicación</button>"+
      "<button class='btn' data-p='account'>Ver mi perfil</button>"+
      "<button class='btn ghost' data-p='logout'>Cerrar sesión</button>";
  }
  A.querySelectorAll("[data-p]").forEach(function(b){
    b.addEventListener("click", function(){ profileAction(b.getAttribute("data-p")); });
  });
  openModal("modalProfile");
}
function profileAction(a){
  if(a==="enter"){ closeModals(); enterApp(); }
  else if(a==="login"){ openModal("modalLogin"); }
  else if(a==="register"){ openModal("modalRegister"); }
  else if(a==="account"){ closeModals(); showTab("perfil"); }
  else if(a==="logout"){ doLogout(); }
}
var modalReturn=null;
function openModal(id){
  if($("authOverlay").hidden) modalReturn=document.activeElement;
  $("authOverlay").hidden=false;
  ["modalLogin","modalRegister","modalProfile"].forEach(function(x){ $(x).hidden=(x!==id); });
  var f=document.querySelector("#"+id+" input, #"+id+" button"); if(f) f.focus();
}
function closeModals(){
  $("authOverlay").hidden=true;
  $("modalLogin").hidden=true; $("modalRegister").hidden=true; $("modalProfile").hidden=true;
  if(modalReturn&&modalReturn.focus) modalReturn.focus();
}
function doLogout(){
  apiPost("auth_logout", {}).then(function(){ setUser(null); toast("Sesión cerrada."); })
    .catch(function(){ setUser(null); });
}
$("userBtn").addEventListener("click", openProfile);
document.addEventListener("keydown", function(e){
  if(e.key==="Escape") closeModals();
});
$("authOverlay").addEventListener("click", closeModals);
document.querySelectorAll("[data-close]").forEach(function(b){ b.addEventListener("click", closeModals); });
$("btnEnter").addEventListener("click", enterApp);
$("btnShowLogin").addEventListener("click", function(){ openModal("modalLogin"); });
$("btnShowRegister").addEventListener("click", function(){ openModal("modalRegister"); });
$("rgPass").addEventListener("input", paintStrength);

$("formLogin").addEventListener("submit", function(ev){
  ev.preventDefault();
  if(state.mode==="demo"){ setErr(null,"loginErr","El inicio de sesión necesita PHP y Python en marcha."); return; }
  var em=$("liEmail").value.trim().toLowerCase(), pw=$("liPass").value;
  var ok=setErr($("liEmail"),"liEmailErr",validEmail(em));
  ok=setErr($("liPass"),"liPassErr",pw?"":"Escribe tu contraseña.")&&ok;
  if(!ok) return;
  setErr(null,"loginErr","");
  var sub=$("formLogin").querySelector("[type=submit]"); sub.disabled=true;
  apiPost("auth_login", {email:em, password:pw}).then(function(res){
    sub.disabled=false;
    if(res.code>=200&&res.code<300){ setUser(res.body.user); closeModals(); $("formLogin").reset(); toast("Hola, "+res.body.user.nombre.split(" ")[0]+"."); enterApp(); }
    else setErr(null,"loginErr",res.body.error||"No se pudo entrar.");
  }).catch(function(){ sub.disabled=false; setErr(null,"loginErr","Sin conexión con el servicio."); });
});
$("formRegister").addEventListener("submit", function(ev){
  ev.preventDefault();
  if(state.mode==="demo"){ setErr(null,"regErr","El registro necesita PHP y Python en marcha."); return; }
  var nm=$("rgName").value.replace(/\s+/g," ").trim();
  var em=$("rgEmail").value.trim().toLowerCase();
  var p1=$("rgPass").value, p2=$("rgPass2").value;
  var ok=setErr($("rgName"),"rgNameErr",validNombre(nm));
  ok=setErr($("rgEmail"),"rgEmailErr",validEmail(em))&&ok;
  ok=setErr($("rgPass"),"rgPassErr",validPass(p1))&&ok;
  ok=setErr($("rgPass2"),"rgPass2Err",p1===p2?"":"Las contraseñas no coinciden.")&&ok;
  if(!ok) return;
  setErr(null,"regErr","");
  var sub2=$("formRegister").querySelector("[type=submit]"); sub2.disabled=true;
  apiPost("auth_register", {nombre:nm, email:em, password:p1}).then(function(res){
    sub2.disabled=false;
    if(res.code===201){ setUser(res.body.user); closeModals(); $("formRegister").reset(); paintStrength(); toast("Cuenta creada. Hola, "+res.body.user.nombre.split(" ")[0]+"."); enterApp(); }
    else setErr(null,"regErr",res.body.error||"No se pudo registrar.");
  }).catch(function(){ sub2.disabled=false; setErr(null,"regErr","Sin conexión con el servicio."); });
});
document.querySelectorAll(".pw-toggle").forEach(function(btn){
  btn.addEventListener("click", function(){
    var input=$(btn.getAttribute("data-for"));
    var show=input.type==="password";
    input.type=show?"text":"password";
    btn.setAttribute("aria-pressed", show?"true":"false");
    btn.setAttribute("aria-label", show?"Ocultar contraseña":"Mostrar contraseña");
    btn.textContent=show?"Ocultar":"Mostrar";
  });
});
function refreshSession(){
  if(state.mode==="demo"){ setUser(null); return; }
  apiGet("auth_me").then(function(res){
    setUser(res.code===200?res.body.user:null);
  }).catch(function(){ setUser(null); });
}
function renderProfile(){
  var u=state.user;
  $("profAvatar").textContent=u?u.nombre.trim()[0].toUpperCase():"?";
  $("profName").textContent=u?u.nombre:"Invitado";
  $("profEmail").textContent=u?u.email:"Sin sesión iniciada.";
  $("profState").textContent=u?("Sesión activa. Tus decisiones quedarán firmadas como "+u.nombre+".")
    :"Exploras como invitado: tus decisiones quedarán sin firma.";
  $("btnProfLogout").hidden=!u;
  $("btnProfLogin").hidden=!!u;
  $("btnProfRegister").hidden=!!u;
}
$("btnProfEnter").addEventListener("click", function(){ showTab("observatorio"); });
$("btnProfLogin").addEventListener("click", function(){ openModal("modalLogin"); });
$("btnProfRegister").addEventListener("click", function(){ openModal("modalRegister"); });
$("btnProfLogout").addEventListener("click", function(){ doLogout(); showTab("observatorio"); });

/* ---------- Arranque ---------- */
function renderAll(){ renderObservatory(); renderCatalog(); renderQuality(); renderDecisions(); renderRuns(); }
$("btnAnalyze").addEventListener("click", runAnalysis);
$("btnHow").addEventListener("click", function(){ var h=$("howBox"); h.hidden=!h.hidden; });
["catSearch","catDomain","catTable"].forEach(function(id){ $(id).addEventListener("input", renderCatalog); });
["fTable","fPrio","fRule"].forEach(function(id){ $(id).addEventListener("change", renderQuality); });

fillCatalogFilters();
loadLocal();
detectMode().then(function(){ renderAll(); refreshSession(); });
renderAll();
setModeBadge();
$("btnEnter").focus();
