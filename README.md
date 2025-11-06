# Cliente-Servidor Chat en Python con Cifrado RSA y SSL/TLS

Sistema de chat seguro con doble capa de cifrado: SSL/TLS a nivel de transporte y RSA a nivel de aplicación. Incluye autenticación y configuración flexible mediante variables de entorno.

## 📋 Características

- **🔐 Cifrado SSL/TLS**: Capa de seguridad de transporte (TLS 1.2+) para todas las conexiones
- **🔒 Cifrado RSA**: Todos los mensajes se cifran usando criptografía asimétrica
- **🛡️ Doble cifrado**: Combinación de SSL/TLS (transporte) + RSA (aplicación)
- **✅ Autenticación segura**: Nickname y contraseña se transmiten cifrados
- **🔑 Claves automáticas**: El servidor genera automáticamente claves RSA y certificados SSL
- **⚙️ Configuración flexible**: Sin hardcoding, todo configurable mediante variables de entorno
- **🔍 Verificación de integridad**: Los mensajes incluyen hashes SHA-256 y MD5 para validación
- **👥 Multi-cliente**: Soporte para múltiples clientes simultáneos con ThreadPoolExecutor

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
git clone <url-del-repo>
cd Python-Client-Server-Chat
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Generar certificados SSL (Primera vez)

Genera certificados SSL/TLS autofirmados para desarrollo:

```bash
python scripts/generate_ssl_certificates.py
```

Esto creará:
- `server_cert.pem` - Certificado SSL del servidor
- `server_key.pem` - Clave privada SSL del servidor

**Nota**: Los certificados generados son solo para desarrollo. Para producción, usa certificados firmados por una CA confiable.

### 4. Configurar variables de entorno (Opcional)

Copia el archivo de ejemplo y ajusta según tus necesidades:

```bash
cp .env.example .env
```

Edita `.env` con tu editor favorito:

```bash
# Ejemplo de configuración
CHAT_HOST=0.0.0.0
CHAT_PORT=5555
CHAT_SERVER_PASSWORD=mi_contraseña_segura
CHAT_RSA_KEY_SIZE=2048

# Configuración SSL/TLS
CHAT_ENABLE_SSL=True
CHAT_SSL_CERT=server_cert.pem
CHAT_SSL_KEY=server_key.pem
```

Si no creas un archivo `.env`, se usarán los valores por defecto.

## 🎮 Uso Básico

### Opción 1: Misma máquina con SSL/TLS (Recomendado)

1. **Genera certificados SSL** (solo la primera vez):
   ```bash
   python scripts/generate_ssl_certificates.py
   ```

2. **Inicia el servidor** (ventana/terminal 1):
   ```bash
   python server/server.py
   ```

3. **Inicia los clientes** (ventanas separadas):
   ```bash
   python client/client.py
   ```

Por defecto, SSL/TLS está **habilitado**. Verás mensajes como:
- `🔐 SSL/TLS habilitado (TLS 1.2+)` en el servidor
- `✓ Conexión TLS establecida` en el cliente

### Opción 2: Sin SSL/TLS (Solo para testing)

Si necesitas desactivar SSL/TLS temporalmente:

**Servidor sin SSL:**
```bash
python server/server.py --disable-ssl
```

**Cliente sin SSL:**
```bash
python client/client.py --disable-ssl
```

### Opción 3: Con argumentos de línea de comandos

**Servidor con configuración personalizada:**
```bash
python server/server.py --host 0.0.0.0 --port 5555 --password mi_password --enable-ssl
```

**Cliente con configuración personalizada:**
```bash
python client/client.py --host 192.168.1.100 --port 5555 --enable-ssl
```

### Opción 4: Mostrar configuración actual

```bash
python server/server.py --show-config
```

## 🌐 Conexión desde otros dispositivos (LAN)

### Configuración del servidor

1. **Genera certificados SSL** (si no lo has hecho):
   ```bash
   python scripts/generate_ssl_certificates.py
   ```

2. **Inicia el servidor en modo público:**
   ```bash
   python server/server.py --host 0.0.0.0 --port 5555
   ```

3. **Obtén la IP local del servidor:**
   
   **En macOS/Linux:**
   ```bash
   ifconfig | grep "inet " | grep -v 127.0.0.1
   # O específicamente para WiFi:
   ipconfig getifaddr en0
   ```
   
   **En Windows:**
   ```bash
   ipconfig
   # Busca "Dirección IPv4"
   ```

4. **Comparte con los clientes:**
   - La IP local (ejemplo: `192.168.1.100`)
   - El puerto (`5555` por defecto)
   - La contraseña del servidor

### Conexión desde clientes

```bash
python client/client.py --host 192.168.1.100 --port 5555
```

O simplemente ejecuta `python client/client.py` y sigue las instrucciones interactivas.

