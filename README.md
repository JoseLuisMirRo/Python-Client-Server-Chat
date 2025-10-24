# Cliente-Servidor Chat en Python con Cifrado RSA

Sistema de chat seguro con cifrado asimétrico RSA, autenticación y configuración flexible mediante variables de entorno.

## 📋 Características

- **Cifrado RSA**: Todos los mensajes se cifran usando criptografía asimétrica
- **Autenticación segura**: Nickname y contraseña se transmiten cifrados
- **Claves automáticas**: El servidor genera automáticamente un par de claves RSA
- **Configuración flexible**: Sin hardcoding, todo configurable mediante variables de entorno
- **Verificación de integridad**: Los mensajes incluyen hashes SHA-256 y MD5 para validación
- **Multi-cliente**: Soporte para múltiples clientes simultáneos con ThreadPoolExecutor

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

### 3. Configurar variables de entorno (Opcional)

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
```

Si no creas un archivo `.env`, se usarán los valores por defecto.

## 🎮 Uso Básico

### Opción 1: Misma máquina

1. **Inicia el servidor** (ventana/terminal 1):
   ```bash
   python server/server.py
   ```

2. **Inicia los clientes** (ventanas separadas):
   ```bash
   python client/client.py
   ```

### Opción 2: Con argumentos de línea de comandos

**Servidor con configuración personalizada:**
```bash
python server/server.py --host 0.0.0.0 --port 5555 --password mi_password
```

**Cliente con configuración personalizada:**
```bash
python client/client.py --host 192.168.1.100 --port 5555
```

### Opción 3: Mostrar configuración actual

```bash
python server/server.py --show-config
```

## 🌐 Conexión desde otros dispositivos (LAN)

### Configuración del servidor

1. **Inicia el servidor en modo público:**
   ```bash
   python server/server.py --host 0.0.0.0 --port 5555
   ```

2. **Obtén la IP local del servidor:**
   
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

3. **Comparte con los clientes:**
   - La IP local (ejemplo: `192.168.1.100`)
   - El puerto (`5555` por defecto)
   - La contraseña del servidor

### Conexión desde clientes

```bash
python client/client.py --host 192.168.1.100 --port 5555
```

O simplemente ejecuta `python client/client.py` y sigue las instrucciones interactivas.

## 📁 Estructura del Proyecto

```
.
├── README.md                    # Este archivo
├── .env.example                 # Plantilla de variables de entorno
├── .gitignore                   # Archivos a ignorar por Git
├── config.py                    # Configuración centralizada
├── requirements.txt             # Dependencias de Python
├── client/
│   └── client.py               # Cliente de chat
├── server/
│   └── server.py               # Servidor de chat
├── crypto/
│   ├── __init__.py
│   └── rsa_crypto.py           # Módulo de cifrado RSA
└── scripts/
    └── test_hash_mismatch.py   # Prueba de verificación de hashes
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
| `CHAT_SERVER_PRIVATE_KEY` | Ruta de clave privada | `server_private_key.pem` |
| `CHAT_SERVER_PUBLIC_KEY` | Ruta de clave pública | `server_public_key.pem` |

### Precedencia de Configuración

1. **Argumentos de línea de comandos** (mayor prioridad)
2. **Variables de entorno** (archivo `.env` o sistema)
3. **Valores por defecto** (en `config.py`)

## 🔐 Seguridad

### Claves RSA

- El servidor genera automáticamente un par de claves RSA al iniciar
- Las claves se guardan en archivos `.pem` (incluidos en `.gitignore`)
- **IMPORTANTE**: Nunca versiones las claves privadas en Git
- Los clientes generan claves temporales en memoria para cada sesión

### Autenticación

1. Cliente y servidor intercambian claves públicas
2. Nickname y contraseña se transmiten cifrados con RSA
3. El servidor valida las credenciales antes de permitir el acceso

### Integridad de Mensajes

- Cada mensaje incluye hashes SHA-256 y MD5
- El servidor verifica la integridad antes de retrasmitir
- Los mensajes manipulados son descartados automáticamente

## 🧪 Pruebas

### Verificar hash mismatch

```bash
python scripts/test_hash_mismatch.py
```

Este script prueba que el servidor rechaza mensajes con hashes inválidos.

## 🔧 Solución de Problemas

### El servidor no inicia

- Verifica que el puerto no esté en uso: `lsof -i :5555` (macOS/Linux)
- Cambia el puerto: `python server/server.py --port 5556`

### Cliente no puede conectarse

- Verifica que el servidor esté ejecutándose
- Confirma que la IP y puerto sean correctos
- Verifica el firewall del servidor permita conexiones entrantes

### Error "No se encontró la clave pública"

- Asegúrate de que el servidor esté ejecutándose primero
- El servidor genera `server_public_key.pem` automáticamente
- Verifica que el cliente pueda acceder al archivo

### Autenticación fallida

- Verifica que uses la contraseña correcta del servidor
- Revisa la configuración en `.env` o los argumentos del servidor

## 📝 Notas

- **Contraseña por defecto**: `secreto` (¡cámbiala en producción!)
- **Puerto por defecto**: `5555`
- **Cifrado**: RSA-2048 por defecto (puedes usar 4096 para mayor seguridad)
- **Firewall**: Asegúrate de permitir conexiones entrantes al puerto configurado

## 🤝 Contribuir

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la licencia MIT. Ver archivo `LICENSE` para más detalles.


**Última actualización**: Octubre 2025 | **Versión**: 2.0.0 (Sin hardcoding)