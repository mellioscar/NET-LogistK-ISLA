# repartos/views.py
from datetime import datetime
from firebase_admin import firestore
from django.shortcuts import redirect, render
from django.contrib import messages
#from NetLogistK.decorators import roles_permitidos

db = firestore.client()

def listar_repartos(request):
    query = request.GET.get('search', '').strip()
    estado = request.GET.get('estado', '').strip()  # Obtener el estado del filtro
    repartos_ref = db.collection('repartos')
    repartos = []

    try:
        # Construir la consulta de Firestore
        if query and estado:
            docs = repartos_ref.where('estado_reparto', '==', estado).stream()
        elif query:
            docs = repartos_ref.stream()
        elif estado:
            docs = repartos_ref.where('estado_reparto', '==', estado).stream()
        else:
            docs = repartos_ref.stream()

        # Filtrar por texto localmente (Firestore no admite "contains" en búsquedas de texto)
        for doc in docs:
            data = doc.to_dict()
            if not query or (
                query.lower() in str(data.get('nro_reparto', '')).lower() or
                query.lower() in data.get('chofer', {}).get('nombre', '').lower() or
                query.lower() in (data.get('acompanante', {}).get('nombre', '') if data.get('acompanante') else '').lower() or
                query.lower() in data.get('zona', '').lower()):
                data['id'] = doc.id
                repartos.append(data)

        # Ordenar por número de reparto
        repartos = sorted(repartos, key=lambda x: int(x['nro_reparto']))

    except Exception as e:
        print("Error al listar repartos:", e)
        messages.error(request, f"Error al listar repartos: {e}")

    return render(request, 'repartos/listar_repartos.html', {'repartos': repartos, 'search': query, 'estado': estado})


def crear_reparto(request):
    sucursal_operario = request.session.get("user_sucursal")

    if request.method == "POST":
        try:
            # Obtener datos del formulario
            sucursal_id = request.POST.get("sucursal", "").strip()
            chofer_id = request.POST.get("chofer", "").strip()
            acompanante_id = request.POST.get("acompanante", "").strip()  # Puede estar vacío
            zona_id = request.POST.get("zona", "").strip()
            vehiculo_id = request.POST.get("vehiculo", "").strip()

            # Validar campos obligatorios
            if not chofer_id:
                messages.error(request, "Debe seleccionar un chofer.")
                return redirect("crear_reparto")
            if not zona_id:
                messages.error(request, "Debe seleccionar una zona.")
                return redirect("crear_reparto")
            if not vehiculo_id:
                messages.error(request, "Debe seleccionar un vehículo.")
                return redirect("crear_reparto")

            # Resolver datos clave desde Firestore
            chofer_doc = db.collection("recursos").document(chofer_id).get()
            zona_doc = db.collection("zonas").document(zona_id).get()
            vehiculo_doc = db.collection("vehiculos").document(vehiculo_id).get()

            chofer_nombre = f"{chofer_doc.to_dict().get('nombre')} {chofer_doc.to_dict().get('apellido')}" if chofer_doc.exists else "Desconocido"
            zona_nombre = zona_doc.to_dict().get("nombre", "Desconocida") if zona_doc.exists else "Desconocida"
            vehiculo_dominio = vehiculo_doc.to_dict().get("dominio", "Desconocido") if vehiculo_doc.exists else "Desconocido"

            # Acompañante puede estar vacío
            acompanante_nombre = ""
            if acompanante_id:
                acompanante_doc = db.collection("recursos").document(acompanante_id).get()
                if acompanante_doc.exists:
                    acompanante_nombre = f"{acompanante_doc.to_dict().get('nombre')} {acompanante_doc.to_dict().get('apellido')}"

            # Preparar datos para guardar
            data = {
                "fecha": request.POST.get("fecha", datetime.today().strftime("%Y-%m-%d")),
                "nro_reparto": request.POST["nro_reparto"],
                "chofer": {"id": chofer_id, "nombre": chofer_nombre},
                "acompanante": {"nombre": acompanante_nombre} if acompanante_id else None,  # Solo el nombre
                "zona": zona_nombre,  # Solo el nombre de la zona
                "vehiculo": vehiculo_dominio,  # Solo el dominio del vehículo
                "estado_reparto": request.POST.get("estado", "Pendiente"),
                "sucursal": sucursal_operario,
            }

            # Guardar en Firestore
            db.collection("repartos").add(data)
            messages.success(request, "Reparto creado exitosamente.")
            return redirect("listar_repartos")

        except Exception as e:
            print("Error al crear el reparto:", e)
            messages.error(request, f"Ocurrió un error: {e}")
            return redirect("crear_reparto")

    # Consultas para obtener sucursales, choferes, acompañantes, vehículos y zonas
    sucursales = db.collection("sucursales").stream()
    choferes = db.collection("recursos").where("categoria", "in", ["Chofer", "Chofer Gruista"]).stream()
    acompanantes = db.collection("recursos").where("categoria", "==", "Acompañante").stream()
    vehiculos = db.collection("vehiculos").where("tipo", "==", "Camion").stream()
    zonas = db.collection("zonas").stream()

    return render(request, "repartos/crear_repartos.html", {
        "sucursales": [doc.to_dict() | {"id": doc.id} for doc in sucursales],
        "choferes": [doc.to_dict() | {"id": doc.id} for doc in choferes],
        "acompanantes": [doc.to_dict() | {"id": doc.id} for doc in acompanantes],
        "vehiculos": [doc.to_dict() | {"id": doc.id} for doc in vehiculos],
        "zonas": [doc.to_dict() | {"id": doc.id} for doc in zonas],
        "hoy": datetime.today().strftime("%Y-%m-%d"),
    })


