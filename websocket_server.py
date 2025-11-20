#!/usr/bin/env python3
"""
Servidor WebSocket - Puente entre navegador web y servidor TCP de chat.
Maneja el protocolo de autenticación y retransmite mensajes.
"""
import asyncio
import websockets
import socket
import ssl
import logging
import sys
import os
from pathlib import Path

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s'
)


class WebSocketChatBridge:
    """Puente entre WebSocket (navegador) y TCP (servidor de chat)."""
    
    def __init__(self):
        self.chat_host = Config.DEFAULT_HOST
        self.chat_port = Config.DEFAULT_PORT
        self.ws_port = 5002
        self.buffer_size = Config.BUFFER_SIZE
        self.enable_ssl = Config.ENABLE_SSL
        
    def _create_ssl_context(self):
        """Crea contexto SSL para conexión con el servidor de chat."""
        if not self.enable_ssl:
            return None
            
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        return context
    
    async def connect_to_chat_server(self):
        """Establece conexión TCP/SSL con el servidor de chat."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((self.chat_host, self.chat_port))
            logging.info(f"✅ Conectado a {self.chat_host}:{self.chat_port}")
            
            if self.enable_ssl:
                ssl_context = self._create_ssl_context()
                sock = ssl_context.wrap_socket(sock, server_hostname=self.chat_host)
                logging.info("🔐 Conexión SSL establecida con el servidor de chat")
                logging.info(f"🔐 Versión SSL: {sock.version()}")
                logging.info(f"🔐 Cifrado: {sock.cipher()}")
            
            # Configurar socket como no bloqueante DESPUÉS del handshake SSL
            sock.setblocking(False)
            return sock
            
        except Exception as e:
            logging.error(f"❌ Error conectando al servidor de chat: {e}")
            raise
    
    async def handle_client(self, websocket):
        """Maneja una conexión WebSocket de un cliente."""
        chat_socket = None
        client_address = websocket.remote_address
        
        try:
            logging.info(f"🌐 Cliente WebSocket conectado desde {client_address}")
            
            # Conectar al servidor de chat
            chat_socket = await self.connect_to_chat_server()
            
            # Leer la clave pública del servidor
            server_public_key_path = Config.SERVER_PUBLIC_KEY_PATH
            if server_public_key_path.exists():
                with open(server_public_key_path, 'r') as f:
                    server_public_key_pem = f.read().strip()
            else:
                logging.error(f"❌ No se encontró la clave pública: {server_public_key_path}")
                await websocket.close()
                return
            
            loop = asyncio.get_event_loop()
            
            # Función auxiliar para leer del socket SSL
            async def read_from_socket(sock, size):
                """Lee datos del socket de forma asíncrona."""
                try:
                    if self.enable_ssl:
                        # Para sockets SSL, usar recv en executor
                        return await loop.run_in_executor(None, sock.recv, size)
                    else:
                        return await loop.sock_recv(sock, size)
                except ssl.SSLWantReadError:
                    await asyncio.sleep(0.01)
                    return b''
                except BlockingIOError:
                    await asyncio.sleep(0.01)
                    return b''
            
            async def write_to_socket(sock, data):
                """Escribe datos al socket de forma asíncrona."""
                if self.enable_ssl:
                    return await loop.run_in_executor(None, sock.sendall, data)
                else:
                    return await loop.sock_sendall(sock, data)
            
            # Dar tiempo al servidor para inicializar
            await asyncio.sleep(0.2)
            
            # Manejar protocolo de autenticación
            async def handle_auth_protocol():
                """Maneja el protocolo inicial de autenticación."""
                buffer = b''
                
                async def read_next_line():
                    """Lee la siguiente línea del socket."""
                    nonlocal buffer
                    max_attempts = 100
                    attempts = 0
                    
                    while b'\n' not in buffer and attempts < max_attempts:
                        data = await read_from_socket(chat_socket, self.buffer_size)
                        if data:
                            buffer += data
                            logging.debug(f"📦 Recibidos {len(data)} bytes, buffer: {len(buffer)} bytes")
                        else:
                            await asyncio.sleep(0.1)
                            attempts += 1
                    
                    if b'\n' not in buffer:
                        return None
                    
                    line, buffer = buffer.split(b'\n', 1)
                    try:
                        return line.decode('utf-8').strip()
                    except UnicodeDecodeError as e:
                        logging.error(f"❌ Error decodificando línea: {e}")
                        logging.error(f"📄 Datos (hex): {line[:50].hex()}...")
                        return None
                
                # 1. Esperar PUBLIC_KEY_READY
                logging.info("⏳ Esperando PUBLIC_KEY_READY...")
                message = await read_next_line()
                if message != 'PUBLIC_KEY_READY':
                    logging.error(f"❌ Se esperaba PUBLIC_KEY_READY, recibido: {message}")
                    return False
                await websocket.send(message)
                logging.info("✅ PUBLIC_KEY_READY recibido y enviado al cliente")
                
                # 2. Esperar CLIENT_PUBLIC_KEY
                logging.info("⏳ Esperando CLIENT_PUBLIC_KEY...")
                message = await read_next_line()
                if message != 'CLIENT_PUBLIC_KEY':
                    logging.error(f"❌ Se esperaba CLIENT_PUBLIC_KEY, recibido: {message}")
                    return False
                await websocket.send(message)
                logging.info("✅ CLIENT_PUBLIC_KEY recibido")
                
                # Enviar clave pública del servidor al cliente web
                await websocket.send(server_public_key_pem)
                logging.info("📤 Clave pública del servidor enviada al cliente web")
                
                # Esperar clave pública del cliente web
                client_public_key = await websocket.recv()
                logging.info("📥 Clave pública del cliente web recibida")
                
                # Enviar al servidor TCP
                await write_to_socket(
                    chat_socket,
                    (client_public_key + '\n').encode('utf-8')
                )
                logging.info("📤 Clave pública del cliente enviada al servidor TCP")
                
                # 3. Esperar NICK
                logging.info("⏳ Esperando NICK...")
                message = await read_next_line()
                if message != 'NICK':
                    logging.error(f"❌ Se esperaba NICK, recibido: {message}")
                    return False
                await websocket.send(message)
                logging.info("✅ NICK recibido y enviado al cliente")
                
                # Esperar nickname cifrado del cliente
                encrypted_nick = await websocket.recv()
                logging.info("📥 Nickname cifrado recibido del cliente")
                
                # Enviar al servidor TCP
                await write_to_socket(
                    chat_socket,
                    (encrypted_nick + '\n').encode('utf-8')
                )
                
                # 4. Esperar PASSWORD
                logging.info("⏳ Esperando PASSWORD...")
                message = await read_next_line()
                if message != 'PASSWORD':
                    logging.error(f"❌ Se esperaba PASSWORD, recibido: {message}")
                    return False
                await websocket.send(message)
                logging.info("✅ PASSWORD recibido y enviado al cliente")
                
                # Esperar password cifrado del cliente
                encrypted_pass = await websocket.recv()
                logging.info("📥 Password cifrado recibido del cliente")
                
                # Enviar al servidor TCP
                await write_to_socket(
                    chat_socket,
                    (encrypted_pass + '\n').encode('utf-8')
                )
                
                # 5. Esperar AUTH_SUCCESS, AUTH_FAILED o SERVIDOR_LLENO
                logging.info("⏳ Esperando resultado de autenticación...")
                message = await read_next_line()
                if message not in ['AUTH_SUCCESS', 'AUTH_FAILED', 'SERVIDOR_LLENO']:
                    logging.error(f"❌ Respuesta de autenticación inesperada: {message}")
                    return False
                
                await websocket.send(message)
                logging.info(f"✅ Autenticación: {message}")
                return message == 'AUTH_SUCCESS'
            
            # Ejecutar protocolo de autenticación
            auth_success = await handle_auth_protocol()
            
            if not auth_success:
                logging.warning("⚠️  Autenticación fallida")
                return
            
            logging.info("✅ Cliente autenticado correctamente")
            
            # Manejar mensajes del chat
            async def ws_to_tcp():
                """Lee mensajes del WebSocket y los envía al TCP."""
                try:
                    async for message in websocket:
                        logging.debug(f"📤 WS -> TCP: {len(message)} bytes")
                        if not message.endswith('\n'):
                            message += '\n'
                        await write_to_socket(
                            chat_socket,
                            message.encode('utf-8')
                        )
                except websockets.exceptions.ConnectionClosed:
                    logging.info("🔌 WebSocket cerrado")
                except Exception as e:
                    logging.error(f"❌ Error WS -> TCP: {e}")
            
            async def tcp_to_ws():
                """Lee mensajes del TCP y los envía al WebSocket."""
                try:
                    buffer = b''
                    while True:
                        data = await read_from_socket(chat_socket, self.buffer_size)
                        
                        if not data:
                            # Si no hay datos, esperar un poco
                            await asyncio.sleep(0.05)
                            continue
                        
                        buffer += data
                        
                        while b'\n' in buffer:
                            line, buffer = buffer.split(b'\n', 1)
                            try:
                                message = line.decode('utf-8').strip()
                            except UnicodeDecodeError as e:
                                logging.error(f"❌ Error decodificando mensaje: {e}")
                                continue
                            
                            if message:
                                logging.debug(f"📥 TCP -> WS: {message[:50]}...")
                                await websocket.send(message)
                        
                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    logging.error(f"❌ Error TCP -> WS: {e}")
            
            # Ejecutar ambas tareas en paralelo
            await asyncio.gather(
                ws_to_tcp(),
                tcp_to_ws()
            )
            
        except Exception as e:
            logging.error(f"❌ Error manejando cliente {client_address}: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if chat_socket:
                try:
                    chat_socket.close()
                except:
                    pass
            logging.info(f"👋 Cliente {client_address} desconectado")
    
    async def start(self):
        """Inicia el servidor WebSocket."""
        logging.info("="*70)
        logging.info("🌐 SERVIDOR WEBSOCKET - PUENTE CHAT")
        logging.info("="*70)
        logging.info(f"📍 WebSocket en:     ws://localhost:{self.ws_port}")
        logging.info(f"🔗 Servidor chat:    {self.chat_host}:{self.chat_port}")
        logging.info(f"🔐 SSL/TLS:          {'Habilitado' if self.enable_ssl else 'Deshabilitado'}")
        logging.info("="*70)
        logging.info("✅ Puente WebSocket listo. Presiona Ctrl+C para detener.\n")
        
        async with websockets.serve(
            self.handle_client,
            'localhost',
            self.ws_port,
            ping_interval=20,
            ping_timeout=10
        ):
            await asyncio.Future()


async def main():
    """Función principal."""
    bridge = WebSocketChatBridge()
    await bridge.start()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n🛑 Servidor WebSocket detenido por el usuario.")
        print("👋 ¡Hasta luego!\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error al iniciar el servidor WebSocket: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)