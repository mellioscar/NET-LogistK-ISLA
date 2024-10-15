from django.shortcuts import render, redirect
# from .models import Vehiculo
# from .forms import VehiculoForm

# # Crear un vehículo
# def crear_vehiculo(request):
#     if request.method == 'POST':
#         form = VehiculoForm(request.POST)
#         if form.is_valid():
#             form.save()
#             return redirect('listar_vehiculos')
#     else:
#         form = VehiculoForm()
#     return render(request, 'vehiculos/crear_vehiculo.html', {'form': form})

# # Listar los vehículos
# def listar_vehiculos(request):
#     vehiculos = Vehiculo.objects.all()
#     return render(request, 'vehiculos/listar_vehiculos.html', {'vehiculos': vehiculos})

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