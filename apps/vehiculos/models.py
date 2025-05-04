# vehiculos/models.py
from django.db import models

class Vehiculo(models.Model):
    dominio = models.CharField(max_length=10, unique=True)
    marca = models.CharField(max_length=50)
    modelo = models.CharField(max_length=50)
    tipo = models.CharField(
        max_length=20,
        choices=[
            ('auto', 'Auto'),
            ('autoelevador', 'Autoelevador'),
            ('camion', 'Camión'),
            ('camioneta', 'Camioneta'),
            ('semirremolque', 'Semirremolque'),
        ]
    )
    hidrogrua = models.BooleanField(default=False)
    carretilla = models.BooleanField(default=False)
    vtv_vencimiento = models.DateField(null=True, blank=True)
    ruta_vencimiento = models.DateField(null=True, blank=True)
    seguro_vencimiento = models.DateField(null=True, blank=True)
    observaciones = models.TextField(null=True, blank=True)
    anio = models.IntegerField("Año de fabricación", null=True, blank=True)

    def __str__(self):
        return f"{self.dominio} - {self.marca} {self.modelo}"
