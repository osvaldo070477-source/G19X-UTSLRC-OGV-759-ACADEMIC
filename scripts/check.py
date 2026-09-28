"""Comprueba requisitos y la equivalencia de la muestra (sin MySQL).
Uso:  python scripts/check.py
"""
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "backend"))
from sample import get_sample_tables  # noqa: E402
from rules import analyze_tables  # noqa: E402
from agent_tools import TOOL_DEFS, validate_call, redact_value  # noqa: E402
from providers import ai_config_from_env, provider_status  # noqa: E402


def cmd_version(cmd):
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        first = (out.stdout or out.stderr or "").strip().splitlines()
        return first[0] if first else "instalado"
    except (FileNotFoundError, subprocess.SubprocessError):
        return None


ok = True
print("== Requisitos ==")
for name, cmd in [("Python", ["python", "--version"]), ("PHP", ["php", "--version"])]:
    v = cmd_version(cmd)
    print(f"  {name}: {v or 'NO ENCONTRADO'}")
    if v is None and name == "Python":
        ok = False
print("  MySQL: pendiente (no requerido para la demostración)")

print("== Muestra y reglas ==")
r = analyze_tables(get_sample_tables())
esperado = {"comprobaciones": 123, "incidencias": 8, "indice": 93,
            "total_registros": 26, "hallazgos": 6}
for k, v in esperado.items():
    real = r[k] if k != "hallazgos" else len(r["hallazgos"])
    marca = "OK " if real == v else "FALLO"
    if real != v:
        ok = False
    print(f"  [{marca}] {k}: {real} (esperado {v})")

print("== Equivalencia JS ==")
print("  La equivalencia con public/app.js se verifica abriendo la demo,")
print("  ejecutando el análisis y comparando 123/8/6/93 (ver README).")

print("== Herramientas agentic ==")
names = [t["name"] for t in TOOL_DEFS]
for esperado in ["listar_tablas", "describir_tabla", "contar_registros", "perfil_columna",
                 "comprobar_obligatoriedad", "comprobar_unicidad", "comprobar_correo",
                 "obtener_evidencia", "consultar_ultimo_analisis"]:
    c = esperado in names
    print(f"  [{'OK ' if c else 'FALLO'}] herramienta {esperado}")
    if not c:
        ok = False
_, err = validate_call("borrar_todo", {})
print(f"  [{'OK ' if err else 'FALLO'}] rechaza herramienta inexistente")
if not err:
    ok = False
_, err = validate_call("describir_tabla", {"tabla": "usuarios"})
print(f"  [{'OK ' if err else 'FALLO'}] rechaza tabla no autorizada")
if not err:
    ok = False
m = redact_value("ana.gomez@example.com", True)
print(f"  [{'OK ' if '@' in m and 'ana.gomez' not in m else 'FALLO'}] enmascara correos ({m})")
if "@" not in m or "ana.gomez" in m:
    ok = False
st = provider_status(ai_config_from_env())
print(f"  [OK ] proveedor configurado: {st['provider']} (stub={st['stub']})")

print("RESULTADO:", "TODO OK" if ok else "HAY FALLOS")
sys.exit(0 if ok else 1)
