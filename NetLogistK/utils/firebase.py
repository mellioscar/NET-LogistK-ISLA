import firebase_admin
from firebase_admin import credentials, auth, firestore
from django.conf import settings
from pathlib import Path

def initialize_firebase():
    """
    Inicializa Firebase si aún no está inicializado
    """
    if not firebase_admin._apps:
        try:
            # Usar la ruta desde settings.py
            cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
            firebase_admin.initialize_app(cred)
            print("Firebase inicializado correctamente.")
        except Exception as e:
            print(f"Error inicializando Firebase: {e}")
            raise

    return firestore.client()

# Inicializar Firebase y obtener el cliente de Firestore
db = initialize_firebase() 