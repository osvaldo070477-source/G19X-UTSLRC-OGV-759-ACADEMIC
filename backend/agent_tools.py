"""Herramientas autorizadas para los agentes (NEXO agentic).

Principios:
- Solo existen estas herramientas; el modelo no puede inventar otras.
- Sin comandos del sistema ni SQL arbitrario: los argumentos se validan
  contra listas permitidas (tablas/columnas) y todo acceso usa consultas
  parametrizadas o la muestra en memoria.
- El contenido de tablas y metadatos es DATO no confiable: se devuelve
  como texto y jamás se interpreta como instrucción.
- Al proveedor solo llegan agregados y evidencias mínimas con valores
  sensibles ocultos (correos enmascarados, textos truncados).
"""

import re

from rules import analyze_tables, is_empty

ALLOWED_TABLES = ("clientes", "pedidos", "productos")
ALLOWED_COLUMNS = {
    "clientes": ("id", "nombre", "email"),
    "pedidos": ("id", "cliente_id", "fecha", "total"),
    "productos": ("id", "nombre", "precio"),
}
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def redact_value(value, redact=True):
    """Enmascara valores sensibles para enviar al proveedor."""
    if value is None:
        return None
    s = str(value)
    if not redact:
        return s
    if "@" in s and EMAIL_RE.match(s.strip()):
        user, _, domain = s.strip().partition("@")
        return (user[:1] + "***@" + domain) if user else "***@" + domain
    return s if len(s) <= 60 else s[:57] + "..."


TOOL_DEFS = [
    {"name": "listar_tablas", "description": "Lista las tablas autorizadas.",
     "parameters": {"type": "object", "properties": {}, "additionalProperties": False}},
    {"name": "describir_tabla", "description": "Estructura, responsable y reglas de una tabla.",
     "parameters": {"type": "object", "properties": {"tabla": {"type": "string"}},
                    "required": ["tabla"], "additionalProperties": False}},
    {"name": "contar_registros", "description": "Número de filas de una tabla.",
     "parameters": {"type": "object", "properties": {"tabla": {"type": "string"}},
                    "required": ["tabla"], "additionalProperties": False}},
    {"name": "perfil_columna", "description": "Agregados de una columna: vacíos, distintos y ejemplos enmascarados.",
     "parameters": {"type": "object", "properties": {"tabla": {"type": "string"}, "columna": {"type": "string"}},
                    "required": ["tabla", "columna"], "additionalProperties": False}},
    {"name": "comprobar_obligatoriedad", "description": "Cuenta valores nulos/ausentes/solo-espacios (0 válido).",
     "parameters": {"type": "object", "properties": {"tabla": {"type": "string"}, "columna": {"type": "string"}},
                    "required": ["tabla", "columna"], "additionalProperties": False}},
    {"name": "comprobar_unicidad", "description": "Cuenta filas con clave de negocio duplicada (vacías excluidas).",
     "parameters": {"type": "object", "properties": {"tabla": {"type": "string"}, "columna": {"type": "string"}},
                    "required": ["tabla", "columna"], "additionalProperties": False}},
    {"name": "comprobar_correo", "description": "Cuenta correos con formato inválido (vacíos excluidos).",
     "parameters": {"type": "object", "properties": {"tabla": {"type": "string"}, "columna": {"type": "string"}},
                    "required": ["tabla", "columna"], "additionalProperties": False}},
    {"name": "obtener_evidencia", "description": "Filas de ejemplo (enmascaradas) de un hallazgo tabla+columna+regla.",
     "parameters": {"type": "object",
                    "properties": {"tabla": {"type": "string"}, "columna": {"type": "string"},
                                   "regla": {"type": "string", "enum": ["required", "unique", "email"]},
                                   "maximo": {"type": "integer", "minimum": 1, "maximum": 20}},
                    "required": ["tabla", "columna", "regla"], "additionalProperties": False}},
    {"name": "consultar_ultimo_analisis", "description": "Resumen del análisis determinista más reciente, si existe.",
     "parameters": {"type": "object", "properties": {}, "additionalProperties": False}},
]


def openai_tools():
    """Definiciones en formato function-calling de la API Chat Completions."""
    return [{"type": "function", "function": {"name": t["name"], "description": t["description"],
                                              "parameters": t["parameters"]}} for t in TOOL_DEFS]


