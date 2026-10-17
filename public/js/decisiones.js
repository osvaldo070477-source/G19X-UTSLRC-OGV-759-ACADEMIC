/* NEXO · Decisiones: aceptar, descartar y reabrir (public/js/decisiones.js) */
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

