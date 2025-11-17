from pathlib import Path
import os
import dj_database_url
import sys
from dotenv import load_dotenv  # Importar para cargar .env
import logging.config

# Cargar variables de entorno del archivo .env
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

TIME_ZONE = "America/Santiago"
USE_TZ = True  # mantenla True para almacenar en UTC y convertir a local

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

LOGIN_REDIRECT_URL = "/profile/" 
LOGOUT_REDIRECT_URL = "/"

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
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",

    # Global exception handler
    "core.middleware.GlobalExceptionMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",

    # Security headers 
    "core.middleware.SecurityHeadersMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


AUTHENTICATION_BACKENDS = [
    "core.auth_backend.AuthIdentidadBackend",  
    "django.contrib.auth.backends.ModelBackend",  
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



# Email (SMTP Gmail)
EMAIL_BACKEND = os.environ.get(
    "EMAIL_BACKEND",
    "django.core.mail.backends.smtp.EmailBackend"  # por defecto SMTP (útil local)
)
EMAIL_HOST = os.environ.get("EMAIL_HOST")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT"))
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "true").lower() == "true"
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER)

SITE_URL = os.environ.get("SITE_URL", "http://localhost:8000")
PASSWORD_RESET_MINUTES = int(os.environ.get("PASSWORD_RESET_MINUTES", "30"))

if EMAIL_BACKEND.startswith("anymail."):
    # API vía Anymail (recomendado para Render)
    INSTALLED_APPS += ["anymail"]
    ANYMAIL = {}
    # SendGrid
    if EMAIL_BACKEND == "anymail.backends.sendgrid.EmailBackend":
        ANYMAIL["SENDGRID_API_KEY"] = os.environ.get("SENDGRID_API_KEY")
else:
    # SMTP (útil en desarrollo local con Gmail App Password)
    EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
    EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
    EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "true").lower() == "true"
    EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
    EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")
    if not DEFAULT_FROM_EMAIL:
        DEFAULT_FROM_EMAIL = EMAIL_HOST_USER


# === Security Headers ===

# Content Security Policy
CSP_DEFAULT_POLICY = (
    "default-src 'self'; "
    # JS: Django, Bootstrap (jsDelivr), CDNs varios, Font Awesome Kit
    "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://kit.fontawesome.com; "
    # CSS: propio, Bootstrap, CDNs, Google Fonts, Font Awesome (kit-free + ka-f)
    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://fonts.googleapis.com https://kit-free.fontawesome.com https://ka-f.fontawesome.com; "
    # Fuentes: propias, Google Fonts, Font Awesome
    "font-src 'self' data: https://fonts.gstatic.com https://cdnjs.cloudflare.com https://ka-f.fontawesome.com; "
    # Imágenes desde tu dominio + cualquier HTTPS + data: (por si usas base64)
    "img-src 'self' data: https:; "
    # Conexiones XHR/Fetch: tu dominio + Font Awesome kit backend
    "connect-src 'self' https://ka-f.fontawesome.com; "
    # No permitir que otros te embeban en iframes
    "frame-ancestors 'self'; "
    # Formularios solo hacia tu dominio
    "form-action 'self'; "
    # Evitar trucos con <base>
    "base-uri 'self';"
)



# Permissions Policy (antes Feature-Policy)
PERMISSIONS_POLICY = (
    "geolocation=(), "
    "camera=(), "
    "microphone=(), "
    "payment=(), "
    "usb=(), "
    "fullscreen=(self), "
    "interest-cohort=()"  # desactiva FLoC/cohortes
)
