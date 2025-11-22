"""
Django settings for kisaan_mgmt project.

Updated for Railway deployment with MySQL and production readiness.
"""

from pathlib import Path
import os
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'fallback-secret-key')

# DEBUG
DEBUG = os.environ.get('DJANGO_DEBUG', 'False') == 'True'

# ALLOWED HOSTS
RAILWAY_URL = os.environ.get('RAILWAY_STATIC_URL')  # optional
ALLOWED_HOSTS = [RAILWAY_URL, 'kishan-production.up.railway.app', 'localhost', '127.0.0.1']

# CSRF Trusted Origins (for Railway HTTPS)
CSRF_TRUSTED_ORIGINS = [
    f"https://{host}" for host in ALLOWED_HOSTS if host not in ['localhost', '127.0.0.1']
]

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

# Database configuration using Railway MySQL URL
DATABASES = {
    'default': dj_database_url.parse(os.environ.get('MYSQL_URL'), conn_max_age=600)
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
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
LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# Tailwind
TAILWIND_APP_NAME = 'theme'
NPM_BIN_PATH = 'npm.cmd'

# Static files
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Serve media files in production (optional, for development only)
if DEBUG:
    from django.conf.urls.static import static
    urlpatterns = []  # make sure this is included in urls.py
    urlpatterns += static(STATIC_URL, document_root=STATIC_ROOT)
    urlpatterns += static(MEDIA_URL, document_root=MEDIA_ROOT)

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Login & Authentication
LOGIN_REDIRECT_URL = '/accounts/redirect/'
LOGOUT_REDIRECT_URL = '/accounts/farmer/login/'
LOGIN_URL = '/accounts/customer/login/'
AUTHENTICATION_BACKENDS = ['accounts.auth_backend.EmailBackend']

# Django Channels
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    }
}

# Email configuration (Gmail SMTP)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', 'kisaan.helps@gmail.com')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')  # Railway secret variable
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'kisaan.helps@gmail.com')
ADMINS = [("Admin", ADMIN_EMAIL)]
