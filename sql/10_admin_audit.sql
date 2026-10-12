-- NEXO · auditoría de acciones administrativas (migración conservadora).
-- Importar como administrador:  source sql/10_admin_audit.sql
USE nexo_app;

CREATE TABLE IF NOT EXISTS admin_audit (
  id INT AUTO_INCREMENT PRIMARY KEY,
  admin_id INT NOT NULL COMMENT 'quién ejecutó la acción',
  accion VARCHAR(32) NOT NULL COMMENT 'estado, desbloquear, reset_password, rol, meta',
  target_id INT NULL COMMENT 'usuario afectado (NULL en meta)',
  detalle VARCHAR(300) NULL COMMENT 'ej. estado=desactivada, tabla=clientes, rol=lector',
  creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX (admin_id), INDEX (creado_en)
) ENGINE=InnoDB;
