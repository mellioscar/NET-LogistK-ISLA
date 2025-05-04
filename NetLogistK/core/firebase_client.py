from firebase_admin import firestore
from functools import lru_cache
import asyncio

class FirebaseClient:
    def __init__(self):
        self.db = firestore.client()
        
    @lru_cache(maxsize=100)
    async def get_cached_collection(self, collection_name):
        """Obtiene y cachea colecciones frecuentemente accedidas"""
        docs = self.db.collection(collection_name).stream()
        return [doc.to_dict() for doc in docs]
        
    async def batch_write(self, operations):
        """Escritura por lotes para mejor performance"""
        batch = self.db.batch()
        for op in operations:
            # Implementar lógica de batch
            pass
        await batch.commit()
