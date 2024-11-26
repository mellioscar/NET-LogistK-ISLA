# decorators.py
from firebase_admin import auth
from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse

def firebase_login_required(view_func):
    #Decorador para proteger vistas y permitir el acceso solo a usuarios autenticados mediante Firebase.

    def wrapper(request, *args, **kwargs):
        # Obtener el token JWT desde la sesión
        firebase_token = request.session.get("firebase_id_token")  # Token almacenado en la sesión
        if not firebase_token:
            # Si no hay token, redirigir al login con un mensaje de error
            messages.error(request, "Debe iniciar sesión para acceder a esta página.")
            return redirect('login')

        try:
            # Verificar el token con Firebase
            decoded_token = auth.verify_id_token(firebase_token)
            
            # Guardar la información del usuario autenticado en el objeto `request`
            request.firebase_user = decoded_token
            
        except auth.ExpiredIdTokenError:
            # Token ha expirado; redirigir al login
            messages.error(request, "Su sesión ha expirado. Por favor, vuelva a iniciar sesión.")
            return redirect('login')
        
        except auth.InvalidIdTokenError:
            # Token no es válido; redirigir al login
            messages.error(request, "Token de autenticación inválido.")
            return redirect('login')
        
        except Exception as e:
            # Error desconocido; redirigir al login
            print(f"Error desconocido al verificar el token de Firebase: {e}")
            messages.error(request, "Ha ocurrido un error inesperado. Por favor, vuelva a iniciar sesión.")
            return redirect('login')

        # Si todo está correcto, ejecutar la vista original
        return view_func(request, *args, **kwargs)

    return wrapper
