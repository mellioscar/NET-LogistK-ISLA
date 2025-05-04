from django.contrib import messages
from django.shortcuts import redirect
from firebase_admin import auth
from functools import wraps
from NetLogistK.utils.firebase_utils import renew_id_token

class FirebaseAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # URLs que no requieren autenticación
        PUBLIC_URLS = ['/login/', '/logout/', '/static/']
        
        # Si la URL es pública o comienza con /static/, permitir el acceso
        if request.path in PUBLIC_URLS or request.path.startswith('/static/'):
            return self.get_response(request)

        # Verificar el token en la sesión
        id_token = request.session.get('firebase_id_token')
        refresh_token = request.session.get('firebase_refresh_token')
        
        if not id_token:
            messages.error(request, 'Sesión expirada. Por favor, inicie sesión nuevamente.')
            return redirect('login')

        try:
            # Verificar el token con Firebase
            decoded_token = auth.verify_id_token(id_token)
            request.user_token = decoded_token
            request.uid = decoded_token.get('uid')
        except auth.ExpiredIdTokenError:
            # Intentar renovar el token
            if refresh_token:
                try:
                    new_id_token, new_refresh_token = renew_id_token(refresh_token)
                    if new_id_token and new_refresh_token:
                        request.session['firebase_id_token'] = new_id_token
                        request.session['firebase_refresh_token'] = new_refresh_token
                        # Verificar el nuevo token
                        decoded_token = auth.verify_id_token(new_id_token)
                        request.user_token = decoded_token
                        request.uid = decoded_token.get('uid')
                        return self.get_response(request)
                except Exception:
                    pass
            messages.error(request, 'Sesión expirada. Por favor, inicie sesión nuevamente.')
            return redirect('login')
        except auth.InvalidIdTokenError:
            messages.error(request, 'Token inválido. Por favor, inicie sesión nuevamente.')
            return redirect('login')
        except Exception as e:
            messages.error(request, f'Error de autenticación: {str(e)}')
            return redirect('login')

        response = self.get_response(request)
        return response
