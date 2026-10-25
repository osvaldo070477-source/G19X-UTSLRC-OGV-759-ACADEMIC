# MVP — NEXO: Arquitectura Agentic para Data Governance

**Autor:** Osvaldo (`osvaldo070477-source`) · **Institución:** UTSLRC · **Fecha:** 2026-10-23 · **Actualizado:** 2026-10-25
**Entrega:** MVP académico (etiqueta `v1.0`; parche de endurecimiento `v1.0.1`) · **Licencia:** MIT
**Estado:** `v1.0.1` en `main`, CI verde · **Notas:** [release-v1.0.1.md](release-v1.0.1.md)

## 1. Qué es

NEXO es una aplicación **local** que demuestra el recorrido completo de gobierno
de datos: **conocer → verificar → evidenciar → recomendar → decidir → auditar**,
sobre datos **sintéticos** de Clientes, Pedidos y Productos.

La idea central que sostiene el MVP: **la Inteligencia Artificial no calcula**.
Las cifras las produce un **motor determinista de reglas**; el modelo solo elige
herramientas autorizadas y propone, y toda escritura pasa por **revisión humana**.

## 2. Qué entra en esta entrega

| Capacidad | Qué incluye | Requisitos |
|-----------|-------------|------------|
| Observatorio | Modo activo, activos, registros, índice, hallazgos y último análisis | RF1–RF2 |
| Catálogo | Activos con responsable, dominio, columnas y reglas; búsqueda y filtros | RF3 |
| Calidad | Hallazgos por tabla, prioridad y tipo; evidencia con valor y `tabla:row_id` | RF4 |
| Decisiones | Aceptar / descartar / reabrir con comentario (≤1000), historial acumulativo | RF5, RF7 |
| Bitácora | Últimas 20 ejecuciones y exportación a JSON | RF6 |
| Centro de agentes | Trabajos en segundo plano, 9 herramientas autorizadas, revisión humana, reintento | RF10–RF14 |
| Usuarios y roles | Registro/login, `operador`, `lector` (403 en escrituras), `admin`; sesiones de 8 h | RF15–RF16 |
| Administración | Activar/desactivar, desbloquear, restablecer claves, cambiar rol; auditoría | RF17 |
| Carga gobernada | Formulario por activo e importación CSV con vista previa y auditoría por fila | RF18–RF19 |
| Recuperación | Código de un solo uso; sin correo externo | RF20 |
| Paginación | Tablas de 10 en 10 sin perder eventos ni filtros | RF21 |
| Tres modos | A: navegador sin servidor · B: PHP + Python en memoria · C: PHP + Python + MySQL | RNF1, RNF5 |
| Equivalencia | Mismo resultado en Python y JavaScript | RNF4 |

**Cifras de referencia (calculadas, nunca escritas a mano):**
44 registros (20 + 14 + 10) · **208 comprobaciones** · **21 incidencias** ·
**8 hallazgos** · índice **90 %**.

## 3. Recorrido de la demostración

Duración objetivo: **10–12 minutos**. Esta es la versión corta para el asesor;
el guion del video es material aparte de la entrega.

1. **Entrar.** Iniciar sesión y mostrar el nombre y el rol en la barra lateral.
2. **Observatorio.** Pulsar **Ejecutar análisis** y leer las cifras: 208 / 21 / 8 / 90 %.
3. **Catálogo.** Señalar que cada activo tiene responsable, dominio y reglas.
4. **Calidad.** Abrir un hallazgo y mostrar la evidencia (`CLI-004`, fila `cli-04`).
5. **Decisiones.** Aceptar una recomendación con comentario; aclarar que **no corrige datos ni índice**.
6. **Bitácora.** Consultar una ejecución reciente y exportar el análisis a JSON.
7. **Centro de agentes.** Abrir el trabajo **#13**: etapas, 9 herramientas, 2 revisiones humanas y 8 recomendaciones.
8. **Administración y perfil.** Mostrar roles, auditoría, desbloqueo y el perfil propio.

