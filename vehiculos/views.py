# vehiculos/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import VehiculoForm
from .models import Vehiculo
from django.db.models import Q

def listar_vehiculos(request):
    query = request.GET.get('search', '')
    if query:
        vehiculos = Vehiculo.objects.filter(
            Q(dominio__icontains=query) |
            Q(marca__icontains=query) |
            Q(modelo__icontains=query)
        ).order_by('marca')
    else:
        vehiculos = Vehiculo.objects.all().order_by('marca')
    
    return render(request, 'vehiculos/listar_vehiculos.html', {'vehiculos': vehiculos, 'search': query})

def crear_vehiculo(request):
    form = VehiculoForm()
    if request.method == 'POST':
        form = VehiculoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Vehículo creado exitosamente.')
            return redirect('ver_vehiculos')
    return render(request, 'vehiculos/crear_vehiculos.html', {'form': form})

def editar_vehiculo(request, vehiculo_id):
    vehiculo = get_object_or_404(Vehiculo, id=vehiculo_id)
    if request.method == 'POST':
        form = VehiculoForm(request.POST, instance=vehiculo)
        if form.is_valid():
            form.save()
            messages.success(request, "Vehículo actualizado exitosamente.")
            return redirect('ver_vehiculos')
    else:
        form = VehiculoForm(instance=vehiculo)
    return render(request, 'vehiculos/editar_vehiculo.html', {'form': form})

def eliminar_vehiculo(request, id):
    vehiculo = get_object_or_404(Vehiculo, id=id)
    if request.method == 'POST':
        vehiculo.delete()
        messages.success(request, 'Vehículo eliminado correctamente.')
    return redirect('ver_vehiculos')
