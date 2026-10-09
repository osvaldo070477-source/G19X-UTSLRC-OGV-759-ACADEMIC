"""Servicio Python de NEXO (solo biblioteca estándar).

Uso:
  .venv\\Scripts\\python.exe backend\\app.py --demo            # muestra sintética, memoria
  .venv\\Scripts\\python.exe backend\\app.py --port 8001       # intenta MySQL según .env
  .venv\\Scripts\\python.exe backend\\app.py --demo --port 8001

Modos:
  --demo : usa la muestra sintética y guarda en memoria (se pierde al reiniciar).
  MySQL  : lee nexo_source y persiste en nexo_app. Si falla, responde error;
           NUNCA cambia silenciosamente a datos simulados.

Rutas (prefijo /api):
  GET  /api/health        (sin token)
  POST /api/analyze       (token)  body: {} -> ejecuta análisis
  GET  /api/runs          (token)  ?limit=20
  GET  /api/runs/<id>     (token)  detalle + decisiones vigentes
  POST /api/decisions     (token)  {run_id, tabla, columna, regla, accion, comentario?}
  GET  /api/catalog       (token)  metadatos + muestra (demo) o conteos (mysql)
  GET  /api/agent/status  (token)  proveedor, modelo, límites (sin secretos)
  POST /api/agent/jobs    (token)  {fuente: muestra|origen, pedir_revision?} -> {job_id}
  GET  /api/agent/jobs    (token)  ?limit=20
  GET  /api/agent/jobs/<id> (token) progreso y detalle
  POST /api/agent/jobs/<id>/cancel (token)
  POST /api/agent/jobs/<id>/review (token) {decision: approve|reject, comentario?}
  POST /api/agent/jobs/<id>/retry  (token) reintento explícito (trabajo nuevo)
  POST /api/auth/register (token) {nombre, email, password} -> {user, session}
  POST /api/auth/login    (token) {email, password} -> {user, session}
  GET  /api/auth/me       (token + sesión) perfil propio
  GET  /api/auth/profile  (token + sesión) perfil completo con rol y registro
  POST /api/auth/update_name (token + sesión) {nombre}
  POST /api/auth/change_password (token + sesión) {actual, nueva}
  GET  /api/auth/activity (token + sesión) decisiones propias paginadas
  GET  /api/admin/users  (token + sesión admin) lista sin hashes
  POST /api/admin/users/<id>/estado|desbloquear|reset_password (admin)
  POST /api/auth/logout   (token + sesión) cierra la sesión

Auth: cabecera X-NEXO-Token == NEXO_INTERNAL_TOKEN del .env.
Límite: 10 000 filas por tabla; si se excede se rechaza (413), sin truncar.
Agentes: trabajos en segundo plano; el proveedor real exige NEXO_AI_API_KEY.
Sin clave se usa el proveedor de prueba (stub), etiquetado como tal.
"""

import argparse
import datetime
import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
from rules import analyze_tables  # noqa: E402
from sample import METADATA, get_sample_tables  # noqa: E402
from providers import ai_config_from_env, make_provider, provider_status  # noqa: E402
from jobs import Manager, MemoryStore, MysqlStore  # noqa: E402
from agents import AGENTS  # noqa: E402
from auth import AuthError, AuthService, MemoryAuthStore, MysqlAuthStore  # noqa: E402

VERSION = "1.1.0"
MAX_ROWS_PER_TABLE = 10000
VALID_ACTIONS = ("accept", "discard", "reopen")

_store_lock = threading.Lock()
_mem_runs = []   # lista de ejecuciones en memoria (modo demo / sin MySQL)
_mem_seq = [0]


