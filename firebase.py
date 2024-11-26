# firebase.py
import firebase_admin
from firebase_admin import credentials, firestore

# Ruta al archivo de credenciales
cred = credentials.Certificate("secrets/firebase.json")

# Verificar si Firebase ya fue inicializado
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
    print("Firebase inicializado correctamente.")
else:
    print("Firebase ya estaba inicializado.")

# Cliente Firestore
db = firestore.client()
