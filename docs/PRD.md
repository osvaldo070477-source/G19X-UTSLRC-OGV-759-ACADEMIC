# PRD — NEXO: Arquitectura Agentic para Data Governance (MVP)

## 1. Problemática
Las organizaciones acumulan datos incompletos, duplicados o inconsistentes y no tienen un lugar centralizado para consultar sus activos, detectar problemas y dar seguimiento a las decisiones. Sin ese recorrido, los errores se descubren tarde y las correcciones no dejan rastro.

## 2. Objetivo general
Demostrar el recorrido completo de gobierno de datos (conocer → verificar → evidenciar → recomendar → decidir → auditar) con datos sintéticos de Clientes, Pedidos y Productos.

## 3. Objetivos específicos
1. Mostrar un catálogo con responsable, dominio, columnas y reglas por activo.
2. Ejecutar verificaciones deterministas de obligatoriedad, unicidad y formato de correo.
3. Presentar evidencias con valores y referencias de fila dentro de cada análisis.
4. Proponer una recomendación concreta por hallazgo.
5. Registrar decisiones humanas (aceptar / descartar / reabrir) con historial acumulativo.
6. Conservar ejecuciones en bitácora y exportarlas en JSON.

## 4. Usuarios
- **Operador/a de datos (estudiante):** ejecuta análisis, revisa hallazgos, carga datos y registra decisiones.
- **Lector/a:** consulta resultados autorizados; el servidor rechaza sus escrituras (403).
- **Administrador/a:** gestiona cuentas (activar/desactivar, desbloquear, restablecer claves, cambiar roles) y edita la ficha de los activos; cada acción queda auditada.
- Aplicación local de un equipo pequeño, con autenticación propia y roles básicos; sin SSO ni autenticación empresarial.

## 5. Alcance
- Tres modos base: A (demostración sin instalaciones), B (PHP + Python sin MySQL), C (PHP + Python + MySQL).
- **Capacidad agentic (este incremento):** trabajos en segundo plano donde un modelo decide qué herramientas autorizadas ejecutar; puntuación siempre del motor; revisión humana entre pasos.
- 3 activos, 44 registros sintéticos, 208 comprobaciones, índice 90 (calculado, nunca escrito a mano).
- Decisiones sobre la ejecución más reciente; lectura de anteriores.

## 6. Exclusiones (lo que NEXO NO hace)
- No corrige datos automáticamente; aceptar una recomendación no cambia la fuente ni el índice.
- La IA no calcula ni escribe: el modelo solo elige herramientas autorizadas y propone; el motor determinista calcula toda puntuación y ninguna escritura ocurre sin aprobación humana. No hay acciones autónomas.
- Autenticación local de un solo equipo: sin SSO, sin jerarquías organizacionales ni roles empresariales.
- Sin entrevistas con empresas, ahorros medidos ni validaciones externas (proyecto académico).

## 7. Requisitos funcionales
| ID | Requisito | Aceptación |
|----|-----------|------------|
| RF1 | Observatorio con modo, activos, registros, índice, hallazgos, pendientes y último análisis | Sin análisis previo no muestra resultados inventados |
| RF2 | Botón Ejecutar análisis | Calcula 208/21/8/90 sobre la muestra |
| RF3 | Catálogo con búsqueda y filtros | Filtra por texto, dominio y activo; muestra datos sintéticos |
| RF4 | Calidad con filtros por tabla, prioridad y tipo | Cada hallazgo abre evidencia con valor y ref de fila |
| RF5 | Decisiones aceptar/descartar/reabrir + comentario ≤1000 | Genera eventos acumulativos; aceptar no altera fuente ni índice |
| RF6 | Bitácora últimas 20 + exportar JSON | Exporta análisis con decisiones; conserva historial |
| RF7 | Decisiones solo sobre la ejecución más reciente | Rechaza (409) decisiones sobre ejecuciones viejas |
| RF8 | Límite 10 000 filas por tabla | Rechaza (413) sin presentar truncados como completos |
| RF9 | Error de conexión visible | Nunca cambia silenciosamente a simulados en modo C |
| RF10 | Trabajos agentic en segundo plano con estados | pendiente → en ejecución → (revisión) → completado/fallido/cancelado; reintento explícito |
| RF11 | Herramientas autorizadas y validadas | Rechaza herramientas, tablas y columnas fuera de lista; sin SQL arbitrario |
| RF12 | Validación de salidas del modelo | Referencias inexistentes, conteos inventados o JSON inválido se rechazan o piden revisión |
| RF13 | Revisión humana | Responde y reanuda solo en estado compatible; rechazos incompatibles devuelven 409 |
| RF14 | Proveedor sin configurar | Sin clave hay proveedor de prueba etiquetado; nunca se presenta como IA real |
| RF15 | Usuarios locales con validación | Registro/login con reglas en cliente y servidor, bloqueo por intentos, sesiones de 8 h; decisiones firmadas |
| RF16 | Perfil propio | Ficha con rol y registro, cambio de nombre y contraseña persistidos, actividad propia paginada; todo identificado desde la sesión |
| RF17 | Administración básica | Lista sin hashes, activar/desactivar (sin auto-bloqueo), desbloquear, restablecer claves y cambiar roles (operador/lector/admin); auditoría de cada acción; primer admin vía script local |
| RF18 | Carga gobernada | Formulario por activo e importar CSV con vista previa; validación, límites y auditoría por usuario |
| RF19 | Metadatos editables | Admin edita descripción y responsable; el catálogo los lee de MySQL |
| RF20 | Recuperación local | Código de un solo uso al registrarse; sin email externo |
| RF21 | Paginación | Tablas de 10 en 10 sin perder eventos ni filtros |

