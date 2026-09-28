"""Genera .env con secretos aleatorios. Conserva archivos existentes:
si ya hay .env, solo añade las claves que falten sin tocar las demás."""
import os
import secrets

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(BASE, ".env")

AI_DEFAULTS = {
    "NEXO_AI_PROVIDER": "stub",
    "NEXO_AI_MODEL": "gpt-4o-mini",
    "NEXO_AI_BASE_URL": "https://api.openai.com/v1",
    "NEXO_AI_API_KEY": "",
    "NEXO_AI_TIMEOUT_S": "60",
    "NEXO_AI_MAX_STEPS": "10",
    "NEXO_AI_MAX_TOOL_CALLS": "20",
    "NEXO_AI_MAX_RETRIES": "2",
    "NEXO_AI_JOB_TIMEOUT_S": "600",
    "NEXO_AI_MAX_ROWS_TOOL": "200",
    "NEXO_AI_REDACT": "1",
}


def read_env(path):
    data = {}
    if not os.path.exists(path):
        return data, []
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()
    for line in lines:
        s = line.strip()
        if s and not s.startswith("#") and "=" in s:
            k, v = s.split("=", 1)
            data[k.strip()] = v.strip()
    return data, lines


if not os.path.exists(ENV_PATH):
    content = f"""# NEXO · configuración local (NO subir a Git).
NEXO_INTERNAL_TOKEN={secrets.token_hex(24)}
NEXO_PY_URL=http://127.0.0.1:8001
NEXO_MYSQL_HOST=127.0.0.1
NEXO_MYSQL_PORT=3306
NEXO_RO_USER=nexo_ro
NEXO_RO_PASSWORD={secrets.token_urlsafe(18)}
NEXO_APP_USER=nexo_app
NEXO_APP_PASSWORD={secrets.token_urlsafe(18)}
"""
    for k, v in AI_DEFAULTS.items():
        content += f"{k}={v}\n"
    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.write(content)
    print("Archivo .env creado con token y contraseñas aleatorias.")
    print("Ajusta los usuarios de MySQL según sql/04_users_template.sql.")
else:
    data, _ = read_env(ENV_PATH)
    missing = {k: v for k, v in AI_DEFAULTS.items() if k not in data}
    if not missing:
        print("Ya existe .env y está completo; no se modificó nada.")
    else:
        with open(ENV_PATH, "a", encoding="utf-8") as f:
            f.write("\n# Claves de IA añadidas por scripts/gen_env.py (sin tocar lo existente).\n")
            for k, v in missing.items():
                f.write(f"{k}={v}\n")
        print(f".env conservado; se añadieron {len(missing)} claves faltantes: "
              + ", ".join(missing))
