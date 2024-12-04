# middleware.py
from django.shortcuts import redirect
from firebase_utils import verify_id_token, renew_id_token
from django.contrib import messages
from usuarios.error_messages import FIREBASE_ERROR_MESSAGES

class FirebaseAuthenticationMiddleware:
    EXCLUDED_PATHS = ['/login/', '/logout/', '/static/']

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Permitir rutas excluidas sin verificación de token
        if any(request.path.startswith(path) for path in self.EXCLUDED_PATHS):
            return self.get_response(request)

        firebase_token = request.session.get("firebase_id_token")
        refresh_token = request.session.get("firebase_refresh_token")

        if not firebase_token:
            print("[MIDDLEWARE] Token de sesión no encontrado. Redirigiendo al login.")
            messages.error(request, FIREBASE_ERROR_MESSAGES.get("TOKEN_EXPIRED", "Tu sesión ha expirado. Por favor, inicia sesión nuevamente."))
            return redirect('login')

        try:
            print("[MIDDLEWARE] Verificando token ID...")
            decoded_token = verify_id_token(firebase_token)
            request.firebase_user = decoded_token

        except Exception as e:
            print(f"[MIDDLEWARE] Error verificando token: {e}. Intentando renovar...")

            # Intentar renovar el token
            if refresh_token:
                new_id_token, new_refresh_token = renew_id_token(refresh_token)
                if new_id_token and new_refresh_token:
                    print("[MIDDLEWARE] Token renovado exitosamente.")
                    request.session["firebase_id_token"] = new_id_token
                    request.session["firebase_refresh_token"] = new_refresh_token
                    request.firebase_user = verify_id_token(new_id_token)
                else:
                    print("[MIDDLEWARE] No se pudo renovar el token. Redirigiendo al login.")
                    messages.error(request, FIREBASE_ERROR_MESSAGES.get("MISSING_REFRESH_TOKEN", "No se pudo renovar el token. Por favor, inicia sesión nuevamente."))
                    return redirect('login')
            else:
                print("[MIDDLEWARE] Token expirado y no hay refresh_token. Redirigiendo al login.")
                messages.error(request, FIREBASE_ERROR_MESSAGES.get("TOKEN_EXPIRED", "Tu sesión ha expirado. Por favor, inicia sesión nuevamente."))
                return redirect('login')

        return self.get_response(request)
