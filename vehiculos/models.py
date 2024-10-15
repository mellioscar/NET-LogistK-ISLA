from django.db import models

class Vehiculo(models.Model):
    # Datos básicos del vehículo
    dominio = models.CharField(max_length=10, unique=True)  # Placa del vehículo
    marca = models.CharField(max_length=50)
    modelo = models.CharField(max_length=50)
    tipo = models.CharField(max_length=20, choices=[('Balancín', 'Balancín'), ('Semi', 'Semi')])
    hidrogrua = models.BooleanField(default=False)  # Indica si tiene hidrogrúa
    carretilla = models.BooleanField(default=False)  # Indica si tiene carretilla elevadora
    fecha_adquisicion = models.DateField()

    def __str__(self):
        return f"{self.marca} {self.modelo} - {self.dominio}"
