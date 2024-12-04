# dispositivos/views.py
from django.shortcuts import render, redirect
from firebase_admin import firestore
from datetime import datetime
from django.contrib import messages

db = firestore.client()

def listar_dispositivos(request):
    dispositivos_ref = db.collection('dispositivos').stream()
    search_query = request.GET.get('search', '')  # Capturar el término de búsqueda

    dispositivos_list = [
        {
            **dispositivo.to_dict(),
            'id': dispositivo.id
        }
        for dispositivo in dispositivos_ref
    ]

    if search_query:
        dispositivos_list = [
            dispositivo for dispositivo in dispositivos_list
            if search_query.lower() in dispositivo.get('nombre', '').lower() or
                search_query.lower() in dispositivo.get('imei', '') or
                search_query.lower() in dispositivo.get('marca', '').lower() or
                search_query.lower() in dispositivo.get('modelo', '').lower()
        ]

    return render(request, 'dispositivos/listar_dispositivos.html', {'dispositivos': dispositivos_list, 'search': search_query})


def crear_dispositivo(request):
    if request.method == 'POST':
        imei = request.POST['imei']
        
        # Validar que el IMEI tenga 15 dígitos
        if not imei.isdigit() or len(imei) != 15:
            messages.error(request, "El IMEI debe contener exactamente 15 dígitos.")
            return render(request, 'dispositivos/crear_dispositivo.html')
        
        # Si pasa la validación, guardar los datos
        data = {
            'imei': imei,
            'nombre': request.POST['nombre'],
            'estado': request.POST['estado'],
            'marca': request.POST['marca'],
            'modelo': request.POST['modelo'],
            'ultima_ubicacion': None,
            'timestamp_ultima_ubicacion': None,
            'vinculacion': request.POST['vinculacion'],
            'frecuencia_actualizacion': int(request.POST['frecuencia_actualizacion']),
        }
        db.collection('dispositivos').add(data)
        return redirect('listar_dispositivos')

    return render(request, 'dispositivos/crear_dispositivo.html')



def editar_dispositivo(request, dispositivo_id):
    dispositivo_ref = db.collection('dispositivos').document(dispositivo_id)
    dispositivo = dispositivo_ref.get().to_dict()

    if request.method == 'POST':
        data = {
            'imei': request.POST['imei'],
            'nombre': request.POST['nombre'],
            'estado': request.POST['estado'],
            'marca': request.POST['marca'],
            'modelo': request.POST['modelo'],
            'vinculacion': request.POST['vinculacion'],
            'frecuencia_actualizacion': int(request.POST['frecuencia_actualizacion']),
        }
        dispositivo_ref.update(data)
        return redirect('listar_dispositivos')

    return render(request, 'dispositivos/editar_dispositivo.html', {'dispositivo': dispositivo})


def eliminar_dispositivo(request, dispositivo_id):
    db.collection('dispositivos').document(dispositivo_id).delete()
    return redirect('listar_dispositivos')
