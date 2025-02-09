# mensajes/views.py
from firebase import db  # Importar cliente Firestore desde firebase.py
from firebase_admin.firestore import SERVER_TIMESTAMP  # Para usar timestamps
from firebase_admin import auth  # Para manejar usuarios de Firebase Authentication
from django.contrib import messages  # Para notificaciones en Django
from django.shortcuts import render, redirect
from firebase_admin import firestore  # Importar Firestore desde firebase_admin

from NetLogistK.decorators import firebase_login_required

def enviar_mensaje(request):
    if request.method == "POST":
        receptor_uid = request.POST.get("receptor")
        contenido = request.POST.get("contenido")

        if not receptor_uid or not contenido:
            messages.error(request, "Todos los campos son obligatorios.")
            return redirect('enviar_mensaje')

        if len(contenido) > 200:
            messages.error(request, "El mensaje no puede exceder los 200 caracteres.")
            return redirect('enviar_mensaje')

        try:
            db.collection('mensajes').add({
                'emisor_uid': request.session.get("firebase_uid"),
                'receptor_uid': receptor_uid,
                'contenido': contenido,
                'fecha_envio': firestore.SERVER_TIMESTAMP,
                'leido': False,
            })
            messages.success(request, "El mensaje se ha enviado con éxito.")
        except Exception as e:
            messages.error(request, f"Error enviando mensaje: {e}")

        return redirect('ver_mensajes')

    # Filtrar usuarios por rol Logística
    usuarios_query = db.collection('usuarios').where('rol', '==', 'Logistica').stream()
    usuarios = [{'uid': doc.id, **doc.to_dict()} for doc in usuarios_query]

    return render(request, 'mensajes/enviar_mensaje.html', {'usuarios': usuarios, 'es_respuesta': False})


def ver_mensajes(request):
    try:
        firebase_user = getattr(request, 'firebase_user', None)
        if not firebase_user:
            messages.error(request, "No se pudo obtener el usuario autenticado.")
            return render(request, 'mensajes/ver_mensajes.html', {'mensajes': []})

        uid = firebase_user.get('uid')  # 🔹 Ahora obtenemos el UID como en el dashboard

        # 🔹 Asegurar que los mensajes se ordenan por fecha
        mensajes_query = db.collection('mensajes').where('receptor_uid', '==', uid).stream()

        mensajes = []
        for doc in mensajes_query:
            mensaje = doc.to_dict()
            mensaje['id'] = doc.id  # ID del mensaje para URLs
            mensaje['leido'] = mensaje.get('leido', False)

            # Obtener el nombre del remitente desde Firestore
            emisor_uid = mensaje.get('emisor_uid')
            if emisor_uid:
                emisor_doc = db.collection('usuarios').document(emisor_uid).get()
                if emisor_doc.exists:
                    emisor_data = emisor_doc.to_dict()
                    mensaje['emisor'] = emisor_data.get('nombre', 'Desconocido')
                else:
                    mensaje['emisor'] = 'Desconocido'
            else:
                mensaje['emisor'] = 'Desconocido'

            mensajes.append(mensaje)

    except Exception as e:
        messages.error(request, f"Error obteniendo mensajes: {e}")
        mensajes = []

    return render(request, 'mensajes/ver_mensajes.html', {'mensajes': mensajes})


def leer_mensaje(request, mensaje_id):
    try:
        # Obtener la referencia del mensaje desde Firestore
        mensaje_ref = db.collection('mensajes').document(mensaje_id)
        mensaje = mensaje_ref.get().to_dict()

        if not mensaje:
            messages.error(request, "El mensaje no existe o no tienes permiso para leerlo.")
            return redirect('ver_mensajes')

        mensaje['id'] = mensaje_id  # ID del mensaje para URLs

        # Si el mensaje aún no fue leído, actualizar el estado
        if not mensaje.get('leido', False):
            mensaje_ref.update({"leido": True})

        # Obtener datos del emisor
        emisor_uid = mensaje.get('emisor_uid', '')
        usuario = {}
        if emisor_uid:
            emisor_doc = db.collection('usuarios').document(emisor_uid).get()
            if emisor_doc.exists:
                usuario = emisor_doc.to_dict()
            else:
                usuario = {
                    "nombre": "Desconocido",
                    "apellido": "",
                    "email": "No disponible",
                }

        # Convertir fecha_envio al formato estándar si está presente
        if 'fecha_envio' in mensaje:
            fecha_envio = mensaje['fecha_envio']
            mensaje['fecha_envio'] = fecha_envio.replace(tzinfo=None) if fecha_envio else None

    except Exception as e:
        messages.error(request, f"Error leyendo el mensaje: {e}")
        return redirect('ver_mensajes')

    # Pasar mensaje y datos del usuario al template
    return render(request, 'mensajes/leer_mensaje.html', {'mensaje': mensaje, 'usuario': usuario})


def eliminar_mensaje(request, mensaje_id):
    try:
        mensaje_ref = db.collection('mensajes').document(mensaje_id)
        mensaje = mensaje_ref.get().to_dict()

        if mensaje['receptor_uid'] != request.session.get("firebase_uid"):
            messages.error(request, "No tienes permiso para eliminar este mensaje.")
            return redirect('ver_mensajes')

        mensaje_ref.delete()
        messages.success(request, "Mensaje eliminado con éxito.")
    except Exception as e:
        messages.error(request, f"Error eliminando mensaje: {e}")

    return redirect('ver_mensajes')


def responder_mensaje(request, mensaje_id):
    if request.method == "POST":
        contenido = request.POST.get("contenido")
        emisor_uid = mensaje_id  # El mensaje_id es el UID del emisor

        if not contenido:
            messages.error(request, "El contenido del mensaje no puede estar vacío.")
            return redirect('ver_mensajes')

        if len(contenido) > 200:
            messages.error(request, "El mensaje no puede exceder los 200 caracteres.")
            return redirect('ver_mensajes')

        try:
            db.collection('mensajes').add({
                'emisor_uid': request.session.get("firebase_uid"),
                'receptor_uid': emisor_uid,
                'contenido': contenido,
                'fecha_envio': firestore.SERVER_TIMESTAMP,
                'leido': False,
            })
            messages.success(request, "Respuesta enviada con éxito.")
        except Exception as e:
            messages.error(request, f"Error al enviar la respuesta: {e}")

        return redirect('ver_mensajes')

    # Obtener datos del destinatario (el remitente del mensaje original)
    usuario = {}
    try:
        usuario_doc = db.collection('usuarios').document(mensaje_id).get()
        if usuario_doc.exists:
            usuario = usuario_doc.to_dict()
        else:
            usuario = {
                "nombre": "Desconocido",
                "apellido": "",
                "email": "No disponible",
            }
    except Exception as e:
        messages.error(request, f"Error obteniendo datos del usuario: {e}")

    return render(request, 'mensajes/enviar_mensaje.html', {'usuario': usuario, 'es_respuesta': True})
