"""
URL configuration for NetLogistK project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from vehiculos import views as vehiculos_views
from usuarios import views as usuarios_views

def home(request):
    return render(request, 'sb_admin2/index.html')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('ver_vehiculos/', vehiculos_views.ver_vehiculos, name='ver_vehiculos'),
    path('agregar_vehiculo/', vehiculos_views.crear_vehiculo, name='agregar_vehiculo'),
    path('usuarios/', usuarios_views.ver_usuarios, name='listar_usuarios'),
    path('crear_usuario/', usuarios_views.crear_usuario, name='crear_usuario'),

]
