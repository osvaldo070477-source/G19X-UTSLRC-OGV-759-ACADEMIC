# Backlog propuesto (organización Scrum sugerida)

## Sprint 0 — Base (completado)
- Estructura del proyecto, muestra sintética, motor de reglas Py+JS, interfaz, 3 modos, docs.

## Sprint 1 — Agentic (completado)
- Proveedor desacoplado (OpenAI-compatible real + prueba), 9 herramientas
  validadas, 3 agentes + orquestador, trabajos en segundo plano con estados,
  revisión humana, persistencia (`sql/05_agentic.sql`), Centro de agentes.
- 20 pruebas con doble de prueba y una corrida real verificada (ver README §10).

## Sprint 2 — Robustez y trazabilidad (completado)
- Paginación de evidencias, catálogo y bitácora.
- Carga gobernada: formulario e **importación CSV** con vista previa y auditoría (`sql/09_carga.sql`).
- Metadatos editables (descripción y responsable) solo por admin.

## Sprint 3 — Equipo y control de acceso (completado)
- Usuarios con roles (`operador`, `lector`, `admin`), sesiones y decisiones firmadas.
- Administración: activar/desactivar, desbloquear, restablecer claves y cambiar rol, con **auditoría de acciones** (`sql/10_admin_audit.sql`).
- Recuperación de contraseña con código de un solo uso y regeneración desde el perfil.

## Sprint 4 — Pendiente
- Más reglas: rangos numéricos, formato de fecha y referencias entre tablas.
- Pruebas de equivalencia automatizadas Py↔JS (generar casos y compararlos).
- Copias de seguridad documentadas de `nexo_app`.

## Visión
- Planificador proactivo y más herramientas de solo lectura, siempre con aprobación humana antes de escribir.
- Todo agente debe dejar rastro en la bitácora; ninguna acción autónoma toca la fuente sin permiso.
