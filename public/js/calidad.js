/* NEXO · Calidad: hallazgos y cajón de evidencia (public/js/calidad.js) */
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

