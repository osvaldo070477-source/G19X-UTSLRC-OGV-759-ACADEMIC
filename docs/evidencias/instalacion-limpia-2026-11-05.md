# Instalación limpia — 2026-11-05

Prueba de reproducibilidad sobre un **clon real** del repositorio, en una
carpeta nueva y con una instancia MySQL temporal. No se usó ni se modificó el
MySQL80 del equipo (puerto 3306).

## Entorno

- Windows, Python 3.13.15, PHP 8.4.25, MySQL 8.0.46.
- Origen: `https://github.com/osvaldo070477-source/G19X-UTSLRC-OGV-759-ACADEMIC.git`.
- `git clone` en `C:\nexo-clone-2026-11-05`, sin `.env`, `.venv` ni historial
  local previo.
- Commit probado: **`c33f8c7`** (`docs: actualiza autoria, cabeceras y revision
  del asesor`). El clon quedó limpio (`git status --short` sin cambios).
- Instancia temporal: `127.0.0.1:3308`, `datadir` nuevo y vacío.
- La única adaptación de entorno fue `NEXO_MYSQL_PORT=3308` en el `.env` de la
  prueba; las cuentas y contraseñas se tomaron del `.env` generado.

## Procedimiento

1. `git clone` del repositorio y `cd` a la carpeta nueva.
2. Modo B: `python -m venv .venv`, `python scripts/gen_env.py`, servicio Python
   con `--demo --port 8001` y `php -S 127.0.0.1:8000 server/router.php`.
3. Modo C: `.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt`
   (instala `mysql-connector-python==9.1.0`).
4. Base vacía en 3308 y scripts del README §3 en orden:
   `01`, `02`, `03`, `04` (plantilla descomentada con las contraseñas del
   `.env`), `05`, `06`, `08`, `09`, `10` y `07` al final.
5. Servicios sin `--demo` en `127.0.0.1:8001` (Python) y `127.0.0.1:8000`
   (PHP).
6. Registro de `clonc@nexo.test`, ascenso a `admin` con
   `scripts/crea_admin.py`, recorrido de `docs/MVP.md` §3 y, al final,
   importación CSV en Catálogo.
7. Suites del README §8 dentro del clon.

## Resultados

### Modo B

```text
health 200 demo 1.0.1
register 201
analyze 200 indice 90 · 208 comprobaciones · 21 incidencias · 8 hallazgos · 44 registros
```

### Modo C

```text
health 200 mysql mysql_ok true 1.0.1
login 200 admin
analyze_antes 200 90 · 208 · 21 · 8 · 44
source_preview 200 1 válida · 0 rechazadas
source_import 201 {'ok': True, 'insertadas': 1, 'rechazadas': []}
analyze_despues 200 90 · 213 · 21 · 8 · 45
```

La carga quedó auditada y la fuente pasó de 20 a 21 clientes:

```text
id  user_id  tabla     row_id  accion
1   1        clientes  cli-21  insert
```

### Cuentas y permisos

`nexo_ro@127.0.0.1` y `nexo_app@127.0.0.1` autenticaron correctamente. Para
`nexo_wr@127.0.0.1`:

```text
GRANT USAGE ON *.* TO `nexo_wr`@`127.0.0.1`
GRANT INSERT ON `nexo_source`.* TO `nexo_wr`@`127.0.0.1`
GRANT INSERT ON `nexo_app`.`source_audit` TO `nexo_wr`@`127.0.0.1`
```

La cuenta de escritura **no puede leer** la fuente:

```text
ERROR 1142 (42000): SELECT command denied to user 'nexo_wr'@'localhost' for table 'clientes'
```

### Recorrido de `docs/MVP.md` §3

Se ejecutó sobre la semilla intacta (208/21/8/90) y antes de la importación CSV.
Los tiempos son de la corrida automatizada, de la acción al pintado de la
pantalla; la narración humana conserva el objetivo de **10–12 minutos**.

