# usuarios/context_processors.py

from .models import Profile

def user_profile(request):
    # Solo devolver perfil si el usuario está autenticado
    if request.user.is_authenticated:
        profile = Profile.objects.filter(user=request.user).first()
        return {'profile': profile}
    return {}
