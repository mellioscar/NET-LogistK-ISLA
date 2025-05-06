from typing import List, Dict
from firebase_admin import firestore
import asyncio
import datetime

class FirebaseService:
    def __init__(self):
        self.db = firestore.client()
        
    async def get_repartos_batch(self, fecha: str) -> List[Dict]:
        """Obtiene repartos en lotes para mejor performance"""
        query = self.db.collection('repartos')\
            .where('fecha_salida', '>=', fecha)\
            .limit(500)
            
        docs = query.stream()
        return [doc.to_dict() for doc in docs]

    async def get_dashboard_stats(self, fecha):
        """Devuelve estadísticas del día para el dashboard."""
        # Acepta fecha como date o datetime
        if isinstance(fecha, datetime.date) and not isinstance(fecha, datetime.datetime):
            fecha = datetime.datetime.combine(fecha, datetime.time.min)
        fecha_fin = fecha + datetime.timedelta(days=1)
        repartos_ref = self.db.collection('repartos')
        repartos_docs = repartos_ref.where('fecha_salida', '>=', fecha).where('fecha_salida', '<', fecha_fin).stream()
        total = 0
        finalizados = 0
        incompletas = 0
        estados = {}
        for doc in repartos_docs:
            data = doc.to_dict()
            total += 1
            estado = data.get('estado_reparto', '').lower()
            if estado == 'finalizado':
                finalizados += 1
            if estado != 'finalizado':
                incompletas += 1
            estados[estado] = estados.get(estado, 0) + 1
        porcentaje_finalizados = int((finalizados / total) * 100) if total > 0 else 0
        return {
            'total': total,
            'finalizados': finalizados,
            'incompletas': incompletas,
            'porcentaje_finalizados': porcentaje_finalizados,
            'labels_estados': list(estados.keys()),
            'data_estados': list(estados.values())
        }

    async def get_monthly_repartos_stats(self, year):
        """Devuelve datos mensuales de repartos para el gráfico de líneas."""
        repartos_ref = self.db.collection('repartos')
        repartos_docs = repartos_ref.stream()
        data = [0] * 12
        for doc in repartos_docs:
            d = doc.to_dict()
            fecha = d.get('fecha_salida', None)
            if isinstance(fecha, datetime.datetime) and fecha.year == year:
                mes = fecha.month - 1
                data[mes] += 1
        labels = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
        return {'labels': labels, 'data': data}

    async def get_available_vehicles_count(self):
        """Devuelve la cantidad de vehículos activos (activo == 'Si')."""
        vehiculos_ref = self.db.collection('vehiculos')
        vehiculos_docs = vehiculos_ref.where('activo', '==', 'Si').stream()
        count = sum(1 for _ in vehiculos_docs)
        return count
