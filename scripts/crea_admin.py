"""Asigna rol admin a una cuenta existente. Ejecutar en la PC del operador:
  .venv\\Scripts\\python.exe scripts/crea_admin.py correo@ejemplo.com
La cuenta debe existir (regístrate primero en la app). No pide ni guarda
contraseñas: solo cambia el rol. Requiere las credenciales de nexo_app en .env.
"""
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "backend"))

from auth import MysqlAuthStore  # noqa: E402


def env_nexo(path):
    data = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if s and not s.startswith("#") and "=" in s:
                k, v = s.split("=", 1)
                data[k.strip()] = v.strip().strip('"').strip("'")
    return data


def main():
    if len(sys.argv) != 2 or "@" not in sys.argv[1]:
        print("Uso: python scripts/crea_admin.py correo@ejemplo.com")
        sys.exit(2)
    email = sys.argv[1].strip().lower()
    e = env_nexo(os.path.join(BASE, ".env"))
    store = MysqlAuthStore({"host": e.get("NEXO_MYSQL_HOST", "127.0.0.1"),
                            "port": int(e.get("NEXO_MYSQL_PORT", "3306")),
                            "user": e.get("NEXO_APP_USER", ""),
                            "password": e.get("NEXO_APP_PASSWORD", "")})
    user = store.find_user(email)
    if not user:
        print("No existe esa cuenta. Regístrala primero en la app.")
        sys.exit(1)
    conn = store._connect()
    try:
        cur = conn.cursor()
        cur.execute("UPDATE users SET rol='admin', estado='activo' WHERE id=%s", (user["id"],))
        conn.commit()
    finally:
        conn.close()
    print(f"Listo: {email} ahora es admin.")


if __name__ == "__main__":
    main()
