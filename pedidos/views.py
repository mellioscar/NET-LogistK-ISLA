# pedidos/views.py
from django.shortcuts import render, redirect, get_object_or_404
#from django.http import HttpResponse
import openpyxl
from firebase_admin import firestore
from datetime import datetime
from django.contrib import messages
import re
from django.http import JsonResponse
import pandas as pd


db = firestore.client()

def agregar_pedidos(request):
    try:
        if request.method == 'POST':
            reparto_id = request.POST.get('reparto')

            # Depuración del ID del reparto
            print(f"ID del reparto recibido: {reparto_id}")

            # Validar selección de reparto
            if not reparto_id:
                messages.error(request, "Reparto no seleccionado.")
                return redirect('agregar_pedidos')

            # Recuperar y verificar el reparto
            reparto_doc = db.collection('repartos').document(reparto_id).get()

            if not reparto_doc.exists:
                print("El reparto no existe en la base de datos.")
                messages.error(request, "El reparto seleccionado no existe.")
                return redirect('agregar_pedidos')

            # Obtener datos de la sucursal del usuario
            sucursal_nombre = request.session.get('user_sucursal', None)
            if not sucursal_nombre:
                messages.error(request, "El usuario no tiene una sucursal asignada.")
                return redirect('agregar_pedidos')

            # Obtener código de la sucursal
            sucursal_query = db.collection('sucursales').where('nombre', '==', sucursal_nombre).stream()
            sucursal_doc = next(sucursal_query, None)
            sucursal_codigo = sucursal_doc.to_dict().get('codigo', 'SIN-CODIGO') if sucursal_doc else 'SIN-CODIGO'

            reparto_data = reparto_doc.to_dict()
            print(f"Datos del reparto recuperado: {reparto_data}")

            # Obtener número de reparto
            nro_reparto = reparto_doc.to_dict().get('nro_reparto', 'Desconocido')

            # Verificar estado_reparto en lugar de estado
            if reparto_data.get('estado_reparto') != 'Abierto':
                print("El estado del reparto no es 'Abierto'.")
                messages.error(request, "El reparto seleccionado no está en estado 'Abierto'.")
                return redirect('agregar_pedidos')

            # Procesar pedidos nuevos
            pedidos_nuevos = []
            for key in request.POST.keys():
                if key.startswith('codigo_cliente_'):
                    index = key.split('_')[-1]
                    factura = request.POST.get(f'factura_{index}')
                    if not factura:
                        continue
                    nro_pedido = f"{sucursal_codigo}-{nro_reparto}-{factura}"
                    pedido = {
                        'nro_pedido': nro_pedido,
                        'codigo_cliente': request.POST.get(f'codigo_cliente_{index}', ''),
                        'nombre': request.POST.get(f'nombre_{index}', ''),
                        'calle_numero': request.POST.get(f'calle_numero_{index}', ''),
                        'ciudad': request.POST.get(f'ciudad_{index}', ''),
                        'provincia': request.POST.get(f'provincia_{index}', ''),
                        'telefono': request.POST.get(f'telefono_{index}', ''),
                        'email': request.POST.get(f'email_{index}', ''),
                        'factura': request.POST.get(f'factura_{index}', ''),
                        'peso': float(request.POST.get(f'peso_{index}', 0)),
                        'estado': request.POST.get(f'estado_{index}', 'Pendiente'),
                        'reparto': reparto_id,
                        'fecha': datetime.today().strftime('%Y-%m-%d'),
                    }
                    pedidos_nuevos.append(pedido)

            # Guardar pedidos nuevos
            for pedido in pedidos_nuevos:
                db.collection('pedidos').add(pedido)

            # Procesar actualizaciones de pedidos existentes
            for key in request.POST.keys():
                if key.startswith('peso_existente_'):
                    pedido_id = key.split('_')[-1]
                    peso = float(request.POST.get(key, 0))
                    db.collection('pedidos').document(pedido_id).update({'peso': peso})

            messages.success(request, "Pedidos procesados correctamente.")
            return redirect('agregar_pedidos')

        # Manejo de solicitudes GET
        repartos_query = db.collection('repartos').where('estado_reparto', '==', 'Abierto').stream()
        repartos = []
        for doc in repartos_query:
            data = doc.to_dict()
            data['id'] = doc.id
            data['chofer_nombre'] = data.get('chofer', {}).get('nombre', '')
            repartos.append(data)

        reparto_id = request.GET.get('reparto_id', None)
        reparto_seleccionado_data = None
        pedidos_existentes = []

        if reparto_id:
            reparto_doc = db.collection('repartos').document(reparto_id).get()
            if reparto_doc.exists:
                reparto_seleccionado_data = reparto_doc.to_dict()
                reparto_seleccionado_data['id'] = reparto_doc.id

                # Obtener pedidos del reparto seleccionado
                pedidos_query = db.collection('pedidos').where('reparto', '==', reparto_id).stream()
                for doc in pedidos_query:
                    pedido = doc.to_dict()
                    pedido['id'] = doc.id
                    pedidos_existentes.append(pedido)

        return render(request, 'pedidos/agregar_pedidos.html', {
            'repartos': repartos,
            'reparto_seleccionado': reparto_id,
            'reparto_seleccionado_data': reparto_seleccionado_data,
            'pedidos_existentes': pedidos_existentes
        })

    except Exception as e:
        print(f"Error al procesar pedidos: {e}")
        messages.error(request, f"Ocurrió un error: {e}")
        return redirect('agregar_pedidos')


