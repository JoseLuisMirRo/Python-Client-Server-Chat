"""
Módulo de cifrado simétrico AES para el servidor de chat.
Implementa generación de claves, cifrado y descifrado usando AES-256-GCM.
"""

import os
import base64
import logging
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class AESCrypto:
    """Clase para manejar operaciones de cifrado AES."""
    
    def __init__(self):
        """Inicializa el objeto AES."""
        self.key = None
        self.aes_gcm = None
    
    def generar_clave_desde_password(self, password: str, salt: bytes = None) -> bytes:
        """Genera una clave AES desde una contraseña usando PBKDF2.
        
        Args:
            password: Contraseña para derivar la clave
            salt: Salt opcional (se genera uno nuevo si no se proporciona)
            
        Returns:
            Clave derivada de 32 bytes para AES-256
        """
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 256 bits para AES-256
            salt=salt,
            iterations=100000,
        )
        
        key = kdf.derive(password.encode('utf-8'))
        self.key = key
        self.aes_gcm = AESGCM(key)
        
        logging.info("✅ Clave AES generada desde contraseña")
        return key, salt
    
    def generar_clave_aleatoria(self) -> bytes:
        """Genera una clave AES aleatoria.
        
        Returns:
            Clave aleatoria de 32 bytes para AES-256
        """
        self.key = os.urandom(32)
        self.aes_gcm = AESGCM(self.key)
        
        logging.info("✅ Clave AES aleatoria generada")
        return self.key
    
    def cargar_clave(self, key: bytes) -> None:
        """Carga una clave AES.
        
        Args:
            key: Clave de 32 bytes para AES-256
        """
        if len(key) != 32:
            raise ValueError("La clave debe tener 32 bytes para AES-256")
        
        self.key = key
        self.aes_gcm = AESGCM(key)
        
        logging.info("✅ Clave AES cargada")
    
    def cifrar(self, mensaje: str) -> tuple[str, str]:
        """Cifra un mensaje usando AES-GCM.
        
        Args:
            mensaje: Mensaje a cifrar
            
        Returns:
            Tupla con (mensaje_cifrado_base64, nonce_base64)
        """
        if not self.aes_gcm:
            raise ValueError("No hay clave AES cargada")
        
        try:
            mensaje_bytes = mensaje.encode('utf-8')
            
            # Generar nonce aleatorio
            nonce = os.urandom(12)  # 96 bits para GCM
            
            # Cifrar con AES-GCM
            mensaje_cifrado = self.aes_gcm.encrypt(nonce, mensaje_bytes, None)
            
            # Codificar en base64
            mensaje_base64 = base64.b64encode(mensaje_cifrado).decode('utf-8')
            nonce_base64 = base64.b64encode(nonce).decode('utf-8')
            
            logging.debug(f"✅ Mensaje cifrado con AES-GCM (tamaño: {len(mensaje_bytes)} bytes)")
            return mensaje_base64, nonce_base64
            
        except Exception as e:
            logging.error(f"❌ Error cifrando mensaje: {e}")
            raise
    
    def descifrar(self, mensaje_cifrado: str, nonce: str) -> str:
        """Descifra un mensaje usando AES-GCM.
        
        Args:
            mensaje_cifrado: Mensaje cifrado en base64
            nonce: Nonce en base64
            
        Returns:
            Mensaje descifrado
        """
        if not self.aes_gcm:
            raise ValueError("No hay clave AES cargada")
        
        try:
            # Decodificar desde base64
            mensaje_bytes = base64.b64decode(mensaje_cifrado.encode('utf-8'))
            nonce_bytes = base64.b64decode(nonce.encode('utf-8'))
            
            # Descifrar
            mensaje_descifrado = self.aes_gcm.decrypt(nonce_bytes, mensaje_bytes, None)
            
            mensaje = mensaje_descifrado.decode('utf-8')
            logging.debug(f"✅ Mensaje descifrado con AES-GCM (tamaño: {len(mensaje)} bytes)")
            return mensaje
            
        except Exception as e:
            logging.error(f"❌ Error descifrando mensaje: {e}")
            raise
    
    def cifrar_con_nonce_combinado(self, mensaje: str) -> str:
        """Cifra un mensaje y combina nonce + mensaje cifrado en un solo string.
        
        Args:
            mensaje: Mensaje a cifrar
            
        Returns:
            String con formato "nonce_base64:mensaje_cifrado_base64"
        """
        mensaje_cifrado, nonce = self.cifrar(mensaje)
        return f"{nonce}:{mensaje_cifrado}"
    
    def descifrar_con_nonce_combinado(self, mensaje_combinado: str) -> str:
        """Descifra un mensaje que tiene el nonce combinado.
        
        Args:
            mensaje_combinado: String con formato "nonce_base64:mensaje_cifrado_base64"
            
        Returns:
            Mensaje descifrado
        """
        try:
            nonce, mensaje_cifrado = mensaje_combinado.split(':', 1)
            return self.descifrar(mensaje_cifrado, nonce)
        except ValueError:
            raise ValueError("Formato de mensaje combinado inválido. Debe ser 'nonce:mensaje'")
    
    def guardar_clave(self, path: str) -> None:
        """Guarda la clave en un archivo.
        
        Args:
            path: Ruta del archivo
        """
        if not self.key:
            raise ValueError("No hay clave generada para guardar")
        
        try:
            with open(path, 'wb') as f:
                f.write(self.key)
            
            logging.info(f"✅ Clave AES guardada en {path}")
            
        except Exception as e:
            logging.error(f"❌ Error guardando clave: {e}")
            raise
    
    def cargar_clave_desde_archivo(self, path: str) -> None:
        """Carga la clave desde un archivo.
        
        Args:
            path: Ruta del archivo
        """
        try:
            with open(path, 'rb') as f:
                key = f.read()
            
            self.cargar_clave(key)
            logging.info(f"✅ Clave AES cargada desde {path}")
            
        except Exception as e:
            logging.error(f"❌ Error cargando clave desde archivo: {e}")
            raise


def generar_clave_servidor(password: str = None, key_path: str = "server_aes_key.key") -> bytes:
    """Función de conveniencia para generar clave del servidor.
    
    Args:
        password: Contraseña opcional para derivar la clave
        key_path: Ruta para guardar la clave
        
    Returns:
        Clave AES generada
    """
    aes_crypto = AESCrypto()
    
    if password:
        key, _ = aes_crypto.generar_clave_desde_password(password)
    else:
        key = aes_crypto.generar_clave_aleatoria()
    
    aes_crypto.guardar_clave(key_path)
    return key
