-- NEXO · datos sintéticos (idempotente: conserva filas existentes).
USE nexo_source;

INSERT INTO clientes (row_id,id,nombre,email) VALUES
 ('cli-01','CLI-001','Lucía Fernández','lucia.fernandez@example.com'),
 ('cli-02','CLI-002','Marco Ruiz','marco.ruiz@example.com'),
 ('cli-03','CLI-003','Sofía Herrera',''),
 ('cli-04','CLI-004','Diego Torres','diego.torres@example.com'),
 ('cli-05','CLI-004','Diego Torres (duplicado)','d.torres2@example.com'),
 ('cli-06','CLI-006','   ','carlos.mendez@example.com'),
 ('cli-07','CLI-007','Ana Gómez','ana.gomez@'),
 ('cli-08','CLI-008','Juan Pérez','juan.perez[at]correo.com'),
 ('cli-09','CLI-009','Valeria Castro','valeria.castro@example.com'),
 ('cli-10','CLI-010','Pedro Sánchez','pedro.sanchez@example.com'),
 ('cli-11','CLI-011','Carmen Díaz','carmen.diaz@example.com'),
 ('cli-12','CLI-012','Raúl Ortega','raul.ortega@example.com')
ON DUPLICATE KEY UPDATE id=VALUES(id), nombre=VALUES(nombre), email=VALUES(email);

INSERT INTO pedidos (row_id,id,cliente_id,fecha,total) VALUES
 ('ped-01','PED-001','CLI-001','2026-01-10',150.50),
 ('ped-02','PED-002','CLI-002','2026-01-11',0),
 ('ped-03','PED-003','','2026-01-12',89.90),
 ('ped-04','PED-004','CLI-004','2026-01-13',210.00),
 ('ped-05','PED-005','CLI-007','2026-01-20',45.00),
 ('ped-06','PED-006','CLI-009','2026-02-01',320.75),
 ('ped-07','PED-007','CLI-010','2026-02-03',15.00),
 ('ped-08','PED-008','CLI-012','2026-02-05',99.99)
ON DUPLICATE KEY UPDATE id=VALUES(id), cliente_id=VALUES(cliente_id), fecha=VALUES(fecha), total=VALUES(total);

INSERT INTO productos (row_id,id,nombre,precio) VALUES
 ('pro-01','PRO-001','Café Molido 500g',85.50),
 ('pro-02','PRO-002','',120.00),
 ('pro-03','PRO-003','Taza Cerámica',45.00),
 ('pro-04','PRO-004','Filtro Papel x40',30.00),
 ('pro-05','PRO-005','Cafetera Prensa 1L',450.00),
 ('pro-06','PRO-006','Termo Acero 750ml',0)
ON DUPLICATE KEY UPDATE id=VALUES(id), nombre=VALUES(nombre), precio=VALUES(precio);
