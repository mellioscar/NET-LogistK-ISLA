# recursos/views.py
from django.shortcuts import render, redirect
from firebase_admin import firestore
from firebase import db
from datetime import datetime

def format_date_string(date_str):
    if date_str:
        try:
            # Convertir de 'YYYY-MM-DD' a 'DD/MM/YYYY'
            return datetime.strptime(date_str, '%Y-%m-%d').strftime('%d/%m/%Y')
        except ValueError:
            return date_str  # Si no coincide, devuelve la cadena original
    return "Sin definir"

def listar_recursos(request):
    recursos_ref = db.collection('recursos').stream()
    search_query = request.GET.get('search', '')  # Capturar el término de búsqueda

    # Crear una lista con los datos de los recursos
    recursos_list = [
        {
            **recurso.to_dict(),
            'id': recurso.id,
            'carnet_conducir': format_date_string(recurso.get('carnet_conducir')),
            'psicofisico': format_date_string(recurso.get('psicofisico')),
            'carnet_cargas_generales': format_date_string(recurso.get('carnet_cargas_generales'))
        }
        for recurso in recursos_ref
    ]

    # Filtrar recursos si hay un término de búsqueda
    if search_query:
        recursos_list = [
            recurso for recurso in recursos_list
            if search_query.lower() in recurso.get('nombre', '').lower() or
                search_query.lower() in recurso.get('apellido', '').lower() or
                search_query.lower() in recurso.get('dni', '').lower() or
                search_query.lower() in recurso.get('categoria', '').lower() or
                search_query.lower() in str(recurso.get('legajo', ''))
        ]

    return render(request, 'recursos/listar_recursos.html', {'recursos': recursos_list, 'search': search_query})


def crear_recurso(request):
    if request.method == 'POST':
        # Obtener el id de la sucursal seleccionada
        sucursal_id = request.POST['sucursal']
        
        # Buscar el nombre de la sucursal usando el id
        sucursal_doc = db.collection('sucursales').document(sucursal_id).get()
        sucursal_nombre = sucursal_doc.to_dict().get('nombre', '') if sucursal_doc.exists else ''

        # Crear el recurso con el nombre de la sucursal
        data = {
            'nombre': request.POST['nombre'],
            'apellido': request.POST['apellido'],
            'dni': request.POST['dni'],
            'categoria': request.POST['categoria'],
            'sucursal': sucursal_nombre,  # Guardar el nombre de la sucursal
            'carnet_conducir': request.POST.get('carnet_conducir'),
            'aviso_carnet_conducir': request.POST.get('aviso_carnet_conducir'),
            'psicofisico': request.POST.get('psicofisico'),
            'aviso_psicofisico': request.POST.get('aviso_psicofisico'),
            'carnet_cargas_generales': request.POST.get('carnet_cargas_generales'),
            'aviso_cargas_generales': request.POST.get('aviso_cargas_generales'),
            'legajo': int(request.POST['legajo']),
            'estado': 'Activo'
        }
        db.collection('recursos').document().set(data)
        return redirect('listar_recursos')

    # Obtener sucursales desde Firestore
    sucursales = db.collection('sucursales').stream()
    sucursales_list = [
        {"id": doc.id, **doc.to_dict()} for doc in sucursales
    ]

    return render(request, 'recursos/crear_recurso.html', {'sucursales': sucursales_list})


def editar_recurso(request, recurso_id):
    recurso_ref = db.collection('recursos').document(recurso_id)
    if request.method == 'POST':
        # Obtener el id de la sucursal seleccionada
        sucursal_id = request.POST['sucursal']
        
        # Buscar el nombre de la sucursal usando el id
        sucursal_doc = db.collection('sucursales').document(sucursal_id).get()
        sucursal_nombre = sucursal_doc.to_dict().get('nombre', '') if sucursal_doc.exists else ''

        updated_data = {
            'nombre': request.POST['nombre'],
            'apellido': request.POST['apellido'],
            'dni': request.POST['dni'],
            'categoria': request.POST['categoria'],
            'sucursal': sucursal_nombre,  # Guardar el nombre de la sucursal
            'carnet_conducir': request.POST.get('carnet_conducir'),
            'aviso_carnet_conducir': request.POST.get('aviso_carnet_conducir'),
            'psicofisico': request.POST.get('psicofisico'),
            'aviso_psicofisico': request.POST.get('aviso_psicofisico'),
            'carnet_cargas_generales': request.POST.get('carnet_cargas_generales'),
            'aviso_cargas_generales': request.POST.get('aviso_cargas_generales'),
            'legajo': int(request.POST['legajo']),
        }
        recurso_ref.update(updated_data)
        return redirect('listar_recursos')

    # Obtener el recurso actual
    recurso = recurso_ref.get().to_dict()

    # Obtener todas las sucursales
    sucursales = db.collection('sucursales').stream()
    sucursales_list = [
        {"id": doc.id, **doc.to_dict()} for doc in sucursales
    ]

    # Identificar el id de la sucursal actual del recurso
    sucursal_id_actual = None
    for sucursal in sucursales_list:
        if sucursal["nombre"] == recurso.get("sucursal"):  # Comparar por nombre
            sucursal_id_actual = sucursal["id"]
            break

    recurso["sucursal_id"] = sucursal_id_actual  # Agregar el id de la sucursal al recurso

    return render(request, 'recursos/editar_recurso.html', {
        'recurso': recurso,
        'id': recurso_id,
        'sucursales': sucursales_list,
    })


def eliminar_recurso(request, recurso_id):
    db.collection('recursos').document(recurso_id).delete()
    return redirect('listar_recursos')
