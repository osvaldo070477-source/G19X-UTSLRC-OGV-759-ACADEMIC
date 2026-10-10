"""Muestra sintética de NEXO (datos ficticios, sin información real).

Totales verificados por tests/test_rules.py y scripts/check.py:
  20 clientes + 14 pedidos + 10 productos = 44 registros
  208 comprobaciones, 21 incidencias, 8 hallazgos, índice 90.

Claves: `row_id` es la clave técnica (única). `id` es la clave de negocio
(puede duplicarse a propósito para demostrar la regla de unicidad).
El 0 en totales/precios es válido (no cuenta como vacío).
"""

METADATA = {
    "clientes": {
        "nombre": "Clientes",
        "descripcion": "Personas registradas en la tienda de ejemplo. Base para segmentación y contacto.",
        "responsable": "Ana Beltrán — Dominio Comercial",
        "dominio": "Comercial",
        "columnas": [
            {"nombre": "id", "tipo": "texto"},
            {"nombre": "nombre", "tipo": "texto"},
            {"nombre": "email", "tipo": "correo"},
        ],
        "reglas": ["Obligatoriedad en id, nombre y email", "Unicidad en id", "Formato de correo en email"],
    },
    "pedidos": {
        "nombre": "Pedidos",
        "descripcion": "Compras realizadas por los clientes con fecha e importe total.",
        "responsable": "Luis Camargo — Dominio Ventas",
        "dominio": "Ventas",
        "columnas": [
            {"nombre": "id", "tipo": "texto"},
            {"nombre": "cliente_id", "tipo": "texto"},
            {"nombre": "fecha", "tipo": "fecha"},
            {"nombre": "total", "tipo": "número"},
        ],
        "reglas": ["Obligatoriedad en id, cliente_id, fecha y total", "Unicidad en id"],
    },
    "productos": {
        "nombre": "Productos",
        "descripcion": "Catálogo de artículos disponibles para la venta.",
        "responsable": "María Solís — Dominio Catálogo",
        "dominio": "Catálogo",
        "columnas": [
            {"nombre": "id", "tipo": "texto"},
            {"nombre": "nombre", "tipo": "texto"},
            {"nombre": "precio", "tipo": "número"},
        ],
        "reglas": ["Obligatoriedad en id, nombre y precio", "Unicidad en id"],
    },
}

CLIENTES = [
    {"row_id": "cli-01", "id": "CLI-001", "nombre": "Lucía Fernández", "email": "lucia.fernandez@example.com"},
    {"row_id": "cli-02", "id": "CLI-002", "nombre": "Marco Ruiz", "email": "marco.ruiz@example.com"},
    {"row_id": "cli-03", "id": "CLI-003", "nombre": "Sofía Herrera", "email": ""},
    {"row_id": "cli-04", "id": "CLI-004", "nombre": "Diego Torres", "email": "diego.torres@example.com"},
    {"row_id": "cli-05", "id": "CLI-004", "nombre": "Diego Torres (duplicado)", "email": "d.torres2@example.com"},
    {"row_id": "cli-06", "id": "CLI-006", "nombre": "   ", "email": "carlos.mendez@example.com"},
    {"row_id": "cli-07", "id": "CLI-007", "nombre": "Ana Gómez", "email": "ana.gomez@"},
    {"row_id": "cli-08", "id": "CLI-008", "nombre": "Juan Pérez", "email": "juan.perez[at]correo.com"},
    {"row_id": "cli-09", "id": "CLI-009", "nombre": "Valeria Castro", "email": "valeria.castro@example.com"},
    {"row_id": "cli-10", "id": "CLI-010", "nombre": "Pedro Sánchez", "email": "pedro.sanchez@example.com"},
    {"row_id": "cli-11", "id": "CLI-011", "nombre": "Carmen Díaz", "email": "carmen.diaz@example.com"},
    {"row_id": "cli-12", "id": "CLI-012", "nombre": "Raúl Ortega", "email": "raul.ortega@example.com"},
    {"row_id": "cli-13", "id": "CLI-013", "nombre": "Elena Ruiz", "email": "elena.ruiz@example.com"},
    {"row_id": "cli-14", "id": "CLI-014", "nombre": "Jorge López", "email": "jorge.lopez@example"},
    {"row_id": "cli-15", "id": "CLI-015", "nombre": "", "email": "sin.nombre@example.com"},
    {"row_id": "cli-16", "id": "CLI-009", "nombre": "Valeria Castro (duplicada)", "email": "valeria2@example.com"},
    {"row_id": "cli-17", "id": "CLI-017", "nombre": "   ", "email": "espacios@example.com"},
    {"row_id": "cli-18", "id": "CLI-018", "nombre": "Marta Gil", "email": ""},
    {"row_id": "cli-19", "id": "CLI-019", "nombre": "Iván Paz", "email": "ivan.paz@example.com"},
    {"row_id": "cli-20", "id": "CLI-020", "nombre": "Sara Rey", "email": "sara.rey@example"},
]