def obtener_pedidos(request):
    reparto_id = request.GET.get('reparto_id')

    if not reparto_id:
        return JsonResponse({'error': 'ID de reparto no proporcionado'}, status=400)

    try:
        pedidos_query = db.collection('pedidos').where('reparto', '==', reparto_id).stream()
        pedidos = []
        for doc in pedidos_query:
            pedido = doc.to_dict()
            pedido['id'] = doc.id  # Incluir el ID del documento
            pedidos.append(pedido)

        return JsonResponse({'pedidos': pedidos}, status=200)
    except Exception as e:
        return JsonResponse({'error': f'Error al obtener pedidos: {str(e)}'}, status=500)

def listar_pedidos(request):
    query = request.GET.get('search', '').strip()
    pedidos_ref = db.collection('pedidos')
    pedidos = []

    try:
        # Obtener todos los pedidos
        docs = pedidos_ref.stream()

        for doc in docs:
            pedido = doc.to_dict()
            pedido['id'] = doc.id

            # Obtener información del reparto relacionado
            reparto_id = pedido.get('reparto')
            if reparto_id:
                reparto_doc = db.collection('repartos').document(reparto_id).get()
                if reparto_doc.exists:
                    pedido['nro_reparto'] = reparto_doc.to_dict().get('nro_reparto', 'Desconocido')
                else:
                    pedido['nro_reparto'] = 'Desconocido'
            else:
                pedido['nro_reparto'] = 'Sin Reparto'

            # Añadir el pedido a la lista
            pedidos.append(pedido)

    except Exception as e:
        print("Error al listar pedidos:", e)
        messages.error(request, f"Error al listar pedidos: {e}")

    return render(request, 'pedidos/listar_pedidos.html', {
        'pedidos': pedidos,
        'search': query
    })


# Validaciones
def validar_email(email):
    patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(patron, email) is not None

def validar_telefono(telefono):
    patron = r'^\+?\d{10,15}$'
    return re.match(patron, telefono) is not None

def importar_y_previsualizar_pedidos(request):
    pedidos_validos = []
    pedidos_invalidos = []
    
    if request.method == 'POST':
        if 'archivo' in request.FILES:
            archivo = request.FILES['archivo']
            try:
                df = pd.read_csv(archivo, delimiter=",", dtype=str)
                
                for idx, row in df.iterrows():
                    pedido = {
                        'pedido': row['Pedido'],
                        'reparto': row['Reparto'],
                        'cliente': {
                            'nombre': row['Cliente'],
                            'direccion': {
                                'calle': row['Calle y Número'],
                                'ciudad': row['Ciudad'],
                                'provincia': row['Provincia/Estado']
                            },
                            'email': row['Email'] if validar_email(row['Email']) else "No informado",
                            'telefono': row['Teléfono (con código de país)'] if validar_telefono(row['Teléfono (con código de país)']) else "No informado"
                        },
                        'fecha_salida': row['Fecha Salida'],
                        'vehiculo': row['Vehículo'],
                        'estado_pedido': 'Asignado',
                        'productos': [{
                            'codigo_producto': row['Código de Producto'],
                            'descripcion_producto': row['Descripción del Producto'],
                            'cantidad': row['Cantidad'],
                            'peso': row['Peso'].replace(".", ",")
                        }]
                    }
                    
                    errores = []
                    if row['Peso'] == "0":
                        errores.append("El peso debe ser mayor a 0.")
                    
                    if errores:
                        pedidos_invalidos.append({'fila': idx + 2, 'errores': errores, 'pedido': pedido})
                    else:
                        pedidos_validos.append(pedido)
            
            except Exception as e:
                messages.error(request, f"Error al procesar el archivo: {e}")
                return redirect('importar_pedidos')
        
        elif 'guardar_pedidos' in request.POST:
            pedidos_validos = eval(request.POST.get('pedidos_validos', '[]'))
            
            for pedido in pedidos_validos:
                doc_ref = db.collection('pedidos').add(pedido)
                for producto in pedido['productos']:
                    db.collection('pedidos').document(doc_ref[1].id).collection('productos').add(producto)
            
            messages.success(request, "Pedidos guardados exitosamente en Firestore.")
            return redirect('listar_pedidos')
    
    return render(request, 'pedidos/importar_y_previsualizar.html', {
        'pedidos_validos': pedidos_validos,
        'pedidos_invalidos': pedidos_invalidos,
    })


def guardar_pedidos(request):
    if request.method == 'POST':
        pedidos = request.POST.getlist('pedidos')
        for pedido in pedidos:
            db.collection('pedidos').add(pedido)
        messages.success(request, "Pedidos guardados exitosamente.")
        return redirect('listar_pedidos')

def eliminar_pedido(request, pedido_id):
    if request.method == "POST":
        try:
            # Ubicación en Firestore (ajústala según tu estructura de datos)
            pedido_ref = db.collection('pedidos').document(pedido_id)
            pedido_ref.delete()  # Eliminar el pedido de Firestore

            return JsonResponse({"success": True, "message": "Pedido eliminado correctamente."})
        except Exception as e:
            return JsonResponse({"success": False, "message": f"Error eliminando el pedido: {str(e)}"})
    
    return JsonResponse({"success": False, "message": "Método no permitido."}, status=400)
