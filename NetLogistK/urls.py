# urls.py
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from vehiculos import views as vehiculos_views
from usuarios import views as usuarios_views
from repartos import views as repartos_views
from tracking import views as tracking_views
from .views import dashboard
from django.urls import path
from . import views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('exportar-reporte-pdf/', views.exportar_reporte_pdf, name='exportar_reporte_pdf'),

    # Redirigir a login por defecto
    path('', usuarios_views.login_view, name='login'),  # Vista de login como página inicial

    # Rutas para Vehículos
    path('ver_vehiculos/', vehiculos_views.listar_vehiculos, name='ver_vehiculos'),
    path('agregar_vehiculo/', vehiculos_views.crear_vehiculo, name='agregar_vehiculo'),
    path('eliminar_vehiculo/<int:id>/', vehiculos_views.eliminar_vehiculo, name='eliminar_vehiculo'),
    path('editar_vehiculo/<int:vehiculo_id>/', vehiculos_views.editar_vehiculo, name='editar_vehiculo'),

    # Rutas para Usuarios
    path('usuarios/', usuarios_views.listar_usuarios, name='listar_usuarios'),
    path('crear_usuario/', usuarios_views.crear_usuario, name='crear_usuario'),
    path('', usuarios_views.login_view, name='login'),
    path('register/', usuarios_views.register_view, name='register'),
    path('logout/', usuarios_views.logout_view, name='logout'),
    path('profile/', usuarios_views.logged_in_user_profile, name='profile_logged_in'),  # Para el perfil del usuario logueado
    path('profile/<int:user_id>/', usuarios_views.profile, name='profile'),  # Para el perfil de cualquier otro usuario
    path('eliminar_usuario/<int:user_id>/', usuarios_views.eliminar_usuario, name='eliminar_usuario'),

    # Rutas para Repartos
    path('ver_repartos/', repartos_views.listar_repartos, name='listar_repartos'),
    path('agregar_reparto/', repartos_views.crear_reparto, name='crear_reparto'),
    path('editar_reparto/<int:id>/', repartos_views.editar_reparto, name='editar_reparto'),
    path('eliminar_reparto/<int:reparto_id>/', repartos_views.eliminar_reparto, name='eliminar_reparto'),

    # Rutas para Tracking
    path('mapa/', tracking_views.mapa_tracking, name='mapa_tracking'),
    path('cronograma/', tracking_views.cronograma, name='cronograma'),

    # Ruta para el dashboard protegido
    path('dashboard/', login_required(dashboard), name='dashboard'),  # Proteger el acceso al dashboard
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)