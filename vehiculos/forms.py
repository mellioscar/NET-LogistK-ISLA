# vehiculos/forms.py
from django import forms
from .models import Vehiculo

class VehiculoForm(forms.ModelForm):
    class Meta:
        model = Vehiculo
        fields = ['dominio', 'marca', 'modelo', 'tipo', 'hidrogrua', 'carretilla', 'anio', 'vtv', 'ruta']
        widgets = {
            'dominio': forms.TextInput(attrs={'class': 'form-control'}),
            'marca': forms.TextInput(attrs={'class': 'form-control'}),
            'modelo': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'hidrogrua': forms.CheckboxInput(attrs={'style': 'width: 20px; height: 20px;'}),
            'carretilla': forms.CheckboxInput(attrs={'style': 'width: 20px; height: 20px;'}),
            'anio': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'aaaa'
            }),
            'vtv': forms.DateInput(format='%d/%m/%Y', attrs={
                'class': 'form-control',
                'placeholder': 'dd/mm/aaaa'
            }),
            'ruta': forms.DateInput(format='%d/%m/%Y', attrs={
                'class': 'form-control',
                'placeholder': 'dd/mm/aaaa'
            }),
        }
