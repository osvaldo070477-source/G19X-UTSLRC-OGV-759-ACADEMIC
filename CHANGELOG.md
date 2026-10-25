# Historial de cambios

Todos los cambios relevantes de NEXO se registran en este archivo.
Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y versionado [semántico](https://semver.org/lang/es/).

## [1.0] - 2026-10-24

Primera entrega académica: MVP local de gobierno de datos con centro de agentes.

### Añadido
- Recorrido guiado de gobierno de datos: Observatorio, Catálogo, Calidad, Decisiones y Bitácora.
- Motor de reglas determinista como fuente de verdad: sobre la muestra de ejemplo da
  44 registros, 208 comprobaciones, 21 incidencias, 8 hallazgos e índice 90.
  La IA nunca inventa cifras; las recomendaciones parten de esos resultados.
- Centro de agentes con bucle de herramientas local. Proveedor real compatible con
  OpenAI/Gemini y proveedor de prueba (`stub`) para desarrollar sin clave.
- Autenticación local en MySQL: registro, inicio de sesión, sesión regenerada, CSRF,
  perfil con nombre, cambio de contraseña y actividad de la cuenta.
- Roles internos `operador`, `lector` (solo lectura) y `admin`, con gestión de cuentas
  y auditoría de las acciones de administración.
- Carga gobernada de datos a `nexo_source` (CSV y manual) con auditoría por fila en
  `nexo_app.source_audit`.
- Permisos mínimos de MySQL por usuario (`nexo_ro`, `nexo_app`, `nexo_wr`).
- Arranque en un clic de los servicios locales (`iniciar-nexo.bat`).
- Integración continua: pruebas de Python y humo de extremo a extremo
  (PHP → Python → MySQL) con comprobación de roles.
- Documento de MVP (`docs/MVP.md`): alcance, recorrido de la demostración y exclusiones.
- Capturas de pantalla de Observatorio, Calidad, Agentes y del trabajo #13 en
  `docs/capturas/`, enlazadas en el README.
- Pruebas de equivalencia Python/JavaScript del motor de reglas
  (`tests/test_equivalencia.py`), ejecutadas en CI.
- Documentación: PRD, arquitectura, agentes, backlog y lista de capturas.
- Licencia MIT.

### Cambiado
- README: §9 describe el equipo pequeño con roles, §5 usa el timeout real (180)
  y §4 lista toda la documentación (incluidos `MVP.md` y `capturas.md`).
- `scripts/gen_env.py` genera `NEXO_AI_TIMEOUT_S=180`, igual que `.env.example`
  y el valor por defecto del código.
- Interfaz dividida en módulos por pantalla (`public/js/`).
- Sistema visual único con variables CSS, iconos SVG (sin emojis) y estados vacíos con acción.
- Accesibilidad: enlace «Saltar al contenido» con foco real, anillo de foco visible en
  campos de formulario y barra de avisos como región `status`.

### Corregido
- La etapa **Calidad** se mostraba «En curso» en un trabajo completado cuando la
  etapa se reanudaba tras una revisión humana: ahora se emite el cierre y la
  interfaz lo refleja también en los trabajos antiguos.
- Detalle del trabajo del agente en modo MySQL: las fechas anidadas no se
  serializaban y cerraban la conexión, mostrando un falso «no se pudo contactar
  al servicio Python» al pulsar **Ver**.
- Listado de trabajos del agente y bucle del modelo en corridas reales.
- Permisos de MySQL (evita el error 1142) y mensajes de error sin filtrar detalles internos.
- Paginación idempotente y varios ajustes de la interfaz.

[1.0]: https://github.com/osvaldo070477-source/G19X-UTSLRC-OGV-759-ACADEMIC/releases/tag/v1.0
