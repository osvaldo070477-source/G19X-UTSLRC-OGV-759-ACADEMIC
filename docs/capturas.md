# Capturas de pantalla (pendientes)

Estado: **todavía no hay imágenes en el repositorio** (0 archivos `*.png`/`*.jpg`).
Esta lista indica exactamente qué capturar para la entrega. Cuando las tengas,
guárdalas en `docs/capturas/` con el nombre indicado y avísame para enlazarlas
en el `README`.

## Requisitos comunes

- Ejecutar en **modo conectado** (PHP 8.1+ y Python) con sesión iniciada
  (o modo demostración para la captura 1, indicándolo).
- Ventana amplia (≈1280×800) y zoom al 100 % para que el texto se lea.
- La muestra es **sintética**: no debe aparecer ninguna clave, token interno ni
  dato personal real.

## Lista de capturas

| # | Archivo | Vista | Qué debe verse | Se enlazará en |
|---|---------|-------|----------------|----------------|
| 1 | `docs/capturas/01-observatorio.png` | Observatorio | Tras pulsar **Ejecutar análisis**: modo activo, 44 registros y **208 comprobaciones · 21 incidencias · 8 hallazgos · índice 90 %** | README §1 y §8 |
| 2 | `docs/capturas/02-calidad.png` | Calidad | Un hallazgo **abierto**, mostrando el cajón de **evidencia** con el valor y la referencia `tabla:row_id` | README §8 |
| 3 | `docs/capturas/03-agentes.png` | Centro de agentes | Proveedor en **«IA habilitada»** (o «proveedor de prueba»), con un trabajo, sus **etapas** y las **herramientas** ejecutadas | README §5 |
| 4 | `docs/capturas/04-agente-13.png` | Centro de agentes | Detalle del trabajo **#13** (`completado`, `gemini-3.5-flash`, ~82 s, 8 recomendaciones) | README §10 |

## Notas

- Las capturas **1–3** son las tres capturas de interfaz solicitadas
  (Observatorio, Calidad, Agentes).
- La captura **4** es la del trabajo real **#13** (punto A1 de la lista).
- Sirve PNG o JPG; conservar el nombre base indicado.
- Las imágenes se guardan bajo `docs/capturas/` y se referencian desde el README
  con rutas relativas, por ejemplo: `docs/capturas/01-observatorio.png`.
