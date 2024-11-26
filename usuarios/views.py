# usuarios/views.py
from firebase_admin import auth, firestore
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
import json
from firebase import db
from django.middleware.csrf import get_token

def login_view(request):
    if request.method == "POST":
        try:
            print("Iniciando autenticación...")
            body = json.loads(request.body)
            id_token = body.get("idToken")

            if not id_token:
                return JsonResponse({"error": "Token no proporcionado"}, status=400)

            # Verificar el token con Firebase
            decoded_token = auth.verify_id_token(id_token, clock_skew_seconds=59)
            uid = decoded_token.get("uid")

            # Obtener datos adicionales del usuario desde Firestore
            user_doc = db.collection("usuarios").document(uid).get()

            if not user_doc.exists:
                return JsonResponse({"error": "Usuario no encontrado en Firestore"}, status=404)

            user_data = user_doc.to_dict()

            # Guardar los datos en la sesión
            request.session["firebase_id_token"] = id_token
            request.session["firebase_uid"] = uid
            request.session["firebase_user_email"] = user_data["email"]
            request.session["firebase_user_name"] = user_data.get("nombre", "")
            request.session["firebase_user_last_name"] = user_data.get("apellido", "Apellido no definido")
            request.session["firebase_user_role"] = user_data.get("rol", "Sin rol asignado")
            request.session["firebase_user_sucursal"] = user_data.get("sucursal", "Sin sucursal asignada")
            role = user_data.get("rol", "Ventas")
            request.session["firebase_user_icon"] = {
                "Administrador": "fa-user-cog",
                "Gerente": "fa-user-tie",
                "Logistica": "fa-truck-moving",
                "Ventas": "fa-user"
            }.get(role, "fa-user")

            # Redirigir al dashboard
            return JsonResponse({"message": "Inicio de sesión exitoso", "redirect_url": "/dashboard/"}, status=200)

        except Exception as e:
            print(f"Error autenticando: {e}")
            return JsonResponse({"error": f"Error autenticando: {str(e)}"}, status=401)

    elif request.method == "GET":
        # Renderizar el formulario de login
        csrf_token = get_token(request)
        return render(request, "usuarios/login.html", {"csrf_token": csrf_token})

    return JsonResponse({"error": "Método no permitido"}, status=405)


def logged_in_user_profile(request):
    try:
        user_uid = request.session.get("firebase_uid")
        if not user_uid:
            messages.error(request, "No se encontró el usuario autenticado.")
            return redirect("login")

        user_doc = db.collection("usuarios").document(user_uid).get()
        if not user_doc.exists():
            messages.error(request, "No se encontró el perfil del usuario en Firestore.")
            return redirect("dashboard")

        user_data = user_doc.to_dict()
        return render(request, "usuarios/perfil_usuario.html", {"usuario": user_data})

    except Exception as e:
        messages.error(request, f"Error al cargar el perfil del usuario: {str(e)}")
        return redirect("dashboard")


def crear_usuario(request):
    estados = ["Activo", "Inactivo"]  # Estados posibles
    sucursales = [{'id': doc.id, **doc.to_dict()} for doc in db.collection('sucursales').stream()]

    if request.method == 'POST':
        email = request.POST.get('email')
        email_confirmation = request.POST.get('email_confirmation')
        nombre = request.POST.get('first_name')
        apellido = request.POST.get('last_name')
        password = request.POST.get('password1')
        password_confirmation = request.POST.get('password2')
        rol = request.POST.get('rol')
        estado = request.POST.get('estado')  # Capturar como string
        sucursal = request.POST.get('sucursal')

        # Validaciones
        if email != email_confirmation:
            messages.error(request, "Los correos electrónicos no coinciden.")
            return render(request, 'usuarios/crear_usuarios.html', {'sucursales': sucursales, 'estados': estados})

        if password != password_confirmation:
            messages.error(request, "Las contraseñas no coinciden.")
            return render(request, 'usuarios/crear_usuarios.html', {'sucursales': sucursales, 'estados': estados})

        try:
            # Crear usuario en Firebase Authentication
            user = auth.create_user(
                email=email,
                password=password,
                display_name=f"{nombre} {apellido}"
            )

            # Registrar datos adicionales en Firestore
            db.collection('usuarios').document(user.uid).set({
                'nombre': nombre,
                'apellido': apellido,
                'email': email,
                'rol': rol,
                'estado': estado,
                'sucursal': sucursal,
                'uid': user.uid,
                'fecha_creacion': firestore.SERVER_TIMESTAMP
            })

            messages.success(request, f"Usuario {email} creado exitosamente.")
            return redirect('listar_usuarios')

        except auth.EmailAlreadyExistsError:
            messages.error(request, "El email ya está registrado.")
        except Exception as e:
            messages.error(request, f"Error al crear el usuario: {str(e)}")

    return render(request, 'usuarios/crear_usuarios.html', {'sucursales': sucursales, 'estados': estados})


