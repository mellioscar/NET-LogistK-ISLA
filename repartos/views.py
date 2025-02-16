# repartos/views.py
from datetime import datetime
from firebase_admin import firestore
from django.shortcuts import redirect, render
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from NetLogistK.decorators import firebase_login_required
import pandas as pd

db = firestore.client()

def listar_repartos(request):
    try:
        # Obtener el estado del filtro
        estado = request.GET.get('estado', '')
        search_query = request.GET.get('search', '').strip()

        # Consultar repartos
        repartos_ref = db.collection('repartos')
        query = repartos_ref

        if estado:
            query = query.where('estado_reparto', '==', estado)

        # Ejecutar la consulta
        repartos = []
        for doc in query.stream():
            reparto = doc.to_dict()
            reparto['id'] = doc.id

            # Obtener y contar pedidos
            pedidos_ref = doc.reference.collection('pedidos')
            pedidos = list(pedidos_ref.stream())
            
            # Contar totales
            total_pedidos = len(pedidos)
            total_entregados = sum(1 for p in pedidos if p.to_dict().get('estado') == 'Entregado')
            total_incompletos = sum(1 for p in pedidos if p.to_dict().get('estado') == 'Incompleto')

            # Agregar contadores al reparto
            reparto['total_facturas'] = total_pedidos
            reparto['total_entregas'] = total_entregados
            reparto['total_incompletos'] = total_incompletos

            # Crear nombre completo del chofer
            if 'chofer' in reparto and isinstance(reparto['chofer'], dict):
                nombre = reparto['chofer'].get('nombre', '')
                apellido = reparto['chofer'].get('apellido', '')
                reparto['chofer']['nombre_completo'] = f"{nombre} {apellido}".strip()

            # Aplicar filtro de búsqueda si existe
            if search_query:
                if not (search_query.lower() in str(reparto.get('nro_reparto', '')).lower() or
                       search_query.lower() in str(reparto.get('chofer', {}).get('nombre_completo', '')).lower() or
                       search_query.lower() in str(reparto.get('zona', '')).lower()):
                    continue

            repartos.append(reparto)

        return render(request, 'repartos/listar_repartos.html', {
            'repartos': repartos,
            'estado': estado,
            'search': search_query
        })

    except Exception as e:
        print("Error al listar repartos:", e)
        messages.error(request, f"Error al listar repartos: {e}")
        return render(request, 'repartos/listar_repartos.html', {'repartos': []})


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


def importar_repartos(request):
    try:
        if request.method == 'POST' and request.FILES['archivo']:
            archivo = request.FILES['archivo']
            
            # Leer el archivo Excel
            df = pd.read_excel(archivo)
            
            # Iniciar transacción de Firestore
            batch = db.batch()
            
            for index, row in df.iterrows():
                try:
                    # Obtener datos del chofer
                    chofer_id = str(row['chofer_id']).strip()
                    chofer_doc = db.collection('recursos').document(chofer_id).get()
                    if not chofer_doc.exists:
                        continue
                        
                    chofer_data = chofer_doc.to_dict()
                    nombre_completo = f"{chofer_data.get('nombre', '')} {chofer_data.get('apellido', '')}"
                    
                    # Crear el documento del reparto
                    reparto_ref = db.collection('repartos').document()
                    datos_reparto = {
                        'fecha': row['fecha'].strftime('%d-%m-%Y'),
                        'fecha_creacion': datetime.now().strftime('%d-%m-%Y'),
                        'nro_reparto': str(row['nro_reparto']).strip(),
                        'chofer': {
                            'id': chofer_id,
                            'nombre_completo': nombre_completo
                        },
                        'sucursal': str(row['sucursal']).strip(),
                        'zona': str(row['zona']).strip(),
                        'vehiculo': str(row['vehiculo']).strip(),
                        'estado_reparto': 'Abierto',
                        'total_facturas': 0  # Inicializamos el contador
                    }
                    
                    batch.set(reparto_ref, datos_reparto)
                    
                    # Obtener pedidos asociados al reparto
                    pedidos_query = db.collection('pedidos').where('nro_reparto', '==', str(row['nro_reparto']).strip())
                    total_facturas = 0
                    
                    for pedido in pedidos_query.stream():
                        total_facturas += 1
                        pedido_ref = db.collection('pedidos').document(pedido.id)
                        batch.update(pedido_ref, {
                            'reparto_id': reparto_ref.id,
                            'estado': 'Asignado'
                        })
                    
                    # Actualizar el total de facturas
                    batch.update(reparto_ref, {'total_facturas': total_facturas})
                    
                except Exception as e:
                    print(f"Error procesando fila {index + 2}: {e}")
                    continue
            
            # Commit de la transacción
            batch.commit()
            messages.success(request, "Repartos importados correctamente")
            
        return redirect('listar_repartos')
        
    except Exception as e:
        print("Error al importar repartos:", e)
        messages.error(request, f"Error al importar repartos: {e}")
        return redirect('listar_repartos')


def ver_detalle_reparto(request, nro_reparto):
    # Por ahora, simplemente redirigimos al nuevo template
    return render(request, 'repartos/detalle_listado.html')