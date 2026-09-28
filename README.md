# NEXO · Arquitectura Agentic para Data Governance (MVP)

Recorrido de gobierno de datos con **reglas deterministas verificables** y
**agentes reales**: el modelo decide qué herramientas autorizadas usar;
catálogo → análisis → evidencias → recomendaciones → decisiones → bitácora.

## 1. Demostración inmediata (sin instalar nada)

Abre con doble clic **`public/index.html`** en tu navegador.

- Verás **«Modo demostración — datos de ejemplo»**.
- Pulsa **Ejecutar análisis**: obtendrás 123 comprobaciones, 8 incidencias, 6 hallazgos e índice **93%** (calculados, no escritos a mano).
- Todo funciona sin Internet, sin PHP, sin Python y sin MySQL.
- Lo que decidas se guarda en el navegador (`localStorage`); si no está disponible, se avisa que durará solo la sesión.
- *Live Server de VS Code no ejecuta PHP: sirve la misma demostración.*

## 2. Modo PHP + Python sin MySQL (memoria)

Necesitas **Python 3.10+** y **PHP 8.1+** (este equipo ya los tiene). Sin dependencias extra.

```powershell
# 1) Crear entorno y .env (solo la primera vez)
python -m venv .venv
python scripts/gen_env.py

# 2) Iniciar el servicio Python (muestra sintética, memoria: se pierde al reiniciar)
.\.venv\Scripts\python.exe backend\app.py --demo --port 8001

# 3) En otra terminal, iniciar PHP (sirve solo public/)
php -S 127.0.0.1:8000 server/router.php

# 4) Abrir en el navegador
# http://127.0.0.1:8000
```

Verás **«Modo local — PHP · Python (memoria)»**. También puedes iniciar ambos servicios con
las tareas de VS Code: **NEXO: servicio Python** y **NEXO: servidor PHP**.
Documentación del flag: `--demo` usa la muestra sintética y guarda en memoria;
sin `--demo` intenta MySQL según `.env` y **falla con error visible** si no hay conexión
(nunca usa simulados en silencio). `backend/app.py --help` muestra `--host` y `--port`.

## 3. Modo completo con MySQL (cuando lo instales)

1. Instala **MySQL 8.0+** (programa ya compilado; instalarlo no es programar en C++).
2. Instala la única dependencia: `.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt`
3. Crea las bases desde el cliente `mysql` (en PowerShell **no** funciona `< archivo.sql`;
   usa `source` dentro del cliente):
   ```sql
   source sql/01_schema_source.sql
   source sql/02_schema_app.sql
   source sql/03_seed_source.sql
   -- sql/04_users_template.sql es plantilla: edita las contraseñas antes de ejecutarla
   ```
4. Copia `.env.example` o genera `.env` con `python scripts/gen_env.py` y anota las contraseñas reales.
5. Inicia Python **sin** `--demo` y PHP como en el punto 2. Verás **«Modo conectado — PHP · Python · MySQL»**.

## 4. Estructura

| Ruta | Qué es |
|------|--------|
| `public/` | `index.html`, `styles.css`, `app.js`, `api.php` (puerta a Python), `index.php` |
| `server/router.php` | Enrutador del servidor PHP (solo sirve `public/`) |
| `backend/` | `app.py` (servicio), `rules.py` (reglas), `sample.py` (muestra), `providers.py` (IA), `agent_tools.py` (9 herramientas), `agents.py` (orquestador), `jobs.py` (trabajos), `requirements.txt` (solo MySQL) |
| `sql/` | Esquemas, semilla idempotente, plantilla de usuarios, `05_agentic.sql` y `06_auth.sql` (migraciones sin borrar nada) |
| `scripts/` | `gen_env.py` (secretos, conserva lo existente), `check.py` (verificación) |
| `tests/` | `test_rules.py`, `test_agents.py`, `test_auth.py` (proveedor de prueba; cero llamadas reales) |
| `docs/` | `PRD.md`, `arquitectura.md`, `agentes.md`, `backlog.md` |

## 5. Agentes y proveedor de IA

El Centro de agentes (pestaña **Agentes**) ejecuta trabajos en segundo plano:
el modelo elige herramientas autorizadas; el índice lo calcula el motor;
puedes cancelar, pedir revisión y reintentar. Las propuestas del modelo
llevan 🤖 IA; las cifras verificadas llevan ✓.

- **Sin configurar:** funciona con el **proveedor de prueba** (respuestas
  programadas, etiquetadas; no es IA real).
