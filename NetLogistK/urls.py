# NetLogistK/urls.py

from django.contrib import admin
from django.urls import path
from vehiculos import views as vehiculos_views
from usuarios import views as usuarios_views
from repartos import views as repartos_views
from tracking import views as tracking_views
from .views import dashboard

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', dashboard, name='dashboard'),  # Vista del dashboard
    
    # Rutas para Vehículos
    path('ver_vehiculos/', vehiculos_views.listar_vehiculos, name='ver_vehiculos'),
    path('agregar_vehiculo/', vehiculos_views.crear_vehiculo, name='agregar_vehiculo'),
    
    # Rutas para Usuarios
    path('usuarios/', usuarios_views.listar_usuarios, name='listar_usuarios'),
    path('crear_usuario/', usuarios_views.crear_usuario, name='crear_usuario'),
    
    # Rutas para Repartos
    path('ver_repartos/', repartos_views.listar_repartos, name='listar_repartos'),
    path('agregar_reparto/', repartos_views.crear_reparto, name='crear_reparto'),
    path('editar_reparto/<int:id>/', repartos_views.editar_reparto, name='editar_reparto'),
    path('eliminar_reparto/<int:id>/', repartos_views.eliminar_reparto, name='eliminar_reparto'),

    # Rutas para Tracking
    path('mapa/', tracking_views.mapa_tracking, name='mapa_tracking'),
    path('cronograma/', tracking_views.cronograma, name='cronograma')
]
