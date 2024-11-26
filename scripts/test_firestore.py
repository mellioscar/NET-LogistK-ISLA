from firebase_admin import firestore

def agregar_documento():
    try:
        db = firestore.client()
        doc_ref = db.collection('test').document('prueba_documento')
        doc_ref.set({
            'nombre': 'Documento de Prueba',
            'creado_por': 'script_test_firestore',
            'activo': True
        })
        print("Documento agregado con éxito.")
    except Exception as e:
        print(f"Error agregando documento: {e}")

def leer_documentos():
    try:
        db = firestore.client()
        docs = db.collection('test').stream()
        print("Documentos en la colección 'test':")
        for doc in docs:
            print(f"- ID: {doc.id}, Data: {doc.to_dict()}")
    except Exception as e:
        print(f"Error leyendo documentos: {e}")

if __name__ == "__main__":
    print("=== Agregar Documento ===")
    agregar_documento()
    print("\n=== Leer Documentos ===")
    leer_documentos()
