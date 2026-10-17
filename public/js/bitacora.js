/* NEXO · Bitácora: ejecuciones, detalle y exportación (public/js/bitacora.js) */
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