PEDIDOS = [
    {"row_id": "ped-01", "id": "PED-001", "cliente_id": "CLI-001", "fecha": "2026-01-10", "total": 150.5},
    {"row_id": "ped-02", "id": "PED-002", "cliente_id": "CLI-002", "fecha": "2026-01-11", "total": 0},
    {"row_id": "ped-03", "id": "PED-003", "cliente_id": "", "fecha": "2026-01-12", "total": 89.9},
    {"row_id": "ped-04", "id": "PED-004", "cliente_id": "CLI-004", "fecha": "2026-01-13", "total": 210.0},
    {"row_id": "ped-05", "id": "PED-005", "cliente_id": "CLI-007", "fecha": "2026-01-20", "total": 45.0},
    {"row_id": "ped-06", "id": "PED-006", "cliente_id": "CLI-009", "fecha": "2026-02-01", "total": 320.75},
    {"row_id": "ped-07", "id": "PED-007", "cliente_id": "CLI-010", "fecha": "2026-02-03", "total": 15.0},
    {"row_id": "ped-08", "id": "PED-008", "cliente_id": "CLI-012", "fecha": "2026-02-05", "total": 99.99},
    {"row_id": "ped-09", "id": "PED-009", "cliente_id": "CLI-013", "fecha": "2026-02-10", "total": 75.0},
    {"row_id": "ped-10", "id": "PED-010", "cliente_id": "", "fecha": "2026-02-11", "total": 120.0},
    {"row_id": "ped-11", "id": "PED-005", "cliente_id": "CLI-015", "fecha": "2026-02-12", "total": 33.3},
    {"row_id": "ped-12", "id": "PED-012", "cliente_id": "CLI-018", "fecha": "2026-02-13", "total": 0},
    {"row_id": "ped-13", "id": "PED-013", "cliente_id": "CLI-019", "fecha": "2026-02-14", "total": 210.5},
    {"row_id": "ped-14", "id": "PED-014", "cliente_id": "CLI-020", "fecha": "2026-02-15", "total": 18.75},
]

PRODUCTOS = [
    {"row_id": "pro-01", "id": "PRO-001", "nombre": "Café Molido 500g", "precio": 85.5},
    {"row_id": "pro-02", "id": "PRO-002", "nombre": "", "precio": 120.0},
    {"row_id": "pro-03", "id": "PRO-003", "nombre": "Taza Cerámica", "precio": 45.0},
    {"row_id": "pro-04", "id": "PRO-004", "nombre": "Filtro Papel x40", "precio": 30.0},
    {"row_id": "pro-05", "id": "PRO-005", "nombre": "Cafetera Prensa 1L", "precio": 450.0},
    {"row_id": "pro-06", "id": "PRO-006", "nombre": "Termo Acero 750ml", "precio": 0},
    {"row_id": "pro-07", "id": "PRO-007", "nombre": "Cafetera Goteo 12T", "precio": 320.0},
    {"row_id": "pro-08", "id": "PRO-008", "nombre": "", "precio": 55.0},
    {"row_id": "pro-09", "id": "PRO-009", "nombre": "Molino Manual", "precio": 0},
    {"row_id": "pro-10", "id": "PRO-003", "nombre": "Taza Cerámica (duplicada)", "precio": 45.0},
]


def get_sample_tables():
    import copy

    return {
        "clientes": copy.deepcopy(CLIENTES),
        "pedidos": copy.deepcopy(PEDIDOS),
        "productos": copy.deepcopy(PRODUCTOS),
    }
