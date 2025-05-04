# cronograma/utils.py
import calendar
from datetime import datetime, timedelta
from firebase_admin import firestore

# CALENDARIO DE CRONOGRAMA

# Definir la clase personalizada para el calendario
class CustomHTMLCalendar(calendar.HTMLCalendar):
    def formatweekday(self, day):
        # Definir los días de la semana en español
        weekdays = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        return f'<th class="text-center">{weekdays[day]}</th>'

    def formatmonthname(self, theyear, themonth, withyear=True):
        # Obtener el nombre del mes en español con la primera letra en mayúscula
        month_name = calendar.month_name[themonth].capitalize()
        return f'<tr><th colspan="7" class="text-center">{month_name} {theyear}</th></tr>'

# Función para generar el calendario HTML con el mes y año dados
def generar_calendario_mes(anio, mes):
    cal = CustomHTMLCalendar(calendar.MONDAY)
    # Generar el calendario HTML
    calendario_html = cal.formatmonth(anio, mes)
    
    # Añadir estilos CSS
    return f"""
    <div class="custom-calendar">
        <table class="table table-bordered text-center">
            {calendario_html}
        </table>
    </div>
    """

def obtener_repartos_periodo(fecha_inicio, fecha_fin):
    """
    Obtiene los repartos para un período específico
    """
    db = firestore.client()
    repartos = {}
    
    try:
        repartos_ref = db.collection('repartos').stream()
        
        for reparto in repartos_ref:
            data = reparto.to_dict()
            fecha_reparto = data.get('fecha', '')
            
            try:
                fecha_reparto_dt = datetime.strptime(fecha_reparto, '%d-%m-%Y')
                if fecha_inicio <= fecha_reparto_dt <= fecha_fin:
                    dia = fecha_reparto_dt.day
                    
                    if dia not in repartos:
                        repartos[dia] = []
                    
                    repartos[dia].append(formatear_reparto(data))
            except Exception:
                continue
                
        return repartos
    except Exception as e:
        print(f"Error al obtener repartos: {e}")
        return {}

def formatear_reparto(data):
    """
    Formatea los datos del reparto para su visualización
    """
    estado_color = {
        'Abierto': 'primary',
        'Cerrado': 'danger',
        'Finalizado': 'success',
        'Cancelado': 'secondary'
    }.get(data.get('estado_reparto', ''), 'secondary')
    
    return {
        'nro_reparto': data.get('nro_reparto', ''),
        'zona': data.get('zona', 'Sin zona'),
        'estado': data.get('estado_reparto', 'Sin estado'),
        'estado_color': estado_color,
        'chofer': data.get('chofer', {}).get('nombre_completo', 'Sin chofer'),
        'fecha': data.get('fecha', ''),
        'zona_descripcion': data.get('zona_descripcion', '')
    }

def generar_semana(fecha):
    """
    Genera la estructura de la semana a partir de una fecha
    """
    lunes = fecha - timedelta(days=fecha.weekday())
    domingo = lunes + timedelta(days=6)
    hoy = datetime.now().date()
    
    semana = []
    for i in range(7):
        dia_actual = lunes + timedelta(days=i)
        semana.append({
            'fecha': dia_actual,
            'numero': dia_actual.day,
            'nombre': dia_actual.strftime('%A').capitalize(),
            'hoy': dia_actual.date() == hoy
        })
    
    return semana, lunes, domingo

def obtener_rango_fechas(fecha_str=None):
    """
    Obtiene el rango de fechas para la semana
    """
    if fecha_str:
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d')
    else:
        fecha = datetime.now()
    
    lunes = fecha - timedelta(days=fecha.weekday())
    domingo = lunes + timedelta(days=6)
    
    return lunes, domingo

def get_week_dates(fecha):
    """
    Obtiene las fechas de la semana (lunes a domingo) en formato `dd-mm-yyyy`
    """
    dia_semana = fecha.weekday()
    lunes = fecha - timedelta(days=dia_semana)

    # Convertir todas las fechas al formato esperado por Firestore
    return [(lunes + timedelta(days=i)).strftime('%d-%m-%Y') for i in range(7)]

