/* NEXO · Administración: cuentas y auditoría de acciones (public/js/admin.js) */
/* ---------- Administración (solo admin) ---------- */
var adminResetId=0;
function renderAdmin(){
  var w=$("adminWrap");
  if(state.mode==="demo"||!state.user||state.user.rol!=="admin"){
    w.innerHTML="<p class='empty'>Sección solo para administradores.</p>";
    $("adminAuditWrap").innerHTML="<p class='empty'>Sin registros.</p>";
    return;
  }
  renderAdminAudit();
  apiGet("admin_users&limit=50&offset=0").then(function(res){
    if(res.code!==200){ w.innerHTML="<p class='empty'>"+esc(res.body.error||"Sin permiso.")+"</p>"; return; }
    var items=res.body.items||[];
    if(!items.length){ w.innerHTML="<p class='empty'>Sin cuentas registradas.</p>"; return; }
    w.innerHTML="<table><thead><tr><th>Cuenta</th><th>Rol</th><th>Estado</th><th></th></tr></thead><tbody>"+
      items.map(function(x){
        var locked=x.locked_until&&x.locked_until>Date.now()/1000;
        return "<tr><td><strong>"+esc(x.nombre)+"</strong><br><span class='muted small'>"+esc(x.email)+"</span>"+
          (locked?"<br><span class='badge media'>Bloqueada</span>":"")+"</td>"+
        "<td>"+esc(x.rol)+"<br><label class='muted small'>Cambiar a "+
        "<select data-rol='"+x.id+"'>"+
        ["operador","lector","admin"].map(function(r){
          return "<option value='"+r+"'"+(r===x.rol?" selected":"")+">"+r+"</option>";
        }).join("")+"</select></label></td>"+
        "<td><span class='badge estado'>"+esc(x.estado)+"</span></td>"+
        "<td><div class='dec-actions'>"+
        (x.estado==="activo"
          ?"<button class='btn danger' data-est='desactivada' data-id='"+x.id+"'>Desactivar</button>"
          :"<button class='btn primary' data-est='activo' data-id='"+x.id+"'>Activar</button>")+
        "<button class='btn' data-unlock='"+x.id+"'>Desbloquear</button>"+
        "<button class='btn ghost' data-rst='"+x.id+"' data-nm='"+esc(x.nombre)+"'>Nueva clave</button>"+
        "</div></td></tr>";
      }).join("")+"</tbody></table>";
    w.querySelectorAll("[data-est]").forEach(function(b){
      b.addEventListener("click", function(){
        apiPost("admin_estado&id="+b.getAttribute("data-id"), {estado:b.getAttribute("data-est")}).then(function(res){
          toast(res.code===200?"Estado actualizado.":(res.body.error||"No se pudo actualizar."));
          if(res.code===200) renderAdmin();
        }).catch(function(){ toast("Sin conexión."); });
      });
    });
    w.querySelectorAll("[data-unlock]").forEach(function(b){
      b.addEventListener("click", function(){
        apiPost("admin_desbloquear&id="+b.getAttribute("data-unlock"), {}).then(function(res){
          toast(res.code===200?"Cuenta desbloqueada.":(res.body.error||"No se pudo desbloquear."));
          if(res.code===200) renderAdmin();
        }).catch(function(){ toast("Sin conexión."); });
      });
    });
    w.querySelectorAll("[data-rol]").forEach(function(s){
      s.addEventListener("change", function(){
        apiPost("admin_rol&id="+s.getAttribute("data-rol"), {rol:s.value}).then(function(res){
          toast(res.code===200?"Rol actualizado.":(res.body.error||"No se pudo cambiar el rol."));
          if(res.code===200) renderAdmin();
        }).catch(function(){ toast("Sin conexión."); });
      });
    });
    w.querySelectorAll("[data-rst]").forEach(function(b){
      b.addEventListener("click", function(){
        adminResetId=+b.getAttribute("data-rst");
        $("adminResetWho").textContent="Nueva clave para "+b.getAttribute("data-nm")+".";
        $("adNew").value=""; setErr($("adNew"),"adNewErr",""); $("adResetMsg").textContent="";
        $("adminResetBox").hidden=false;
        $("adNew").focus();
      });
    });
  }).catch(function(){ w.innerHTML="<p class='empty'>Sin conexión con el servicio.</p>"; });
}
function renderAdminAudit(page){
  var w=$("adminAuditWrap"), p=Math.max(0,page||0);
  apiGet("admin_audit&limit=10&offset="+(p*10)).then(function(res){
    if(res.code!==200){ w.innerHTML="<p class='empty'>"+esc(res.body.error||"Sin permiso.")+"</p>"; return; }
    var items=res.body.items||[], total=res.body.total||0;
    var pages=Math.max(1,Math.ceil(total/10));
    if(!items.length){ w.innerHTML="<p class='empty'>Sin acciones registradas.</p>"; return; }
    w.innerHTML="<table><thead><tr><th>Fecha</th><th>Admin</th><th>Acción</th><th>Detalle</th></tr></thead><tbody>"+
      items.map(function(x){
        return "<tr><td>"+esc(String(x.creado_en||"").slice(0,16).replace("T"," "))+"</td>"+
        "<td>"+esc(x.admin||("#"+x.admin_id))+"</td>"+
        "<td><span class='badge estado'>"+esc(x.accion)+"</span></td>"+
        "<td class='small'>"+esc([x.objetivo||(x.target_id?("#"+x.target_id):""),x.detalle||""].filter(Boolean).join(" · "))+"</td></tr>";
      }).join("")+"</tbody></table>"+
      "<div class='dec-actions pager pgbar'><button class='btn ghost' data-apg='"+(p-1)+"'"+(p<=0?" disabled":"")+">Anterior</button>"+
      "<span class='muted small'>Página "+(p+1)+" de "+pages+" · "+total+" en total</span>"+
      "<button class='btn ghost' data-apg='"+(p+1)+"'"+(p>=pages-1?" disabled":"")+">Siguiente</button></div>";
    w.querySelectorAll("[data-apg]").forEach(function(b){
      b.addEventListener("click", function(){ renderAdminAudit(+b.getAttribute("data-apg")); });
    });
  }).catch(function(){ w.innerHTML="<p class='empty'>Sin conexión con el servicio.</p>"; });
}
$("adResetCancel").addEventListener("click", function(){ $("adminResetBox").hidden=true; });
$("formAdminReset").addEventListener("submit", function(ev){
  ev.preventDefault();
  var nw=$("adNew").value;
  if(!setErr($("adNew"),"adNewErr",validPass(nw))) return;
  $("adResetMsg").textContent="";
  var sub=$("formAdminReset").querySelector("[type=submit]"); sub.disabled=true;
  apiPost("admin_reset&id="+adminResetId, {nueva:nw}).then(function(res){
    sub.disabled=false;
    if(res.code===200&&res.body.ok){
      $("formAdminReset").reset();
      $("adminResetBox").hidden=true;
      $("adResetMsg").textContent="";
      toast("Contraseña restablecida.");
      renderAdmin();
    } else setErr($("adNew"),"adNewErr",res.body.error||"No se pudo guardar.");
  }).catch(function(){ sub.disabled=false; setErr($("adNew"),"adNewErr","Sin conexión con el servicio."); });
});
$("btnProfLogin").addEventListener("click", function(){ openModal("modalLogin"); });
$("btnProfRegister").addEventListener("click", function(){ openModal("modalRegister"); });
$("btnProfLogout").addEventListener("click", function(){ doLogout(); });

