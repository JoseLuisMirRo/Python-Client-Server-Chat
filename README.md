# Cliente-Servidor Chat en Python

## Instrucciones (misma máquina)
1. Primero, ejecuta el servidor:
	- `python server/server.py`
2. Luego, en ventanas separadas, ejecuta los clientes:
	- `python client/client.py`

## Funcionamiento
- El servidor arroja el puerto en el que se está corriendo 
- Cada cliente elige un nickname al conectarse
- Existe una contraseña predefinida a nivel código fuente en el servidor
- Los mensajes se transmiten a todos los clientes conectados

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