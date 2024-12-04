# scripts/cargar_zonas
from xml.etree import ElementTree as ET
from firebase_admin import firestore, credentials, initialize_app

# Inicializar Firebase
cred = credentials.Certificate("secrets/firebase.json")
initialize_app(cred)
db = firestore.client()

def cargar_zonas_desde_kml(file_path):
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        namespaces = {'kml': 'http://www.opengis.net/kml/2.2'}

        for placemark in root.findall('.//kml:Placemark', namespaces):
            # Validar si los elementos existen antes de intentar acceder a ellos
            nombre = placemark.find('kml:name', namespaces)
            descripcion = placemark.find('kml:description', namespaces)
            coordenadas = placemark.find('.//kml:coordinates', namespaces)

            # Obtener valores o asignar un valor por defecto
            data = {
                'nombre': nombre.text if nombre is not None else 'Sin nombre',
                'descripcion': descripcion.text if descripcion is not None else 'Sin descripción',
                'sucursal': '',
                'info': '',
                'coordenadas': coordenadas.text.strip() if coordenadas is not None else 'Sin coordenadas',
            }
            db.collection('zonas').add(data)

        print("Zonas cargadas exitosamente desde el archivo KML.")
    except Exception as e:
        print(f"Error al cargar zonas desde el archivo KML: {e}")

# Ruta absoluta del archivo KML
if __name__ == "__main__":
    file_path = r"NetLogistK\ZonasCI.kml"  # Ruta del archivo KML
    cargar_zonas_desde_kml(file_path)

