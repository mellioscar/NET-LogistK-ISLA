# views.py
from django.shortcuts import render, redirect
from django.utils import timezone
from django.db.models import Count, Sum
from datetime import datetime, date
from django.db.models.functions import TruncMonth
import pytz
from firebase_admin import auth
from firebase import db
from openpyxl import Workbook
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
import json

from NetLogistK.decorators import firebase_login_required

def exportar_repartos_excel(request):
    # Obtener la fecha seleccionada
    fecha_str = request.GET.get('fecha')  # Captura la fecha desde la URL
    if fecha_str:
        fecha_actual = datetime.strptime(fecha_str, "%Y-%m-%d").date()
    else:
        fecha_actual = date.today()

    # Consultar Firestore para obtener repartos de la fecha seleccionada
    repartos_ref = db.collection('repartos')
    docs = repartos_ref.where('fecha', '==', fecha_str).stream() if fecha_str else repartos_ref.stream()

    # Crear el archivo Excel
    workbook = Workbook()
    hoja = workbook.active
    hoja.title = f"Repartos del {fecha_actual.strftime('%d-%m-%Y')}"

    # Encabezados para el Excel
    encabezados = [
        "Fecha", "Nro de Reparto", "Chofer", "Acompañante", "Zona",
        "Facturas", "Estado", "Entregas", "Incompletos"
    ]
    hoja.append(encabezados)

    # Agregar los datos de los repartos
    for doc in docs:
        reparto = doc.to_dict()
        hoja.append([
            reparto.get('fecha', 'Sin fecha'),
            reparto.get('nro_reparto', 'Sin nro'),
            reparto.get('chofer', 'Sin chofer'),
            reparto.get('acompanante', 'None'),
            reparto.get('zona', 'Sin zona'),
            reparto.get('facturas', 0),
            reparto.get('estado', 'Sin estado'),
            reparto.get('entregas', 0),
            reparto.get('incompletos', 0),
        ])

    # Configurar la respuesta HTTP para descargar el archivo
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f"attachment; filename=repartos_{fecha_actual.strftime('%Y-%m-%d')}.xlsx"

    # Guardar el archivo en la respuesta
    workbook.save(response)
    return response


@firebase_login_required
def dashboard(request):
    try:
        firebase_user = getattr(request, 'firebase_user', None)
        if not firebase_user:
            return redirect('login')

        # Configuración de zona horaria y fecha
        zona_horaria = pytz.timezone('America/Argentina/Buenos_Aires')
        fecha_actual = timezone.now().astimezone(zona_horaria).date()
        
        # Obtener fecha del filtro o usar la fecha actual
        fecha_str = request.GET.get('fecha')
        if fecha_str:
            try:
                fecha_seleccionada = datetime.strptime(fecha_str, "%Y-%m-%d").date()
            except ValueError:
                fecha_seleccionada = fecha_actual
        else:
            fecha_seleccionada = fecha_actual

        # Formatear fechas para consulta y display
        fecha_consulta = fecha_seleccionada.strftime("%d-%m-%Y")  # Para Firestore
        fecha_mostrar = fecha_consulta  # Para mostrar en el template
        anio_actual = fecha_seleccionada.year

        # KPIs del día seleccionado
        repartos_dia = db.collection('repartos').where('fecha', '==', fecha_consulta).stream()
        total_repartos_dia = 0
        total_finalizados_dia = 0
        estados_repartos = {'Abierto': 0, 'En Curso': 0, 'Finalizado': 0}

        # Convertimos el stream a lista para poder iterarlo múltiples veces
        repartos_dia = list(repartos_dia)
        total_repartos_dia = len(repartos_dia)

        for reparto in repartos_dia:
            reparto_data = reparto.to_dict()
            estado = reparto_data.get('estado_reparto', 'Abierto')
            if estado in estados_repartos:
                estados_repartos[estado] += 1
            if estado == 'Finalizado':
                total_finalizados_dia += 1

        # Calcular porcentaje de finalizados
        porcentaje_finalizados = (total_finalizados_dia / total_repartos_dia * 100) if total_repartos_dia > 0 else 0

        # Vehículos disponibles
        vehiculos_disponibles = db.collection('vehiculos')\
            .where('tipo', '==', 'Camion')\
            .where('activo', '==', 'Si')\
            .stream()
        total_vehiculos_disponibles = sum(1 for _ in vehiculos_disponibles)

        # Repartos mensuales (gráfico de líneas)
        meses_labels = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
        datos_mensuales = [0] * 12

        repartos_anuales = db.collection('repartos')\
            .where('fecha', '>=', f"01-01-{anio_actual}")\
            .where('fecha', '<=', f"31-12-{anio_actual}")\
            .stream()

        for reparto in repartos_anuales:
            try:
                fecha_str = reparto.get('fecha')
                fecha_reparto = datetime.strptime(fecha_str, '%d-%m-%Y')
                if fecha_reparto.year == anio_actual:
                    datos_mensuales[fecha_reparto.month - 1] += 1
            except ValueError as e:
                print(f"Error al procesar fecha: {fecha_str} - {e}")
                continue

        # Datos para el gráfico de torta (estados del día)
        labels_estados = list(estados_repartos.keys())
        data_estados = list(estados_repartos.values())

        # Entregas incompletas del día
        entregas_incompletas = 0
        for reparto in repartos_dia:
            pedidos = reparto.reference.collection('pedidos')\
                .where('estado', '!=', 'Entregado')\
                .stream()
            entregas_incompletas += sum(1 for _ in pedidos)

        return render(request, 'sb_admin2/index.html', {
            'total_repartos_hoy': total_repartos_dia,
            'total_repartos_finalizados_hoy': total_finalizados_dia,
            'porcentaje_repartos_finalizados': round(porcentaje_finalizados, 2),
            'total_vehiculos_disponibles': total_vehiculos_disponibles,
            'entregas_incompletas': entregas_incompletas,
            'fecha_seleccionada': fecha_mostrar,
            'labels_repartos_mensuales': json.dumps(meses_labels),
            'data_repartos_mensuales': json.dumps(datos_mensuales),
            'labels_estados': json.dumps(labels_estados),
            'data_estados': json.dumps(data_estados)
        })

    except Exception as e:
        print(f"Error en el dashboard: {e}")
        messages.error(request, f"Error al cargar el dashboard: {e}")
        return render(request, 'sb_admin2/index.html', {
            'total_repartos_hoy': 0,
            'total_repartos_finalizados_hoy': 0,
            'porcentaje_repartos_finalizados': 0,
            'total_vehiculos_disponibles': 0,
            'entregas_incompletas': 0,
            'fecha_seleccionada': fecha_mostrar if 'fecha_mostrar' in locals() else datetime.now().strftime("%d-%m-%Y"),
            'labels_repartos_mensuales': json.dumps([]),
            'data_repartos_mensuales': json.dumps([0] * 12),
            'labels_estados': json.dumps(['Abierto', 'En Curso', 'Finalizado']),
            'data_estados': json.dumps([0, 0, 0])
        })

