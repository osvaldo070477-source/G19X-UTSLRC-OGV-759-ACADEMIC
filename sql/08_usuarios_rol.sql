-- NEXO · roles y estado de cuentas (migración: conserva cuentas y datos).
-- Si marca error 1060 (columna duplicada) es que ya estaba aplicada: ignóralo.
-- Importar desde el cliente mysql con:  source sql/08_usuarios_rol.sql
USE nexo_app;

ALTER TABLE users ADD COLUMN rol VARCHAR(16) NOT NULL DEFAULT 'operador'
  COMMENT 'rol inicial seguro; ningún formulario puede cambiarlo';
ALTER TABLE users ADD COLUMN estado VARCHAR(16) NOT NULL DEFAULT 'activo'
  COMMENT 'activo o desactivada; las desactivadas no entran';
ALTER TABLE users ADD COLUMN actualizado_en TIMESTAMP NOT NULL
  DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;

-- Las cuentas existentes quedan como operador activas.
UPDATE users SET rol='operador', estado='activo' WHERE rol='' OR estado='';
