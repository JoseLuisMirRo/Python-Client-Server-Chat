"""
Cliente de Chat con cifrado RSA.
Permite conectarse a un servidor de chat, autenticarse y enviar/recibir mensajes.
"""
import socket
import threading
import traceback
import time
import os
import sys
import hashlib
import json
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crypto.rsa_crypto import RSACrypto
from cryptography.hazmat.primitives import serialization
from config import Config


class ChatClient:
    """Cliente de chat con cifrado RSA."""
    
    def __init__(self, host: str | None = None, port: int | None = None):
        """Inicializa el cliente de chat con un flujo amigable."""
        print("\n" + "="*60)
        print("    🎯 BIENVENIDO AL CHAT SEGURO CON CIFRADO RSA")
        print("="*60)
        
        
    
        print("\n📡 PASO 1: Configuración de Conexión")
        print("-" * 60)
        
        if host is None:
            print("¿A qué servidor deseas conectarte?")
            ingresado = input(f"  → IP del servidor (Enter para {Config.DEFAULT_HOST}): ").strip()
            host = ingresado if ingresado else Config.DEFAULT_HOST
        
        print(f"  ✓ Servidor: {host}")
        
        if port is None:
            print("\n¿En qué puerto está escuchando el servidor?")
            port_input = input(f"  → Puerto (Enter para {Config.DEFAULT_PORT}): ").strip()
            port = int(port_input) if port_input else Config.DEFAULT_PORT
        
        print(f"  ✓ Puerto: {port}")
        
    
        print("\n🔐 PASO 2: Configuración de Cifrado RSA")
        print("-" * 60)
        print("El cifrado RSA garantiza que tus mensajes sean privados y seguros.")
        print()
        
        print(f"  → Generando tu par de claves RSA ({Config.RSA_KEY_SIZE} bits)...")
        self.rsa_crypto = RSACrypto()
        self.rsa_crypto.generar_par_claves(key_size=Config.RSA_KEY_SIZE)
        print("  ✓ Tus claves RSA han sido generadas correctamente")
        print("    • Estas claves solo existen en memoria (no se guardan en disco)")
        print("    • Se usarán para cifrar/descifrar tus mensajes")
        
        print("\n  → Necesitas la clave pública del servidor para autenticarte")
        self.server_rsa = RSACrypto()
        key_path_input = input(f"  → Ruta del archivo (Enter para '{Config.SERVER_PUBLIC_KEY_PATH.name}'): ").strip()
        key_path = key_path_input if key_path_input else str(Config.SERVER_PUBLIC_KEY_PATH)
        
        possible_paths = [
            Path(key_path),
            Config.BASE_DIR / key_path,
            Path(__file__).parent / key_path,
        ]
        
        key_found = False
        try:
            for path in possible_paths:
                if path.exists():
                    with open(path, 'rb') as f:
                        public_key_pem = f.read()
                    self.server_rsa.cargar_clave_publica(public_key_pem)
                    print(f"  ✓ Clave pública del servidor cargada desde: {path}")
                    key_found = True
                    break
            
            if not key_found:
                print(f"\n  ✗ Archivo no encontrado: {key_path}")
                print("    Asegúrate de que el servidor esté ejecutándose.")
                print("    El servidor genera automáticamente 'server_public_key.pem' al iniciar.")
                raise FileNotFoundError(f"No se encontró la clave pública en: {key_path}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
            raise
        
        print("\n👤 PASO 3: Tus Credenciales")
        print("-" * 60)
        
        print("Para conectarte, necesitas conocer la contraseña del servidor.")
        self.server_password = input("  → Contraseña del servidor: ").strip()
        
        print("\nElige un nombre de usuario para el chat.")
        self.nickname = input("  → Tu nombre de usuario: ").strip()
        
        print(f"\n  ✓ Configurado como: {self.nickname}")
        
        print("\n🔌 PASO 4: Estableciendo Conexión")
        print("-" * 60)
        print(f"  → Conectando a {host}:{port}...")
        
        try:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.connect((host, port))
            print("  ✓ Conexión TCP establecida")
            print("  ✓ Iniciando protocolo de cifrado...")
        except Exception as e:
            print(f"  ✗ Error de conexión: {e}")
            raise
        
        self.authenticated = False
        self.running = True
        self.buffer_size = Config.BUFFER_SIZE
        
        print("\n" + "="*60)

    def recibir(self):
        """Recibe mensajes del servidor de chat."""
        buffer = ""
        while self.running:
            try:
                data = self.client.recv(self.buffer_size)
                if not data:
                    print("🔌 Conexión cerrada por el servidor.")
                    self.running = False
                    break
                
                buffer += data.decode('utf-8')
                
                while '\n' in buffer:
                    mensaje, buffer = buffer.split('\n', 1)
                    mensaje = mensaje.strip()
                    
                    if not mensaje:
                        continue
                    
                    if mensaje == 'PUBLIC_KEY_READY':
                        print("🔒 Servidor listo para autenticación cifrada")
                    
                    elif mensaje == 'CLIENT_PUBLIC_KEY':
                        import base64
                        my_public_key_pem = self.rsa_crypto.public_key.public_bytes(
                            encoding=serialization.Encoding.PEM,
                            format=serialization.PublicFormat.SubjectPublicKeyInfo
                        )
                        my_public_key_b64 = base64.b64encode(my_public_key_pem).decode('utf-8')
                        self.client.send(f'{my_public_key_b64}\n'.encode('utf-8'))
                        print("🔑 Tu clave pública enviada al servidor")
                    
                    elif mensaje == 'NICK':
                        print("  → Enviando nombre de usuario cifrado...")
                        nickname_cifrado = self.server_rsa.cifrar(self.nickname)
                        self.client.send(nickname_cifrado.encode('utf-8'))
                    
                    elif mensaje == 'PASSWORD':
                        print("  → Enviando contraseña cifrada...")
                        contrasena_cifrada = self.server_rsa.cifrar(self.server_password)
                        self.client.send(contrasena_cifrada.encode('utf-8'))
                    
                    elif mensaje == 'AUTH_FAILED':
                        print("❌ Autenticación fallida. Saliendo...")
                        self.running = False
                        self.client.close()
                        break
                    
                    elif mensaje == 'AUTH_SUCCESS':
                        print("\n" + "="*60)
                        print("  ✅ ¡AUTENTICACIÓN EXITOSA!")
                        print("="*60)
                        print("\n💬 Ya puedes escribir mensajes.")
                        print("   • Escribe tu mensaje y presiona Enter para enviarlo")
                        print(f"   • Todos los mensajes están cifrados con RSA-{Config.RSA_KEY_SIZE}")
                        print("   • Presiona Ctrl+C para salir\n")
                        print("-" * 60 + "\n")
                        self.authenticated = True
                        
                    else:
                        try:
                            mensaje_descifrado = self.rsa_crypto.descifrar(mensaje)
                            print(mensaje_descifrado)
                        except Exception as e:
                            print(f"[Sin cifrar] {mensaje}")
            
            except Exception as e:
                print(f"❌ Error al recibir mensaje: {e}")
                traceback.print_exc()
                self.running = False
                try:
                    self.client.close()
                except:
                    pass
                break

    def escribir(self):
        """Envía mensajes al servidor de chat."""
        while self.running:
            try:
                if not self.authenticated:
                    time.sleep(Config.CLIENT_RECEIVE_TIMEOUT)
                    continue
                
                mensaje = input()
                if not self.running:
                    break
                
                try:
                    mensaje_hash = hashlib.sha256(mensaje.encode('utf-8')).hexdigest()
                    mensaje_md5 = hashlib.md5(mensaje.encode('utf-8')).hexdigest()
                    print(f"\n🔒 MD5 del mensaje enviado: {mensaje_md5}")
                except Exception:
                    mensaje_hash = ''
                    mensaje_md5 = ''

                mensaje_cifrado = self.server_rsa.cifrar(mensaje)

                payload = json.dumps({
                    'cipher': mensaje_cifrado,
                    'hash': mensaje_hash,
                    'md5': mensaje_md5
                })
                self.client.send(payload.encode('utf-8'))
            
            except Exception as e:
                print(f"❌ Error al enviar mensaje: {e}")
                self.running = False
                try:
                    self.client.close()
                except:
                    pass
                break

    def iniciar(self):
        """Inicia el cliente de chat."""
        hilo_recepcion = threading.Thread(target=self.recibir)
        hilo_recepcion.daemon = True
        hilo_recepcion.start()
        
        hilo_escritura = threading.Thread(target=self.escribir)
        hilo_escritura.daemon = True
        hilo_escritura.start()
        
        while self.running:
            time.sleep(Config.CLIENT_RECEIVE_TIMEOUT)
        
        hilo_recepcion.join(timeout=1)
        hilo_escritura.join(timeout=1)


def main():
    """Función principal para iniciar el cliente de chat."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Cliente de chat con cifrado RSA')
    parser.add_argument('--host', type=str, help=f'Host del servidor (default: {Config.DEFAULT_HOST})')
    parser.add_argument('--port', type=int, help=f'Puerto del servidor (default: {Config.DEFAULT_PORT})')
    
    args = parser.parse_args()
    
    try:
        cliente = ChatClient(host=args.host, port=args.port)
        cliente.iniciar()
    except KeyboardInterrupt:
        print("\n👋 Saliendo del chat...")
    except Exception as e:
        print(f"❌ Error crítico: {e}")


if __name__ == "__main__":
    main()