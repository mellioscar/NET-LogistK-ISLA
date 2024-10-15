from django.contrib.auth.models import User
from django.db import models

class TipoUsuario(models.TextChoices):
    ADMINISTRADOR = 'Administrador', 'Administrador'
    LOGISTICA = 'Logística', 'Logística'
    VENDEDOR = 'Vendedor', 'Vendedor'

class PerfilUsuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    tipo_usuario = models.CharField(
        max_length=20,
        choices=TipoUsuario.choices,
        default=TipoUsuario.LOGISTICA
    )

    def __str__(self):
        return f'{self.user.username} - {self.tipo_usuario}'
