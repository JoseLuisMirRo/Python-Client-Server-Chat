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
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crypto.rsa_crypto import RSACrypto
from cryptography.hazmat.primitives import serialization
from config import Config

try:
    from colorama import init as colorama_init
    colorama_init(autoreset=True)
except Exception:
    pass

threading.stack_size(Config.THREAD_STACK_SIZE)

try:
    if hasattr(multiprocessing, "set_start_method"):
        metodo = "fork" if hasattr(os, "fork") else "spawn"
        multiprocessing.set_start_method(metodo, force=True)
except RuntimeError:
    pass

logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format=Config.LOG_FORMAT,
    datefmt=Config.LOG_DATE_FORMAT
)


class ChatServer:
    """Servidor de chat TCP con autenticación por contraseña."""

    def __init__(
        self, 
        host: str | None = None, 
        port: int | None = None, 
        password: str | None = None, 
        max_clients: int | None = None
    ) -> None:
        """Inicializa el servidor de chat.

        Args:
            host: Dirección donde escuchar (usa Config.DEFAULT_HOST si es None).
            port: Puerto (usa Config.DEFAULT_PORT si es None).
            password: Contraseña requerida (usa Config.SERVER_PASSWORD si es None).
            max_clients: Límite de clientes simultáneos (usa Config.MAX_CLIENTS si es None).
        """
        self.host = host or Config.DEFAULT_HOST
        self.port = port or Config.DEFAULT_PORT
        self.password = password or Config.SERVER_PASSWORD
        self.max_clients = max_clients or Config.MAX_CLIENTS
        self.buffer_size = Config.BUFFER_SIZE
        
        self.rsa_crypto = RSACrypto()
        self.inicializar_claves_rsa()

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            import resource
            resource.setrlimit(resource.RLIMIT_NOFILE, (self.max_clients, self.max_clients))
        except Exception as e:
            logging.warning(f"No se pudo ajustar el límite de archivos: {e}")

        self.server.bind((self.host, self.port))
        self.server.listen(self.max_clients)
        self.port = self.server.getsockname()[1]

        self.local_ip = self._descubrir_ip_local()

        self.clients: dict[socket.socket, tuple[str, bytes]] = {}
        self.thread_pool = ThreadPoolExecutor(
            max_workers=self.max_clients, 
            thread_name_prefix="ChatClientThread"
        )
        self.global_lock = threading.Lock()

        logging.info(f"🌐 Servidor de chat iniciado en {self.host}:{self.port}")
        if self.host == '0.0.0.0':
            logging.info(f"🔗 Conéctate desde otros dispositivos: {self.local_ip}:{self.port}")
        logging.info(f"🔐 Contraseña del servidor: {'*' * len(self.password)}")
        logging.info(f"🔒 Cifrado RSA habilitado ({Config.RSA_KEY_SIZE} bits)")

    def _descubrir_ip_local(self) -> str:
        """Descubre la IP local para conexiones LAN."""
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
        private_key_path = str(Config.SERVER_PRIVATE_KEY_PATH)
        public_key_path = str(Config.SERVER_PUBLIC_KEY_PATH)
        
        try:
            if os.path.exists(private_key_path) and os.path.exists(public_key_path):
                self.rsa_crypto.cargar_claves_desde_archivo(private_key_path, public_key_path)
                logging.info(f"✅ Claves RSA cargadas desde {public_key_path}")
            else:
                self.rsa_crypto.generar_par_claves(key_size=Config.RSA_KEY_SIZE)
                self.rsa_crypto.guardar_claves(private_key_path, public_key_path)
                logging.info(f"✅ Nuevas claves RSA generadas y guardadas en {public_key_path}")
        except Exception as e:
            logging.error(f"❌ Error inicializando claves RSA: {e}")
            raise

    def broadcast(self, message: str, sender: socket.socket | None = None) -> None:
        """Envía un mensaje cifrado a todos los clientes excepto al remitente."""
        try:
            with self.global_lock:
                clients_copy = dict(self.clients)
            
            for client, (nickname, public_key_pem) in clients_copy.items():
                if client is sender:
                    continue
                try:
                    client_rsa = RSACrypto()
                    client_rsa.cargar_clave_publica(public_key_pem)
                    mensaje_cifrado = client_rsa.cifrar(message)
                    client.send(f'{mensaje_cifrado}\n'.encode('utf-8'))
                except Exception as e:
                    logging.error(f"❌ Error enviando mensaje a {nickname}: {e}")
                    self.desconectar_cliente(client)
        except Exception as e:
            logging.error(f"❌ Error en broadcast: {e}")

    def manejar_cliente(self, client: socket.socket, address: tuple[str, int]) -> None:
        """Gestiona la sesión de un cliente."""
        nickname: str | None = None
        try:
            client.send(b'PUBLIC_KEY_READY\n')
            
            client.send(b'CLIENT_PUBLIC_KEY\n')
            client_public_key_data = client.recv(self.buffer_size)
            import base64
            client_public_key_pem = base64.b64decode(client_public_key_data.decode('utf-8').strip())
            logging.debug("Clave pública del cliente recibida")
            
            client.send(b'NICK\n')
            nickname_cifrado = client.recv(self.buffer_size)
            nickname = self.rsa_crypto.descifrar(nickname_cifrado.decode('utf-8'))

            client.send(b'PASSWORD\n')
            password_cifrado = client.recv(self.buffer_size)
            recv_password = self.rsa_crypto.descifrar(password_cifrado.decode('utf-8'))

            if recv_password != self.password:
                client.send(b'AUTH_FAILED\n')
                client.close()
                return

            client.send(b'AUTH_SUCCESS\n')
            with self.global_lock:
                if len(self.clients) >= self.max_clients:
                    client.send(b'SERVIDOR_LLENO')
                    client.close()
                    return
                self.clients[client] = (nickname, client_public_key_pem)

            logging.info(f"👤 {nickname} se conectó desde {address}")
            self.broadcast(f'📢 {nickname} se unió al chat!', sender=None)

            while True:
                data = client.recv(self.buffer_size)
                if not data:
                    break

                raw = data.decode('utf-8')
                mensaje_descifrado = None
                
                try:
                    parsed = json.loads(raw)
                    if isinstance(parsed, dict) and all(k in parsed for k in ['cipher', 'hash', 'md5']):
                        cipher = parsed['cipher']
                        recv_hash = parsed['hash']
                        recv_md5 = parsed['md5']
                        
                        try:
                            mensaje_descifrado = self.rsa_crypto.descifrar(cipher)
                        except Exception as e:
                            logging.warning(f"❌ No se pudo descifrar mensaje de {nickname}: {e}")
                            continue

                        import hashlib
                        calc_hash = hashlib.sha256(mensaje_descifrado.encode('utf-8')).hexdigest()
                        calc_md5 = hashlib.md5(mensaje_descifrado.encode('utf-8')).hexdigest()
                        
                        if recv_hash != calc_hash or recv_md5 != calc_md5:
                            logging.warning(f"⚠️ Hash inválido de {nickname}. Mensaje descartado.")
                            continue
                        
                        logging.debug(f"🔒 MD5 verificado: {recv_md5}")
                    else:
                        mensaje_descifrado = self.rsa_crypto.descifrar(raw)
                except json.JSONDecodeError:
                    try:
                        mensaje_descifrado = self.rsa_crypto.descifrar(raw)
                    except Exception as e:
                        logging.warning(f"❌ No se pudo descifrar mensaje de {nickname}: {e}")
                        continue

                if mensaje_descifrado is None:
                    continue

                logging.info(f"💬 {nickname}: {mensaje_descifrado}")
                self.broadcast(f'👤 {nickname}: {mensaje_descifrado}', sender=client)

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
                self.broadcast(f'📢 {nickname} abandonó el chat', sender=None)

    def iniciar(self) -> None:
        """Inicia el bucle de aceptación de conexiones."""
        try:
            display_host = self.local_ip if self.host == '0.0.0.0' else self.host
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
    """Punto de entrada para iniciar el servidor de chat."""
    if '--show-config' in sys.argv:
        Config.display_config()
        return
    
    import argparse
    parser = argparse.ArgumentParser(description='Servidor de chat con cifrado RSA')
    parser.add_argument('--host', type=str, help=f'Host (default: {Config.DEFAULT_HOST})')
    parser.add_argument('--port', type=int, help=f'Puerto (default: {Config.DEFAULT_PORT})')
    parser.add_argument('--password', type=str, help='Contraseña del servidor')
    parser.add_argument('--max-clients', type=int, help=f'Máximo de clientes (default: {Config.MAX_CLIENTS})')
    parser.add_argument('--show-config', action='store_true', help='Mostrar configuración y salir')
    
    args = parser.parse_args()
    
    server = ChatServer(
        host=args.host,
        port=args.port,
        password=args.password,
        max_clients=args.max_clients
    )
    server.iniciar()


if __name__ == "__main__":
    main()