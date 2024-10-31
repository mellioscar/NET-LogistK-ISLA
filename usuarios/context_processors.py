# usuarios/context_processors.py

from .models import Profile, PerfilUsuario
from mensajes.models import Mensaje

def user_profile(request):
    # Solo devolver datos si el usuario está autenticado
    if request.user.is_authenticated:
        profile = Profile.objects.filter(user=request.user).first()
        perfil_usuario = PerfilUsuario.objects.filter(user=request.user).first()
        
        # Contar mensajes no leídos del usuario autenticado
        mensajes_no_leidos = Mensaje.objects.filter(receptor=request.user, leido=False).count()

        return {
            'profile': profile,
            'full_name': request.user.get_full_name(),  # Nombre completo del usuario
            'tipo_usuario': perfil_usuario.tipo_usuario if perfil_usuario else None,  # Tipo de usuario
            'mensajes_no_leidos': mensajes_no_leidos,  # Cantidad de mensajes no leídos
        }
    return {}