def load_env(path):
    """Carga KEY=VALUE simple sin dependencias. No sobrescribe lo ya definido."""
    if not os.path.isfile(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if k and k not in os.environ:
                os.environ[k] = v


load_env(os.path.join(os.path.dirname(BASE_DIR), ".env"))

INTERNAL_TOKEN = os.environ.get("NEXO_INTERNAL_TOKEN", "")
AI_CFG = ai_config_from_env()
MYSQL_CFG = {
    "host": os.environ.get("NEXO_MYSQL_HOST", "127.0.0.1"),
    "port": int(os.environ.get("NEXO_MYSQL_PORT", "3306")),
    "user": os.environ.get("NEXO_APP_USER", ""),
    "password": os.environ.get("NEXO_APP_PASSWORD", ""),
    "database": "nexo_app",
}
SOURCE_CFG = dict(MYSQL_CFG, user=os.environ.get("NEXO_RO_USER", ""),
                  password=os.environ.get("NEXO_RO_PASSWORD", ""),
                  database="nexo_source")


def log_internal(action, exc):
    """Detalle técnico solo en el log protegido del servidor, nunca al usuario."""
    try:
        logdir = os.path.join(os.path.dirname(BASE_DIR), "logs")
        os.makedirs(logdir, exist_ok=True)
        with open(os.path.join(logdir, "nexo.log"), "a", encoding="utf-8") as f:
            f.write(f"{datetime.datetime.now().isoformat(timespec='seconds')} "
                    f"[{action}] {type(exc).__name__}: {exc}\n")
    except OSError:
        pass


# ---------------- MySQL (opcional, solo modo C) ----------------

def _mysql():
    try:
        import mysql.connector  # type: ignore
    except ImportError as e:
        raise RuntimeError(
            "mysql-connector-python no está instalado. Instálalo con: "
            ".venv\\Scripts\\python.exe -m pip install mysql-connector-python"
        ) from e
    return mysql.connector


def mysql_conn(cfg):
    mod = _mysql()
    return mod.connect(host=cfg["host"], port=cfg["port"], user=cfg["user"],
                       password=cfg["password"], database=cfg["database"])


def mysql_available():
    try:
        c = mysql_conn(MYSQL_CFG)
        c.close()
        return True
    except Exception:
        return False


def fetch_source_tables():
    """Lee las 3 tablas fuente con cuenta de solo lectura. Rechaza > límite."""
    conn = mysql_conn(SOURCE_CFG)
    try:
        cur = conn.cursor(dictionary=True)
        tables = {}
        mapping = {"clientes": "clientes", "pedidos": "pedidos", "productos": "productos"}
        for logical, physical in mapping.items():
            cur.execute(f"SELECT COUNT(*) AS n FROM `{physical}`")
            n = cur.fetchone()["n"]
            if n > MAX_ROWS_PER_TABLE:
                raise ValueError(
                    f"La tabla {physical} tiene {n} filas y excede el límite de "
                    f"{MAX_ROWS_PER_TABLE}. Análisis rechazado sin truncar."
                )
            cur.execute(f"SELECT * FROM `{physical}` ORDER BY row_id")
            tables[logical] = cur.fetchall()
        return tables
    finally:
        conn.close()


def save_run_mysql(result, mode):
    """Guarda ejecución + hallazgos en transacción. Devuelve run_id."""
    conn = mysql_conn(MYSQL_CFG)
    try:
        cur = conn.cursor()
        conn.start_transaction()
        cur.execute(
            "INSERT INTO runs (modo, total_registros, comprobaciones, incidencias, indice, hallazgos) "
            "VALUES (%s,%s,%s,%s,%s,%s)",
            (mode, result["total_registros"], result["comprobaciones"],
             result["incidencias"], result["indice"], len(result["hallazgos"])),
        )
        run_id = cur.lastrowid
        for h in result["hallazgos"]:
            cur.execute(
                "INSERT INTO findings (run_id, tabla, columna, regla, prioridad, incidencias, recomendacion) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (run_id, h["tabla"], h["columna"], h["regla"], h["prioridad"],
                 h["incidencias"], h["recomendacion"]),
            )
            finding_id = cur.lastrowid
            for e in h["evidencias"]:
                cur.execute(
                    "INSERT INTO evidence (finding_id, row_id, valor, ref) VALUES (%s,%s,%s,%s)",
                    (finding_id, str(e["row_id"]), None if e["valor"] is None else str(e["valor"]), e["ref"]),
                )
        conn.commit()
        return run_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def list_runs_mysql(limit=20):
    conn = mysql_conn(MYSQL_CFG)
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM runs ORDER BY id DESC LIMIT %s", (limit,))
        return cur.fetchall()
    finally:
        conn.close()


def latest_run_id_mysql():
    conn = mysql_conn(MYSQL_CFG)
    try:
        cur = conn.cursor()
        cur.execute("SELECT MAX(id) FROM runs")
        row = cur.fetchone()
        return row[0] if row else None
    finally:
        conn.close()


