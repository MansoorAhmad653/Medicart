from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-medicart-secret-key-change-in-production-2024')

DEBUG = os.getenv('DEBUG', 'True') == 'True'

# Parse ALLOWED_HOSTS from environment, strip whitespace
ALLOWED_HOSTS = [host.strip() for host in os.getenv('ALLOWED_HOSTS', '*').split(',')]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party apps
    'corsheaders',
    
    # Local apps
    'users',
    'shop',
    'orders',
    'prescriptions',
    'feedback',
    'dashboard',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Serve static files in production
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'medicart.urls'

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
                'shop.context_processors.cart_count',
            ],
        },
    },
]

WSGI_APPLICATION = 'medicart.wsgi.application'

# Database Configuration - PostgreSQL/Supabase Only
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'postgres'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'OPTIONS': {
            'sslmode': 'require',
            'connect_timeout': 10,
            'options': '-c default_transaction_isolation=read_committed'
        },
        'CONN_MAX_AGE': 600,  # Connection pooling - keep connections alive for 10 minutes
        'ATOMIC_REQUESTS': False,  # Disable atomic requests for better concurrency
    }
}

# Caching Configuration (in-memory cache for development, local memory for sessions)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'medicart-cache',
        'TIMEOUT': 300,  # Cache timeout: 5 minutes
        'OPTIONS': {
            'MAX_ENTRIES': 10000
        }
    }
}

# Session configuration - database-backed to persist across restarts/reloads
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

AUTH_USER_MODEL = 'users.CustomUser'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Karachi'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_REDIRECT_URL = '/shop/'
LOGOUT_REDIRECT_URL = '/users/login/'
LOGIN_URL = '/users/login/'

MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

# CORS Configuration (for API access from different origins)
CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', 'http://localhost:3000,http://localhost:8000').split(',')

# WhiteNoise Configuration (for serving static files in production)
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Security Settings for Production
# NOTE: Railway already handles SSL at proxy level
if not DEBUG:
    # Trust Railway's X-Forwarded-Proto header for HTTPS detection
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_SECURITY_POLICY = {
        'default-src': ("'self'",),
        'script-src': ("'self'", "'unsafe-inline'", 'cdn.jsdelivr.net'),
        'style-src': ("'self'", "'unsafe-inline'", 'cdn.jsdelivr.net'),
        'img-src': ("'self'", 'data:', 'https:'),
    }

# CSRF Trusted Origins - Allow Railway domains
CSRF_TRUSTED_ORIGINS = [
    'https://medicart.up.railway.app',
    'https://*.up.railway.app',
]

# Email Configuration
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp-relay.brevo.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@medicart.com')

