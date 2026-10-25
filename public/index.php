<?php
// Servir la misma interfaz cuando el proyecto se abre vía PHP.
// La detección del modo la hace public/js/base.js (si api.php responde => modo conectado).
declare(strict_types=1);
// Sin caché: al editar la interfaz, el navegador siempre recibe la versión actual.
header('Content-Type: text/html; charset=utf-8');
header('Cache-Control: no-store');
header('X-Content-Type-Options: nosniff');
header('X-Frame-Options: DENY');
header('Referrer-Policy: no-referrer');
header("Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'");
readfile(__DIR__ . '/index.html');
