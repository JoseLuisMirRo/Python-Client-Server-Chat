"""
Servidor de chat con autenticación básica y difusión de mensajes.
Mantiene múltiples clientes usando ThreadPoolExecutor y manejo seguro de recursos.
"""

import socket
import threading
import traceback
import logging
import multiprocessing
from concurrent.futures import ThreadPoolExecutor

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
            password: Contraseña requerida para clientes.
            max_clients: Límite de clientes simultáneos.
        """
        self.host = host
        self.port = port
        self.password = password
        self.max_clients = max_clients

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

        # Gestión de clientes
        self.clients: dict[socket.socket, str] = {}
        self.thread_pool = ThreadPoolExecutor(max_workers=max_clients, thread_name_prefix="ChatClientThread")
        self.global_lock = threading.Lock()

        logging.info(f"🌐 Servidor de chat iniciado en {self.host}:{self.port}")
        if self.host == '0.0.0.0':
            logging.info(f"🔗 Conéctate desde otros dispositivos: {self.local_ip}:{self.port}")
        logging.info(f"🔐 Contraseña del servidor: {self.password or 'Sin contraseña'}")
        logging.info(f"📊 Máximo de clientes: {self.max_clients}")

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

    def broadcast(self, message: bytes, sender: socket.socket | None = None) -> None:
        """Envía un mensaje a todos los clientes excepto al remitente."""
        try:
            with self.global_lock:
                clients_copy = list(self.clients.keys())
            for client in clients_copy:
                if client is sender:
                    continue
                try:
                    client.send(message)
                except Exception as e:
                    logging.error(f"❌ Error enviando mensaje: {e}")
                    self.desconectar_cliente(client)
        except Exception as e:
            logging.error(f"❌ Error en broadcast: {e}")

    def manejar_cliente(self, client: socket.socket, address: tuple[str, int]) -> None:
        """Gestiona la sesión de un cliente, incluida la autenticación y mensajería."""
        nickname: str | None = None
        try:
            # Solicitar nickname
            client.send(b'NICK')
            nickname = client.recv(1024).decode('utf-8').strip()

            # Solicitar contraseña
            client.send(b'PASSWORD')
            recv_password = client.recv(1024).decode('utf-8').strip()

            # Validar contraseña
            if recv_password != self.password:
                client.send(b'AUTH_FAILED')
                client.close()
                return

            # Registrar y confirmar
            client.send(b'AUTH_SUCCESS')
            with self.global_lock:
                if len(self.clients) >= self.max_clients:
                    client.send(b'SERVIDOR_LLENO')
                    client.close()
                    return
                self.clients[client] = nickname

            logging.info(f"👤 {nickname} se conectó desde {address}")
            self.broadcast(f'📢 {nickname} se unió al chat!'.encode('utf-8'))

            # Bucle principal de mensajes
            while True:
                data = client.recv(1024)
                if not data:
                    break
                decoded = data.decode('utf-8').strip()
                logging.info(f"💬 {nickname}: {decoded}")
                self.broadcast(f'👤 {nickname}: {decoded}'.encode('utf-8'), sender=client)

        except Exception as e:
            logging.error(f"❌ Error con {nickname or 'Cliente desconocido'}: {e}")
            logging.debug(traceback.format_exc())
        finally:
            self.desconectar_cliente(client)

    def desconectar_cliente(self, client: socket.socket) -> None:
        """Desconecta un cliente y notifica al resto."""
        with self.global_lock:
            if client in self.clients:
                nickname = self.clients.pop(client)
                try:
                    client.close()
                except Exception:
                    pass
                logging.info(f"🚪 {nickname} se desconectó del chat")
                self.broadcast(f'📢 {nickname} abandonó el chat'.encode('utf-8'))

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