**Nota sobre SSL/TLS en LAN**: Los certificados autofirmados funcionan perfectamente en la red local. Los clientes aceptarán automáticamente el certificado del servidor (configurado para desarrollo).

## 📁 Estructura del Proyecto

```
.
├── README.md                           # Este archivo
├── .env.example                        # Plantilla de variables de entorno
├── .gitignore                          # Archivos a ignorar por Git
├── config.py                           # Configuración centralizada
├── requirements.txt                    # Dependencias de Python
├── client/
│   └── client.py                      # Cliente de chat
├── server/
│   └── server.py                      # Servidor de chat
├── crypto/
│   ├── __init__.py
│   └── rsa_crypto.py                  # Módulo de cifrado RSA
└── scripts/
    ├── generate_ssl_certificates.py   # Generador de certificados SSL
    └── test_hash_mismatch.py          # Prueba de verificación de hashes
```

## ⚙️ Configuración

### Variables de Entorno Disponibles

| Variable | Descripción | Default |
|----------|-------------|---------|
| `CHAT_HOST` | Host del servidor | `localhost` |
| `CHAT_PORT` | Puerto del servidor | `5555` |
| `CHAT_SERVER_PASSWORD` | Contraseña de autenticación | `secreto` |
| `CHAT_RSA_KEY_SIZE` | Tamaño de clave RSA (bits) | `2048` |
| `CHAT_MAX_CLIENTS` | Máximo de clientes simultáneos | `500` |
| `CHAT_BUFFER_SIZE` | Tamaño del buffer de recepción | `4096` |
| `CHAT_LOG_LEVEL` | Nivel de logging | `INFO` |
| `CHAT_SERVER_PRIVATE_KEY` | Ruta de clave privada RSA | `server_private_key.pem` |
| `CHAT_SERVER_PUBLIC_KEY` | Ruta de clave pública RSA | `server_public_key.pem` |
| `CHAT_ENABLE_SSL` | Habilitar SSL/TLS | `True` |
| `CHAT_SSL_CERT` | Ruta del certificado SSL | `server_cert.pem` |
| `CHAT_SSL_KEY` | Ruta de la clave privada SSL | `server_key.pem` |
| `CHAT_SSL_VERIFY_CLIENT` | Verificar certificados de cliente | `False` |
| `CHAT_SSL_CA_CERT` | Ruta del certificado CA | (opcional) |

### Precedencia de Configuración

1. **Argumentos de línea de comandos** (mayor prioridad)
2. **Variables de entorno** (archivo `.env` o sistema)
3. **Valores por defecto** (en `config.py`)

## 🔐 Seguridad

### Arquitectura de Seguridad Multicapa

Este sistema implementa **defensa en profundidad** con múltiples capas de seguridad:

```
┌─────────────────────────────────────────┐
│   Capa 4: Verificación de Integridad   │ ← SHA-256/MD5
├─────────────────────────────────────────┤
│   Capa 3: Cifrado de Aplicación (RSA)  │ ← Mensajes cifrados
├─────────────────────────────────────────┤
│   Capa 2: Autenticación                │ ← Nickname + Contraseña
├─────────────────────────────────────────┤
│   Capa 1: Cifrado de Transporte (TLS)  │ ← SSL/TLS 1.2+
└─────────────────────────────────────────┘
```

### 1. Cifrado SSL/TLS (Capa de Transporte)

- **Protocolo**: TLS 1.2 o superior (TLS 1.0 y 1.1 deshabilitados)
- **Cifrados**: Solo cifrados seguros (ECDHE+AESGCM, CHACHA20, etc.)
- **Certificados**: Autofirmados para desarrollo (usa CA confiable en producción)
- **Verificación**: El cliente acepta certificados autofirmados en desarrollo
- **Beneficio**: Protege toda la comunicación a nivel de socket, incluyendo handshake y metadatos

### 2. Claves RSA (Capa de Aplicación)

- El servidor genera automáticamente un par de claves RSA al iniciar
- Tamaño de clave: 2048 bits (configurable a 4096)
- Las claves se guardan en archivos `.pem` (incluidos en `.gitignore`)
- **IMPORTANTE**: Nunca versiones las claves privadas en Git
- Los clientes generan claves temporales en memoria para cada sesión

### 3. Autenticación

1. Cliente y servidor establecen conexión SSL/TLS
2. Intercambian claves públicas RSA (cifradas por SSL)
3. Nickname y contraseña se transmiten cifrados con RSA
4. El servidor valida las credenciales antes de permitir el acceso

### 4. Integridad de Mensajes

- Cada mensaje incluye hashes SHA-256 y MD5
- El servidor verifica la integridad antes de retrasmitir
- Los mensajes manipulados son descartados automáticamente

### ¿Por qué dos capas de cifrado?

- **SSL/TLS**: Protege contra ataques de red (sniffing, MITM)
- **RSA**: Protege contra compromisos del servidor o logs de red
- **Defensa en profundidad**: Si una capa falla, la otra sigue protegiendo