def get_run_mysql(run_id):
    conn = mysql_conn(MYSQL_CFG)
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM runs WHERE id=%s", (run_id,))
        run = cur.fetchone()
        if not run:
            return None
        run["creado_en"] = str(run.get("creado_en"))
        cur.execute("SELECT * FROM findings WHERE run_id=%s ORDER BY id", (run_id,))
        findings = cur.fetchall()
        for f in findings:
            cur.execute("SELECT row_id, valor, ref FROM evidence WHERE finding_id=%s ORDER BY row_id", (f["id"],))
            f["evidencias"] = cur.fetchall()
            cur.execute(
                "SELECT accion, comentario, creado_en FROM decision_events "
                "WHERE finding_id=%s ORDER BY id DESC LIMIT 1", (f["id"],))
            last = cur.fetchone()
            f["estado"] = last["accion"] if last else "pending"
            f["ultimo_comentario"] = last["comentario"] if last else None
        run["hallazgos"] = findings
        return run
    finally:
        conn.close()


def add_decision_mysql(run_id, tabla, columna, regla, accion, comentario, decided_by=None,
                       with_author=False):
    latest = latest_run_id_mysql()
    if latest is None or int(run_id) != int(latest):
        raise ValueError("Solo se aceptan decisiones sobre la ejecución más reciente.")
    conn = mysql_conn(MYSQL_CFG)
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id FROM findings WHERE run_id=%s AND tabla=%s AND columna=%s AND regla=%s",
            (run_id, tabla, columna, regla))
        row = cur.fetchone()
        if not row:
            raise ValueError("Hallazgo no encontrado en esa ejecución.")
        if with_author:
            cur.execute(
                "INSERT INTO decision_events (finding_id, accion, comentario, decided_by) "
                "VALUES (%s,%s,%s,%s)",
                (row[0], accion, comentario, decided_by))
        else:
            cur.execute(
                "INSERT INTO decision_events (finding_id, accion, comentario) VALUES (%s,%s,%s)",
                (row[0], accion, comentario))
        conn.commit()
        return row[0]
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ---------------- Memoria (modos demo / sin MySQL) ----------------

def save_run_memory(result, mode):
    with _store_lock:
        _mem_seq[0] += 1
        run = {
            "id": _mem_seq[0],
            "modo": mode,
            "creado_en": datetime.datetime.now().isoformat(timespec="seconds"),
            "total_registros": result["total_registros"],
            "comprobaciones": result["comprobaciones"],
            "incidencias": result["incidencias"],
            "indice": result["indice"],
            "hallazgos": [],
        }
        fid = 0
        for h in result["hallazgos"]:
            fid += 1
            run["hallazgos"].append({
                "id": fid, "tabla": h["tabla"], "columna": h["columna"],
                "regla": h["regla"], "prioridad": h["prioridad"],
                "incidencias": h["incidencias"], "recomendacion": h["recomendacion"],
                "evidencias": h["evidencias"], "estado": "pending",
                "eventos": [], "ultimo_comentario": None,
            })
        _mem_runs.append(run)
        return run["id"]


def add_decision_memory(run_id, tabla, columna, regla, accion, comentario, decided_by=None):
    with _store_lock:
        if not _mem_runs or int(run_id) != int(_mem_runs[-1]["id"]):
            raise ValueError("Solo se aceptan decisiones sobre la ejecución más reciente.")
        run = _mem_runs[-1]
        for f in run["hallazgos"]:
            if f["tabla"] == tabla and f["columna"] == columna and f["regla"] == regla:
                f["eventos"].append({"accion": accion, "comentario": comentario,
                                     "creado_en": datetime.datetime.now().isoformat(timespec="seconds"),
                                     "por": decided_by})
                f["estado"] = accion
                f["ultimo_comentario"] = comentario
                f["decidido_por"] = (decided_by or {}).get("nombre")
                return f["id"]
        raise ValueError("Hallazgo no encontrado en esa ejecución.")


# ---------------- HTTP ----------------

