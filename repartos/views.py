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
        estado = request.GET.get('estado', '')
        search_query = request.GET.get('search', '').strip()

        # Consultar repartos
        repartos_ref = db.collection('repartos')
        query = repartos_ref.order_by('fecha_salida', direction=firestore.Query.DESCENDING)

        if estado:
            query = query.where('estado_reparto', '==', estado)

        repartos = []
        for doc in query.stream():
            reparto = doc.to_dict()
            reparto['id'] = doc.id

            # Convertir timestamp a string para mostrar
            fecha_salida = reparto.get('fecha_salida')
            if fecha_salida:
                reparto['fecha_salida'] = fecha_salida.strftime('%d/%m/%Y')

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

#VERIFICAR QUE SEA IGUAL AL DE IMPORTAR PEDIDOS - HAY DIFERENCIAS
def crear_reparto(request):
    sucursal_operario = request.session.get("user_sucursal")

    if request.method == "POST":
        try:
            # Obtener datos del formulario
            chofer_id = request.POST.get("chofer", "").strip()
            acompanante_id = request.POST.get("acompanante", "").strip()
            zona_id = request.POST.get("zona", "").strip()
            vehiculo_id = request.POST.get("vehiculo", "").strip()
            fecha_salida = request.POST.get("fecha")
            nro_reparto = request.POST.get("nro_reparto")  # Ya viene formateado del frontend

            # Validaciones...
            if not all([chofer_id, zona_id, vehiculo_id, fecha_salida, nro_reparto]):
                messages.error(request, "Todos los campos obligatorios deben estar completos.")
                return redirect("crear_reparto")

            # Obtener datos relacionados
            chofer_doc = db.collection("recursos").document(chofer_id).get()
            zona_doc = db.collection("zonas").document(zona_id).get()
            vehiculo_doc = db.collection("vehiculos").document(vehiculo_id).get()

            chofer_data = chofer_doc.to_dict()
            nombre_completo = f"{chofer_data['nombre']} {chofer_data.get('apellido', '')}"

            # Convertir fecha_salida a timestamp
            fecha_obj = datetime.strptime(fecha_salida, '%Y-%m-%d')
            fecha_salida_timestamp = datetime.combine(fecha_obj.date(), datetime.min.time())

            # Preparar datos del reparto
            data = {
                'nro_reparto': nro_reparto,
                'fecha_salida': fecha_salida_timestamp,
                'fecha_creacion': datetime.now(),
                'chofer': {
                    'id': chofer_id,
                    'nombre': chofer_data['nombre'],
                    'apellido': chofer_data.get('apellido', ''),
                    'nombre_completo': nombre_completo
                },
                'vehiculo': vehiculo_doc.to_dict().get('dominio'),
                'zona': zona_doc.to_dict().get('nombre'),
                'estado_reparto': 'Abierto',
                'sucursal': sucursal_operario,
            }

            # Si hay acompañante, agregarlo
            if acompanante_id:
                acompanante_doc = db.collection("recursos").document(acompanante_id).get()
                if acompanante_doc.exists:
                    acompanante_data = acompanante_doc.to_dict()
                    data['acompanante'] = {
                        'id': acompanante_id,
                        'nombre': acompanante_data['nombre'],
                        'apellido': acompanante_data.get('apellido', '')
                    }

            # Crear documento de reparto
            nuevo_reparto = db.collection("repartos").document()
            nuevo_reparto.set(data)

            # Crear colección de pedidos vacía
            pedidos_ref = nuevo_reparto.collection('pedidos')
            # Crear un documento inicial vacío en la colección de pedidos
            pedidos_ref.document().set({
                'fecha_creacion': datetime.now().strftime('%d-%m-%Y'),
                'estado': 'Pendiente'
            })

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
                "fecha": request.POST.get("fecha", reparto.get("fecha", datetime.today().strftime("%d-%m-%Y"))),
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
            df = pd.read_excel(archivo)
            batch = db.batch()
            
            for index, row in df.iterrows():
                try:
                    chofer_id = str(row['chofer_id']).strip()
                    chofer_doc = db.collection('recursos').document(chofer_id).get()
                    
                    if not chofer_doc.exists:
                        continue
                        
                    chofer_data = chofer_doc.to_dict()
                    nombre_completo = f"{chofer_data.get('nombre', '')} {chofer_data.get('apellido', '')}"
                    
                    # Convertir fecha del excel a timestamp
                    fecha_excel = row['fecha']
                    if isinstance(fecha_excel, str):
                        fecha_obj = datetime.strptime(fecha_excel, '%d-%m-%Y')
                    else:
                        fecha_obj = fecha_excel
                    
                    fecha_salida = datetime.combine(fecha_obj.date(), datetime.min.time())
                    
                    datos_reparto = {
                        'fecha_salida': fecha_salida,
                        'fecha_creacion': datetime.now(),
                        'nro_reparto': str(row['nro_reparto']).strip(),
                        'chofer': {
                            'id': chofer_id,
                            'nombre_completo': nombre_completo
                        },
                        'sucursal': str(row['sucursal']).strip(),
                        'zona': str(row['zona']).strip(),
                        'vehiculo': str(row['vehiculo']).strip(),
                        'estado_reparto': 'Abierto',
                        'total_facturas': 0
                    }
                    
                    reparto_ref = db.collection('repartos').document()
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
    try:
        db = firestore.client()
        reparto_ref = db.collection('repartos').where('nro_reparto', '==', nro_reparto).limit(1).stream()
        reparto_data = None
        
        for doc in reparto_ref:
            reparto_data = doc.to_dict()
            break
            
        if not reparto_data:
            messages.error(request, 'Reparto no encontrado')
            return redirect('cronograma_semanal')
            
        # Obtener pedidos y sus artículos
        pedidos_ref = doc.reference.collection('pedidos').stream()
        pedidos = []
        peso_total = 0
        
        for pedido in pedidos_ref:
            pedido_data = pedido.to_dict()
            
            # Obtener artículos del array dentro del pedido
            articulos = []
            for articulo in pedido_data.get('articulos', []):
                articulos.append({
                    'cantidad': articulo.get('cantidad', '0'),
                    'codigo': articulo.get('codigo', ''),
                    'descripcion': articulo.get('descripcion', ''),
                    'peso': float(articulo.get('peso', 0))
                })
            
            # Calcular peso total del pedido
            peso_pedido = sum(float(art.get('peso', 0)) for art in pedido_data.get('articulos', []))
            peso_total += peso_pedido
            
            estado_color = {
                'Asignado': 'primary',
                'Entregado': 'success',
                'Pendiente': 'warning',
                'Cancelado': 'danger'
            }.get(pedido_data.get('estado', ''), 'secondary')
            
            pedidos.append({
                'nro_factura': pedido_data.get('nro_factura', ''),
                'cliente': pedido_data.get('cliente', ''),
                'direccion': pedido_data.get('direccion', ''),
                'estado': pedido_data.get('estado', 'Sin estado'),
                'estado_color': estado_color,
                'peso': peso_pedido,
                'articulos': articulos
            })
        
        context = {
            'reparto': {
                'nro_reparto': reparto_data.get('nro_reparto', ''),
                'fecha': reparto_data.get('fecha', ''),
                'estado': reparto_data.get('estado_reparto', 'Sin estado'),
                'estado_color': estado_color,
                'chofer': reparto_data.get('chofer', {}).get('nombre_completo', 'Sin chofer'),
                'zona': reparto_data.get('zona', 'Sin zona'),
                'sucursal': reparto_data.get('sucursal', 'Sin sucursal'),
                'total_facturas': len(pedidos),
                'peso_total': peso_total
            },
            'pedidos': pedidos,
            'fecha_actual': request.GET.get('fecha', '')
        }
        
        return render(request, 'repartos/detalle_listado.html', context)
        
    except Exception as e:
        messages.error(request, f'Error al cargar los detalles del reparto: {str(e)}')
        return redirect('listar_repartos')
