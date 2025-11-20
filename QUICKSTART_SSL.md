# 🚀 Guía Rápida de Inicio con SSL/TLS

Esta guía te ayudará a poner en marcha el chat con SSL/TLS en menos de 5 minutos.

## ⚡ Inicio Rápido (3 Pasos)

### 1️⃣ Genera los Certificados SSL

```bash
python scripts/generate_ssl_certificates.py
```

**Salida esperada:**
```
🔐 GENERADOR DE CERTIFICADOS SSL/TLS AUTOFIRMADOS
✅ CERTIFICADOS SSL/TLS GENERADOS EXITOSAMENTE
```

Esto creará:
- `server_cert.pem` - Certificado SSL del servidor
- `server_key.pem` - Clave privada SSL del servidor

### 2️⃣ Inicia el Servidor

```bash
python server/server.py
```

**Verás:**
```
🌐 Servidor de chat iniciado en localhost:5555
🔐 Contraseña del servidor: *******
🔒 Cifrado RSA habilitado (2048 bits)
🔐 SSL/TLS habilitado (TLS 1.2+)
✅ Esperando conexiones TLS en localhost:5555
```

### 3️⃣ Conecta un Cliente

En otra terminal:

```bash
python client/client.py
```

**Sigue las instrucciones:**
1. IP del servidor: `Enter` (usa localhost)
2. Puerto: `Enter` (usa 5555)
3. Contraseña: `secreto`
4. Tu nombre de usuario: `tu_nombre`

**Verás:**
```
✓ Conexión TLS establecida
✓ Protocolo: TLSv1.3
✓ Cifrado: TLS_AES_256_GCM_SHA384
✅ ¡AUTENTICACIÓN EXITOSA!
```

## 🎯 ¡Listo! Ya puedes chatear de forma segura

Tus mensajes ahora están protegidos con:
- ✅ Cifrado de transporte (TLS 1.2+)
- ✅ Cifrado de aplicación (RSA-2048)
- ✅ Verificación de integridad (SHA-256 + MD5)

## 📡 Usar en Red Local (LAN)

### En el Servidor:

```bash
python server/server.py --host 0.0.0.0 --port 5555
```

**Obtén tu IP local:**
```bash
# macOS/Linux
ipconfig getifaddr en0

# Windows
ipconfig
```

### En los Clientes:

```bash
python client/client.py --host 192.168.1.XXX --port 5555
```

(Reemplaza `192.168.1.XXX` con la IP del servidor)

## ⚙️ Opciones Avanzadas

### Deshabilitar SSL/TLS (solo para testing)

**Servidor:**
```bash
python server/server.py --disable-ssl
```

**Cliente:**
```bash
python client/client.py --disable-ssl
```

### Ver Configuración Actual

```bash
python server/server.py --show-config
```

### Cambiar la Contraseña

```bash
python server/server.py --password mi_contraseña_segura
```

### Usar Puerto Diferente

```bash
python server/server.py --port 8888
python client/client.py --port 8888
```

## 🔐 Configuración Permanente

Crea un archivo `.env` en la raíz del proyecto:

```bash
CHAT_HOST=0.0.0.0
CHAT_PORT=5555
CHAT_SERVER_PASSWORD=mi_contraseña_super_segura
CHAT_ENABLE_SSL=True
CHAT_RSA_KEY_SIZE=4096
```

Luego simplemente ejecuta:
```bash
python server/server.py
python client/client.py
```

## 🛠️ Solución de Problemas Comunes

### "Certificado SSL no encontrado"
```bash
python scripts/generate_ssl_certificates.py
```

### "Puerto en uso"
```bash
python server/server.py --port 5556
```

### Cliente no puede conectar
- Verifica que el servidor esté corriendo
- Verifica firewall
- Verifica que ambos usen la misma configuración SSL

## 📚 Más Información

- README completo: `README.md`
- Configuración avanzada: `config.py`
- Documentación SSL/TLS: https://docs.python.org/3/library/ssl.html

## 💡 Tips

1. **Desarrollo**: Los certificados autofirmados son perfectos
2. **Producción**: Usa Let's Encrypt u otra CA confiable
3. **LAN**: Los certificados autofirmados funcionan bien
4. **Seguridad**: Siempre usa contraseñas fuertes
5. **Rendimiento**: RSA-2048 es más rápido, RSA-4096 más seguro

---

**¿Necesitas ayuda?** Revisa el README.md o la sección de Solución de Problemas.

