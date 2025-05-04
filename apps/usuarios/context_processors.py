# usuarios/context_processors.py
from NetLogistK.utils.firebase import db  # Importar cliente Firestore desde firebase.py

def user_profile(request):
    """
    Proporciona información del perfil del usuario autenticado a los templates.
    """
    try:
        # Verificar si hay un usuario autenticado en Firebase
        user_uid = request.session.get('firebase_uid')
        if not user_uid:
            return {}
        
        # Obtener datos del usuario desde Firestore
        user_doc = db.collection('usuarios').document(user_uid).get()
        if user_doc.exists:
            user_data = user_doc.to_dict()
            return {
                'full_name': f"{user_data.get('nombre', '')} {user_data.get('apellido', '')}".strip(),
                'email': user_data.get('email', ''),
                'rol': user_data.get('rol', ''),
                'sucursal': user_data.get('sucursal', ''),
            }
        else:
            # Si no se encuentra el documento, devolver un contexto vacío
            return {}

    except Exception as e:
        # Loguear el error para depuración
        print(f"[CONTEXT_PROCESSOR ERROR] {str(e)}")
        return {}

