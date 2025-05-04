# vehiculos/forms.py
from django import forms

class VehiculoForm(forms.Form):
    dominio = forms.CharField(max_length=10, label="Dominio")
    marca = forms.CharField(max_length=50, label="Marca")
    modelo = forms.CharField(max_length=50, label="Modelo")
    tipo = forms.CharField(max_length=50, label="Tipo")
    hidrogrua = forms.CharField(
        max_length=50,
        required=False,
        label="Modelo de Hidrogrúa",
        widget=forms.TextInput(attrs={'placeholder': 'Detalle el modelo si aplica'})
    )
    carretilla_elevadora = forms.CharField(
        max_length=50,
        required=False,
        label="Modelo de Carretilla",
        widget=forms.TextInput(attrs={'placeholder': 'Detalle el modelo si aplica'})
    )
    observaciones = forms.CharField(widget=forms.Textarea, required=False, label="Observaciones")
    anio = forms.IntegerField(
        required=True,
        label="Año de Fabricación",
        widget=forms.NumberInput(attrs={'placeholder': 'Ingrese el año'})
    )
    # Campos para los vencimientos y alertas
    vtv = forms.DateField(required=False, label="Fecha de VTV", widget=forms.DateInput(attrs={'type': 'date'}))
    alerta_vtv = forms.DateField(required=False, label="Alerta de VTV", widget=forms.DateInput(attrs={'type': 'date'}))
    ruta = forms.DateField(required=False, label="Fecha de RUTA", widget=forms.DateInput(attrs={'type': 'date'}))
    alerta_ruta = forms.DateField(required=False, label="Alerta de RUTA", widget=forms.DateInput(attrs={'type': 'date'}))
    seguro = forms.DateField(required=False, label="Fecha de Seguro", widget=forms.DateInput(attrs={'type': 'date'}))
    alerta_seguro = forms.DateField(required=False, label="Alerta de Seguro", widget=forms.DateInput(attrs={'type': 'date'}))
