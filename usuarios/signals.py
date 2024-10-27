# usuarios/signals.py
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Profile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    # Solo creamos el perfil si es un nuevo usuario y no existe un perfil previo
    if created and not Profile.objects.filter(user=instance).exists():
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    # Guardar el perfil asociado al usuario si ya existe
    if hasattr(instance, 'profile'):
        instance.profile.save()
