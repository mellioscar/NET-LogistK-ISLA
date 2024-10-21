# repartos/views.py
from django.shortcuts import get_object_or_404, redirect, render
from .models import Reparto
from .forms import RepartoForm
from django.db.models import Q

def listar_repartos(request):
    query = request.GET.get('search', '') 
    if query:
        repartos = Reparto.objects.filter(
            Q(nro_reparto__icontains=query) |  # Buscar en el campo Nro de Reparto
            Q(chofer__icontains=query) |       # Buscar en el campo Chofer
            Q(acompanante__icontains=query) |  # Buscar en el campo Acompañante
            Q(zona__icontains=query)           # Buscar en el campo Zona
        ).order_by('-fecha')
    else:
        repartos = Reparto.objects.all().order_by('-fecha')  # Mostrar todos los repartos si no hay búsqueda
    
    return render(request, 'repartos/listar_repartos.html', {'repartos': repartos, 'search': query})

def crear_reparto(request):
    if request.method == 'POST':
        form = RepartoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('listar_repartos')
    else:
        form = RepartoForm()
    return render(request, 'repartos/crear_repartos.html', {'form': form})

def editar_reparto(request, id):
    reparto = get_object_or_404(Reparto, id=id)
    if request.method == 'POST':
        form = RepartoForm(request.POST, instance=reparto)
        if form.is_valid():
            form.save()
            print("Formulario guardado correctamente")
            return redirect('listar_repartos')
        else:
            print("El formulario no es válido")
    else:
        form = RepartoForm(instance=reparto)
    return render(request, 'repartos/editar_reparto.html', {'form': form})


def eliminar_reparto(id):
    reparto = get_object_or_404(Reparto, id=id)
    reparto.delete()
    return redirect('listar_repartos')

