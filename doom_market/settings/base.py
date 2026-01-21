import os
from pathlib import Path

from celery.schedules import crontab

# Email distribution service
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
RESEND_API_URL = os.getenv("RESEND_API_URL")
FROM_EMAIL = os.getenv("FROM_EMAIL")

if not RESEND_API_KEY:
    raise ImproperlyConfigured('RESEND_API_KEY not found in environment variables')

# Payment service
MOLLIE_API_KEY = os.getenv("MOLLIE_API_KEY")
MOLLIE_BASE_URL = os.getenv("MOLLIE_BASE_URL")
NGROK_DOMAIN = os.getenv("NGROK_DOMAIN")  # webhook acceptance within dev stage

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")
BASE_DOMAIN = os.getenv("DJANGO_BASE_DOMAIN").strip() or None
DEBUG = os.getenv("DJANGO_DEBUG") == "1"

AUTH_USER_MODEL = 'accounts.UserProfile'

ALLOWED_HOSTS = []
INTERNAL_IPS = []

# Media
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Staticfiles
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'core:product_list'
LOGOUT_REDIRECT_URL = 'core:product_list'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,  # Enable all standard loggers e.g Django/SQL errors etc.
    'formatters': {
        'standard': {
            'format': '{asctime} {levelname} - {message}',
            'style': '{',
        },
        'verbose': {
            'format': '{levelname} {asctime} {module}:{lineno} - {message}',
            'style': '{',
        },
        # colorlog package
        'colorful': {
            '()': 'colorlog.ColoredFormatter',
            "format": "%(log_color)s%(levelname)-8s%(reset)s %(blue)s%(message)s",
            "log_colors": {
                "DEBUG":    "white",
                "INFO":     "green",
                "WARNING":  "yellow",
                "ERROR":    "red",
                "CRITICAL": "bold_red",
            },
        },
    },
    'handlers': {
        'console': {
            # 'class': 'logging.StreamHandler',
            # 'formatter': 'verbose',
            'class': 'colorlog.StreamHandler',
            'formatter': 'colorful',

            'level': 'DEBUG',
        },
        'docker': {
            # makes logs more readable, command: "docker logs {container}"
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',
            'formatter': 'standard',
        },
        'core_app_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs/core_app.log',
            'maxBytes': 1024 * 1024 * 5,
            'backupCount': 5,
            'formatter': 'verbose',
            'level': 'INFO',
        },
        'accounts_app_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs/accounts_app.log',
            'maxBytes': 1024 * 1024 * 5,
            'backupCount': 5,
            'formatter': 'verbose',
            'level': 'INFO',
        },
        'email_delivery_tasks': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs/email_delivery_tasks.log',
            'maxBytes': 1024 * 1024 * 5,
            'backupCount': 5,
            'formatter': 'verbose',
            'level': 'INFO',
        },
        'order_cleanup_tasks': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs/order_cleanup_tasks.log',
            'maxBytes': 1024 * 1024 * 5,
            'backupCount': 5,
            'formatter': 'verbose',
            'level': 'INFO',
        },
        'payments_app_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs/payments_app.log',
            'maxBytes': 1024 * 1024 * 5,
            'backupCount': 5,
            'formatter': 'verbose',
            'level': 'INFO',
        },
        'errors_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs/generic_errors.log',
            'maxBytes': 1024*1024*5,
            'backupCount': 10,
            'formatter': 'verbose',
            'level': 'ERROR',
        },

    },
    'root': {
        'handlers': ['console', 'errors_file'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'errors_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'core': {
            'handlers': ['console', 'core_app_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'core.tasks': {
            'handlers': ['console', 'order_cleanup_tasks'],
            'level': 'INFO',
            'propagate': False,
        },
        'accounts': {
            'handlers': ['console', 'accounts_app_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'shared.tasks': {
            'handlers': ['console', 'email_delivery_tasks'],
            'level': 'INFO',
            'propagate': False,
        },
        'shared.services.email_sender': {
            'handlers': ['console', 'email_delivery_tasks'],
            'level': 'INFO',
            'propagate': False,
        },
        'payments': {
            'handlers': ['console', 'payments_app_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]
INSTALLED_APPS += [
    'core.apps.CoreConfig',
    'accounts.apps.AccountsConfig',
    'payments.apps.PaymentsConfig',
    'shared.apps.SharedConfig',
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
MIDDLEWARE += ['accounts.middleware.email_verification_middleware.EmailVerificationMiddleware']

ROOT_URLCONF = 'doom_market.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'core' / 'templates'],
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

WSGI_APPLICATION = 'doom_market.wsgi.application'


# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB'),
        'USER': os.getenv('POSTGRES_USER'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD'),
        'HOST': os.getenv('POSTGRES_HOST', 'localhost'),
        'PORT': os.getenv('POSTGRES_PORT', '5432'),
    }
}

REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/1')

CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', REDIS_URL)

CELERY_BEAT_SCHEDULE = {
    'cleanup_expired_pending_orders_every_hour': {
        'task': 'core.tasks.cleanup_expired_pending_orders',
        'schedule': crontab(minute=0, hour='*'),
    },
    'cleanup_expired_session_orders_every_hour': {
        'task': 'core.tasks.cleanup_expired_session_orders',
        'schedule': crontab(minute=0, hour='*'),
    }
}


SESSION_COOKIE_AGE = 86400
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {'CLIENT_CLASS': 'django_redis.client.DefaultClient'},
    }
}


# Password validation
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
LANGUAGE_CODE = 'en-us'
TIME_ZONE = os.getenv("DJANGO_TIME_ZONE", "UTC")
USE_I18N = True
USE_TZ = True

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
