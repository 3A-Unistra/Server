import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # External apps
    'channels',

    # Local

    'server.game_handler'
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

ROOT_URLCONF = 'server.urls'

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

# WSGI_APPLICATION = 'server.wsgi.application'
ASGI_APPLICATION = 'server.asgi.application'

# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

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

# Logging

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
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'daphne': {
            'handlers': [
                'console',
            ],
            'level': 'DEBUG'
        }
    },
}

# Internationalization
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# JWT Private KEy
JWT_KEY = config('JWT_TOKEN',
                 default='@xxw!3fx@wjfi+%t-#m5^m4n&r#(-gz$nz2o24tij%9a&w')

# django channels layers

REDIS_HOST = config('REDIS_HOST', default='127.0.0.1')
REDIS_PASSWORD = config('REDIS_PASSWORD', default='')
REDIS_PORT = config('REDIS_PORT', default=6379, cast=int)
REDIS_CONNECTION_STRING = "redis://:%s@%s:%s/0" % (
    REDIS_PASSWORD, REDIS_HOST, REDIS_PORT)

CHANNEL_LAYERS = {
    'default': {
        # Method 2: Via local Redis
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [REDIS_CONNECTION_STRING],
        },
        # Method 3: Via In-memory channel layer
        # Using this method.
        # "BACKEND": "channels.layers.InMemoryChannelLayer"
    },
}

# If server is localhost then SERVER_OFFLINE should be True
SERVER_OFFLINE = config('SERVER_OFFLINE', default=False, cast=bool)

ENGINE_CONFIG = {
    'TICK_RATE': 20,

    # In seconds
    'WAITING_PLAYERS_TIMEOUT': 60,
    'GAME_STARTING_TIMEOUT': 3,
    'START_DICE_WAIT': 5,
    'START_DICE_REROLL_WAIT': 3,
    'ROUND_START_WAIT': 1,
    'ROUND_DICE_CHOICE_WAIT': 3,
    'ACTION_START_WAIT': 3,
    'ACTION_TIMEOUT_WAIT': 100,
    'AUCTION_TOUR_WAIT': 10,
    'GAME_WIN_WAIT': 10,
    'GAME_END_WAIT': 4,

    'PING_HEARTBEAT_TIMEOUT': 10,

    'MONEY_START_MIN': 500,
    'MONEY_START_DEFAULT': 1000,
    'MONEY_START_MAX': 4000,

    'NB_ROUNDS_MIN': 5,
    'NB_ROUNDS_DEFAULT': 13,
    'NB_ROUNDS_MAX': 1000,

    # Min 30 secs, Max 2min for action_timeout
    'TIME_ROUNDS_MIN': 30,
    'TIME_ROUNDS_DEFAULT': 90,
    'TIME_ROUNDS_MAX': 120,

    'MONEY_GO': 200,

    # replace w number of pieces
    'MAX_PIECE_NB': 7,

    'MIN_NB_PLAYERS': 2,
    'MAX_NB_PLAYERS': 8,
    'DEFAULT_NB_PLAYERS': 8,

    'MAX_DOUBLES_JAIL': 3,
    'MAX_JAIL_TURNS': 3,
    'JAIL_LEAVE_PRICE': 50,
    'MAX_NUMBER_OF_GAMES': 10,

    'BANK_HOUSES_COUNT': 32,
    'BANK_HOTELS_COUNT': 12
}