## 🧪 Pruebas

### Verificar hash mismatch

```bash
python scripts/test_hash_mismatch.py
```

Este script prueba que el servidor rechaza mensajes con hashes inválidos.

### Probar SSL/TLS

Para verificar que SSL/TLS está funcionando:

1. Inicia el servidor con SSL habilitado (default)
2. Conéctate con un cliente
3. Verifica en los logs del servidor: `🔐 Conexión SSL establecida`
4. Verifica en el cliente: `✓ Protocolo: TLSv1.3` (o TLSv1.2)

Para probar sin SSL y ver la diferencia:
```bash
# Terminal 1
python server/server.py --disable-ssl

# Terminal 2
python client/client.py --disable-ssl
```

## 🔧 Solución de Problemas

### El servidor no inicia

- Verifica que el puerto no esté en uso: `lsof -i :5555` (macOS/Linux)
- Cambia el puerto: `python server/server.py --port 5556`

### Error "Certificado SSL no encontrado"

Si ves: `❌ Certificado SSL no encontrado: server_cert.pem`

**Solución:**
```bash
python scripts/generate_ssl_certificates.py
```

Esto generará los certificados necesarios.

### Error SSL en el cliente

Si ves errores SSL al conectar:

1. Verifica que el servidor tenga certificados válidos
2. Verifica que ambos (cliente y servidor) usen la misma configuración SSL
3. Para desarrollo, desactiva temporalmente: `--disable-ssl`

### Cliente no puede conectarse

- Verifica que el servidor esté ejecutándose
- Confirma que la IP y puerto sean correctos
- Verifica el firewall del servidor permita conexiones entrantes
- Verifica que SSL esté habilitado/deshabilitado en ambos lados

### Error "No se encontró la clave pública"

- Asegúrate de que el servidor esté ejecutándose primero
- El servidor genera `server_public_key.pem` automáticamente
- Verifica que el cliente pueda acceder al archivo

### Autenticación fallida

- Verifica que uses la contraseña correcta del servidor
- Revisa la configuración en `.env` o los argumentos del servidor

### Advertencias de certificados autofirmados

Es normal ver advertencias sobre certificados autofirmados en desarrollo. Para producción:

1. Obtén un certificado de una CA confiable (Let's Encrypt, etc.)
2. Configura las rutas en `.env`:
   ```bash
   CHAT_SSL_CERT=/ruta/a/tu/certificado.pem
   CHAT_SSL_KEY=/ruta/a/tu/clave.pem
   ```
3. En el cliente, habilita verificación de certificados modificando `_configurar_ssl_cliente()`

## 📝 Notas

### Configuración por defecto

- **Contraseña**: `secreto` (¡cámbiala en producción!)
- **Puerto**: `5555`
- **Cifrado SSL/TLS**: Habilitado por defecto
- **Cifrado RSA**: 2048 bits (puedes usar 4096 para mayor seguridad)
- **Firewall**: Asegúrate de permitir conexiones entrantes al puerto configurado

### Recomendaciones de Seguridad para Producción

1. **Certificados SSL/TLS**:
   - Usa certificados de una CA confiable (Let's Encrypt, DigiCert, etc.)
   - Nunca uses certificados autofirmados en producción
   - Habilita verificación de certificados en el cliente

2. **Contraseñas**:
   - Cambia la contraseña por defecto
   - Usa contraseñas fuertes (mínimo 16 caracteres)
   - Considera implementar autenticación basada en tokens

3. **Claves RSA**:
   - Usa claves de 4096 bits para mayor seguridad
   - Rota las claves periódicamente
   - Protege las claves privadas con permisos de archivo adecuados

4. **Red**:
   - Usa un firewall configurado apropiadamente
   - Considera rate limiting para prevenir ataques de fuerza bruta
   - Implementa logging de seguridad

5. **Certificados en LAN**:
   - Para redes locales, los certificados autofirmados son aceptables
   - Considera crear una CA interna para tu organización

## 🤝 Contribuir

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la licencia MIT. Ver archivo `LICENSE` para más detalles.

## 🎓 Aprende Más

### Recursos sobre SSL/TLS
- [Transport Layer Security (Wikipedia)](https://es.wikipedia.org/wiki/Transport_Layer_Security)
- [Let's Encrypt - Certificados gratuitos](https://letsencrypt.org/)
- [OWASP TLS Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Transport_Layer_Protection_Cheat_Sheet.html)

### Recursos sobre Criptografía
- [Biblioteca cryptography de Python](https://cryptography.io/)
- [RSA en Wikipedia](https://es.wikipedia.org/wiki/RSA)
- [Mejores prácticas de criptografía](https://www.owasp.org/index.php/Cryptographic_Storage_Cheat_Sheet)


**Última actualización**: Noviembre 2025 | **Versión**: 3.0.0 (Con SSL/TLS)