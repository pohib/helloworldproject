from pathlib import Path
import os
from django.utils.translation import gettext_lazy as _

LANGUAGES = [
    ('ru', _('Russian')),
]

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = 'django-insecure-mc^q-u5kr)d)!04@r#f%!mxgnkfrzth-+gs6iyfc=v%krevz%('

DEBUG = True

ALLOWED_HOSTS = []

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'tinymce',
    'core',
    'django_recaptcha',
    'django.contrib.sites',
    'users.apps.UsersConfig',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.github',
]

AUTHENTICATION_BACKENDS = [
    'users.backends.TelegramBackend',
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

SITE_ID = 1

LOGIN_URL = 'account_login'
LOGIN_REDIRECT_URL = 'users:profile'
ACCOUNT_LOGOUT_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'  
ACCOUNT_LOGIN_REDIRECT_URL = 'users:profile'
ACCOUNT_LOGIN_METHODS = {'username', 'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'username*', 'password1*', 'password2*']
ACCOUNT_UNIQUE_EMAIL = True
SOCIALACCOUNT_AUTO_SIGNUP = True 
ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'https' if not DEBUG else 'http'

TELEGRAM_BOT_NAME = 'projectsite_bot'
TELEGRAM_BOT_TOKEN = '7635912613:AAEnXeADRXJ3fdiqee5f8OFF6qpIxvBGrlY'
TELEGRAM_LOGIN_REDIRECT_URL = '/profile/'
TELEGRAM_LOGIN_REDIRECT_URL_FAIL = '/login/'
TELEGRAM_LOGIN_SESSION_EXPIRATION = 86400

RECAPTCHA_PUBLIC_KEY = '6Ld2d2srAAAAAEV_IF2zpRsZWIQn7FlMi3vyfU_-'
RECAPTCHA_PRIVATE_KEY = '6Ld2d2srAAAAAJjD-W7v4a7aa0ZeMn5rUvZ2aeRv'


MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'csp.middleware.CSPMiddleware',
]

TINYMCE_DEFAULT_CONFIG = {
    'height': 400,
    'width': '100%',
    'cleanup_on_startup': True,
    'custom_undo_redo_levels': 20,
    'selector': 'textarea',
    'theme': 'silver',
    'plugins': '''
        textcolor save link image media preview codesample contextmenu
        table code lists fullscreen insertdatetime nonbreaking
        contextmenu directionality searchreplace wordcount visualblocks
        visualchars code fullscreen autolink lists charmap print hr
        anchor pagebreak
    ''',
    'toolbar1': '''
        fullscreen preview bold italic underline | fontselect,
        fontsizeselect | forecolor backcolor | alignleft alignright |
        aligncenter alignjustify | indent outdent | bullist numlist table |
        | link image media | codesample |
    ''',
    'toolbar2': '''
        visualblocks visualchars |
        charmap hr pagebreak nonbreaking anchor | code |
    ''',
    'contextmenu': 'formats | link image',
    'menubar': True,
    'statusbar': True,
    'language': 'ru',
    'skin': 'oxide-dark',
    'content_css': 'dark',
}

TINYMCE_FILEBROWSER = True

CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = (
    "'self'",
    "https://telegram.org",
    "https://*.telegram.org",
)
CSP_IMG_SRC = ("'self'", "data:", "https://*.telegram.org")
CSP_CONNECT_SRC = ("'self'", "https://telegram.org")
CSP_FRAME_SRC = ("'self'", "https://telegram.org")
CSP_FRAME_ANCESTORS = ("'self'", "https://*.telegram.org")


ROOT_URLCONF = 'helloworldproject.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
            ],
        },
    },
]

WSGI_APPLICATION = 'helloworldproject.wsgi.application'

LECTURES_HTML_ROOT = os.path.join(MEDIA_ROOT, 'courses_html')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

"""
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'mysite',
        'USER': 'admin',
        'PASSWORD': '123',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
} 
"""

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



LANGUAGE_CODE = 'ru-RU'

TIME_ZONE = 'Europe/Moscow'

USE_I18N = True

USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

USE_L10N = False
DECIMAL_SEPARATOR = '.'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': os.path.join(BASE_DIR, 'cache'),
        'TIMEOUT': 86400,
    }
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
}

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'vedenyov10@gmail.com'
EMAIL_HOST_PASSWORD = 'wsiw piwu szpa vbnx'
DEFAULT_FROM_EMAIL = 'vedenyov10@gmail.com'

ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 3
ACCOUNT_EMAIL_SUBJECT_PREFIX = "127.0.0.1"
ACCOUNT_DEFAULT_HTTP_PROTOCOL = "http"


ACCOUNT_EMAIL_CONFIRMATION_TEMPLATE = "users/account/email/email_confirmation_message.html"
ACCOUNT_EMAIL_CONFIRMATION_SUBJECT = "users/account/email/email_confirmation_subject.txt"

SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin-allow-popups"

ADMIN_SITE_HEADER = "Панель проверки заданий"