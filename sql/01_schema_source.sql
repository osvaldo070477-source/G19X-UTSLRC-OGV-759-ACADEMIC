-- NEXO · base de origen (solo lectura para la app).
-- Importar desde el cliente mysql con:  source sql/01_schema_source.sql
CREATE DATABASE IF NOT EXISTS nexo_source CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE nexo_source;

CREATE TABLE IF NOT EXISTS clientes (
  row_id VARCHAR(16) PRIMARY KEY,
  id VARCHAR(16) NOT NULL COMMENT 'clave de negocio (puede duplicarse a propósito)',
  nombre VARCHAR(120) NOT NULL,
  email VARCHAR(160) NOT NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS pedidos (
  row_id VARCHAR(16) PRIMARY KEY,
  id VARCHAR(16) NOT NULL,
  cliente_id VARCHAR(16) NOT NULL,
  fecha DATE NOT NULL,
  total DECIMAL(10,2) NOT NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS productos (
  row_id VARCHAR(16) PRIMARY KEY,
  id VARCHAR(16) NOT NULL,
  nombre VARCHAR(120) NOT NULL,
  precio DECIMAL(10,2) NOT NULL
) ENGINE=InnoDB;
