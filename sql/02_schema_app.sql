-- NEXO · base de aplicación (resultados y decisiones).
-- Importar desde el cliente mysql con:  source sql/02_schema_app.sql
CREATE DATABASE IF NOT EXISTS nexo_app CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE nexo_app;

CREATE TABLE IF NOT EXISTS runs (
  id INT AUTO_INCREMENT PRIMARY KEY,
  modo VARCHAR(16) NOT NULL,
  creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  total_registros INT NOT NULL,
  comprobaciones INT NOT NULL,
  incidencias INT NOT NULL,
  indice INT NULL COMMENT 'NULL = sin evaluar',
  hallazgos INT NOT NULL,
  INDEX (creado_en)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS findings (
  id INT AUTO_INCREMENT PRIMARY KEY,
  run_id INT NOT NULL,
  tabla VARCHAR(32) NOT NULL,
  columna VARCHAR(64) NOT NULL,
  regla VARCHAR(16) NOT NULL,
  prioridad VARCHAR(8) NOT NULL,
  incidencias INT NOT NULL,
  recomendacion VARCHAR(500) NOT NULL,
  CONSTRAINT fk_find_run FOREIGN KEY (run_id) REFERENCES runs(id),
  INDEX (run_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS evidence (
  id INT AUTO_INCREMENT PRIMARY KEY,
  finding_id INT NOT NULL,
  row_id VARCHAR(16) NOT NULL,
  valor VARCHAR(200) NULL,
  ref VARCHAR(64) NOT NULL,
  CONSTRAINT fk_ev_find FOREIGN KEY (finding_id) REFERENCES findings(id),
  INDEX (finding_id)
) ENGINE=InnoDB;

-- Eventos acumulativos: jamás se sobrescriben; el estado vigente es el último.
CREATE TABLE IF NOT EXISTS decision_events (
  id INT AUTO_INCREMENT PRIMARY KEY,
  finding_id INT NOT NULL,
  accion ENUM('accept','discard','reopen') NOT NULL,
  comentario VARCHAR(1000) NULL,
  creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_dec_find FOREIGN KEY (finding_id) REFERENCES findings(id),
  INDEX (finding_id)
) ENGINE=InnoDB;
