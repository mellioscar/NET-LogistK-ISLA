from django.db import models

class Mensaje(models.Model):
    emisor_uid = models.CharField(max_length=255)  # UID del emisor (Firebase)
    receptor_uid = models.CharField(max_length=255)  # UID del receptor (Firebase)
    contenido = models.TextField()  # Contenido del mensaje
    fecha_envio = models.DateTimeField(auto_now_add=True)  # Fecha y hora de envío
    leido = models.BooleanField(default=False)  # Indicador de si el mensaje ha sido leído

    def __str__(self):
        return f"De {self.emisor_uid} a {self.receptor_uid} - {self.fecha_envio}"
