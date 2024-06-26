"""
Django settings for _ project.

Generated by 'django-admin startproject' using Django 3.2.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""
import os

from pathlib import Path

from dotenv import load_dotenv

from .logging_filters import color_log

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Custum setting
# Load the env to the environment variables from _/env/.env
load_dotenv(os.path.join(BASE_DIR, '_/env/.env'))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = bool(os.getenv('DEBUG', False))

APPEND_SLASH = False

#modify
#ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', 'localhost').split(',')
ALLOWED_HOSTS = ['*']
# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_apscheduler',  # scheduler
    'sslserver',  # python manager.py runsslserver
    'devicetalk',
    'api',
    'xtalk_account',
    'file_handle',
    'my_admin',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = '_.urls'

TEMPLATES = [  # TODO: delete
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates')
        ],
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

WSGI_APPLICATION = '_.wsgi.application'

# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases
DATABASES = {  # TODO: support sqlite & mysql
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'datas/db/db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators
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

# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/
LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Taipei'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# please keep the host name same with DEFAULT_SITE_NAME
WEB_SERVER_PREFIX = os.getenv('WEB_SERVER_PREFIX', '/')

# ref: https://pypi.org/project/django-apscheduler/
# Format string for displaying run time timestamps in the Django admin site. The default
# just adds seconds to the standard Django format, which is useful for displaying the
# timestamps for jobs that are scheduled to run on intervals of less than one minute.

# See https://docs.djangoproject.com/en/dev/ref/settings/#datetime-format for format string
# syntax details.
APSCHEDULER_DATETIME_FORMAT = 'N j, Y, f:s a'

# Maximum run time allowed for jobs that are triggered manually via the Django admin site,
# which prevents admin site HTTP requests from timing out.

# Longer running jobs should probably be handed over to a background task processing library
# that supports multiple background worker processes instead (e.g. Dramatiq, Celery,
# Django-RQ, etc. See: https://djangopackages.org/grids/g/workers-queues-tasks/ for popular
# options).
APSCHEDULER_RUN_NOW_TIMEOUT = 25  # Seconds

FILE_UPLOAD_DIR = 'datas/upload/'
RESULT_DIR = os.path.join(FILE_UPLOAD_DIR, 'result/')

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/
STATIC_URL = '/static/'
if WEB_SERVER_PREFIX and WEB_SERVER_PREFIX != '/':
    STATIC_URL = WEB_SERVER_PREFIX + STATIC_URL
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
    os.path.join(BASE_DIR, FILE_UPLOAD_DIR),
]

LOG_DIR = 'datas/log'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname_color_sequence)s%(levelname)s%(reset_color_sequence)s '
                      '%(name)s [%(asctime)s] => %(msg_color_sequence)s%(message)s'
                      '%(reset_color_sequence)s',
            'style': '%',
        },
        'file': {
            'format': '%(levelname)s %(name)s [%(asctime)s] => %(message)s',
            'style': '%',
        }
    },
    'filters': {
        'color_log': {
            '()': 'django.utils.log.CallbackFilter',
            'callback': color_log,
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',
            'formatter': 'verbose',
            'filters': [
                'color_log',
            ],
        },
        'log_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'access.log'),
            'maxBytes': 10 * 1024 * 1024,
            'backupCount': 3,
            'encoding': 'UTF-8',
            'formatter': 'file',
        },
        'error_log_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'error.log'),
            'maxBytes': 10 * 1024 * 1024,
            'backupCount': 3,
            'encoding': 'UTF-8',
            'formatter': 'file',
            'level': 'WARNING',
        },
    },
    'loggers': {
        '': {  # Root logger
            'handlers': [
                'console',
                'log_file',
                'error_log_file',
            ],
            'level': 'INFO',
        },
        'django': {
            'handlers': [
                'console',
                'log_file',
                'error_log_file',
            ],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# https setting
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Security related configurations
# Make sure csrf cookie is sent only with an HTTPS connection
CSRF_COOKIE_SECURE = bool(os.getenv('CSRF_COOKIE_SECURE', False))

# Session related configurations
# Make sure session cookie is sent only with an HTTPS connection
SESSION_COOKIE_SECURE = bool(os.getenv('SESSION_COOKIE_SECURE', False))
SESSION_COOKIE_NAME = 'devicetalk_session'
SESSION_COOKIE_PATH = os.path.join('/' + WEB_SERVER_PREFIX)
SECURE_SSL_REDIRECT = bool(os.getenv('SECURE_SSL_REDIRECT', False))

# XTALK setting
AUTH_USER_MODEL = 'xtalk_account.User'
XTALK_REFRESHTOKEN_MODEL = 'xtalk_account.RefreshToken'
XTALK_ACCESSTOKEN_MODEL = 'xtalk_account.AccessToken'

XTALK_OAUTH2_REDIRECT_URI = os.getenv('XTALK_OAUTH2_REDIRECT_URI')
XTALK_OAUTH2_REVOCATION_ENDPOINT = os.getenv('XTALK_OAUTH2_REVOCATION_ENDPOINT')
XTALK_OAUTH2_TOKEN_ENDPOINT = os.getenv('XTALK_OAUTH2_TOKEN_ENDPOINT')
XTALK_OIDC_DISCOVERY_ENDPOINT = os.getenv('XTALK_OIDC_DISCOVERY_ENDPOINT')

XTALK_OAUTH2_CLIENT_ID = os.getenv('XTALK_OAUTH2_CLIENT_ID')
XTALK_OAUTH2_CLIENT_SECRET = os.getenv('XTALK_OAUTH2_CLIENT_SECRET')

# AutoGen setting
AUTOGEN_CCMAPI_URL = os.getenv('AUTOGEN_CCMAPI_URL')

# DeviceTalk setting
DA_SERVER_URL_DEFAULT = os.getenv('IOTTALK_EC_URL')
DA_PUSH_INTERVAL_DEFAULT = int(os.getenv('DA_PUSH_INTERVAL', '10'))

# These languages will be automatically create when the db init.
DEFAULT_LANGUAGE_LIST = os.getenv('DEFAULT_LANGUAGE_LIST', 'Python').split(',')

# DeviceTalk language's Basic-file setting
# A valid BASICFILE_CONFIG_FILENAME file should include these sessions.
# See document for more detail.
BASICFILE_CONF_FILENAME = 'config.ini'
# BASICFILE_CONF = (section_name, properties key name)
BASICFILE_CONF_TEMPLATE_LIST = ('templates', 'sa')
BASICFILE_CONF_DEVICE_LIB_PATH_LIST = ('templates', 'safuncs')
BASICFILE_CONF_IDF_TEMPLATE = ('new-function', 'IDF')
BASICFILE_CONF_ODF_TEMPLATE = ('new-function', 'ODF')
BASICFILE_CONF_MANUAL = ('manual', 'url')
BASICFILE_CONF_LIB_ROOT = ('lib', 'root')
BASICFILE_CONF_LIB_EXAMPLE_DIR = ('lib', 'example-dir')
BASICFILE_CONF_SESSIONS = [
    BASICFILE_CONF_TEMPLATE_LIST,
    BASICFILE_CONF_DEVICE_LIB_PATH_LIST,
    BASICFILE_CONF_IDF_TEMPLATE,
    BASICFILE_CONF_ODF_TEMPLATE,
    BASICFILE_CONF_MANUAL,
    BASICFILE_CONF_LIB_ROOT,
    BASICFILE_CONF_LIB_EXAMPLE_DIR
]

# DeviceTalk Library fields setting
# All the name in LIB_FUNC_FIELDS will create a same-named TextField in
# api.models.LibraryFunction.
# In the example file of a uploaded library, only these fields will be stored,
# other fields will be ignored.
# ## Important!!
# Once LIB_FUNC_FIELDS is changed, need to run `./manager.py makemigrations`
# again to update api.models.LibraryFunction.
# See document for more detail.
LIB_FUNC_VAR_SETUP_FIELD = 'var_define'
LIB_FUNC_FIELDS = [
    LIB_FUNC_VAR_SETUP_FIELD,
    'import_string',
    'member_var_define',
    'init_content',
    'runs_content'
]


# The file name and the session name of the global variable of a uploaded library.
LIB_GVS_FILENAME = 'gvs'
LIB_GVS_SECTION_NAME = 'gvs'
LIB_GVSRO_SECTION_NAME = 'gvsro'

LIB_GVS_SECTION = [
    LIB_GVS_SECTION_NAME,
    LIB_GVSRO_SECTION_NAME
]
