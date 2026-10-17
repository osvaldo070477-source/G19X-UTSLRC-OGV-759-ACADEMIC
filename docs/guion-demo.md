# Guion de demostración para el asesor

Recorrido de unos 10 minutos para mostrar el funcionamiento completo de NEXO
en el orden de la historia de usuario: **portada → análisis (208/21/90) →
evidencia → decisión → Centro de agentes → bitácora**.

## Antes de empezar (preparación)

1. Modo recomendado: **C (PHP + Python + MySQL)**.
   - Iniciar MySQL y aplicar las migraciones `sql/01…10` (ver README §3).
   - Arrancar los servicios:
     ```powershell
     .\.venv\Scripts\python.exe backend\app.py --port 8001
     php -S 127.0.0.1:8000 server/router.php
     ```
   - Abrir <http://127.0.0.1:8000>.
   - Si no hay MySQL disponible, usar **modo B**: `backend\app.py --demo --port 8001`.
2. Comprobar el estado del proveedor de IA: **«IA habilitada»** si hay clave en
   `.env`, o **«proveedor de prueba»** si no (ambos demuestran el flujo).
3. Tener a mano tu usuario y contraseña; evita cuentas o datos personales reales.
4. Verificación rápida previa: confirmar que el análisis da **208 / 21 / 90**.

## Recorrido paso a paso

### 1. Portada (30 s)
- **Qué se ve:** la bienvenida con la explicación del recorrido.
- **Qué decir:** «NEXO recorre conocer → verificar → evidenciar → recomendar →
  decidir → auditar. La IA no calcula; el motor determinista sí.»
- Nota: la aplicación real siempre parte de la portada de bienvenida.

### 2. Observatorio — ejecutar análisis (1,5 min)
- Pulsar **Ejecutar análisis**.
- **Mostrar:** 44 registros, **208 comprobaciones · 21 incidencias ·
  8 hallazgos · índice 90 %**.
- **Qué decir:** «Son cifras calculadas y reproducibles; idénticas en Python y
  JavaScript (RF2/RNF4), nunca escritas a mano.»

### 3. Evidencia (2 min)
- Ir a **Calidad** y filtrar por tabla, prioridad y regla.
- **Abrir un hallazgo** para ver el cajón de **evidencia**: el valor observado y
  la referencia **`tabla:row_id`** (p. ej. el `id` duplicado `CLI-004`).
- **Qué decir:** «Cada hallazgo es auditable; `row_id` es la clave técnica y `id`
  es la clave de negocio con el duplicado intencional.»

### 4. Decisión (1,5 min)
- Ir a **Decisiones**.
- **Aceptar** una propuesta (con comentario) y **reabrir** otra.
- **Mostrar:** se crea un **evento nuevo** y **aceptar no cambia los datos ni el
  índice**.
- **Qué decir:** «La decisión registra intención, no corrige; queda firmada con mi
  nombre y el historial es acumulativo.»

### 5. Centro de agentes (3 min)
- Ir a **Agentes** y mostrar el **estado del proveedor**.
- Explicar los estados del trabajo: *pendiente → en ejecución → (revisión) →
  completado/fallido/cancelado*, con **reintento explícito**.
- Señalar: **9 herramientas autorizadas**, **límites** de pasos/llamadas y
  **revisión humana** antes de escribir.
- Si está disponible, abrir el trabajo real **#13** (`completado`,
  `gemini-3.5-flash`, ~82 s, **8 recomendaciones**) y su detalle de etapas.
- **Qué decir:** «El modelo elige herramientas; el motor valida los conteos;
  nada se escribe sin aprobación humana.»

### 6. Bitácora (1 min)
- Ir a **Bitácora**: últimas ejecuciones con fecha, volumen, hallazgos e índice.
- **Exportar JSON** del análisis actual.

### 7. Cierre (1 min)
- Resumir **límites**: datos sintéticos, autenticación local de un equipo
  pequeño, sin linaje ni monitoreo continuo (visión futura).
- Mencionar los **siguientes pasos**: más reglas y validación con usuarios.

## Preguntas previsibles

- **¿La IA calcula o inventa números?** No: el motor determinista calcula todo;
  el modelo solo elige herramientas autorizadas y propone; hay revisión humana.
- **¿Modifica los datos?** No al decidir; aceptar registra intención. Sí escribe
  la **carga gobernada** (formulario/CSV), siempre con auditoría.
- **¿Cuánto cuesta?** El proveedor de prueba es gratuito; la corrida real se hizo
  con la cuota gratuita del proveedor.
- **¿Es seguro?** Secretos fuera de `public`, token interno PHP↔Python, CSRF en
  escrituras, cuentas MySQL separadas y consultas parametrizadas.

## Qué evitar

- No decir que NEXO «corrige» o «limpia» los datos.
- No mostrar claves, tokens ni correos personales.
- No prometer porcentajes de ahorro sin una línea base medida.
