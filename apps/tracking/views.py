# tracking/views.py

from django.shortcuts import render
from .utils import crear_mapa_tracking
from datetime import datetime, timedelta
import locale
from NetLogistK.utils.firebase import db
import calendar
from django.http import JsonResponse
import os
from django.conf import settings
from firebase_admin import firestore
import folium
from geopy.geocoders import Nominatim


def mapa_tracking(request):
    # Generar el mapa (ver el ejemplo anterior con folium)
    crear_mapa_tracking()  # Esta función generará el archivo HTML del mapa
    # Leer el HTML generado por folium
    folium_path = os.path.join(settings.BASE_DIR, 'NetLogistK', 'static', 'tracking', 'tracking_mapa.html')
    folium_map = ''
    if os.path.exists(folium_path):
        with open(folium_path, 'r', encoding='utf-8') as f:
            folium_map = f.read()
    return render(request, 'tracking/mapa_tracking.html', {'folium_map': folium_map})
