# NET-LogistK ISLA

## Descripción del Proyecto

Net-LogistK es una aplicación web integral para la gestión de logística, distribución y seguimiento de repartos. Esta plataforma permite gestionar vehículos, usuarios, crear y seguir repartos, con opciones de seguimiento en tiempo real, control de recursos y generación de reportes.

## Características Principales

1. **Gestión de Vehículos**: Crear, listar y actualizar datos de vehículos.
2. **Gestión de Repartos**: Organizar y controlar repartos, incluyendo datos del chofer, acompañante, cantidad de facturas y kilos transportados.
3. **Gestión de Usuarios**: Crear usuarios con diferentes tipos de permisos asignados por grupos.
4. **Autenticación de Usuarios**: Uso de Firebase Authentication para la autenticación segura.
5. **Dashboard Interactivo**: Tablero para visualizar el estado de los repartos y otros KPIs importantes.
6. **Mapas y Seguimiento**: Implementación de mapas utilizando Leaflet.js para visualizar rutas de reparto.
7. **Notificaciones y Reportes**: Generación de informes y opciones para enviar notificaciones por correo electrónico.

## Tecnologías Utilizadas

- **Backend**: Django (Python)
- **Frontend**: ReactJS, Bootstrap (SB Admin 2 Template)
- **Mapas**: Leaflet.js para integración con OpenStreetMap

## Instalación y Configuración

1. **Clonar el Repositorio**: `git clone https://github.com/mellioscar/NET-LogistK-ISLA.git`
2. **Instalar Dependencias**: Ejecutar `pip install -r requirements.txt` para instalar las dependencias de Python.
3. **Migrar la Base de Datos**: `python manage.py migrate`
4. **Iniciar el Servidor**: `python manage.py runserver`
5. **Configuración de Variables**: Actualizar las variables de entorno necesarias en `env`

## Uso de la Aplicación

1. **Acceso**: Iniciar sesión en la plataforma.
2. **Crear Vehículos**: Desde la sección de "Vehículos", añadir un nuevo vehículo llenando los datos requeridos.
3. **Asignar Usuarios a Grupos**: Al crear un usuario, se puede definir su grupo, lo que determinará sus permisos.
4. **Generar Reportes**: Acceder a la opción de reportes para generar y descargar informes.

## Contacto

- **Contacto**: Oscar Lizzi
- **Sitio Web**: [www.NET-LogistK.com]
