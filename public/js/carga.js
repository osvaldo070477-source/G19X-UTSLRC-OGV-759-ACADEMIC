/* NEXO · Carga gobernada: formulario por activo e importación CSV (public/js/carga.js) */
/* ---------- Carga gobernada (punto 1) ---------- */
var FIELD_TYPES = {
  clientes: {id:"texto", nombre:"texto", email:"correo"},
  pedidos: {id:"texto", cliente_id:"texto", fecha:"fecha", total:"número"},
  productos: {id:"texto", nombre:"texto", precio:"número"}
};
function loadCatalog(force){
  if(state.mode==="demo"||state.catalog&&!force) return Promise.resolve(state.catalog);
  return apiGet("catalog&muestra=1").then(function(res){
    if(res.code===200){
      state.catalog={metadatos:res.body.metadatos||META, muestra:res.body.muestra||SAMPLE};
    }
    return state.catalog;
  }).catch(function(){ return state.catalog; });
}
function catData(){
  return state.catalog||{metadatos:META, muestra:SAMPLE};
}
var rowCtx={tabla:null, modo:null};
function openRowModal(tabla, modo, extra){
  rowCtx={tabla:tabla, modo:modo};
  var meta=catData().metadatos[tabla];
  $("rowTitle").textContent=modo==="meta"?("Editar "+meta.nombre):("Agregar a "+meta.nombre);
  var box=$("rowFields"); box.innerHTML="";
  $("rowErr").hidden=true; $("rowMsg").textContent="";
  var cols = modo==="meta" ? [] : meta.columnas.map(function(c){return c.nombre;}).filter(function(n){return n!=="row_id";});
  if(modo==="meta"){
    box.innerHTML=
      "<label>Descripción<textarea id='rf_desc' maxlength='500'>"+esc(meta.descripcion)+"</textarea></label>"+
      "<label>Responsable<input id='rf_resp' maxlength='120' value='"+esc(meta.responsable)+"'></label>";
  } else {
    box.innerHTML=cols.map(function(n){
      var tipo=(FIELD_TYPES[tabla]||{})[n]||"texto";
      var ph=tipo==="fecha"?"AAAA-MM-DD":tipo==="número"?"0":tipo==="correo"?"usuario@dominio.com":"";
      var inp=tipo==="fecha"
        ?"<input id='rf_"+n+"' placeholder='"+ph+"'>"
        :"<input id='rf_"+n+"' placeholder='"+ph+"'>";
      return "<label>"+esc(n)+" <span class='muted small'>"+esc(tipo)+"</span>"+inp+"</label>";
    }).join("");
  }
  if(extra&&extra.nota){
    var p=document.createElement("p"); p.className="muted small"; p.textContent=extra.nota;
    box.appendChild(p);
  }
  openModal("modalRow");
}
$("formRow").addEventListener("submit", function(ev){
  ev.preventDefault();
  var t=rowCtx.tabla;
  if(rowCtx.modo==="meta"){
    var d=$("rf_desc").value.trim(), r=$("rf_resp").value.trim();
    if(!d||!r){ setErr(null,"rowErr","Completa descripción y responsable."); return; }
    var sub=$("formRow").querySelector("[type=submit]"); sub.disabled=true;
    apiPost("source_meta", {tabla:t, descripcion:d, responsable:r}).then(function(res){
      sub.disabled=false;
      if(res.code===200){ closeModals(); loadCatalog(true).then(renderCatalog); toast("Metadatos actualizados."); }
      else setErr(null,"rowErr",res.body.error||"No se pudo guardar.");
    }).catch(function(){ sub.disabled=false; setErr(null,"rowErr","Sin conexión."); });
    return;
  }
  var fila={};
  (catData().metadatos[t].columnas||[]).forEach(function(c){
    if(c.nombre==="row_id") return;
    var el=$("rf_"+c.nombre);
    fila[c.nombre]=el?el.value.trim():"";
  });
  setErr(null,"rowErr","");
  var sub2=$("formRow").querySelector("[type=submit]"); sub2.disabled=true;
  apiPost("source_add", {tabla:t, fila:fila}).then(function(res){
    sub2.disabled=false;
    if(res.code===201){ closeModals(); loadCatalog(true).then(function(){ renderCatalog(); toast("Registro guardado. Ejecuta un análisis para verlo en Calidad."); }); }
    else setErr(null,"rowErr",res.body.error||"No se pudo guardar.");
  }).catch(function(){ sub2.disabled=false; setErr(null,"rowErr","Sin conexión."); });
});
var csvPayload=null;
$("btnImportCSV").addEventListener("click", function(){
  if(state.mode==="demo"){ toast("La importación necesita el modo conectado."); return; }
  if(!state.user){ toast("Inicia sesión para cargar datos."); return; }
  $("csvResult").innerHTML=""; $("btnCSVImport").hidden=true;
  openModal("modalCSV");
});
function readCSVFile(){
  return new Promise(function(resolve, reject){
    var f=$("csvFile").files[0];
    if(!f){ reject("Elige un archivo .csv."); return; }
    var rd=new FileReader();
    rd.onload=function(){ resolve(rd.result); };
    rd.onerror=function(){ reject("No se pudo leer el archivo."); };
    rd.readAsText(f);
  });
}
$("btnCSVPreview").addEventListener("click", function(){
  var t=$("csvTable").value;
  readCSVFile().then(function(text){
    return apiPost("source_preview", {tabla:t, csv:text});
  }).then(function(res){
    if(res.code!==200){ $("csvResult").innerHTML="<p class='error-box'>"+esc(res.body.error||"No se pudo validar.")+"</p>"; $("btnCSVImport").hidden=true; csvPayload=null; return; }
    csvPayload={tabla:$("csvTable").value};
    var ok=res.body.validas||[], mal=res.body.rechazadas||[];
    $("csvResult").innerHTML="<p><strong>"+ok.length+"</strong> válidas · <strong>"+mal.length+"</strong> rechazadas.</p>"+
      (mal.length?"<div class='table-wrap'><table><thead><tr><th>Línea</th><th>Motivo</th></tr></thead><tbody>"+
        mal.slice(0,20).map(function(x){return "<tr><td>"+x.linea+"</td><td>"+esc(x.error)+"</td></tr>";}).join("")+
        "</tbody></table></div>"+(mal.length>20?"<p class='muted small'>Mostrando 20 de "+mal.length+".</p>":""):"");
    $("btnCSVImport").hidden=ok.length===0;
    paginateTables($("csvResult"));
  }).catch(function(err){ $("csvResult").innerHTML="<p class='error-box'>"+esc(typeof err==="string"?err:"Sin conexión.")+"</p>"; });
});
$("btnCSVImport").addEventListener("click", function(){
  if(!csvPayload) return;
  readCSVFile().then(function(text){
    return apiPost("source_import", {tabla:csvPayload.tabla, csv:text});
  }).then(function(res){
    if(res.code===201){
      closeModals();
      loadCatalog(true).then(function(){ renderCatalog(); toast("Importadas "+res.body.insertadas+" filas ("+(res.body.rechazadas||[]).length+" rechazadas). Ejecuta un análisis."); });
    } else toast(res.body.error||"No se pudo importar.");
  }).catch(function(){ toast("Sin conexión."); });
});
$("btnShowRecover").addEventListener("click", function(){ openModal("modalRecover"); });
$("formRecover").addEventListener("submit", function(ev){
  ev.preventDefault();
  var em=$("rcEmail").value.trim().toLowerCase(), co=$("rcCode").value.trim(), nw=$("rcNew").value;
  var ok=setErr($("rcEmail"),"rcEmailErr",validEmail(em));
  ok=setErr($("rcCode"),"rcCodeErr",co?"":"Escribe el código de 12 caracteres.")&&ok;
  ok=setErr($("rcNew"),"rcNewErr",validPass(nw))&&ok;
  if(!ok) return;
  setErr(null,"recErr",""); $("recMsg").textContent="";
  var sub=$("formRecover").querySelector("[type=submit]"); sub.disabled=true;
  apiPost("auth_recover", {email:em, codigo:co, nueva:nw}).then(function(res){
    sub.disabled=false;
    if(res.code===200&&res.body.ok){
      $("formRecover").reset();
      $("recMsg").textContent="Listo. Entra con tu nueva contraseña.";
      toast("Contraseña recuperada. Inicia sesión.");
    } else setErr(null,"recErr",res.body.error||"No se pudo recuperar.");
  }).catch(function(){ sub.disabled=false; setErr(null,"recErr","Sin conexión."); });
});

