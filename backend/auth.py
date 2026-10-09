"""Autenticación local de NEXO (un operador, sin autenticación empresarial).

- Registro e inicio de sesión con validaciones en servidor.
- Contraseñas con PBKDF2-HMAC-SHA256 + sal aleatoria (biblioteca estándar).
- Bloqueo temporal tras 5 intentos fallidos; sesiones de 8 h.
- Los mensajes de inicio de sesión son genéricos para no revelar
  qué correos existen. Las sesiones viajan como token opaco que PHP
  guarda en $_SESSION; el navegador nunca ve hashes ni tokens.
"""

import hashlib
import re
import secrets
import time

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
NAME_RE = re.compile(r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ'’\- ]{2,60}$")
MAX_ATTEMPTS = 5
LOCK_SECONDS = 15 * 60
SESSION_SECONDS = 8 * 60 * 60
PBKDF2_ROUNDS = 260_000


class AuthError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def validate_nombre(nombre):
    nombre = " ".join(str(nombre or "").split())
    if not NAME_RE.match(nombre):
        return None, "El nombre debe tener entre 2 y 60 letras (se permiten espacios, guiones y apóstrofes)."
    return nombre, None


def validate_email(email):
    email = str(email or "").strip().lower()
    if len(email) > 160 or not EMAIL_RE.match(email):
        return None, "Escribe un correo válido (ej. usuario@dominio.com)."
    return email, None


def validate_password(password):
    pw = str(password or "")
    if not (8 <= len(pw) <= 72):
        return "La contraseña debe tener entre 8 y 72 caracteres."
    faltan = []
    if not re.search(r"[a-záéíóúüñ]", pw):
        faltan.append("una minúscula")
    if not re.search(r"[A-ZÁÉÍÓÚÜÑ]", pw):
        faltan.append("una mayúscula")
    if not re.search(r"[0-9]", pw):
        faltan.append("un número")
    if faltan:
        return "La contraseña debe incluir " + ", ".join(faltan) + "."
    return None


def hash_password(password):
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", str(password).encode("utf-8"), salt, PBKDF2_ROUNDS)
    return f"pbkdf2${PBKDF2_ROUNDS}${salt.hex()}${dk.hex()}"


def check_password(password, stored):
    try:
        algo, rounds, salt_h, dk_h = stored.split("$")
        assert algo == "pbkdf2"
        dk = hashlib.pbkdf2_hmac("sha256", str(password).encode("utf-8"),
                                 bytes.fromhex(salt_h), int(rounds))
        return secrets.compare_digest(dk.hex(), dk_h)
    except (ValueError, AssertionError, TypeError):
        return False


def new_session_token():
    return secrets.token_urlsafe(32)


def token_hash(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class MemoryAuthStore:
    """Usuarios y sesiones temporales (sin MySQL): se pierden al reiniciar."""

    def __init__(self):
        self.users, self.sessions, self.seq = {}, {}, [0]

    def find_user(self, email):
        return self.users.get(email.lower())

    def get_user(self, uid):
        for u in self.users.values():
            if u["id"] == uid:
                return u
        return None

    def insert_user(self, nombre, email, pw_hash):
        self.seq[0] += 1
        user = {"id": self.seq[0], "nombre": nombre, "email": email,
                "pw_hash": pw_hash, "failed": 0, "locked_until": 0,
                "rol": "operador", "estado": "activo",
                "creado_en": time.strftime("%Y-%m-%d %H:%M:%S")}
        self.users[email.lower()] = user
        return user

    def update_user(self, user):
        self.users[user["email"].lower()] = user

    def set_estado(self, uid, estado):
        for u in self.users.values():
            if u["id"] == uid:
                u["estado"] = estado
                return True
        return False

    def list_users(self, limit=20, offset=0):
        users = sorted(self.users.values(), key=lambda u: u["id"])
        items = [{"id": u["id"], "nombre": u["nombre"], "email": u["email"],
                  "rol": u.get("rol") or "operador", "estado": u.get("estado") or "activo",
                  "failed": u.get("failed", 0), "locked_until": u.get("locked_until", 0),
                  "creado_en": str(u.get("creado_en") or "")} for u in users]
        return {"items": items[offset:offset + limit], "total": len(items)}

    def set_nombre(self, uid, nombre):
        for u in self.users.values():
            if u["id"] == uid:
                u["nombre"] = nombre
                return u
        return None

    def set_password(self, uid, pw_hash):
        for u in self.users.values():
            if u["id"] == uid:
                u["pw_hash"] = pw_hash
                u["failed"] = 0
                u["locked_until"] = 0
                return True
        return False

    def insert_session(self, user_id, thash, expira):
        self.sessions[thash] = {"user_id": user_id, "expira": expira}

    def find_session(self, thash):
        s = self.sessions.get(thash)
        if not s or s["expira"] < time.time():
            self.sessions.pop(thash, None)
            return None
        return s

    def delete_session(self, thash):
        self.sessions.pop(thash, None)


class MysqlAuthStore:
    """Persistencia real en nexo_app (ver sql/06_auth.sql)."""

    def __init__(self, cfg):
        self.cfg = cfg

    def _connect(self):
        try:
            import mysql.connector  # type: ignore
        except ImportError as e:
            raise RuntimeError("mysql-connector-python no está instalado.") from e
        c = self.cfg
        return mysql.connector.connect(host=c["host"], port=c["port"], user=c["user"],
                                       password=c["password"], database="nexo_app")

    def find_user(self, email):
        conn = self._connect()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT id, nombre, email, pw_hash, failed_attempts, locked_until, rol, estado, "
                        "creado_en FROM users WHERE email=%s", (email.lower(),))
            r = cur.fetchone()
            if not r:
                return None
            return {"id": r["id"], "nombre": r["nombre"], "email": r["email"],
                    "pw_hash": r["pw_hash"], "failed": r["failed_attempts"] or 0,
                    "locked_until": (r["locked_until"] or 0),
                    "rol": r.get("rol") or "operador", "estado": r.get("estado") or "activo",
                    "creado_en": str(r.get("creado_en") or "")}
        finally:
            conn.close()

    def insert_user(self, nombre, email, pw_hash):
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute("INSERT INTO users (nombre, email, pw_hash) VALUES (%s,%s,%s)",
                        (nombre, email.lower(), pw_hash))
            uid = cur.lastrowid
            conn.commit()
            return {"id": uid, "nombre": nombre, "email": email.lower(),
                    "pw_hash": pw_hash, "failed": 0, "locked_until": 0}
        finally:
            conn.close()

    def update_user(self, user):
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute("UPDATE users SET failed_attempts=%s, locked_until=%s WHERE id=%s",
                        (user["failed"], user["locked_until"], user["id"]))
            conn.commit()
        finally:
            conn.close()

    def set_estado(self, uid, estado):
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute("UPDATE users SET estado=%s WHERE id=%s", (estado, uid))
            ok = cur.rowcount == 1
            conn.commit()
            return ok
        finally:
            conn.close()

    def list_users(self, limit=20, offset=0):
        conn = self._connect()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT COUNT(*) AS total FROM users")
            total = cur.fetchone()["total"]
            cur.execute(
                "SELECT id, nombre, email, rol, estado, failed_attempts, locked_until, creado_en "
                "FROM users ORDER BY id LIMIT %s OFFSET %s", (limit, offset))
            items = [dict(r, creado_en=str(r.get("creado_en"))) for r in cur.fetchall()]
            return {"items": items, "total": total}
        finally:
            conn.close()

    def set_nombre(self, uid, nombre):
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute("UPDATE users SET nombre=%s WHERE id=%s", (nombre, uid))
            ok = cur.rowcount == 1
            conn.commit()
            return ok
        finally:
            conn.close()

    def set_password(self, uid, pw_hash):
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute("UPDATE users SET pw_hash=%s, failed_attempts=0, locked_until=0 WHERE id=%s",
                        (pw_hash, uid))
            ok = cur.rowcount == 1
            conn.commit()
            return ok
        finally:
            conn.close()

    def user_activity(self, uid, limit=10, offset=0):
        conn = self._connect()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT COUNT(*) AS total FROM decision_events WHERE decided_by=%s", (uid,))
            total = cur.fetchone()["total"]
            cur.execute(
                "SELECT de.accion, de.comentario, de.creado_en, f.tabla, f.columna, f.regla, f.run_id "
                "FROM decision_events de JOIN findings f ON f.id=de.finding_id "
                "WHERE de.decided_by=%s ORDER BY de.id DESC LIMIT %s OFFSET %s",
                (uid, limit, offset))
            items = [dict(r, creado_en=str(r.get("creado_en"))) for r in cur.fetchall()]
            return {"items": items, "total": total}
        finally:
            conn.close()

    def insert_session(self, user_id, thash, expira):
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute("INSERT INTO sessions (token_hash, user_id, expira) VALUES (%s,%s,FROM_UNIXTIME(%s))",
                        (thash, user_id, int(expira)))
            conn.commit()
        finally:
            conn.close()

    def find_session(self, thash):
        conn = self._connect()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT user_id, UNIX_TIMESTAMP(expira) AS expira FROM sessions WHERE token_hash=%s",
                        (thash,))
            r = cur.fetchone()
            if not r or (r["expira"] or 0) < time.time():
                cur2 = conn.cursor()
                cur2.execute("DELETE FROM sessions WHERE token_hash=%s", (thash,))
                conn.commit()
                return None
            return {"user_id": r["user_id"], "expira": r["expira"]}
        finally:
            conn.close()

    def get_user(self, uid):
        conn = self._connect()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT id, nombre, email, pw_hash, failed_attempts, locked_until, rol, estado, "
                        "creado_en FROM users WHERE id=%s", (uid,))
            r = cur.fetchone()
            if not r:
                return None
            return {"id": r["id"], "nombre": r["nombre"], "email": r["email"],
                    "pw_hash": r["pw_hash"], "failed": r["failed_attempts"] or 0,
                    "locked_until": (r["locked_until"] or 0),
                    "rol": r.get("rol") or "operador", "estado": r.get("estado") or "activo",
                    "creado_en": str(r.get("creado_en") or "")}
        finally:
            conn.close()

    def delete_session(self, thash):
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM sessions WHERE token_hash=%s", (thash,))
            conn.commit()
        finally:
            conn.close()


