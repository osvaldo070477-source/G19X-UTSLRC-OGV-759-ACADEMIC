"""Pruebas de autenticación local (biblioteca estándar: unittest).
Uso:  python tests/test_auth.py
Sin red ni MySQL: todo contra el almacén en memoria.
"""
import os
import sys
import time
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "backend"))

from auth import (AuthError, AuthService, MemoryAuthStore, check_password,  # noqa: E402
                  hash_password, validate_email, validate_nombre, validate_password)


def svc():
    return AuthService(MemoryAuthStore())


class TestValidaciones(unittest.TestCase):
    def test_nombre(self):
        self.assertEqual(validate_nombre("  Ana  Beltrán ")[0], "Ana Beltrán")
        _, err = validate_nombre("A")
        self.assertTrue(err)
        _, err = validate_nombre("Juan123")
        self.assertTrue(err)
        _, err = validate_nombre("<script>")
        self.assertTrue(err)

    def test_email(self):
        self.assertEqual(validate_email("  Ana@Ejemplo.COM ")[0], "ana@ejemplo.com")
        for malo in ["", "sin-arroba", "a@b", "a b@c.com", "x" * 155 + "@a.com"]:
            _, err = validate_email(malo)
            self.assertTrue(err, malo)

    def test_password(self):
        self.assertIsNone(validate_password("Segura123"))
        for mala in ["corta1A", "sinmayusculas1", "SINMINUSCULAS1", "SinNumeros"]:
            self.assertTrue(validate_password(mala), mala)

    def test_hash_no_reversible(self):
        h = hash_password("Secreta123")
        self.assertNotIn("Secreta123", h)
        self.assertTrue(check_password("Secreta123", h))
        self.assertFalse(check_password("secreta123", h))
        self.assertFalse(check_password("Secreta123", "basura"))


class TestServicio(unittest.TestCase):
    def test_registro_y_login(self):
        s = svc()
        user, token = s.register("Ana Beltrán", "ana@example.com", "Segura123")
        self.assertEqual(user["nombre"], "Ana Beltrán")
        self.assertEqual(user["rol"], "operador")
        self.assertTrue(token)
        user2, _ = s.login("ANA@example.com", "Segura123")
        self.assertEqual(user2["id"], user["id"])
        pub = s.user_public(user["id"])
        self.assertEqual(pub["email"], "ana@example.com")
        self.assertEqual(pub["rol"], "operador")
        self.assertNotIn("pw_hash", pub)

    def test_duplicado(self):
        s = svc()
        s.register("Ana", "ana@example.com", "Segura123")
        with self.assertRaises(AuthError) as c:
            s.register("Otra", "ANA@example.com", "Segura123")
        self.assertEqual(c.exception.code, "email_en_uso")

    def test_login_generico_y_bloqueo(self):
        s = svc()
        s.register("Ana", "ana@example.com", "Segura123")
        for _ in range(5):
            with self.assertRaises(AuthError) as c:
                s.login("ana@example.com", "Mal12345")
            self.assertEqual(c.exception.code, "credenciales_invalidas")
        with self.assertRaises(AuthError) as c:
            s.login("ana@example.com", "Segura123")
        self.assertEqual(c.exception.code, "cuenta_bloqueada")
        # correo inexistente: mismo mensaje genérico, sin bloqueo ajeno
        with self.assertRaises(AuthError) as c:
            s.login("nadie@example.com", "Mal12345")
        self.assertEqual(c.exception.code, "credenciales_invalidas")

    def test_sesion_expira_y_cierra(self):
        s = svc()
        user, token = s.register("Ana", "ana@example.com", "Segura123")
        self.assertEqual(s.me(token), user["id"])
        s.logout(token)
        with self.assertRaises(AuthError):
            s.me(token)
        with self.assertRaises(AuthError):
            s.me("inventado")

    def test_datos_invalidos(self):
        s = svc()
        with self.assertRaises(AuthError):
            s.register("A", "mal", "x")

    def test_perfil_y_cambio_nombre(self):
        s = svc()
        user, token = s.register("Ana Beltrán", "ana@example.com", "Segura123")
        p = s.profile(token)
        self.assertEqual(p["rol"], "operador")
        self.assertTrue(p["creado_en"])
        self.assertNotIn("pw_hash", p)
        p2 = s.update_nombre(token, "Ana María Beltrán")
        self.assertEqual(p2["nombre"], "Ana María Beltrán")
        self.assertEqual(p2["rol"], "operador")
        with self.assertRaises(AuthError):
            s.update_nombre(token, "X")

    def test_cambio_contrasena(self):
        s = svc()
        user, token = s.register("Ana", "ana@example.com", "Segura123")
        with self.assertRaises(AuthError) as c:
            s.change_password(token, "Mal12345", "Nueva1234")
        self.assertEqual(c.exception.code, "credenciales_invalidas")
        with self.assertRaises(AuthError):
            s.change_password(token, "Segura123", "corta")
        self.assertTrue(s.change_password(token, "Segura123", "Nueva1234"))
        user2, _ = s.login("ana@example.com", "Nueva1234")
        self.assertEqual(user2["id"], user["id"])
        with self.assertRaises(AuthError):
            s.login("ana@example.com", "Segura123")

    def test_cuenta_desactivada_no_entra(self):
        s = svc()
        user, _ = s.register("Ana", "ana@example.com", "Segura123")
        user["estado"] = "desactivada"
        with self.assertRaises(AuthError) as c:
            s.login("ana@example.com", "Segura123")
        self.assertEqual(c.exception.code, "credenciales_invalidas")

    def test_actividad_solo_propia(self):
        s = svc()
        a, ta = s.register("Ana", "ana@example.com", "Segura123")
        b, tb = s.register("Beto", "beto@example.com", "Segura123")
        s.runs_provider = lambda: [{"id": 7, "hallazgos": [
            {"tabla": "clientes", "columna": "email", "regla": "email", "eventos": [
                {"accion": "accept", "comentario": "ok", "creado_en": "2026-01-01",
                 "por": {"id": a["id"], "nombre": "Ana"}},
                {"accion": "discard", "comentario": "", "creado_en": "2026-01-02",
                 "por": {"id": b["id"], "nombre": "Beto"}}]}]}]
        act = s.activity(ta, limit=10, offset=0)
        self.assertEqual(act["total"], 1)
        self.assertEqual(act["items"][0]["run_id"], 7)
        self.assertEqual(s.activity(ta, limit=1, offset=5)["items"], [])
        actb = s.activity(tb, limit=10, offset=0)
        self.assertEqual(actb["items"][0]["accion"], "discard")