def listar_usuarios(request):
    try:
        # Obtener el valor del parámetro de búsqueda
        search_query = request.GET.get('search', '').strip()  # Usar strip() para eliminar espacios en blanco

        # Consultar todos los usuarios desde Firestore
        usuarios_ref = db.collection('usuarios')
        usuarios = usuarios_ref.stream()

        # Crear una lista con los datos de los usuarios
        usuarios_list = [
            {**user.to_dict(), 'uid': user.id}
            for user in usuarios
        ]

        # Filtrar usuarios si hay un término de búsqueda
        if search_query:
            usuarios_list = [
                usuario for usuario in usuarios_list
                if search_query.lower() in usuario.get('nombre', '').lower() or
                    search_query.lower() in usuario.get('apellido', '').lower() or
                    search_query.lower() in usuario.get('email', '').lower()
            ]

    except Exception as e:
        messages.error(request, f"Error al listar usuarios: {str(e)}")
        usuarios_list = []

    # Pasar el término de búsqueda y los usuarios filtrados al template
    return render(request, 'usuarios/listar_usuarios.html', {
        'usuarios': usuarios_list,
        'search': search_query
    })


def eliminar_usuario(request, uid):
    try:
        auth.delete_user(uid)
        db.collection('usuarios').document(uid).delete()
        messages.success(request, f"Usuario fue eliminado exitosamente.")
    except Exception as e:
        messages.error(request, f"Error al eliminar usuario: {str(e)}")

    return redirect('listar_usuarios')


def logout_view(request):
    # Eliminar el token de la sesión
    if 'firebase_id_token' in request.session:
        del request.session['firebase_id_token']
    request.session.flush()  # Limpiar toda la sesión
    return redirect('login')  # Redirigir al login


def perfil_usuario(request):
    try:
        # Obtener el UID del usuario logueado desde la sesión
        user_uid = request.session.get("firebase_uid")

        # Obtener el documento del usuario desde Firestore
        user_doc = db.collection('usuarios').document(user_uid).get()

        # Convertir el documento a un diccionario
        usuario = user_doc.to_dict()

        # Renderizar el template del perfil
        return render(request, 'usuarios/perfil_usuario.html', {'usuario': usuario})

    except Exception as e:
        print(f"Error al obtener el perfil del usuario: {e}")
        messages.error(request, f"Error al cargar el perfil del usuario: {str(e)}")
        return redirect("dashboard")


def editar_usuario(request, uid):
    try:
        user_doc = db.collection('usuarios').document(uid).get()

        usuario = user_doc.to_dict()

        if request.method == 'POST':
            # Obtener datos del formulario
            email = request.POST.get('email')
            nombre = request.POST.get('first_name')
            apellido = request.POST.get('last_name')
            rol = request.POST.get('rol')
            sucursal = request.POST.get('sucursal')
            estado = request.POST.get('estado')
            password1 = request.POST.get('password1')
            password2 = request.POST.get('password2')

            # Validar contraseñas si se proporcionan
            if password1 or password2:
                if password1 != password2:
                    messages.error(request, "Las contraseñas no coinciden.")
                    return redirect(f'/editar_usuario/{uid}/')

                try:
                    auth.update_user(uid, password=password1)
                except Exception as e:
                    messages.error(request, f"Error al actualizar la contraseña: {str(e)}")
                    return redirect(f'/editar_usuario/{uid}/')

            # Actualizar usuario en Firestore
            db.collection('usuarios').document(uid).update({
                'nombre': nombre,
                'apellido': apellido,
                'email': email,
                'rol': rol,
                'estado': estado,
                'sucursal': sucursal,
            })

            messages.success(request, "Usuario actualizado correctamente.")
            return redirect('listar_usuarios')

        # Pasar datos al template
        sucursales = [{'id': doc.id, **doc.to_dict()} for doc in db.collection('sucursales').stream()]
        estados = ["Activo", "Inactivo"]
        return render(request, 'usuarios/editar_usuarios.html', {
            'usuario': usuario,
            'sucursales': sucursales,
            'estados': estados,
        })

    except Exception as e:
        print(f"Error: {e}")
        messages.error(request, f"Error al editar el usuario: {str(e)}")
        return redirect('listar_usuarios')
