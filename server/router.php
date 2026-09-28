<?php
// Enrutador para: php -S 127.0.0.1:8000 server/router.php
// Sirve solo archivos de public/ y dirige /api* a public/api.php.
declare(strict_types=1);

$public = dirname(__DIR__) . '/public';
$uri = parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH) ?: '/';

if (str_starts_with($uri, '/api') || isset($_GET['action'])) {
    require $public . '/api.php';
    return;
}
if ($uri === '/' || $uri === '/index.php') {
    require $public . '/index.php';
    return;
}
$file = realpath($public . $uri);
if ($file !== false && str_starts_with($file, (string)realpath($public)) && is_file($file)) {
    $ext = strtolower(pathinfo($file, PATHINFO_EXTENSION));
    // Bloquear archivos privados aunque alguien los copie a public.
    if (in_array($ext, ['env', 'sql'], true) || basename($file) === '.env') {
        http_response_code(403);
        echo 'Prohibido.';
        return;
    }
    // El servidor se lanza desde la raíz; los estáticos se sirven aquí mismo.
    $mime = ['css' => 'text/css', 'js' => 'text/javascript', 'html' => 'text/html',
             'svg' => 'image/svg+xml', 'png' => 'image/png', 'ico' => 'image/x-icon',
             'json' => 'application/json'];
    if (!isset($mime[$ext])) {
        http_response_code(404);
        echo 'No encontrado.';
        return;
    }
    header('Content-Type: ' . $mime[$ext] . '; charset=utf-8');
    readfile($file);
    return;
}
http_response_code(404);
header('Content-Type: text/plain; charset=utf-8');
echo 'No encontrado.';
