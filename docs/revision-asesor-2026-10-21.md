# Revisión del asesor — 21 de octubre de 2026

**Estado:** puntos atendidos en `main` al **2026-10-25**.
**Versión:** `v1.0.1` (tag anotado sobre `785cb83`).
**CI:** run 48 en verde: trabajos `test` y `smoke` (MySQL + PHP + Python).
**Release:** no publicado al 2026-10-25; el texto está listo en
[release-v1.0.1.md](release-v1.0.1.md).
**SGPA:** `docs/MVP.md` está listo para subir; la carga a Documentos del SGPA
queda como acción externa.

## 1. Puntos de la revisión

| # | Observación | Estado | Evidencia |
|---|-------------|--------|-----------|
| 1 | Subir lo local en commits pequeños, aunque esté incompleto | Resuelto | 8 commits de endurecimiento desde `1949f83` (`a9a3dd3` … `785cb83`); el árbol quedó limpio y sincronizado antes de agregar este documento |
| 2 | Guardar las 4 capturas en `docs/capturas/` y enlazarlas en el README (§1, §5, §8 y §10), sobre todo la del trabajo #13 | Resuelto | Cuatro PNG en `docs/capturas/`; enlaces en `README.md` §1, §5, §8 y §10; la captura 04 muestra el trabajo #13 con 4 etapas y 8 recomendaciones; commit `034f120`; verificación visual 2026-10-25 |
| 3 | Agregar un documento de MVP con qué entra, recorrido de la demostración y qué queda fuera | Resuelto | `docs/MVP.md` §2 (qué entra), §3 (recorrido), §5 (qué queda fuera) y §7 (criterios); commit `8410db9`; actualizado a 1.0.1 |
| 4 | Quitar «App local de un solo operador» del README §9 | Resuelto | `README.md` §9 describe un equipo pequeño con roles `operador`, `lector` y `admin`; commit `8410db9` |
| 5 | Unificar `NEXO_AI_TIMEOUT_S` en 180 (§5) | Resuelto | Texto y tabla de `README.md` §5 usan **180**; commits `35afcc2` y `8410db9` |
| 6 | Quitar de `docs/capturas.md` la frase dirigida a un asistente | Resuelto | `docs/capturas.md` §Enlace dice «ya enlazadas»; commit `8410db9` |

## 2. Endurecimiento adicional 1.0.1

| Cambio | Commit | Verificación |
|--------|--------|--------------|
| Revocación de sesiones al desactivar, restablecer, recuperar o cambiar contraseña | `a9a3dd3` | `test_auth` 24/24 |
| Sesión obligatoria en la API y refresco de la interfaz tras el login | `d49fb01` | CI: 401 sin sesión y 403 con origen ajeno; humo local |
| CSV con BOM, fechas reales, números finitos y longitudes | `9ec5912` | `test_carga` 9/9 |
| Redacción de correos incompletos y validación de `maximo` | `36c4469` | `test_agents` 21/21 |
| Cabeceras de seguridad, origen exacto y límite de rutas estáticas | `869c954` | Prueba PHP en vivo: CSP/XFO/nosniff, 403 y 404 |
| Cuerpo vacío de PHP a Python como objeto JSON | `dce2fbc` | Humo local PHP → Python |
| Versión 1.0.1, CHANGELOG y notas | `a5744ed` | `VERSION` y `docs/release-v1.0.1.md` |
| Validación JSON del humo de CI | `785cb83` | Run 48: `test` y `smoke` en verde |

El endurecimiento **no cambia las reglas, los datos ni las cifras**: siguen siendo
**208 comprobaciones · 21 incidencias · 8 hallazgos · índice 90 %** (44 registros).

## 3. Verificación ejecutada

- `tests/test_rules.py`: 208/21/8/90 y 44 registros.
- `tests/test_agents.py`: **21/21**.
- `tests/test_auth.py`: **24/24**.
- `tests/test_carga.py`: **9/9**.
- `scripts/check.py` y `scripts/check_ui.py`: OK.
- PHP 8.4: sintaxis correcta en `public/api.php`, `public/index.php` y `server/router.php`.
- Humo local PHP → Python: 401 sin sesión, 403 con origen ajeno, registro 201,
  análisis 200 con índice 90 y 401 después del logout.
- CI: [run 48](https://github.com/osvaldo070477-source/G19X-UTSLRC-OGV-759-ACADEMIC/actions/runs/40170477168), `test` y `smoke` en verde.
- `git status` limpio antes de este documento; la entrega de código está en
  `785cb83` y el tag `v1.0.1` apunta ahí.

## 4. Pendiente externo

- Subir `docs/MVP.md` a **Documentos del SGPA**.
- Publicar el **release de GitHub** con el tag `v1.0.1`; el entorno no tiene
  credenciales de GitHub y actualmente hay **0 releases publicados**.
