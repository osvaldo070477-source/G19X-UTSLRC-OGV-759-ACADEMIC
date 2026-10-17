/* NEXO · Perfil: información, seguridad y actividad (public/js/perfil.js) */
function refreshSession(){
  if(state.mode==="demo"){ setUser(null); return Promise.resolve(null); }
  return apiGet("auth_me").then(function(res){
    var u=res.code===200?res.body.user:null;
    setUser(u);
    if(u && !entered()){
      enterApp();
      var t=null;
      try{ t=sessionStorage.getItem("nexo_tab"); }catch(e){}
      if(t && tabs.indexOf(t)>=0) showTab(t);
    }
    return u;
  }).catch(function(){ setUser(null); return null; });
}
var profTab="info", actPage=0;
var ACT_SIZE=10;
function selectPTab(name){
  profTab=name;
  document.querySelectorAll("[data-ptab]").forEach(function(b){
    var on=b.getAttribute("data-ptab")===name;
    b.setAttribute("aria-selected",on?"true":"false");
    b.tabIndex=on?0:-1;
    $(b.getAttribute("aria-controls")).hidden=!on;
  });
  if(name==="act") loadActivity(0);
}
document.querySelectorAll("[data-ptab]").forEach(function(b){
  b.addEventListener("click", function(){ selectPTab(b.getAttribute("data-ptab")); });
  b.addEventListener("keydown", function(e){
    var order=["info","sec","act"], i=order.indexOf(profTab), j=null;
    if(e.key==="ArrowRight") j=(i+1)%3;
    else if(e.key==="ArrowLeft") j=(i+2)%3;
    else if(e.key==="Home") j=0;
    else if(e.key==="End") j=2;
    if(j!==null){ e.preventDefault(); selectPTab(order[j]); document.querySelector('[data-ptab="'+order[j]+'"]').focus(); }
  });
});
function renderProfile(){
  var u=state.user, guest=!u;
  $("profAvatar").textContent=u?initials(u.nombre):"?";
  $("profName").textContent=u?u.nombre:"Invitado";
  $("profEmail").textContent=u?u.email:"Sin sesión iniciada.";
  $("profRole").textContent=u?(u.rol||"operador"):"Invitado";
  $("profState").textContent=u?"Sesión activa":"Sin sesión";
  $("profTabs").hidden=guest;
  ["ppanel-info","ppanel-sec","ppanel-act"].forEach(function(id){ $(id).hidden=guest; });
  $("profGuestActions").hidden=!guest;
  $("profUserActions").hidden=guest;
  if(guest) return;
  selectPTab("info");
  apiGet("auth_profile").then(function(res){
    if(res.code!==200||!res.body.user){ toast("No se pudo cargar el perfil."); return; }
    var p=res.body.user;
    setUser({id:p.id, nombre:p.nombre, email:p.email, rol:p.rol});
    $("profAvatar").textContent=initials(p.nombre);
    $("profName").textContent=p.nombre;
    $("profEmail").textContent=p.email;
    $("profRole").textContent=p.rol||"operador";
    $("profState").textContent=(p.estado||"activo")==="activo"?"Sesión activa":"Cuenta desactivada";
    $("piName").textContent=p.nombre;
    $("piEmail").textContent=p.email;
    $("piRole").textContent=p.rol||"operador";
    $("piSince").textContent=p.creado_en?p.creado_en.slice(0,10):"—";
    $("pfName").value=p.nombre;
    $("pfNameMsg").textContent="";
    loadActivity(0);
  }).catch(function(){ toast("Sin conexión con el servicio."); });
}
function loadActivity(page){
  actPage=Math.max(0,page||0);
  if(state.mode==="demo"||!state.user){
    $("profActivity").innerHTML="<p class='empty'>La actividad necesita PHP, Python y sesión iniciada.</p>";
    $("actPage").textContent=""; $("actPrev").disabled=true; $("actNext").disabled=true;
    return;
  }
  apiGet("auth_activity&limit="+ACT_SIZE+"&offset="+(actPage*ACT_SIZE)).then(function(res){
    if(res.code!==200){ $("profActivity").innerHTML="<p class='empty'>No se pudo cargar la actividad.</p>"; return; }
    var items=res.body.items||[], total=res.body.total||0;
    var pages=Math.max(1,Math.ceil(total/ACT_SIZE));
    if(!items.length){
      $("profActivity").innerHTML="<div class='empty-state'><h2>Sin actividad todavía</h2><p>Aquí aparecerán tus decisiones aceptadas, descartadas o reabiertas.</p><button class='btn primary' data-goto='calidad'>Ver hallazgos</button></div>";
    } else {
      $("profActivity").innerHTML="<table><thead><tr><th>Fecha</th><th>Acción</th><th>Hallazgo</th><th></th></tr></thead><tbody>"+
        items.map(function(it){
          return "<tr><td>"+esc(String(it.creado_en||"").slice(0,16).replace("T"," "))+"</td>"+
          "<td><span class='badge estado'>"+esc(estadoTxt(it.accion))+"</span></td>"+
          "<td><code>"+esc(it.tabla+"."+it.columna+" ("+it.regla+")")+"</code></td>"+
          "<td><button class='btn' data-runid='"+it.run_id+"'>Ver en bitácora</button></td></tr>";
        }).join("")+"</tbody></table>";
      $("profActivity").querySelectorAll("[data-runid]").forEach(function(b){
        b.addEventListener("click", function(){ gotoRun(+b.getAttribute("data-runid")); });
      });
    }
    $("actPage").textContent="Página "+(actPage+1)+" de "+pages+" · "+total+" en total";
    $("actPrev").disabled=actPage<=0;
    $("actNext").disabled=actPage>=pages-1;
  }).catch(function(){ $("profActivity").innerHTML="<p class='empty'>Sin conexión con el servicio.</p>"; });
}
function gotoRun(id){
  showTab("bitacora");
  var s=$("runSelect"), found=false, i;
  for(i=0;i<s.options.length;i++){ if(+s.options[i].value===id){ found=true; break; } }
  if(!found){ var o=document.createElement("option"); o.value=id; o.textContent="Ejecución #"+id; s.appendChild(o); }
  s.value=String(id);
  if(state.mode==="server") loadServerRunDetail(id);
  else { var r=state.runs.filter(function(x){return x.id===id;})[0]; if(r) paintRunDetail(r); }
  syncExport();
}
$("actPrev").addEventListener("click", function(){ loadActivity(actPage-1); });
$("actNext").addEventListener("click", function(){ loadActivity(actPage+1); });
$("formName").addEventListener("submit", function(ev){
  ev.preventDefault();
  var nm=$("pfName").value.replace(/\s+/g," ").trim();
  if(!setErr($("pfName"),"pfNameErr",validNombre(nm))) return;
  $("pfNameMsg").textContent="";
  var sub=$("formName").querySelector("[type=submit]"); sub.disabled=true;
  apiPost("auth_update_name", {nombre:nm}).then(function(res){
    sub.disabled=false;
    if(res.code===200&&res.body.user){
      setUser({id:res.body.user.id, nombre:res.body.user.nombre, email:res.body.user.email, rol:res.body.user.rol});
      renderProfile();
      $("pfNameMsg").textContent="Nombre guardado correctamente.";
      toast("Nombre actualizado.");
    } else setErr($("pfName"),"pfNameErr",res.body.error||"No se pudo guardar.");
  }).catch(function(){ sub.disabled=false; setErr($("pfName"),"pfNameErr","Sin conexión con el servicio."); });
});
$("formPass").addEventListener("submit", function(ev){
  ev.preventDefault();
  var cur=$("pfCur").value, nw=$("pfNew").value, nw2=$("pfNew2").value;
  var ok=setErr($("pfCur"),"pfCurErr",cur?"":"Escribe tu contraseña actual.");
  ok=setErr($("pfNew"),"pfNewErr",validPass(nw))&&ok;
  ok=setErr($("pfNew2"),"pfNew2Err",nw===nw2?"":"Las contraseñas no coinciden.")&&ok;
  if(!ok) return;
  $("pfPassMsg").textContent="";
  var sub=$("formPass").querySelector("[type=submit]"); sub.disabled=true;
  apiPost("auth_change_password", {actual:cur, nueva:nw}).then(function(res){
    sub.disabled=false;
    if(res.code===200&&res.body.ok){
      $("formPass").reset();
      $("pfPassMsg").textContent="Contraseña actualizada. Úsala la próxima vez que entres.";
      toast("Contraseña actualizada.");
    } else {
      var msg=res.body.error||"No se pudo cambiar.";
      if(res.code===401) setErr($("pfCur"),"pfCurErr",msg);
      else setErr($("pfNew"),"pfNewErr",msg);
    }
  }).catch(function(){ sub.disabled=false; setErr($("pfNew"),"pfNewErr","Sin conexión con el servicio."); });
});
$("btnRecGen").addEventListener("click", function(){
  $("pfRecMsg").textContent="";
  var b=$("btnRecGen"); b.disabled=true;
  apiPost("auth_recovery_regen", {}).then(function(res){
    b.disabled=false;
    if(res.code===200&&res.body.recovery_code){
      $("pfRecMsg").textContent="Tu código nuevo (solo se muestra una vez): "+res.body.recovery_code;
      toast("Código generado. Anótalo.");
    } else toast(res.body.error||"No se pudo generar.");
  }).catch(function(){ b.disabled=false; toast("Sin conexión."); });
});
