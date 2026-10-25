# Capturas de pantalla (evidencia visual)

Estado: **4 imágenes verificadas en `docs/capturas/`**, enlazadas en el `README`.
Verificación visual: **2026-10-25** (commit `785cb83`). Este documento fija qué
capturar, con qué nombre guardarlo y en qué sección se enlaza.

## Requisitos comunes

- Modo **conectado** (PHP 8.1+ y Python) con sesión iniciada. La captura 1
  también puede tomarse en modo demostración, indicándolo.
- Ventana amplia (≈1280×800) y zoom al 100 % para que el texto se lea.
- Datos **sintéticos**: no debe aparecer ninguna clave, token interno, correo
  personal real ni la barra de direcciones con parámetros sensibles.
- Formato PNG o JPG; conservar el nombre base indicado.

## Lista de capturas

| # | Archivo | Vista | Qué debe verse | Dimensiones | Se enlaza en |
|---|---------|-------|----------------|-------------|--------------|
| 1 | `docs/capturas/01-observatorio.png` | Observatorio | Tras pulsar **Ejecutar análisis**: modo activo, 44 registros y **208 comprobaciones · 21 incidencias · 8 hallazgos · índice 90 %** | 1919×937 | README §1 |
| 2 | `docs/capturas/02-calidad.png` | Calidad | Un hallazgo **abierto**, mostrando el cajón de **evidencia** con el valor y la referencia `tabla:row_id` | 1919×943 | README §8 |
| 3 | `docs/capturas/03-agentes.png` | Centro de agentes | Panel **Proveedor** con «IA habilitada» y el modelo, más el formulario de inicio | 1907×770 | README §5 |
| 4 | `docs/capturas/04-agente-13.png` | Centro de agentes | Detalle del trabajo **#13**: `completado`, las cuatro etapas cerradas y las **8 recomendaciones** (5 Alta, 3 Media) | 1355×805 | README §10 |

Las capturas **1–3** son las tres vistas de interfaz solicitadas (Observatorio,
Calidad, Agentes). La captura **4** es la prueba visual del recorrido agentic.

## Cómo tomarlas

1. Inicia MySQL y los dos servicios como indica el `README` §3.
2. Abre `http://127.0.0.1:8000` e inicia sesión.
3. **Captura 1:** Observatorio → **Ejecutar análisis** → espera el resultado.
4. **Captura 2:** Calidad → abre un hallazgo → **Ver evidencia**.
5. **Captura 3:** Agentes → parte superior, con el panel **Proveedor** visible.
6. **Captura 4:** Agentes → elige el trabajo **#13** → baja hasta las etapas y las recomendaciones.
7. Guarda cada imagen en `docs/capturas/` con el nombre exacto de la tabla.

## Enlace en el README

Se referencian con rutas relativas (ya enlazadas):

```markdown
![Observatorio](docs/capturas/01-observatorio.png)
![Calidad](docs/capturas/02-calidad.png)
![Centro de agentes](docs/capturas/03-agentes.png)
![Trabajo #13](docs/capturas/04-agente-13.png)
```

## Verificación antes de publicar

- [x] Los cuatro archivos existen en `docs/capturas/`.
- [x] Se leen las cifras 208 / 21 / 8 / 90 % sin ampliar la imagen.
- [x] La captura 4 muestra el trabajo **#13** completado, con las etapas cerradas.
- [x] No hay claves, tokens ni correos reales en pantalla.
- [x] El `README` muestra las imágenes (no enlaces rotos).

Verificado el **2026-10-25** sobre el commit `785cb83`.
