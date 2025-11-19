"""
Servidor de chat con autenticación básica y difusión de mensajes.
Mantiene múltiples clientes usando ThreadPoolExecutor y manejo seguro de recursos.
"""

import socket
import ssl
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
        max_clients: int | None = None,
        enable_ssl: bool | None = None
    ) -> None:
        """Inicializa el servidor de chat."""
        self.host = host or Config.DEFAULT_HOST
        self.port = port or Config.DEFAULT_PORT
        self.password = password or Config.SERVER_PASSWORD
        self.max_clients = max_clients or Config.MAX_CLIENTS
        self.buffer_size = Config.BUFFER_SIZE
        self.enable_ssl = enable_ssl if enable_ssl is not None else Config.ENABLE_SSL
        
        self.rsa_crypto = RSACrypto()
        self.inicializar_claves_rsa()

        # Crear socket base
        base_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        base_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            import resource
            resource.setrlimit(resource.RLIMIT_NOFILE, (self.max_clients, self.max_clients))
        except Exception as e:
            logging.warning(f"No se pudo ajustar el límite de archivos: {e}")

        base_server.bind((self.host, self.port))
        base_server.listen(self.max_clients)
        self.port = base_server.getsockname()[1]

        # Configurar SSL/TLS si está habilitado
        if self.enable_ssl:
            self.ssl_context = self._configurar_ssl()
            self.server = base_server
        else:
            self.server = base_server
            self.ssl_context = None

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
        if self.enable_ssl:
            logging.info(f"🔐 SSL/TLS habilitado (TLS 1.2+)")
        else:
            logging.warning(f"⚠️  SSL/TLS deshabilitado")

    def _configurar_ssl(self) -> ssl.SSLContext:
        """Configura el contexto SSL/TLS para el servidor."""
        try:
            if not Config.SSL_CERT_PATH.exists():
                logging.error(f"❌ Certificado SSL no encontrado: {Config.SSL_CERT_PATH}")
                raise FileNotFoundError(f"Certificado SSL no encontrado: {Config.SSL_CERT_PATH}")
            
            if not Config.SSL_KEY_PATH.exists():
                logging.error(f"❌ Clave privada SSL no encontrada: {Config.SSL_KEY_PATH}")
                raise FileNotFoundError(f"Clave privada SSL no encontrada: {Config.SSL_KEY_PATH}")
            
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.options |= ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1
            context.minimum_version = ssl.TLSVersion.TLSv1_2
            
            context.load_cert_chain(
                certfile=str(Config.SSL_CERT_PATH),
                keyfile=str(Config.SSL_KEY_PATH)
            )
            
            context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS')
            
            if Config.SSL_VERIFY_CLIENT and Config.SSL_CA_CERT_PATH:
                context.verify_mode = ssl.CERT_REQUIRED
                context.load_verify_locations(cafile=str(Config.SSL_CA_CERT_PATH))
            else:
                context.verify_mode = ssl.CERT_NONE
            
            return context
            
        except Exception as e:
            logging.error(f"❌ Error configurando SSL: {e}")
            raise

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
                logging.info(f"✅ Nuevas claves RSA generadas")
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
                    logging.error(f"❌ Error enviando a {nickname}: {e}")
                    self.desconectar_cliente(client)
        except Exception as e:
            logging.error(f"❌ Error en broadcast: {e}")

    def manejar_cliente(self, client: socket.socket, address: tuple[str, int]) -> None:
        """Gestiona la sesión de un cliente."""
        nickname: str | None = None
        try:
            # 1. Notificar que estamos listos para intercambiar claves
            client.send(b'PUBLIC_KEY_READY\n')
            
            # 2. Solicitar clave pública del cliente
            client.send(b'CLIENT_PUBLIC_KEY\n')
            
            # 3. Recibir clave pública del cliente (PEM completo en Base64)
            client_public_key_b64 = client.recv(self.buffer_size).decode('utf-8').strip()
            
            # Decodificar: el cliente envía el PEM completo (con headers) en Base64
            import base64
            try:
                client_public_key_pem = base64.b64decode(client_public_key_b64)
                logging.debug(f"✅ Clave pública recibida ({len(client_public_key_pem)} bytes)")
                logging.debug(f"📄 PEM: {client_public_key_pem[:50]}...")
            except Exception as e:
                logging.error(f"❌ Error decodificando clave pública Base64: {e}")
                client.send(b'AUTH_FAILED\n')
                client.close()
                return
            
            # 4. Solicitar nickname
            client.send(b'NICK\n')
            nickname_cifrado = client.recv(self.buffer_size).decode('utf-8').strip()
            nickname = self.rsa_crypto.descifrar(nickname_cifrado)
            logging.debug(f"✅ Nickname descifrado: {nickname}")

            # 5. Solicitar contraseña
            client.send(b'PASSWORD\n')
            password_cifrado = client.recv(self.buffer_size).decode('utf-8').strip()
            recv_password = self.rsa_crypto.descifrar(password_cifrado)

            # 6. Verificar contraseña
            if recv_password != self.password:
                client.send(b'AUTH_FAILED\n')
                logging.warning(f"⚠️  Autenticación fallida para {nickname}")
                client.close()
                return

            # 7. Verificar capacidad del servidor
            with self.global_lock:
                if len(self.clients) >= self.max_clients:
                    client.send(b'SERVIDOR_LLENO\n')
                    client.close()
                    return
                self.clients[client] = (nickname, client_public_key_pem)

            # 8. Confirmar autenticación exitosa
            client.send(b'AUTH_SUCCESS\n')
            logging.info(f"👤 {nickname} se conectó desde {address}")
            self.broadcast(f'📢 {nickname} se unió al chat!', sender=None)

            # 9. Loop principal de mensajes
            while True:
                data = client.recv(self.buffer_size)
                if not data:
                    break

                raw = data.decode('utf-8').strip()
                mensaje_descifrado = None
                
                # Intentar parsear formato: cipher|hash|md5
                if '|' in raw:
                    parts = raw.split('|')
                    if len(parts) == 3:
                        cipher, recv_hash, recv_md5 = parts
                        
                        try:
                            mensaje_descifrado = self.rsa_crypto.descifrar(cipher)
                            
                            # Verificar integridad
                            import hashlib
                            calc_hash = hashlib.sha256(mensaje_descifrado.encode('utf-8')).hexdigest()
                            calc_md5 = hashlib.md5(mensaje_descifrado.encode('utf-8')).hexdigest()
                            
                            if recv_hash != calc_hash or recv_md5 != calc_md5:
                                logging.warning(f"⚠️  Hash inválido de {nickname}")
                                continue
                            
                            logging.debug(f"✅ Mensaje verificado (MD5: {recv_md5[:8]}...)")
                            
                        except Exception as e:
                            logging.warning(f"❌ Error descifrando de {nickname}: {e}")
                            continue
                    else:
                        # Formato incorrecto, intentar descifrar directamente
                        try:
                            mensaje_descifrado = self.rsa_crypto.descifrar(raw)
                        except Exception as e:
                            logging.warning(f"❌ No se pudo descifrar de {nickname}: {e}")
                            continue
                else:
                    # Sin pipes, intentar descifrar directamente (retrocompatibilidad)
                    try:
                        # Intentar JSON (formato antiguo)
                        parsed = json.loads(raw)
                        if isinstance(parsed, dict) and 'cipher' in parsed:
                            cipher = parsed['cipher']
                            mensaje_descifrado = self.rsa_crypto.descifrar(cipher)
                        else:
                            mensaje_descifrado = self.rsa_crypto.descifrar(raw)
                    except json.JSONDecodeError:
                        try:
                            mensaje_descifrado = self.rsa_crypto.descifrar(raw)
                        except Exception as e:
                            logging.warning(f"❌ No se pudo descifrar de {nickname}: {e}")
                            continue

                if mensaje_descifrado:
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
                logging.info(f"🚪 {nickname} se desconectó")
                self.broadcast(f'📢 {nickname} abandonó el chat', sender=None)

    def iniciar(self) -> None:
        """Inicia el bucle de aceptación de conexiones."""
        try:
            display_host = self.local_ip if self.host == '0.0.0.0' else self.host
            protocol = "TLS" if self.enable_ssl else "TCP"
            logging.info(f"✅ Esperando conexiones {protocol} en {display_host}:{self.port}")
            
            while True:
                client, address = self.server.accept()
                
                # Envolver con SSL si está habilitado
                if self.enable_ssl and self.ssl_context:
                    try:
                        client = self.ssl_context.wrap_socket(client, server_side=True)
                        logging.debug(f"🔐 Conexión SSL con {address}")
                    except ssl.SSLError as e:
                        logging.warning(f"⚠️  Error SSL con {address}: {e}")
                        try:
                            client.close()
                        except:
                            pass
                        continue
                
                self.thread_pool.submit(self.manejar_cliente, client, address)
        except KeyboardInterrupt:
            logging.info("🛑 Servidor detenido")
        finally:
            self.thread_pool.shutdown(wait=True)
            self.server.close()


