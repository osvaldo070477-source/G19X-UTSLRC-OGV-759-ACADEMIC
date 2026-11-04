-- NEXO · carga gobernada de datos y recuperación (migración conservadora).
-- Importar como administrador:  source sql/09_carga.sql
USE nexo_app;

-- Auditoría de filas agregadas manualmente a la fuente.
CREATE TABLE IF NOT EXISTS source_audit (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NULL,
  tabla VARCHAR(32) NOT NULL,
  row_id VARCHAR(16) NOT NULL,
  accion VARCHAR(16) NOT NULL DEFAULT 'insert',
  creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX (tabla), INDEX (user_id)
) ENGINE=InnoDB;

-- Metadatos editables del catálogo (por defecto, los del código).
CREATE TABLE IF NOT EXISTS asset_meta (
  tabla VARCHAR(32) PRIMARY KEY,
  nombre VARCHAR(80) NOT NULL,
  descripcion VARCHAR(500) NOT NULL,
  responsable VARCHAR(120) NOT NULL,
  dominio VARCHAR(40) NOT NULL
) ENGINE=InnoDB;

INSERT IGNORE INTO asset_meta (tabla, nombre, descripcion, responsable, dominio) VALUES
 ('clientes', 'Clientes', 'Personas registradas en la tienda de ejemplo. Base para segmentación y contacto.', 'Ana Beltrán — Dominio Comercial', 'Comercial'),
 ('pedidos', 'Pedidos', 'Compras realizadas por los clientes con fecha e importe total.', 'Luis Camargo — Dominio Ventas', 'Ventas'),
 ('productos', 'Productos', 'Catálogo de artículos disponibles para la venta.', 'María Solís — Dominio Catálogo', 'Catálogo');

-- Código de recuperación de un solo uso (hash; NULL cuando ya se usó).
ALTER TABLE users ADD COLUMN recovery_hash CHAR(64) NULL COMMENT 'SHA-256 del código; NULL = sin código vigente';

-- La cuenta de inserción nexo_wr se crea en sql/04_users_template.sql.
-- Su permiso sobre nexo_app.source_audit se concede en sql/07_permisos.sql,
-- que se ejecuta al final (después de crear esta tabla).
