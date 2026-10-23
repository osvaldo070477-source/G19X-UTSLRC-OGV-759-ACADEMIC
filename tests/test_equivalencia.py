"""Equivalencia del motor de reglas Python/JavaScript (RNF4).

Ejecuta los mismos casos con backend/rules.py y con el bloque JavaScript de
public/js/base.js, y compara cifras, hallazgos y evidencias.

Uso local:  python tests/test_equivalencia.py
En CI:      python tests/test_equivalencia.py --require-node

Si Node no esta instalado, la prueba se omite (salvo con --require-node).
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "backend"))
from rules import analyze_tables  # noqa: E402
from sample import get_sample_tables  # noqa: E402

fails = []


def check(name, cond):
    print(("OK  " if cond else "FALLO ") + name)
    if not cond:
        fails.append(name)


def canon(r):
    """Normaliza la salida de ambos motores a una forma comparable."""
    hallazgos = []
    for h in r["hallazgos"]:
        hallazgos.append({
            "tabla": h["tabla"],
            "columna": h["columna"],
            "regla": h["regla"],
            "regla_etiqueta": h["regla_etiqueta"],
            "prioridad": h["prioridad"],
            "incidencias": h["incidencias"],
            "recomendacion": h["recomendacion"],
            "evidencias": sorted(
                ({"row_id": e["row_id"], "valor": e["valor"], "ref": e["ref"]}
                 for e in h["evidencias"]),
                key=lambda e: str(e["row_id"]),
            ),
        })
    hallazgos.sort(key=lambda h: (h["tabla"], h["columna"], h["regla"]))
    return {
        "comprobaciones": r["comprobaciones"],
        "incidencias": r["incidencias"],
        "indice": r["indice"],
        "filas_afectadas": r["filas_afectadas"],
        "total_registros": r["total_registros"],
        "hallazgos": hallazgos,
    }


def casos():
    return [
        {"id": "muestra", "tables": get_sample_tables()},
        {"id": "sin_tablas", "tables": {}},
        {"id": "tablas_vacias", "tables": {"clientes": [], "pedidos": [], "productos": []}},
        {"id": "cero_no_es_vacio", "tables": {
            "clientes": [
                {"row_id": "c1", "id": "C-1", "nombre": 0, "email": "a@b.co"},
            ],
            "pedidos": [
                {"row_id": "p1", "id": "P-1", "cliente_id": "", "fecha": "", "total": 0},
            ],
            "productos": [],
        }},
        {"id": "booleanos", "tables": {
            "clientes": [
                {"row_id": "c1", "id": "C-1", "nombre": False, "email": "a@b.co"},
            ],
            "pedidos": [],
            "productos": [],
        }},
        {"id": "espacios", "tables": {
            "clientes": [
                {"row_id": "c1", "id": "   ", "nombre": "\t", "email": "  "},
            ],
            "pedidos": [],
            "productos": [],
        }},
        {"id": "duplicado_con_espacios", "tables": {
            "clientes": [
                {"row_id": "c1", "id": "X-1", "nombre": "A", "email": "a@b.co"},
                {"row_id": "c2", "id": "  X-1  ", "nombre": "B", "email": "b@b.co"},
            ],
            "pedidos": [],
            "productos": [],
        }},
        {"id": "correos_borde", "tables": {
            "clientes": [
                {"row_id": "c1", "id": "C-1", "nombre": "A", "email": "a@b.c"},
                {"row_id": "c2", "id": "C-2", "nombre": "B", "email": "a@b"},
                {"row_id": "c3", "id": "C-3", "nombre": "C", "email": "a b@c.d"},
                {"row_id": "c4", "id": "C-4", "nombre": "D", "email": "a@b.co "},
                {"row_id": "c5", "id": "C-5", "nombre": "E", "email": ""},
            ],
            "pedidos": [],
            "productos": [],
        }},
        {"id": "faltantes", "tables": {
            "clientes": [{"row_id": "c1"}],
            "pedidos": [{"row_id": "p1"}],
            "productos": [{"row_id": "pr1"}],
        }},
        {"id": "redondeo_mitad", "tables": {
            "clientes": [
                {"row_id": "c%02d" % n, "id": "C-%03d" % n,
                 "nombre": "" if n <= 3 else "N%d" % n,
                 "email": "u%d@example.com" % n}
                for n in range(1, 41)
            ],
            "pedidos": [],
            "productos": [],
        }},
        {"id": "tabla_desconocida", "tables": {
            "clientes": [
                {"row_id": "c1", "id": "C-1", "nombre": "A", "email": "a@b.co"},
            ],
            "desconocida": [{"row_id": "x1", "id": "X-1"}],
        }},
    ]


def main():
    lista = casos()

    node = shutil.which("node")
    if not node:
        if "--require-node" in sys.argv:
            print("FALLO  Node no esta disponible y se exigio --require-node")
            print("RESULTADO: 1 FALLOS")
            return 1
        print("OMITIDO  Node no esta instalado: no se puede ejecutar el motor JavaScript.")
        print("RESULTADO: OMITIDO")
        return 0

    with tempfile.TemporaryDirectory() as tmp:
        ruta = os.path.join(tmp, "casos.json")
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(lista, f, ensure_ascii=False)
        proc = subprocess.run(
            [node, os.path.join(BASE, "tests", "equivalence.js"), ruta],
            capture_output=True, text=True, encoding="utf-8",
        )

    if proc.returncode != 0:
        print("FALLO  el motor JavaScript no se pudo ejecutar:")
        print((proc.stderr or proc.stdout or "")[:2000])
        print("RESULTADO: 1 FALLOS")
        return 1

    try:
        salida = json.loads(proc.stdout)
    except ValueError:
        print("FALLO  el motor JavaScript no devolvio JSON valido:")
        print(proc.stdout[:2000])
        print("RESULTADO: 1 FALLOS")
        return 1

    js = {item["id"]: item["result"] for item in salida}

    # El propio motor JS debe reproducir las cifras de referencia.
    muestra = canon(js["muestra"])
    check("JS muestra: 44 registros", muestra["total_registros"] == 44)
    check("JS muestra: 208 comprobaciones", muestra["comprobaciones"] == 208)
    check("JS muestra: 21 incidencias", muestra["incidencias"] == 21)
    check("JS muestra: 8 hallazgos", len(muestra["hallazgos"]) == 8)
    check("JS muestra: indice 90", muestra["indice"] == 90)

    for caso in lista:
        py = canon(analyze_tables(caso["tables"]))
        jsr = canon(js[caso["id"]])
        igual = py == jsr
        check("equivalencia: " + caso["id"], igual)
        if not igual:
            print("   Python: " + json.dumps(py, ensure_ascii=False, sort_keys=True)[:900])
            print("   JS:     " + json.dumps(jsr, ensure_ascii=False, sort_keys=True)[:900])

    print("RESULTADO:", "TODO OK" if not fails else str(len(fails)) + " FALLOS")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
