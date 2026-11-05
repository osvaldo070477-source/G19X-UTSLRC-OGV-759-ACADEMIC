# Instalación limpia — 2026-11-02

Prueba real de instalación desde cero sobre una instancia MySQL temporal.
No se usó ni se modificó el MySQL80 del equipo (puerto 3306).

## Entorno

- Windows, Python 3.13.15, PHP 8.4.25, MySQL 8.0.46.
- Instancia temporal: `127.0.0.1:3307`, `datadir` nuevo y vacío.
- Código: repositorio en `32faa12` más los cambios locales de
  `sql/04_users_template.sql`, `sql/07_permisos.sql`, `sql/09_carga.sql`,
  `README.md` y `.github/workflows/ci.yml` (sin commit al momento de la prueba).
- Datos: semilla sintética de `sql/03_seed_source.sql` (20 clientes, 14 pedidos,
  10 productos).

## Procedimiento

1. Se inicializó un `datadir` temporal con `mysqld --initialize-insecure` y se
   arrancó en el puerto 3307 con `--no-defaults --mysqlx=0`.
2. Se ejecutaron, en orden, los scripts del README:
   `01`, `02`, `03`, `04` (descomentado), `05`, `06`, `08`, `09`, `10` y `07`.
3. Para `04` se usó una copia temporal con los marcadores sustituidos por
   contraseñas de prueba; el archivo del repositorio no se modificó.
4. Se comprobó el acceso de las tres cuentas y se arrancó la aplicación en
   `127.0.0.1:8002` (Python) y `127.0.0.1:8003` (PHP), con IA en modo `stub`.

## Resultados

### Scripts SQL

Todos los scripts terminaron con código 0. `07` confirmó:

```text
Permisos mínimos aplicados a nexo_app y nexo_wr.
```

### Cuentas

Las tres cuentas existen para `127.0.0.1` y `localhost`, y las tres pueden
autenticarse:

```text
nexo_ro@127.0.0.1
nexo_app@127.0.0.1
nexo_wr@127.0.0.1
```

### Semilla

```text
clientes  pedidos  productos
20        14       10
```

### Aplicación

```text
health 200 ok mysql True 1.0.1
register 201 {'id': 1, 'nombre': 'Operador Limpio', 'email': 'limpio2@nexo.test', 'rol': 'operador'}
analyze_pristina 200 90 208 21 8
source_add 201 {'ok': True, 'insertadas': 1}
source_preview 200 1 0
source_import 201 {'ok': True, 'insertadas': 1, 'rechazadas': []}
analyze_con_carga 200 90 217 21
```

La primera lectura es la de la semilla intacta: **208 comprobaciones, 21
incidencias, 8 hallazgos e índice 90**. Después de agregar una fila a productos
y otra a clientes, el motor reporta 217 comprobaciones y mantiene el índice 90.

### Carga y auditoría

```text
tabla      row_id  accion
productos  pro-11  insert
clientes   cli-21  insert
```

Las filas quedaron en la fuente:

```text
row_id  id          nombre           precio
pro-11  P-LIMPIO-1  Producto limpio  12.50

row_id  id          nombre          email
cli-21  C-LIMPIO-1  Cliente limpio  cliente@nexo.test
```

### Permisos de `nexo_wr`

```text
GRANT USAGE ON *.* TO `nexo_wr`@`127.0.0.1`
GRANT INSERT ON `nexo_source`.* TO `nexo_wr`@`127.0.0.1`
GRANT INSERT ON `nexo_app`.`source_audit` TO `nexo_wr`@`127.0.0.1`
```

Se comprobó además que `nexo_wr` **no puede leer** la fuente:

```text
ERROR 1142 (42000): SELECT command denied to user 'nexo_wr'@'localhost' for table 'productos'
```

## Conclusión

La secuencia `01 → 02 → 03 → 04 → 05 → 06 → 08 → 09 → 10 → 07` funciona en una
base vacía. `nexo_wr` se crea en `04`, recibe solo `INSERT` en la fuente y en
`source_audit`, y la carga gobernada responde **201** tanto en `source_add` como
en `source_import`. No se detectó el error 1146 en esta prueba.

## Limpieza

La instancia temporal y los procesos de prueba se detuvieron al terminar. El
MySQL80 del equipo no se tocó.
