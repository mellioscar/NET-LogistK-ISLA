# views.py
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Count, Sum
from datetime import datetime, date
from vehiculos.models import Vehiculo
from repartos.models import Reparto
from django.db.models.functions import TruncMonth
import pytz

from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from django.templatetags.static import static

from django.contrib.auth.decorators import login_required
from mensajes.models import Mensaje
from usuarios.models import Profile

def exportar_reporte_pdf(request):
    # Obtener la fecha seleccionada
    fecha_str = request.GET.get('fecha')
    if fecha_str:
        fecha_actual = datetime.strptime(fecha_str, "%Y-%m-%d").date()
    else:
        fecha_actual = date.today()

    # Obtener datos de repartos
    logo_url = request.build_absolute_uri(static('img/Logo NET-LOGISTK.jpg'))
    repartos = Reparto.objects.filter(fecha=fecha_actual)
    total_repartos = repartos.count()
    total_vehiculos = Vehiculo.objects.count()
    total_repartos_finalizados = repartos.filter(estado='Finalizado').count()
    porcentaje_repartos_finalizados = (total_repartos_finalizados / total_repartos) * 100 if total_repartos > 0 else 0
    total_entregas_incompletas_hoy = repartos.aggregate(total_incompletos=Sum('incompletos'))['total_incompletos'] or 0

    # Calcular los porcentajes de estados para el gráfico de barras
    estados = repartos.values('estado').annotate(total=Count('estado'))
    estados_data = []
    for estado in estados:
        porcentaje = (estado['total'] / total_repartos) * 100 if total_repartos > 0 else 0
        estados_data.append({
            'estado': estado['estado'],
            'porcentaje': porcentaje,
            'total': estado['total']
        })

    context = {
        'fecha': fecha_actual,
        'repartos': repartos,
        'total_repartos': total_repartos,
        'total_vehiculos': total_vehiculos,
        'porcentaje_repartos_finalizados': porcentaje_repartos_finalizados,
        'total_entregas_incompletas_hoy': total_entregas_incompletas_hoy,
        'logo_url': logo_url,
        'usuario': request.user.get_full_name() or request.user.username,
    }

    html_string = render_to_string('reportes/reporte_pdf.html', context)
    html = HTML(string=html_string)
    pdf_file = html.write_pdf()

    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="reporte_{fecha_actual}.pdf"'
    return response


@login_required
def dashboard(request):
    # Zona horaria de Buenos Aires
    zona_horaria = pytz.timezone('America/Argentina/Buenos_Aires')

    # Obtener la fecha seleccionada por el usuario, o usar la fecha actual si no hay ninguna
    fecha_str = request.GET.get('fecha')
    if fecha_str:
        try:
            fecha_seleccionada = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except ValueError:
            fecha_seleccionada = timezone.now().astimezone(zona_horaria).date()  # Usar la fecha actual local
    else:
        fecha_seleccionada = timezone.now().astimezone(zona_horaria).date()

    # Obtener los datos basados en la fecha seleccionada
    total_repartos_hoy = Reparto.objects.filter(fecha=fecha_seleccionada).count()
    total_vehiculos = Vehiculo.objects.count()
    total_repartos_finalizados_hoy = Reparto.objects.filter(fecha=fecha_seleccionada, estado='Finalizado').count()
    porcentaje_repartos_finalizados = (total_repartos_finalizados_hoy / total_repartos_hoy) * 100 if total_repartos_hoy > 0 else 0
    total_entregas_incompletas_hoy = Reparto.objects.filter(fecha=fecha_seleccionada).aggregate(total_incompletos=Sum('incompletos'))['total_incompletos'] or 0

    # Datos para el gráfico de área (Repartos Mensuales)
    year_actual = fecha_seleccionada.year
    repartos_mensuales = (
        Reparto.objects.filter(fecha__year=year_actual)
        .annotate(month=TruncMonth('fecha'))
        .values('month')
        .annotate(total=Count('id'))
        .order_by('month')
    )

    # Crear listas de etiquetas y datos para el gráfico
    labels_repartos_mensuales = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    data_repartos_mensuales = [0] * 12  # Inicializar la lista con 12 meses

    # Llenar los datos reales obtenidos de la consulta
    for reparto in repartos_mensuales:
        month = reparto['month'].month - 1  # Ajustar índice (0 = Enero, 11 = Diciembre)
        data_repartos_mensuales[month] = reparto['total']

    # Datos para el gráfico circular (Segmentación por Estado)
    estados_repartos = Reparto.objects.filter(fecha=fecha_seleccionada).values('estado').annotate(total=Count('estado'))
    labels_estados = [estado['estado'] for estado in estados_repartos]
    data_estados = [estado['total'] for estado in estados_repartos]


    # Obtener el perfil del usuario autenticado
    profile_logged_in = Profile.objects.get(user=request.user)
    # Obtener la cantidad de mensajes no leídos del usuario actual
    mensajes_no_leidos = Mensaje.objects.filter(receptor=request.user, leido=False).count()
    
    # Obtener los últimos 5 mensajes no leídos
    mensajes_recientes = Mensaje.objects.filter(receptor=request.user, leido=False).order_by('-fecha_envio')[:5]

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
        'profile_logged_in': profile_logged_in,
        'mensajes_no_leidos': mensajes_no_leidos,
        'mensajes_recientes': mensajes_recientes,
    })
