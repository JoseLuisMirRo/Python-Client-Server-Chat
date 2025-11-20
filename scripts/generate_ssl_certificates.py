#!/usr/bin/env python3
"""
Script para generar certificados SSL/TLS autofirmados para el servidor de chat.
Los certificados generados son válidos solo para desarrollo y testing.
"""

import os
import sys
import ipaddress
from pathlib import Path
from datetime import datetime, timedelta, timezone

try:
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization
except ImportError:
    print("❌ Error: El módulo 'cryptography' es requerido.")
    print("   Instala las dependencias: pip install -r requirements.txt")
    sys.exit(1)


def generar_certificados_ssl(
    cert_path: Path = Path("server_cert.pem"),
    key_path: Path = Path("server_key.pem"),
    dias_validez: int = 365
) -> None:
    """
    Genera un par de certificado y clave privada SSL autofirmados.
    
    Args:
        cert_path: Ruta donde guardar el certificado
        key_path: Ruta donde guardar la clave privada
        dias_validez: Días de validez del certificado
    """
    print("\n" + "="*70)
    print("    🔐 GENERADOR DE CERTIFICADOS SSL/TLS AUTOFIRMADOS")
    print("="*70)
    print()
    print("⚠️  AVISO: Estos certificados son SOLO para desarrollo y testing.")
    print("   Para producción, usa certificados firmados por una CA confiable.")
    print()
    
    # Generar clave privada
    print("📝 Paso 1: Generando clave privada RSA (2048 bits)...")
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    print("   ✓ Clave privada generada")
    
    # Crear el sujeto del certificado
    print("\n📝 Paso 2: Configurando información del certificado...")
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "ES"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Madrid"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "Madrid"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Chat Server"),
        x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
    ])
    print("   ✓ Información configurada")
    
    # Crear el certificado
    print("\n📝 Paso 3: Generando certificado X.509...")
    now = datetime.now(timezone.utc)
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        now
    ).not_valid_after(
        now + timedelta(days=dias_validez)
    ).add_extension(
        x509.SubjectAlternativeName([
            x509.DNSName("localhost"),
            x509.DNSName("*.localhost"),
            x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
            x509.IPAddress(ipaddress.IPv4Address("0.0.0.0")),
        ]),
        critical=False,
    ).sign(private_key, hashes.SHA256())
    print(f"   ✓ Certificado generado (válido por {dias_validez} días)")
    
    # Guardar la clave privada
    print(f"\n📝 Paso 4: Guardando clave privada en '{key_path}'...")
    with open(key_path, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))
    
    # Establecer permisos seguros en la clave privada (solo en Unix)
    if os.name != 'nt':
        os.chmod(key_path, 0o600)
        print(f"   ✓ Permisos de archivo configurados a 600 (solo lectura del propietario)")
    print(f"   ✓ Clave privada guardada")
    
    # Guardar el certificado
    print(f"\n📝 Paso 5: Guardando certificado en '{cert_path}'...")
    with open(cert_path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    print(f"   ✓ Certificado guardado")
    
    print("\n" + "="*70)
    print("    ✅ CERTIFICADOS SSL/TLS GENERADOS EXITOSAMENTE")
    print("="*70)
    print()
    print(f"📄 Certificado: {cert_path.absolute()}")
    print(f"🔑 Clave privada: {key_path.absolute()}")
    print(f"📅 Válido hasta: {(datetime.now(timezone.utc) + timedelta(days=dias_validez)).strftime('%Y-%m-%d')}")
    print()
    print("🚀 Siguiente paso:")
    print("   Inicia el servidor con: python server/server.py --enable-ssl")
    print()
    print("⚠️  Recuerda:")
    print("   • Nunca compartas tu clave privada (server_key.pem)")
    print("   • Estos certificados son solo para desarrollo local")
    print("   • Los navegadores mostrarán advertencias de seguridad (es normal)")
    print()


def main():
    """Función principal del generador de certificados."""
    import argparse
    import ipaddress
    
    parser = argparse.ArgumentParser(
        description='Genera certificados SSL/TLS autofirmados para el servidor de chat'
    )
    parser.add_argument(
        '--cert', 
        type=str, 
        default='server_cert.pem',
        help='Ruta del archivo de certificado (default: server_cert.pem)'
    )
    parser.add_argument(
        '--key', 
        type=str, 
        default='server_key.pem',
        help='Ruta del archivo de clave privada (default: server_key.pem)'
    )
    parser.add_argument(
        '--days', 
        type=int, 
        default=365,
        help='Días de validez del certificado (default: 365)'
    )
    
    args = parser.parse_args()
    
    try:
        # Convertir a Path y hacer rutas absolutas si es necesario
        cert_path = Path(args.cert)
        key_path = Path(args.key)
        
        # Si las rutas son relativas, hacerlas relativas al directorio del proyecto
        base_dir = Path(__file__).parent.parent.absolute()
        if not cert_path.is_absolute():
            cert_path = base_dir / cert_path
        if not key_path.is_absolute():
            key_path = base_dir / key_path
        
        generar_certificados_ssl(cert_path, key_path, args.days)
        
    except Exception as e:
        print(f"\n❌ Error al generar certificados: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

