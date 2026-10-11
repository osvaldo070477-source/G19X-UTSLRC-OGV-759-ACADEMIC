# Registro de implementación — NEXO

Evidencia del trabajo realizado en diseño de interfaces y programación.

## 1. Diseño de interfaces
- Portada de bienvenida separada de la aplicación.
- Barra lateral compacta flotante con navegación e indicador de entorno.
- Barra superior con título de sección y menú de usuario.
- Tema oscuro tipo panel (azul medianoche, turquesa, dorado).
- Observatorio con saludo personalizado, estadísticas e índice de calidad.
- Catálogo con filtros alineados y tarjetas por activo.
- Tablas de calidad, decisiones y bitácora con estados y evidencias.
- Centro de agentes con progreso por etapas y revisión humana.
- Página de perfil con cabecera, pestañas y actividad.
- Modales de acceso, validación junto a campos y mostrar/ocultar contraseña.
- Diseño adaptable a computadora y celular, operable por teclado.

## 2. Programación del acceso (login)
- Registro con validaciones en cliente y servidor.
- Hash PBKDF2, bloqueo tras 5 intentos, sesiones opacas de 8 h.
- Corrección del error 1142 con permisos mínimos por tabla.
- Token CSRF en escrituras, cookies HttpOnly, regeneración de sesión.
- Cambio de nombre y contraseña, actividad propia, rol admin con panel.

## 3. Motor y datos
- Reglas deterministas idénticas en Python y JavaScript.
- Muestra ampliada: 44 registros, 208 comprobaciones, índice 90.
- Persistencia MySQL en dos bases con cuentas limitadas.

## 4. Agentes con IA
- Proveedor desacoplado OpenAI-compatible + stub de prueba.
- Orquestador, 9 herramientas autorizadas y revisión humana.
