import os
from pathlib import Path

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-9wk9v#!qk$5j(-b3o@n1%ca@%*fiw9#62n@4t8w6()i)7z^0^0'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Allowed Hosts
ALLOWED_HOSTS = ['*']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
     'inventory',
    'widget_tweaks',

]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
     'django.middleware.csrf.CsrfViewMiddleware', 
]

ROOT_URLCONF = 'gestiondestock.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],  # <-- OK (important pour ton base_site.html)
        'APP_DIRS': True,  # <-- OK
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

WSGI_APPLICATION = 'gestiondestock.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JS, images)
STATIC_URL = '/static/'

STATICFILES_DIRS = [BASE_DIR / 'static']  # ✔ pour trouver tes CSS

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Authentication settings
LOGIN_REDIRECT_URL = '/dashboard/'
LOGIN_URL = '/login/'
TWILIO_ACCOUNT_SID = 'TON_ACCOUNT_SID'
TWILIO_AUTH_TOKEN = 'TON_AUTH_TOKEN'
TWILIO_PHONE_NUMBER = '+TON_NUMERO_TWILIO'
AUTH_USER_MODEL = 'inventory.CustomUser' 