<?php
// Puerta de entrada PHP -> servicio Python. No expone secretos al navegador.
// La sesión de usuario vive en $_SESSION del servidor; el navegador solo
// recibe el perfil público (id, nombre, email), nunca el token de sesión.
declare(strict_types=1);
// Cookies de sesión solo HTTP (nunca JavaScript) y válidas en HTTP local:
// sin 'secure' para no romper el desarrollo en http://127.0.0.1.
if (session_status() === PHP_SESSION_NONE) {
    session_set_cookie_params(['httponly' => true, 'secure' => false, 'samesite' => 'Lax']);
    session_start();
}

function nexo_env(string $key, string $default = ''): string {
    static $env = null;
    if ($env === null) {
        $env = [];
        $path = dirname(__DIR__) . '/.env';
        if (is_readable($path)) {
            foreach (file($path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) as $line) {
                $line = trim($line);
                if ($line === '' || $line[0] === '#') continue;
                $pos = strpos($line, '=');
                if ($pos === false) continue;
                $k = trim(substr($line, 0, $pos));
                $v = trim(substr($line, $pos + 1), " \t\"'");
                if ($k !== '' && getenv($k) === false) $env[$k] = $v;
            }
        }
    }
    $val = getenv($key);
    if ($val !== false) return (string)$val;
    return $env[$key] ?? $default;
}

function nexo_len(string $s): int {
    if (function_exists('mb_strlen')) return mb_strlen($s, 'UTF-8');
    if (function_exists('preg_match_all')) {
        $n = preg_match_all('/./us', $s);
        if ($n !== false) return $n;
    }
    return strlen($s);
}
function nexo_out(int $code, array $data): void {
    http_response_code($code);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode($data, JSON_UNESCAPED_UNICODE);
    exit;
}

$token = nexo_env('NEXO_INTERNAL_TOKEN', '');
$pyBase = rtrim(nexo_env('NEXO_PY_URL', 'http://127.0.0.1:8001'), '/');
if ($token === '') {
    nexo_out(500, ['error' => 'Falta NEXO_INTERNAL_TOKEN. Ejecuta: python scripts/gen_env.py']);
}

$action = $_GET['action'] ?? '';
$method = $_SERVER['REQUEST_METHOD'] ?? 'GET';

// Escrituras solo desde el mismo origen (el fetch de nuestra página).
if (in_array($action, ['analyze', 'decisions', 'agent_start', 'agent_cancel', 'agent_review', 'agent_retry', 'auth_register', 'auth_login', 'auth_logout'], true)) {
    $origin = $_SERVER['HTTP_ORIGIN'] ?? '';
    $referer = $_SERVER['HTTP_REFERER'] ?? '';
    $host = $_SERVER['HTTP_HOST'] ?? '';
    if (($origin !== '' && strpos($origin, $host) === false) ||
        ($origin === '' && $referer !== '' && strpos($referer, $host) === false)) {
        nexo_out(403, ['error' => 'Origen no permitido para escritura.']);
    }
}

$routes = [
    'health'    => ['GET', '/api/health'],
    'catalog'   => ['GET', '/api/catalog'],
    'runs'      => ['GET', '/api/runs' . (!empty($_GET['limit']) ? '?limit=' . (int)$_GET['limit'] : '')],
    'run'       => ['GET', '/api/runs/' . (int)($_GET['id'] ?? 0)],
    'analyze'   => ['POST', '/api/analyze'],
    'decisions' => ['POST', '/api/decisions'],
    'agent_status' => ['GET', '/api/agent/status'],
    'agent_jobs'   => ['GET', '/api/agent/jobs' . (!empty($_GET['limit']) ? '?limit=' . (int)$_GET['limit'] : '')],
    'agent_job'    => ['GET', '/api/agent/jobs/' . (int)($_GET['id'] ?? 0)],
    'agent_start'  => ['POST', '/api/agent/jobs'],
    'agent_cancel' => ['POST', '/api/agent/jobs/' . (int)($_GET['id'] ?? 0) . '/cancel'],
    'agent_review' => ['POST', '/api/agent/jobs/' . (int)($_GET['id'] ?? 0) . '/review'],
    'agent_retry'  => ['POST', '/api/agent/jobs/' . (int)($_GET['id'] ?? 0) . '/retry'],
    'auth_register' => ['POST', '/api/auth/register'],
    'auth_login'    => ['POST', '/api/auth/login'],
    'auth_me'       => ['GET', '/api/auth/me'],
    'auth_logout'   => ['POST', '/api/auth/logout'],
];
if (!isset($routes[$action])) {
    nexo_out(404, ['error' => 'Acción desconocida.']);
}
[$expectMethod, $pyPath] = $routes[$action];
if ($method !== $expectMethod && !($action === 'health' && $method === 'GET')) {
    nexo_out(405, ['error' => 'Método no permitido.']);
}

