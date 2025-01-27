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
from django.http import HttpResponse

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
    # Obtener el usuario autenticado desde el decorador
    firebase_user = getattr(request, 'firebase_user', None)
    if not firebase_user:
        return redirect('login')

    uid = firebase_user.get('uid')
    email = firebase_user.get('email')

    # Zona horaria de Buenos Aires
    zona_horaria = pytz.timezone('America/Argentina/Buenos_Aires')
    fecha_str = request.GET.get('fecha')
    if fecha_str:
        try:
            fecha_seleccionada = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except ValueError:
            fecha_seleccionada = timezone.now().astimezone(zona_horaria).date()
    else:
        fecha_seleccionada = timezone.now().astimezone(zona_horaria).date()

    # Convertir la fecha seleccionada a string en formato "yyyy-mm-dd"
    fecha_seleccionada_str = fecha_seleccionada.strftime("%Y-%m-%d")

    # Calcular el total de repartos del día seleccionado
    try:
        repartos_query = db.collection('repartos').where('fecha', '==', fecha_seleccionada_str).stream()
        total_repartos_hoy = sum(1 for _ in repartos_query)  # Contar los repartos del día seleccionado
    except Exception as e:
        total_repartos_hoy = 0  # Manejo de errores

    # Calcular el total de repartos finalizados hoy
    try:
        repartos_finalizados_query = db.collection('repartos')\
            .where('fecha', '==', fecha_seleccionada_str)\
            .where('estado_reparto', '==', 'Finalizado').stream()
        total_repartos_finalizados_hoy = sum(1 for _ in repartos_finalizados_query)
    except Exception as e:
        total_repartos_finalizados_hoy = 0  # Manejo de errores

    porcentaje_repartos_finalizados = (
        (total_repartos_finalizados_hoy / total_repartos_hoy) * 100
        if total_repartos_hoy > 0 else 0
    )

    anio_actual = fecha_seleccionada.year

    # Inicializar contadores para los meses
    meses_contadores = {
        1: 0, 2: 0, 3: 0, 4: 0,
        5: 0, 6: 0, 7: 0, 8: 0,
        9: 0, 10: 0, 11: 0, 12: 0
    }

    # Calcular los repartos finalizados por mes
    try:
        # Consultar todos los repartos del año actual con estado "Finalizado"
        repartos_query = db.collection('repartos').where('estado_reparto', '==', 'Finalizado').stream()
        for doc in repartos_query:
            reparto = doc.to_dict()
            fecha_reparto = reparto.get('fecha')
            if fecha_reparto:
                reparto_date = datetime.strptime(fecha_reparto, "%Y-%m-%d").date()
                if reparto_date.year == anio_actual:
                    mes = reparto_date.month
                    # Incrementar el contador del mes correspondiente
                    if mes in meses_contadores:
                        meses_contadores[mes] += 1
    except Exception as e:
        # Manejo de errores: los contadores se mantendrán en 0
        pass



    # Valores predeterminados para evitar consultas
    total_entregas_incompletas_hoy = 5
    labels_repartos_mensuales = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    data_repartos_mensuales = [meses_contadores[1], meses_contadores[2], meses_contadores[3],
        meses_contadores[4], meses_contadores[5], meses_contadores[6],
        meses_contadores[7], meses_contadores[8], meses_contadores[9],
        meses_contadores[10], meses_contadores[11], meses_contadores[12]] * 12
    labels_estados = []
    data_estados = []

    # Calcular el total de vehículos activos de tipo "Camión"
    try:
        vehiculos_query = db.collection('vehiculos').where('tipo', '==', 'Camion').where('activo', '==', 'Si').stream()
        total_vehiculos = sum(1 for _ in vehiculos_query)  # Contar los vehículos que cumplen con el criterio
    except Exception as e:
        total_vehiculos = 0  # Manejo de errores

    # Mensajes no leídos y recientes
    try:
        # Filtrar mensajes no leídos para el usuario actual
        mensajes_query = db.collection('mensajes').where('receptor_uid', '==', uid).where('leido', '==', False).stream()
        mensajes_no_leidos = [{'id': doc.id, **doc.to_dict()} for doc in mensajes_query]

        # Obtener los últimos 5 mensajes no leídos
        mensajes_recientes = sorted(mensajes_no_leidos, key=lambda x: x['fecha_envio'], reverse=True)[:5]

        # Actualizar cantidad de mensajes no leídos
        cantidad_no_leidos = len(mensajes_no_leidos)

        # Agregar información del emisor para los mensajes recientes
        for mensaje in mensajes_recientes:
            emisor_uid = mensaje.get('emisor_uid')
            if emisor_uid:
                emisor_doc = db.collection('usuarios').document(emisor_uid).get()
                emisor_data = emisor_doc.to_dict() if emisor_doc.exists else {}
                mensaje['emisor'] = emisor_data.get('nombre', 'Desconocido')
            else:
                mensaje['emisor'] = 'Desconocido'

    except Exception as e:
        # Manejo de errores
        mensajes_recientes = []
        cantidad_no_leidos = 0

    # Renderizar la plantilla con los datos
    return render(request, 'sb_admin2/index.html', {
        'fecha_actual': fecha_seleccionada,
        'total_repartos_hoy': total_repartos_hoy,
        'total_vehiculos': total_vehiculos,
        'porcentaje_repartos_finalizados': porcentaje_repartos_finalizados,
        'total_entregas_incompletas_hoy': total_entregas_incompletas_hoy,
        'labels_repartos_mensuales': labels_repartos_mensuales,
        'data_repartos_mensuales': data_repartos_mensuales,
        'labels_estados': labels_estados,
        'data_estados': data_estados,
        'mensajes_no_leidos': cantidad_no_leidos,  # Número de mensajes no leídos
        'mensajes_recientes': mensajes_recientes,  # Lista de los mensajes recientes
    })
