"""Pruebas de carga gobernada (puras, sin MySQL) y recuperación.
Uso:  python tests/test_carga.py
"""
import os
import sys
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "backend"))

from auth import AuthError, AuthService, MemoryAuthStore  # noqa: E402
from carga import MAX_IMPORT_BATCH, parse_csv, preview_rows, validate_row  # noqa: E402


class TestValidacion(unittest.TestCase):
    def test_rechaza_tabla_y_columnas(self):
        _, e1 = validate_row("usuarios", {}, set())
        _, e2 = validate_row("clientes", {"id": "X", "nombre": "A", "email": "a@b.co", "clave": 1}, set())
        self.assertTrue(e1 and e2)

    def test_requeridos_email_numero_fecha(self):
        _, e1 = validate_row("clientes", {"id": "X", "nombre": "", "email": "a@b.co"}, set())
        _, e2 = validate_row("clientes", {"id": "X", "nombre": "A", "email": "mal"}, set())
        _, e3 = validate_row("pedidos", {"id": "P", "cliente_id": "C", "fecha": "2026-01-01", "total": "abc"}, set())
        _, e4 = validate_row("pedidos", {"id": "P", "cliente_id": "C", "fecha": "01/01/2026", "total": 1}, set())
        self.assertTrue(e1 and e2 and e3 and e4)
        ok, err = validate_row("productos", {"id": "P1", "nombre": "Taza", "precio": "45.5"}, set())
        self.assertIsNone(err)
        self.assertEqual(ok["precio"], 45.5)

    def test_duplicado_contra_existentes_y_lote(self):
        _, e1 = validate_row("clientes", {"id": "CLI-001", "nombre": "A", "email": "a@b.co"}, {"CLI-001"})
        vistos = set()
        validate_row("clientes", {"id": "X", "nombre": "A", "email": "a@b.co"}, vistos)
        _, e2 = validate_row("clientes", {"id": "X", "nombre": "B", "email": "b@b.co"}, vistos)
        self.assertTrue(e1 and e2)


class TestCSV(unittest.TestCase):
    def test_parse_y_preview(self):
        texto = "id,nombre,email\nA1,Ana,a@b.co\nA2,,mal\n\nA1,Otra,o@b.co\n"
        filas, err = parse_csv(texto)
        self.assertIsNone(err)
        self.assertEqual(len(filas), 3)  # ignora la vacía
        res = preview_rows("clientes", filas, set())
        self.assertEqual(len(res["validas"]), 1)
        self.assertEqual(len(res["rechazadas"]), 2)

    def test_csv_vacio_y_limite(self):
        filas, err = parse_csv("id,nombre\n")
        self.assertTrue(err or filas == [])
        grande = "id,nombre,email\n" + "\n".join(f"X{i},A,a{i}@b.co" for i in range(MAX_IMPORT_BATCH + 1))
        _, err = parse_csv(grande)
        self.assertTrue(err)


class TestRecuperacion(unittest.TestCase):
    def test_flujo_completo(self):
        s = AuthService(MemoryAuthStore())
        user, _ = s.register("Ana", "ana@example.com", "Segura123")
        # el registro emite código (devuelto por issue_recovery)
        codigo = s.issue_recovery(user["id"])
        self.assertEqual(len(codigo), 12)
        user2 = s.recover("ana@example.com", codigo, "Nueva1234")
        self.assertEqual(user2["id"], user["id"])
        u3, _ = s.login("ana@example.com", "Nueva1234")
        self.assertEqual(u3["id"], user["id"])
        # un solo uso
        with self.assertRaises(AuthError):
            s.recover("ana@example.com", codigo, "Otra1234")

    def test_codigo_malo(self):
        s = AuthService(MemoryAuthStore())
        s.register("Ana", "ana@example.com", "Segura123")
        with self.assertRaises(AuthError):
            s.recover("ana@example.com", "incorrecto123", "Nueva1234")
        with self.assertRaises(AuthError):
            s.recover("nadie@example.com", "loquesea1234", "Nueva1234")


if __name__ == "__main__":
    unittest.main(verbosity=1)