def editar_reparto(request, id):
    # Obtener la sucursal desde la sesión
    sucursal_operario = request.session.get("user_sucursal")

    # Referencia al reparto a editar
    reparto_ref = db.collection("repartos").document(id)
    reparto = reparto_ref.get().to_dict()

    if not reparto:
        messages.error(request, "El reparto no existe.")
        return redirect("listar_repartos")

    if request.method == "POST":
        try:
            # Datos actualizados del formulario
            chofer_id = request.POST.get("chofer", "").strip()
            acompanante_id = request.POST.get("acompanante", "").strip()
            zona_id = request.POST.get("zona", "").strip()
            vehiculo_id = request.POST.get("vehiculo", "").strip()

            # Resolver datos clave desde Firestore
            chofer_doc = db.collection("recursos").document(chofer_id).get()
            zona_doc = db.collection("zonas").document(zona_id).get()
            vehiculo_doc = db.collection("vehiculos").document(vehiculo_id).get()

            chofer_nombre = f"{chofer_doc.to_dict().get('nombre')} {chofer_doc.to_dict().get('apellido')}" if chofer_doc.exists else "Desconocido"
            zona_nombre = zona_doc.to_dict().get("nombre", "Desconocida") if zona_doc.exists else "Desconocida"
            vehiculo_dominio = vehiculo_doc.to_dict().get("dominio", "Desconocido") if vehiculo_doc.exists else "Desconocido"

            # Acompañante puede estar vacío
            acompanante_nombre = ""
            if acompanante_id:
                acompanante_doc = db.collection("recursos").document(acompanante_id).get()
                if acompanante_doc.exists:
                    acompanante_nombre = f"{acompanante_doc.to_dict().get('nombre')} {acompanante_doc.to_dict().get('apellido')}"

            # Preparar datos actualizados
            updated_data = {
                "fecha": request.POST.get("fecha", reparto.get("fecha", datetime.today().strftime("%Y-%m-%d"))),
                "nro_reparto": request.POST["nro_reparto"],
                "chofer": {"id": chofer_id, "nombre": chofer_nombre},
                "acompanante": {"nombre": acompanante_nombre} if acompanante_id else None,  # Solo el nombre
                "zona": zona_nombre,  # Solo el nombre de la zona
                "vehiculo": vehiculo_dominio,  # Solo el dominio del vehículo
                "estado_reparto": request.POST.get("estado", reparto.get("estado_reparto", "Pendiente")),
            }

            # Actualizar el reparto en Firestore
            reparto_ref.update(updated_data)
            messages.success(request, "Reparto actualizado exitosamente.")
            return redirect("listar_repartos")

        except Exception as e:
            print("Error al actualizar el reparto:", e)
            messages.error(request, f"Ocurrió un error al actualizar el reparto: {e}")
            return redirect("editar_reparto", id=id)

    # Consultas para obtener opciones de Firestore
    choferes = db.collection("recursos").where("categoria", "in", ["Chofer", "Chofer Gruista"]).stream()
    acompanantes = db.collection("recursos").where("categoria", "==", "Acompañante").stream()
    vehiculos = db.collection("vehiculos").where("tipo", "==", "Camion").stream()
    zonas = db.collection("zonas").stream()

    return render(request, "repartos/editar_reparto.html", {
        "reparto": reparto,
        "choferes": [doc.to_dict() | {"id": doc.id} for doc in choferes],
        "acompanantes": [doc.to_dict() | {"id": doc.id} for doc in acompanantes],
        "vehiculos": [doc.to_dict() | {"id": doc.id} for doc in vehiculos],
        "zonas": [doc.to_dict() | {"id": doc.id} for doc in zonas],
    })


def eliminar_reparto(request, reparto_id):
    reparto_ref = db.collection('repartos').document(reparto_id)
    reparto_ref.delete()
    messages.success(request, f'Reparto eliminado correctamente.')
    return redirect('listar_repartos')


def repartos_filtrados(request):
    # Obtener parámetros de fecha y estado desde la URL
    fecha_str = request.GET.get('fecha', '').strip()
    estado = request.GET.get('estado_reparto', '').strip()

    repartos_ref = db.collection('repartos')
    repartos = []

    try:
        if fecha_str and estado:
            # Filtro combinado: fecha y estado
            docs = repartos_ref.where('fecha', '==', fecha_str).where('estado_reparto', '==', estado).stream()
        elif fecha_str:
            # Filtro solo por fecha
            docs = repartos_ref.where('fecha', '==', fecha_str).stream()
        elif estado:
            # Filtro solo por estado
            docs = repartos_ref.where('estado_reparto', '==', estado).stream()
        else:
            # Sin filtros: traer todos los repartos
            docs = repartos_ref.stream()

        # Procesar documentos obtenidos
        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id
            repartos.append(data)

    except Exception as e:
        print(f"Error al filtrar repartos: {e}")
        messages.error(request, f"Error al filtrar repartos: {e}")

    # Enviar datos al template
    context = {
        'repartos': repartos,
        'fecha': fecha_str,
        'estado': estado,
    }
    return render(request, 'repartos/repartos_filtrados.html', context)
