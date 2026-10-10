# Arquitectura de NEXO (explicación sencilla)

## Piezas y por qué existen
- **`public/` (lo que ves):** `index.html` (estructura), `styles.css` (diseño azul profundo + turquesa),
  `app.js` (interacción + motor de reglas en JS para el modo demostración). `api.php` es la puerta:
  recibe las peticiones del navegador y las reenvía al servicio Python con un token secreto.
  Existe para que el navegador nunca vea contraseñas ni hable directo con la base de datos.
- **`server/router.php`:** enrutador para el servidor integrado de PHP (`php -S`). Sirve solo archivos
  de `public/` y manda `/api*` a `api.php`. Existe para que ningún archivo privado quede expuesto.
- **`backend/app.py`:** servicio Python con biblioteca estándar. Expone `/api/health`, `/api/analyze`,
  `/api/runs`, `/api/decisions`, `/api/catalog`. Existe porque concentra la lógica y el acceso a datos.
- **`backend/rules.py`:** motor de reglas deterministas (obligatoriedad, unicidad, correo). Existe para que
  los criterios sean explícitos, auditables e idénticos a los de `app.js`.
- **`backend/sample.py`:** muestra sintética + metadatos (responsables, dominios). Existe para demostrar
  sin datos reales.
- **`sql/`:** `nexo_source` (datos) y `nexo_app` (resultados). Dos bases y dos cuentas separan
  «mirar la fuente» (solo lectura) de «registrar resultados» (permisos limitados).
- **`scripts/`:** `gen_env.py` crea `.env` con secretos aleatorios; `check.py` verifica requisitos y totales.
- **`tests/test_rules.py`:** comprueba 208/21/8/90 y cada regla con la biblioteca estándar.

## Cómo se comunican
1. El navegador pide `api.php?action=analyze`.
2. PHP valida la petición, añade la cabecera `X-NEXO-Token` y la reenvía a Python (`http://127.0.0.1:8001`).
3. Python ejecuta `analyze_tables`, guarda (memoria o MySQL en transacción) y responde JSON.
4. PHP devuelve ese JSON al navegador; los secretos nunca viajan al cliente.

## Decisiones de diseño
- Sin frameworks ni CDNs: el modo A debe abrirse con doble clic y sin Internet.
- PHP no toca MySQL: una sola pieza (Python) habla con la base, con consultas parametrizadas.
- Decisiones como eventos acumulativos: el historial nunca se sobrescribe.
- Errores explícitos: si MySQL falla, se muestra; jamás se finge con datos simulados.

## Nota sobre C++
PHP y MySQL para Windows se distribuyen como programas ya compilados. Instalarlos es usar un
programa, no programar en C++; el proyecto no contiene ni exige código C++.