| # | Paso | Qué pasó | Tiempo |
|---|------|----------|--------|
| 1 | Entrar | Sesión con `clonc@nexo.test`; la barra lateral mostró **«Clon · admin»** | 277 ms |
| 2 | Observatorio | **208 comprobaciones, 21 incidencias, 8 hallazgos, índice 90 %**, 44 registros | 151 ms |
| 3 | Catálogo | 3 activos, cada uno con dominio, responsable y reglas aplicables | 18 ms |
| 4 | Calidad | Evidencia de `clientes.id` (Unicidad): `clientes:cli-04`, valor `CLI-004` | 35 ms |
| 5 | Decisiones | Recomendación de formato de correo aceptada con comentario; el reanálisis siguió en **208/21/8/90** y la fuente no cambió | 159 ms + 117 ms |
| 6 | Bitácora | Ejecución #2 consultada y exportada a `nexo_ejecucion_2.json` (5 762 bytes, 8 hallazgos) | 76 ms |
| 7 | Agentes | La base nueva no trae el trabajo #13; se creó el trabajo #1 con el proveedor de prueba: etapas, 4 herramientas, 2 revisiones aprobadas y 8 recomendaciones | ~3.8 s |
| 8 | Administración y perfil | Tabla de cuentas con rol `admin`, desbloqueo auditado y perfil propio con rol `admin` | 522 ms |

Tiempo total de la corrida automatizada: **~5.2 s**. El trabajo #13 con 9
herramientas y ~82 s corresponde a la corrida real con IA documentada en el
README §10; no se reproduce con el proveedor de prueba ni con una base nueva.

### Suites del README §8

```text
tests/test_rules.py        RESULTADO: TODO OK
tests/test_agents.py       21/21 OK
tests/test_auth.py         24/24 OK
tests/test_carga.py        9/9 OK
tests/test_equivalencia.py OMITIDO (Node no instalado)
scripts/check.py           RESULTADO: TODO OK
scripts/check_ui.py        RESULTADO: TODO OK
```

### Integración continua

El humo de GitHub Actions fallaba porque el contenedor de MySQL recibe la
conexión desde la red de Docker, no como `127.0.0.1`: `nexo_wr` solo existía
para `'127.0.0.1'` y `'localhost'`, y el permiso de `source_audit` de
`sql/07_permisos.sql` tampoco aplicaba a `'%'`. Se corrigió en
`.github/workflows/ci.yml` (commit `3a747eb`) creando `nexo_wr@'%'` y
concediéndole `INSERT` en la fuente y en la auditoría. La reproducción local con
una cuenta `nexo_wr@'%'` únicamente devolvió `source_add` **201**.

Run verde: [42116125752](https://github.com/osvaldo070477-source/G19X-UTSLRC-OGV-759-ACADEMIC/actions/runs/42116125752)
sobre `3a747eb`; los trabajos **`test`** y **`smoke`** terminaron en `success`.

## Fallos encontrados y correcciones

1. **Rol ausente en la barra lateral (paso 1).** El guion pide mostrar nombre y
   rol; la interfaz solo añadía «(lectura)» para el rol `lector`. Corregido en
   `public/js/auth.js` (commit `7fcd1a1`): ahora muestra `Nombre · admin`,
   `Nombre · operador` o `Nombre (lectura)`. Verificado en el clon.
2. **Modo C sin el conector de MySQL.** En la primera copia limpia se omitió el
   paso 3.2 del README; el servicio arrancó sin `mysql-connector-python` y
   `mysql_ok` quedó en `false`. En el clon se siguió el README y el conector se
   instaló antes de arrancar. No hizo falta cambiar el README.
3. **El trabajo #13 no existe en una base nueva.** El recorrido se ajustó en
   `docs/MVP.md` §3: en una base nueva se inicia un trabajo con el proveedor de
   prueba y se aprueban sus dos revisiones; el #13 queda como evidencia de la
   corrida real.
4. **208 vs 213 comprobaciones.** La importación CSV sube el total a 213. El
   recorrido se hizo antes de la carga y `docs/MVP.md` §3 ahora lo advierte.
5. **Plantilla `04` comentada.** El README explica que hay que descomentarla y
   sustituir las tres contraseñas; al hacerlo, las tres cuentas se crearon sin
   error.

## Conclusión

El repositorio se instala desde un clon limpio siguiendo el README: modo B y
modo C arrancan, las tres cuentas de MySQL funcionan, la carga CSV responde
**201** y deja auditoría, `nexo_wr` solo puede insertar, y los ocho pasos del
recorrido se completan. Las correcciones pendientes son de documentación y de
la etiqueta del rol; no cambian reglas, datos ni cifras.

## Limpieza

Los servicios de prueba y la instancia temporal de 3308 se detuvieron al
terminar. El MySQL80 del equipo (3306) no se tocó.
