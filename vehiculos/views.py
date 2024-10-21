# vehiculos/views.py
from django.shortcuts import render
from .forms import VehiculoForm
from .models import Vehiculo
from django.db.models import Q
from .models import Vehiculo

def listar_vehiculos(request):
    query = request.GET.get('search', '')  # Captura el término de búsqueda desde el formulario
    if query:
        # Filtrar por dominio, marca o modelo
        vehiculos = Vehiculo.objects.filter(
            Q(dominio__icontains=query) |
            Q(marca__icontains=query) |
            Q(modelo__icontains=query)
        ).order_by('marca')  # Ordenar por marca
    else:
        vehiculos = Vehiculo.objects.all().order_by('marca')  # Mostrar todos los vehículos si no hay búsqueda
    
    return render(request, 'vehiculos/listar_vehiculos.html', {'vehiculos': vehiculos, 'search': query})

def crear_vehiculo(request):
    form = VehiculoForm()
    if request.method == 'POST':
        form = VehiculoForm(request.POST)
        if form.is_valid():
            form.save()  # Guarda el nuevo vehículo
            # Redirige a otra página o muestra un mensaje de éxito
    return render(request, 'vehiculos/crear_vehiculos.html', {'form': form})