import json
from django.shortcuts import render, redirect
from django.utils import timezone
from datetime import datetime, timedelta
import pytz
from django.http import HttpRequest, HttpResponse
from django.contrib import messages

# Importa tus nuevos servicios, utilidades y decoradores
# from ..core.firebase_client import FirebaseClient  # Si necesitas acceso directo (preferir servicio)
from ..services.firebase_service import FirebaseService
from ..services.cache_service import cache_decorator
from ..decorators.auth import verify_firebase_token # Asumiendo que tienes un decorador para autenticación

# Configura tu logger personalizado
# import logging
# logger = logging.getLogger(__name__) # O usa tu clase CustomLogger

# Instancia servicios (puedes hacerlo global si las dependencias son simples)
firebase_service = FirebaseService()
# firebase_client = FirebaseClient() # Solo si es necesario

# @verify_firebase_token # Aplica tu decorador si es necesario
@cache_decorator(timeout=60) # Cachear por 1 minuto
async def dashboard_view(request: HttpRequest) -> HttpResponse:
    """
    Muestra el dashboard principal con estadísticas.
    Utiliza FirebaseService para obtener datos y aplica caché.
    """
    try:
        # Verifica si el usuario está autenticado (depende de tu implementación de middleware/decorador)
        # firebase_user = getattr(request, 'firebase_user', None)
        # if not firebase_user:
        #     messages.error(request, "Acceso no autorizado.")
        #     return redirect('login') # Redirige si no está autenticado

        # Configuración de zona horaria y fecha
        zona_horaria = pytz.timezone('America/Argentina/Buenos_Aires')
        fecha_actual_dt = timezone.now().astimezone(zona_horaria)
        fecha_actual = fecha_actual_dt.date()

        # Obtener fecha del filtro o usar la fecha actual
        fecha_str = request.GET.get('fecha')
        if fecha_str:
            try:
                fecha_seleccionada = datetime.strptime(fecha_str, "%Y-%m-%d").date()
                # Asegúrate de que fecha_seleccionada_dt tenga hora para comparar con Firestore
                fecha_seleccionada_dt = datetime.combine(fecha_seleccionada, datetime.min.time()).astimezone(zona_horaria)
            except ValueError:
                fecha_seleccionada = fecha_actual
                fecha_seleccionada_dt = fecha_actual_dt
        else:
            fecha_seleccionada = fecha_actual
            fecha_seleccionada_dt = fecha_actual_dt

        # Obtener datos usando el servicio (asumiendo funciones asíncronas)
        stats_dia = await firebase_service.get_dashboard_stats(fecha_seleccionada)
        stats_mensuales = await firebase_service.get_monthly_repartos_stats(fecha_seleccionada.year)
        total_vehiculos = await firebase_service.get_available_vehicles_count()

        # --- Consulta y procesamiento de zonas para los próximos 2 días ---
        zonas_dashboard = []
        try:
            # Obtener todas las zonas
            zonas_ref = firebase_service.db.collection('zonas')
            zonas_docs = zonas_ref.stream()
            zonas_dict = {z.id: z.to_dict() for z in zonas_docs}

            # Fechas de los próximos dos días (como datetime)
            fechas_objetivo = [fecha_actual + timedelta(days=1), fecha_actual + timedelta(days=2)]
            fecha_inicio = datetime.combine(fechas_objetivo[0], datetime.min.time()).astimezone(zona_horaria)
            fecha_fin = datetime.combine(fechas_objetivo[1], datetime.max.time()).astimezone(zona_horaria)

            # Obtener repartos de los próximos dos días usando rango de fechas
            repartos_ref = firebase_service.db.collection('repartos')
            repartos_query = repartos_ref.where('fecha_salida', '>=', fecha_inicio).where('fecha_salida', '<=', fecha_fin)
            repartos_docs = repartos_query.stream()

            # Agrupar repartos por zona (normalizando)
            zona_repartos = {}
            for r in repartos_docs:
                data = r.to_dict()
                zona = str(data.get('zona', '')).strip().lower()
                estado = data.get('estado_reparto', '').lower()
                if zona not in zona_repartos:
                    zona_repartos[zona] = []
                zona_repartos[zona].append(estado)

            # Procesar estado de cada zona (normalizando nombre)
            for zona_id, zona_data in zonas_dict.items():
                nombre_zona = str(zona_data.get('nombre', '')).strip().lower()
                estados = zona_repartos.get(nombre_zona, [])
                if not estados:
                    estado = 'sin_actividad'
                elif any(e == 'abierto' for e in estados):
                    estado = 'abierta'
                elif all(e in ['cerrado', 'finalizado'] for e in estados):
                    estado = 'cerrada'
                else:
                    estado = 'sin_actividad'
                zonas_dashboard.append({
                    'nombre': zona_data.get('nombre', zona_id),
                    'descripcion': zona_data.get('descripcion', ''),
                    'estado': estado,
                    'cantidad_repartos': len(estados)
                })
        except Exception as ex_zonas:
            print(f"Error obteniendo estado de zonas: {ex_zonas}")

        context = {
            'total_repartos_hoy': stats_dia.get('total', 0),
            'total_repartos_finalizados_hoy': stats_dia.get('finalizados', 0),
            'porcentaje_repartos_finalizados': stats_dia.get('porcentaje_finalizados', 0),
            'total_vehiculos_disponibles': total_vehiculos,
            'entregas_incompletas': stats_dia.get('incompletas', 0),
            'fecha_seleccionada': fecha_seleccionada.strftime("%Y-%m-%d"),
            'labels_repartos_mensuales': json.dumps(stats_mensuales.get('labels', [])),
            'data_repartos_mensuales': json.dumps(stats_mensuales.get('data', [])),
            'labels_estados': json.dumps(stats_dia.get('labels_estados', [])),
            'data_estados': json.dumps(stats_dia.get('data_estados', [])),
            'zonas_dashboard': zonas_dashboard
        }
        # Asegúrate que la plantilla 'dashboard.html' exista en 'templates/'
        return render(request, 'dashboard/dashboard.html', context)

    except Exception as e:
        # logger.error(f"Error en dashboard_view: {e}", exc_info=True)
        print(f"Error en el dashboard: {e}") # Log básico mientras configuras logger
        messages.error(request, f"Error al cargar el dashboard. Intente nuevamente.")
        # Proporciona un contexto por defecto en caso de error
        context_error = {
            'total_repartos_hoy': 0, 'total_repartos_finalizados_hoy': 0,
            'porcentaje_repartos_finalizados': 0, 'total_vehiculos_disponibles': 0,
            'entregas_incompletas': 0, 'fecha_seleccionada': fecha_actual.strftime("%Y-%m-%d"),
            'labels_repartos_mensuales': json.dumps([]), 'data_repartos_mensuales': json.dumps([0]*12),
            'labels_estados': json.dumps(['Abierto', 'En Curso', 'Finalizado']), 'data_estados': json.dumps([0,0,0]),
            'zonas_dashboard': []
        }
        return render(request, 'dashboard/dashboard.html', context_error)

# Si decides mover la lógica de exportar Excel aquí:
# async def exportar_repartos_dashboard_excel(request: HttpRequest) -> HttpResponse:
#     fecha_str = request.GET.get('fecha')
#     # ... obtener fecha_seleccionada ...
#     try:
#         workbook_data = await firebase_service.generate_repartos_excel(fecha_seleccionada)
#         response = HttpResponse(
#             workbook_data,
#             content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
#         )
#         response["Content-Disposition"] = f"attachment; filename=repartos_{fecha_seleccionada.strftime('%Y-%m-%d')}.xlsx"
#         return response
#     except Exception as e:
#         # logger.error(...)
#         messages.error(request, "Error al generar el archivo Excel.")
#         return redirect('dashboard') # O a donde sea apropiado
