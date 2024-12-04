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

    # Valores predeterminados para evitar consultas
    total_repartos_hoy = 10
    total_vehiculos = 3
    total_repartos_finalizados_hoy = 5
    porcentaje_repartos_finalizados = 50
    total_entregas_incompletas_hoy = 5
    labels_repartos_mensuales = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    data_repartos_mensuales = [0] * 12
    labels_estados = []
    data_estados = []

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
