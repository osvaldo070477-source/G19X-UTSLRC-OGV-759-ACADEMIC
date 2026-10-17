/* NEXO · Paginador genérico de tablas (public/js/paginador.js) */
/* ---------- Paginador genérico (punto 4) ---------- */
var PAGE_SIZE=10, pgSeq=0;
function paginateTables(root){
  if(!root) return;
  var tables=root.querySelectorAll?root.querySelectorAll("table"):[];
  tables.forEach(function(tb){
    var rows=tb.tBodies.length?tb.tBodies[0].rows:[];
    if(rows.length<=PAGE_SIZE) return;
    if(!tb.dataset.pgid){ tb.dataset.pgid="pg"+(pgSeq++); tb.dataset.page="0"; }
    var page=+tb.dataset.page||0;
    var pages=Math.ceil(rows.length/PAGE_SIZE);
    if(page>=pages) page=pages-1;
    var key=page+"/"+pages+"/"+rows.length;
    if(tb.dataset.pgstate===key) return;  // sin cambios: no tocar el DOM
    tb.dataset.page=page;
    tb.dataset.pgstate=key;
    for(var i=0;i<rows.length;i++){
      rows[i].style.display=(i>=page*PAGE_SIZE&&i<(page+1)*PAGE_SIZE)?"":"none";
    }
    var bar=tb.nextElementSibling;
    if(!bar||!bar.classList||!bar.classList.contains("pgbar")){
      bar=document.createElement("div");
      bar.className="dec-actions pager pgbar";
      tb.parentNode.insertBefore(bar, tb.nextSibling);
    }
    bar.innerHTML="";
    var mk=function(txt,pg,dis,go){
      var b=document.createElement("button");
      b.className="btn ghost"; b.textContent=txt; b.disabled=!!dis;
      b.setAttribute("data-pg",tb.dataset.pgid); b.setAttribute("data-go",go);
      bar.appendChild(b);
    };
    mk("Anterior",page,page<=0,-1);
    var info=document.createElement("span");
    info.className="muted small";
    info.textContent="Página "+(page+1)+" de "+pages+" · "+rows.length+" filas";
    bar.appendChild(info);
    mk("Siguiente",page,page>=pages-1,1);
  });
}
document.addEventListener("click", function(e){
  var b=e.target&&e.target.closest?e.target.closest("[data-pg]"):null;
  if(!b||b.disabled) return;
  var tb=document.querySelector("table[data-pgid='"+b.getAttribute("data-pg")+"']");
  if(!tb) return;
  tb.dataset.page=(+tb.dataset.page||0)+(+b.getAttribute("data-go"));
  paginateTables(tb.parentNode);
});
var pgBusy=false, pgTimer=null;
if(window.MutationObserver){
  new MutationObserver(function(){
    if(pgBusy) return;
    clearTimeout(pgTimer);
    pgTimer=setTimeout(function(){
      pgBusy=true;
      try{ paginateTables($("contenido")); }catch(err){}
      pgBusy=false;
    }, 80);
  }).observe($("contenido"), {childList:true, subtree:true});
}

