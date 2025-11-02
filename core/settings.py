import os
from datetime import timedelta
from pathlib import Path
from typing import Dict, List

import environ

env = environ.Env(
    # set casting, default value
    DEBUG=(bool, True),
    ALLOWED_HOSTS=(list, []),
)
env.escape_proxy = True


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Take environment variables from .env file
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY: str = env("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
# True if not in os.environ because of casting above
DEBUG: bool = env("DEBUG")

ALLOWED_HOSTS: List[str] = env("ALLOWED_HOSTS")

# Application definition

INSTALLED_APPS = [
    "dal",
    "dal_select2",
    "import_export",
    "nested_admin",
    "smart_selects",
    "admin_interface",
    "colorfield",
    "rangefilter",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "django.contrib.postgres",
    # Third party apps
    "messages_extends",
    "computedfields",
    "sequences.apps.SequencesConfig",
    "drf_yasg",
    "corsheaders",
    "rest_framework",
    "dj_rest_auth",
    "django.contrib.sites",
    "allauth",
    "allauth.account",
    "dj_rest_auth.registration",
    "allauth.socialaccount",
    "imagekit",
    "django_extensions",
    "django_cron",
    "django_lifecycle_checks",
    # Local apps
    "authentication",
    "products",
    "orders",
    "files",
    "notifications",
    # Third party apps
    "constance",
    "constance.backends.database",
    "django_cleanup.apps.CleanupConfig",
]

MESSAGE_STORAGE = "messages_extends.storages.FallbackStorage"

CONSTANCE_BACKEND = "constance.backends.database.DatabaseBackend"

CONSTANCE_CONFIG = {
    "USD_TO_IQD_EXCHANGE_RATE": (1450, "USD to IQD exchange rate", int),
}

USE_DJANGO_JQUERY = True

SITE_ID = 1

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "crum.CurrentRequestUserMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

CRON_CLASSES = [
    "orders.cron.CancelOrdersNotPaid",
]

DJANGO_CRON_DELETE_LOGS_OLDER_THAN = 15

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"

# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DATABASES = {
    "default": env.db(),
}

# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    # {
    #     "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    # },
    # {
    #     "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    #     "OPTIONS": {
    #         "min_length": 6,
    #     },
    # },
    # {
    #     "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    # },
    # {
    #     "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    # },
]

# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Baghdad"

USE_I18N = True

USE_TZ = False

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = "https://api.original-software.project1.company/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")

MEDIA_URL = "https://api.original-software.project1.company/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Custom User Model
AUTH_USER_MODEL = "authentication.User"

# django-corsheaders
CORS_ALLOW_ALL_ORIGINS = True
# CORS_ALLOWED_ORIGINS = [
#     "https://api.original-software.project1.company",
# ]


# Rest Framework Settings
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "dj_rest_auth.jwt_auth.JWTCookieAuthentication",
    ],
    "COERCE_DECIMAL_TO_STRING": False,
    "DEFAULT_RENDERER_CLASSES": ("rest_framework.renderers.JSONRenderer",),
}

# drf_yasg
SWAGGER_SETTINGS = {
    # "USE_SESSION_AUTH": False,
    "SECURITY_DEFINITIONS": {
        "Bearer": {"type": "apiKey", "name": "Authorization", "in": "header"},
    },
    "LOGOUT_URL": "/admin/logout/",
}

# dj-rest-auth
REST_AUTH = {
    "USE_JWT": True,
    "JWT_AUTH_COOKIE": "original_software-jwt",
    "JWT_AUTH_REFRESH_COOKIE": "original_software-jwt-refresh",
    "USER_DETAILS_SERIALIZER": "authentication.serializers.CustomUserDetailsSerializer",
    "REGISTER_SERIALIZER": "authentication.registration.serializers.CustomRegisterSerializer",
    "PASSWORD_RESET_SERIALIZER": "authentication.serializers.CustomPasswordResetSerializer",
    "TOKEN_MODEL": None,
    "JWT_AUTH_HTTPONLY": False,
    "JWT_AUTH_SECURE": True,
    "JWT_AUTH_RETURN_EXPIRATION": True,
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=43200),
}

