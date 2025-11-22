"""
Django settings for kisaan_mgmt project.

Updated for Railway deployment with MySQL and static files.
"""

from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'fallback-secret-key')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'

ALLOWED_HOSTS = ['*']  # For production, replace with your Railway URL

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
    'whitenoise.middleware.WhiteNoiseMiddleware',  # <-- added for static files
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',  # For translations
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

# Database configuration for Railway MySQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get("MYSQLDATABASE"),
        'USER': os.environ.get("MYSQLUSER"),
        'PASSWORD': os.environ.get("MYSQLPASSWORD"),
        'HOST': os.environ.get("MYSQLHOST"),
        'PORT': os.environ.get("MYSQLPORT"),
    }
}

# PyMySQL setup (in __init__.py)
# import pymysql
# pymysql.install_as_MySQLdb()

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

LANGUAGE_CODE = 'ne'  # Default Nepali
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
STATICFILES_DIRS = [
    BASE_DIR / "static",
]
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"  # <-- added for production

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Login & Authentication
LOGIN_REDIRECT_URL = '/accounts/redirect/'
LOGOUT_REDIRECT_URL = '/accounts/farmer/login/'
LOGIN_URL = '/accounts/customer/login/'

AUTHENTICATION_BACKENDS = [
    'accounts.auth_backend.EmailBackend',
]

# Django Channels (for WebSocket)
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    }
}

# Email configuration (for sending emails)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', 'kisaan.helps@gmail.com')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')  # Use Railway Secret Variable
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'kisaan.helps@gmail.com')
ADMINS = [
    ("Admin", ADMIN_EMAIL),
]
