# tracking/views.py

from django.shortcuts import render
from .utils import generar_calendario_mes, crear_mapa_tracking
from datetime import datetime, timedelta
import locale
from firebase_admin import firestore
import calendar
from django.http import JsonResponse


def mapa_tracking(request):
    # Generar el mapa (ver el ejemplo anterior con folium)
    crear_mapa_tracking()  # Esta función generará el archivo HTML del mapa
    return render(request, 'tracking/mapa_tracking.html')  # Renderiza la página con el mapa


def cronograma(request):
    try:
        # Configurar locale para español
        locale.setlocale(locale.LC_TIME, 'Spanish_Spain.1252')
        
        # Obtener el mes y el año actual o de la URL
        mes = int(request.GET.get('month', datetime.now().month))
        anio = int(request.GET.get('year', datetime.now().year))
        
        # Obtener el nombre del mes en español
        nombre_mes = datetime(anio, mes, 1).strftime('%B').capitalize()
        
        # Calcular el mes anterior y siguiente
        prev_month = mes - 1 if mes > 1 else 12
        next_month = mes + 1 if mes < 12 else 1
        prev_year = anio if mes > 1 else anio - 1
        next_year = anio if mes < 12 else anio + 1
        
        # Obtener repartos del mes
        db = firestore.client()
        
        # Formatear fechas para la consulta
        fecha_inicio = f"01-{mes:02d}-{anio}"
        if mes == 12:
            fecha_fin = f"01-01-{anio + 1}"
        else:
            fecha_fin = f"01-{(mes + 1):02d}-{anio}"
        
        # Obtener todos los repartos y filtrar por fecha
        repartos_ref = db.collection('repartos').stream()
        
        repartos = {}
        for reparto in repartos_ref:
            data = reparto.to_dict()
            fecha_reparto = data.get('fecha', '')
            
            # Verificar si la fecha está en el mes actual
            try:
                fecha = datetime.strptime(fecha_reparto, '%d-%m-%Y')
                if fecha.month == mes and fecha.year == anio:
                    dia = fecha.day
                    
                    if dia not in repartos:
                        repartos[dia] = []
                    
                    estado_color = {
                        'Abierto': 'primary',
                        'Cerrado': 'danger',
                        'Finalizado': 'success',
                        'Cancelado': 'secondary'
                    }.get(data.get('estado_reparto', ''), 'secondary')
                    
                    repartos[dia].append({
                        'nro_reparto': data.get('nro_reparto', ''),
                        'zona': data.get('zona', 'Sin zona'),
                        'estado': data.get('estado_reparto', 'Sin estado'),
                        'estado_color': estado_color
                    })
            except Exception:
                continue
        
        # Generar calendario
        cal = calendar.monthcalendar(anio, mes)
        hoy = datetime.now()
        calendario = []
        
        for semana in cal:
            semana_formato = []
            for dia in semana:
                if dia != 0:
                    dia_data = {
                        'numero': dia,
                        'otro_mes': False,
                        'hoy': (dia == hoy.day and mes == hoy.month and anio == hoy.year),
                        'repartos': repartos.get(dia, [])
                    }
                else:
                    dia_data = {
                        'numero': '',
                        'otro_mes': True,
                        'hoy': False,
                        'repartos': []
                    }
                semana_formato.append(dia_data)
            calendario.append(semana_formato)
        
        return render(request, 'tracking/cronograma.html', {
            'calendario': calendario,
            'nombre_mes': nombre_mes,
            'anio': anio,
            'prev_month': prev_month,
            'next_month': next_month,
            'prev_year': prev_year,
            'next_year': next_year,
        })
        
    except Exception as e:
        return render(request, 'tracking/cronograma.html', {
            'error': f"Error al cargar el cronograma: {str(e)}"
        })