$body = null;
if ($expectMethod === 'POST') {
    $raw = file_get_contents('php://input');
    $data = json_decode($raw ?: '{}', true);
    if (!is_array($data)) nexo_out(400, ['error' => 'Cuerpo JSON inválido.']);
    if ($action === 'decisions') {
        $valid = ['accept', 'discard', 'reopen'];
        if (!in_array($data['accion'] ?? '', $valid, true)) {
            nexo_out(400, ['error' => 'Acción inválida. Usa accept, discard o reopen.']);
        }
        $c = $data['comentario'] ?? '';
        if (!is_string($c) || nexo_len($c) > 1000) {
            nexo_out(400, ['error' => 'El comentario debe tener como máximo 1000 caracteres.']);
        }
        foreach (['run_id', 'tabla', 'columna', 'regla'] as $f) {
            if (empty($data[$f])) nexo_out(400, ['error' => "Falta el campo obligatorio: $f."]);
        }
    }
    if ($action === 'agent_start') {
        $f = $data['fuente'] ?? 'muestra';
        if (!in_array($f, ['muestra', 'origen'], true)) {
            nexo_out(400, ['error' => "Fuente inválida: usa muestra u origen."]);
        }
        $data = ['fuente' => $f, 'pedir_revision' => !empty($data['pedir_revision'])];
    }
    if ($action === 'agent_review') {
        if (!in_array($data['decision'] ?? '', ['approve', 'reject'], true)) {
            nexo_out(400, ['error' => 'Decisión inválida. Usa approve o reject.']);
        }
        $c = $data['comentario'] ?? '';
        if (!is_string($c) || nexo_len($c) > 1000) {
            nexo_out(400, ['error' => 'El comentario debe tener como máximo 1000 caracteres.']);
        }
    }
    if ($action === 'auth_register') {
        foreach (['nombre', 'email', 'password'] as $f) {
            if (!isset($data[$f]) || !is_string($data[$f]) || trim($data[$f]) === '') {
                nexo_out(400, ['error' => "Completa el campo: $f."]);
            }
        }
        if (strlen($data['password']) > 72) {
            nexo_out(400, ['error' => 'La contraseña es demasiado larga.']);
        }
        $data = ['nombre' => $data['nombre'], 'email' => $data['email'], 'password' => $data['password']];
    }
    if ($action === 'auth_login') {
        foreach (['email', 'password'] as $f) {
            if (!isset($data[$f]) || !is_string($data[$f]) || $data[$f] === '') {
                nexo_out(400, ['error' => 'Escribe tu correo y contraseña.']);
            }
        }
        $data = ['email' => $data['email'], 'password' => $data['password']];
    }
    if ($action === 'auth_logout') {
        $data = [];
    }
    $body = json_encode($data, JSON_UNESCAPED_UNICODE);

    $body = json_encode($data, JSON_UNESCAPED_UNICODE);
}

$headers = "Content-Type: application/json\r\nX-NEXO-Token: $token\r\n";
if (!empty($_SESSION['nexo_session'])) {
    $headers .= "X-NEXO-Session: " . $_SESSION['nexo_session'] . "\r\n";
}

$ctx = stream_context_create(['http' => [
    'method' => $expectMethod,
    'header' => $headers,
    'content' => $body,
    'timeout' => 20,
    'ignore_errors' => true,
]]);
$res = @file_get_contents($pyBase . $pyPath, false, $ctx);
if ($res === false) {
    nexo_out(502, ['error' => 'No se pudo contactar al servicio Python en ' . $pyBase .
        '. Inicia el servicio con la tarea “NEXO: servicio Python”.']);
}
$code = 200;
if (isset($http_response_header[0]) && preg_match('#\s(\d{3})\s#', $http_response_header[0], $m)) {
    $code = (int)$m[1];
}
// El token de sesión vive en el servidor: se guarda aquí y nunca sale al navegador.
// Al entrar se regenera el identificador de sesión (anti-fijación).
if (in_array($action, ['auth_register', 'auth_login'], true) && $code >= 200 && $code < 300) {
    $payload = json_decode($res, true);
    if (is_array($payload) && !empty($payload['session'])) {
        session_regenerate_id(true);
        $_SESSION['nexo_session'] = $payload['session'];
        $_SESSION['nexo_user'] = $payload['user'] ?? null;
        unset($payload['session']);
        $res = json_encode($payload, JSON_UNESCAPED_UNICODE);
    }
}
if ($action === 'auth_logout' || ($action === 'auth_me' && $code === 401)) {
    unset($_SESSION['nexo_session'], $_SESSION['nexo_user']);
}
http_response_code($code);
header('Content-Type: application/json; charset=utf-8');
echo $res;
