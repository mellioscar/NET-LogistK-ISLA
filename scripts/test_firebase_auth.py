import firebase_admin
from firebase_admin import credentials, auth

# Ruta completa o relativa al archivo JSON de credenciales
cred = credentials.Certificate("C:/Users/oscar/OneDrive/Documentos/Carlos Isla/Proyecto - Carlos Isla/NET-LogistiK ISLA/App NET-LogistK ISLA/secrets/firebase.json")

# Inicializar Firebase
try:
    firebase_admin.initialize_app(cred)
    print("Script - Firebase inicializado correctamente.")
except Exception as e:
    print(f"Error al inicializar Firebase: {e}")

def listar_usuarios():
    try:
        users = auth.list_users().users
        print("Usuarios existentes:")
        for user in users:
            print(f"- Email: {user.email}, UID: {user.uid}")
    except Exception as e:
        print(f"Error listando usuarios: {e}")

# def crear_usuario():
#     try:
#         user = auth.create_user(
#             email="prueba@example.com",
#             password="ContraseñaSegura123",
#             display_name="Usuario de Prueba"
#         )
#         print(f"Usuario creado con éxito: {user.uid}")
#     except Exception as e:
#         print(f"Error creando usuario: {e}")

if __name__ == "__main__":
    print("=== Listar Usuarios ===")
    listar_usuarios()
    #print("\n=== Crear Usuario ===")
    #crear_usuario()
    #print("\n=== Listar Usuarios Nuevamente ===")
    #listar_usuarios()
