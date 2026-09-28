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
        self.assertTrue(token)
        user2, _ = s.login("ANA@example.com", "Segura123")
        self.assertEqual(user2["id"], user["id"])
        self.assertEqual(s.user_public(user["id"])["email"], "ana@example.com")

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
