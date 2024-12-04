import requests
from firebase_admin import auth
from firebase_admin.firestore import Client

# Firebase API Key
API_KEY = "AIzaSyCkj3ZWSU_UdlDoyfonJTexHkcF7JLV4m4"

def sign_in_with_email_and_password(email, password):
    """
    Autentica un usuario con Firebase usando la API REST.
    """
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={API_KEY}"
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }

    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            # Capturar el mensaje de error devuelto por Firebase
            error_message = response.json().get("error", {}).get("message", "Error desconocido")
            raise ValueError(f"Error en el inicio de sesión: {error_message}")
    except requests.RequestException as e:
        raise ValueError(f"Error en la comunicación con Firebase: {e}")

def verify_id_token(id_token):
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except auth.ExpiredIdTokenError:
        print("[FIREBASE UTILS] Token expirado.")
        raise
    except auth.InvalidIdTokenError:
        print("[FIREBASE UTILS] Token inválido.")
        raise
    except Exception as e:
        print(f"[FIREBASE UTILS] Error al verificar token: {e}")
        raise

def renew_id_token(refresh_token):
    try:
        refresh_url = f"https://securetoken.googleapis.com/v1/token?key={API_KEY}"
        response = requests.post(refresh_url, data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        })
        if response.status_code == 200:
            print("[FIREBASE UTILS] Token renovado correctamente.")
            return response.json().get("id_token"), response.json().get("refresh_token")
        else:
            print(f"[FIREBASE UTILS] Error al renovar el token: {response.json()}")
            return None, None
    except Exception as e:
        print(f"[FIREBASE UTILS] Error durante la renovación del token: {e}")
        return None, None

def get_user_from_firestore(uid, db: Client):
    user_doc = db.collection("usuarios").document(uid).get()
    if user_doc.exists:
        return user_doc.to_dict()
    return None
