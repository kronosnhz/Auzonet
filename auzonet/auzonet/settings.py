"""
Django settings for auzonet project.

Generated by 'django-admin startproject' using Django 1.9.1.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.9/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'f_+dc(p+5!uiuvmf5ym(^uu8bqafbd(m8_)vc_^h_tuage9%oe'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'apps.morelab.deusto.es', 'auzonet-env.mehfcbcfzm.us-west-2.elasticbeanstalk.com']

# Email settings
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = '587'
EMAIL_HOST_USER = 'aitor.brazaola@opendeusto.es'
EMAIL_HOST_PASSWORD = 'CT7V8BkWdJ'
EMAIL_USE_TLS = 'TRUE'

# Application definition
INSTALLED_APPS = [
    'auzonetweb.apps.AuzonetwebConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.sites',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'djangobower',
    'bootstrap3',
    'favicon',
    'storages',
]

MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'auzonet.urls'

SITE_ID = 1

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'auzonetweb/templates/auzonetweb/')],
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

# Favicon
FAVICON_CONFIG = {
    'shortcut icon': [16, 32, 48, 128, 192],
    'touch-icon': [196],
    'icon': [196],
    'apple-touch-icon': [57, 72, 114, 144, 180],
    'apple-touch-icon-precomposed': [57, 72, 76, 114, 120, 144, 152, 180],
}

WSGI_APPLICATION = 'auzonet.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases
if 'RDS_HOSTNAME' in os.environ:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.environ['RDS_DB_NAME'],
            'USER': os.environ['RDS_USERNAME'],
            'PASSWORD': os.environ['RDS_PASSWORD'],
            'HOST': os.environ['RDS_HOSTNAME'],
            'PORT': os.environ['RDS_PORT'],
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        }
    }

# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators
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

LOGIN_URL = 'welcome'

# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/
LANGUAGE_CODE = 'en'
LANGUAGES = (
    ('en', 'English'),
    ('es', 'Spanish'),
)
TIME_ZONE = 'Europe/Madrid'
USE_I18N = True
USE_L10N = True
USE_TZ = True
LOCALE_PATHS = (
    os.path.join(BASE_DIR, '../locale'),
)

if 'RDS_HOSTNAME' in os.environ:
    # Static files (CSS, JavaScript, Images)
    # https://docs.djangoproject.com/en/1.9/howto/static-files/
    # FOR S3
    AWS_S3_CUSTOM_DOMAIN = 's3-us-west-2.amazonaws.com/auzonet-bucket'
    STATICFILES_LOCATION = 'static'
    STATIC_URL = "https://%s/%s/" % (AWS_S3_CUSTOM_DOMAIN, STATICFILES_LOCATION)
    STATICFILES_STORAGE = 'custom_storages.StaticStorage'
    AWS_STORAGE_BUCKET_NAME = 'auzonet-bucket'
    AWS_ACCESS_KEY_ID = 'AKIAJSVJEMMUQQZ5Z3OA'
    AWS_SECRET_ACCESS_KEY = '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'
    AWS_S3_HOST = 's3-us-west-2.amazonaws.com'

    MEDIAFILES_LOCATION = 'media'
    MEDIA_URL = "https://%s/%s/" % (AWS_S3_CUSTOM_DOMAIN, MEDIAFILES_LOCATION)
    DEFAULT_FILE_STORAGE = 'custom_storages.MediaStorage'
    # END S3
else:
    # Media files management (local)
    MEDIA_ROOT = os.path.join(BASE_DIR, 'auzonetweb/media/')
    MEDIA_URL = '/auzonet/auzonetweb/media/'
    STATIC_URL = '/static/'
    # END LOCAL

# FOR SERVER (DEPRECATED NOW ARE IN AWS)
#STATIC_URL = '/auzonet/static/'
#STATIC_ROOT = os.path.join(BASE_DIR, 'collected_static')
#USE_X_FORWARDED_HOST = True
#FORCE_SCRIPT_NAME = '/auzonet'
# END SERVER

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'djangobower.finders.BowerFinder',
)

# Bower package manager
BOWER_COMPONENTS_ROOT = os.path.join(BASE_DIR, 'components')
BOWER_INSTALLED_APPS = (
    'jquery#1.9',
    'jquery-ui',
    'Chart.js',
    'jquery-numeric',
)
