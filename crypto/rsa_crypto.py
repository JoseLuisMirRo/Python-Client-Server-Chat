"""
Módulo de cifrado asimétrico RSA para el servidor de chat.
Implementa generación de claves, cifrado y descifrado usando RSA.
"""

import os
import base64
import logging
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend


class RSACrypto:
    """Clase para manejar operaciones de cifrado RSA."""
    
    def __init__(self):
        """Inicializa el objeto RSA."""
        self.private_key = None
        self.public_key = None
        self.backend = default_backend()
    
    def generar_par_claves(self, key_size: int = 2048) -> tuple[bytes, bytes]:
        """Genera un par de claves RSA.
        
        Args:
            key_size: Tamaño de la clave en bits (por defecto 2048)
            
        Returns:
            Tupla con (clave_privada, clave_publica) en formato PEM
        """
        try:
            # Generar clave privada
            self.private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=key_size,
                backend=self.backend
            )
            
            # Obtener clave pública
            self.public_key = self.private_key.public_key()
            
            # Serializar claves
            private_pem = self.private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            public_pem = self.public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
            logging.info(f"✅ Par de claves RSA generado (tamaño: {key_size} bits)")
            return private_pem, public_pem
            
        except Exception as e:
            logging.error(f"❌ Error generando claves RSA: {e}")
            raise
    
    def cargar_clave_privada(self, private_key_pem: bytes) -> None:
        """Carga una clave privada desde formato PEM.
        
        Args:
            private_key_pem: Clave privada en formato PEM
        """
        try:
            self.private_key = serialization.load_pem_private_key(
                private_key_pem,
                password=None,
                backend=self.backend
            )
            logging.debug("✅ Clave privada RSA cargada")
        except Exception as e:
            logging.error(f"❌ Error cargando clave privada: {e}")
            raise
    
    def cargar_clave_publica(self, public_key_pem: bytes) -> None:
        """Carga una clave pública desde formato PEM.
        
        Args:
            public_key_pem: Clave pública en formato PEM
        """
        try:
            self.public_key = serialization.load_pem_public_key(
                public_key_pem,
                backend=self.backend
            )
            logging.debug("✅ Clave pública RSA cargada")
        except Exception as e:
            logging.error(f"❌ Error cargando clave pública: {e}")
            raise
    
    def cifrar(self, mensaje: str) -> str:
        """Cifra un mensaje usando la clave pública.
        
        Args:
            mensaje: Mensaje a cifrar
            
        Returns:
            Mensaje cifrado en base64
        """
        if not self.public_key:
            raise ValueError("No hay clave pública cargada")
        
        try:
            mensaje_bytes = mensaje.encode('utf-8')
            
            # Cifrar con padding OAEP
            mensaje_cifrado = self.public_key.encrypt(
                mensaje_bytes,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            # Codificar en base64 para transmisión
            mensaje_base64 = base64.b64encode(mensaje_cifrado).decode('utf-8')
            
            logging.debug(f"✅ Mensaje cifrado con RSA (tamaño: {len(mensaje_bytes)} bytes)")
            return mensaje_base64
            
        except Exception as e:
            logging.error(f"❌ Error cifrando mensaje: {e}")
            raise
    
    def descifrar(self, mensaje_cifrado: str) -> str:
        """Descifra un mensaje usando la clave privada.
        
        Args:
            mensaje_cifrado: Mensaje cifrado en base64
            
        Returns:
            Mensaje descifrado
        """
        if not self.private_key:
            raise ValueError("No hay clave privada cargada")
        
        try:
            # Decodificar desde base64
            mensaje_bytes = base64.b64decode(mensaje_cifrado.encode('utf-8'))
            
            # Descifrar
            mensaje_descifrado = self.private_key.decrypt(
                mensaje_bytes,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            mensaje = mensaje_descifrado.decode('utf-8')
            logging.debug(f"✅ Mensaje descifrado con RSA (tamaño: {len(mensaje)} bytes)")
            return mensaje
            
        except Exception as e:
            logging.error(f"❌ Error descifrando mensaje: {e}")
            raise
    
    def guardar_claves(self, private_path: str, public_path: str) -> None:
        """Guarda las claves en archivos.
        
        Args:
            private_path: Ruta para la clave privada
            public_path: Ruta para la clave pública
        """
        if not self.private_key or not self.public_key:
            raise ValueError("No hay claves generadas para guardar")
        
        try:
            # Guardar clave privada
            with open(private_path, 'wb') as f:
                f.write(self.private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            
            # Guardar clave pública
            with open(public_path, 'wb') as f:
                f.write(self.public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ))
            
            logging.info(f"✅ Claves guardadas en {private_path} y {public_path}")
            
        except Exception as e:
            logging.error(f"❌ Error guardando claves: {e}")
            raise
    
    def cargar_claves_desde_archivo(self, private_path: str, public_path: str) -> None:
        """Carga las claves desde archivos.
        
        Args:
            private_path: Ruta de la clave privada
            public_path: Ruta de la clave pública
        """
        try:
            # Cargar clave privada
            with open(private_path, 'rb') as f:
                private_pem = f.read()
                self.cargar_clave_privada(private_pem)
            
            # Cargar clave pública
            with open(public_path, 'rb') as f:
                public_pem = f.read()
                self.cargar_clave_publica(public_pem)
            
            logging.info(f"✅ Claves cargadas desde {private_path} y {public_path}")
            
        except Exception as e:
            logging.error(f"❌ Error cargando claves desde archivos: {e}")
            raise


def generar_par_claves_servidor(private_path: str = "server_private_key.pem", 
                               public_path: str = "server_public_key.pem") -> tuple[bytes, bytes]:
    """Función de conveniencia para generar claves del servidor.
    
    Args:
        private_path: Ruta para guardar la clave privada
        public_path: Ruta para guardar la clave pública
        
    Returns:
        Tupla con (clave_privada, clave_publica) en formato PEM
    """
    rsa_crypto = RSACrypto()
    private_pem, public_pem = rsa_crypto.generar_par_claves()
    rsa_crypto.guardar_claves(private_path, public_path)
    return private_pem, public_pem
