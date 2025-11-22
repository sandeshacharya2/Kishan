"""
Django settings for kisaan_mgmt project.

Updated for Railway deployment with MySQL using DATABASE_URL.
"""

from pathlib import Path
import os
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DJANGO_DEBUG', 'False') == 'True'

# Determine the public Railway domain
RAILWAY_DOMAIN = os.environ.get('RAILWAY_PUBLIC_URL', '').replace('https://', '').replace('http://', '')
ALLOWED_HOSTS = [RAILWAY_DOMAIN, '127.0.0.1', 'localhost'] if RAILWAY_DOMAIN else ['127.0.0.1', 'localhost']

# Application definition
INSTALLED_APPS = [
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accounts',
    'products',
    'chat',
    'payments',
    'django_extensions',
    'channels',
    'tailwind',
    'theme',
    'django_browser_reload',
    'report',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_browser_reload.middleware.BrowserReloadMiddleware',
]

ROOT_URLCONF = 'kisaan_mgmt.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'kisaan_mgmt.wsgi.application'
ASGI_APPLICATION = 'kisaan_mgmt.asgi.application'

# ----------------------------
# Database configuration
# ----------------------------
# Railway provides DATABASE_URL automatically when MySQL add-on is attached
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL'),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# Ensure a database name is present (optional safety check)
if not DATABASES['default'].get('NAME'):
    raise ValueError("Database name not found in DATABASE_URL. Check your Railway MySQL add-on.")

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
USE_I18N = True
USE_L10N = True
USE_TZ = True
TIME_ZONE = 'UTC'

LANGUAGE_CODE = 'ne'
LANGUAGES = [
    ('ne', 'Nepali'),
    ('en', 'English'),
]
LOCALE_PATHS = [BASE_DIR / 'locale']

# Tailwind
TAILWIND_APP_NAME = 'theme'
NPM_BIN_PATH = os.environ.get('NPM_BIN_PATH', 'npm')

# Static & Media files
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Authentication
LOGIN_REDIRECT_URL = '/accounts/redirect/'
LOGOUT_REDIRECT_URL = '/accounts/farmer/login/'
LOGIN_URL = '/accounts/customer/login/'

AUTHENTICATION_BACKENDS = [
    'accounts.auth_backend.EmailBackend',
]

# Django Channels
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    }
}

# Email configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', 'kisaan.helps@gmail.com')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'kisaan.helps@gmail.com')
ADMINS = [("Admin", ADMIN_EMAIL)]

# CSRF & Security
CSRF_TRUSTED_ORIGINS = [f"https://{RAILWAY_DOMAIN}"] if RAILWAY_DOMAIN else []
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Optional: Redirect HTTP to HTTPS in production
if not DEBUG and RAILWAY_DOMAIN:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True