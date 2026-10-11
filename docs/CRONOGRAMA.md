# Desglose — Actividad 4. Realización del Proyecto completo (NEXO)

Distribución del trabajo implementado para el cronograma Sem5–Sem8.

## Sem5 — Base funcional (MVP local)
1. Estructura del proyecto y repositorio GitHub (público, sin secretos).
2. Interfaz: portada, Observatorio, Catálogo, Calidad, Decisiones, Bitácora.
3. Motor de reglas deterministas idéntico en Python y JavaScript.
4. API PHP↔Python con token interno; MySQL `nexo_source` (lectura) y `nexo_app` (escritura).
5. Muestra sintética + seed SQL idempotente + scripts (`gen_env`, `check`) + tareas VS Code.
6. Tres modos: demo sin instalaciones, PHP+Python en memoria y MySQL conectado.

## Sem6 — Agentes con IA
7. Proveedor desacoplado OpenAI-compatible (verificado contra documentación) + doble de prueba etiquetado.
8. 9 herramientas autorizadas, orquestador y 3 agentes (catálogo, calidad, recomendaciones).
9. Trabajos en segundo plano con estados, revisión humana, cancelación y reintento.
10. Centro de agentes en la interfaz; compatibilidad Gemini (historial plano, reintentos 429/503).
11. Migración `05_agentic.sql` y pruebas 20/20.

## Sem7 — Usuarios, acceso y diseño
12. Registro/login con validaciones, PBKDF2, bloqueo, sesiones 8 h; corrección del error 1142 con permisos mínimos (`07_permisos.sql`).
13. Perfil (ficha, cambio de nombre/clave, actividad), CSRF y modo invitado solo en demo.
14. Rol admin: script de primer admin y panel de administración (RF17).
15. Rediseños: barra lateral compacta, portada separada y tema oscuro tipo panel.

## Sem8 — Datos, calidad y cierre
16. Muestra ampliada 26→44 registros (208 comprobaciones, 21 incidencias, 8 hallazgos, índice 90) con re-sembrado MySQL.
17. Suites completas (reglas, agentes, auth, UI) + CI automático en GitHub.
18. Documentación: PRD, manuales, reporte QA, plan maestro, informe y acta.
