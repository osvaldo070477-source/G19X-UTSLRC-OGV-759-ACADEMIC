"""Motor de reglas deterministas de NEXO.

Reglas (idénticas en Python y JavaScript — ver public/app.js):
  1. Obligatoriedad (required): nulo, ausente o solo espacios => incidencia.
     El número 0 NO cuenta como vacío. Booleanos nunca vacíos.
  2. Unicidad (unique): claves de negocio duplicadas. Se marca TODA fila
     del grupo duplicado (1 incidencia por fila). Claves vacías excluidas
     (no generan comprobación de unicidad).
  3. Formato de correo (email): regex ^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$.
     Correos vacíos excluidos (no duplican la incidencia de obligatoriedad).

Terminología:
  comprobación  = evaluación individual
  incidencia    = comprobación fallida
  hallazgo      = agrupación por (tabla, columna, regla)
  fila afectada = registro con >= 1 incidencia

Índice: redondear((comprobaciones - incidencias) / comprobaciones * 100).
  Sin comprobaciones => None ("Sin evaluar").
  Redondeo: round() mitad arriba (Python round es bancario; aquí se usa
  Decimal ROUND_HALF_UP para coincidir con Math.round de JavaScript).
"""

import re
from collections import Counter
from decimal import Decimal, ROUND_HALF_UP

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Configuración de comprobaciones por tabla y columna.
# required: genera 1 comprobación por fila. / unique: 1 por fila no vacía.
# email: 1 por fila con correo no vacío.
RULE_CONFIG = {
    "clientes": {
        "id": {"required": True, "unique": True},
        "nombre": {"required": True},
        "email": {"required": True, "email": True},
    },
    "pedidos": {
        "id": {"required": True, "unique": True},
        "cliente_id": {"required": True},
        "fecha": {"required": True},
        "total": {"required": True},
    },
    "productos": {
        "id": {"required": True, "unique": True},
        "nombre": {"required": True},
        "precio": {"required": True},
    },
}

PRIORITY = {"required": "Alta", "unique": "Alta", "email": "Media"}
RULE_LABEL = {
    "required": "Obligatoriedad",
    "unique": "Unicidad",
    "email": "Formato de correo",
}

RECOMMENDATIONS = {
    ("clientes", "id", "unique"): "Unificar las filas con el mismo id de cliente bajo un único registro maestro y redirigir los pedidos afectados antes del próximo análisis.",
    ("clientes", "nombre", "required"): "Completar el nombre faltante desde el formulario de alta y marcar el campo como obligatorio en la captura.",
    ("clientes", "email", "required"): "Solicitar el correo faltante al responsable comercial y reintentar el envío de comunicaciones.",
    ("clientes", "email", "email"): "Corregir los correos con formato inválido validándolos contra el patrón usuario@dominio.extensión.",
    ("pedidos", "cliente_id", "required"): "Asignar el cliente correspondiente a cada pedido sin referencia; bloquear el cierre de pedidos sin cliente.",
    ("productos", "nombre", "required"): "Completar el nombre del producto desde el catálogo maestro antes de publicarlo.",
}


def is_empty(value):
    """True si nulo, ausente o cadena solo con espacios. 0 no es vacío."""
    if value is None:
        return True
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        return False
    return str(value).strip() == ""


def quality_index(checks, issues):
    if checks == 0:
        return None
    pct = (Decimal(checks - issues) / Decimal(checks)) * Decimal(100)
    return int(pct.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def recommendation_for(table, column, rule):
    return RECOMMENDATIONS.get(
        (table, column, rule),
        "Revisar los valores señalados con el responsable del dato y registrar la decisión en NEXO.",
    )


def analyze_tables(tables):
    """tablas: dict nombre -> lista de dicts (cada fila con 'row_id').
    Devuelve dict con totals, findings y rows afectadas."""
    total_checks = 0
    total_issues = 0
    groups = {}  # (tabla, columna, regla) -> {count, evidence[]}
    affected = set()

    def add_issue(table, column, rule, row, value):
        nonlocal total_issues
        total_issues += 1
        key = (table, column, rule)
        g = groups.setdefault(key, {"count": 0, "evidence": []})
        g["count"] += 1
        g["evidence"].append(
            {"row_id": row.get("row_id"), "valor": value, "ref": f"{table}:{row.get('row_id')}"}
        )
        affected.add(f"{table}:{row.get('row_id')}")

    for table, rows in tables.items():
        cfg = RULE_CONFIG.get(table, {})
        # 1) Obligatoriedad + formato (por fila)
        for row in rows:
            for column, rules in cfg.items():
                value = row.get(column)
                if rules.get("required"):
                    total_checks += 1
                    if is_empty(value):
                        add_issue(table, column, "required", row, value)
                if rules.get("email"):
                    if not is_empty(value):
                        total_checks += 1
                        if not EMAIL_RE.match(str(value).strip()):
                            add_issue(table, column, "email", row, value)
        # 2) Unicidad (por columna, excluye vacías)
        for column, rules in cfg.items():
            if not rules.get("unique"):
                continue
            keys = []
            for row in rows:
                value = row.get(column)
                if is_empty(value):
                    continue
                total_checks += 1
                keys.append(str(value).strip())
            dupes = {k for k, c in Counter(keys).items() if c > 1}
            for row in rows:
                value = row.get(column)
                if is_empty(value):
                    continue
                if str(value).strip() in dupes:
                    add_issue(table, column, "unique", row, value)

    findings = []
    for (table, column, rule), g in sorted(groups.items()):
        findings.append(
            {
                "tabla": table,
                "columna": column,
                "regla": rule,
                "regla_etiqueta": RULE_LABEL[rule],
                "prioridad": PRIORITY[rule],
                "incidencias": g["count"],
                "recomendacion": recommendation_for(table, column, rule),
                "evidencias": sorted(g["evidence"], key=lambda e: str(e["row_id"])),
            }
        )

    return {
        "comprobaciones": total_checks,
        "incidencias": total_issues,
        "indice": quality_index(total_checks, total_issues),
        "hallazgos": findings,
        "filas_afectadas": len(affected),
        "total_registros": sum(len(r) for r in tables.values()),
    }
