# vehiculos/views.py
from django.shortcuts import render
from .forms import VehiculoForm
from .models import Vehiculo

def ver_vehiculos(request):
    # Obtener todos los vehículos
    vehiculos = Vehiculo.objects.all()
    return render(request, 'vehiculos/listar_vehiculos.html', {'vehiculos': vehiculos})

def crear_vehiculo(request):
    form = VehiculoForm()
    if request.method == 'POST':
        form = VehiculoForm(request.POST)
        if form.is_valid():
            form.save()  # Guarda el nuevo vehículo
            # Redirige a otra página o muestra un mensaje de éxito
    return render(request, 'vehiculos/crear_vehiculos.html', {'form': form})