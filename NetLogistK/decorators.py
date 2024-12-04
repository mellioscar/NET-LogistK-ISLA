# decorators.py
from firebase_admin import auth
import requests
from django.shortcuts import redirect
from django.contrib import messages

def firebase_login_required(view_func):
    def wrapper(request, *args, **kwargs):
        firebase_token = request.session.get("firebase_id_token")
        refresh_token = request.session.get("firebase_refresh_token")

        print("Token ID:", firebase_token)
        print("Refresh Token:", refresh_token)

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


# def firebase_login_required(view_func):
#     """
#     Decorador para proteger vistas y permitir el acceso solo a usuarios autenticados mediante Firebase.
#     """
#     def wrapper(request, *args, **kwargs):
#         # Obtener el token JWT desde la sesión
#         firebase_token = request.session.get("firebase_id_token")
#         if not firebase_token:
#             # Si no hay token, redirigir al login con un mensaje de error
#             messages.error(request, "Debe iniciar sesión para acceder a esta página.")
#             return redirect('login')

#         try:
#             # Verificar el token con Firebase
#             decoded_token = auth.verify_id_token(firebase_token)
            
#             # Guardar la información del usuario autenticado en el objeto `request`
#             request.firebase_user = decoded_token

#         except auth.ExpiredIdTokenError:
#             # Token ha expirado; intentar renovar el token
#             refresh_token = request.session.get("firebase_refresh_token")
#             if not refresh_token:
#                 messages.error(request, "Su sesión ha expirado. Por favor, vuelva a iniciar sesión.")
#                 return redirect('login')

#             try:
#                 # Renovar el token usando el endpoint de Firebase
#                 refresh_url = "https://securetoken.googleapis.com/v1/token?key=YOUR_FIREBASE_API_KEY"
#                 response = requests.post(refresh_url, data={
#                     "grant_type": "refresh_token",
#                     "refresh_token": refresh_token
#                 })
#                 response_data = response.json()

#                 if response.status_code == 200:
#                     # Actualizar los tokens en la sesión
#                     request.session["firebase_id_token"] = response_data["id_token"]
#                     request.session["firebase_refresh_token"] = response_data["refresh_token"]
                    
#                     # Verificar el nuevo token
#                     decoded_token = auth.verify_id_token(response_data["id_token"])
#                     request.firebase_user = decoded_token
#                 else:
#                     # Si no se pudo renovar el token, redirigir al login
#                     messages.error(request, "No se pudo renovar su sesión. Por favor, vuelva a iniciar sesión.")
#                     return redirect('login')

#             except Exception as e:
#                 # Manejo de errores al renovar el token
#                 print(f"Error al renovar el token de Firebase: {e}")
#                 messages.error(request, "Ha ocurrido un error al renovar su sesión. Por favor, vuelva a iniciar sesión.")
#                 return redirect('login')

#         except auth.TokenSignError as e:
#             # Error de sincronización de reloj
#             print(f"Error verificando token: {e}")
#             messages.error(request, "Error de sincronización: Verifique el reloj de su dispositivo.")
#             return redirect('login')

#         except auth.InvalidIdTokenError:
#             # Token no es válido; redirigir al login
#             messages.error(request, "Token de autenticación inválido.")
#             return redirect('login')

#         except Exception as e:
#             # Error desconocido; redirigir al login
#             print(f"Error desconocido al verificar el token de Firebase: {e}")
#             messages.error(request, "Ha ocurrido un error inesperado. Por favor, vuelva a iniciar sesión.")
#             return redirect('login')

#         # Si todo está correcto, ejecutar la vista original
#         return view_func(request, *args, **kwargs)

#     return wrapper
