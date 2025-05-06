from pathlib import Path
import firebase_admin
from firebase_admin import credentials
import os
from dotenv import load_dotenv
import sys

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Agregar el directorio 'apps' al PYTHONPATH
sys.path.insert(0, str(BASE_DIR / 'apps'))

# Inicialización de Firebase
FIREBASE_CREDENTIALS_PATH = BASE_DIR / 'secrets/firebase.json'

try:
    if not firebase_admin._apps:
        cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
        firebase_admin.initialize_app(cred)
        #print("Settings.py - Firebase inicializado correctamente.")
    else:
        print("Firebase ya estaba inicializado.")
except Exception as e:
    print(f"Error inicializando Firebase: {e}")

# Seguridad
SECRET_KEY = 'django-insecure-)_(9&m_jk-2dqth1177o5($27cg56h8gg=++zn@3!iyvco=nv4'
DEBUG = True
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

# Aplicaciones instaladas
INSTALLED_APPS = [
    # Core de Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Aplicaciones del proyecto
    'repartos',
    'usuarios',
    'vehiculos',
    'tracking',
    'mensajes',
    'dispositivos',
    'parametros',
    'recursos',
    'zonas',
    'pedidos',
    'cronograma',
    'bienvenida',
]

# Middlewares
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',  
    #'NetLogistK.middleware.rate_limit.RateLimitMiddleware',  # Comentado temporalmente
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Activa sesiones si las necesitas para Firebase
    'NetLogistK.middleware.auth.FirebaseAuthenticationMiddleware',
]

# Configuración de mensajes
from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.DEBUG: 'debug',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}

# Archivos multimedia
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
STATIC_ROOT = BASE_DIR / 'staticfiles'


# Configuración de plantillas
ROOT_URLCONF = 'NetLogistK.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # Asegúrate de que este context processor no dependa de request.user
                'usuarios.context_processors.user_profile',
            ],
        },
    },
]

WSGI_APPLICATION = 'NetLogistK.wsgi.application'

# Base de datos
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',  # SQLite3 como base mínima
        'NAME': BASE_DIR / 'db.sqlite3',        # Ruta al archivo de base de datos
    }
}

# Configuración de validadores de contraseñas
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Configuración internacional
LANGUAGE_CODE = 'es-ar'
TIME_ZONE = 'America/Argentina/Buenos_Aires'
USE_I18N = True
USE_TZ = True

# Archivos estáticos
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'NetLogistK' / 'static',
    BASE_DIR / 'static',
]

# Clave primaria por defecto
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Configuración de sesiones (puedes usar Firebase en lugar de Django si no necesitas sesiones locales)
#SESSION_ENGINE = 'django.contrib.sessions.backends.db'  # O usa 'django.contrib.sessions.backends.db'

# Iconos de los Roles de los Usuarios
ROLE_ICONS = {
    "Administrador": "fas fa-user-cog",
    "Gerente": "fas fa-user-tie",
    "Logística": "fas fa-truck-moving",
    "Ventas": "fas fa-user",
}

load_dotenv()

# Configuración de Redis
REDIS_CONFIG = {
    'host': os.getenv('REDIS_HOST', 'localhost'),
    'port': int(os.getenv('REDIS_PORT', 6379)),
    'db': int(os.getenv('REDIS_DB', 0))
}

# Configuración de Firebase
FIREBASE_CONFIG = {
    'apiKey': 'AIzaSyCkj3ZWSU_UdlDoyfonJTexHkcF7JLV4m4',  # Tu API Key
    'authDomain': 'net-logistk-isla.firebaseapp.com',
    'projectId': 'net-logistk-isla',
    'storageBucket': 'net-logistk-isla.appspot.com',
    'messagingSenderId': '103980156985793532248',
    'appId': '1:103980156985793532248:web:XXXXXXXXXXXXX'  # Tu App ID
}

# Configuración de caché
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}