@firebase_login_required
def obtener_detalles_reparto(request, nro_reparto):
    try:
        # Obtener el reparto
        reparto_ref = db.collection('repartos').where('nro_reparto', '==', nro_reparto).limit(1).get()
        if not reparto_ref:
            return JsonResponse({'error': 'Reparto no encontrado'}, status=404)
            
        reparto = reparto_ref[0]
        reparto_data = reparto.to_dict()
        
        # Obtener los pedidos del reparto
        pedidos = []
        pedidos_ref = reparto.reference.collection('pedidos').stream()
        
        for pedido in pedidos_ref:
            pedido_data = pedido.to_dict()
            pedidos.append({
                'nro_factura': pedido_data.get('nro_factura', ''),
                'cliente': pedido_data.get('cliente', ''),
                'direccion': pedido_data.get('direccion', ''),
                'estado': pedido_data.get('estado', ''),
                'estado_color': 'success' if pedido_data.get('estado') == 'Entregado' else 'warning'
            })
        
        # Preparar la respuesta
        response_data = {
            'reparto': {
                'nro_reparto': reparto_data.get('nro_reparto', ''),
                'fecha': reparto_data.get('fecha', ''),
                'estado': reparto_data.get('estado_reparto', ''),
                'estado_color': 'success' if reparto_data.get('estado_reparto') == 'Finalizado' else 'primary',
                'chofer': reparto_data.get('chofer', {}).get('nombre', ''),
                'zona': reparto_data.get('zona', ''),
                'zona_descripcion': reparto_data.get('zona_descripcion', '')
            },
            'pedidos': pedidos
        }
        
        return JsonResponse(response_data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@firebase_login_required
def ver_detalle_reparto(request, nro_reparto):
    try:
        # Obtener el reparto
        reparto_ref = db.collection('repartos').where('nro_reparto', '==', nro_reparto).limit(1).get()
        if not reparto_ref:
            messages.error(request, 'Reparto no encontrado')
            return redirect('ver_repartos')
            
        reparto = reparto_ref[0]
        reparto_data = reparto.to_dict()
        
        # Obtener los pedidos
        pedidos = []
        pedidos_ref = reparto.reference.collection('pedidos').stream()
        
        for pedido in pedidos_ref:
            pedido_data = pedido.to_dict()
            estado = pedido_data.get('estado', '')
            pedidos.append({
                'nro_factura': pedido_data.get('nro_factura', ''),
                'cliente': pedido_data.get('cliente', ''),
                'direccion': pedido_data.get('direccion', ''),
                'estado': estado,
                'peso': pedido_data.get('peso', 0),
                'estado_color': 'success' if estado == 'Entregado' else 'warning'
            })
            
        context = {
            'reparto': reparto_data,
            'pedidos': pedidos
        }
        
        return render(request, 'repartos/detalle_reparto.html', context)
        
    except Exception as e:
        messages.error(request, f'Error al obtener los detalles: {str(e)}')
        return redirect('ver_repartos')
