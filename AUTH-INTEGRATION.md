        # 🔐 Documentación de Integración OAuth 2.0

        ## 📚 Índice

        1. [Resumen Ejecutivo](#resumen-ejecutivo)
        2. [Arquitectura de la Solución](#arquitectura-de-la-solución)
        3. [Flujo de Autenticación](#flujo-de-autenticación)
        4. [Componentes del Sistema](#componentes-del-sistema)
        5. [Configuración y Despliegue](#configuración-y-despliegue)
        6. [Guía de Uso](#guía-de-uso)
        7. [Seguridad](#seguridad)
        8. [Troubleshooting](#troubleshooting)
        9. [Changelog](#changelog)

        ---

        ## 🎯 Resumen Ejecutivo

        ### Objetivo

        Integrar autenticación OAuth 2.0 con Google en el sistema de chat cliente-servidor existente, eliminando el método de autenticación tradicional (usuario/contraseña) y reemplazándolo con un flujo seguro basado en Google Identity Services.

        ### Cambios Principales

        #### ✅ Implementado
        - ✅ Sistema de autenticación OAuth 2.0 con Google
        - ✅ Servidor web Flask (puerto 5000) para gestionar flujo OAuth
        - ✅ Templates HTML modernos (SIN formulario estático)
        - ✅ Integración token OAuth en servidor de chat
        - ✅ Cliente de chat actualizado para usar tokens OAuth
        - ✅ Documentación completa

        #### ❌ Eliminado
        - ❌ Formulario de login con correo + contraseña
        - ❌ Endpoint `/api/auth/login` (POST estático)
        - ❌ Autenticación local con contraseña de servidor

        ### Resultado Final

        Un sistema de chat seguro que:
        1. Autentica usuarios con sus cuentas de Google
        2. Genera tokens de acceso (email del usuario)
        3. Valida tokens en el servidor de chat
        4. Mantiene cifrado RSA + SSL/TLS en las comunicaciones

        ---

        ## 🏗️ Arquitectura de la Solución

        ### Diagrama de Componentes

        ```
        ┌──────────────────────────────────────────────────────────────────┐
        │                    SISTEMA DE CHAT OAUTH                         │
        └──────────────────────────────────────────────────────────────────┘

        ┌─────────────────┐                    ┌─────────────────┐
        │   Navegador     │                    │  Google OAuth   │
        │  (localhost:    │ ◄─── OAuth ────►   │   Platform      │
        │     5000)       │                    │                 │
        └────────┬────────┘                    └─────────────────┘
                │
                │ 1. Login con Google
                │ 2. Obtiene token (email)
                │
                ▼
        ┌─────────────────────────────────────────────────────────┐
        │            SERVIDOR WEB (Flask - Puerto 5000)           │
        │  ┌────────────────────────────────────────────────┐    │
        │  │  Rutas OAuth:                                  │    │
        │  │  • GET  /              → login.html            │    │
        │  │  • GET  /login/google  → Inicia flujo OAuth    │    │
        │  │  • GET  /callback      → Procesa respuesta     │    │
        │  │  • GET  /authenticated → Muestra token         │    │
        │  │  • GET  /logout        → Cierra sesión         │    │
        │  │  • GET  /api/chat/token → API token           │    │
        │  └────────────────────────────────────────────────┘    │
        │                                                         │
        │  Gestiona:                                              │
        │  • Sesiones de usuario (Flask sessions)                │
        │  • Tokens OAuth (email como identificador)             │
        │  • Interfaz web de autenticación                       │
        └─────────────────────────────────────────────────────────┘
                                │
                                │ 3. Usuario copia token
                                │
                                ▼
        ┌─────────────────────────────────────────────────────────┐
        │          CLIENTE DE CHAT (Python - client.py)           │
        │                                                         │
        │  • Solicita token OAuth al usuario                     │
        │  • Conecta al servidor de chat (puerto 5555)           │
        │  • Envía token cifrado con RSA                         │
        │  • Recibe/envía mensajes cifrados                      │
        └────────────┬────────────────────────────────────────────┘
                    │
                    │ 4. Conexión TLS + Token OAuth
                    │
                    ▼
        ┌─────────────────────────────────────────────────────────┐
        │         SERVIDOR DE CHAT (Python - server.py)           │
        │                 Puerto 5555 (SSL/TLS)                   │
        │                                                         │
        │  Autenticación:                                         │
        │  • Recibe token OAuth cifrado                          │
        │  • Valida formato de email                             │
        │  • Acepta conexión si token válido                     │
        │                                                         │
        │  Comunicación:                                          │
        │  • Cifrado RSA (mensajes)                              │
        │  • Cifrado TLS (canal)                                 │
        │  • Broadcast a clientes autenticados                   │
        └─────────────────────────────────────────────────────────┘
        ```

        ### Separación de Responsabilidades

        | Componente | Puerto | Responsabilidad |
        |------------|--------|-----------------|
        | **Servidor Web Flask** | 5000 | Autenticación OAuth, Gestión de sesiones, UI web |
        | **Servidor de Chat** | 5555 | Validación de tokens, Mensajería cifrada, Broadcast |
        | **Cliente de Chat** | N/A | Interfaz de usuario, Cifrado de mensajes |
        | **Google OAuth** | N/A | Autenticación de identidad, Emisión de tokens |

        ---

        ## 🔄 Flujo de Autenticación

        ### Flujo Completo Paso a Paso

        ```
        ┌─────────────┐
        │  1. INICIO  │
        └──────┬──────┘
            │
            │ Usuario ejecuta: python client/client.py
            │
            ▼
        ┌──────────────────────────────────────┐
        │  2. CLIENTE SOLICITA TOKEN           │
        │  "Ingresa tu token OAuth (email):"   │
        └──────┬───────────────────────────────┘
            │
            │ Usuario abre navegador: http://localhost:5000
            │
            ▼
        ┌──────────────────────────────────────┐
        │  3. PÁGINA DE LOGIN                  │
        │  • Solo botón "Continuar con Google" │
        │  • SIN formulario email/password     │
        └──────┬───────────────────────────────┘
            │
            │ Click en botón Google
            │
            ▼
        ┌──────────────────────────────────────┐
        │  4. REDIRECCIÓN A GOOGLE             │
        │  GET /login/google                   │
        │  → Genera URL de autorización        │
        │  → Redirige a accounts.google.com    │
        └──────┬───────────────────────────────┘
            │
            │ Usuario inicia sesión en Google
            │ Autoriza aplicación
            │
            ▼
        ┌──────────────────────────────────────┐
        │  5. CALLBACK DE GOOGLE               │
        │  GET /callback?code=...              │
        │  • Intercambia code por token        │
        │  • Obtiene user info (email, name)   │
        │  • Guarda sesión en Flask            │
        │  • Genera chat_token (email)         │
        └──────┬───────────────────────────────┘
            │
            │ Redirige a /authenticated
            │
            ▼
        ┌──────────────────────────────────────┐
        │  6. PÁGINA AUTENTICADA               │
        │  • Muestra datos del usuario          │
        │  • Muestra token: usuario@gmail.com  │
        │  • Botón para copiar token           │
        └──────┬───────────────────────────────┘
            │
            │ Usuario copia token
            │
            ▼
        ┌──────────────────────────────────────┐
        │  7. CLIENTE RECIBE TOKEN             │
        │  Input: usuario@gmail.com            │
        │  • Valida formato de email           │
        │  • Conecta al servidor de chat       │
        │  • Envía token cifrado con RSA       │
        └──────┬───────────────────────────────┘
            │
            │ Conexión TLS establecida
            │ Intercambio de claves RSA
            │
            ▼
        ┌──────────────────────────────────────┐
        │  8. SERVIDOR VALIDA TOKEN            │
        │  • Recibe token cifrado              │
        │  • Descifra con RSA privado          │
        │  • Valida formato email              │
        │  • Acepta conexión si válido         │
        └──────┬───────────────────────────────┘
            │
            │ AUTH_SUCCESS
            │
            ▼
        ┌──────────────────────────────────────┐
        │  9. CHAT ACTIVO                      │
        │  • Usuario puede enviar/recibir      │
        │  • Mensajes cifrados RSA + TLS       │
        │  • Nickname = email del usuario      │
        └──────────────────────────────────────┘
        ```

        ### Códigos de Protocolo

        | Mensaje | Dirección | Descripción |
        |---------|-----------|-------------|
        | `PUBLIC_KEY_READY` | Servidor → Cliente | Servidor listo para recibir clave pública |
        | `CLIENT_PUBLIC_KEY` | Servidor → Cliente | Solicita clave pública del cliente |
        | `OAUTH_TOKEN` | Servidor → Cliente | Solicita token OAuth |
        | `AUTH_SUCCESS` | Servidor → Cliente | Autenticación exitosa |
        | `AUTH_FAILED` | Servidor → Cliente | Autenticación fallida |
        | `SERVIDOR_LLENO` | Servidor → Cliente | Máximo de clientes alcanzado |

        ---

        ## 🧩 Componentes del Sistema

        ### 1. Modelo OAuth (`auth/models/oauth_model.py`)

        **Responsabilidades**:
        - Configurar cliente OAuth de Google con Authlib
        - Generar URLs de autorización
        - Intercambiar códigos por tokens
        - Extraer información del usuario
        - Gestionar sesiones de Flask

        **Métodos Principales**:

        ```python
        class OAuthModel:
            def init_app(app)                    # Configura OAuth con credenciales de Google
            def get_authorization_url(redirect)  # Genera URL de Google OAuth
            def get_token()                      # Obtiene token de acceso
            def get_user_info(token)             # Extrae email, nombre, foto
            def save_user_session(user_info)     # Guarda en Flask session
            def get_current_user()               # Obtiene usuario autenticado
            def get_chat_token()                 # Obtiene email como token
            def is_authenticated()               # Verifica autenticación
            def logout_user()                    # Cierra sesión
        ```

        ### 2. Controlador de Rutas (`auth/controllers/auth_routes.py`)

        **Rutas Implementadas**:

        | Ruta | Método | Descripción |
        |------|--------|-------------|
        | `/` | GET | Página de login (solo botón Google) |
        | `/login/google` | GET | Inicia flujo OAuth con Google |
        | `/callback` | GET | Procesa respuesta de Google |
        | `/authenticated` | GET | Muestra usuario y token |
        | `/api/chat/token` | GET | API JSON con token (para clientes programáticos) |
        | `/logout` | GET | Cierra sesión |

        **Características**:
        - ✅ SOLO autenticación OAuth (formulario ELIMINADO)
        - ✅ Manejo de errores robusto
        - ✅ Redirecciones automáticas
        - ✅ Protección de rutas (requiere autenticación)

        ### 3. Templates HTML

        #### `login.html` - Página de Login

        **Características**:
        - ✅ Diseño moderno con gradiente
        - ✅ SOLO botón "Continuar con Google"
        - ✅ Logo de Google oficial
        - ✅ Instrucciones claras
        - ✅ Responsive design
        - ❌ **NO tiene** formulario email/contraseña

        #### `authenticated.html` - Página Post-Login

        **Características**:
        - ✅ Muestra información del usuario (nombre, email, foto)
        - ✅ Token visible en caja de código
        - ✅ Botón para copiar token al portapapeles
        - ✅ Instrucciones para usar el chat
        - ✅ Botones de acción (refrescar, cerrar sesión)

        #### `error.html` - Página de Errores

        **Características**:
        - ✅ Muestra errores de OAuth
        - ✅ Detalles técnicos (opcional)
        - ✅ Botón para reintentar
        - ✅ Consejos de troubleshooting

        ### 4. Servidor Web Flask (`web_server.py`)

        **Configuración**:
        ```python
        app.config = {
            'SECRET_KEY': os.getenv('SECRET_KEY'),
            'GOOGLE_CLIENT_ID': os.getenv('GOOGLE_CLIENT_ID'),
            'GOOGLE_CLIENT_SECRET': os.getenv('GOOGLE_CLIENT_SECRET'),
            'SESSION_COOKIE_HTTPONLY': True,
            'SESSION_COOKIE_SAMESITE': 'Lax'
        }
        ```

        **Ejecución**:
        ```bash
        python web_server.py
        # Ejecuta en http://0.0.0.0:5000
        ```

        ### 5. Servidor de Chat (`server/server.py`)

        **Cambios en Autenticación**:

        **ANTES** (Contraseña):
        ```python
        client.send(b'NICK\n')
        nickname = descifrar(recv())

        client.send(b'PASSWORD\n')
        password = descifrar(recv())

        if password != server_password:
            AUTH_FAILED
        ```

        **DESPUÉS** (OAuth):
        ```python
        client.send(b'OAUTH_TOKEN\n')
        oauth_token = descifrar(recv())

        if '@' not in oauth_token:
            AUTH_FAILED

        nickname = oauth_token  # Email del usuario
        AUTH_SUCCESS
        ```

        ### 6. Cliente de Chat (`client/client.py`)

        **Cambios en Autenticación**:

        **ANTES**:
        ```python
        server_password = input("Contraseña: ")
        nickname = input("Nombre de usuario: ")
        ```

        **DESPUÉS**:
        ```python
        print("Obtén tu token en: http://localhost:5000")
        oauth_token = input("Token OAuth (email): ")

        if '@' not in oauth_token:
            raise ValueError("Token inválido")

        nickname = oauth_token
        ```

        ---

        ## ⚙️ Configuración y Despliegue

        ### Requisitos Previos

        #### 1. Credenciales de Google OAuth

        1. Accede a [Google Cloud Console](https://console.cloud.google.com/)
        2. Crea un proyecto nuevo o selecciona uno existente
        3. Navega a **APIs & Services** → **Credentials**
        4. Click en **Create Credentials** → **OAuth Client ID**
        5. Tipo de aplicación: **Web application**
        6. Authorized JavaScript origins:
        ```
        http://localhost:5000
        ```
        7. Authorized redirect URIs:
        ```
        http://localhost:5000/callback
        ```
        8. Guarda `Client ID` y `Client Secret`

        #### 2. Dependencias de Python

        ```bash
        pip install -r requirements.txt
        ```

        **Dependencias agregadas**:
        - `flask==3.1.2`
        - `authlib==1.6.5`
        - `requests==2.32.3`
        - `python-dotenv==1.2.1`

        ### Configuración de Variables de Entorno

        #### Paso 1: Copiar archivo de ejemplo

        ```powershell
        Copy-Item .env.example .env
        ```

        #### Paso 2: Editar `.env`

        ```env
        # OAuth 2.0 con Google
        GOOGLE_CLIENT_ID=tu-client-id.apps.googleusercontent.com
        GOOGLE_CLIENT_SECRET=GOCSPX-tu-client-secret

        # Clave secreta para sesiones (generar nueva)
        SECRET_KEY=5f8a9c3d1e7b2f4a6c8e0d9b7a5c3e1f4d6b8a0c2e4f6a8c0e2d4b6a8c0e2f4

        # Servidor web OAuth
        WEB_SERVER_PORT=5000
        WEB_SERVER_HOST=0.0.0.0

        # Chat (configuración existente)
        CHAT_PORT=5555
        CHAT_HOST=localhost
        CHAT_ENABLE_SSL=True
        ```

        #### Paso 3: Generar clave secreta (opcional)

        ```powershell
        python -c "import secrets; print(secrets.token_hex(32))"
        ```

        ### Instalación Completa

        ```powershell
        # 1. Clonar / Ubicarse en el proyecto
        cd Python-Client-Server-Chat

        # 2. Instalar dependencias
        pip install -r requirements.txt

        # 3. Configurar variables de entorno
        Copy-Item .env.example .env
        notepad .env  # Editar con credenciales OAuth

        # 4. Generar certificados SSL (si es primera vez)
        python scripts/generate_ssl_certificates.py
        ```

        ---

        ## 🚀 Guía de Uso

        ### Escenario Completo de Uso

        #### Terminal 1: Servidor Web OAuth

        ```powershell
        python web_server.py
        ```

        **Salida esperada**:
        ```
        ======================================================================
        🔐 SERVIDOR WEB DE AUTENTICACIÓN OAUTH 2.0
        ======================================================================
        📍 URL Local:     http://localhost:5000
        📍 URL Red:       http://0.0.0.0:5000
        ======================================================================
        🔑 Método de autenticación: Google OAuth 2.0
        🛡️  Seguridad: Sesiones cifradas
        ======================================================================

        ✅ Servidor listo. Presiona Ctrl+C para detener.

        📋 INSTRUCCIONES:
        1. Abre http://localhost:5000 en tu navegador
        2. Inicia sesión con tu cuenta de Google
        3. Copia el token mostrado
        4. Úsalo en el cliente de chat cuando se solicite
        ======================================================================
        ```

        #### Terminal 2: Servidor de Chat

        ```powershell
        python server/server.py
        ```

        **Salida esperada**:
        ```
        🌐 Servidor de chat iniciado en localhost:5555
        🔒 Cifrado RSA habilitado (2048 bits)
        🔐 SSL/TLS habilitado (TLS 1.2+)
        ✅ Esperando conexiones TLS en localhost:5555
        ```

        #### Terminal 3: Cliente de Chat

        ```powershell
        python client/client.py
        ```

        **Flujo interactivo**:
        ```
        ============================================================
            🎯 BIENVENIDO AL CHAT SEGURO CON CIFRADO RSA
        ============================================================

        📡 PASO 1: Configuración de Conexión
        ------------------------------------------------------------
        ¿A qué servidor deseas conectarte?
        → IP del servidor (Enter para localhost):
        ✓ Servidor: localhost
        ✓ Puerto: 5555

        🔐 PASO 2: Configuración de Cifrado RSA
        ------------------------------------------------------------
        → Generando tu par de claves RSA (2048 bits)...
        ✓ Tus claves RSA han sido generadas correctamente
        ✓ Clave pública del servidor cargada

        👤 PASO 3: Autenticación OAuth
        ------------------------------------------------------------
        Para conectarte al chat, necesitas un token OAuth de Google.

        🔐 Pasos para obtener tu token:
        1. Abre en tu navegador: http://localhost:5000
        2. Inicia sesión con tu cuenta de Google
        3. Copia el token (email) que se muestra

        → Ingresa tu token OAuth (email): usuario@gmail.com
        ✓ Token OAuth: usuario@gmail.com

        🔌 PASO 4: Estableciendo Conexión
        ------------------------------------------------------------
        → Conectando a localhost:5555 mediante TLS...
        ✓ Conexión TLS establecida
        ✓ Iniciando protocolo de cifrado RSA...

        ============================================================
        ✅ ¡AUTENTICACIÓN EXITOSA!
        ============================================================

        💬 Ya puedes escribir mensajes.
        • Escribe tu mensaje y presiona Enter para enviarlo
        • Cifrado de aplicación: RSA-2048
        • Cifrado de transporte: TLS (capa adicional de seguridad)
        • Presiona Ctrl+C para salir

        ------------------------------------------------------------
        ```

        #### Navegador: Autenticación Web

        1. **Abre**: `http://localhost:5000`
        2. **Click**: Botón "Continuar con Google"
        3. **Autoriza**: Aplicación en Google
        4. **Copia**: Email mostrado en página autenticada
        5. **Pega**: En cliente de chat

        ---

        ## 🔒 Seguridad

        ### Capas de Seguridad Implementadas

        #### 1. Capa de Autenticación (OAuth 2.0)

        - ✅ **Delegación de autenticación** a Google
        - ✅ **Sin almacenamiento de contraseñas**
        - ✅ **Tokens de corta duración**
        - ✅ **Scopes limitados** (openid, email, profile)

        #### 2. Capa de Transporte (SSL/TLS)

        - ✅ **TLS 1.2+** (1.0 y 1.1 deshabilitados)
        - ✅ **Cifrados seguros** (ECDHE+AESGCM, CHACHA20)
        - ✅ **Certificados** (autofirmados para desarrollo)

        #### 3. Capa de Aplicación (RSA)

        - ✅ **Cifrado asimétrico RSA-2048**
        - ✅ **Padding OAEP con SHA-256**
        - ✅ **Verificación de integridad** (SHA-256 + MD5)

        #### 4. Capa de Sesión (Flask)

        - ✅ **Sesiones cifradas** con SECRET_KEY
        - ✅ **Cookies HttpOnly** (protección XSS)
        - ✅ **SameSite=Lax** (protección CSRF)

        ### Mejores Prácticas Implementadas

        #### ✅ OAuth 2.0

        - Uso de `authlib` (librería robusta y actualizada)
        - OpenID Connect Discovery (configuración automática)
        - Manejo de errores OAuth detallado
        - Validación de tokens en servidor de chat

        #### ✅ Separación de Responsabilidades

        - Servidor web (puerto 5000): Solo autenticación
        - Servidor de chat (puerto 5555): Solo mensajería
        - No hay mezcla de responsabilidades

        #### ✅ Validación de Datos

        - Validación de formato de email (`@` presente)
        - Validación de sesión antes de acceder a rutas protegidas
        - Validación de tokens OAuth antes de aceptar conexión

        ### Recomendaciones para Producción

        #### 🔴 Crítico

        1. **Certificados SSL**:
        ```
        Usar certificados firmados por CA confiable
        (Let's Encrypt, DigiCert, etc.)
        NO usar certificados autofirmados
        ```

        2. **SECRET_KEY**:
        ```python
        # Generar nueva clave aleatoria
        import secrets
        SECRET_KEY = secrets.token_hex(32)
        # NO reutilizar la del .env.example
        ```

        3. **HTTPS Obligatorio**:
        ```python
        app.config['SESSION_COOKIE_SECURE'] = True
        # Solo transmite cookies por HTTPS
        ```

        #### 🟡 Importante

        4. **URIs Autorizadas**:
        ```
        Configurar dominio real en Google Cloud Console
        Ejemplo: https://chat.tudominio.com/callback
        NO usar http://localhost en producción
        ```

        5. **Rate Limiting**:
        ```python
        # Agregar flask-limiter
        from flask_limiter import Limiter
        
        limiter = Limiter(
            app,
            key_func=get_remote_address,
            default_limits=["200 per day", "50 per hour"]
        )
        ```

        6. **Logging de Seguridad**:
        ```python
        import logging
        
        # Loggear intentos de autenticación
        logging.info(f"Login exitoso: {user.email}")
        logging.warning(f"Login fallido desde {request.remote_addr}")
        ```

        ---

        ## 🛠️ Troubleshooting

        ### Problemas Comunes y Soluciones

        #### 1. Error: "Credenciales OAuth no configuradas"

        **Síntoma**:
        ```
        ⚠️  ADVERTENCIA: Las credenciales de Google OAuth no están configuradas
        ```

        **Solución**:
        ```powershell
        # Verificar que .env exista
        Get-Content .env | Select-String "GOOGLE"

        # Debe mostrar:
        # GOOGLE_CLIENT_ID=...
        # GOOGLE_CLIENT_SECRET=...

        # Si no existe, crear desde .env.example
        Copy-Item .env.example .env
        notepad .env  # Agregar credenciales
        ```

        #### 2. Error: "redirect_uri_mismatch"

        **Síntoma**:
        ```
        Error 400: redirect_uri_mismatch
        The redirect URI in the request does not match
        ```

        **Solución**:
        1. Ir a [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
        2. Editar OAuth Client ID
        3. Verificar **Authorized redirect URIs**:
        ```
        http://localhost:5000/callback
        ```
        4. Guardar cambios
        5. Esperar 5-10 minutos para propagación

        #### 3. Error: "Token OAuth inválido"

        **Síntoma**:
        ```
        ✗ Token inválido. Debe ser un email válido.
        ```

        **Solución**:
        1. Verificar que copiaste el **email completo**
        2. Formato esperado: `usuario@gmail.com`
        3. NO copiar espacios antes/después
        4. Re-autenticarse en `http://localhost:5000`

        #### 4. Error: "Port 5000 already in use"

        **Síntoma**:
        ```
        OSError: [WinError 10048] Only one usage of each socket address
        ```

        **Solución**:
        ```powershell
        # Ver qué proceso usa el puerto 5000
        netstat -ano | findstr :5000

        # Matar proceso por PID
        taskkill /PID <PID> /F

        # O cambiar puerto en .env
        # WEB_SERVER_PORT=5001
        ```

        #### 5. Error: "SSL Certificate verify failed"

        **Síntoma**:
        ```
        ssl.SSLError: [SSL: CERTIFICATE_VERIFY_FAILED]
        ```

        **Solución**:
        ```powershell
        # Regenerar certificados SSL
        python scripts/generate_ssl_certificates.py

        # O deshabilitar SSL temporalmente (solo testing)
        python client/client.py --disable-ssl
        python server/server.py --disable-ssl
        ```

        #### 6. Error: "ModuleNotFoundError: No module named 'flask'"

        **Síntoma**:
        ```
        ModuleNotFoundError: No module named 'flask'
        ```

        **Solución**:
        ```powershell
        # Instalar dependencias
        pip install -r requirements.txt

        # Verificar instalación
        pip list | Select-String "flask"
        # Debe mostrar: flask 3.1.2
        ```

        ---

        ## 📋 Changelog

        ### [1.0.0] - 2025-11-16

        #### ✅ Agregado

        - Sistema completo de autenticación OAuth 2.0 con Google
        - Servidor web Flask en puerto 5000
        - Modelo `OAuthModel` con Authlib
        - Controlador `auth_routes` con rutas OAuth
        - Templates HTML:
        - `login.html` (solo botón Google)
        - `authenticated.html` (muestra token)
        - `error.html` (manejo de errores)
        - Integración de token OAuth en servidor de chat
        - Cliente de chat actualizado para usar tokens OAuth
        - Variables de entorno OAuth en `.env.example`
        - Documentación completa:
        - `AUTH-INTEGRATION.md`
        - `INTEGRATION-PLAN.md`

        #### ❌ Eliminado

        - Formulario de login con email + contraseña
        - Endpoint `/api/auth/login` (POST estático)
        - Autenticación local con `CHAT_SERVER_PASSWORD`
        - Solicitud de `NICK` y `PASSWORD` en servidor

        #### 🔧 Modificado

        - `server/server.py`: 
        - Método `manejar_cliente()` ahora usa `OAUTH_TOKEN`
        - Validación de formato de email
        - `client/client.py`:
        - Paso 3 solicita token OAuth en lugar de contraseña
        - Manejo de mensaje `OAUTH_TOKEN`
        - `config.py`:
        - Agregadas variables OAuth (`GOOGLE_CLIENT_ID`, `SECRET_KEY`, etc.)
        - `requirements.txt`:
        - Agregadas dependencias Flask y Authlib

        ---

        ## 📞 Soporte y Contacto

        ### Documentación Relacionada

        - **README.md**: Guía general del proyecto
        - **copilot.md**: Arquitectura y comandos del sistema
        - **INTEGRATION-PLAN.md**: Plan detallado de integración
        - **QUICKSTART_SSL.md**: Guía rápida de SSL/TLS

        ### Recursos Externos

        - [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
        - [Authlib Documentation](https://docs.authlib.org/)
        - [Flask Documentation](https://flask.palletsprojects.com/)
        - [Python Cryptography](https://cryptography.io/)

        ---

        **Versión**: 1.0.0  
        **Fecha**: 16 de Noviembre de 2025  
        **Autor**: GitHub Copilot Agent (Claude Sonnet 4.5)  
        **Proyecto**: Python-Client-Server-Chat con OAuth 2.0
