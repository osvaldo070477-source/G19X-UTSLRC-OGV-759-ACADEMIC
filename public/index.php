<?php
// Servir la misma interfaz cuando el proyecto se abre vía PHP.
// La detección del modo la hace public/js/base.js (si api.php responde => modo conectado).
declare(strict_types=1);
// Sin caché: al editar la interfaz, el navegador siempre recibe la versión actual.
header('Cache-Control: no-store');
readfile(__DIR__ . '/index.html');
