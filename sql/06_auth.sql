-- NEXO · usuarios y sesiones locales (migración: conserva todo lo existente).
-- Importar desde el cliente mysql con:  source sql/06_auth.sql
USE nexo_app;

CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(60) NOT NULL,
  email VARCHAR(160) NOT NULL UNIQUE,
  pw_hash VARCHAR(255) NOT NULL COMMENT 'PBKDF2; jamás en texto claro',
  failed_attempts INT NOT NULL DEFAULT 0,
  locked_until BIGINT NOT NULL DEFAULT 0 COMMENT 'época Unix; 0 = sin bloqueo',
  creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS sessions (
  token_hash CHAR(64) PRIMARY KEY COMMENT 'SHA-256 del token; el token real no se guarda',
  user_id INT NOT NULL,
  expira DATETIME NOT NULL COMMENT 'validez de 8 horas',
  creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_ses_user FOREIGN KEY (user_id) REFERENCES users(id),
  INDEX (user_id)
) ENGINE=InnoDB;

-- Atribución opcional de decisiones (NULL = invitado). Si marca error 1060
-- (columna duplicada) es que ya estaba aplicada: ignóralo sin problema.
ALTER TABLE decision_events ADD COLUMN decided_by INT NULL COMMENT 'users.id o NULL';