class AuthService:
    def __init__(self, store, runs_provider=None):
        self.store = store
        self.runs_provider = runs_provider or (lambda: [])

    @staticmethod
    def public(user):
        return {"id": user["id"], "nombre": user["nombre"], "email": user["email"],
                "rol": user.get("rol") or "operador"}

    @staticmethod
    def profile_data(user):
        return {"id": user["id"], "nombre": user["nombre"], "email": user["email"],
                "rol": user.get("rol") or "operador",
                "estado": user.get("estado") or "activo",
                "creado_en": str(user.get("creado_en") or "")}

    def user_public(self, uid):
        user = self.store.get_user(uid)
        if not user:
            raise AuthError("sesion_invalida", "Sesión vencida o inválida.")
        return self.public(user)

    def _new_session(self, user):
        token = new_session_token()
        self.store.insert_session(user["id"], token_hash(token), time.time() + SESSION_SECONDS)
        return token

    def register(self, nombre, email, password):
        nombre, err = validate_nombre(nombre)
        if err:
            raise AuthError("datos_invalidos", err)
        email, err = validate_email(email)
        if err:
            raise AuthError("datos_invalidos", err)
        err = validate_password(password)
        if err:
            raise AuthError("datos_invalidos", err)
        if self.store.find_user(email):
            raise AuthError("email_en_uso", "Ese correo ya está registrado. Prueba a iniciar sesión.")
        try:
            user = self.store.insert_user(nombre, email, hash_password(password))
        except Exception as e:
            if "1062" in str(e) or "uplicate" in str(e):
                raise AuthError("email_en_uso", "Ese correo ya está registrado. Prueba a iniciar sesión.") from e
            raise
        return user, self._new_session(user)

    def login(self, email, password):
        email, err = validate_email(email)
        if err:
            raise AuthError("credenciales_invalidas", "Correo o contraseña incorrectos.")
        if not password:
            raise AuthError("credenciales_invalidas", "Correo o contraseña incorrectos.")
        user = self.store.find_user(email)
        if user and user["locked_until"] > time.time():
            mins = int((user["locked_until"] - time.time()) // 60) + 1
            raise AuthError("cuenta_bloqueada",
                            f"Cuenta bloqueada por intentos fallidos. Intenta de nuevo en ~{mins} min.")
        ok = bool(user) and user.get("estado", "activo") == "activo" and check_password(password, user["pw_hash"])
        if not ok:
            if user:
                user["failed"] = user.get("failed", 0) + 1
                if user["failed"] >= MAX_ATTEMPTS:
                    user["locked_until"] = time.time() + LOCK_SECONDS
                self.store.update_user(user)
            raise AuthError("credenciales_invalidas", "Correo o contraseña incorrectos.")
        user["failed"] = 0
        user["locked_until"] = 0
        self.store.update_user(user)
        return user, self._new_session(user)

    def me(self, token):
        if not token:
            raise AuthError("sesion_invalida", "Sin sesión.")
        s = self.store.find_session(token_hash(token))
        if not s:
            raise AuthError("sesion_invalida", "Sesión vencida o inválida.")
        return s["user_id"]

    def logout(self, token):
        if token:
            self.store.delete_session(token_hash(token))

    def _admin(self, token):
        """Devuelve el usuario solo si es admin; si no, error 403."""
        uid = self.me(token)
        user = self.store.get_user(uid)
        if not user or user.get("rol") != "admin":
            raise AuthError("no_autorizado", "Se requiere rol de administrador.")
        return user

    @staticmethod
    def _page(limit, offset):
        try:
            limit = max(1, min(50, int(limit)))
        except (TypeError, ValueError):
            limit = 20
        try:
            offset = max(0, int(offset))
        except (TypeError, ValueError):
            offset = 0
        return limit, offset

    def admin_list(self, token, limit=20, offset=0):
        self._admin(token)
        limit, offset = self._page(limit, offset)
        if hasattr(self.store, "list_users"):
            return self.store.list_users(limit, offset)
        return {"items": [], "total": 0}

    def admin_estado(self, token, target_id, estado):
        admin = self._admin(token)
        if estado not in ("activo", "desactivada"):
            raise AuthError("datos_invalidos", "Estado inválido: usa activo o desactivada.")
        try:
            target_id = int(target_id)
        except (TypeError, ValueError):
            raise AuthError("datos_invalidos", "Usuario inválido.")
        if target_id == admin["id"]:
            raise AuthError("datos_invalidos", "No puedes cambiar tu propia cuenta.")
        if not self.store.set_estado(target_id, estado):
            raise AuthError("datos_invalidos", "Usuario no encontrado.")
        return True

    def admin_unlock(self, token, target_id):
        admin = self._admin(token)
        try:
            target_id = int(target_id)
        except (TypeError, ValueError):
            raise AuthError("datos_invalidos", "Usuario inválido.")
        user = self.store.get_user(target_id)
        if not user:
            raise AuthError("datos_invalidos", "Usuario no encontrado.")
        user["failed"] = 0
        user["locked_until"] = 0
        self.store.update_user(user)
        return True

    def admin_reset(self, token, target_id, nueva):
        admin = self._admin(token)
        try:
            target_id = int(target_id)
        except (TypeError, ValueError):
            raise AuthError("datos_invalidos", "Usuario inválido.")
        if target_id == admin["id"]:
            raise AuthError("datos_invalidos", "Cambia tu propia clave desde Mi perfil.")
        err = validate_password(nueva)
        if err:
            raise AuthError("datos_invalidos", err)
        if not self.store.set_password(target_id, hash_password(nueva)):
            raise AuthError("datos_invalidos", "Usuario no encontrado.")
        return True

    def profile(self, token):
        user = self.store.get_user(self.me(token))
        if not user:
            raise AuthError("sesion_invalida", "Sesión vencida o inválida.")
        return self.profile_data(user)

    def update_nombre(self, token, nombre):
        uid = self.me(token)
        nombre, err = validate_nombre(nombre)
        if err:
            raise AuthError("datos_invalidos", err)
        if not self.store.set_nombre(uid, nombre):
            raise AuthError("sesion_invalida", "Sesión vencida o inválida.")
        return self.profile_data(self.store.get_user(uid))

    def change_password(self, token, actual, nueva):
        uid = self.me(token)
        user = self.store.get_user(uid)
        if not user or not check_password(actual or "", user["pw_hash"]):
            raise AuthError("credenciales_invalidas", "La contraseña actual no es correcta.")
        err = validate_password(nueva)
        if err:
            raise AuthError("datos_invalidos", err)
        if not self.store.set_password(uid, hash_password(nueva)):
            raise AuthError("sesion_invalida", "Sesión vencida o inválida.")
        return True

    def activity(self, token, limit=10, offset=0):
        uid = self.me(token)
        try:
            limit = max(1, min(50, int(limit)))
        except (TypeError, ValueError):
            limit = 10
        try:
            offset = max(0, int(offset))
        except (TypeError, ValueError):
            offset = 0
        if hasattr(self.store, "user_activity"):
            return self.store.user_activity(uid, limit, offset)
        items = []
        for run in reversed(self.runs_provider()):
            for h in run.get("hallazgos", []):
                for ev in h.get("eventos", []):
                    por = ev.get("por") or {}
                    if por.get("id") == uid:
                        items.append({"accion": ev.get("accion"), "comentario": ev.get("comentario"),
                                      "creado_en": ev.get("creado_en"), "tabla": h.get("tabla"),
                                      "columna": h.get("columna"), "regla": h.get("regla"),
                                      "run_id": run.get("id")})
        return {"items": items[offset:offset + limit], "total": len(items)}
