# pedidos/views.py
from django.shortcuts import render, redirect, get_object_or_404
import openpyxl
from firebase_admin import firestore
from datetime import datetime, timedelta
from django.contrib import messages
import re
from django.http import JsonResponse
import pandas as pd
from firebase_admin import credentials
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import folium
import requests
from opencage.geocoder import OpenCageGeocode
from geopy.extra.rate_limiter import RateLimiter
from django.conf import settings
import os
import json
# Inicializar Firestore
db = firestore.client()

def get_google_api_key():
    with open('secrets/API KEYS.json') as f:
        keys = json.load(f)
        return keys['API_KEY_GOOGLE']

API_KEY_GOOGLE = get_google_api_key()

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


#def obtener_pedidos(request):
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
    try:
        pedidos = []
        repartos_ref = db.collection('repartos')
        
        for reparto in repartos_ref.stream():
            pedidos_ref = reparto.reference.collection('pedidos')
            for pedido in pedidos_ref.stream():
                pedido_data = pedido.to_dict()
                pedido_data['id'] = pedido.id  # Agregar el ID del documento
                pedido_data['nro_reparto'] = reparto.get('nro_reparto')
                pedidos.append(pedido_data)
        
        return render(request, 'pedidos/listar_pedidos.html', {'pedidos': pedidos})
    except Exception as e:
        messages.error(request, f'Error al listar pedidos: {str(e)}')
        return redirect('dashboard')

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
    errores_log = []
    datos_reparto = {
        'numero': '',
        'vehiculo': '',
        'fecha_salida': datetime.now().strftime('%Y-%m-%d')  # Fecha por defecto
    }

    if request.method == 'POST' and request.FILES.get('archivo'):
        try:
            archivo = request.FILES['archivo']
            df = pd.read_excel(archivo, sheet_name=0, dtype=str)
            df.columns = df.columns.str.strip()
            
            if len(df) > 0:
                fecha_str = str(df.iloc[0]['Fecha Salida']).strip()
                try:
                    fecha_obj = pd.to_datetime(fecha_str)
                    fecha_formateada = fecha_obj.strftime('%Y-%m-%d')  # Formato para input type="date"
                except:
                    fecha_formateada = datetime.now().strftime('%Y-%m-%d')

                datos_reparto = {
                    'numero': str(df.iloc[0]['Reparto']).strip(),
                    'vehiculo': str(df.iloc[0]['Vehículo']).strip(),
                    'fecha_salida': fecha_formateada
                }

            pedidos_agrupados = {}
            for index, row in df.iterrows():
                try:
                    nro_factura = str(row['Factura']).strip()
                    peso = float(str(row['Peso']).replace(',', '.')) if row['Peso'] else 0.0
                    
                    if nro_factura not in pedidos_agrupados:
                        direccion_completa = f"{str(row['Dirección']).strip()}"
                        if row['Localidad'].strip():
                            direccion_completa += f" - {str(row['Localidad']).strip()}"
                        
                        # Obtener coordenadas usando la función existente
                        coordenadas = geocode_google(direccion_completa)
                        
                        pedidos_agrupados[nro_factura] = {
                            'nro_factura': nro_factura,
                            'nombre': str(row['Cliente']).strip(),
                            'direccion': direccion_completa,
                            'email': str(row['Email']).strip(),
                            'telefono': str(row['Teléfono (con código de país)']).strip(),
                            'peso_total': peso,
                            'fecha': fecha_formateada,
                            'latitud': coordenadas[0] if coordenadas else None,
                            'longitud': coordenadas[1] if coordenadas else None,
                            'articulos': []
                        }
                    else:
                        pedidos_agrupados[nro_factura]['peso_total'] += peso

                    articulo = {
                        'codigo': str(row['Artículo']).strip(),
                        'descripcion': str(row['Descripción del artículo']).strip(),
                        'cantidad': str(row['Cantidad']).strip(),
                        'peso': peso
                    }
                    pedidos_agrupados[nro_factura]['articulos'].append(articulo)

                except Exception as e:
                    errores_log.append(f"Error en fila {index + 2}: {str(e)}")
                    pedidos_invalidos.append({
                        'fila': index + 2,
                        'errores': [str(e)],
                        'pedido': row.to_dict()
                    })

            pedidos_validos = list(pedidos_agrupados.values())
            request.session['pedidos_temp'] = pedidos_validos
            request.session['datos_reparto_temp'] = datos_reparto
            request.session.save()

        except Exception as e:
            messages.error(request, f"Error al procesar el archivo: {str(e)}")
            return redirect('importar_y_previsualizar_pedidos')

    elif request.POST.get('confirmar_importacion'):
        try:
            chofer_id = request.POST.get('chofer')
            zona_id = request.POST.get('zona')
            fecha_salida = request.POST.get('fecha_salida')
            pedidos_data = request.session.get('pedidos_temp', [])
            datos_reparto = request.session.get('datos_reparto_temp', {})

            if not chofer_id or not zona_id or not fecha_salida:
                messages.error(request, "Debe seleccionar un chofer, una zona y una fecha")
                return redirect('importar_y_previsualizar_pedidos')

            # Obtener datos de la zona
            zona_doc = db.collection('zonas').document(zona_id).get()
            zona_data = zona_doc.to_dict()

            # Obtener datos del chofer
            chofer_ref = db.collection('recursos').document(chofer_id)
            chofer_data = chofer_ref.get().to_dict()
            nombre_completo = f"{chofer_data['nombre']} {chofer_data.get('apellido', '')}"

            # Convertir fecha a formato DD-MM-YYYY para almacenar
            fecha_obj = datetime.strptime(fecha_salida, '%Y-%m-%d')
            fecha_formateada = fecha_obj.strftime('%d-%m-%Y')

            # Crear el reparto
            reparto_data = {
                'nro_reparto': datos_reparto['numero'],
                'fecha_salida': datetime.combine(fecha_obj.date(), datetime.min.time()),
                'fecha_creacion': datetime.now(),
                'chofer': {
                    'id': chofer_id,
                    'nombre': chofer_data['nombre'],
                    'apellido': chofer_data.get('apellido', ''),
                    'nombre_completo': nombre_completo
                },
                'vehiculo': datos_reparto['vehiculo'],
                'zona': zona_data['nombre'],
                'estado_reparto': 'Abierto',
                'sucursal': request.session.get('user_sucursal')
            }

            # Crear documento de reparto
            nuevo_reparto = db.collection('repartos').document()
            nuevo_reparto.set(reparto_data)

            # Crear pedidos como subcolección del reparto
            pedidos_ref = nuevo_reparto.collection('pedidos')
            for pedido in pedidos_data:
                pedido_data = {
                    'nro_factura': pedido['nro_factura'],
                    'cliente': pedido['nombre'],
                    'direccion': pedido['direccion'],
                    'email': pedido['email'],
                    'telefono': pedido['telefono'],
                    'peso_total': float(pedido['peso_total']),
                    'fecha': fecha_formateada,
                    'estado': 'Asignado',
                    'articulos': pedido['articulos'],
                    'fecha_creacion': datetime.now().strftime('%d-%m-%Y')
                }
                
                pedidos_ref.document().set(pedido_data)

            # Limpiar sesión
            del request.session['pedidos_temp']
            del request.session['datos_reparto_temp']
            request.session.save()

            messages.success(request, "Reparto y pedidos creados exitosamente")
            return redirect('listar_repartos')

        except Exception as e:
            messages.error(request, f"Error al procesar la importación: {str(e)}")
            return redirect('importar_y_previsualizar_pedidos')

    # Consultas para obtener choferes y zonas
    choferes = db.collection("recursos").where("categoria", "in", ["Chofer", "Chofer Gruista"]).stream()
    zonas = db.collection("zonas").stream()
    
    context = {
        'pedidos_validos': pedidos_validos,
        'pedidos_invalidos': pedidos_invalidos,
        'errores_log': errores_log,
        'datos_reparto': datos_reparto,
        'choferes': [{
            'id': doc.id,
            'nombre': doc.to_dict()['nombre'],
            'apellido': doc.to_dict().get('apellido', ''),
            'nombre_completo': f"{doc.to_dict()['nombre']} {doc.to_dict().get('apellido', '')}"
        } for doc in choferes],
        'zonas': [doc.to_dict() | {"id": doc.id} for doc in zonas],
        'peso_total': round(sum(float(pedido.get('peso_total', 0)) for pedido in pedidos_validos), 2),
        'google_api_key': API_KEY_GOOGLE  # Asegurarse de que la API key esté disponible
    }
    
    return render(request, 'pedidos/importar_y_previsualizar.html', context)


