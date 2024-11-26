# usuarios/context_processors.py
from firebase_admin import firestore

def user_profile(request):
    if request.user.is_authenticated:
        user_uid = request.session.get('firebase_uid')
        if not user_uid:
            return {}
        
        db = firestore.client()
        user_doc = db.collection('usuarios').document(user_uid).get()
        
        if user_doc.exists:
            user_data = user_doc.to_dict()
            return {
                'full_name': user_data.get('nombre_completo', ''),
                'email': user_data.get('email', ''),
                'rol': user_data.get('rol', ''),
            }
    return {}
