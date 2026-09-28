# Backlog propuesto (organización Scrum sugerida)

## Sprint 0 — Base (completado)
- Estructura del proyecto, muestra sintética, motor de reglas Py+JS, interfaz, 3 modos, docs.

## Sprint 1 — Agentic (completado)
- Proveedor desacoplado (OpenAI-compatible real + prueba), 9 herramientas
  validadas, 3 agentes + orquestador, trabajos en segundo plano con estados,
  revisión humana, persistencia (`sql/05_agentic.sql`), Centro de agentes,
  20 pruebas con doble de prueba.

## Sprint 2 — Robustez (pendiente)
- Paginación de evidencias y catálogo.
- Más reglas: rangos numéricos, formato de fecha, totales negativos.
- Pruebas de equivalencia automatizadas Py↔JS (generar casos y compararlos).

## Sprint 2 — Trazabilidad
- Filtros por fecha en bitácora, vista de eventos por hallazgo.
- Importación de CSV a `nexo_source` con validación previa.

## Sprint 3 — Equipo
- Operadores y roles básicos (quién decidió qué).
- Copias de seguridad documentadas de `nexo_app`.

## Visión — Agentes (futuro, fuera del MVP)
1. **Planificador:** sugiere qué verificar según cambios en la fuente.
2. **Ejecutor:** usa herramientas (consultas, reglas) dentro de límites.
3. **Revisor:** pide aprobación humana antes de cualquier escritura.
Todo agente debe dejar rastro en la bitácora; ninguna acción autónoma toca la fuente sin permiso.
