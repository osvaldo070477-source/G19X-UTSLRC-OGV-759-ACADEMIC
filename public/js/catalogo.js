/* NEXO · Catálogo: búsqueda, filtros y fichas de activos (public/js/catalogo.js) */
/* ---------- Catálogo ---------- */
var CAT_TABLES=["clientes","pedidos","productos"];
function renderCatalog(){
  var box=$("catalogList");
  var canWrite=state.mode==="server"&&!!state.user;
  var isAdmin=!!(state.user&&state.user.rol==="admin");
  $("btnImportCSV").hidden=!canWrite;
  function paint(){
    var q=($("catSearch").value||"").toLowerCase(), dom=$("catDomain").value, tab=$("catTable").value;
    var cd=catData(), META2=cd.metadatos, DATA=cd.muestra;
    box.innerHTML="";
    var shown=0;
    CAT_TABLES.forEach(function(t){
      var m=META2[t]||META[t], rows=DATA[t]||[];
      if(!rows.length) return;
      if(dom && m.dominio!==dom) return;
      if(tab && t!==tab) return;
      var hay=[m.nombre,m.descripcion,m.responsable,m.dominio,t].join(" ").toLowerCase();
      var rowsHit=rows.filter(function(r){return Object.values(r).join(" ").toLowerCase().indexOf(q)>=0;});
      if(q && hay.indexOf(q)<0 && rowsHit.length===0) return;
      shown++;
      var d=document.createElement("article"); d.className="asset";
      d.innerHTML=
        "<div class='asset-head'><h2>"+esc(m.nombre)+" <code class='asset-tech'>"+esc(t)+"</code></h2>"+
        "<div class='asset-meta'><span>Dominio: <strong>"+esc(m.dominio)+"</strong></span>"+
        "<span>Responsable: <strong>"+esc(m.responsable)+"</strong></span>"+
        "<span><strong>"+rows.length+"</strong> registros</span></div>"+
        (canWrite?"<div class='dec-actions'><button class='btn' data-add='"+t+"'>Agregar registro</button>"+
          (isAdmin?"<button class='btn ghost' data-meta='"+t+"'>Editar ficha</button>":"")+"</div>":"")+"</div>"+
        "<div class='asset-body'><p>"+esc(m.descripcion)+"</p>"+
        "<ul class='cols'>"+m.columnas.map(function(c){return "<li><strong>"+esc(c.nombre)+"</strong> · "+esc(c.tipo)+"</li>";}).join("")+"</ul>"+
        "<details><summary>Reglas aplicables ("+m.reglas.length+")</summary><ul class='rules'>"+m.reglas.map(function(x){return "<li>"+esc(x)+"</li>";}).join("")+"</ul></details>"+
        "<details><summary>Ver datos ("+rowsHit.length+" de "+rows.length+")</summary><div class='table-wrap'><table>"+
        "<thead><tr>"+Object.keys(rows[0]).map(function(k){return "<th>"+esc(k)+"</th>";}).join("")+"</tr></thead>"+
        "<tbody>"+rowsHit.map(function(r){return "<tr>"+Object.keys(rows[0]).map(function(k){
          return "<td>"+(isEmpty(r[k])&&typeof r[k]!=="number"?showVal(r[k]):esc(r[k]))+"</td>";}).join("")+"</tr>";}).join("")+
        "</tbody></table></div></details></div>";
      box.appendChild(d);
    });
    if(!shown) box.innerHTML="<div class='empty-state'><h2>Sin resultados</h2><p>Prueba con «correo» o limpia los filtros.</p><button class='btn' data-clear='1'>Limpiar filtros</button></div>";
    var active=$("catSearch").value||dom||tab;
    $("btnClearFilters").hidden=!active;
    box.querySelectorAll("[data-add]").forEach(function(b){
      b.addEventListener("click", function(){ openRowModal(b.getAttribute("data-add"), "add"); });
    });
    box.querySelectorAll("[data-meta]").forEach(function(b){
      b.addEventListener("click", function(){ openRowModal(b.getAttribute("data-meta"), "meta"); });
    });
    paginateTables(box);
  }
  if(state.mode==="server"&&!state.catalog){
    box.innerHTML="<p class='empty'>Cargando catálogo…</p>";
    loadCatalog().then(paint);
  } else paint();
}
$("btnClearFilters").addEventListener("click", clearCatalogFilters);
function clearCatalogFilters(){
  $("catSearch").value=""; $("catDomain").value=""; $("catTable").value="";
  renderCatalog();
}
function fillCatalogFilters(){
  var MM=(state.catalog&&state.catalog.metadatos)||META;
  var doms=[...new Set(CAT_TABLES.map(function(t){return MM[t].dominio;}))];
  doms.forEach(function(d){ var o=document.createElement("option"); o.textContent=d; $("catDomain").appendChild(o); });
  CAT_TABLES.forEach(function(t){ var o=document.createElement("option"); o.value=t; o.textContent=t; $("catTable").appendChild(o); });
}