def obtener_detalles_reparto(request, nro_reparto):
    try:
        db = firestore.client()
        
        # Obtener datos del reparto
        reparto_ref = db.collection('repartos').where('nro_reparto', '==', str(nro_reparto)).stream()
        reparto_doc = next(reparto_ref, None)
        
        if not reparto_doc:
            return JsonResponse({'error': 'Reparto no encontrado'}, status=404)
            
        reparto_data = reparto_doc.to_dict()
        
        # Obtener pedidos de la subcolección
        pedidos_ref = reparto_doc.reference.collection('pedidos').stream()
        pedidos = []
        
        for pedido in pedidos_ref:
            pedido_data = pedido.to_dict()
            pedidos.append({
                'nro_factura': pedido_data.get('nro_factura', ''),
                'cliente': pedido_data.get('cliente', ''),
                'direccion': pedido_data.get('direccion', ''),
                'estado': pedido_data.get('estado', 'Sin estado'),
                'estado_color': {
                    'Pendiente': 'warning',
                    'Entregado': 'success',
                    'Cancelado': 'danger',
                    'En Reparto': 'primary',
                    'Asignado': 'info'
                }.get(pedido_data.get('estado', ''), 'secondary')
            })
        
        response_data = {
            'reparto': {
                'nro_reparto': reparto_data.get('nro_reparto', ''),
                'estado': reparto_data.get('estado_reparto', ''),
                'fecha': reparto_data.get('fecha', ''),
                'estado_color': {
                    'Abierto': 'primary',
                    'Cerrado': 'danger',
                    'Finalizado': 'success',
                    'Cancelado': 'secondary'
                }.get(reparto_data.get('estado_reparto', ''), 'secondary'),
                'chofer': f"{reparto_data.get('chofer', {}).get('nombre', 'Sin asignar')} {reparto_data.get('chofer', {}).get('apellido', '')}",
                'zona': reparto_data.get('zona', 'Sin zona'),
                'zona_descripcion': reparto_data.get('zona_descripcion', '')
            },
            'pedidos': pedidos
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def importar_pedidos(request):
    try:
        db = firestore.client()
        
        # ... código existente de validación del archivo ...
        
        for pedido in pedidos:
            # ... código existente de procesamiento de pedido ...
            
            # Buscar o crear el reparto para la fecha
            fecha_reparto = pedido.get('fecha_reparto')
            nro_reparto = pedido.get('nro_reparto')
            zona = pedido.get('zona')
            
            # Obtener la descripción de la zona
            zona_ref = db.collection('zonas').where('nombre', '==', zona).limit(1).stream()
            zona_doc = next(zona_ref, None)
            zona_descripcion = zona_doc.to_dict().get('descripcion', '') if zona_doc else ''
            
            # Buscar si existe el reparto
            reparto_ref = db.collection('repartos').where('nro_reparto', '==', nro_reparto).limit(1).stream()
            reparto_doc = next(reparto_ref, None)
            
            if not reparto_doc:
                # Crear nuevo reparto
                nuevo_reparto = {
                    'nro_reparto': nro_reparto,
                    'fecha': fecha_reparto,
                    'zona': zona,
                    'zona_descripcion': zona_descripcion,
                    'estado_reparto': 'Abierto',
                    'fecha_creacion': datetime.now().strftime('%d-%m-%Y'),
                    'chofer': None
                }
                reparto_doc_ref = db.collection('repartos').document()
                reparto_doc_ref.set(nuevo_reparto)
            else:
                reparto_doc_ref = reparto_doc.reference
            
            # Agregar el pedido como subdocumento del reparto
            pedido_data = {
                'nro_factura': pedido.get('nro_factura'),
                'cliente': pedido.get('cliente'),
                'direccion': pedido.get('direccion'),
                'estado': 'Asignado',
                'fecha_creacion': datetime.now().strftime('%d-%m-%Y'),
                'peso_total': pedido.get('peso_total'),
                'telefono': pedido.get('telefono'),
                'email': pedido.get('email')
            }
            
            reparto_doc_ref.collection('pedidos').add(pedido_data)
            
        return JsonResponse({'mensaje': 'Importación completada con éxito'})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
