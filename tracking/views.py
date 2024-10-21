# tracking/views.py

from django.shortcuts import render
from .utils import generar_calendario_mes, crear_mapa_tracking
from datetime import datetime
import locale


def mapa_tracking(request):
    # Generar el mapa (ver el ejemplo anterior con folium)
    crear_mapa_tracking()  # Esta función generará el archivo HTML del mapa
    return render(request, 'tracking/mapa_tracking.html')  # Renderiza la página con el mapa


# Configurar locale para español
locale.setlocale(locale.LC_TIME, 'Spanish_Spain.1252')  # Ajustar según el sistema operativo

def cronograma(request):
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

    # Generar el calendario en HTML
    calendario_html = generar_calendario_mes(anio, mes)

    # Renderizar la plantilla
    return render(request, 'tracking/cronograma.html', {
        'calendario_html': calendario_html,
        'nombre_mes': nombre_mes,
        'anio': anio,
        'prev_month': prev_month,
        'next_month': next_month,
        'prev_year': prev_year,
        'next_year': next_year,
    })
