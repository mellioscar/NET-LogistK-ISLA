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

        # 🔹 Modificación: Ahora usamos `fecha_salida`
        fecha_inicio = datetime(fecha_seleccionada.year, fecha_seleccionada.month, fecha_seleccionada.day, 0, 0, 0)
        fecha_fin = datetime(fecha_seleccionada.year, fecha_seleccionada.month, fecha_seleccionada.day, 23, 59, 59)

        # KPIs del día seleccionado (consulta con `fecha_salida`)
        repartos_dia = db.collection('repartos')\
            .where('fecha_salida', '>=', fecha_inicio)\
            .where('fecha_salida', '<=', fecha_fin)\
            .stream()

        # Convertimos el stream a lista para poder iterarlo múltiples veces
        repartos_dia = list(repartos_dia)
        total_repartos_dia = len(repartos_dia)
        total_finalizados_dia = 0
        estados_repartos = {'Abierto': 0, 'En Curso': 0, 'Finalizado': 0}

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
            .where('activo', '==', 'Si')\
            .stream()

        # Filtrar los tipos requeridos
        tipos_permitidos = {'Camion', 'Hidrogrua', 'Semirremolque', 'Semi_con_Hidrogrua'}
        total_vehiculos_disponibles = sum(1 for vehiculo in vehiculos_disponibles if vehiculo.to_dict().get('tipo') in tipos_permitidos)

        # Repartos mensuales (gráfico de líneas)
        meses_labels = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
        datos_mensuales = [0] * 12

        repartos_anuales = db.collection('repartos')\
            .where('fecha_salida', '>=', datetime(fecha_seleccionada.year, 1, 1))\
            .where('fecha_salida', '<=', datetime(fecha_seleccionada.year, 12, 31, 23, 59, 59))\
            .stream()

        for reparto in repartos_anuales:
            try:
                fecha_reparto = reparto.get('fecha_salida')
                if isinstance(fecha_reparto, datetime):
                    if fecha_reparto.year == fecha_seleccionada.year:
                        datos_mensuales[fecha_reparto.month - 1] += 1
                else:
                    print(f"Error: `fecha_salida` no es datetime en {reparto.id}")
            except Exception as e:
                print(f"Error al procesar fecha: {e}")
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

        return render(request, 'dashboard.html', {
            'total_repartos_hoy': total_repartos_dia,
            'total_repartos_finalizados_hoy': total_finalizados_dia,
            'porcentaje_repartos_finalizados': round(porcentaje_finalizados, 2),
            'total_vehiculos_disponibles': total_vehiculos_disponibles,
            'entregas_incompletas': entregas_incompletas,
            'fecha_seleccionada': fecha_seleccionada.strftime("%Y-%m-%d"),
            'labels_repartos_mensuales': json.dumps(meses_labels),
            'data_repartos_mensuales': json.dumps(datos_mensuales),
            'labels_estados': json.dumps(labels_estados),
            'data_estados': json.dumps(data_estados)
        })

    except Exception as e:
        print(f"Error en el dashboard: {e}")
        messages.error(request, f"Error al cargar el dashboard: {e}")
        return render(request, 'dashboard.html', {
            'total_repartos_hoy': 0,
            'total_repartos_finalizados_hoy': 0,
            'porcentaje_repartos_finalizados': 0,
            'total_vehiculos_disponibles': 0,
            'entregas_incompletas': 0,
            'fecha_seleccionada': fecha_actual.strftime("%d-%m-%Y"),
            'labels_repartos_mensuales': json.dumps([]),
            'data_repartos_mensuales': json.dumps([0] * 12),
            'labels_estados': json.dumps(['Abierto', 'En Curso', 'Finalizado']),
            'data_estados': json.dumps([0, 0, 0])
        })

# Exportar repartos a Excel -
# def exportar_repartos_excel(request):
#    # Obtener la fecha seleccionada
#    fecha_str = request.GET.get('fecha')  # Captura la fecha desde la URL
#    if fecha_str:
#        fecha_actual = datetime.strptime(fecha_str, "%Y-%m-%d").date()
#    else:
#        fecha_actual = date.today()

#    # Consultar Firestore para obtener repartos de la fecha seleccionada
#    repartos_ref = db.collection('repartos')
#    docs = repartos_ref.where('fecha', '==', fecha_str).stream() if fecha_str else repartos_ref.stream()

#    # Crear el archivo Excel
#    workbook = Workbook()
#    hoja = workbook.active
#    hoja.title = f"Repartos del {fecha_actual.strftime('%d-%m-%Y')}"

#    # Encabezados para el Excel
#    encabezados = [
#        "Fecha", "Nro de Reparto", "Chofer", "Acompañante", "Zona",
#        "Facturas", "Estado", "Entregas", "Incompletos"
#    ]
#    hoja.append(encabezados)

#    # Agregar los datos de los repartos
#    for doc in docs:
#        reparto = doc.to_dict()
#        hoja.append([
#            reparto.get('fecha', 'Sin fecha'),
#            reparto.get('nro_reparto', 'Sin nro'),
#            reparto.get('chofer', 'Sin chofer'),
#            reparto.get('acompanante', 'None'),
#            reparto.get('zona', 'Sin zona'),
#            reparto.get('facturas', 0),
#            reparto.get('estado', 'Sin estado'),
#            reparto.get('entregas', 0),
#            reparto.get('incompletos', 0),
#        ])

#    # Configurar la respuesta HTTP para descargar el archivo
#    response = HttpResponse(
#        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
#    )
#    response["Content-Disposition"] = f"attachment; filename=repartos_{fecha_actual.strftime('%Y-%m-%d')}.xlsx"

#    # Guardar el archivo en la respuesta
#    workbook.save(response)
#    return response
