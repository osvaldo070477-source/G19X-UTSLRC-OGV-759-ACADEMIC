"""Pruebas del motor de reglas (biblioteca estándar, sin pytest).
Uso:  python tests/test_rules.py
"""
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "backend"))
from rules import analyze_tables, is_empty, quality_index  # noqa: E402
from sample import get_sample_tables  # noqa: E402

fails = []


def check(name, cond):
    print(("OK  " if cond else "FALLO ") + name)
    if not cond:
        fails.append(name)


t = get_sample_tables()
check("muestra: 20 clientes", len(t["clientes"]) == 20)
check("muestra: 14 pedidos", len(t["pedidos"]) == 14)
check("muestra: 10 productos", len(t["productos"]) == 10)

r = analyze_tables(t)
check("44 registros", r["total_registros"] == 44)
check("208 comprobaciones", r["comprobaciones"] == 208)
check("21 incidencias", r["incidencias"] == 21)
check("8 hallazgos", len(r["hallazgos"]) == 8)
check("índice 90", r["indice"] == 90)

# Reglas individuales
check("cero no es vacío", is_empty(0) is False and is_empty(0.0) is False)
check("espacios sí son vacío", is_empty("   ") is True)
check("nulo es vacío", is_empty(None) is True)
check("sin comprobaciones = sin evaluar", quality_index(0, 0) is None)

dup = analyze_tables({"clientes": [
    {"row_id": "a", "id": "X-1", "nombre": "A", "email": "a@example.com"},
    {"row_id": "b", "id": "X-1", "nombre": "B", "email": "b@example.com"},
], "pedidos": [], "productos": []})
check("duplicado marca ambas filas", dup["incidencias"] == 2)

fmt = analyze_tables({"clientes": [
    {"row_id": "a", "id": "X-1", "nombre": "A", "email": ""},
], "pedidos": [], "productos": []})
check("correo vacío no duplica incidencia", fmt["incidencias"] == 1 and fmt["comprobaciones"] == 4)

print("RESULTADO:", "TODO OK" if not fails else f"{len(fails)} FALLOS")
sys.exit(0 if not fails else 1)
