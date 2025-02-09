# firebase.py

import firebase_admin
from firebase_admin import credentials, auth, firestore

cred = credentials.Certificate("secrets/firebase.json")
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = firestore.client()
