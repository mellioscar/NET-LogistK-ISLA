# zonas/views.py
from django.shortcuts import render, redirect
from firebase_admin import firestore
from django.contrib import messages

db = firestore.client()

def listar_zonas(request):
    zonas_ref = db.collection('zonas')
    zonas = [doc.to_dict() | {'id': doc.id} for doc in zonas_ref.stream()]
    return render(request, 'zonas/listar_zonas.html', {'zonas': zonas})


def crear_zona(request):
    db = firestore.client()
    sucursales_ref = db.collection('sucursales')
    sucursales = [doc.to_dict() for doc in sucursales_ref.stream()]

    if request.method == 'POST':
        data = {
            'nombre': request.POST['nombre'],
            'descripcion': request.POST['descripcion'],
            'sucursal': request.POST['sucursal'],
            'info': request.POST['info'],
        }
        db.collection('zonas').add(data)
        messages.success(request, "Zona creada correctamente.")
        return redirect('listar_zonas')

    return render(request, 'zonas/crear_zona.html', {'sucursales': sucursales})


def editar_zona(request, zona_id):
    db = firestore.client()
    zona_ref = db.collection('zonas').document(zona_id)
    zona = zona_ref.get().to_dict()

    sucursales_ref = db.collection('sucursales')
    sucursales = [doc.to_dict() for doc in sucursales_ref.stream()]

    if request.method == 'POST':
        data = {
            'nombre': request.POST['nombre'],
            'descripcion': request.POST['descripcion'],
            'sucursal': request.POST['sucursal'],
            'info': request.POST['info'],
        }
        zona_ref.update(data)
        messages.success(request, "Zona actualizada correctamente.")
        return redirect('listar_zonas')

    return render(request, 'zonas/editar_zona.html', {'zona': zona, 'sucursales': sucursales})


def eliminar_zona(request, zona_id):
    db.collection('zonas').document(zona_id).delete()
    messages.success(request, f'Zona eliminada correctamente.')
    return redirect('listar_zonas')
