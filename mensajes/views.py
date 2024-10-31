# mensajes/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from .models import Mensaje
from django.contrib.auth.decorators import login_required
from django.contrib import messages

@login_required
def enviar_mensaje(request):
    if request.method == "POST":
        receptor_id = request.POST.get("receptor")
        contenido = request.POST.get("contenido")
        
        if not receptor_id or not contenido:
            messages.error(request, "Todos los campos son obligatorios.")
            return redirect('enviar_mensaje')
        
        if len(contenido) > 200:
            messages.error(request, "El mensaje no puede exceder los 200 caracteres.")
            return redirect('enviar_mensaje')

        receptor = User.objects.get(id=receptor_id)
        Mensaje.objects.create(emisor=request.user, receptor=receptor, contenido=contenido)
        messages.success(request, "El mensaje se ha enviado con éxito.")  # Mensaje flash
        return redirect('ver_mensajes')

    usuarios = User.objects.exclude(id=request.user.id)
    return render(request, 'mensajes/enviar_mensaje.html', {'usuarios': usuarios})

@login_required
def ver_mensajes(request):
    mensajes = Mensaje.objects.filter(receptor=request.user).order_by('-fecha_envio')
    return render(request, 'mensajes/ver_mensajes.html', {'mensajes': mensajes})

@login_required
def leer_mensaje(request, mensaje_id):
    mensaje = get_object_or_404(Mensaje, id=mensaje_id, receptor=request.user)
    mensaje.leido = True  # Marca el mensaje como leído
    mensaje.save()
    return render(request, 'mensajes/leer_mensaje.html', {'mensaje': mensaje})

@login_required
def responder_mensaje(request, emisor_id):
    # Obtener el usuario emisor del mensaje al que se está respondiendo
    emisor = get_object_or_404(User, id=emisor_id)
    usuarios = User.objects.exclude(id=request.user.id)

    if request.method == "POST":
        receptor_id = request.POST.get("receptor")
        contenido = request.POST.get("contenido")
        
        # Validación de receptor y contenido (igual que en enviar_mensaje)
        if not receptor_id or not contenido:
            messages.error(request, "Todos los campos son obligatorios.")
            return redirect('responder_mensaje', emisor_id=emisor_id)
        
        if len(contenido) > 200:
            messages.error(request, "El mensaje no puede exceder los 200 caracteres.")
            return redirect('responder_mensaje', emisor_id=emisor_id)

        # Crear el mensaje de respuesta
        receptor = User.objects.get(id=receptor_id)
        Mensaje.objects.create(emisor=request.user, receptor=receptor, contenido=contenido)
        messages.success(request, "Respuesta enviada con éxito.")
        return redirect('ver_mensajes')

    # Pasar el emisor preseleccionado al template
    return render(request, 'mensajes/enviar_mensaje.html', {
        'usuarios': usuarios,
        'emisor': emisor,
    })

@login_required
def eliminar_mensaje(request, mensaje_id):
    mensaje = get_object_or_404(Mensaje, id=mensaje_id, receptor=request.user)
    mensaje.delete()
    messages.success(request, "Mensaje eliminado con éxito.")
    return redirect('ver_mensajes')
