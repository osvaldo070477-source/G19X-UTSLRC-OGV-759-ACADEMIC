"""Carga gobernada de datos a nexo_source (NEXO punto 1).

- Solo tablas/columnas permitidas; todo lo demás se rechaza.
- Validación con las mismas reglas del motor (requeridos, email, duplicados).
- Escritura con cuenta exclusiva de inserción (nexo_wr); la app nunca usa root.
- Auditoría de cada fila en nexo_app.source_audit (quién, qué, cuándo).
- Límite de filas por tabla y por lote; sin truncados silenciosos.
"""
import csv
import io
import re

MAX_IMPORT_BATCH = 500
MAX_ROWS_PER_TABLE = 10000
FECHA_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

SCHEMAS = {
    "clientes": {
        "columnas": ["id", "nombre", "email"],
        "requeridas": ["id", "nombre", "email"],
        "tipos": {"id": "texto", "nombre": "texto", "email": "correo"},
        "prefijo": "cli",
    },
    "pedidos": {
        "columnas": ["id", "cliente_id", "fecha", "total"],
        "requeridas": ["id", "cliente_id", "fecha", "total"],
        "tipos": {"id": "texto", "cliente_id": "texto", "fecha": "fecha", "total": "numero"},
        "prefijo": "ped",
    },
    "productos": {
        "columnas": ["id", "nombre", "precio"],
        "requeridas": ["id", "nombre", "precio"],
        "tipos": {"id": "texto", "nombre": "texto", "precio": "numero"},
        "prefijo": "pro",
    },
}


def _vacio(v):
    if v is None:
        return True
    if isinstance(v, bool):
        return False
    if isinstance(v, (int, float)):
        return False
    return str(v).strip() == ""


def validate_row(tabla, fila, ids_existentes):
    """Devuelve (limpia, None) o (None, error). No toca la base."""
    sch = SCHEMAS.get(tabla)
    if sch is None:
        return None, "Tabla no permitida."
    if not isinstance(fila, dict):
        return None, "La fila debe ser un objeto."
    extra = [k for k in fila if k not in sch["columnas"]]
    if extra:
        return None, "Columnas no permitidas: " + ", ".join(sorted(extra)) + "."
    limpia = {}
    for col in sch["columnas"]:
        v = fila.get(col)
        v = "" if v is None else (v if isinstance(v, (int, float)) else str(v).strip())
        if col in sch["requeridas"] and _vacio(v):
            return None, f"Falta el campo obligatorio: {col}."
        tipo = sch["tipos"][col]
        if tipo == "correo" and not _vacio(v) and not EMAIL_RE.match(str(v)):
            return None, f"Correo inválido en {col}."
        if tipo == "numero" and not _vacio(v):
            try:
                v = float(v)
            except (TypeError, ValueError):
                return None, f"{col} debe ser un número."
        if tipo == "fecha" and not _vacio(v) and not FECHA_RE.match(str(v)):
            return None, f"{col} debe tener formato AAAA-MM-DD."
        limpia[col] = v
    clave = str(limpia.get("id", "")).strip()
    if clave in ids_existentes:
        return None, f"El id '{clave}' ya existe en {tabla}."
    ids_existentes.add(clave)
    return limpia, None


def parse_csv(texto):
    """Parsea CSV a lista de dicts. Devuelve (filas, error)."""
    try:
        lector = csv.DictReader(io.StringIO((texto or "").strip()))
    except Exception as e:  # noqa: BLE001 - formato ilegible
        return None, f"No se pudo leer el CSV: {e}."
    if not lector.fieldnames:
        return None, "El CSV no tiene encabezados."
    cols = [c.strip() for c in lector.fieldnames if c and c.strip()]
    if not cols:
        return None, "El CSV no tiene columnas."
    filas = []
    for i, reg in enumerate(lector, start=2):
        if reg is None:
            continue
        fila = {(k.strip() if k else ""): (v.strip() if isinstance(v, str) else v)
                for k, v in reg.items() if k}
        if all(_vacio(v) for v in fila.values()):
            continue
        if len(filas) >= MAX_IMPORT_BATCH:
            return None, f"El lote supera el máximo de {MAX_IMPORT_BATCH} filas."
        filas.append((i, fila))
    if not filas:
        return None, "El CSV no trae filas con datos."
    return filas, None


