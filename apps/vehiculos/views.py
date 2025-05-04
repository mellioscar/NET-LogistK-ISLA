# vehiculos/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from NetLogistK.utils.firebase import db
from firebase_admin import firestore
from datetime import datetime

def listar_vehiculos(request):
    search_query = request.GET.get('search', '').strip()
    sort_field = request.GET.get('sort', 'dominio')
    sort_order = request.GET.get('order', 'asc')

    # Obtener todos los vehículos desde Firestore
    vehiculos_ref = db.collection('vehiculos').stream()
    marcas_ref = db.collection('marcas').stream()
    modelos_ref = db.collection('modelos').stream()
    sucursales_ref = db.collection('sucursales').stream()

    # Crear diccionarios para resolver relaciones
    marcas = {marca.id: marca.to_dict().get('nombre') for marca in marcas_ref}
    modelos = {modelo.id: modelo.to_dict().get('nombre') for modelo in modelos_ref}
    sucursales = {sucursal.id: sucursal.to_dict().get('nombre') for sucursal in sucursales_ref}

    vehiculos = []
    for doc in vehiculos_ref:
        vehiculo = doc.to_dict()
        vehiculo['id'] = doc.id
        vehiculo['marca_nombre'] = marcas.get(vehiculo.get('marca'), 'N/A')
        vehiculo['modelo_nombre'] = modelos.get(vehiculo.get('modelo'), 'N/A')
        vehiculo['sucursal_nombre'] = sucursales.get(vehiculo.get('sucursal'), 'N/A')

        # Formatear fechas a dd/mm/yyyy
        for campo in ['fecha_vtv', 'fecha_ruta', 'fecha_seguro']:
            if vehiculo.get(campo):
                try:
                    fecha = datetime.strptime(vehiculo[campo], '%Y-%m-%d')
                    vehiculo[campo] = fecha.strftime('%d/%m/%Y')
                except ValueError:
                    pass

        vehiculos.append(vehiculo)

    # Filtros y orden
    if search_query:
        vehiculos = [v for v in vehiculos if search_query.lower() in v['dominio'].lower()]

    reverse = (sort_order == 'desc')
    vehiculos.sort(key=lambda x: x.get(sort_field, ''), reverse=reverse)

    return render(request, 'vehiculos/listar_vehiculos.html', {
        'vehiculos': vehiculos,
        'search': search_query,
        'sort': sort_field,
        'order': sort_order,
    })


def crear_vehiculo(request):
    # Cargar datos de Firebase
    marcas = [{'id': doc.id, **doc.to_dict()} for doc in db.collection('marcas').stream()]
    modelos = [{'id': doc.id, **doc.to_dict()} for doc in db.collection('modelos').stream()]
    sucursales = [{'id': doc.id, **doc.to_dict()} for doc in db.collection('sucursales').stream()]
    tipos_service = [{'id': doc.id, **doc.to_dict()} for doc in db.collection('tipos_de_service').stream()]

    if request.method == 'POST':
        # Recibir datos del formulario
        marca_id = request.POST.get('marca')
        modelo_id = request.POST.get('modelo')
        sucursal_id = request.POST.get('sucursal')
        tipo_service_id = request.POST.get('tipo_service')

        # Resolver los nombres correspondientes
        marca_nombre = next((m['nombre'] for m in marcas if m['id'] == marca_id), '')
        modelo_nombre = next((m['nombre'] for m in modelos if m['id'] == modelo_id), '')
        sucursal_nombre = next((s['nombre'] for s in sucursales if s['id'] == sucursal_id), '')
        tipo_service_nombre = next((t['nombre'] for t in tipos_service if t['id'] == tipo_service_id), '')

        # Preparar los datos para guardar
        data = {
            'dominio': request.POST.get('dominio'),
            'marca': marca_nombre,
            'modelo': modelo_nombre,
            'sucursal': sucursal_nombre,
            'tipo': request.POST.get('tipo'),
            'anio': request.POST.get('anio'),
            'kilometraje': request.POST.get('kilometraje'),
            'activo': request.POST.get('activo'),
            'fecha_vtv': request.POST.get('fecha_vtv'),
            'alerta_vtv': request.POST.get('alerta_vtv'),
            'fecha_ruta': request.POST.get('fecha_ruta'),
            'alerta_ruta': request.POST.get('alerta_ruta'),
            'fecha_seguro': request.POST.get('fecha_seguro'),
            'alerta_seguro': request.POST.get('alerta_seguro'),
            'tipo_service': tipo_service_nombre,
            'alerta_service': request.POST.get('alerta_service'),
            'observaciones': request.POST.get('observaciones'),
        }

        # Guardar en Firebase
        db.collection('vehiculos').add(data)
        return redirect('ver_vehiculos')

    return render(request, 'vehiculos/crear_vehiculo.html', {
        'marcas': marcas,
        'modelos': modelos,
        'sucursales': sucursales,
        'tipos_service': tipos_service,
    })