def validate_call(name, args):
    """Valida nombre y argumentos. Devuelve (limpios, None) o (None, error)."""
    names = {t["name"] for t in TOOL_DEFS}
    if name not in names:
        return None, f"Herramienta no autorizada: {name}."
    if not isinstance(args, dict):
        return None, "Los argumentos deben ser un objeto."
    args = {k: v for k, v in args.items() if k in ("tabla", "columna", "regla", "maximo")}
    if "tabla" in args and args["tabla"] not in ALLOWED_TABLES:
        return None, f"Tabla no autorizada: {args['tabla']}."
    if "columna" in args:
        cols = ALLOWED_COLUMNS.get(args.get("tabla", ""), ())
        if args["columna"] not in cols:
            return None, f"Columna no autorizada: {args.get('tabla')}.{args['columna']}."
    if "regla" in args and args["regla"] not in ("required", "unique", "email"):
        return None, f"Regla desconocida: {args['regla']}."
    if "maximo" in args and not (1 <= int(args["maximo"]) <= 20):
        return None, "maximo debe estar entre 1 y 20."
    return args, None


def execute_tool(name, args, ctx):
    """Ejecuta una herramienta validada. ctx: {tables, metadata, last_run, redact, max_rows}. """
    tables, meta = ctx["tables"], ctx["metadata"]
    redact = ctx.get("redact", True)
    if name == "listar_tablas":
        return {"tablas": list(ALLOWED_TABLES)}
    if name == "describir_tabla":
        t = args["tabla"]
        m = meta[t]
        return {"tabla": t, "descripcion": m["descripcion"], "responsable": m["responsable"],
                "dominio": m["dominio"], "columnas": m["columnas"], "reglas": m["reglas"]}
    if name == "contar_registros":
        return {"tabla": args["tabla"], "registros": len(tables[args["tabla"]])}
    if name == "perfil_columna":
        rows = tables[args["tabla"]]
        col = args["columna"]
        vacios = sum(1 for r in rows if is_empty(r.get(col)))
        distintos = sorted({str(r.get(col)).strip() for r in rows if not is_empty(r.get(col))})[:50]
        ejemplos = [redact_value(r.get(col), redact) for r in rows[:5]]
        return {"tabla": args["tabla"], "columna": col, "filas": len(rows),
                "vacios": vacios, "distintos_muestra": len(distintos), "ejemplos": ejemplos}
    if name in ("comprobar_obligatoriedad", "comprobar_unicidad", "comprobar_correo"):
        rows = tables[args["tabla"]]
        col = args["columna"]
        if name == "comprobar_obligatoriedad":
            malas = [r for r in rows if is_empty(r.get(col))]
            return {"tabla": args["tabla"], "columna": col, "regla": "required",
                    "comprobaciones": len(rows), "incidencias": len(malas)}
        if name == "comprobar_correo":
            base = [r for r in rows if not is_empty(r.get(col))]
            malas = [r for r in base if not EMAIL_RE.match(str(r.get(col)).strip())]
            return {"tabla": args["tabla"], "columna": col, "regla": "email",
                    "comprobaciones": len(base), "incidencias": len(malas)}
        vistos, dupes = {}, set()
        for r in rows:
            v = r.get(col)
            if is_empty(v):
                continue
            k = str(v).strip()
            if k in vistos:
                dupes.add(k)
            vistos[k] = True
        base = [r for r in rows if not is_empty(r.get(col))]
        malas = [r for r in base if str(r.get(col)).strip() in dupes]
        return {"tabla": args["tabla"], "columna": col, "regla": "unique",
                "comprobaciones": len(base), "incidencias": len(malas)}
    if name == "obtener_evidencia":
        full = analyze_tables(tables)
        for h in full["hallazgos"]:
            if h["tabla"] == args["tabla"] and h["columna"] == args["columna"] and h["regla"] == args["regla"]:
                ev = [{"ref": e["ref"], "row_id": e["row_id"],
                       "valor": redact_value(e["valor"], redact)}
                      for e in h["evidencias"][: int(args.get("maximo", 5))]]
                return {"hallazgo": f"{h['tabla']}.{h['columna']}.{h['regla']}",
                        "incidencias": h["incidencias"], "evidencias": ev}
        return {"hallazgo": None, "incidencias": 0, "evidencias": []}
    if name == "consultar_ultimo_analisis":
        last = ctx.get("last_run")
        if not last:
            return {"existe": False}
        return {"existe": True, "comprobaciones": last["comprobaciones"],
                "incidencias": last["incidencias"], "indice": last["indice"],
                "hallazgos": len(last["hallazgos"])}
    return {"error": "no implementada"}
