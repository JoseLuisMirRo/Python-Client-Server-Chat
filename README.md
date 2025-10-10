# 🔐 Sistema de Chat Seguro Cliente-Servidor en Python

Un sistema de chat en tiempo real con múltiples esquemas de cifrado implementados en diferentes ramas. Este proyecto demuestra el uso de criptografía simétrica (AES) y asimétrica (RSA) en aplicaciones de comunicación en red.

## 📋 Tabla de Contenidos

- [Características](#-características)
- [Arquitectura](#-arquitectura)
- [Ramas del Proyecto](#-ramas-del-proyecto)
- [Instalación](#-instalación)
- [Uso](#-uso)
- [Verificación de Integridad](#-verificación-de-integridad)
- [Seguridad](#-seguridad)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Tecnologías Utilizadas](#-tecnologías-utilizadas)

## ✨ Características

### Características Generales
- 🔒 **Comunicación cifrada end-to-end**
- 👥 **Soporte para múltiples clientes simultáneos** (hasta 500)
- 🔐 **Autenticación segura con contraseña**
- 💬 **Chat en tiempo real** con notificaciones de entrada/salida
- 🌐 **Soporte para conexiones LAN** (misma red local)
- 🧵 **Arquitectura multihilo** con ThreadPoolExecutor
- 📝 **Logging detallado** de eventos y errores
- ✅ **Verificación de integridad** con checksums MD5

### Características por Rama

#### `cifrado-simetrico` (AES)
- **Cifrado AES-256-GCM**: Algoritmo de cifrado simétrico rápido y seguro
- **Clave compartida**: Todos los participantes usan la misma clave secreta
- **Autenticación de integridad**: GCM proporciona autenticación automática
- **Nonces únicos**: Cada mensaje tiene su propio nonce para máxima seguridad
- **Gestión de claves**: Generación y carga de claves desde archivo

#### `cifrado-asimetrico` (RSA)
- **Cifrado RSA-2048**: Algoritmo de cifrado asimétrico con par de claves
- **Claves públicas/privadas**: Cada cliente tiene su propio par de claves
- **Intercambio seguro de claves**: No requiere canal previo seguro
- **Padding OAEP**: Protocolo de relleno óptimo para máxima seguridad
- **Gestión de certificados**: Sistema de claves públicas compartidas

## 🏗️ Arquitectura

```
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│   Cliente 1     │◄────────┤   Servidor      │────────►│   Cliente 2     │
│                 │         │                 │         │                 │
│  - Socket TCP   │         │  - Escucha en   │         │  - Socket TCP   │
│  - Cifrado      │         │    puerto 5555  │         │  - Cifrado      │
│  - Hilos RX/TX  │         │  - ThreadPool   │         │  - Hilos RX/TX  │
└─────────────────┘         │  - Broadcast    │         └─────────────────┘
                            │  - Autenticación│
                            └─────────────────┘
```

### Flujo de Comunicación

1. **Conexión**: Cliente se conecta al servidor via TCP
2. **Autenticación**: 
   - Servidor solicita nickname (cifrado)
   - Servidor solicita contraseña (cifrada)
   - Servidor valida y responde AUTH_SUCCESS/AUTH_FAILED
3. **Mensajería**:
   - Cliente envía mensaje cifrado
   - Servidor descifra, valida y reenvía a otros clientes
   - Clientes reciben y descifran mensajes

## 🌿 Ramas del Proyecto

### `main`
Rama principal con documentación base del proyecto.

### `cifrado-simetrico` ⭐
Implementación con **cifrado simétrico AES-256-GCM**.

**Ventajas:**
- ⚡ Muy rápido para mensajes de cualquier tamaño
- 🔒 Seguro con clave de 256 bits
- ✅ Autenticación integrada (GCM)
- 💾 Bajo uso de recursos

**Desventajas:**
- 🔑 Todos comparten la misma clave
- 📤 Distribución de clave puede ser compleja

**Archivos clave:**
- `crypto/aes_crypto.py`: Módulo de cifrado AES
- `shared_aes_key.key`: Clave compartida (generada por el servidor)

### `cifrado-asimetrico`
Implementación con **cifrado asimétrico RSA-2048**.

**Ventajas:**
- 🔐 Cada cliente tiene su propio par de claves
- 📤 No requiere compartir secretos previamente
- 🎯 Ideal para autenticación y firma digital

**Desventajas:**
- 🐌 Más lento que AES
- 📏 Limitación en tamaño de mensaje
- 💻 Mayor uso de CPU

**Archivos clave:**
- `crypto/rsa_crypto.py`: Módulo de cifrado RSA
- `server_private_key.pem`: Clave privada del servidor
- `server_public_key.pem`: Clave pública del servidor

## 📦 Instalación

### Requisitos Previos
- Python 3.9 o superior
- pip (gestor de paquetes de Python)
- Conexión a internet (para instalar dependencias)

### Pasos de Instalación

1. **Clonar el repositorio**
```bash
git clone <url-del-repositorio>
cd LearningPython
```

2. **Seleccionar la rama deseada**

Para cifrado simétrico (AES):
```bash
git checkout cifrado-simetrico
```

Para cifrado asimétrico (RSA):
```bash
git checkout cifrado-asimetrico
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

### Dependencias
- `cryptography>=41.0.0`: Biblioteca de criptografía
- `colorama>=0.4.6`: Colores en terminal (opcional)

## 🚀 Uso

### Configuración Rápida (Misma Máquina)

1. **Iniciar el servidor**
```bash
python server/server.py
```

El servidor:
- Escuchará en `0.0.0.0:5555`
- Generará automáticamente las claves necesarias
- Mostrará la IP local para conexiones LAN

2. **Iniciar cliente(s)**

En otra(s) terminal(es):
```bash
python client/client.py
```

3. **Configurar el cliente**
- **IP del servidor**: Presiona Enter para `localhost` o ingresa la IP
- **Puerto**: Presiona Enter para `5555` o ingresa otro puerto
- **Clave/Archivo**: Presiona Enter para usar el predeterminado
- **Contraseña del servidor**: `secreto` (por defecto)
- **Nombre de usuario**: Tu nickname preferido

### Conexión desde Otros Dispositivos (Misma Red LAN)

#### En el Servidor

1. Inicia el servidor:
```bash
python server/server.py
```

2. Anota la IP local mostrada, o consúltala con:

**macOS:**
```bash
ipconfig getifaddr en0  # Wi-Fi
ipconfig getifaddr en1  # Ethernet
```

**Linux:**
```bash
hostname -I
```

**Windows:**
```bash
ipconfig
```

3. Asegúrate de que el firewall permita conexiones al puerto 5555.

#### En los Clientes

1. Ejecuta el cliente:
```bash
python client/client.py
```

2. Cuando se te solicite:
   - **IP del servidor**: Ingresa la IP del servidor (ej: `192.168.1.100`)
   - **Puerto**: `5555`
   - **Archivo de clave**: Si estás en otra máquina, debes copiar el archivo de clave generado por el servidor
   - **Contraseña**: `secreto` (o la que hayas configurado)

### Cambiar Configuración del Servidor

Edita `server/server.py`:

```python
# Línea 254
server = ChatServer(
    host="0.0.0.0",      # Escuchar en todas las interfaces
    port=5555,           # Puerto de escucha
    password="secreto"   # Cambia esta contraseña
)
```

## 🔍 Verificación de Integridad (MD5)

**Versión**: 1.0.0 - Rama `cifrado-simetrico`

Para verificar la integridad de los archivos principales del proyecto, compara los siguientes checksums MD5:

### Checksums de Archivos Principales

```bash
# Servidor
MD5 (server/server.py) = d2d226b31af60182ad5f62e08ef42f06

# Cliente
MD5 (client/client.py) = 63b392887464fe2ee44ae67117d66ee3

# Módulo de Cifrado AES
MD5 (crypto/aes_crypto.py) = 3c8ff6960cd7767286e23e22850ca6b1
```

### Verificar Checksums

Para verificar manualmente la integridad de los archivos en macOS/Linux:

```bash
md5 server/server.py client/client.py crypto/aes_crypto.py
```

Si los checksums no coinciden, los archivos pueden haber sido modificados. Para restaurar la versión original:

```bash
git checkout server/server.py
git checkout client/client.py
git checkout crypto/aes_crypto.py
```

## 🔒 Seguridad

### Mejores Prácticas

1. **Contraseñas fuertes**: Cambia la contraseña predeterminada del servidor
2. **Permisos de archivos**: Protege los archivos de claves
   ```bash
   chmod 600 shared_aes_key.key
   chmod 600 server_private_key.pem
   ```
3. **Distribución segura**: Comparte las claves por canales seguros (USB, HTTPS, etc.)
4. **Firewall**: Configura reglas de firewall apropiadas
5. **Logs**: Revisa los logs regularmente para detectar actividad sospechosa
6. **Verificación de integridad**: Verifica los checksums MD5 regularmente (ver sección de Verificación de Integridad)

### Consideraciones de Seguridad

#### Cifrado Simétrico (AES)
- ✅ **Velocidad**: Excelente para chat en tiempo real
- ✅ **Seguridad**: AES-256 es estándar militar
- ⚠️ **Gestión de claves**: La clave debe distribuirse de forma segura
- ⚠️ **Escala**: Cada grupo necesita su propia clave

#### Cifrado Asimétrico (RSA)
- ✅ **Distribución**: No requiere canal seguro previo
- ✅ **Identidad**: Permite verificar identidad del emisor
- ⚠️ **Rendimiento**: Más lento, no ideal para mensajes grandes
- ⚠️ **Complejidad**: Requiere infraestructura de claves públicas

### Limitaciones Conocidas

- El servidor conoce todos los mensajes (no es E2E puro)
- Sin forward secrecy en la implementación actual
- Sin revocación de claves implementada
- Sin autenticación de identidad del servidor (rama RSA)

## 📁 Estructura del Proyecto

```
LearningPython/
│
├── client/
│   └── client.py              # Cliente de chat
│
├── server/
│   └── server.py              # Servidor de chat
│
├── crypto/
│   ├── __init__.py            # Paquete crypto
│   ├── aes_crypto.py          # Módulo de cifrado AES (rama simetrico)
│   └── rsa_crypto.py          # Módulo de cifrado RSA (rama asimetrico)
│
├── requirements.txt           # Dependencias del proyecto
├── README.md                  # Este archivo
│
└── [Archivos de claves generados]
    ├── shared_aes_key.key     # Clave AES (generada automáticamente)
    ├── server_private_key.pem # Clave privada RSA (generada automáticamente)
    └── server_public_key.pem  # Clave pública RSA (generada automáticamente)
```

## 🛠️ Tecnologías Utilizadas

- **Python 3.9+**: Lenguaje de programación
- **socket**: Comunicación TCP/IP
- **threading**: Concurrencia con hilos
- **cryptography**: 
  - `AESGCM`: Cifrado simétrico AES-256-GCM
  - `RSA`: Cifrado asimétrico RSA-2048
  - `PBKDF2`: Derivación de claves
- **concurrent.futures**: ThreadPoolExecutor para gestión de clientes
- **logging**: Sistema de logs

## 🔧 Solución de Problemas

### El cliente no puede conectarse

1. Verifica que el servidor esté ejecutándose
2. Confirma que la IP y puerto sean correctos
3. Revisa las reglas del firewall
4. Asegúrate de que ambos estén en la misma red (para LAN)

### Error de autenticación

1. Verifica que la contraseña sea correcta
2. Confirma que tengas el archivo de clave correcto
3. Asegúrate de que el archivo de clave no esté corrupto

### Mensajes no se descifran correctamente

1. Verifica que todos usen la misma clave (AES)
2. Confirma que el archivo de clave sea el generado por el servidor actual
3. Reinicia el servidor y clientes

### Error de verificación de integridad

1. Verifica los checksums MD5 con: `md5 server/server.py client/client.py crypto/aes_crypto.py`
2. Compara los resultados con los checksums en la sección "Verificación de Integridad" del README
3. Si no coinciden y los cambios no son legítimos, restaura desde git: `git checkout <archivo>`

## 📝 Notas de Desarrollo

### Cambiar entre Ramas

```bash
# A cifrado simétrico
git checkout cifrado-simetrico

# A cifrado asimétrico
git checkout cifrado-asimetrico
```

### Contribuir al Proyecto

1. Crea un fork del repositorio
2. Crea una rama para tu feature: `git checkout -b feature/nueva-funcionalidad`
3. Haz commit de tus cambios: `git commit -am 'Agrega nueva funcionalidad'`
4. Push a la rama: `git push origin feature/nueva-funcionalidad`
5. Crea un Pull Request

### Testing

Prueba con múltiples clientes:
```bash
# Terminal 1: Servidor
python server/server.py

# Terminal 2: Cliente 1
python client/client.py

# Terminal 3: Cliente 2
python client/client.py

# Terminal 4: Cliente 3
python client/client.py
```

## 📄 Licencia

Este proyecto es con fines educativos. Úsalo bajo tu propio riesgo.

## 👨‍💻 Autor

Proyecto de aprendizaje de criptografía y redes en Python.

---

**⚠️ IMPORTANTE**: Este es un proyecto educativo. Para aplicaciones de producción, considera usar protocolos establecidos como TLS/SSL, Signal Protocol, o soluciones comerciales de mensajería segura.

---

## 🆘 Soporte

Si encuentras problemas:
1. Revisa la sección de [Solución de Problemas](#-solución-de-problemas)
2. Verifica los logs del servidor y cliente
3. Ejecuta la verificación de integridad
4. Consulta la documentación en el código

---

**Última actualización**: Octubre 2025
**Versión**: 1.0.0
