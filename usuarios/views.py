# usuarios/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from .forms import CrearUsuarioForm
from django.db.models import Q

def listar_usuarios(request):
    query = request.GET.get('search', '')
    if query:
        # Filtra por nombre de usuario, nombre, apellido o correo electrónico
        usuarios = User.objects.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        ).order_by('username')  # Ordenar por nombre de usuario
    else:
        usuarios = User.objects.all().order_by('username')  # Mostrar todos los usuarios si no hay búsqueda
    
    return render(request, 'usuarios/listar_usuarios.html', {'usuarios': usuarios, 'search': query})

def crear_usuario(request):
    if request.method == 'POST':
        form = CrearUsuarioForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('listar_usuarios')  # Redirige a la vista de lista de usuarios
    else:
        form = CrearUsuarioForm()
    return render(request, 'usuarios/crear_usuarios.html', {'form': form})
