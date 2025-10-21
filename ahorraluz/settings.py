from pathlib import Path
import os
import dj_database_url
import sys
from dotenv import load_dotenv  # Importar para cargar .env
import logging.config

# Cargar variables de entorno del archivo .env
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# Logging to console
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {"format": "%(asctime)s %(levelname)s %(name)s: %(message)s"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
    },
    "root": {"handlers": ["console"], "level": "DEBUG"},
}

LOGIN_REDIRECT_URL = "/home/"

# Secret key y debug desde entorno
SECRET_KEY = os.environ.get('SECRET_KEY')
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

# Validación de SECRET_KEY en producción
if not DEBUG and not SECRET_KEY:
    raise ValueError("❌ SECRET_KEY es requerida en producción")

# Clave por defecto solo para desarrollo
if DEBUG and not SECRET_KEY:
    SECRET_KEY = 'clave-temporal-desarrollo-solo-para-testing'
    print("⚠️  Usando SECRET_KEY temporal para desarrollo")

ALLOWED_HOSTS = []
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# Para desarrollo local, permitir localhost
if DEBUG:
    ALLOWED_HOSTS.extend(['localhost', '127.0.0.1', '0.0.0.0'])

INSTALLED_APPS = [
    'core.apps.CoreConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

AUTHENTICATION_BACKENDS = [
    "core.auth_backend.AuthIdentidadBackend",  # nuestro backend que verifica AuthIdentidad
    "django.contrib.auth.backends.ModelBackend",  # fallback a backend por defecto
]

ROOT_URLCONF = 'ahorraluz.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'ahorraluz.wsgi.application'

# Configuración de base de datos
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL'),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# Verificación de conexión a la base de datos (para desarrollo y producción)
# Solo se ejecuta cuando no son tests y no son comandos de gestión de base de datos
excluded_commands = ['test', 'migrate', 'makemigrations', 'shell', 'dbshell', 'showmigrations']

should_check_db = (
    'runserver' in sys.argv or 
    'gunicorn' in ' '.join(sys.argv) or
    os.environ.get('RENDER') or
    (len(sys.argv) > 1 and sys.argv[1] not in excluded_commands)
)

if should_check_db and 'test' not in sys.argv:
    try:
        from django.db import connections
        conn = connections['default']
        c = conn.cursor()
        c.execute('SELECT 1')
        one = c.fetchone()
        
        # Información detallada de la conexión
        print("🚀 ===========================================")
        print("✅ CONEXIÓN A BASE DE DATOS EXITOSA")
        print("🚀 ===========================================")
        print(f"📊 Base de datos: {DATABASES['default'].get('NAME', 'No definida')}")
        print(f"🌐 Host: {DATABASES['default'].get('HOST', 'No definido')}")
        print(f"👤 Usuario: {DATABASES['default'].get('USER', 'No definido')}")
        print(f"🔧 Puerto: {DATABASES['default'].get('PORT', 'Default (5432)')}")
        print(f"🏷️  Motor: {DATABASES['default'].get('ENGINE', 'No definido')}")
        print(f"🔧 Modo: {'Desarrollo' if DEBUG else 'Producción'}")
        print(f"🌍 Entorno: {'Render' if os.environ.get('RENDER') else 'Local'}")
        print("🚀 ===========================================")
        
        # Información adicional del sistema
        if DEBUG:
            print(f"🔑 DEBUG: {DEBUG}")
            print(f"🔒 SECRET_KEY definida: {'Sí' if SECRET_KEY else 'No'}")
            
    except Exception as e:
        print("❌ ===========================================")
        print("❌ ERROR DE CONEXIÓN A BASE DE DATOS")
        print("❌ ===========================================")
        print(f"💥 Error: {e}")
        print(f"🔧 Modo: {'Desarrollo' if DEBUG else 'Producción'}")
        
        if DEBUG:
            print("💡 Posibles soluciones:")
            print("1. Verifica que DATABASE_URL en .env sea correcta")
            print("2. Revisa que la BD de Render esté activa")
            print("3. Verifica tu conexión a internet")
            print("4. Revisa el firewall si estás en redes restrictivas")
        
        print("❌ ===========================================")
        
        # En producción, no crashear la app, solo loguear el error
        if not DEBUG:
            print("⚠️  La aplicación continuará pero la BD podría no funcionar")

STATIC_URL = '/static/'
if not DEBUG:
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
else:
    # Para desarrollo, buscar static files en apps
    STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static'), os.path.join(BASE_DIR, 'core', 'static')]

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
##Fernet KEY Crypto
FERNET_KEY = os.getenv("FERNET_KEY", None)