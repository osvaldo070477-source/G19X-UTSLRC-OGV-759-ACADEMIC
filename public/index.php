<?php
// Servir la misma interfaz cuando el proyecto se abre vía PHP.
// La detección del modo la hace app.js (si api.php responde => modo conectado).
declare(strict_types=1);
readfile(__DIR__ . '/index.html');
