#!/usr/bin/env python3
"""
Script de utilidad para ejecutar el servidor o cliente con configuración interactiva.
Facilita el inicio rápido del sistema de chat sin necesidad de recordar comandos.
"""
import sys
import os
import subprocess
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config


def print_banner():
    """Imprime un banner de bienvenida."""
    print("\n" + "="*70)
    print("    🚀 SISTEMA DE CHAT SEGURO CON CIFRADO RSA")
    print("="*70)


def print_menu():
    """Imprime el menú principal."""
    print("\n¿Qué deseas hacer?\n")
    print("  1. Iniciar SERVIDOR")
    print("  2. Iniciar CLIENTE")
    print("  3. Mostrar configuración actual")
    print("  4. Ejecutar pruebas de hash")
    print("  5. Generar archivo .env de ejemplo")
    print("  6. Salir")
    print()


def iniciar_servidor():
    """Inicia el servidor con opciones interactivas."""
    print("\n" + "-"*70)
    print("    📡 CONFIGURACIÓN DEL SERVIDOR")
    print("-"*70)
    
    # Host
    print(f"\nHost actual: {Config.DEFAULT_HOST}")
    print("  • 0.0.0.0 = Acepta conexiones desde cualquier IP (LAN)")
    print("  • localhost = Solo conexiones locales")
    host = input(f"  → Cambiar host? (Enter para mantener '{Config.DEFAULT_HOST}'): ").strip()
    
    # Puerto
    print(f"\nPuerto actual: {Config.DEFAULT_PORT}")
    port = input(f"  → Cambiar puerto? (Enter para mantener '{Config.DEFAULT_PORT}'): ").strip()
    
    # Contraseña
    print(f"\nContraseña actual: {'*' * len(Config.SERVER_PASSWORD)}")
    password = input("  → Cambiar contraseña? (Enter para mantener actual): ").strip()
    
    # Construir comando
    cmd = [sys.executable, "server/server.py"]
    
    if host:
        cmd.extend(["--host", host])
    if port:
        cmd.extend(["--port", port])
    if password:
        cmd.extend(["--password", password])
    
    print("\n" + "="*70)
    print("  ✅ Iniciando servidor...")
    print("="*70 + "\n")
    
    # Ejecutar servidor
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n\n🛑 Servidor detenido por el usuario")


def iniciar_cliente():
    """Inicia el cliente con opciones interactivas."""
    print("\n" + "-"*70)
    print("    👤 CONFIGURACIÓN DEL CLIENTE")
    print("-"*70)
    
    print("\n¿Deseas especificar la conexión ahora o durante la ejecución?")
    print("  1. Especificar ahora")
    print("  2. Configurar interactivamente (recomendado)")
    
    opcion = input("\n  → Opción: ").strip()
    
    cmd = [sys.executable, "client/client.py"]
    
    if opcion == "1":
        host = input(f"\n  → Host del servidor (Enter para '{Config.DEFAULT_HOST}'): ").strip()
        port = input(f"  → Puerto (Enter para '{Config.DEFAULT_PORT}'): ").strip()
        
        if host:
            cmd.extend(["--host", host])
        if port:
            cmd.extend(["--port", port])
    
    print("\n" + "="*70)
    print("  ✅ Iniciando cliente...")
    print("="*70 + "\n")
    
    # Ejecutar cliente
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n\n👋 Cliente cerrado por el usuario")


def mostrar_configuracion():
    """Muestra la configuración actual."""
    Config.display_config()
    input("\nPresiona Enter para continuar...")


def ejecutar_pruebas():
    """Ejecuta las pruebas de hash."""
    print("\n" + "="*70)
    print("    🧪 EJECUTANDO PRUEBAS DE VERIFICACIÓN DE HASH")
    print("="*70 + "\n")
    
    try:
        subprocess.run([sys.executable, "scripts/test_hash_mismatch.py"])
    except KeyboardInterrupt:
        print("\n\n🛑 Pruebas interrumpidas")
    
    input("\nPresiona Enter para continuar...")


def generar_env_ejemplo():
    """Genera un archivo .env desde .env.example."""
    env_example = Path(".env.example")
    env_file = Path(".env")
    
    if not env_example.exists():
        print("\n❌ Error: No se encontró .env.example")
        input("Presiona Enter para continuar...")
        return
    
    if env_file.exists():
        print(f"\n⚠️  El archivo .env ya existe.")
        respuesta = input("¿Deseas sobrescribirlo? (s/N): ").strip().lower()
        if respuesta != 's':
            print("Operación cancelada.")
            input("Presiona Enter para continuar...")
            return
    
    try:
        # Copiar .env.example a .env
        with open(env_example, 'r') as f:
            contenido = f.read()
        
        with open(env_file, 'w') as f:
            f.write(contenido)
        
        print(f"\n✅ Archivo .env creado exitosamente")
        print(f"   Puedes editarlo en: {env_file.absolute()}")
        print("\n📝 Recuerda cambiar la contraseña en producción!")
    except Exception as e:
        print(f"\n❌ Error creando .env: {e}")
    
    input("\nPresiona Enter para continuar...")


def main():
    """Función principal del script."""
    while True:
        print_banner()
        print_menu()
        
        try:
            opcion = input("  → Selecciona una opción (1-6): ").strip()
            
            if opcion == "1":
                iniciar_servidor()
            elif opcion == "2":
                iniciar_cliente()
            elif opcion == "3":
                mostrar_configuracion()
            elif opcion == "4":
                ejecutar_pruebas()
            elif opcion == "5":
                generar_env_ejemplo()
            elif opcion == "6":
                print("\n👋 ¡Hasta pronto!")
                break
            else:
                print("\n❌ Opción inválida. Intenta de nuevo.")
                input("Presiona Enter para continuar...")
        
        except KeyboardInterrupt:
            print("\n\n👋 ¡Hasta pronto!")
            break
        except Exception as e:
            print(f"\n❌ Error inesperado: {e}")
            input("Presiona Enter para continuar...")


if __name__ == "__main__":
    main()