def preview_rows(tabla, filas, ids_existentes):
    """Valida un lote sin escribir. Devuelve {validas, rechazadas:[{linea, error}]}."""
    validas, rechazadas, vistos = [], [], set(ids_existentes)
    for linea, fila in filas:
        limpia, err = validate_row(tabla, fila, vistos)
        if err:
            rechazadas.append({"linea": linea, "error": err})
        else:
            validas.append(limpia)
    return {"validas": validas, "rechazadas": rechazadas}


def _connector():
    try:
        import mysql.connector  # type: ignore
    except ImportError as e:
        raise RuntimeError("mysql-connector-python no está instalado.") from e
    return mysql.connector


def connect(cfg):
    mod = _connector()
    return mod.connect(host=cfg["host"], port=cfg["port"], user=cfg["user"],
                       password=cfg["password"], database=cfg["database"])


def existing_ids(source_cfg, tabla):
    conn = connect(source_cfg)
    try:
        cur = conn.cursor()
        cur.execute(f"SELECT id FROM `{tabla}`")
        return {str(r[0]).strip() for r in cur.fetchall()}
    finally:
        conn.close()


def table_count(source_cfg, tabla):
    conn = connect(source_cfg)
    try:
        cur = conn.cursor()
        cur.execute(f"SELECT COUNT(*) FROM `{tabla}`")
        return cur.fetchone()[0]
    finally:
        conn.close()


def insert_validas(wr_cfg, source_cfg, tabla, validas, user_id):
    """Inserta y audita en UNA transacción con la cuenta exclusiva.
    Requiere: INSERT en nexo_source.<tabla> e INSERT en nexo_app.source_audit."""
    if table_count(source_cfg, tabla) + len(validas) > MAX_ROWS_PER_TABLE:
        raise ValueError(f"Se superaría el límite de {MAX_ROWS_PER_TABLE} filas en {tabla}.")
    sch = SCHEMAS[tabla]
    cols = sch["columnas"]
    hechas = []
    rc = connect(dict(source_cfg, database="nexo_source"))
    try:
        cur = rc.cursor()
        cur.execute(f"SELECT row_id FROM `{tabla}`")
        usados = {r[0] for r in cur.fetchall()}
    finally:
        rc.close()
    conn = connect(dict(wr_cfg, database="nexo_source"))
    try:
        cur = conn.cursor()
        k = len(usados) + 1
        for fila in validas:
            while True:
                rid = f"{sch['prefijo']}-{k:02d}"
                k += 1
                if rid not in usados:
                    usados.add(rid)
                    break
            cur.execute(f"INSERT INTO `{tabla}` (row_id, {', '.join(cols)}) "
                        f"VALUES ({', '.join(['%s'] * (len(cols) + 1))})",
                        [rid] + [fila[c] for c in cols])
            hechas.append(rid)
        for rid in hechas:
            cur.execute("INSERT INTO nexo_app.source_audit (user_id, tabla, row_id, accion) "
                        "VALUES (%s,%s,%s,'insert')", (user_id, tabla, rid))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    return {"insertadas": len(hechas)}


def fetch_meta(app_cfg):
    conn = connect(app_cfg)
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT tabla, nombre, descripcion, responsable, dominio FROM asset_meta")
        return {r["tabla"]: r for r in cur.fetchall()}
    finally:
        conn.close()


def save_meta(app_cfg, tabla, descripcion, responsable):
    if tabla not in SCHEMAS:
        raise ValueError("Tabla no permitida.")
    descripcion = str(descripcion or "").strip()
    responsable = str(responsable or "").strip()
    if not (1 <= len(descripcion) <= 500) or not (1 <= len(responsable) <= 120):
        raise ValueError("Descripción (1-500) y responsable (1-120) obligatorios.")
    conn = connect(app_cfg)
    try:
        cur = conn.cursor()
        cur.execute("UPDATE asset_meta SET descripcion=%s, responsable=%s WHERE tabla=%s",
                    (descripcion, responsable, tabla))
        if cur.rowcount != 1:
            raise ValueError("Activo no encontrado.")
        conn.commit()
    finally:
        conn.close()
