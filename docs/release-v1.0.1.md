# NEXO v1.0.1 — Endurecimiento de seguridad y robustez

Parche sobre la entrega **v1.0** del MVP académico. No cambia el alcance, las
reglas, los datos ni las cifras: el motor determinista sigue dando **208
comprobaciones · 21 incidencias · 8 hallazgos · índice 90 %**.

## Qué corrige

- **Sesiones:** se revocan al desactivar una cuenta, restablecerla, recuperar la
  contraseña o cambiarla; al cambiarla se conserva solo la sesión actual.
- **API:** en modo servidor exige sesión (401 sin ella); el humo de CI comprueba
  también el rechazo de un origen ajeno (403).
- **CSV:** acepta BOM UTF-8 y rechaza fechas imposibles, números no finitos,
  valores fuera de rango y longitudes excesivas.
- **Redacción:** los correos incompletos o mal formados también se enmascaran;
  `maximo` se valida sin lanzar excepciones ante entradas inválidas.
- **Cabeceras:** CSP, `X-Frame-Options`, `X-Content-Type-Options`,
  `Referrer-Policy` y `Cache-Control: no-store` en HTML y API.
- **Origen y rutas:** comparación exacta de esquema, host y puerto; el límite de
  archivos estáticos ya no acepta directorios hermanos con el mismo prefijo.
- **Errores y concurrencia:** respuestas sin detalles internos, cuerpo JSON
  obligatoriamente objeto y `ThreadingHTTPServer` con contador de trabajos
  protegido.

## Verificación

- `tests/test_rules.py`: OK (208/21/8/90).
- `tests/test_agents.py`: **21/21**.
- `tests/test_auth.py`: **24/24**.
- `tests/test_carga.py`: **9/9**.
- `scripts/check.py` y `scripts/check_ui.py`: OK.
- Humo local PHP → Python: 401 sin sesión, 403 con origen ajeno, registro 201,
  análisis 200 con índice 90 y logout con 401 posterior.
- PHP 8.4: sintaxis correcta y prueba en vivo de cabeceras, origen ajeno (403) y
  travesía de rutas (404).
- La equivalencia Python ↔ JavaScript se ejecuta en CI (requiere Node).

## Documentación

- `README.md`, `docs/MVP.md`, `CHANGELOG.md` y esta nota.
- Capturas y corrida real del trabajo **#13** sin cambios.

**Autor:** Osvaldo (`osvaldo070477-source`) · **Licencia:** MIT