#def guardar_pedidos(request):
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


def geocode_google(direccion):
    """Obtiene coordenadas precisas desde Google Maps API."""
    
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={direccion}&key={API_KEY_GOOGLE}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        if data['results']:
            location = data['results'][0]['geometry']['location']
            return location['lat'], location['lng']
    
    return None

def generar_mapa(direccion, coordenadas=None):
    try:
        # Si se proporcionan coordenadas, usarlas directamente
        if coordenadas:
            lat, lon = coordenadas
        else:
            # Si no, obtenerlas con geocoding
            coordenadas = geocode_google(direccion)
            if coordenadas:
                lat, lon = coordenadas
            else:
                # Si no encuentra la ubicación, mostrar mapa regional
                print("Ubicación no encontrada, mostrando mapa regional")
                return None

        # Crear mapa centrado en la ubicación
        m = folium.Map(
            location=[lat, lon],
            zoom_start=14
        )

        # Agregar marcador
        folium.Marker(
            [lat, lon],
            popup=direccion,
            icon=folium.Icon(color='red', icon='info-sign')
        ).add_to(m)

        # Configurar el mapa
        m.fit_bounds(m.get_bounds())

        # Generar HTML del mapa
        mapa_html = m._repr_html_()
        return mapa_html

    except Exception as e:
        print(f"Error al generar mapa: {e}")
        return None


