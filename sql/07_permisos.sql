-- NEXO · permisos mínimos de la cuenta de aplicación (requiere root u otro admin).
-- Corrige el error 1142 en login: nexo_app necesita UPDATE en users y
-- sesiones, e INSERT/UPDATE según tabla. Nunca DDL ni acceso a mysql.*.
-- Ejecutar en el cliente mysql como administrador, una sola vez.
USE nexo_app;

-- Limpia concesiones previas para partir del mínimo exacto.
REVOKE ALL PRIVILEGES, GRANT OPTION FROM 'nexo_app'@'127.0.0.1';
REVOKE ALL PRIVILEGES, GRANT OPTION FROM 'nexo_app'@'localhost';

-- Cuentas: leer, crear y actualizar intentos/bloqueo (nunca borrar).
GRANT SELECT, INSERT, UPDATE ON nexo_app.users TO 'nexo_app'@'127.0.0.1';
GRANT SELECT, INSERT, UPDATE ON nexo_app.users TO 'nexo_app'@'localhost';

-- Sesiones: crear, leer y cerrar (borrar la propia fila al salir o expirar).
GRANT SELECT, INSERT, DELETE ON nexo_app.sessions TO 'nexo_app'@'127.0.0.1';
GRANT SELECT, INSERT, DELETE ON nexo_app.sessions TO 'nexo_app'@'localhost';

-- Resultados: solo registrar y leer (nunca modificar ni borrar historial).
GRANT SELECT, INSERT ON nexo_app.runs TO 'nexo_app'@'127.0.0.1';
GRANT SELECT, INSERT ON nexo_app.runs TO 'nexo_app'@'localhost';
GRANT SELECT, INSERT ON nexo_app.findings TO 'nexo_app'@'127.0.0.1';
GRANT SELECT, INSERT ON nexo_app.findings TO 'nexo_app'@'localhost';
GRANT SELECT, INSERT ON nexo_app.evidence TO 'nexo_app'@'127.0.0.1';
GRANT SELECT, INSERT ON nexo_app.evidence TO 'nexo_app'@'localhost';
GRANT SELECT, INSERT ON nexo_app.decision_events TO 'nexo_app'@'127.0.0.1';
GRANT SELECT, INSERT ON nexo_app.decision_events TO 'nexo_app'@'localhost';
GRANT SELECT, INSERT ON nexo_app.agent_steps TO 'nexo_app'@'127.0.0.1';
GRANT SELECT, INSERT ON nexo_app.agent_steps TO 'nexo_app'@'localhost';
GRANT SELECT, INSERT ON nexo_app.tool_calls TO 'nexo_app'@'127.0.0.1';
GRANT SELECT, INSERT ON nexo_app.tool_calls TO 'nexo_app'@'localhost';
GRANT SELECT, INSERT ON nexo_app.recommendations TO 'nexo_app'@'127.0.0.1';
GRANT SELECT, INSERT ON nexo_app.recommendations TO 'nexo_app'@'localhost';

-- Trabajos y revisiones: además actualizan su propio estado.
GRANT SELECT, INSERT, UPDATE ON nexo_app.agent_jobs TO 'nexo_app'@'127.0.0.1';
GRANT SELECT, INSERT, UPDATE ON nexo_app.agent_jobs TO 'nexo_app'@'localhost';
GRANT SELECT, INSERT, UPDATE ON nexo_app.reviews TO 'nexo_app'@'127.0.0.1';
GRANT SELECT, INSERT, UPDATE ON nexo_app.reviews TO 'nexo_app'@'localhost';

FLUSH PRIVILEGES;
SELECT 'Permisos mínimos aplicados a nexo_app.' AS resultado;