X_FRAME_OPTIONS = "SAMEORIGIN"
SILENCED_SYSTEM_CHECKS = ["security.W019"]

# allauth
# https://django-allauth.readthedocs.io/en/latest/configuration.html

ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = "optional"  # "mandatory", "optional", or "none"
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USERNAME_MIN_LENGTH = 4
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_ADAPTER = "authentication.adapter.CustomAccountAdapter"

# ACCOUNT_CONFIRM_EMAIL_ON_GET = True
# LOGIN_URL = 'http://localhost:8000/users/login'

AUTHENTICATION_BACKENDS = [
    # Needed to login by username in Django admin, regardless of allauth
    "django.contrib.auth.backends.ModelBackend",
    # allauth specific authentication methods, such as login by e-mail
    "allauth.account.auth_backends.AuthenticationBackend",
]

DEFAULT_FROM_EMAIL = env("EMAIL_HOST_USER")
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "mail.your-server.de"
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False

CLIENT_DOMAIN = env("CLIENT_DOMAIN")
CLIENT_RESET_PATH = env("CLIENT_RESET_PATH")
CLIENT_VERIFY_ACCOUNT_PATH = env("CLIENT_VERIFY_ACCOUNT_PATH")

ZAIN_CASH_TRANSACTION_URL = env("ZAIN_CASH_TRANSACTION_URL")
ZAIN_CASH_MSISDN = env("ZAIN_CASH_MSISDN")
ZAIN_CASH_MERCHANT_ID = env("ZAIN_CASH_MERCHANT_ID")
ZAIN_CASH_MERCHANT_SECRET = env("ZAIN_CASH_MERCHANT_SECRET")
ZAIN_CASH_REDIRECT_URL = env("ZAIN_CASH_REDIRECT_URL")

CLIENT_TRANSACTION_SUCCESS_URL = env("CLIENT_TRANSACTION_SUCCESS_URL")
CLIENT_TRANSACTION_FAILED_URL = env("CLIENT_TRANSACTION_FAILED_URL")

QICARD_USERNAME = env("QICARD_USERNAME")
QICARD_PASSWORD = env("QICARD_PASSWORD")
QICARD_TERMINAL_ID = env("QICARD_TERMINAL_ID")
QICARD_PAY_TRANSACTION_URL = env("QICARD_PAY_TRANSACTION_URL")
QICARD_TRANSACTION_STATUS_URL = env("QICARD_TRANSACTION_STATUS_URL")
QICARD_REDIRECT_URL = env("QICARD_REDIRECT_URL")
QICARD_WEBHOOK_URL = env("QICARD_WEBHOOK_URL")
QICARD_PUBLIC_KEY_PATH = env("QICARD_PUBLIC_KEY_PATH")

FASTPAY_PAYMENT_INITIAITON_URL = env("FASTPAY_PAYMENT_INITIAITON_URL")
FASTPAY_PAYMENT_VALIDATION_URL = env("FASTPAY_PAYMENT_VALIDATION_URL")
FASTPAY_STORE_ID = env("FASTPAY_STORE_ID")
FASTPAY_STORE_PASSWORD = env("FASTPAY_STORE_PASSWORD")

FIB_CLIENT_ID = env("FIB_CLIENT_ID")
FIB_CLIENT_SECRET = env("FIB_CLIENT_SECRET")
FIB_AUTH_URL = env("FIB_AUTH_URL")
FIB_CREATE_PAYMENT_URL = env("FIB_CREATE_PAYMENT_URL")
FIB_REDIRECT_URL = env("FIB_REDIRECT_URL")
FIB_PAYMENT_STATUS_URL = env("FIB_PAYMENT_STATUS_URL")

# SECURE_SSL_REDIRECT = True
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True


# Removing old collected static files
# python manage.py collectstatic --noinput --clear --no-post-process
