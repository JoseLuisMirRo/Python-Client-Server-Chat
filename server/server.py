"""
Servidor de chat con autenticación básica y difusión de mensajes.
Mantiene múltiples clientes usando ThreadPoolExecutor y manejo seguro de recursos.
"""

import socket
import threading
import traceback
import logging
import multiprocessing
import os
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from crypto.rsa_crypto import RSACrypto
from cryptography.hazmat.primitives import serialization

try:
    from colorama import init as colorama_init
    colorama_init(autoreset=True)
except Exception:
    # Colorama es opcional; si no está disponible, continuamos sin colores.
    pass

# Aumentar límite de threads (opcional)
threading.stack_size(67108864)  # 64MB de stack por thread

# Método de inicio seguro para multiprocessing
try:
    multiprocessing.set_start_method('fork')
except RuntimeError:
    # Ya fue establecido en otro lugar; ignorar
    pass

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


class ChatServer:
    """Servidor de chat TCP con autenticación por contraseña.

    Protocolo simple con mensajes de control:
    - 'NICK' para solicitar nombre de usuario
    - 'PASSWORD' para solicitar contraseña
    - 'AUTH_SUCCESS'/'AUTH_FAILED' para indicar resultado de autenticación
    - Mensajes normales se difunden al resto de clientes
    """

    def __init__(self, host: str = 'localhost', port: int = 0, password: str | None = None, max_clients: int = 500) -> None:
        """Inicializa el servidor de chat.

        Args:
            host: Dirección donde escuchar.
            port: Puerto (0 para asignación automática del SO).
            password: Contraseña requerida para.
            max_clients: Límite de clientes simultáneos.
        """
        self.host = host
        self.port = port
        self.password = password
        self.max_clients = max_clients
        
        # Inicializar cifrado RSA
        self.rsa_crypto = RSACrypto()
        self.inicializar_claves_rsa()

        # Configurar socket
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Intentar aumentar límites del sistema (opcional)
        try:
            import resource
            resource.setrlimit(resource.RLIMIT_NOFILE, (max_clients, max_clients))
        except Exception as e:
            logging.warning(f"No se pudo ajustar el límite de archivos: {e}")

        self.server.bind((self.host, self.port))
        self.server.listen(max_clients)
        self.port = self.server.getsockname()[1]

        # Detectar IP local para mostrar a los clientes de la misma red
        self.local_ip = self._descubrir_ip_local()

        # Gestión de clientes - guardar nickname y clave pública de cada cliente
        self.clients: dict[socket.socket, tuple[str, bytes]] = {}  # {socket: (nickname, public_key_pem)}
        self.thread_pool = ThreadPoolExecutor(max_workers=max_clients, thread_name_prefix="ChatClientThread")
        self.global_lock = threading.Lock()

        logging.info(f"🌐 Servidor de chat iniciado en {self.host}:{self.port}")
        if self.host == '0.0.0.0':
            logging.info(f"🔗 Conéctate desde otros dispositivos: {self.local_ip}:{self.port}")
        logging.info(f"🔐 Contraseña del servidor: {self.password or 'Sin contraseña'}")
        logging.info("🔒 Cifrado RSA habilitado")

    def _descubrir_ip_local(self) -> str:
        """Intenta descubrir la IP local preferida para conexiones LAN.

        Método no intrusivo: abre un socket UDP a un destino externo (no envía datos)
        para obtener la IP de salida. Si falla, recurre al hostname o localhost.
        """
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                s.connect(('8.8.8.8', 80))
                return s.getsockname()[0]
            finally:
                s.close()
        except Exception:
            try:
                return socket.gethostbyname(socket.gethostname())
            except Exception:
                return '127.0.0.1'

    def inicializar_claves_rsa(self) -> None:
        """Inicializa las claves RSA del servidor."""
        private_key_path = "server_private_key.pem"
        public_key_path = "server_public_key.pem"
        
        try:
            # Intentar cargar claves existentes
            if os.path.exists(private_key_path) and os.path.exists(public_key_path):
                self.rsa_crypto.cargar_claves_desde_archivo(private_key_path, public_key_path)
                logging.info("✅ Claves RSA cargadas desde archivos existentes")
            else:
                # Generar nuevas claves
                self.rsa_crypto.generar_par_claves()
                self.rsa_crypto.guardar_claves(private_key_path, public_key_path)
                logging.info("✅ Nuevas claves RSA generadas y guardadas")
                
        except Exception as e:
            logging.error(f"❌ Error inicializando claves RSA: {e}")
            raise

    def broadcast(self, message: str, sender: socket.socket | None = None) -> None:
        """Envía un mensaje cifrado a todos los clientes excepto al remitente."""
        try:
            with self.global_lock:
                clients_copy = dict(self.clients)  # Copia de {socket: (nickname, public_key_pem)}
            
            for client, (nickname, public_key_pem) in clients_copy.items():
                if client is sender:
                    continue
                try:
                    # Crear RSACrypto temporal para este cliente
                    client_rsa = RSACrypto()
                    client_rsa.cargar_clave_publica(public_key_pem)
                    
                    # Cifrar mensaje con la clave pública del cliente
                    mensaje_cifrado = client_rsa.cifrar(message)
                    client.send(f'{mensaje_cifrado}\n'.encode('utf-8'))
                except Exception as e:
                    logging.error(f"❌ Error enviando mensaje a {nickname}: {e}")
                    self.desconectar_cliente(client)
        except Exception as e:
            logging.error(f"❌ Error en broadcast: {e}")

    def manejar_cliente(self, client: socket.socket, address: tuple[str, int]) -> None:
        """Gestiona la sesión de un cliente, incluida la autenticación y mensajería."""
        nickname: str | None = None
        try:
            # Informar al cliente sobre la clave pública
            client.send(b'PUBLIC_KEY_READY\n')
            
            # Solicitar clave pública del cliente
            client.send(b'CLIENT_PUBLIC_KEY\n')
            client_public_key_data = client.recv(4096)
            import base64
            client_public_key_pem = base64.b64decode(client_public_key_data.decode('utf-8').strip())
            logging.info("Clave pública del cliente recibida")
            
            # Solicitar nickname (cifrado)
            client.send(b'NICK\n')
            nickname_cifrado = client.recv(4096)
            nickname = self.rsa_crypto.descifrar(nickname_cifrado.decode('utf-8'))

            # Solicitar contraseña (cifrada)
            client.send(b'PASSWORD\n')
            password_cifrado = client.recv(4096)
            recv_password = self.rsa_crypto.descifrar(password_cifrado.decode('utf-8'))

            # Validar contraseña
            if recv_password != self.password:
                client.send(b'AUTH_FAILED\n')
                client.close()
                return

            # Registrar y confirmar
            client.send(b'AUTH_SUCCESS\n')
            with self.global_lock:
                if len(self.clients) >= self.max_clients:
                    client.send(b'SERVIDOR_LLENO')
                    client.close()
                    return
                # Guardar nickname Y clave pública del cliente
                self.clients[client] = (nickname, client_public_key_pem)

            logging.info(f"👤 {nickname} se conectó desde {address}")
            mensaje_union = f'📢 {nickname} se unió al chat!'
            # Broadcast cifrado con la clave pública de cada cliente
            self.broadcast(mensaje_union, sender=None)

            # Bucle principal de mensajes
            while True:
                data = client.recv(4096)  # Aumentado para RSA
                if not data:
                    break
                
                # Descifrar mensaje
                mensaje_cifrado = data.decode('utf-8')
                mensaje_descifrado = self.rsa_crypto.descifrar(mensaje_cifrado)
                
                logging.info(f"💬 {nickname}: {mensaje_descifrado}")
                
                # Broadcast cifrado para cada cliente con su clave pública
                mensaje_broadcast = f'👤 {nickname}: {mensaje_descifrado}'
                self.broadcast(mensaje_broadcast, sender=client)

        except Exception as e:
            logging.error(f"❌ Error con {nickname or 'Cliente desconocido'}: {e}")
            logging.debug(traceback.format_exc())
        finally:
            self.desconectar_cliente(client)

    def desconectar_cliente(self, client: socket.socket) -> None:
        """Desconecta un cliente y notifica al resto."""
        with self.global_lock:
            if client in self.clients:
                nickname, _ = self.clients.pop(client)
                try:
                    client.close()
                except Exception:
                    pass
                logging.info(f"🚪 {nickname} se desconectó del chat")
                mensaje_desconexion = f'📢 {nickname} abandonó el chat'
                # Broadcast cifrado
                self.broadcast(mensaje_desconexion, sender=None)

    def iniciar(self) -> None:
        """Inicia el bucle de aceptación de conexiones y delega en el pool de hilos."""
        try:
            display_host = self.local_ip if self.host == '0.0.0.0' else self.host
            if self.host == '0.0.0.0':
                logging.info(f"✅ Esperando conexiones en {display_host}:{self.port} (escuchando en {self.host})")
            else:
                logging.info(f"✅ Esperando conexiones en {display_host}:{self.port}")
            while True:
                client, address = self.server.accept()
                self.thread_pool.submit(self.manejar_cliente, client, address)
        except KeyboardInterrupt:
            logging.info("🛑 Servidor detenido")
        except Exception as e:
            logging.error(f"❌ Error crítico del servidor: {e}")
            logging.debug(traceback.format_exc())
        finally:
            self.thread_pool.shutdown(wait=True)
            self.server.close()


def main() -> None:
    """Punto de entrada para iniciar el servidor de chat.

    Se configura para escuchar en todas las interfaces (0.0.0.0) y un puerto fijo (5555)
    para facilitar conexiones desde otros dispositivos en la red local.
    """
    server = ChatServer(host="0.0.0.0", port=5555, password="secreto")
    server.iniciar()


if __name__ == "__main__":
    main()