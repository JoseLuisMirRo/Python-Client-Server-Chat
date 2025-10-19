import socket
import threading
import traceback
import time
import os
import sys
import hashlib
import json

# Agregar el directorio padre al path para importar crypto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from crypto.rsa_crypto import RSACrypto
from cryptography.hazmat.primitives import serialization

# ===============================
# Cliente de Chat
# ===============================
# Este cliente permite conectarse a un servidor de chat, autenticarse y enviar/recibir mensajes en tiempo real.
# El código utiliza hilos para gestionar la recepción y el envío de mensajes de forma simultánea.

class ChatClient:
    """
    Clase que representa un cliente de chat.
    Permite conectarse a un servidor, autenticarse y enviar/recibir mensajes.
    """
    def __init__(self, host='localhost', port=0):
        """
        Inicializa el cliente de chat con un flujo amigable y descriptivo.
        """
        print("\n" + "="*60)
        print("    🎯 BIENVENIDO AL CHAT SEGURO CON CIFRADO RSA")
        print("="*60)
        
        # ============================================================
        # PASO 1: Configuración de Conexión
        # ============================================================
        print("\n📡 PASO 1: Configuración de Conexión")
        print("-" * 60)
        
        # Solicitar IP
        if host in (None, '', 'localhost'):
            print("¿A qué servidor deseas conectarte?")
            ingresado = input("  → IP del servidor (Enter para localhost): ").strip()
            if ingresado:
                host = ingresado
            else:
                host = 'localhost'
        
        print(f"  ✓ Servidor: {host}")
        
        # Solicitar puerto
        if port == 0:
            print("\n¿En qué puerto está escuchando el servidor?")
            port = int(input("  → Puerto (por defecto 5555): ") or "5555")
        
        print(f"  ✓ Puerto: {port}")
        
        # ============================================================
        # PASO 2: Configuración de Cifrado
        # ============================================================
        print("\n🔐 PASO 2: Configuración de Cifrado RSA")
        print("-" * 60)
        print("El cifrado RSA garantiza que tus mensajes sean privados y seguros.")
        print()
        
        # Generar claves del cliente
        print("  → Generando tu par de claves RSA (pública/privada)...")
        self.rsa_crypto = RSACrypto()
        self.rsa_crypto.generar_par_claves()
        print("  ✓ Tus claves RSA han sido generadas correctamente")
        print("    • Estas claves solo existen en memoria (no se guardan en disco)")
        print("    • Se usarán para cifrar/descifrar tus mensajes")
        
        # Cargar clave pública del servidor
        print("\n  → Necesitas la clave pública del servidor para autenticarte")
        self.server_rsa = RSACrypto()
        key_path = input("  → Ruta del archivo (Enter para 'server_public_key.pem'): ").strip()
        if not key_path:
            key_path = "server_public_key.pem"
        
        try:
            if os.path.exists(key_path):
                with open(key_path, 'rb') as f:
                    public_key_pem = f.read()
                self.server_rsa.cargar_clave_publica(public_key_pem)
                print(f"  ✓ Clave pública del servidor cargada desde: {key_path}")
            else:
                print(f"\n  ✗ Archivo no encontrado: {key_path}")
                print("    Asegúrate de que el servidor esté ejecutándose.")
                print("    El servidor genera automáticamente 'server_public_key.pem' al iniciar.")
                raise FileNotFoundError(f"No se encontró la clave pública en: {key_path}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
            raise
        
        # ============================================================
        # PASO 3: Credenciales
        # ============================================================
        print("\n👤 PASO 3: Tus Credenciales")
        print("-" * 60)
        
        # Solicitar contraseña del servidor
        print("Para conectarte, necesitas conocer la contraseña del servidor.")
        self.server_password = input("  → Contraseña del servidor: ").strip()
        
        # Solicitar nombre de usuario
        print("\nElige un nombre de usuario para el chat.")
        self.nickname = input("  → Tu nombre de usuario: ").strip()
        
        print(f"\n  ✓ Configurado como: {self.nickname}")
        
        # ============================================================
        # PASO 4: Conectar al servidor
        # ============================================================
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
        
        print("\n" + "="*60)

    

    def recibir(self):
        """
        Recibe mensajes del servidor de chat.
        - Gestiona la autenticación (nickname y contraseña).
        - Imprime los mensajes recibidos.
        - Si la conexión se pierde o la autenticación falla, termina el cliente.
        """
        buffer = ""
        while self.running:
            try:
                # Recibir datos y agregarlos al buffer
                data = self.client.recv(4096)
                if not data:
                    print("🔌 Conexión cerrada por el servidor.")
                    self.running = False
                    break
                
                buffer += data.decode('utf-8')
                
                # Procesar todos los mensajes completos en el buffer
                while '\n' in buffer:
                    mensaje, buffer = buffer.split('\n', 1)
                    mensaje = mensaje.strip()
                    
                    if not mensaje:
                        continue
                    
                    # Manejo de confirmación de clave pública
                    if mensaje == 'PUBLIC_KEY_READY':
                        print("🔒 Servidor listo para autenticación cifrada")
                    
                    # Enviar nuestra clave pública al servidor
                    elif mensaje == 'CLIENT_PUBLIC_KEY':
                        import base64
                        from cryptography.hazmat.primitives import serialization
                        # Serializar nuestra clave pública
                        my_public_key_pem = self.rsa_crypto.public_key.public_bytes(
                            encoding=serialization.Encoding.PEM,
                            format=serialization.PublicFormat.SubjectPublicKeyInfo
                        )
                        # Enviar en base64
                        my_public_key_b64 = base64.b64encode(my_public_key_pem).decode('utf-8')
                        self.client.send(f'{my_public_key_b64}\n'.encode('utf-8'))
                        print("🔑 Tu clave pública enviada al servidor")
                    
                    # Manejo de autenticación (cifrar con clave pública del SERVIDOR)
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
                        print("   • Todos los mensajes están cifrados con RSA")
                        print("   • Presiona Ctrl+C para salir\n")
                        print("-" * 60 + "\n")
                        self.authenticated = True
                        
                    else:
                        # Descifrar mensajes de broadcast con NUESTRA clave privada
                        try:
                            mensaje_descifrado = self.rsa_crypto.descifrar(mensaje)
                            print(mensaje_descifrado)
                        except Exception as e:
                            # Si no se puede descifrar, mostrar tal como viene
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
        """
        Envía mensajes al servidor de chat.
        - Espera hasta que el usuario esté autenticado.
        - Permite al usuario escribir mensajes y los envía al servidor.
        - Si ocurre un error o se pierde la conexión, termina el cliente.
        """
        while self.running:
            try:
                # Esperar hasta estar autenticado
                if not self.authenticated:
                    time.sleep(0.1)
                    continue
                # Leer y enviar mensaje
                mensaje = input()
                if not self.running:
                    break
                
                # Calcular SHA-256 del mensaje en claro
                try:
                    mensaje_hash = hashlib.sha256(mensaje.encode('utf-8')).hexdigest()
                except Exception:
                    mensaje_hash = ''

                # Cifrar mensaje con la clave pública del servidor
                mensaje_cifrado = self.server_rsa.cifrar(mensaje)

                # Enviar un JSON con el ciphertext y el hash para validación en el servidor
                payload = json.dumps({
                    'cipher': mensaje_cifrado,
                    'hash': mensaje_hash
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
        """
        Inicia el cliente de chat.
        - Crea y lanza los hilos para recibir y enviar mensajes.
        - Espera a que el usuario termine o se pierda la conexión.
        """
        # Hilo para recibir mensajes
        hilo_recepcion = threading.Thread(target=self.recibir)
        hilo_recepcion.daemon = True
        hilo_recepcion.start()
        # Hilo para escribir mensajes
        hilo_escritura = threading.Thread(target=self.escribir)
        hilo_escritura.daemon = True
        hilo_escritura.start()
        # Esperar a que los hilos terminen
        while self.running:
            time.sleep(0.1)
        # Esperar a que los hilos terminen si running se vuelve False
        hilo_recepcion.join(timeout=1)
        hilo_escritura.join(timeout=1)

def main():
    """
    Función principal para iniciar el cliente de chat.
    """
    try:
        cliente = ChatClient()
        cliente.iniciar()
    except KeyboardInterrupt:
        print("\n👋 Saliendo del chat...")
    except Exception as e:
        print(f"❌ Error crítico: {e}")

if __name__ == "__main__":
    main()