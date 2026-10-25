/* NEXO · Arranque: enlaces finales y primera carga (public/js/arranque.js) */
/* ---------- Arranque ---------- */
function renderAll(){ renderObservatory(); renderCatalog(); renderQuality(); renderDecisions(); renderRuns(); }
$("btnAnalyze").addEventListener("click", runAnalysis);
$("btnAnalyzeFirst").addEventListener("click", runAnalysis);
$("guideAnalyze").addEventListener("click", runAnalysis);
$("btnHow").addEventListener("click", function(){ var h=$("howBox"); h.hidden=!h.hidden; });
["catSearch","catDomain","catTable"].forEach(function(id){ $(id).addEventListener("input", renderCatalog); });
["fTable","fPrio","fRule"].forEach(function(id){ $(id).addEventListener("change", renderQuality); });

fillCatalogFilters();
loadLocal();
detectMode().then(function(){ renderAll(); refreshSession(); loadCsrf(); });
renderAll();
setModeBadge();
($("btnEnter").hidden?$("btnShowLogin"):$("btnEnter")).focus();
