# repartos/forms.py
from django import forms
from .models import Reparto

class RepartoForm(forms.ModelForm):
    fecha = forms.DateField(
        input_formats=['%d/%m/%Y'],  # Define el formato dd/mm/aaaa
        widget=forms.DateInput(attrs={'placeholder': 'dd/mm/aaaa', 'class': 'form-control'})
    )

    class Meta:
        model = Reparto
        fields = ['fecha', 'nro_reparto', 'chofer', 'acompanante', 'zona', 'facturas', 'estado', 'entregas', 'incompletos']
        widgets = {
            'nro_reparto': forms.NumberInput(attrs={'class': 'form-control'}),
            'chofer': forms.TextInput(attrs={'class': 'form-control'}),
            'acompanante': forms.TextInput(attrs={'class': 'form-control'}),
            'zona': forms.TextInput(attrs={'class': 'form-control'}),
            'facturas': forms.NumberInput(attrs={'class': 'form-control'}),
            'estado': forms.Select(attrs={'class': 'form-control'}),
            'entregas': forms.NumberInput(attrs={'class': 'form-control'}),
            'incompletos': forms.NumberInput(attrs={'class': 'form-control'}),
        }
