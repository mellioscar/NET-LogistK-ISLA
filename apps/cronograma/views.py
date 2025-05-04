# cronograma/views.py
from django.shortcuts import render, redirect
from .utils import generar_calendario_mes, get_week_dates
from datetime import datetime, timedelta
import locale
from firebase_admin import firestore
import calendar
from django.http import JsonResponse
from django.contrib import messages
from django.urls import reverse
import json
import traceback


def cronograma_mensual(request):
    try:
        # Configurar locale para español
        locale.setlocale(locale.LC_TIME, 'Spanish_Spain.1252')
        
        # Obtener el mes y el año actual o de la URL
        mes = int(request.GET.get('mes', datetime.now().month))
        anio = int(request.GET.get('anio', datetime.now().year))
        
        # Obtener la zona seleccionada de los parámetros de la URL
        zona_seleccionada = request.GET.get('zona', '')
        
        # Obtener el nombre del mes en español
        nombre_mes = datetime(anio, mes, 1).strftime('%B').capitalize()
        
        # Calcular el mes anterior y siguiente
        prev_month = mes - 1 if mes > 1 else 12
        next_month = mes + 1 if mes < 12 else 1
        prev_year = anio if mes > 1 else anio - 1
        next_year = anio if mes < 12 else anio + 1
        
        # Obtener repartos del mes
        db = firestore.client()
        
        # Obtener todas las zonas ordenadas alfabéticamente
        zonas_ref = db.collection('zonas').order_by('nombre')
        zonas = []
        for zona_doc in zonas_ref.stream():
            zona_data = zona_doc.to_dict()
            zonas.append({
                'nombre': zona_data.get('nombre', ''),
                'descripcion': zona_data.get('descripcion', ''),
                'display': f"{zona_data.get('nombre', '')} - {zona_data.get('descripcion', '')}"
            })
        
        if zona_seleccionada:
            zona_encontrada = zona_seleccionada in [z['nombre'] for z in zonas]
            if not zona_encontrada:
                print("ADVERTENCIA: La zona seleccionada no existe en la lista de zonas")
        
        # Crear fechas inicio y fin del mes como datetime
        fecha_inicio = datetime(anio, mes, 1)
        if mes == 12:
            fecha_fin = datetime(anio + 1, 1, 1)
        else:
            fecha_fin = datetime(anio, mes + 1, 1)
        
        
        # Consultar repartos del mes (solo por fecha)
        repartos_ref = db.collection('repartos')\
            .where('fecha_salida', '>=', fecha_inicio)\
            .where('fecha_salida', '<', fecha_fin)\
            .stream()
        repartos = {}
        eventos = []
        for reparto in repartos_ref:
            data = reparto.to_dict()
            fecha_salida = data.get('fecha_salida')
            if fecha_salida:
                # Filtrar por zona si está seleccionada
                if zona_seleccionada and data.get('zona') != zona_seleccionada:
                    continue
                dia = fecha_salida.day
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
                eventos.append({
                    'id': data.get('nro_reparto', ''),
                    'title': f"{data.get('nro_reparto', '')}",
                    'start': fecha_salida.strftime('%Y-%m-%d'),
                    'descripcion': data.get('estado_reparto', 'Sin estado')
                })
        
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
        
        # Construir URLs de navegación preservando la zona seleccionada
        prev_url = f"{reverse('cronograma_mensual')}?mes={prev_month}&anio={prev_year}"
        next_url = f"{reverse('cronograma_mensual')}?mes={next_month}&anio={next_year}"
        
        if zona_seleccionada:
            prev_url += f"&zona={zona_seleccionada}"
            next_url += f"&zona={zona_seleccionada}"
        
        context = {
            'calendario': calendario,
            'nombre_mes': nombre_mes,
            'anio': anio,
            'mes': mes,  # Agregar mes al contexto
            'prev_month': prev_month,
            'next_month': next_month,
            'prev_year': prev_year,
            'next_year': next_year,
            'prev_url': prev_url,
            'next_url': next_url,
            'zonas': zonas,
            'zona_seleccionada': zona_seleccionada,
            'eventos': json.dumps(eventos, ensure_ascii=False)
        }
        
        return render(request, 'cronograma/cronograma_mensual.html', context)
        
    except Exception as e:
        print(f"- Error en cronograma_mensual: {str(e)}")
        traceback.print_exc()
        return render(request, 'cronograma/cronograma_mensual.html', {
            'error': f"Error al cargar el cronograma: {str(e)}",
            'eventos': '[]'
        })


