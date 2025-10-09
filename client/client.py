import socket
import threading
import traceback
import time
import os
import sys

# Agregar el directorio padre al path para importar crypto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from crypto.aes_crypto import AESCrypto

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
        Inicializa el cliente de chat con cifrado AES simétrico.
        """
        print("\n" + "="*60)
        print("    🎯 BIENVENIDO AL CHAT SEGURO CON CIFRADO AES")
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
        # PASO 2: Configuración de Cifrado Simétrico
        # ============================================================
        print("\n🔐 PASO 2: Configuración de Cifrado AES-256-GCM")
        print("-" * 60)
        print("El cifrado AES simétrico es rápido y seguro.")
        print("Todos los participantes comparten la misma clave secreta.")
        print()
        
        # Cargar clave compartida AES
        print("  → Necesitas la clave secreta compartida del servidor")
        self.aes_crypto = AESCrypto()
        key_path = input("  → Ruta del archivo de clave (Enter para 'shared_aes_key.key'): ").strip()
        if not key_path:
            key_path = "shared_aes_key.key"
        
        try:
            if os.path.exists(key_path):
                self.aes_crypto.cargar_clave_desde_archivo(key_path)
                print(f"  ✓ Clave AES cargada desde: {key_path}")
                print("    • Esta clave se usa para cifrar/descifrar todos los mensajes")
                print("    • Es compartida por todos los usuarios del chat")
            else:
                print(f"\n  ✗ Archivo no encontrado: {key_path}")
                print("    Asegúrate de que el servidor esté ejecutándose.")
                print("    El servidor genera automáticamente 'shared_aes_key.key' al iniciar.")
                raise FileNotFoundError(f"No se encontró la clave en: {key_path}")
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
            print("  ✓ Listo para autenticación cifrada...")
        except Exception as e:
            print(f"  ✗ Error de conexión: {e}")
            raise
        
        self.authenticated = False
        self.running = True
        
        print("\n" + "="*60)

    def inicializar_clave_aes(self) -> None:
        """Método obsoleto - la inicialización ahora se hace en __init__"""
        pass

    

    def recibir(self):
        """
        Recibe mensajes del servidor de chat.
        - Gestiona la autenticación (nickname y contraseña).
        - Imprime los mensajes recibidos.
        - Si la conexión se pierde o la autenticación falla, termina el cliente.
        """
        while self.running:
            try:
                mensaje = self.client.recv(1024).decode('utf-8')
                if not mensaje:
                    print("🔌 Conexión cerrada por el servidor.")
                    self.running = False
                    break
                
                # Manejo de autenticación
                if mensaje == 'NICK':
                    print("  → Enviando nombre de usuario cifrado...")
                    nickname_cifrado = self.aes_crypto.cifrar_con_nonce_combinado(self.nickname)
                    self.client.send(nickname_cifrado.encode('utf-8'))
                elif mensaje == 'PASSWORD':
                    print("  → Enviando contraseña cifrada...")
                    contrasena_cifrada = self.aes_crypto.cifrar_con_nonce_combinado(self.server_password)
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
                    print("   • Todos los mensajes están cifrados con AES-256-GCM")
                    print("   • Presiona Ctrl+C para salir\n")
                    print("-" * 60 + "\n")
                    self.authenticated = True
                    
                else:
                    # Descifrar y mostrar mensajes
                    try:
                        mensaje_descifrado = self.aes_crypto.descifrar_con_nonce_combinado(mensaje)
                        print(mensaje_descifrado)
                    except Exception:
                        # Si no se puede descifrar, mostrar tal como viene
                        print(mensaje)
            except Exception as e:
                print(f"❌ Error al recibir mensaje: {e}")
                traceback.print_exc()
                self.running = False
                try:
                    self.client.close()
                except Exception:
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
                
                # Cifrar mensaje antes de enviar
                mensaje_cifrado = self.aes_crypto.cifrar_con_nonce_combinado(mensaje)
                self.client.send(mensaje_cifrado.encode('utf-8'))
            except Exception as e:
                print(f"❌ Error al enviar mensaje: {e}")
                self.running = False
                try:
                    self.client.close()
                except Exception:
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