class TestAdmin(unittest.TestCase):
    def admin_svc(self):
        s = svc()
        a, ta = s.register("Admin Uno", "admin@example.com", "Admin1234")
        s.store.get_user(a["id"])["rol"] = "admin"
        u, tu = s.register("Usuaria Dos", "dos@example.com", "Usuaria1234")
        return s, ta, tu, u["id"]

    def test_no_admin_rechazado(self):
        s, ta, tu, uid = self.admin_svc()
        with self.assertRaises(AuthError) as c:
            s.admin_list(tu)
        self.assertEqual(c.exception.code, "no_autorizado")

    def test_list_sin_hashes(self):
        s, ta, tu, uid = self.admin_svc()
        res = s.admin_list(ta)
        self.assertEqual(res["total"], 2)
        for it in res["items"]:
            self.assertNotIn("pw_hash", it)
            self.assertIn("rol", it)

    def test_estado_y_autoproteccion(self):
        s, ta, tu, uid = self.admin_svc()
        self.assertTrue(s.admin_estado(ta, uid, "desactivada"))
        with self.assertRaises(AuthError):
            s.login("dos@example.com", "Usuaria1234")
        with self.assertRaises(AuthError) as c:
            s.admin_estado(ta, 1, "desactivada")
        self.assertEqual(c.exception.code, "datos_invalidos")
        with self.assertRaises(AuthError):
            s.admin_estado(ta, uid, "raro")

    def test_unlock_y_reset(self):
        s, ta, tu, uid = self.admin_svc()
        for _ in range(5):
            try:
                s.login("dos@example.com", "Mal12345")
            except AuthError:
                pass
        self.assertTrue(s.admin_unlock(ta, uid))
        u2, _ = s.login("dos@example.com", "Usuaria1234")
        self.assertEqual(u2["id"], uid)
        self.assertTrue(s.admin_reset(ta, uid, "Nueva1234"))
        u3, _ = s.login("dos@example.com", "Nueva1234")
        self.assertEqual(u3["id"], uid)
        with self.assertRaises(AuthError):
            s.admin_reset(ta, uid, "corta")
        with self.assertRaises(AuthError):
            s.admin_reset(tu, uid, "Otra1234")


class TestDDL(unittest.TestCase):
    def test_migracion_06(self):
        with open(os.path.join(BASE, "sql", "06_auth.sql"), encoding="utf-8") as f:
            sql = f.read()
        self.assertIn("CREATE TABLE IF NOT EXISTS users", sql)
        self.assertIn("CREATE TABLE IF NOT EXISTS sessions", sql)
        self.assertIn("decided_by", sql)
        upper = sql.upper()
        self.assertNotIn("DROP DATABASE", upper)
        self.assertNotIn("DROP TABLE", upper)


if __name__ == "__main__":
    unittest.main(verbosity=1)
