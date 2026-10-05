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
            cur.execute("SELECT id, nombre, email, pw_hash, failed_attempts, locked_until, rol, estado "
                        "FROM users WHERE email=%s", (email.lower(),))
            r = cur.fetchone()
            if not r:
                return None
            return {"id": r["id"], "nombre": r["nombre"], "email": r["email"],
                    "pw_hash": r["pw_hash"], "failed": r["failed_attempts"] or 0,
                    "locked_until": (r["locked_until"] or 0),
                    "rol": r.get("rol") or "operador", "estado": r.get("estado") or "activo"}
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
            cur.execute("SELECT id, nombre, email, pw_hash, failed_attempts, locked_until, rol, estado "
                        "FROM users WHERE id=%s", (uid,))
            r = cur.fetchone()
            if not r:
                return None
            return {"id": r["id"], "nombre": r["nombre"], "email": r["email"],
                    "pw_hash": r["pw_hash"], "failed": r["failed_attempts"] or 0,
                    "locked_until": (r["locked_until"] or 0),
                    "rol": r.get("rol") or "operador", "estado": r.get("estado") or "activo"}
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
    def __init__(self, store):
        self.store = store

    @staticmethod
    def public(user):
        return {"id": user["id"], "nombre": user["nombre"], "email": user["email"],
                "rol": user.get("rol") or "operador"}

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