def obtener_detalle_pedido(request, pedido_id):
    try:
        # Primero necesitamos encontrar el reparto que contiene este pedido
        repartos_ref = db.collection('repartos')
        repartos = repartos_ref.stream()
        
        pedido_data = None
        reparto_data = None
        
        # Buscar en cada reparto
        for reparto in repartos:
            # Buscar el pedido en la subcolección de pedidos
            pedido_doc = reparto.reference.collection('pedidos').document(pedido_id).get()
            
            if pedido_doc.exists:
                pedido_data = pedido_doc.to_dict()
                pedido_data['id'] = pedido_doc.id
                reparto_data = reparto.to_dict()
                break
        
        if not pedido_data:
            return JsonResponse({'error': 'Pedido no encontrado'}, status=404)
        
        # Agregar información del reparto al pedido
        pedido_data['nro_reparto'] = reparto_data.get('nro_reparto', 'Sin asignar')
        pedido_data['fecha_reparto'] = reparto_data.get('fecha', 'Sin fecha')
        
        if pedido_data:
            # Agregar peso total
            pedido_data['peso_total'] = float(pedido_data.get('peso_total', 0))
            
            # Agregar coordenadas por defecto de la zona
            pedido_data['ubicacion'] = {
                'lat': -39.044,  # Coordenadas de Neuquén
                'lon': -67.579
            }
            
            # Generar mapa
            if pedido_data.get('direccion'):
                mapa_html = generar_mapa(pedido_data['direccion'])
                pedido_data['mapa_html'] = mapa_html
        
        return JsonResponse(pedido_data)
    except Exception as e:
        print(f"Error al obtener detalles del pedido: {e}")
        return JsonResponse({'error': str(e)}, status=500)


def detalles_pedido(request, pedido_id):
    try:
        # Obtener el documento del pedido
        pedido_doc = db.collection('pedidos').document(pedido_id).get()
        
        if not pedido_doc.exists:
            return JsonResponse({'error': 'Pedido no encontrado'}, status=404)
        
        # Obtener los datos del pedido
        pedido_data = pedido_doc.to_dict()
        pedido_data['id'] = pedido_doc.id
        
        # Obtener información del reparto si existe
        reparto_id = pedido_data.get('reparto_id')
        if reparto_id:
            reparto_doc = db.collection('repartos').document(reparto_id).get()
            if reparto_doc.exists:
                reparto_data = reparto_doc.to_dict()
                pedido_data['nro_reparto'] = reparto_data.get('nro_reparto', 'Desconocido')
        
        return JsonResponse(pedido_data)
        
    except Exception as e:
        print("Error al obtener detalles del pedido:", e)
        return JsonResponse({'error': str(e)}, status=500)


@csrf_protect
@require_POST
def actualizar_estado_articulo(request, pedido_id):
    try:
        codigo_articulo = request.POST.get('codigo_articulo')
        nuevo_estado = request.POST.get('estado')
        
        # Obtener el pedido
        pedido_ref = db.collection('pedidos').document(pedido_id)
        pedido_doc = pedido_ref.get()
        
        if not pedido_doc.exists:
            return JsonResponse({'success': False, 'error': 'Pedido no encontrado'})
            
        pedido_data = pedido_doc.to_dict()
        articulos = pedido_data.get('articulos', [])
        
        # Actualizar el estado del artículo
        for articulo in articulos:
            if articulo['codigo'] == codigo_articulo:
                articulo['estado'] = nuevo_estado
                break
        
        # Guardar los cambios
        pedido_ref.update({
            'articulos': articulos
        })
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        print("Error al actualizar estado del artículo:", e)
        return JsonResponse({'success': False, 'error': str(e)})

def generar_mapa_view(request):
    direccion = request.GET.get('direccion')
    lat = request.GET.get('lat')
    lng = request.GET.get('lng')
    
    if direccion and lat and lng:
        try:
            # Convertir las coordenadas reemplazando coma por punto
            lat = float(lat.replace(',', '.'))
            lng = float(lng.replace(',', '.'))
            
            # Usar las coordenadas proporcionadas
            mapa_html = generar_mapa(direccion, coordenadas=(lat, lng))
            if mapa_html:
                return JsonResponse({'mapa_html': mapa_html})
        except Exception as e:
            print(f"Error al generar mapa: {e}")
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Faltan parámetros'}, status=400)
