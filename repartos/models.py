# repartos/models.py
from django.db import models

class Reparto(models.Model):
    fecha = models.DateField()  # Fecha en formato dd/mm/aaaa, se manejará en las vistas para asegurar el formato
    nro_reparto = models.IntegerField()
    chofer = models.CharField(max_length=100)
    acompanante = models.CharField(max_length=100, blank=True, null=True)  # Acompañante puede ser opcional
    zona = models.CharField(max_length=100)
    facturas = models.IntegerField()
    estado = models.CharField(max_length=20, choices=[
        ('Abierto', 'Abierto'),
        ('Cerrado', 'Cerrado'),
        ('Finalizado', 'Finalizado')
    ], default='Abierto')
    entregas = models.IntegerField(default=0)
    incompletos = models.IntegerField(default=0)

    def __str__(self):
        return f"Reparto {self.nro_reparto} - {self.zona} ({self.estado})"
