# middleware.py
from firebase_admin import auth
from django.shortcuts import redirect

class FirebaseAuthenticationMiddleware:
    """
    Middleware para proteger todas las rutas excepto las excluidas.
    """
    EXCLUDED_PATHS = ['/login/', '/logout/', '/static/']  # Excluir rutas públicas

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Excluir las rutas especificadas
        if request.path in self.EXCLUDED_PATHS:
            return self.get_response(request)

        # Verificar si hay un token válido en la sesión
        firebase_token = request.session.get("firebase_id_token")
        if not firebase_token:
            # Si no hay token, redirigir al login
            return redirect('login')

        try:
            # Verificar el token con Firebase
            decoded_token = auth.verify_id_token(firebase_token)
            request.firebase_user = decoded_token  # Usuario autenticado en Firebase
        except Exception as e:
            print(f"Error verificando token: {e}")
            return redirect('login')

        # Continuar con la solicitud
        return self.get_response(request)
