from pathlib import Path
import os
import dj_database_url

# -------------------------------
# RUTAS BÁSICAS DEL PROYECTO
# -------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent


# -------------------------------
# SEGURIDAD
# -------------------------------
SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "django-insecure-usa-una-clave-muy-larga-en-produccion",
)

DEBUG = os.getenv("DEBUG", "True") == "True"

ALLOWED_HOSTS = os.getenv(
    "ALLOWED_HOSTS",
    "127.0.0.1,localhost,.onrender.com"
).split(",")

_raw_csrf = os.getenv("CSRF_TRUSTED_ORIGINS", "")
if _raw_csrf:
    CSRF_TRUSTED_ORIGINS = [
        origin.strip() for origin in _raw_csrf.split(",") if origin.strip()
    ]
else:
    CSRF_TRUSTED_ORIGINS = []


# -------------------------------
# APLICACIONES INSTALADAS
# -------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # 👇 ESTA ES LA ÚNICA LÍNEA QUE CAMBIAMOS
    'tickets.apps.TicketsConfig',  # permite crear admintechfix automáticamente
]


# -------------------------------
# MIDDLEWARE
# -------------------------------
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


# -------------------------------
# URLS Y TEMPLATES
# -------------------------------
ROOT_URLCONF = 'sistema_tickets.urls'

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

WSGI_APPLICATION = 'sistema_tickets.wsgi.application'


# -------------------------------
# BASE DE DATOS
# -------------------------------
db_url = os.getenv("DATABASE_URL")

if db_url:
    DATABASES = {
        "default": dj_database_url.config(
            default=db_url,
            conn_max_age=600,
            ssl_require=False,
        )
    }
else:
    DATABASES = {
        "default": {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# -------------------------------
# VALIDADORES DE CONTRASEÑA
# -------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# -------------------------------
# INTERNACIONALIZACIÓN
# -------------------------------
LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True


# -------------------------------
# ARCHIVOS ESTÁTICOS
# -------------------------------
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# -------------------------------
# CONFIG GENERAL
# -------------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_REDIRECT_URL = 'dashboard'
