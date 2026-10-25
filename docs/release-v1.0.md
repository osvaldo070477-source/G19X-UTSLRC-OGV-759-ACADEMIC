# NEXO v1.0 — Arquitectura Agentic para Data Governance (MVP)

Primera entrega académica del proyecto de estadías (UTSLRC): un recorrido local
de gobierno de datos sobre Clientes, Pedidos y Productos, con **reglas
deterministas** y agentes que proponen sin inventar cifras.

## Qué incluye

- **Recorrido completo:** catálogo → verificación → evidencia → recomendación →
  decisión → bitácora.
- **Centro de agentes:** 9 herramientas autorizadas, trabajos en segundo plano,
  revisión humana, cancelación y reintento.
- **Usuarios y roles:** operador, lector (403 en escrituras) y admin;
  administración auditada y recuperación con código de un solo uso.
- **Carga gobernada:** formulario por activo e importación CSV con vista previa
  y auditoría por fila.
- **Tres modos:** A (navegador sin servidor), B (PHP + Python en memoria) y
  C (PHP + Python + MySQL).

## Verificación

- Motor determinista: **208 comprobaciones · 21 incidencias · 8 hallazgos ·
  índice 90 %**.
- Suites: `test_rules` OK, `test_agents` **21/21**, `test_auth` **24/24**,
  `test_carga` **7/7** y equivalencia Python↔JavaScript en CI.
- CI en verde: pruebas y humo de extremo a extremo con MySQL, PHP y Python.
- Corrida real: trabajo **#13** con `gemini-3.5-flash`, 9 llamadas al modelo,
  9 herramientas, 10 577 tokens y **8 recomendaciones** (5 Alta, 3 Media).

## Documentación

- `README.md` (con las cuatro capturas enlazadas)
- `docs/PRD.md`, `docs/MVP.md`, `docs/arquitectura.md`, `docs/agentes.md`
- `docs/backlog.md`, `docs/capturas.md`
- `CHANGELOG.md` y `LICENSE` (MIT)

**Autor:** Osvaldo (`osvaldo070477-source`) · **Licencia:** MIT
