# NetLogistK/urls.py
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from apps.vehiculos import views as vehiculos_views
from apps.usuarios import views as usuarios_views
from apps.repartos import views as repartos_views
from apps.tracking import views as tracking_views
from apps.mensajes import views as mensajes_views
from apps.parametros import views as parametros_views
from apps.recursos import views as recursos_views
from apps.dispositivos import views as dispositivos_views
from apps.pedidos import views as pedidos_views
from apps.cronograma import views as cronograma_views
from .views import dashboard as dashboard_views
from apps.bienvenida import views as bienvenida_views
from apps.zonas import views as zonas_views


urlpatterns = [
    path('admin/', admin.site.urls),
    #path('exportar-excel/', views.exportar_repartos_excel, name='exportar_excel'),

    # Rutas para Vehículos
    path('ver_vehiculos/', vehiculos_views.listar_vehiculos, name='ver_vehiculos'),
    path('crear_vehiculo/', vehiculos_views.crear_vehiculo, name='agregar_vehiculo'),
    path('editar_vehiculo/<str:vehiculo_id>/', vehiculos_views.editar_vehiculo, name='editar_vehiculo'),
    path('eliminar_vehiculo/<str:vehiculo_id>/', vehiculos_views.eliminar_vehiculo, name='eliminar_vehiculo'),

    # Rutas para Usuarios
    path('login/', usuarios_views.login_view, name='login'),
    path('logout/', usuarios_views.logout_view, name='logout'),
    path('usuarios/', usuarios_views.listar_usuarios, name='listar_usuarios'),
    path('usuarios/crear/', usuarios_views.crear_usuario, name='crear_usuario'),
    path('usuarios/editar/<str:uid>/', usuarios_views.editar_usuario, name='editar_usuario'),
    path('usuarios/eliminar/<str:uid>/', usuarios_views.eliminar_usuario, name='eliminar_usuario'),
    path('usuarios/perfil/', usuarios_views.perfil_usuario, name='perfil_usuario'),

    # Rutas para Repartos
    path('ver_repartos/', repartos_views.listar_repartos, name='listar_repartos'),
    path('agregar_reparto/', repartos_views.crear_reparto, name='crear_reparto'),
    path('editar_reparto/<str:id>/', repartos_views.editar_reparto, name='editar_reparto'),
    path('eliminar_reparto/<str:reparto_id>/', repartos_views.eliminar_reparto, name='eliminar_reparto'),
    path('repartos_filtrados/', repartos_views.repartos_filtrados, name='repartos_filtrados'),
    path('ver_detalle_reparto/<str:nro_reparto>/', repartos_views.ver_detalle_reparto, name='ver_detalle_reparto'),
    path('obtener_detalles_reparto/<str:nro_reparto>/', cronograma_views.obtener_detalles_reparto, name='obtener_detalles_reparto'),

    # Rutas para Pedidos
    path('listar/', pedidos_views.listar_pedidos, name='listar_pedidos'),
    path('eliminar_pedido/<str:pedido_id>/', pedidos_views.eliminar_pedido, name='eliminar_pedido'),
    path('importar/', pedidos_views.importar_y_previsualizar_pedidos, name='importar_y_previsualizar_pedidos'),
    path('pedidos/detalle/<str:pedido_id>/', pedidos_views.obtener_detalle_pedido, name='detalle_pedido'),
    path('pedidos/actualizar-estado-articulo/<str:pedido_id>/', pedidos_views.actualizar_estado_articulo, name='actualizar_estado_articulo'),
    path('generar_mapa/', pedidos_views.generar_mapa_view, name='generar_mapa'),

    # Rutas para Tracking
    path('mapa/', tracking_views.mapa_tracking, name='mapa_tracking'),

    # Rutas para Cronograma
    path('cronograma/', cronograma_views.cronograma_mensual, name='cronograma_mensual'),
    path('cronograma_semanal/', cronograma_views.cronograma_semanal, name='cronograma_semanal'),
    path('lista_detalle_reparto/<str:nro_reparto>/', cronograma_views.lista_detalle_reparto, name='lista_detalle_reparto'),

    # Rutas para Mensajes
    path('ver_mensajes/', mensajes_views.ver_mensajes, name='ver_mensajes'),
    path('enviar_mensaje/', mensajes_views.enviar_mensaje, name='enviar_mensaje'),
    path('leer_mensaje/<str:mensaje_id>/', mensajes_views.leer_mensaje, name='leer_mensaje'),
    path('responder_mensaje/<str:mensaje_id>/', mensajes_views.responder_mensaje, name='responder_mensaje'),
    path('eliminar_mensaje/<str:mensaje_id>/', mensajes_views.eliminar_mensaje, name='eliminar_mensaje'),

    # Rutas para Sucursales
    path('sucursales/', parametros_views.listar_sucursales, name='listar_sucursales'),
    path('sucursales/crear/', parametros_views.crear_sucursal, name='crear_sucursal'),
    path('sucursales/editar/<str:sucursal_id>/', parametros_views.editar_sucursal, name='editar_sucursal'),
    path('sucursales/eliminar/<str:sucursal_id>/', parametros_views.eliminar_sucursal, name='eliminar_sucursal'),

    # Rutas para Marcas
    path('marcas/', parametros_views.listar_marcas, name='listar_marcas'),
    path('marcas/crear/', parametros_views.crear_marca, name='crear_marca'),
    path('marcas/editar/<str:marca_id>/', parametros_views.editar_marca, name='editar_marca'),
    path('marcas/eliminar/<str:marca_id>/', parametros_views.eliminar_marca, name='eliminar_marca'),

    # Rutas para Modelos
    path('modelos/', parametros_views.listar_modelos, name='listar_modelos'),
    path('modelos/crear/', parametros_views.crear_modelo, name='crear_modelo'),
    path('modelos/editar/<str:modelo_id>/', parametros_views.editar_modelo, name='editar_modelo'),
    path('modelos/eliminar/<str:modelo_id>/', parametros_views.eliminar_modelo, name='eliminar_modelo'),

    # Rutas para Tipos de Service
    path('tipos_service/', parametros_views.listar_tipos_service, name='listar_tipos_service'),
    path('tipos_service/crear/', parametros_views.crear_tipo_service, name='crear_tipo_service'),
    path('tipos_service/editar/<str:tipo_service_id>/', parametros_views.editar_tipo_service, name='editar_tipo_service'),
    path('tipos_service/eliminar/<str:tipo_service_id>/', parametros_views.eliminar_tipo_service, name='eliminar_tipo_service'),

    # Rutas para Recursos
    path('recursos/', recursos_views.listar_recursos, name='listar_recursos'),
    path('recursos/crear/', recursos_views.crear_recurso, name='crear_recurso'),
    path('recursos/editar/<str:recurso_id>/', recursos_views.editar_recurso, name='editar_recurso'),
    path('recursos/eliminar/<str:recurso_id>/', recursos_views.eliminar_recurso, name='eliminar_recurso'),

    # Rutas para Dispositivos
    path('dispositivos/', dispositivos_views.listar_dispositivos, name='listar_dispositivos'),
    path('dispositivos/crear/', dispositivos_views.crear_dispositivo, name='crear_dispositivo'),
    path('dispositivos/editar/<str:dispositivo_id>/', dispositivos_views.editar_dispositivo, name='editar_dispositivo'),
    path('dispositivos/eliminar/<str:dispositivo_id>/', dispositivos_views.eliminar_dispositivo, name='eliminar_dispositivo'),

    # Rutas para Zonas
    path('zonas/', zonas_views.listar_zonas, name='listar_zonas'),
    path('zonas/crear/', zonas_views.crear_zona, name='crear_zona'),
    path('zonas/editar/<str:zona_id>/', zonas_views.editar_zona, name='editar_zona'),
    path('zonas/eliminar/<str:zona_id>/', zonas_views.eliminar_zona, name='eliminar_zona'),

    # Ruta para el dashboard
    path('dashboard/', dashboard_views.dashboard_view, name='dashboard'),

    path('', bienvenida_views.bienvenida_view, name='bienvenida'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
