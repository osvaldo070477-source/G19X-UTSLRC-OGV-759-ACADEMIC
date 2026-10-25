/* NEXO · Núcleo: muestra, reglas, estado, almacenamiento, navegación, modo y API (public/js/base.js) */
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
    {row_id:"cli-12",id:"CLI-012",nombre:"Raúl Ortega",email:"raul.ortega@example.com"},
    {row_id:"cli-13",id:"CLI-013",nombre:"Elena Ruiz",email:"elena.ruiz@example.com"},
    {row_id:"cli-14",id:"CLI-014",nombre:"Jorge López",email:"jorge.lopez@example"},
    {row_id:"cli-15",id:"CLI-015",nombre:"",email:"sin.nombre@example.com"},
    {row_id:"cli-16",id:"CLI-009",nombre:"Valeria Castro (duplicada)",email:"valeria2@example.com"},
    {row_id:"cli-17",id:"CLI-017",nombre:"   ",email:"espacios@example.com"},
    {row_id:"cli-18",id:"CLI-018",nombre:"Marta Gil",email:""},
    {row_id:"cli-19",id:"CLI-019",nombre:"Iván Paz",email:"ivan.paz@example.com"},
    {row_id:"cli-20",id:"CLI-020",nombre:"Sara Rey",email:"sara.rey@example"}
  ],
  pedidos: [
    {row_id:"ped-01",id:"PED-001",cliente_id:"CLI-001",fecha:"2026-01-10",total:150.5},
    {row_id:"ped-02",id:"PED-002",cliente_id:"CLI-002",fecha:"2026-01-11",total:0},
    {row_id:"ped-03",id:"PED-003",cliente_id:"",fecha:"2026-01-12",total:89.9},
    {row_id:"ped-04",id:"PED-004",cliente_id:"CLI-004",fecha:"2026-01-13",total:210.0},
    {row_id:"ped-05",id:"PED-005",cliente_id:"CLI-007",fecha:"2026-01-20",total:45.0},
    {row_id:"ped-06",id:"PED-006",cliente_id:"CLI-009",fecha:"2026-02-01",total:320.75},
    {row_id:"ped-07",id:"PED-007",cliente_id:"CLI-010",fecha:"2026-02-03",total:15.0},
    {row_id:"ped-08",id:"PED-008",cliente_id:"CLI-012",fecha:"2026-02-05",total:99.99},
    {row_id:"ped-09",id:"PED-009",cliente_id:"CLI-013",fecha:"2026-02-10",total:75.0},
    {row_id:"ped-10",id:"PED-010",cliente_id:"",fecha:"2026-02-11",total:120.0},
    {row_id:"ped-11",id:"PED-005",cliente_id:"CLI-015",fecha:"2026-02-12",total:33.3},
    {row_id:"ped-12",id:"PED-012",cliente_id:"CLI-018",fecha:"2026-02-13",total:0},
    {row_id:"ped-13",id:"PED-013",cliente_id:"CLI-019",fecha:"2026-02-14",total:210.5},
    {row_id:"ped-14",id:"PED-014",cliente_id:"CLI-020",fecha:"2026-02-15",total:18.75}
  ],
  productos: [
    {row_id:"pro-01",id:"PRO-001",nombre:"Café Molido 500g",precio:85.5},
    {row_id:"pro-02",id:"PRO-002",nombre:"",precio:120.0},
    {row_id:"pro-03",id:"PRO-003",nombre:"Taza Cerámica",precio:45.0},
    {row_id:"pro-04",id:"PRO-004",nombre:"Filtro Papel x40",precio:30.0},
    {row_id:"pro-05",id:"PRO-005",nombre:"Cafetera Prensa 1L",precio:450.0},
    {row_id:"pro-06",id:"PRO-006",nombre:"Termo Acero 750ml",precio:0},
    {row_id:"pro-07",id:"PRO-007",nombre:"Cafetera Goteo 12T",precio:320.0},
    {row_id:"pro-08",id:"PRO-008",nombre:"",precio:55.0},
    {row_id:"pro-09",id:"PRO-009",nombre:"Molino Manual",precio:0},
    {row_id:"pro-10",id:"PRO-003",nombre:"Taza Cerámica (duplicada)",precio:45.0}
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
function notice(msg){ var n=document.getElementById("noticeBar");
  if(msg){ n.hidden=false; n.textContent=msg; } else { n.textContent=""; n.hidden=true; } }
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
var tabs = ["observatorio","catalogo","calidad","decisiones","bitacora","agentes","admin","perfil"];
var SECTIONS = {
  observatorio: ["Observatorio", "Estado general de tus datos y último análisis."],
  catalogo: ["Catálogo", "Activos, responsables y estructura."],
  calidad: ["Calidad", "Hallazgos verificados por las reglas."],
  decisiones: ["Decisiones", "Responde las recomendaciones pendientes."],
  bitacora: ["Bitácora", "Historial de ejecuciones y exportaciones."],
  agentes: ["Agentes", "Trabajos de análisis con IA."],
  admin: ["Administración", "Cuentas y accesos (solo admin)."],
  perfil: ["Mi perfil", "Tu cuenta y sesión."]
};
function entered(){ return $("welcome").hidden; }
function enterApp(){
  $("welcome").hidden=true;
  $("shell").hidden=false;
  showTab("observatorio");
  renderAll();
  var main=$("contenido");
  if(main&&main.focus) main.focus();
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
  try{ if(entered()) sessionStorage.setItem("nexo_tab",name); }catch(e){}
  if(name==="bitacora") renderRuns();
  if(name==="observatorio") renderObservatory();
  if(name==="decisiones") renderDecisions();
  if(name==="calidad") renderQuality();
  if(name==="agentes") renderAgents();
  if(name==="admin") renderAdmin();
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
  var s=$("modeState"), t=$("modeTech"), f=$("footMode");
  if(state.mode==="demo"){
    s.textContent="Modo demostración"; t.textContent="Navegador · datos de ejemplo";
    f.textContent="modo demostración (navegador, sin servidor)";
  } else if(state.serverMode==="mysql"){
    s.textContent="Modo conectado"; t.textContent="PHP · Python · MySQL";
    f.textContent="modo conectado (MySQL)";
  } else {
    s.textContent="Modo local"; t.textContent="PHP · Python · memoria";
    f.textContent="modo local (la memoria se pierde al reiniciar)";
  }
  var modeShort=state.mode==="demo"?"Demostración":state.serverMode==="mysql"?"Conectado":"Local";
  if($("obsMode")) $("obsMode").textContent=modeShort;
  // Invitado solo en demostración (sin servidor no hay autenticación).
  $("btnEnter").hidden=state.mode!=="demo";
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
var csrfToken="";
function loadCsrf(){
  if(state.mode==="demo") return Promise.resolve("");
  return apiGet("auth_csrf").then(function(res){
    if(res.code===200&&res.body.csrf) csrfToken=res.body.csrf;
  }).catch(function(){});
}
function apiPost(action, data){
  return fetch("api.php?action="+action, {method:"POST",
    headers:{"Content-Type":"application/json","X-CSRF-Token":csrfToken}, body:JSON.stringify(data||{})})
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

