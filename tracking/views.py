# tracking/views.py

from django.shortcuts import render
from .utils import crear_mapa_tracking
from datetime import datetime, timedelta
import locale
from firebase_admin import firestore
import calendar
from django.http import JsonResponse


def mapa_tracking(request):
    # Generar el mapa (ver el ejemplo anterior con folium)
    crear_mapa_tracking()  # Esta función generará el archivo HTML del mapa
    return render(request, 'tracking/mapa_tracking.html')  # Renderiza la página con el mapa
