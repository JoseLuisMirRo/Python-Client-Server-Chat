#!/usr/bin/env python3
"""
Servidor Web Flask - Maneja autenticación OAuth 2.0 con Google
Se ejecuta en puerto 5000 (separado del servidor de chat en puerto 5555)

Este servidor proporciona:
- Autenticación con Google OAuth
- Gestión de sesiones de usuario
- Token de acceso para el chat
- Archivos estáticos (CSS, JS) para la interfaz del chat
"""
import os
import sys
from flask import Flask
from dotenv import load_dotenv

# Cargar variables de entorno ANTES de importar Config
load_dotenv()

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from auth.controllers.auth_routes import auth_bp, init_auth_routes


def create_web_app():
    """
    Factory function para crear y configurar la aplicación Flask.
    
    Returns:
        Aplicación Flask configurada
    """
    # Crear aplicación Flask con configuración de templates y static
    app = Flask(
        __name__,
        template_folder='auth/templates',
        static_folder='auth/static',
        static_url_path='/static'
    )
    
    # ===== CONFIGURACIÓN DE LA APLICACIÓN =====
    app.config['SECRET_KEY'] = Config.OAUTH_SECRET_KEY
    app.config['SESSION_COOKIE_NAME'] = 'chat_oauth_session'
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    # En producción, habilitar:
    # app.config['SESSION_COOKIE_SECURE'] = True  # Solo HTTPS
    
    # Configuración OAuth
    app.config['GOOGLE_CLIENT_ID'] = Config.GOOGLE_CLIENT_ID
    app.config['GOOGLE_CLIENT_SECRET'] = Config.GOOGLE_CLIENT_SECRET
    
    # ===== VALIDACIÓN DE CREDENCIALES =====
    if not app.config['GOOGLE_CLIENT_ID'] or not app.config['GOOGLE_CLIENT_SECRET']:
        print("\n" + "="*70)
        print("⚠️  ADVERTENCIA: Las credenciales de Google OAuth no están configuradas")
        print("="*70)
        print("   Por favor, configura las siguientes variables en el archivo .env:")
        print("   • GOOGLE_CLIENT_ID")
        print("   • GOOGLE_CLIENT_SECRET")
        print("   • SECRET_KEY")
        print("\n   Consulta el archivo README.md para más información.")
        print("="*70 + "\n")
    
    # ===== INICIALIZAR RUTAS DE AUTENTICACIÓN =====
    init_auth_routes(app)
    
    # ===== REGISTRAR BLUEPRINT =====
    app.register_blueprint(auth_bp)
    
    return app


def main():
    """
    Función principal para ejecutar el servidor web.
    """
    app = create_web_app()
    
    print("\n" + "="*70)
    print("🔐 SERVIDOR WEB DE AUTENTICACIÓN OAUTH 2.0")
    print("="*70)
    print(f"📍 URL Local:     http://localhost:{Config.WEB_SERVER_PORT}")
    print(f"📍 URL Red:       http://{Config.WEB_SERVER_HOST}:{Config.WEB_SERVER_PORT}")
    print("="*70)
    print("🔑 Método de autenticación: Google OAuth 2.0")
    print("🛡️  Seguridad: Sesiones cifradas")
    print("="*70)
    print("\n✅ Servidor listo. Presiona Ctrl+C para detener.\n")
    print("📋 INSTRUCCIONES:")
    print("   1. Abre http://localhost:5000 en tu navegador")
    print("   2. Inicia sesión con tu cuenta de Google")
    print("   3. Accede al chat directamente desde el navegador")
    print("   4. Recuerda iniciar también el servidor WebSocket:")
    print("      → python websocket_server.py")
    print("="*70 + "\n")
    
    # Ejecutar la aplicación en modo debug
    app.run(
        debug=True,
        host=Config.WEB_SERVER_HOST,
        port=Config.WEB_SERVER_PORT,
        use_reloader=True
    )


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Servidor detenido por el usuario.")
        print("👋 ¡Hasta luego!\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error al iniciar el servidor: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)