- **IA real (OpenAI compatible):** verificado contra la referencia oficial
  `POST {base}/chat/completions` con `tools` y `response_format`
  (https://platform.openai.com/docs/api-reference/chat/create).
  1. Crea tu clave en el panel del proveedor (no la pegues en ningún chat).
  2. Escríbela solo en tu `.env` local: `NEXO_AI_PROVIDER=openai` y `NEXO_AI_API_KEY=tu_clave`.
  3. Opcional: `NEXO_AI_MODEL=gpt-4o-mini` (u otro modelo documentado de tu cuenta).
  4. Reinicia el servicio Python y abre el Centro de agentes: debe decir «IA habilitada».
- **Costos:** la API del proveedor normalmente es de pago por uso y puede
  generar cargos; revisa su página de precios antes de activar. El proveedor
  de prueba y la demo no cuestan nada. No se hizo ninguna llamada de pago
  en este proyecto.
- **Alternativa local:** apunta `NEXO_AI_BASE_URL` a un servidor compatible
  en tu máquina (p. ej. un modelo local con API tipo OpenAI) y usa su modelo.

Límites conservadores (variables `NEXO_AI_*` en `.env`):

| Variable | Defecto | Qué limita |
|----------|---------|------------|
| `NEXO_AI_MAX_STEPS` | 10 | Pasos del modelo por etapa |
| `NEXO_AI_MAX_TOOL_CALLS` | 20 | Llamadas a herramientas por trabajo |
| `NEXO_AI_MAX_RETRIES` | 2 | Reintentos ante respuestas inválidas |
| `NEXO_AI_TIMEOUT_S` | 60 | Espera máxima por llamada al modelo |
| `NEXO_AI_JOB_TIMEOUT_S` | 600 | Duración máxima del trabajo |
| `NEXO_AI_MAX_ROWS_TOOL` | 200 | Filas máximas que ve una herramienta |
| `NEXO_AI_REDACT` | 1 | Enmascara correos antes de enviarlos |

## 6. Detener y volver a iniciar

```powershell
Get-Process python,php -ErrorAction SilentlyContinue | Stop-Process
.\.venv\Scripts\python.exe backend\app.py --demo --port 8001  # terminal 1
php -S 127.0.0.1:8000 server/router.php                       # terminal 2
```
En modo memoria los trabajos se pierden al detener Python; en MySQL los
interrumpidos se marcan y ofrecen **reintento explícito** (trabajo nuevo,
sin duplicar eventos del original).

## 7. Usuarios y sesiones (local)

La **portada de bienvenida** es lo primero que se ve al entrar: presenta la
aplicación y ofrece entrar como invitado, iniciar sesión o registrarse.
El botón 👤 de la esquina superior derecha abre el menú de usuario
(ver **Mi perfil**, cerrar sesión o entrar). La pestaña **Perfil** muestra
tu nombre, correo y estado de sesión; no aparece en la barra principal.

- Registro: nombre (2–60 letras), correo válido y único, contraseña de
  8–72 caracteres con mayúscula, minúscula y número (verificada en el
  navegador y de nuevo en el servidor).
- Inicio de sesión: mensajes genéricos, bloqueo de ~15 min tras 5 fallos.
- Contraseñas con PBKDF2 + sal (nunca en texto claro); sesiones opacas de
  8 h guardadas en el servidor (PHP `$_SESSION`); el navegador solo recibe
  tu nombre y correo. Tus decisiones aceptadas quedan firmadas con tu nombre.
- Sin MySQL todo es temporal (memoria); con MySQL aplica `sql/06_auth.sql`.
- Alcance local de un operador: no es autenticación empresarial.

## 8. Reglas y muestra
- **Obligatoriedad:** nulo/ausente/espacios = incidencia; **0 no es vacío**.
- **Unicidad:** marca todas las filas del grupo duplicado; claves vacías excluidas.
- **Correo:** `usuario@dominio.extensión`; vacíos excluidos.
- Índice = `redondear((comprobaciones − incidencias) / comprobaciones × 100)`; sin comprobaciones = «Sin evaluar».
- `row_id` (técnica, única) ≠ `id` (negocio, con duplicado intencional `CLI-004`).
- Verificación: `python tests/test_rules.py`, `python tests/test_agents.py` y `python scripts/check.py`.

## 9. Seguridad local

Secretos en `.env` (fuera de `public`, en `.gitignore`); el navegador jamás recibe el token
ni la clave del proveedor; PHP valida origen en escrituras; MySQL con cuentas separadas,
consultas parametrizadas y transacciones; decisiones como eventos acumulativos;
límite de 10 000 filas por tabla; agentes sin comandos del sistema ni SQL arbitrario.
App local de un solo operador, sin autenticación empresarial.

## 10. Estado de verificación

Ejecutado aquí (2026-09-21): `tests/test_rules.py` (15/15 OK),
`tests/test_agents.py` (20/20 OK, todo con proveedor de prueba),
`tests/test_auth.py` (10/10 OK), `scripts/check.py` (OK), flujo agentic vivo PHP→Python con stub
(inicio, revisión, aprobación, cancelación, reintento, rechazos 409;
trabajo #1 completado con 123/8/93 y 6 recomendaciones).
**Cero llamadas a IA real: no hay clave configurada.**
Flujo de usuarios vivo: registro, duplicado (400), login erróneo (401),
bloqueo tras 5 fallos (423), sesión que sobrevive, decisión firmada con el
nombre, invitado sin firma y logout (401 posterior).
MySQL 8.0 local verificado (2026-09-21): usuarios limitados, semilla 12/8/6,
análisis real 123/8/93, decisión que sobrevive al reinicio del servicio.
Ojo: el servicio Python debe iniciarse con `.\.venv\Scripts\python.exe`
(donde está `mysql-connector-python`), y se corrigió la fecha del detalle.
Pendiente (requiere tu clave y autorización): una llamada real al proveedor
desde el Centro de agentes.
