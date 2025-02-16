# cronograma/views.py
from django.shortcuts import render, redirect
from .utils import generar_calendario_mes, get_week_dates
from datetime import datetime, timedelta
import locale
from firebase_admin import firestore
import calendar
from django.http import JsonResponse
from django.contrib import messages


def cronograma_mensual(request):
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
        
        return render(request, 'cronograma/cronograma_mensual.html', {
            'calendario': calendario,
            'nombre_mes': nombre_mes,
            'anio': anio,
            'prev_month': prev_month,
            'next_month': next_month,
            'prev_year': prev_year,
            'next_year': next_year,
        })
        
    except Exception as e:
        return render(request, 'cronograma/cronograma_mensual.html', {
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


def cronograma_semanal(request):
    try:
        db = firestore.client()
        
        # Obtener la fecha de la URL o usar la fecha actual
        fecha_str = request.GET.get('fecha')
        
        if fecha_str:
            fecha_actual = datetime.strptime(fecha_str, '%d-%m-%Y')
        else:
            fecha_actual = datetime.now()
        
        # Obtener las fechas de la semana en formato `dd-mm-yyyy`
        fechas_semana = get_week_dates(fecha_actual)

        # Filtrar los repartos en Firestore por rango de fechas
        repartos_ref = db.collection('repartos').where('fecha', 'in', fechas_semana).stream()
        
        repartos_por_dia = {fecha: [] for fecha in fechas_semana}

        for reparto in repartos_ref:
            reparto_data = reparto.to_dict()
            fecha_reparto = reparto_data.get('fecha')

            if fecha_reparto in repartos_por_dia:
                estado_color = {
                    'Abierto': 'success',
                    'Cerrado': 'danger',
                    'Finalizado': 'primary',
                    'En curso': 'primary',
                    'Sin Reparto': 'secondary',
                    'Abierto Parcial - Solo Metalúrgico': 'warning',
                    'Abierto Parcial - Solo Paletizado': 'warning'
                }.get(reparto_data.get('estado_reparto', ''), 'light')

                repartos_por_dia[fecha_reparto].append({
                    'nro_reparto': reparto_data.get('nro_reparto', ''),
                    'zona': reparto_data.get('zona', ''),
                    'estado': reparto_data.get('estado_reparto', 'Sin estado'),
                    'estado_color': estado_color,
                    'chofer': reparto_data.get('chofer', {}).get('nombre_completo', 'Sin chofer')
                })
        
        # Construir la respuesta con los datos organizados
        dias_semana = []
        for fecha in fechas_semana:
            dias_semana.append({
                'fecha': fecha,
                'nombre_dia': datetime.strptime(fecha, '%d-%m-%Y').strftime('%A').capitalize(),
                'repartos': repartos_por_dia[fecha]
            })

        context = {
            'dias_semana': dias_semana,
            'fecha_actual': fecha_actual.strftime('%d-%m-%Y'),
            'error': None
        }
        
        return render(request, 'cronograma/cronograma_semanal.html', context)
        
    except Exception as e:
        return render(request, 'cronograma/cronograma_semanal.html', {
            'error': f"Error al cargar el cronograma: {str(e)}"
        })



def lista_detalle_reparto(request, nro_reparto):
    try:
        db = firestore.client()
        reparto_ref = db.collection('repartos').where('nro_reparto', '==', nro_reparto).limit(1).stream()
        reparto_data = None
        
        for doc in reparto_ref:
            reparto_data = doc.to_dict()
            break
            
        if not reparto_data:
            messages.error(request, 'Reparto no encontrado')
            return redirect('cronograma_semanal')
            
        # Obtener pedidos y sus artículos
        pedidos_ref = doc.reference.collection('pedidos').stream()
        pedidos = []
        peso_total = 0
        
        for pedido in pedidos_ref:
            pedido_data = pedido.to_dict()
            
            # Obtener artículos del array dentro del pedido
            articulos = []
            for articulo in pedido_data.get('articulos', []):
                articulos.append({
                    'cantidad': articulo.get('cantidad', '0'),
                    'codigo': articulo.get('codigo', ''),
                    'descripcion': articulo.get('descripcion', ''),
                    'peso': float(articulo.get('peso', 0))
                })
            
            # Calcular peso total del pedido
            peso_pedido = sum(float(art.get('peso', 0)) for art in pedido_data.get('articulos', []))
            peso_total += peso_pedido
            
            estado_color = {
                'Asignado': 'primary',
                'Entregado': 'success',
                'Pendiente': 'warning',
                'Cancelado': 'danger'
            }.get(pedido_data.get('estado', ''), 'secondary')
            
            pedidos.append({
                'nro_factura': pedido_data.get('nro_factura', ''),
                'cliente': pedido_data.get('cliente', ''),
                'direccion': pedido_data.get('direccion', ''),
                'estado': pedido_data.get('estado', 'Sin estado'),
                'estado_color': estado_color,
                'peso': peso_pedido,
                'articulos': articulos
            })
        
        context = {
            'reparto': {
                'nro_reparto': reparto_data.get('nro_reparto', ''),
                'fecha': reparto_data.get('fecha', ''),
                'estado': reparto_data.get('estado_reparto', 'Sin estado'),
                'estado_color': estado_color,
                'chofer': reparto_data.get('chofer', {}).get('nombre_completo', 'Sin chofer'),
                'zona': reparto_data.get('zona', 'Sin zona'),
                'sucursal': reparto_data.get('sucursal', 'Sin sucursal'),
                'total_facturas': len(pedidos),
                'peso_total': peso_total
            },
            'pedidos': pedidos,
            'fecha_actual': request.GET.get('fecha', '')
        }
        
        return render(request, 'cronograma/lista_detalle_reparto.html', context)
        
    except Exception as e:
        messages.error(request, f'Error al cargar los detalles del reparto: {str(e)}')
        return redirect('cronograma_semanal')

