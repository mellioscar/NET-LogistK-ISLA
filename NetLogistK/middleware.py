# middleware.py
from django.shortcuts import redirect
from firebase_utils import verify_id_token, renew_id_token
from django.contrib import messages
from usuarios.error_messages import FIREBASE_ERROR_MESSAGES
from .firebase_utils import verificar_y_renovar_token
import logging

logger = logging.getLogger(__name__)

class FirebaseAuthenticationMiddleware:
    EXCLUDED_PATHS = ['/login/', '/logout/', '/static/']

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Permitir rutas excluidas sin verificación de token
        if any(request.path.startswith(path) for path in self.EXCLUDED_PATHS):
            return self.get_response(request)

        if 'firebase_token' in request.session:
            try:
                # Verificar y renovar token si es necesario
                token = request.session['firebase_token']
                nuevo_token = verificar_y_renovar_token(token)
                
                if nuevo_token != token:
                    request.session['firebase_token'] = nuevo_token
                    request.firebase_user = verify_id_token(nuevo_token)
                else:
                    request.firebase_user = verify_id_token(token)
            except Exception as e:
                # Solo log si hay error real
                logger.error(f"Error de autenticación: {e}")

        return self.get_response(request)
