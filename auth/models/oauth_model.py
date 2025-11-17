"""
Modelo OAuth - Gestiona autenticación con Google OAuth 2.0
Migrado y adaptado del proyecto OAuth original para el sistema de chat
"""
import os
import ssl
import certifi
from authlib.integrations.flask_client import OAuth
from flask import session


class OAuthModel:
    """
    Modelo que gestiona la autenticación y autorización de usuarios
    mediante OAuth 2.0 con Google usando Authlib
    """

    def __init__(self, app=None):
        """
        Inicializa el modelo OAuth.
        
        Args:
            app: Aplicación Flask (opcional)
        """
        self.oauth = OAuth()
        self.google = None
        if app:
            self.init_app(app)

    def init_app(self, app):
        """
        Inicializa la configuración de OAuth con Google.
        
        Args:
            app: Aplicación Flask
        """
        self.oauth.init_app(app)

        # Configurar contexto SSL con certificados del sistema
        ssl_context = ssl.create_default_context(cafile=certifi.where())

        # Configuración del cliente OAuth de Google
        self.google = self.oauth.register(
            name='google',
            client_id=os.getenv('GOOGLE_CLIENT_ID'),
            client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
            server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
            client_kwargs={
                'scope': 'openid email profile',
                'verify': certifi.where()  # Usar certificados de certifi
            }
        )

    def get_authorization_url(self, redirect_uri):
        """
        Genera la URL de autorización de Google.
        
        Args:
            redirect_uri: URL de callback después de la autorización
            
        Returns:
            Respuesta de redirección a Google OAuth
        """
        return self.google.authorize_redirect(redirect_uri)

    def get_token(self):
        """
        Obtiene el token de acceso después de la autorización.
        
        Returns:
            Token de acceso OAuth con información del usuario
            
        Raises:
            Exception: Si falla la obtención del token
        """
        return self.google.authorize_access_token()

    def get_user_info(self, token):
        """
        Obtiene la información del usuario desde el token.
        
        Args:
            token: Token de acceso OAuth (dict que contiene 'userinfo')
            
        Returns:
            Diccionario con información del usuario (email, name, picture)
        """
        # El token de Authlib ya contiene la información del usuario en 'userinfo'
        if token and 'userinfo' in token:
            return token['userinfo']
        # Si no está en userinfo, intentar obtenerlo del servidor
        return self.google.userinfo(token=token)

    def save_user_session(self, user_info):
        """
        Guarda la información del usuario en la sesión.
        
        Args:
            user_info: Información del usuario obtenida de Google
        """
        session['oauth_user'] = {
            'email': user_info.get('email'),
            'name': user_info.get('name'),
            'picture': user_info.get('picture'),
            'authenticated': True
        }
        # También guardamos el email como token para el chat
        session['chat_token'] = user_info.get('email')

    def get_current_user(self):
        """
        Obtiene el usuario actual de la sesión.
        
        Returns:
            Información del usuario o None si no está autenticado
        """
        return session.get('oauth_user')

    def get_chat_token(self):
        """
        Obtiene el token (email) para autenticación del chat.
        
        Returns:
            Email del usuario autenticado o None
        """
        return session.get('chat_token')

    def is_authenticated(self):
        """
        Verifica si el usuario está autenticado.
        
        Returns:
            True si el usuario está autenticado, False en caso contrario
        """
        user = self.get_current_user()
        return user is not None and user.get('authenticated', False)

    def logout_user(self):
        """
        Cierra la sesión del usuario eliminando datos de sesión.
        """
        session.pop('oauth_user', None)
        session.pop('chat_token', None)
