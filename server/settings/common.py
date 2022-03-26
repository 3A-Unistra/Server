import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
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
JWT_KEY = '@xxw!3fx@wjfi+%t-#m5^m4n&r#(-gz$nz2o24tij%9a&w'

# django channels layers

REDIS_HOST = os.getenv('REDIS_HOST', '127.0.0.1')
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')
REDIS_PORT = os.getenv('REDIS_PORT', 6379)
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
SERVER_OFFLINE = os.getenv('SERVER_OFFLINE', 'False').lower() in ('true', '1')

ENGINE_CONFIG = {
    'TICK_RATE': 20,

    # In seconds
    'WAITING_PLAYERS_TIMEOUT': 30,
    'GAME_STARTING_TIMEOUT': 3,
    'START_DICE_WAIT': 5,
    'START_DICE_REROLL_WAIT': 3,
    'ROUND_START_WAIT': 5,
    'ROUND_DICE_CHOICE_WAIT': 5,
    'ACTION_START_WAIT': 5,

    'PING_HEARTBEAT_TIMEOUT': 10,

    'MONEY_START': 1000,
    'MONEY_GO': 200,

    'MAX_DOUBLES_JAIL': 3,
    'MAX_JAIL_TURNS': 3,
    'JAIL_LEAVE_PRICE': 50,
    'MAX_NUMBER_OF_GAMES': 10
}