**Frase que resume el cierre:** *«El motor calcula; la IA propone; la persona decide.»*

## 4. Evidencia que respalda el MVP

- **Pruebas:** `tests/test_rules.py` (OK), `tests/test_agents.py` (21/21),
  `tests/test_auth.py` (24/24), `tests/test_carga.py` (9/9) y
  `tests/test_equivalencia.py` (Python ↔ JavaScript).
- **Integración continua:** `.github/workflows/ci.yml` ejecuta las pruebas y un
  humo de extremo a extremo que levanta MySQL + PHP + Python y comprueba los
  tres roles (operador escribe, admin lista, lector recibe 403).
- **Corrida real con IA:** trabajo **#13**, proveedor `openai` (endpoint Gemini),
  modelo `gemini-3.5-flash`, `completado` en ~82 s, 9 llamadas al modelo,
  9 herramientas, 10 577 tokens y **8 recomendaciones** (5 Alta, 3 Media).
  El detalle está en el `README` §10.
- **Capturas:** las cuatro están en `docs/capturas/` y enlazadas en el `README`
  §1, §5, §8 y §10 (Observatorio, Calidad, Agentes y trabajo #13).

### Parche de endurecimiento 1.0.1

La entrega base es `v1.0`. Sobre ella, `v1.0.1` corrige la revocación de
sesiones, la autorización de la API, la robustez de la carga CSV, la redacción
de datos, las cabeceras de seguridad y la concurrencia. **No cambia las reglas,
los datos ni las cifras** (208/21/8/90); las capturas siguen vigentes. Detalle:
[release-v1.0.1.md](release-v1.0.1.md).

## 5. Qué queda fuera

Estas exclusiones son deliberadas y forman parte del alcance:

- **No corrige ni limpia datos.** Aceptar una recomendación registra una decisión;
  no cambia la fuente, no recalcula el índice y no ejecuta acciones autónomas.
- **La IA no calcula ni escribe.** Sin aprobación humana no hay escritura; el
  modelo no inventa conteos ni evidencias.
- **Sin autenticación empresarial:** sin SSO, sin directorios corporativos
  (Entra ID), sin jerarquías organizacionales; roles locales básicos.
- **Sin linaje, monitoreo continuo, cumplimiento normativo ni respaldos
  automáticos.** Son visión futura, no parte del MVP.
- **Sin integraciones externas** (Purview, Power BI, Azure AI Search, colas o
  contenedores). NEXO es local y no depende de servicios en la nube.
- **Reglas fijas:** obligatoriedad, unicidad y formato de correo. No hay
  detección semántica ni aprendizaje automático.
- **Sin validación externa:** no hay entrevistas con empresas, ahorros medidos
  ni piloto en producción (proyecto académico).
- **Límites operativos:** 10 000 filas por tabla y 500 filas por lote de CSV.

## 6. Cómo ejecutarlo

- **Modo A (sin instalar):** abrir `public/index.html` en el navegador.
- **Modo B (sin MySQL):** `python backend/app.py --demo --port 8001` + `php -S 127.0.0.1:8000 server/router.php`.
- **Modo C (completo):** MySQL 8 según el orden de `sql/` y los dos servicios sin `--demo`.

El detalle paso a paso, las variables y la verificación están en el `README`.

## 7. Criterios de aceptación

El MVP se considera entregado cuando:

1. Un análisis de la muestra devuelve **208 / 21 / 8 / 90 %** sin editar código.
2. La evidencia de un hallazgo permite localizar la fila exacta (`tabla:row_id`).
3. Aceptar una recomendación **no** modifica la fuente ni el índice.
4. El rol `lector` recibe **403** en las escrituras.
5. Un trabajo agentic deja etapas, herramientas, tokens y recomendaciones guardadas.
6. Las pruebas y el humo de CI terminan en verde.
7. Las cuatro capturas de `docs/capturas.md` están enlazadas en el `README`.
