-- NEXO · entidades agentic (migración: conserva todo lo existente).
-- No borra ni recrea bases; todo es CREATE TABLE IF NOT EXISTS.
-- Importar desde el cliente mysql con:  source sql/05_agentic.sql
USE nexo_app;

CREATE TABLE IF NOT EXISTS agent_jobs (
  id INT AUTO_INCREMENT PRIMARY KEY,
  estado VARCHAR(24) NOT NULL,
  modo_fuente VARCHAR(16) NOT NULL,
  proveedor VARCHAR(16) NOT NULL,
  modelo VARCHAR(80) NOT NULL,
  es_prueba TINYINT NOT NULL DEFAULT 0 COMMENT '1 = proveedor de prueba, no IA real',
  params_json VARCHAR(1000) NOT NULL,
  run_id INT NULL COMMENT 'análisis determinista del trabajo',
  uso_json VARCHAR(1000) NULL COMMENT 'consumo reportado por el proveedor',
  resumen_json VARCHAR(4000) NULL,
  codigo_error VARCHAR(32) NULL,
  error VARCHAR(500) NULL,
  creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  iniciado_en DATETIME NULL,
  terminado_en DATETIME NULL,
  INDEX (estado)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS agent_steps (
  id INT AUTO_INCREMENT PRIMARY KEY,
  job_id INT NOT NULL,
  etapa VARCHAR(32) NOT NULL,
  evento VARCHAR(32) NOT NULL,
  resumen VARCHAR(500) NULL,
  creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_step_job FOREIGN KEY (job_id) REFERENCES agent_jobs(id),
  INDEX (job_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS tool_calls (
  id INT AUTO_INCREMENT PRIMARY KEY,
  job_id INT NOT NULL,
  agente VARCHAR(32) NOT NULL,
  herramienta VARCHAR(48) NOT NULL,
  argumentos_json VARCHAR(2000) NOT NULL,
  ok TINYINT NOT NULL,
  resumen VARCHAR(1000) NULL,
  ms INT NOT NULL DEFAULT 0,
  creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_tool_job FOREIGN KEY (job_id) REFERENCES agent_jobs(id),
  INDEX (job_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS recommendations (
  id INT AUTO_INCREMENT PRIMARY KEY,
  job_id INT NOT NULL,
  tabla VARCHAR(32) NOT NULL,
  columna VARCHAR(64) NOT NULL,
  regla VARCHAR(16) NOT NULL,
  problema VARCHAR(500) NOT NULL,
  accion VARCHAR(500) NOT NULL COMMENT 'propuesta; aceptarla NO la ejecuta',
  prioridad VARCHAR(8) NOT NULL,
  justificacion VARCHAR(500) NOT NULL,
  limitaciones VARCHAR(500) NULL,
  revision_humana TINYINT NOT NULL DEFAULT 0,
  estado ENUM('pendiente','aceptada','descartada','reabierta') NOT NULL DEFAULT 'pendiente',
  creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_rec_job FOREIGN KEY (job_id) REFERENCES agent_jobs(id),
  INDEX (job_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS reviews (
  id INT AUTO_INCREMENT PRIMARY KEY,
  job_id INT NOT NULL,
  motivo VARCHAR(500) NOT NULL,
  contexto_json VARCHAR(4000) NULL,
  estado ENUM('pendiente','aprobada','rechazada') NOT NULL DEFAULT 'pendiente',
  comentario VARCHAR(1000) NULL,
  creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  respondido_en DATETIME NULL,
  CONSTRAINT fk_rev_job FOREIGN KEY (job_id) REFERENCES agent_jobs(id),
  INDEX (job_id)
) ENGINE=InnoDB;
