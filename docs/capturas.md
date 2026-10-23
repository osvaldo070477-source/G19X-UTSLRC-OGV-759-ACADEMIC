# Capturas de pantalla (evidencia visual)

Estado: **0 imágenes en el repositorio**. Este documento fija qué capturar, con
qué nombre guardarlo y en qué sección del `README` se enlaza.

## Requisitos comunes

- Modo **conectado** (PHP 8.1+ y Python) con sesión iniciada. La captura 1
  también puede tomarse en modo demostración, indicándolo.
- Ventana amplia (≈1280×800) y zoom al 100 % para que el texto se lea.
- Datos **sintéticos**: no debe aparecer ninguna clave, token interno, correo
  personal real ni la barra de direcciones con parámetros sensibles.
- Formato PNG o JPG; conservar el nombre base indicado.

## Lista de capturas

| # | Archivo | Vista | Qué debe verse | Se enlaza en |
|---|---------|-------|----------------|--------------|
| 1 | `docs/capturas/01-observatorio.png` | Observatorio | Tras pulsar **Ejecutar análisis**: modo activo, 44 registros y **208 comprobaciones · 21 incidencias · 8 hallazgos · índice 90 %** | README §1 y §8 |
| 2 | `docs/capturas/02-calidad.png` | Calidad | Un hallazgo **abierto**, mostrando el cajón de **evidencia** con el valor y la referencia `tabla:row_id` | README §8 |
| 3 | `docs/capturas/03-agentes.png` | Centro de agentes | Proveedor en **«IA habilitada»** (o «proveedor de prueba»), con un trabajo, sus **etapas** y las **herramientas** ejecutadas | README §5 |
| 4 | `docs/capturas/04-agente-13.png` | Centro de agentes | Detalle del trabajo **#13** (`completado`, `gemini-3.5-flash`, ~82 s, 8 recomendaciones) | README §10 |

Las capturas **1–3** son las tres vistas de interfaz solicitadas (Observatorio,
Calidad, Agentes). La captura **4** es la prueba visual del recorrido agentic.

## Cómo tomarlas

1. Inicia MySQL y los dos servicios como indica el `README` §3.
2. Abre `http://127.0.0.1:8000` e inicia sesión.
3. **Captura 1:** Observatorio → **Ejecutar análisis** → espera el resultado.
4. **Captura 2:** Calidad → abre un hallazgo → **Ver evidencia**.
5. **Captura 3:** Agentes → selecciona un trabajo → deja ver etapas y herramientas.
6. **Captura 4:** Agentes → **Ver** en el trabajo **#13** → etapas, herramientas y recomendaciones.
7. Guarda cada imagen en `docs/capturas/` con el nombre exacto de la tabla.

## Enlace en el README

Cuando los archivos existan, se referencian con rutas relativas:

```markdown
![Observatorio](docs/capturas/01-observatorio.png)
![Calidad](docs/capturas/02-calidad.png)
![Centro de agentes](docs/capturas/03-agentes.png)
![Trabajo #13](docs/capturas/04-agente-13.png)
```

## Verificación antes de publicar

- [ ] Los cuatro archivos existen en `docs/capturas/`.
- [ ] Se leen las cifras 208 / 21 / 8 / 90 % sin ampliar la imagen.
- [ ] La captura 4 muestra el trabajo **#13** completado y su modelo.
- [ ] No hay claves, tokens ni correos reales en pantalla.
- [ ] El `README` muestra las imágenes (no enlaces rotos).
