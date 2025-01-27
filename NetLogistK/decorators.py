# decorators.py
from firebase_admin import auth
import requests
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied


def firebase_login_required(view_func):
    def wrapper(request, *args, **kwargs):
        firebase_token = request.session.get("firebase_id_token")
        refresh_token = request.session.get("firebase_refresh_token")

        #print("Token ID:", firebase_token)
        #print("Refresh Token:", refresh_token)

        if not firebase_token:
            messages.error(request, "Debe iniciar sesión.")
            return redirect('login')

        try:
            # Verificar el token
            decoded_token = auth.verify_id_token(firebase_token)
            request.firebase_user = decoded_token
        except auth.ExpiredIdTokenError:
            # Intentar renovar el token
            if refresh_token:
                refresh_url = "https://securetoken.googleapis.com/v1/token?key=YOUR_FIREBASE_API_KEY"
                response = requests.post(refresh_url, data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token
                })
                if response.status_code == 200:
                    data = response.json()
                    new_token = data.get("id_token")
                    request.session["firebase_id_token"] = new_token
                    decoded_token = auth.verify_id_token(new_token)
                    request.firebase_user = decoded_token
                else:
                    messages.error(request, "No se pudo renovar la sesión. Por favor, inicie sesión nuevamente.")
                    return redirect('login')
            else:
                messages.error(request, "La sesión ha expirado. Por favor, vuelva a iniciar sesión.")
                return redirect('login')
        except Exception as e:
            print(f"Decorators: Error verificando token: {e}")
            messages.error(request, "Error al verificar la autenticación.")
            return redirect('login')

        return view_func(request, *args, **kwargs)
    return wrapper


def roles_permitidos(*roles_permitidos):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                raise PermissionDenied("Usuario no autenticado.")
            
            if not hasattr(request.user, 'rol') or request.user.rol not in roles_permitidos:
                raise PermissionDenied("No tienes permiso para realizar esta acción.")
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
