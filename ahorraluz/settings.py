from pathlib import Path
import os
import dj_database_url
import sys
from dotenv import load_dotenv  # Importar para cargar .env

# Cargar variables de entorno del archivo .env
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# Logging to console
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {'class': 'logging.StreamHandler', 'stream': sys.stdout},
    },
    'root': {'handlers': ['console'], 'level': 'DEBUG'},
}

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

# Verificación de conexión a la base de datos
if 'test' not in sys.argv:
    try:
        from django.db import connections
        conn = connections['default']
        c = conn.cursor()
        c.execute('SELECT 1')
        print("✅ Conexión a la base de datos PostgreSQL exitosa!")
        print(f"📊 Base de datos: {DATABASES['default']['NAME']}")
        print(f"🌐 Host: {DATABASES['default']['HOST']}")
        print(f"🔧 Modo: {'Desarrollo' if DEBUG else 'Producción'}")
    except Exception as e:
        print(f"❌ Error conectando a la base de datos: {e}")
        if DEBUG:
            print("💡 Asegúrate de que tu .env tenga la DATABASE_URL correcta")

STATIC_URL = '/static/'
if not DEBUG:
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
else:
    # Para desarrollo, buscar static files en apps
    STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

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