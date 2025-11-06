"""
Módulo de configuración centralizado para el sistema de chat.
Maneja configuración desde variables de entorno y valores por defecto.
"""
import os
from pathlib import Path
from typing import Optional


class Config:
    """Clase de configuración para el servidor y cliente de chat."""
    
    # Directorio base del proyecto
    BASE_DIR = Path(__file__).parent.absolute()
    
    # ===== CONFIGURACIÓN DE RED =====
    DEFAULT_HOST: str = os.getenv('CHAT_HOST', 'localhost')
    DEFAULT_PORT: int = int(os.getenv('CHAT_PORT', '5555'))
    
    # ===== CONFIGURACIÓN DE SEGURIDAD =====
    # Contraseña del servidor (CAMBIAR EN PRODUCCIÓN)
    SERVER_PASSWORD: str = os.getenv('CHAT_SERVER_PASSWORD', 'secreto')
    
    # ===== CONFIGURACIÓN DE CIFRADO RSA =====
    # Tamaño de clave RSA en bits
    RSA_KEY_SIZE: int = int(os.getenv('CHAT_RSA_KEY_SIZE', '2048'))
    
    # Rutas de claves RSA
    SERVER_PRIVATE_KEY_PATH: Path = Path(
        os.getenv('CHAT_SERVER_PRIVATE_KEY', 
                  str(BASE_DIR / 'server_private_key.pem'))
    )
    SERVER_PUBLIC_KEY_PATH: Path = Path(
        os.getenv('CHAT_SERVER_PUBLIC_KEY', 
                  str(BASE_DIR / 'server_public_key.pem'))
    )
    
    # ===== CONFIGURACIÓN SSL/TLS =====
    # Habilitar SSL/TLS por defecto
    ENABLE_SSL: bool = os.getenv('CHAT_ENABLE_SSL', 'True').lower() in ('true', '1', 'yes')
    
    # Rutas de certificados SSL
    SSL_CERT_PATH: Path = Path(
        os.getenv('CHAT_SSL_CERT', 
                  str(BASE_DIR / 'server_cert.pem'))
    )
    SSL_KEY_PATH: Path = Path(
        os.getenv('CHAT_SSL_KEY', 
                  str(BASE_DIR / 'server_key.pem'))
    )
    
    # Verificar certificados del cliente (para autenticación mutua)
    SSL_VERIFY_CLIENT: bool = os.getenv('CHAT_SSL_VERIFY_CLIENT', 'False').lower() in ('true', '1', 'yes')
    
    # Ruta del certificado CA para verificar clientes (si SSL_VERIFY_CLIENT está habilitado)
    SSL_CA_CERT_PATH: Optional[Path] = Path(
        os.getenv('CHAT_SSL_CA_CERT', '')
    ) if os.getenv('CHAT_SSL_CA_CERT') else None
    
    # ===== CONFIGURACIÓN DEL SERVIDOR =====
    MAX_CLIENTS: int = int(os.getenv('CHAT_MAX_CLIENTS', '500'))
    BUFFER_SIZE: int = int(os.getenv('CHAT_BUFFER_SIZE', '4096'))
    THREAD_STACK_SIZE: int = int(os.getenv('CHAT_THREAD_STACK_SIZE', '67108864'))  # 64MB
    
    # ===== CONFIGURACIÓN DE LOGGING =====
    LOG_LEVEL: str = os.getenv('CHAT_LOG_LEVEL', 'INFO')
    LOG_FORMAT: str = '%(asctime)s - %(levelname)s: %(message)s'
    LOG_DATE_FORMAT: str = '%Y-%m-%d %H:%M:%S'
    
    # ===== CONFIGURACIÓN DE CLIENTE =====
    CLIENT_RECEIVE_TIMEOUT: float = float(os.getenv('CHAT_CLIENT_TIMEOUT', '0.1'))
    
    @classmethod
    def get_server_config(cls) -> dict:
        """Retorna la configuración del servidor como diccionario."""
        return {
            'host': cls.DEFAULT_HOST,
            'port': cls.DEFAULT_PORT,
            'password': cls.SERVER_PASSWORD,
            'max_clients': cls.MAX_CLIENTS,
            'buffer_size': cls.BUFFER_SIZE,
            'rsa_key_size': cls.RSA_KEY_SIZE,
            'private_key_path': str(cls.SERVER_PRIVATE_KEY_PATH),
            'public_key_path': str(cls.SERVER_PUBLIC_KEY_PATH),
            'enable_ssl': cls.ENABLE_SSL,
            'ssl_cert_path': str(cls.SSL_CERT_PATH),
            'ssl_key_path': str(cls.SSL_KEY_PATH),
            'ssl_verify_client': cls.SSL_VERIFY_CLIENT,
        }
    
    @classmethod
    def get_client_config(cls) -> dict:
        """Retorna la configuración del cliente como diccionario."""
        return {
            'default_host': cls.DEFAULT_HOST,
            'default_port': cls.DEFAULT_PORT,
            'buffer_size': cls.BUFFER_SIZE,
            'public_key_path': str(cls.SERVER_PUBLIC_KEY_PATH),
            'receive_timeout': cls.CLIENT_RECEIVE_TIMEOUT,
        }
    
    @classmethod
    def display_config(cls) -> None:
        """Muestra la configuración actual (omitiendo datos sensibles)."""
        print("\n" + "="*60)
        print("    CONFIGURACIÓN DEL SISTEMA")
        print("="*60)
        print(f"Host por defecto: {cls.DEFAULT_HOST}")
        print(f"Puerto por defecto: {cls.DEFAULT_PORT}")
        print(f"Máximo de clientes: {cls.MAX_CLIENTS}")
        print(f"Tamaño de buffer: {cls.BUFFER_SIZE} bytes")
        print(f"Tamaño de clave RSA: {cls.RSA_KEY_SIZE} bits")
        print(f"Nivel de logging: {cls.LOG_LEVEL}")
        print(f"Clave privada del servidor: {cls.SERVER_PRIVATE_KEY_PATH}")
        print(f"Clave pública del servidor: {cls.SERVER_PUBLIC_KEY_PATH}")
        print(f"Contraseña del servidor: {'*' * len(cls.SERVER_PASSWORD)}")
        print(f"SSL/TLS habilitado: {cls.ENABLE_SSL}")
        if cls.ENABLE_SSL:
            print(f"Certificado SSL: {cls.SSL_CERT_PATH}")
            print(f"Clave SSL: {cls.SSL_KEY_PATH}")
            print(f"Verificar clientes: {cls.SSL_VERIFY_CLIENT}")
        print("="*60 + "\n")


# Configuración global accesible
config = Config()