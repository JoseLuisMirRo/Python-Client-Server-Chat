import socket
import threading
import traceback
import time

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
        Inicializa el cliente de chat.
        - Solicita el host/IP del servidor si no se proporciona.
        - Solicita el puerto si no se proporciona.
        - Solicita el nombre de usuario.
        - Establece la conexión con el servidor.
        """
        # Solicitar host si no se proporciona explícitamente
        if host in (None, '', 'localhost'):
            ingresado = input("Ingrese IP o host del servidor (Enter para localhost): ").strip()
            if ingresado:
                host = ingresado

        # Solicitar puerto si no se proporciona
        if port == 0:
            port = int(input("Ingrese el puerto del servidor: "))
        # Configurar socket
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((host, port))
        # Solicitar nickname
        self.nickname = input("Elija su nombre de usuario: ")
        self.authenticated = False
        self.running = True

    

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
                    self.client.send(self.nickname.encode('utf-8'))
                elif mensaje == 'PASSWORD':
                    contrasena = input("Ingrese la contraseña del servidor: ")
                    self.client.send(contrasena.encode('utf-8'))
                elif mensaje == 'AUTH_FAILED':
                    print("❌ Autenticación fallida. Saliendo...")
                    self.running = False
                    self.client.close()
                    break
                elif mensaje == 'AUTH_SUCCESS':
                    print("✅ Autenticación exitosa!")
                    self.authenticated = True
                    
                else:
                    # Imprimir mensajes tal cual
                    print(mensaje)
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
                self.client.send(mensaje.encode('utf-8'))
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