def obtener_detalles_reparto(request, nro_reparto):
    try:
        db = firestore.client()
        # Listar todos los nro_reparto existentes para depuración
        todos = list(db.collection('repartos').stream())
        for doc in todos:
            d = doc.to_dict()
        # Buscar el reparto por nro_reparto exacto
        reparto_ref = db.collection('repartos').where('nro_reparto', '==', str(nro_reparto)).stream()
        reparto_doc = next(reparto_ref, None)
        if not reparto_doc:
            return JsonResponse({'error': 'Reparto no encontrado'}, status=404)
        reparto_data = reparto_doc.to_dict()
        pedidos_ref = reparto_doc.reference.collection('pedidos').stream()
        pedidos = []
        peso_total = 0
        for pedido in pedidos_ref:
            pedido_data = pedido.to_dict()
            if not pedido_data.get('nro_factura') or not pedido_data['nro_factura'].strip():
                continue
            peso_pedido = sum(float(art.get('peso', 0)) for art in pedido_data.get('articulos', []))
            peso_total += peso_pedido
            pedidos.append({
                'factura': pedido_data.get('nro_factura', ''),
                'cliente': pedido_data.get('cliente', ''),
                'direccion': pedido_data.get('direccion', ''),
                'estado': pedido_data.get('estado', 'Sin estado'),
                'estado_clase': {
                    'Pendiente': 'warning',
                    'Entregado': 'success',
                    'Cancelado': 'danger',
                    'En Reparto': 'primary',
                    'Asignado': 'info'
                }.get(pedido_data.get('estado', ''), 'secondary'),
                'peso': peso_pedido,
                'latitud': pedido_data.get('latitud', None),
                'longitud': pedido_data.get('longitud', None)
            })
        try:
            fecha_salida = reparto_data.get('fecha_salida', '')
            fecha_str = fecha_salida.strftime('%d/%m/%Y') if fecha_salida else ''
        except Exception as e:
            print(f"[ERROR] Error al formatear fecha_salida: {e}")
            fecha_str = ''
        response_data = {
            'numero': reparto_data.get('nro_reparto', ''),
            'fecha': fecha_str,
            'estado': reparto_data.get('estado_reparto', ''),
            'estado_clase': {
                'Abierto': 'primary',
                'Cerrado': 'danger',
                'Finalizado': 'success',
                'Cancelado': 'secondary'
            }.get(reparto_data.get('estado_reparto', ''), 'secondary'),
            'chofer': reparto_data.get('chofer', {}).get('nombre_completo',
                        f"{reparto_data.get('chofer', {}).get('nombre', 'Sin asignar')} {reparto_data.get('chofer', {}).get('apellido', '')}"),
            'zona': reparto_data.get('zona', 'Sin zona'),
            'vehiculo': reparto_data.get('vehiculo', ''),
            'sucursal': reparto_data.get('sucursal', 'Sin sucursal'),
            'peso_total': peso_total,
            'pedidos': pedidos
        }
        return JsonResponse(response_data)
    except Exception as e:
        import traceback
        print(f"[ERROR] Excepción en obtener_detalles_reparto: {e}")
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


def cronograma_semanal(request):
    try:
        # Configurar locale para español
        locale.setlocale(locale.LC_TIME, 'Spanish_Spain.1252')

        db = firestore.client()
        fecha_str = request.GET.get('fecha')
        if fecha_str:
            fecha_actual = datetime.strptime(fecha_str, '%d-%m-%Y')
        else:
            fecha_actual = datetime.now()

        # Obtener las fechas de la semana
        fechas_semana = get_week_dates(fecha_actual)
        fecha_inicio = datetime.strptime(fechas_semana[0], '%d-%m-%Y')
        fecha_fin = datetime.strptime(fechas_semana[-1], '%d-%m-%Y')
        fecha_inicio = datetime.combine(fecha_inicio.date(), datetime.min.time())
        fecha_fin = datetime.combine(fecha_fin.date(), datetime.max.time())

        # Consultar repartos de la semana (igual que en mensual, pero rango semanal)
        repartos_ref = db.collection('repartos')\
            .where('fecha_salida', '>=', fecha_inicio)\
            .where('fecha_salida', '<=', fecha_fin)\
            .stream()
        eventos = []
        for reparto in repartos_ref:
            data = reparto.to_dict()
            fecha_salida = data.get('fecha_salida')
            if fecha_salida:
                eventos.append({
                    'id': data.get('nro_reparto', ''),
                    'title': f"{data.get('nro_reparto', '')}",
                    'start': fecha_salida.strftime('%Y-%m-%d'),
                    'descripcion': data.get('estado_reparto', 'Sin estado')
                })

        context = {
            'fecha_actual': fecha_actual.strftime('%d-%m-%Y'),
            'eventos': json.dumps(eventos, ensure_ascii=False)
        }
        return render(request, 'cronograma/cronograma_semanal.html', context)
    except Exception as e:
        print(f"- Error en cronograma_semanal: {str(e)}")
        traceback.print_exc()
        return render(request, 'cronograma/cronograma_semanal.html', {
            'error': f"Error al cargar el cronograma: {str(e)}",
            'eventos': '[]'
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
        estado_color = ''

        for pedido in pedidos_ref:
            pedido_data = pedido.to_dict()

            # Verificar si 'nro_factura' existe y no está vacío
            if not pedido_data.get('nro_factura') or not pedido_data['nro_factura'].strip():
                continue  # Saltar este pedido si no tiene factura válida

            # Obtener artículos del array dentro del pedido
            articulos = [
                {
                    'cantidad': articulo.get('cantidad', '0'),
                    'codigo': articulo.get('codigo', ''),
                    'descripcion': articulo.get('descripcion', ''),
                    'peso': float(articulo.get('peso', 0))
                }
                for articulo in pedido_data.get('articulos', [])
            ]

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
                'latitud': pedido_data.get('latitud', None),
                'longitud': pedido_data.get('longitud', None),
                'articulos': articulos
            })

        context = {
            'reparto': {
                'nro_reparto': reparto_data.get('nro_reparto', ''),
                'fecha': reparto_data.get('fecha_salida', '').strftime('%d/%m/%Y'),
                'estado': reparto_data.get('estado_reparto', 'Sin estado'),
                'estado_color': estado_color,
                'chofer': reparto_data.get('chofer', {}).get('nombre_completo', 'Sin chofer'),
                'zona': reparto_data.get('zona', 'Sin zona'),
                'sucursal': reparto_data.get('sucursal', 'Sin sucursal'),
                'total_facturas': len(pedidos),  # Se actualiza con pedidos filtrados
                'peso_total': peso_total
            },
            'pedidos': pedidos,
            'fecha_actual': request.GET.get('fecha', '')
        }

        return render(request, 'cronograma/lista_detalle_reparto.html', context)

    except Exception as e:
        messages.error(request, f'Error al cargar los detalles del reparto: {str(e)}')
        return redirect('cronograma_semanal')
