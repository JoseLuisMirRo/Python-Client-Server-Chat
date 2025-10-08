# Cliente-Servidor Chat en Python con Cifrado AES

## Instalación de dependencias
```bash
pip install -r requirements.txt
```

## Características
- **Cifrado AES-256-GCM**: Todos los mensajes se cifran usando criptografía simétrica AES
- **Autenticación segura**: Nickname y contraseña se transmiten cifrados
- **Claves derivadas**: Las claves se derivan de la contraseña del servidor usando PBKDF2
- **Comunicación segura**: Todos los mensajes del chat están cifrados end-to-end
- **Autenticación de integridad**: GCM proporciona autenticación además de cifrado

## Instrucciones (misma máquina)
1. Primero, ejecuta el servidor:
	- `python server/server.py`
2. Luego, en ventanas separadas, ejecuta los clientes:
	- `python client/client.py`

## Funcionamiento
- El servidor genera una clave AES derivada de la contraseña del servidor
- Los clientes deben ingresar la misma contraseña para sincronizar las claves
- El nickname y contraseña se envían cifrados con AES-256-GCM
- Todos los mensajes del chat se cifran antes de la transmisión
- Los mensajes se descifran automáticamente al recibirse
- Cada mensaje incluye su propio nonce para máxima seguridad

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