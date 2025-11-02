"""
Django Settings for InstiPass Project

Production-ready configuration with security, authentication, and API settings.
"""

from datetime import timedelta
from pathlib import Path
import os

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'
BASE_DIR = Path(__file__).resolve().parent.parent

# =============================================================================
# CORE DJANGO SETTINGS
# =============================================================================

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["127.0.0.1", 'localhost']

# Application definition
INSTALLED_APPS = [
    # Django Core Apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-Party Apps
    'axes',
    'corsheaders',
    'django_otp',
    'django_otp.plugins.otp_totp',
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'drf_spectacular',
    'django_cleanup.apps.CleanupConfig',
    
    # Local Apps
    'administrator',
    'accounts',
    'institution',
    'student',
    'logs',
    'Id',
]

# Middleware configuration
MIDDLEWARE = [
    # Security & CORS
    'InstiPass.middleware.IPBanMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    
    # Django Core Middleware
    'django.middleware.security.SecurityMiddleware',
    'InstiPass.middleware.RequestMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    
    # Authentication & Security
    'django_otp.middleware.OTPMiddleware',
    'InstiPass.middleware.APILogMiddleware',
    "axes.middleware.AxesMiddleware",
    
    # Django Core (continued)
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'InstiPass.urls'

# Template configuration
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],
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

WSGI_APPLICATION = 'InstiPass.wsgi.application'

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ["DB_NAME"],
        "USER": os.environ['DB_USER'],
        "PASSWORD": os.environ["DB_PASS"],
        "HOST": os.environ["DB_HOST"],
        "PORT": os.environ["DB_PORT"],
        "OPTIONS": {
            # Add any MySQL-specific options here
        }
    }
}

# =============================================================================
# AUTHENTICATION & SECURITY
# =============================================================================

# Custom user model
AUTH_USER_MODEL = 'accounts.User'

# Authentication backends
AUTHENTICATION_BACKENDS = [
    "accounts.forms.EmailBackend",  # Custom email backend
    'django.contrib.auth.backends.ModelBackend',
    "axes.backends.AxesBackend",  # Axes (login attempt limiting)
]

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

# =============================================================================
# SESSION & SECURITY SETTINGS
# =============================================================================

# Session settings
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_AGE = 14400  # 4 hours (in seconds)
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_SAVE_EVERY_REQUEST = True

# CSRF settings
CSRF_COOKIE_AGE = 3600  # 1 hour
CSRF_TRUSTED_ORIGINS = [
    "http://127.0.0.1:3000",
    "http://localhost:3000",
]

# =============================================================================
# CORS (CROSS-ORIGIN RESOURCE SHARING) SETTINGS
# =============================================================================

CORS_ALLOWED_ORIGINS = [
    "http://127.0.0.1:3000",
    "http://localhost:3000",
]

CORS_ALLOW_CREDENTIALS = True

# =============================================================================
# REST FRAMEWORK CONFIGURATION
# =============================================================================

REST_FRAMEWORK = {
    # Throttling settings
    'DEFAULT_THROTTLE_CLASSES': [
        "InstiPass.throttles.EscalatingAnonThrottle",
        'rest_framework.throttling.UserRateThrottle',  # authenticated users
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '90/day',   # 90 requests per day for unauthenticated
        'user': '350/day'   # 350 requests per day for authenticated users
    },
    
    # Renderer classes
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    
    # Authentication classes
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    
    # API Schema
    'DEFAULT_SCHEMA_CLASS': "drf_spectacular.openapi.AutoSchema",
}

# =============================================================================
# JWT (JSON WEB TOKEN) SETTINGS
# =============================================================================

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=8),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': False,
    
    'ALGORITHM': 'HS256',
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'JWK_URL': None,
    'LEEWAY': 0,
    
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',
    
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',
    
    'JTI_CLAIM': 'jti',
}

# =============================================================================
# SECURITY & RATE LIMITING SETTINGS
# =============================================================================

