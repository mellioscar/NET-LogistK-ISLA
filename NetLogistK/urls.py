# NetLogistK/urls.py

from django.contrib import admin
from django.urls import path
from vehiculos import views as vehiculos_views
from usuarios import views as usuarios_views
from repartos import views as repartos_views
from .views import dashboard

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', dashboard, name='dashboard'),  # Vista del dashboard
    
    # Rutas para Vehículos
    path('ver_vehiculos/', vehiculos_views.ver_vehiculos, name='ver_vehiculos'),
    path('agregar_vehiculo/', vehiculos_views.crear_vehiculo, name='agregar_vehiculo'),
    
    # Rutas para Usuarios
    path('usuarios/', usuarios_views.ver_usuarios, name='listar_usuarios'),
    path('crear_usuario/', usuarios_views.crear_usuario, name='crear_usuario'),
    
    # Rutas para Repartos
    path('ver_repartos/', repartos_views.listar_repartos, name='listar_repartos'),
    path('agregar_reparto/', repartos_views.crear_reparto, name='crear_reparto'),
]
