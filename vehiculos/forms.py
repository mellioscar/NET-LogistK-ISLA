# vehiculos/forms.py
from django import forms
from .models import Vehiculo

class VehiculoForm(forms.ModelForm):
    class Meta:
        model = Vehiculo
        fields = ['dominio', 'marca', 'modelo', 'tipo', 'hidrogrua', 'carretilla', 'anio', 'vtv', 'ruta']
