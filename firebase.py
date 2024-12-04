# firebase.py

import firebase_admin
from firebase_admin import credentials, auth, firestore

cred = credentials.Certificate("secrets/firebase.json")
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = firestore.client()


# import firebase_admin
# from firebase_admin import credentials, firestore
# import warnings  # Importar módulo warnings para manejar advertencias

# # Ruta al archivo de credenciales
# cred = credentials.Certificate("secrets/firebase.json")

# # Verificar si Firebase ya fue inicializado
# if not firebase_admin._apps:
#     firebase_admin.initialize_app(cred)
#     print("1-Firebase inicializado correctamente.")
# else:
#     print("Firebase ya estaba inicializado.")

# # Suprimir advertencias específicas del SDK de Firestore
# warnings.filterwarnings("ignore", message="Detected filter using positional arguments.*", category=UserWarning)

# # Cliente Firestore
# db = firestore.client()

