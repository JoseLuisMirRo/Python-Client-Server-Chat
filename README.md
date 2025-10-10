# Cliente-Servidor Chat en Python con Cifrado RSA

## Instalación de dependencias
```bash
pip install -r requirements.txt
```

## Características
- **Cifrado RSA**: Todos los mensajes se cifran usando criptografía asimétrica RSA
- **Autenticación segura**: Nickname y contraseña se transmiten cifrados
- **Claves automáticas**: El servidor genera automáticamente un par de claves RSA
- **Comunicación segura**: Todos los mensajes del chat están cifrados end-to-end

## Instrucciones (misma máquina)
1. Primero, ejecuta el servidor:
	- `python server/server.py`
2. Luego, en ventanas separadas, ejecuta los clientes:
	- `python client/client.py`

## Funcionamiento
- El servidor genera automáticamente un par de claves RSA al iniciar
- Cada cliente recibe la clave pública del servidor al conectarse
- El nickname y contraseña se envían cifrados con RSA
- Todos los mensajes del chat se cifran antes de la transmisión
- Los mensajes se descifran automáticamente al recibirse

## Conexión desde otros dispositivos (misma red LAN)
El servidor está configurado para escuchar en todas las interfaces (0.0.0.0) en el puerto fijo 5555.

Pasos:
1. En la máquina del servidor, inicia el servidor:
	- `python server/server.py`
2. Obtén la IP local del servidor (ejemplos en macOS):
	- `ipconfig getifaddr en0` (Wi‑Fi) o `ipconfig getifaddr en1` (Ethernet)
	- Alternativa: `ifconfig | grep inet` y toma la IP de tu interfaz activa
3. En cada cliente (otro equipo o el mismo), ejecuta:
	- `python client/client.py`
	- Cuando te pida, ingresa la IP del servidor y el puerto 5555

Notas:
- Asegúrate de que el firewall del servidor permita conexiones entrantes al puerto 5555.
- Todos los dispositivos deben estar en la misma red (por ejemplo, conectados al mismo router Wi‑Fi).
- La contraseña del servidor es "secreto" por defecto; puedes cambiarla en `server/server.py`.

## 🔍 Verificación de Integridad (MD5)

**Versión**: 1.0.0 - Rama `cifrado-asimetrico`

Para verificar la integridad de los archivos principales del proyecto, compara los siguientes checksums MD5:

### Checksums de Archivos Principales

```bash
# Servidor
MD5 (server/server.py) = f01372c816011aad464ea8501a575b2e

# Cliente
MD5 (client/client.py) = 085318b57d96c898ea81319dad4c9987

# Módulo de Cifrado RSA
MD5 (crypto/rsa_crypto.py) = f639f6651b5b0837eda3d67900c10062
```

### Verificar Checksums

Para verificar manualmente la integridad de los archivos en macOS/Linux:

```bash
md5 server/server.py client/client.py crypto/rsa_crypto.py
```

Si los checksums no coinciden, los archivos pueden haber sido modificados. Para restaurar la versión original:

```bash
git checkout server/server.py
git checkout client/client.py
git checkout crypto/rsa_crypto.py
```

---

**Última actualización**: Octubre 2025