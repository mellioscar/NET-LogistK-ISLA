# parametros/views.py
from django.shortcuts import render, redirect
from firebase_admin import firestore

db = firestore.client()

# Vistas Sucursales
# Listar sucursales
def listar_sucursales(request):
    sucursales_ref = db.collection('sucursales').stream()
    sucursales = [{'id': doc.id, **doc.to_dict()} for doc in sucursales_ref]
    return render(request, 'parametros/listar_sucursales.html', {'sucursales': sucursales})

# Crear sucursal
def crear_sucursal(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        direccion = request.POST.get('direccion')
        latitud = request.POST.get('latitud')
        longitud = request.POST.get('longitud')

        sucursal = {
            'nombre': nombre,
            'direccion': direccion,
            'latitud': float(latitud) if latitud else None,
            'longitud': float(longitud) if longitud else None,
        }
        db.collection('sucursales').add(sucursal)  # Agregar a Firebase
        return redirect('listar_sucursales')

    return render(request, 'parametros/crear_sucursal.html')

# Editar sucursal
def editar_sucursal(request, sucursal_id):
    sucursal_ref = db.collection('sucursales').document(sucursal_id)
    sucursal = sucursal_ref.get().to_dict()

    # Convertir las coordenadas en números si existen
    sucursal['latitud'] = float(sucursal['latitud']) if 'latitud' in sucursal and sucursal['latitud'] else None
    sucursal['longitud'] = float(sucursal['longitud']) if 'longitud' in sucursal and sucursal['longitud'] else None

    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        direccion = request.POST.get('direccion')
        latitud = request.POST.get('latitud')
        longitud = request.POST.get('longitud')

        sucursal_data = {
            'nombre': nombre,
            'direccion': direccion,
            'latitud': float(latitud) if latitud else None,
            'longitud': float(longitud) if longitud else None,
        }

        sucursal_ref.update(sucursal_data)
        return redirect('listar_sucursales')

    return render(request, 'parametros/editar_sucursal.html', {'sucursal': sucursal, 'id': sucursal_id})

# Eliminar sucursal
def eliminar_sucursal(request, sucursal_id):
    db.collection('sucursales').document(sucursal_id).delete()
    return redirect('listar_sucursales')


# Vistas Marcas
# Listar Marcas
def listar_marcas(request):
    marcas_ref = db.collection('marcas').stream()
    marcas = [{'id': doc.id, **doc.to_dict()} for doc in marcas_ref]
    return render(request, 'parametros/listar_marcas.html', {'marcas': marcas})

# Crear Marcas
def crear_marca(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        db.collection('marcas').add({'nombre': nombre})
        return redirect('listar_marcas')
    return render(request, 'parametros/crear_marca.html')

# Editar Marcas
def editar_marca(request, marca_id):
    marca_ref = db.collection('marcas').document(marca_id)
    marca = marca_ref.get().to_dict()
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        marca_ref.update({'nombre': nombre})
        return redirect('listar_marcas')
    return render(request, 'parametros/editar_marca.html', {'marca': marca, 'id': marca_id})

# Eliminar Marcas
def eliminar_marca(request, marca_id):
    db.collection('marcas').document(marca_id).delete()
    return redirect('listar_marcas')


# Vistas Modelos
# Listar Modelos
def listar_modelos(request):
    modelos_ref = db.collection('modelos').stream()
    modelos = [{'id': doc.id, **doc.to_dict()} for doc in modelos_ref]
    return render(request, 'parametros/listar_modelos.html', {'modelos': modelos})

# Crear Modelos
def crear_modelo(request):
    marcas_ref = db.collection('marcas').stream()
    marcas = [{'id': doc.id, 'nombre': doc.to_dict()['nombre']} for doc in marcas_ref]

    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        marca_id = request.POST.get('marca')
        marca_nombre = next((marca['nombre'] for marca in marcas if marca['id'] == marca_id), None)

        db.collection('modelos').add({'nombre': nombre, 'marca_id': marca_id, 'marca_nombre': marca_nombre})
        return redirect('listar_modelos')
    
    return render(request, 'parametros/crear_modelo.html', {'marcas': marcas})

# Editar Modelo
def editar_modelo(request, modelo_id):
    modelo_ref = db.collection('modelos').document(modelo_id)
    modelo = modelo_ref.get().to_dict()

    marcas_ref = db.collection('marcas').stream()
    marcas = [{'id': doc.id, 'nombre': doc.to_dict()['nombre']} for doc in marcas_ref]

    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        marca_id = request.POST.get('marca')
        marca_nombre = next((marca['nombre'] for marca in marcas if marca['id'] == marca_id), None)

        modelo_ref.update({'nombre': nombre, 'marca_id': marca_id, 'marca_nombre': marca_nombre})
        return redirect('listar_modelos')
    
    return render(request, 'parametros/editar_modelo.html', {'modelo': modelo, 'marcas': marcas, 'id': modelo_id})

# Eliminar Modelo
def eliminar_modelo(request, modelo_id):
    db.collection('modelos').document(modelo_id).delete()
    return redirect('listar_modelos')


# Vistas Tipos de Service
# Listar Tipos de Service
def listar_tipos_service(request):
    tipos_service_ref = db.collection('tipos_de_service').stream()
    tipos_service = [{'id': doc.id, **doc.to_dict()} for doc in tipos_service_ref]
    return render(request, 'parametros/listar_tipos_service.html', {'tipos_service': tipos_service})

# Crear Tipo de Service
def crear_tipo_service(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion')

        nuevo_service = {
            'nombre': nombre,
            'descripcion': descripcion,
        }
        db.collection('tipos_de_service').add(nuevo_service)
        return redirect('listar_tipos_service')
    
    return render(request, 'parametros/crear_tipo_service.html')

# Editar Tipo de Service
def editar_tipo_service(request, tipo_service_id):
    tipo_service_ref = db.collection('tipos_de_service').document(tipo_service_id)
    tipo_service = tipo_service_ref.get().to_dict()

    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion')

        tipo_service_data = {
            'nombre': nombre,
            'descripcion': descripcion,
        }
        tipo_service_ref.update(tipo_service_data)
        return redirect('listar_tipos_service')
    
    return render(request, 'parametros/editar_tipo_service.html', {'tipo_service': tipo_service, 'id': tipo_service_id})

# Eliminar Tipo de Service
def eliminar_tipo_service(request, tipo_service_id):
    db.collection('tipos_de_service').document(tipo_service_id).delete()
    return redirect('listar_tipos_service')
