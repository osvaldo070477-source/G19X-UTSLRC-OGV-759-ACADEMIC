/* NEXO · Centro de agentes: trabajos, etapas, revisión y reintento (public/js/agentes.js) */
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
function resumenError(job){
  var code=job.codigo_error||"", msg=String(job.error||"");
  var espera="";
  var hm=msg.match(/(\d+)h(\d+)m/);
  if(hm) espera=" (reintenta en ~"+hm[1]+" h "+hm[2]+" min)";
  else { var rs=msg.match(/retryDelay"?\s*:\s*"(\d+)s/); if(rs) espera=" (reintenta en ~"+Math.round(+rs[1]/3600)+" h)"; }
  if(code==="proveedor_server"&&/cuota|quota|429/i.test(msg)) return "Cuota del proveedor agotada"+espera+".";
  if(code==="proveedor_server") return "El proveedor falló temporalmente. Reintenta más tarde.";
  if(code==="proveedor_timeout") return "El proveedor tardó demasiado. Reintenta más tarde.";
  if(code==="proveedor_bad_request") return "Petición rechazada por el proveedor.";
  if(code==="proveedor_auth") return "Clave del proveedor rechazada.";
  if(code==="limite_pasos") return "El modelo no concluyó en los pasos permitidos.";
  if(code==="respuesta_invalida") return "El modelo devolvió un formato inválido.";
  if(code==="tiempo_agotado") return "Se agotó el tiempo máximo del trabajo.";
  if(code==="cancelado") return "Cancelado por el operador.";
  return msg.slice(0,160);
}
function paintAgentJob(){
  var job=agState.job;
  if(!job) return;
  var comentarioPrev=($("agRevComment")||{}).value||"";
  $("agJobId").textContent="#"+job.id+" · "+job.estado+(job.stub?" · proveedor de prueba":"");
  $("agStages").innerHTML=AG_STAGES.map(function(st){
    var s=stageState(job,st[0]);
    var word=s==="done"?"Completada":s==="active"?"En curso":"Pendiente";
    return "<li class='"+s+"'><strong>"+st[1]+"</strong><span class='stage-state'>"+word+"</span></li>";
  }).join("")+(job.error?"<li><strong>Error ("+esc(job.codigo_error||"")+ "):</strong> "+esc(resumenError(job))+
    "<details><summary>Detalle técnico</summary><p class='small'>"+esc(job.error)+"</p></details></li>":"");
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
  var nc=$("agRevComment");
  if(nc&&comentarioPrev) nc.value=comentarioPrev;
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
  if(job.estado==="en_ejecucion"){
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

