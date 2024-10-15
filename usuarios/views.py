# usuarios/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from .forms import CrearUsuarioForm

def crear_usuario(request):
    if request.method == 'POST':
        form = CrearUsuarioForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('listar_usuarios')  # Redirige a la vista de lista de usuarios
    else:
        form = CrearUsuarioForm()
    return render(request, 'usuarios/crear_usuarios.html', {'form': form})


def ver_usuarios(request):
    usuarios = User.objects.all()
    return render(request, 'usuarios/listar_usuarios.html', {'usuarios': usuarios})
