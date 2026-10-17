/* NEXO · Autenticación: registro, inicio de sesión y recuperación (public/js/auth.js) */
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
  $("userLabel").textContent=name+(u&&u.rol==="lector"?" (lectura)":"");
  if($("userInitials")) $("userInitials").textContent=u?initials(u.nombre):"?";
  var admin=!!(u&&u.rol==="admin");
  if($("navAdmin")) $("navAdmin").hidden=!admin;
  if(!admin && !$("tab-admin").hidden) showTab("observatorio");
}
function initials(nombre){
  var p=String(nombre||"").trim().split(/\s+/);
  return ((p[0]||"?")[0]+((p[1]||"")[0]||"")).toUpperCase();
}
function toggleUserMenu(force){
  var m=$("userMenu"), show=force!==undefined?force:m.hidden;
  m.hidden=!show;
  $("userBtn").setAttribute("aria-expanded",show?"true":"false");
  if(show){ var f=m.querySelector("button"); if(f) f.focus(); }
}
function closeUserMenu(){ toggleUserMenu(false); }
var modalReturn=null;
var regActionsHTML=null;
function openModal(id){
  if($("authOverlay").hidden) modalReturn=document.activeElement;
  $("authOverlay").hidden=false;
  ["modalLogin","modalRegister","modalRow","modalCSV","modalRecover"].forEach(function(x){ $(x).hidden=(x!==id); });
  if(id==="modalRegister"){
    var acts=$("formRegister").querySelector(".dec-actions");
    if(regActionsHTML===null) regActionsHTML=acts.innerHTML;
    else acts.innerHTML=regActionsHTML;
    $("regCode").textContent="";
  }
  var f=document.querySelector("#"+id+" input, #"+id+" button"); if(f) f.focus();
}
function closeModals(){
  $("authOverlay").hidden=true;
  $("modalLogin").hidden=true; $("modalRegister").hidden=true;
  $("modalRow").hidden=true; $("modalCSV").hidden=true; $("modalRecover").hidden=true;
  if(modalReturn&&modalReturn.focus) modalReturn.focus();
}
function doLogout(){
  apiPost("auth_logout", {}).then(function(){ setUser(null); exitToWelcome(); })
    .catch(function(){ setUser(null); exitToWelcome(); });
}
function exitToWelcome(){
  closeModals();
  closeNav();
  $("shell").hidden=true;
  $("welcome").hidden=false;
  $("btnEnter").focus();
}
$("userBtn").addEventListener("click", function(){ toggleUserMenu(); });
$("userMenu").querySelectorAll("[data-m]").forEach(function(b){
  b.addEventListener("click", function(){
    var a=b.getAttribute("data-m");
    closeUserMenu();
    if(a==="profile") showTab("perfil");
    else if(a==="logout") doLogout();
  });
});
document.addEventListener("click", function(e){
  var m=$("userMenu");
  if(!m.hidden && !$("userBtn").contains(e.target) && !m.contains(e.target)) closeUserMenu();
});
document.addEventListener("keydown", function(e){
  if(e.key==="Escape"){ closeModals(); closeUserMenu(); }
});
$("authOverlay").addEventListener("click", closeModals);
document.addEventListener("click", function(e){
  var c=e.target&&e.target.closest?e.target.closest("[data-close]"):null;
  if(c) closeModals();
});
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
    if(res.code===201){
      setUser(res.body.user);
      $("formRegister").reset(); paintStrength();
      var code=res.body.recovery_code||"";
      $("regCode").innerHTML="Tu código de recuperación (anótalo, solo se muestra una vez): <strong>"+esc(code)+"</strong>";
      $("formRegister").querySelector(".dec-actions").innerHTML=
        "<button type='button' class='btn primary' id='btnRegDone'>Ya lo anoté, entrar</button>";
      $("btnRegDone").addEventListener("click", function(){ closeModals(); enterApp(); });
      toast("Cuenta creada. Hola, "+res.body.user.nombre.split(" ")[0]+".");
    }
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
