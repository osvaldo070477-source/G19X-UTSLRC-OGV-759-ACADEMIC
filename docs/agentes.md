# Agentes de NEXO (explicación sencilla)

## Qué problema resuelven
Las reglas fijas siempre ejecutan lo mismo. Los agentes añaden criterio:
el modelo de lenguaje decide **qué herramientas autorizadas usar y en qué
orden** según lo que va encontrando, y propone acciones en lenguaje claro.
Lo verificable (conteos, índice, evidencias) lo sigue calculando el motor
determinista; el modelo nunca inventa cifras.

## Qué hace cada agente
- **Catálogo:** explora tablas, estructura y conteos con herramientas de
  solo lectura. Puede proponer descripciones, marcadas como pendientes;
  jamás inventa responsables.
- **Calidad:** elige comprobaciones (obligatoriedad, unicidad, correo),
  las ejecuta y confirma hallazgos. Si su confirmación no coincide con el
  motor, el orquestador usa el motor y pide revisión humana.
- **Recomendaciones:** propone una acción concreta por hallazgo citando
  referencias reales (`tabla.columna.regla`). No corrige ni borra datos;
  indica si necesita revisión.
- **Orquestador:** coordina las etapas, valida cada decisión del modelo,
  impone límites (pasos, llamadas, tiempo), detecta bucles y pide
  revisión o detiene el trabajo cuando corresponde.

## Qué decide el modelo y qué ejecutan las herramientas
- El modelo decide: qué herramienta usar, con qué argumentos permitidos,
  cuándo pedir revisión y qué proponer.
- Las herramientas ejecutan: lecturas y comprobaciones con consultas
  parametrizadas o la muestra en memoria. Sin comandos del sistema ni SQL
  arbitrario.

## Por qué existe cada componente
- `backend/providers.py`: habla con el proveedor (adaptador real
  OpenAI-compatible + doble de prueba). Sin dependencias nuevas.
- `backend/agent_tools.py`: las 9 herramientas permitidas con validación
  y enmascarado de datos sensibles.
- `backend/agents.py`: instrucciones de cada agente y el orquestador.
- `backend/jobs.py`: trabajos en segundo plano con estados, cancelación,
  revisión, reintento y persistencia (memoria o MySQL).
- `sql/05_agentic.sql`: tablas de trabajos, pasos, llamadas,
  recomendaciones y revisiones (migración sin borrar nada).
- Centro de agentes (interfaz): estado del proveedor, progreso por
  etapas, herramientas ejecutadas, revisiones, errores e historial.

## Qué datos salen hacia el proveedor
Solo metadatos (nombres de tablas/columnas, responsables configurados),
agregados (conteos, perfiles) y evidencias mínimas con correos
enmascarados (`a***@dominio`) y textos truncados. Nunca salen claves,
contraseñas ni tablas completas. El contenido de los datos se trata como
texto no confiable, nunca como instrucciones.

## Límites de esta versión local
Un operador, un trabajo revisado a la vez en la interfaz, sin corrección
automática de datos. Sin clave de API solo funciona el proveedor de
prueba (etiquetado, no es IA real). No es producción empresarial.
