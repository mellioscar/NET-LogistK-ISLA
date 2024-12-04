# repartos/views.py
from datetime import datetime
from firebase_admin import firestore
from django.shortcuts import redirect, render
from django.contrib import messages

db = firestore.client()

def listar_repartos(request):
    query = request.GET.get('search', '')
    repartos_ref = db.collection('repartos')
    repartos = []

    # Aplicar búsqueda si hay un término de búsqueda
    if query:
        docs = repartos_ref.stream()
        for doc in docs:
            data = doc.to_dict()
            if (query.lower() in str(data.get('nro_reparto', '')).lower() or
                query.lower() in data.get('chofer', '').lower() or
                query.lower() in data.get('acompanante', '').lower() or
                query.lower() in data.get('zona', '').lower()):
                data['id'] = doc.id
                repartos.append(data)
    else:
        # Obtener todos los repartos
        docs = repartos_ref.order_by('fecha', direction=firestore.Query.DESCENDING).stream()
        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id
            repartos.append(data)

    return render(request, 'repartos/listar_repartos.html', {'repartos': repartos, 'search': query})


def crear_reparto(request):
    if request.method == 'POST':
        data = {
            'fecha': request.POST['fecha'],
            'nro_reparto': int(request.POST['nro_reparto']),
            'chofer': request.POST['chofer'],
            'acompanante': request.POST.get('acompanante', ''),
            'zona': request.POST['zona'],
            'facturas': int(request.POST['facturas']),
            'estado': request.POST['estado'],
            'entregas': int(request.POST['entregas']),
            'incompletos': int(request.POST['incompletos']),
        }
        db.collection('repartos').add(data)
        messages.success(request, 'Reparto creado exitosamente.')
        return redirect('listar_repartos')

    # Obtener datos dinámicos
    choferes = db.collection('recursos').where('categoria', 'in', ['Chofer', 'Chofer Gruista']).stream()
    vehiculos = db.collection('vehiculos').where('tipo', '==', 'Camión').stream()
    zonas = db.collection('zonas').stream()

    return render(request, 'repartos/crear_repartos.html', {
        'choferes': [doc.to_dict() for doc in choferes],
        'vehiculos': [doc.to_dict() for doc in vehiculos],
        'zonas': [doc.to_dict() for doc in zonas],
    })


def editar_reparto(request, id):
    reparto_ref = db.collection('repartos').document(id)
    reparto = reparto_ref.get().to_dict()

    if request.method == 'POST':
        data = {
            'fecha': request.POST['fecha'],
            'nro_reparto': int(request.POST['nro_reparto']),
            'chofer': request.POST['chofer'],
            'acompanante': request.POST.get('acompanante', ''),
            'zona': request.POST['zona'],
            'facturas': int(request.POST['facturas']),
            'estado': request.POST['estado'],
            'entregas': int(request.POST['entregas']),
            'incompletos': int(request.POST['incompletos']),
        }
        reparto_ref.update(data)
        messages.success(request, 'Reparto actualizado correctamente.')
        return redirect('listar_repartos')

    return render(request, 'repartos/editar_reparto.html', {'reparto': reparto})


def eliminar_reparto(request, reparto_id):
    reparto_ref = db.collection('repartos').document(reparto_id)
    reparto_ref.delete()
    messages.success(request, f'Reparto con ID {reparto_id} eliminado correctamente.')
    return redirect('listar_repartos')


def repartos_filtrados(request):
    # Obtener parámetros de fecha y estado de la URL
    fecha_str = request.GET.get('fecha')
    estado = request.GET.get('estado')

    # Convertir fecha de string a formato compatible si está presente
    fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date() if fecha_str else None

    # Consultar Firestore
    repartos_ref = db.collection('repartos')
    repartos = []

    if fecha:
        # Filtrar por fecha
        docs = repartos_ref.where('fecha', '==', fecha_str).stream()
        for doc in docs:
            data = doc.to_dict()
            # Filtrar por estado si está presente
            if estado and data.get('estado') != estado:
                continue
            data['id'] = doc.id
            repartos.append(data)
    elif estado:
        # Filtrar solo por estado
        docs = repartos_ref.where('estado', '==', estado).stream()
        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id
            repartos.append(data)
    else:
        # Si no hay filtros, traer todos los repartos
        docs = repartos_ref.stream()
        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id
            repartos.append(data)

    context = {
        'repartos': repartos,
        'fecha': fecha_str,
        'estado': estado,
    }

    return render(request, 'repartos/repartos_filtrados.html', context)
