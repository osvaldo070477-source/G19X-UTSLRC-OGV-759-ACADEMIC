/* NEXO · Observatorio: resumen del último análisis (public/js/observatorio.js) */
/* ---------- Observatorio ---------- */
function renderObservatory(){
  var r=state.run;
  var first=state.user?state.user.nombre.split(" ")[0]:null;
  $("obsHello").textContent=first?("Hola, "+first):"Hola de nuevo";
  try{
    $("obsDate").textContent=new Date().toLocaleDateString("es-MX",{weekday:"long",day:"numeric",month:"long",year:"numeric"});
  }catch(e){ $("obsDate").textContent=""; }
  $("obsAvatar").textContent=state.user?initials(state.user.nombre):"?";
  if(!r){
    $("obsNext").textContent="Explora el catálogo y ejecuta tu primer análisis para ver el estado de tus datos.";
    $("obsEmpty").hidden=false;
    $("obsGrid").hidden=true;
    $("stAssets").textContent="3";
    $("stRows").textContent="—"; $("stFindings").textContent="—";
    $("stPending").textContent="—"; $("stLast").textContent="—";
    return;
  }
  $("obsEmpty").hidden=true;
  $("obsGrid").hidden=false;
  var pend=r.hallazgos.filter(function(h){return h.estado==="pending";}).length;
  $("obsNext").textContent=pend
    ?("Tienes "+pend+" decisiones pendientes de "+r.hallazgos.length+".")
    :("Análisis #"+r.id+" al día: "+r.hallazgos.length+" hallazgos revisados.");
  $("stAssets").textContent="3";
  $("stRows").textContent=r.total_registros;
  $("stFindings").textContent=r.hallazgos.length;
  $("stPending").textContent=pend;
  $("stLast").textContent=r.creado_en;
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