def editar_vehiculo(request, vehiculo_id):
    vehiculo_ref = db.collection('vehiculos').document(vehiculo_id)
    vehiculo_data = vehiculo_ref.get().to_dict()

    if not vehiculo_data:
        messages.error(request, 'Vehículo no encontrado.')
        return redirect('ver_vehiculos')

    # Cargar datos para los selects
    marcas = [{'id': doc.id, **doc.to_dict()} for doc in db.collection('marcas').stream()]
    modelos = [{'id': doc.id, **doc.to_dict()} for doc in db.collection('modelos').stream()]
    sucursales = [{'id': doc.id, **doc.to_dict()} for doc in db.collection('sucursales').stream()]
    tipos_service = [{'id': doc.id, **doc.to_dict()} for doc in db.collection('tipos_de_service').stream()]

    if request.method == 'POST':
        # Capturar datos del formulario
        marca_id = request.POST.get('marca')
        modelo_id = request.POST.get('modelo')
        sucursal_id = request.POST.get('sucursal')
        tipo_service_id = request.POST.get('tipo_service')

        # Resolver los nombres correspondientes
        marca_nombre = next((m['nombre'] for m in marcas if m['id'] == marca_id), '')
        modelo_nombre = next((m['nombre'] for m in modelos if m['id'] == modelo_id), '')
        sucursal_nombre = next((s['nombre'] for s in sucursales if s['id'] == sucursal_id), '')
        tipo_service_nombre = next((t['nombre'] for t in tipos_service if t['id'] == tipo_service_id), '')

        # Actualizar los datos del vehículo
        data = {
            'dominio': request.POST.get('dominio'),
            'marca': marca_nombre,
            'modelo': modelo_nombre,
            'sucursal': sucursal_nombre,
            'tipo': request.POST.get('tipo'),
            'anio': request.POST.get('anio'),
            'kilometraje': request.POST.get('kilometraje'),
            'activo': request.POST.get('activo'),
            'fecha_vtv': request.POST.get('fecha_vtv'),
            'alerta_vtv': request.POST.get('alerta_vtv'),
            'fecha_ruta': request.POST.get('fecha_ruta'),
            'alerta_ruta': request.POST.get('alerta_ruta'),
            'fecha_seguro': request.POST.get('fecha_seguro'),
            'alerta_seguro': request.POST.get('alerta_seguro'),
            'tipo_service': tipo_service_nombre,
            'alerta_service': request.POST.get('alerta_service'),
            'observaciones': request.POST.get('observaciones'),
        }

        vehiculo_ref.update(data)
        messages.success(request, 'Vehículo actualizado exitosamente.')
        return redirect('ver_vehiculos')

    # Resolver IDs para que coincidan con los valores en el formulario
    vehiculo_data['marca'] = next((m['id'] for m in marcas if m['nombre'] == vehiculo_data.get('marca')), '')
    vehiculo_data['modelo'] = next((m['id'] for m in modelos if m['nombre'] == vehiculo_data.get('modelo')), '')
    vehiculo_data['sucursal'] = next((s['id'] for s in sucursales if s['nombre'] == vehiculo_data.get('sucursal')), '')

    return render(request, 'vehiculos/editar_vehiculo.html', {
        'vehiculo': vehiculo_data,
        'marcas': marcas,
        'modelos': modelos,
        'sucursales': sucursales,
        'tipos_service': tipos_service,
    })


def eliminar_vehiculo(request, vehiculo_id):
    # Referencia al documento usando el ID generado por Firebase
    vehiculo_ref = db.collection('vehiculos').document(vehiculo_id)
    
    # Eliminar el documento
    vehiculo_ref.delete()
    
    messages.success(request, 'Vehículo eliminado correctamente.')
    return redirect('ver_vehiculos')