def main() -> None:
    """Punto de entrada para iniciar el servidor de chat."""
    if '--show-config' in sys.argv:
        Config.display_config()
        return
    
    import argparse
    parser = argparse.ArgumentParser(description='Servidor de chat con cifrado RSA y SSL/TLS')
    parser.add_argument('--host', type=str, help=f'Host (default: {Config.DEFAULT_HOST})')
    parser.add_argument('--port', type=int, help=f'Puerto (default: {Config.DEFAULT_PORT})')
    parser.add_argument('--password', type=str, help='Contraseña del servidor')
    parser.add_argument('--max-clients', type=int, help=f'Máximo de clientes (default: {Config.MAX_CLIENTS})')
    parser.add_argument('--enable-ssl', action='store_true', help='Habilitar SSL/TLS')
    parser.add_argument('--disable-ssl', action='store_true', help='Deshabilitar SSL/TLS')
    
    args = parser.parse_args()
    
    enable_ssl = None
    if args.enable_ssl:
        enable_ssl = True
    elif args.disable_ssl:
        enable_ssl = False
    
    server = ChatServer(
        host=args.host,
        port=args.port,
        password=args.password,
        max_clients=args.max_clients,
        enable_ssl=enable_ssl
    )
    server.iniciar()


if __name__ == "__main__":
    main()