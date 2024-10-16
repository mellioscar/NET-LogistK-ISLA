# repartos/views.py
from django.shortcuts import render, redirect
from .models import Reparto
from .forms import RepartoForm

def listar_repartos(request):
    repartos = Reparto.objects.all().order_by('-fecha')
    return render(request, 'repartos/listar_repartos.html', {'repartos': repartos})

def crear_reparto(request):
    if request.method == 'POST':
        form = RepartoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('listar_repartos')
    else:
        form = RepartoForm()
    return render(request, 'repartos/crear_repartos.html', {'form': form})