class Handler(BaseHTTPRequestHandler):
    server_version = "NEXO/1.0"

    def log_message(self, *a):
        pass

    def _send(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _need_token(self):
        if not INTERNAL_TOKEN:
            return True  # sin token configurado, el servidor rechaza escrituras
        return self.headers.get("X-NEXO-Token") != INTERNAL_TOKEN

    def _body(self):
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            n = 0
        if n <= 0:
            return {}
        try:
            return json.loads(self.rfile.read(n).decode("utf-8") or "{}")
        except (ValueError, UnicodeDecodeError):
            return None

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/api/health":
            ok = (not self.server.use_mysql) or mysql_available()
            ai = provider_status(AI_CFG)
            self._send(200, {"status": "ok", "version": VERSION,
                             "mode": "mysql" if self.server.use_mysql else "demo",
                             "mysql_ok": ok if self.server.use_mysql else False,
                             "ai": {"provider": ai["provider"], "model": ai["model"],
                                    "stub": ai["stub"], "configured": ai["configured"],
                                    "missing": ai["missing"]}})
            return
        if self._need_token():
            self._send(401, {"error": "Token interno inválido o ausente."})
            return
        if path == "/api/agent/status":
            self._send(200, {**provider_status(AI_CFG), "agents": AGENTS,
                             "modes": ["muestra", "origen"]})
            return
        if path == "/api/auth/me":
            try:
                user = self.server.auth.user_public(
                    self.server.auth.me(self.headers.get("X-NEXO-Session") or ""))
            except AuthError:
                self._send(401, {"error": "Sin sesión válida."})
            else:
                self._send(200, {"user": user})
            return
        if path == "/api/auth/profile":
            try:
                user = self.server.auth.profile(self.headers.get("X-NEXO-Session") or "")
            except AuthError as e:
                self._auth_error(e)
            except Exception as e:
                log_internal("profile", e)
                self._send(502, {"error": "No fue posible cargar el perfil. Inténtalo de nuevo."})
            else:
                self._send(200, {"user": user})
            return
        if path == "/api/auth/activity":
            qs = parse_qs(parsed.query)
            try:
                act = self.server.auth.activity(self.headers.get("X-NEXO-Session") or "",
                                                qs.get("limit", ["10"])[0], qs.get("offset", ["0"])[0])
            except AuthError as e:
                self._auth_error(e)
            except Exception as e:
                log_internal("activity", e)
                self._send(502, {"error": "No fue posible cargar la actividad. Inténtalo de nuevo."})
            else:
                self._send(200, act)
            return
        if path == "/api/admin/users":
            qs = parse_qs(parsed.query)
            try:
                res = self.server.auth.admin_list(self.headers.get("X-NEXO-Session") or "",
                                                  qs.get("limit", ["20"])[0], qs.get("offset", ["0"])[0])
            except AuthError as e:
                self._auth_error(e)
            except Exception as e:
                log_internal("admin_list", e)
                self._send(502, {"error": "No fue posible listar usuarios. Inténtalo de nuevo."})
            else:
                self._send(200, res)
            return
        if path == "/api/agent/jobs":
            qs = parse_qs(parsed.query)
            try:
                limit = max(1, min(100, int(qs.get("limit", ["20"])[0])))
            except ValueError:
                limit = 20
            try:
                self._send(200, {"jobs": self.server.agent_manager.list(limit)})
            except Exception as e:
                self._send(502, {"error": f"No se pudieron listar los trabajos: {e}"})
            return
        if path.startswith("/api/agent/jobs/"):
            try:
                job_id = int(path.rsplit("/", 1)[1])
            except ValueError:
                self._send(400, {"error": "Identificador de trabajo inválido."})
                return
            try:
                job = self.server.agent_manager.get(job_id)
            except Exception as e:
                self._send(502, {"error": f"No se pudo recuperar el trabajo: {e}"})
                return
            if not job:
                self._send(404, {"error": "Trabajo no encontrado."})
                return
            self._send(200, {"job": job})
            return
        if path == "/api/runs":
            qs = parse_qs(parsed.query)
            try:
                limit = max(1, min(100, int(qs.get("limit", ["20"])[0])))
            except ValueError:
                limit = 20
            try:
                if self.server.use_mysql:
                    rows = list_runs_mysql(limit)
                    items = [dict(r, creado_en=str(r.get("creado_en"))) for r in rows]
                else:
                    with _store_lock:
                        items = [{k: v for k, v in r.items() if k != "hallazgos"} | {"hallazgos": len(r["hallazgos"])}
                                 for r in reversed(_mem_runs[-limit:])]
                self._send(200, {"runs": items})
            except Exception as e:
                self._send(502, {"error": f"No se pudo consultar el historial: {e}"})
            return
        if path.startswith("/api/runs/"):
            try:
                run_id = int(path.rsplit("/", 1)[1])
            except ValueError:
                self._send(400, {"error": "Identificador de ejecución inválido."})
                return
            try:
                if self.server.use_mysql:
                    run = get_run_mysql(run_id)
                else:
                    with _store_lock:
                        run = next((r for r in _mem_runs if r["id"] == run_id), None)
                if not run:
                    self._send(404, {"error": "Ejecución no encontrada."})
                    return
                self._send(200, {"run": run})
            except Exception as e:
                self._send(502, {"error": f"No se pudo recuperar la ejecución: {e}"})
            return
        if path == "/api/catalog":
            try:
                if self.server.use_mysql:
                    tables = fetch_source_tables()
                    counts = {k: len(v) for k, v in tables.items()}
                    self._send(200, {"metadatos": METADATA, "conteos": counts, "muestra": None,
                                     "nota": "Modo MySQL: la vista de datos vive en la base nexo_source."})
                else:
                    tables = get_sample_tables()
                    self._send(200, {"metadatos": METADATA, "conteos": {k: len(v) for k, v in tables.items()},
                                     "muestra": tables})
            except Exception as e:
                self._send(502, {"error": f"No se pudo leer el origen: {e}"})
            return
        self._send(404, {"error": "Ruta no encontrada."})

    def _session_user(self):
        """Devuelve el perfil público o None (invitado). Nunca falla."""
        try:
            uid = self.server.auth.me(self.headers.get("X-NEXO-Session") or "")
            return self.server.auth.user_public(uid)
        except AuthError:
            return None

    def _auth_error(self, e):
        codes = {"datos_invalidos": 400, "email_en_uso": 400,
                 "credenciales_invalidas": 401, "sesion_invalida": 401,
                 "cuenta_bloqueada": 423, "no_autorizado": 403}
        self._send(codes.get(e.code, 400), {"error": str(e), "code": e.code})

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if path not in ("/api/analyze", "/api/decisions",
                        "/api/auth/register", "/api/auth/login", "/api/auth/logout",
                        "/api/auth/update_name", "/api/auth/change_password") \
                and not path.startswith("/api/agent/jobs") \
                and not path.startswith("/api/admin/users"):
            self._send(404, {"error": "Ruta no encontrada."})
            return
        if self._need_token():
            self._send(401, {"error": "Token interno inválido o ausente."})
            return
        data = self._body()
        if data is None:
            self._send(400, {"error": "Cuerpo JSON inválido."})
            return
        if path == "/api/auth/register":
            try:
                user, session = self.server.auth.register(
                    data.get("nombre", ""), data.get("email", ""), data.get("password", ""))
            except AuthError as e:
                self._auth_error(e)
            except Exception as e:
                log_internal("register", e)
                self._send(502, {"error": "No fue posible completar el registro. Inténtalo de nuevo."})
            else:
                self._send(201, {"ok": True, "user": AuthService.public(user), "session": session})
            return
        if path == "/api/auth/login":
            try:
                user, session = self.server.auth.login(
                    data.get("email", ""), data.get("password", ""))
            except AuthError as e:
                self._auth_error(e)
            except Exception as e:
                log_internal("login", e)
                self._send(502, {"error": "No fue posible completar el acceso. Inténtalo de nuevo."})
            else:
                self._send(200, {"ok": True, "user": AuthService.public(user), "session": session})
            return
        if path == "/api/auth/logout":
            self.server.auth.logout(self.headers.get("X-NEXO-Session") or "")
            self._send(200, {"ok": True})
            return
        if path.startswith("/api/admin/users/"):
            parts = path.rsplit("/", 2)
            try:
                target = int(parts[-2])
            except ValueError:
                self._send(400, {"error": "Usuario inválido."})
                return
            op, ses = parts[-1], self.headers.get("X-NEXO-Session") or ""
            try:
                if op == "estado":
                    self.server.auth.admin_estado(ses, target, data.get("estado", ""))
                elif op == "desbloquear":
                    self.server.auth.admin_unlock(ses, target)
                elif op == "reset_password":
                    self.server.auth.admin_reset(ses, target, data.get("nueva", ""))
                else:
                    self._send(404, {"error": "Ruta no encontrada."})
                    return
            except AuthError as e:
                self._auth_error(e)
            except Exception as e:
                log_internal("admin_user", e)
                self._send(502, {"error": "No fue posible completar la acción. Inténtalo de nuevo."})
            else:
                self._send(200, {"ok": True})
            return
        if path == "/api/auth/update_name":
            try:
                user = self.server.auth.update_nombre(self.headers.get("X-NEXO-Session") or "",
                                                      data.get("nombre", ""))
            except AuthError as e:
                self._auth_error(e)
            except Exception as e:
                log_internal("update_name", e)
                self._send(502, {"error": "No fue posible guardar el nombre. Inténtalo de nuevo."})
            else:
                self._send(200, {"ok": True, "user": user})
            return
        if path == "/api/auth/change_password":
            try:
                self.server.auth.change_password(self.headers.get("X-NEXO-Session") or "",
                                                 data.get("actual", ""), data.get("nueva", ""))
            except AuthError as e:
                self._auth_error(e)
            except Exception as e:
                log_internal("change_password", e)
                self._send(502, {"error": "No fue posible cambiar la contraseña. Inténtalo de nuevo."})
            else:
                self._send(200, {"ok": True})
            return
        if path == "/api/agent/jobs":
            try:
                job_id = self.server.agent_manager.start(data)
            except ValueError as e:
                self._send(409, {"error": str(e)})
            except Exception as e:
                self._send(502, {"error": f"No se pudo iniciar el trabajo: {e}"})
            else:
                self._send(202, {"job_id": job_id, "estado": "en_ejecucion",
                                 "nota": "Trabajo en segundo plano; consulta su progreso."})
            return
        if path.startswith("/api/agent/jobs/"):
            parts = path.rsplit("/", 2)
            try:
                job_id = int(parts[-2])
            except ValueError:
                self._send(400, {"error": "Identificador de trabajo inválido."})
                return
            action = parts[-1]
            mgr = self.server.agent_manager
            try:
                if action == "cancel":
                    mgr.cancel(job_id)
                    self._send(200, {"ok": True, "estado": "cancelado"})
                elif action == "review":
                    decision = data.get("decision")
                    estado = mgr.review(job_id, decision, data.get("comentario") or "")
                    self._send(200, {"ok": True, "estado": estado})
                elif action == "retry":
                    new_id = mgr.retry(job_id)
                    self._send(202, {"job_id": new_id, "estado": "en_ejecucion"})
                else:
                    self._send(404, {"error": "Ruta no encontrada."})
            except LookupError as e:
                self._send(404, {"error": str(e)})
            except ValueError as e:
                self._send(409, {"error": str(e)})
            except Exception as e:
                self._send(502, {"error": f"No se pudo procesar la acción: {e}"})
            return
        if path == "/api/analyze":
            try:
                if self.server.use_mysql:
                    tables = fetch_source_tables()
                    mode = "mysql"
                else:
                    tables = get_sample_tables()
                    mode = "demo"
                result = analyze_tables(tables)
                if self.server.use_mysql:
                    run_id = save_run_mysql(result, mode)
                else:
                    run_id = save_run_memory(result, mode)
                self._send(200, {"run_id": run_id, "modo": mode,
                                 "creado_en": datetime.datetime.now().isoformat(timespec="seconds"),
                                 **result,
                                 "aviso": "Resultados en memoria: se pierden al reiniciar el servicio."
                                 if mode == "demo" else None})
            except ValueError as e:
                self._send(413, {"error": str(e)})
            except Exception as e:
                self._send(502, {"error": f"Error al analizar: {e}"})
            return
        # /api/decisions
        accion = data.get("accion")
        comentario = data.get("comentario") or ""
        if accion not in VALID_ACTIONS:
            self._send(400, {"error": "Acción inválida. Usa accept, discard o reopen."})
            return
        if not isinstance(comentario, str) or len(comentario) > 1000:
            self._send(400, {"error": "El comentario debe tener como máximo 1000 caracteres."})
            return
        for campo in ("run_id", "tabla", "columna", "regla"):
            if not data.get(campo):
                self._send(400, {"error": f"Falta el campo obligatorio: {campo}."})
                return
        if data["tabla"] not in ("clientes", "pedidos", "productos"):
            self._send(400, {"error": "Tabla desconocida."})
            return
        try:
            author = self._session_user()  # None si es invitado; decidir no exige sesión
            if self.server.use_mysql:
                fid = add_decision_mysql(data["run_id"], data["tabla"], data["columna"],
                                         data["regla"], accion, comentario,
                                         decided_by=author["id"] if author else None,
                                         with_author=self.server.with_author)
            else:
                fid = add_decision_memory(data["run_id"], data["tabla"], data["columna"],
                                          data["regla"], accion, comentario, decided_by=author)
            self._send(200, {"ok": True, "finding_id": fid, "estado": accion,
                             "nota": "La decisión queda registrada; no modifica los datos de origen ni el índice."})
        except ValueError as e:
            self._send(409, {"error": str(e)})
        except Exception as e:
            self._send(502, {"error": f"No se pudo registrar la decisión: {e}"})


def main():
    ap = argparse.ArgumentParser(description="Servicio Python de NEXO")
    ap.add_argument("--demo", action="store_true", help="Usa la muestra sintética y memoria.")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8001)
    args = ap.parse_args()

    use_mysql = not args.demo
    if use_mysql and not INTERNAL_TOKEN:
        print("AVISO: NEXO_INTERNAL_TOKEN no configurado; genera .env con scripts/gen_env.py", flush=True)
    mode = "mysql" if use_mysql else "demo"
    srv = HTTPServer((args.host, args.port), Handler)
    srv.use_mysql = use_mysql

    def _fetch_tables(fuente):
        if fuente == "muestra":
            return get_sample_tables()
        if use_mysql:
            return fetch_source_tables()
        raise ValueError("Fuente 'origen' no disponible: el servicio corre sin MySQL (--demo).")

    def _last_run():
        try:
            if use_mysql:
                latest = latest_run_id_mysql()
                return get_run_mysql(latest) if latest else None
            with _store_lock:
                return _mem_runs[-1] if _mem_runs else None
        except Exception:  # noqa: BLE001 - el sondeo del agente no debe fallar por esto
            return None

    def _save_run(result, modo):
        if use_mysql:
            return save_run_mysql(result, modo)
        return save_run_memory(result, modo)

    store = MysqlStore(MYSQL_CFG) if use_mysql else MemoryStore()
    if use_mysql:
        try:
            n = store.mark_interrupted_on_boot()
            if n:
                print(f"Recuperación: {n} trabajo(s) interrumpido(s) por reinicio.", flush=True)
        except Exception as e:  # noqa: BLE001 - sin MySQL a mano se informa y se sigue
            print(f"AVISO: no se pudo verificar trabajos previos: {e}", flush=True)
    try:
        auth_store = MysqlAuthStore(MYSQL_CFG) if use_mysql else MemoryAuthStore()
        try:
            conn = mysql_conn(MYSQL_CFG)
            cur = conn.cursor()
            cur.execute("SELECT decided_by FROM decision_events LIMIT 0")
            with_author = True
            conn.close()
        except Exception:  # noqa: BLE001 - sin la migración 06 se decide sin autoría
            with_author = False
            if use_mysql:
                print("AVISO: aplica sql/06_auth.sql para atribuir decisiones a usuarios.", flush=True)
    except Exception:  # noqa: BLE001
        auth_store, with_author = MemoryAuthStore(), False
    srv.auth = AuthService(auth_store, runs_provider=lambda: list(_mem_runs))
    srv.with_author = with_author and use_mysql
    srv.agent_manager = Manager(store, lambda: make_provider(AI_CFG), AI_CFG,
                                {"fetch_tables": _fetch_tables, "metadata": lambda: METADATA,
                                 "last_run": _last_run, "save_run": _save_run,
                                 "mysql_ok": lambda: mysql_available() if use_mysql else False})
    ai = provider_status(AI_CFG)
    print(f"NEXO servicio Python v{VERSION} en http://{args.host}:{args.port} (modo {mode}, "
          f"IA: {ai['provider']}{' (prueba)' if ai['stub'] else ''})", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
