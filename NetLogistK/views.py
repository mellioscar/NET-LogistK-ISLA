# views.py
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Count, Sum  # Asegúrate de importar Sum aquí
from datetime import datetime
from vehiculos.models import Vehiculo
from repartos.models import Reparto
from django.db.models.functions import TruncMonth
import pytz

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
    })
