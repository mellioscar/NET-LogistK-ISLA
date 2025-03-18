# mensajes/views.py
from firebase import db  # Importar cliente Firestore desde firebase.py
from firebase_admin import firestore  # Importar Firestore desde firebase_admin
from django.contrib import messages  # Para notificaciones en Django
from django.shortcuts import render, redirect
from firebase_admin import auth  # Para manejar usuarios de Firebase Authentication

from NetLogistK.decorators import firebase_login_required

@firebase_login_required
def enviar_mensaje(request):
    if request.method == "POST":
        receptor_uid = request.POST.get("receptor")
        contenido = request.POST.get("contenido")
        emisor_uid = request.session.get("firebase_uid")

        if not emisor_uid:
            messages.error(request, "No se ha podido identificar al emisor.")
            return redirect('enviar_mensaje')

        if not receptor_uid or not contenido:
            messages.error(request, "Todos los campos son obligatorios.")
            return redirect('enviar_mensaje')

        if len(contenido) > 200:
            messages.error(request, "El mensaje no puede exceder los 200 caracteres.")
            return redirect('enviar_mensaje')

        try:
            db.collection('mensajes').add({
                'emisor_uid': emisor_uid,
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


@firebase_login_required
def ver_mensajes(request):
    try:
        firebase_user = getattr(request, 'firebase_user', None)
        if not firebase_user:
            messages.error(request, "No se pudo obtener el usuario autenticado.")
            return render(request, 'mensajes/ver_mensajes.html', {'mensajes': []})

        uid = firebase_user.get('uid')

        # Obtener mensajes ordenados por fecha de envío descendente
        mensajes_query = (db.collection('mensajes')
                         .where('receptor_uid', '==', uid)
                         .order_by('fecha_envio', direction=firestore.Query.DESCENDING)
                         .stream())

        mensajes = []
        for doc in mensajes_query:
            mensaje = doc.to_dict()
            mensaje['id'] = doc.id

            # Asegurar que todos los campos necesarios existen
            mensaje['leido'] = mensaje.get('leido', False)
            mensaje['fecha_envio'] = mensaje.get('fecha_envio')
            mensaje['contenido'] = mensaje.get('contenido', '')

            # Obtener el nombre del remitente
            emisor_uid = mensaje.get('emisor_uid')
            if emisor_uid:
                emisor_doc = db.collection('usuarios').document(emisor_uid).get()
                if emisor_doc.exists:
                    emisor_data = emisor_doc.to_dict()
                    mensaje['emisor'] = f"{emisor_data.get('nombre', '')} {emisor_data.get('apellido', '')}".strip() or 'Desconocido'
                else:
                    mensaje['emisor'] = 'Desconocido'
            else:
                mensaje['emisor'] = 'Desconocido'

            mensajes.append(mensaje)

    except Exception as e:
        messages.error(request, f"Error obteniendo mensajes: {e}")
        mensajes = []

    return render(request, 'mensajes/ver_mensajes.html', {'mensajes': mensajes})


@firebase_login_required
def leer_mensaje(request, mensaje_id):
    try:
        # Verificar que el usuario actual es el receptor legítimo
        firebase_user = getattr(request, 'firebase_user', None)
        if not firebase_user:
            messages.error(request, "No se pudo obtener el usuario autenticado.")
            return redirect('ver_mensajes')

        uid = firebase_user.get('uid')
        
        # Obtener la referencia del mensaje desde Firestore
        mensaje_ref = db.collection('mensajes').document(mensaje_id)
        mensaje = mensaje_ref.get()
        
        if not mensaje.exists:
            messages.error(request, "El mensaje no existe.")
            return redirect('ver_mensajes')
            
        mensaje_data = mensaje.to_dict()
        
        # Verificar que el usuario actual es el receptor legítimo
        if mensaje_data.get('receptor_uid') != uid:
            messages.error(request, "No tienes permiso para leer este mensaje.")
            return redirect('ver_mensajes')

        mensaje_data['id'] = mensaje_id

        # Si el mensaje aún no fue leído, actualizar el estado
        if not mensaje_data.get('leido', False):
            mensaje_ref.update({"leido": True})

        # Obtener datos del emisor
        emisor_uid = mensaje_data.get('emisor_uid', '')
        usuario = {
            "nombre": "Desconocido",
            "apellido": "",
            "email": "No disponible",
        }
        
        if emisor_uid:
            emisor_doc = db.collection('usuarios').document(emisor_uid).get()
            if emisor_doc.exists:
                usuario = emisor_doc.to_dict()

        # Asegurar que fecha_envio existe
        mensaje_data['fecha_envio'] = mensaje_data.get('fecha_envio')

    except Exception as e:
        messages.error(request, f"Error leyendo el mensaje: {e}")
        return redirect('ver_mensajes')

    return render(request, 'mensajes/leer_mensaje.html', {
        'mensaje': mensaje_data,
        'usuario': usuario
    })


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