## 8. Requisitos no funcionales
- RNF1: Modo A funciona con `file://`, sin Internet ni dependencias.
- RNF2: Interfaz en español, adaptable a móvil, operable por teclado, foco visible, respeta `prefers-reduced-motion`, estados no comunicados solo por color.
- RNF3: Secretos en `.env` fuera de `public`; token interno PHP↔Python; consultas parametrizadas; transacciones.
- RNF4: Python y JavaScript con idénticos criterios y redondeo.
- RNF5: Pocas dependencias (cero en A/B; solo `mysql-connector-python` en C).

## 9. Historias de usuario (resumen)
- HU1 «Como operador quiero ejecutar el análisis y ver el índice» → 90% con 21 incidencias en 8 hallazgos.
- HU2 «…ver quién es responsable de cada dato» → responsable y dominio visibles por activo.
- HU3 «…ver la evidencia de cada problema» → valores y refs `tabla:row_id`.
- HU4 «…registrar mi decisión con comentario» → evento acumulativo, ≤1000 caracteres.
- HU5 «…consultar ejecuciones pasadas y exportarlas» → bitácora + JSON.

## 10. Arquitectura
Navegador → PHP (`public/api.php`) → servicio Python (`backend/app.py`) → MySQL (`nexo_source`, `nexo_app`). PHP nunca toca MySQL directamente. Detalle en `docs/arquitectura.md`.

## 11. Métricas de calidad
`índice = redondear((comprobaciones − incidencias) / comprobaciones × 100)`; sin comprobaciones → «Sin evaluar». Muestra de referencia: 208 comprobaciones, 21 incidencias, 8 hallazgos, 90%.

## 12. Modos de ejecución
- **A:** `public/index.html` directo; reglas en JS; `localStorage` (o solo sesión). Sin agentes reales.
- **B:** Python `--demo` (memoria, se pierde al reiniciar) + PHP en `127.0.0.1:8000`. Agentes con proveedor de prueba.
- **C:** Python con MySQL (lee fuente, persiste todo); errores visibles, sin repliegue silencioso.
- **Agentic habilitado:** requiere Python y proveedor configurado (`NEXO_AI_PROVIDER=openai` + `NEXO_AI_API_KEY`); analiza la muestra o la fuente autorizada. Sin clave, el proveedor de prueba demuestra el flujo sin IA real.

## 13. Riesgos y limitaciones
- Sin MySQL instalado solo funcionan A y B (historial en memoria).
- Alcance local de un equipo: autenticación propia con roles básicos (operador, lector, admin) y auditoría, sin integración empresarial.
- Reglas fijas: no detectan problemas semánticos complejos.
- Límite de 10 000 filas por tabla en esta versión.

## 14. Backlog por incrementos
- **Inc. 1 (MVP base):** recorrido completo + 3 modos + docs.
- **Inc. 2 (agentic, implementado):** proveedor desacoplado (real OpenAI-compatible + prueba), 3 agentes + orquestador, trabajos en segundo plano, revisión humana, persistencia agentic, Centro de agentes. Corrida real verificada contra un proveedor externo (ver README §10).
- **Inc. 3 (implementado):** carga gobernada (formulario + importación CSV con vista previa y auditoría), edición de metadatos y paginación.
- **Inc. 4 (implementado):** usuarios con roles (operador, lector, admin), administración con auditoría de acciones y recuperación de contraseña con código de un solo uso.
- **Inc. 5 (pendiente):** más reglas (rangos, fechas, referencias entre tablas), pruebas de equivalencia Py↔JS y copias de seguridad documentadas de `nexo_app`.
- **Visión:** planificador proactivo y más herramientas de solo lectura, siempre con aprobación humana antes de escribir.
