/* Equivalencia del motor de reglas (RNF4).
 *
 * Ejecuta el bloque JavaScript del motor (public/js/base.js) sobre los mismos
 * casos que backend/rules.py y devuelve los resultados en JSON.
 *
 * Uso:  node tests/equivalence.js casos.json
 * Requiere Node 14 o superior. No se usa en la aplicación: solo en pruebas.
 */
"use strict";

var fs = require("fs");
var path = require("path");
var vm = require("vm");

var RAIZ = path.resolve(__dirname, "..");
var BASE_JS = path.join(RAIZ, "public", "js", "base.js");

var INICIO = "/* ---------- Reglas (idénticas a backend/rules.py) ---------- */";
var FIN = "/* ---------- Estado y almacenamiento ---------- */";

var fuente = fs.readFileSync(BASE_JS, "utf8");
var i = fuente.indexOf(INICIO);
var f = fuente.indexOf(FIN);

if (i < 0 || f < 0 || f <= i) {
  console.error("No se encontro el bloque del motor de reglas en public/js/base.js");
  process.exit(2);
}

var contexto = {};
vm.createContext(contexto);
vm.runInContext(fuente.slice(i, f), contexto);

if (typeof contexto.analyzeTables !== "function") {
  console.error("analyzeTables no quedo disponible en el contexto de prueba");
  process.exit(2);
}

var rutaCasos = process.argv[2];
if (!rutaCasos) {
  console.error("Falta la ruta del archivo de casos (JSON).");
  process.exit(2);
}

var casos = JSON.parse(fs.readFileSync(rutaCasos, "utf8"));
var salida = casos.map(function (caso) {
  return { id: caso.id, result: contexto.analyzeTables(caso.tables) };
});

process.stdout.write(JSON.stringify(salida));