# CAPTCHA settings
FAILED_CAPTCHA_LIMIT = 5

# IP Ban settings
IPBAN_BAN_LADDER = [15, 60, 24 * 60]  # minutes for successive bans
IPBAN_PERMANENT_AFTER = 4  # Permanent ban after 4 offenses
IPBAN_USE_CACHE = True  # Use cache for IP ban tracking

# Axes (login attempt limiting) settings
AXES_ENABLED = True
AXES_LOGIN_FAILURE_LIMIT = 5  # Block after 5 failed attempts
AXES_COOLOFF_TIME = 2  # Lockout for 2 hours
AXES_USERNAME_CALLABLE = lambda request, credentials: credentials.get('email')  # Use email as username
AXES_RESET_ON_SUCCESS = True  # Reset failed attempts on successful login
AXES_LOCKOUT_TEMPLATE = 'lockout.html'  # Custom lockout template
AXES_ONLY_USER_OR_IP_FAILURES = True  # Lock if either user OR IP exceeds limits
AXES_ONLY_ADMIN_SITE = True
AXES_ENABLE_ADMIN = True
AXES_LOCKOUT_PARAMETERS = ['username', 'ip_address', 'user_agent']
AXES_ONLY_ATTEMPTS_POST = True  # Only count POST requests

# =============================================================================
# APPLICATION-SPECIFIC SETTINGS
# =============================================================================

# Token expiration settings
ALGORITHM = "HS256"
DEFAULT_REGISTRATION_HOURS = 168  # 7 days
DEFAULT_SIGNUP_DURATION_HOURS = 1
DEFAULT_INSTITUTION_LOGIN_DURATION = 0.25  # 15 minutes

# =============================================================================
# INTERNATIONALIZATION & LOCALIZATION
# =============================================================================

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Nairobi'
USE_I18N = True
USE_TZ = True

# =============================================================================
# STATIC & MEDIA FILES
# =============================================================================

# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / 'static/'

# Media files (user-uploaded content)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# =============================================================================
# EMAIL CONFIGURATION
# =============================================================================

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = os.environ['HOST_MAIL']
EMAIL_HOST_PASSWORD = os.environ['HOST_PWD']
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False

# =============================================================================
# CELERY CONFIGURATION (ASYNCHRONOUS TASK PROCESSING)
# =============================================================================

CELERY_BROKER_URL = "redis://127.0.0.1:6379/0"
CELERY_RESULT_BACKEND = "redis://127.0.0.1:6379/0"
CELERY_TIMEZONE = "Africa/Nairobi"
CELERY_ENABLE_UTC = True
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes

# =============================================================================
# THIRD-PARTY APP CONFIGURATION
# =============================================================================

# Django Cleanup (automatic file deletion)
DJANGO_CLEANUP_KEEP_FILE_IF_ERROR = True
DJANGO_CLEANUP_LOG_LEVEL = "ERROR"

# =============================================================================
# CACHE CONFIGURATION (COMMENTED - UNCOMMENT TO ENABLE REDIS)
# =============================================================================

# CACHES = {
#     "default": {
#         "BACKEND": "django_redis.cache.RedisCache",
#         "LOCATION": "redis://127.0.0.1:6379/1",
#         "OPTIONS": {
#             "CLIENT_CLASS": "django_redis.client.DefaultClient",
#         }
#     }
# }

# =============================================================================
# SECURITY SETTINGS FOR PRODUCTION (RECOMMENDED)
# =============================================================================

# Uncomment and configure these for production deployment:

# # HTTPS Settings
# SECURE_SSL_REDIRECT = True
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True
# SECURE_BROWSER_XSS_FILTER = True
# SECURE_CONTENT_TYPE_NOSNIFF = True
# 
# # HSTS Settings
# SECURE_HSTS_SECONDS = 31536000  # 1 year
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# SECURE_HSTS_PRELOAD = True
# 
# # Additional Security Headers
# SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'