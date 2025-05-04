from typing import List, Dict
from firebase_admin import firestore
import asyncio

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
