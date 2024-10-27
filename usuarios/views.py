# usuarios/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserUpdateForm, ProfileUpdateForm, CrearUsuarioForm
from django.contrib.auth import authenticate, login, logout
from .forms import UserUpdateForm, ProfileUpdateForm
from django.db import IntegrityError
from .models import Profile
from django.contrib.auth.models import Group


def login_view(request):
    storage = messages.get_messages(request)
    storage.used = True

    if request.method == 'POST':
        email = request.POST.get('username')
        password = request.POST.get('password')
        
        try:
            user = User.objects.get(email=email)
            user = authenticate(request, username=user.username, password=password)
        except User.DoesNotExist:
            user = None
        
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Correo electrónico o contraseña incorrectos.')

    return render(request, 'usuarios/login.html')


def logout_view(request):
    logout(request)
    storage = messages.get_messages(request)
    return redirect('login')

@login_required
def listar_usuarios(request):
    query = request.GET.get('search', '')
    if query:
        usuarios = User.objects.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) 

        ).order_by('username')
    else:
        usuarios = User.objects.all().order_by('username')
    
    return render(request, 'usuarios/listar_usuarios.html', {'usuarios': usuarios, 'search': query})

def crear_usuario(request):
    if request.method == 'POST':
        form = CrearUsuarioForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuario creado exitosamente.')
            return redirect('listar_usuarios')
    else:
        form = CrearUsuarioForm()
    return render(request, 'usuarios/crear_usuarios.html', {'form': form})


@login_required
def logged_in_user_profile(request):
    user = request.user
    profile = user.profile

    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        
        # Actualización del grupo
        group_id = request.POST.get("group")
        if group_id:
            user.groups.set([group_id])

        # Guardar ambos formularios si son válidos
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            profile = p_form.save(commit=False)
            # Asignar imagen predeterminada si no se proporciona una
            if not profile.image:
                profile.image = 'profile_pics/default.jpg'
            profile.save()
            messages.success(request, 'Tu perfil ha sido actualizado.')
            return redirect('profile_logged_in')  # Redirige para evitar reenvío de formulario
    else:
        u_form = UserUpdateForm(instance=user)
        p_form = ProfileUpdateForm(instance=profile)

    context = {
        'u_form': u_form,
        'p_form': p_form,
        'groups': Group.objects.all(),
        'user_group': user.groups.first(),
        'profile': profile  # Aseguramos que el contexto incluya el perfil
    }

    return render(request, 'usuarios/profile.html', context)



@login_required
def profile(request, user_id):
    user = User.objects.get(id=user_id)
    profile = user.profile

    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)

        group_id = request.POST.get("group")
        if group_id:
            user.groups.set([group_id])

        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            profile = p_form.save(commit=False)
            if not profile.image:
                profile.image = 'profile_pics/default.jpg'
            profile.save()
            messages.success(request, 'El perfil del usuario ha sido actualizado.')
            return redirect('profile', user_id=user.id)
    else:
        u_form = UserUpdateForm(instance=user)
        p_form = ProfileUpdateForm(instance=profile)

    context = {
        'u_form': u_form,
        'p_form': p_form,
        'groups': Group.objects.all(),
        'user_group': user.groups.first(),
        'user_id': user_id,
        'profile': profile  # Incluimos el perfil en el contexto
    }

    return render(request, 'usuarios/profile.html', context)


def register_view(request):
    if request.method == 'POST':
        form = CrearUsuarioForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                return redirect('login')
            except IntegrityError:
                messages.error(request, 'Ocurrió un error al crear el perfil. Es posible que ya exista un perfil asociado con este usuario.')
        else:
            messages.error(request, 'Ocurrió un error en el registro. Por favor, revisa los datos ingresados.')
    else:
        form = CrearUsuarioForm()

    return render(request, 'usuarios/register.html', {'form': form})


@login_required
def eliminar_usuario(request, user_id):
    user = User.objects.get(id=user_id)
    
    if request.method == 'POST':
        user.delete()
        return redirect('listar_usuarios')
    
    return redirect('listar_usuarios')
