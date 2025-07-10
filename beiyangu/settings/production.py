"""Production settings for beiyangu project.

This module contains settings specific to the production environment.
It includes security hardening, production database configuration,
and optimized settings for performance and security.
"""

import os

import dj_database_url

from .base import *

from dotenv import load_dotenv

load_dotenv()


# Security: Debug must be False in production
DEBUG = False

# Database configuration using DATABASE_URL
DATABASES = {
    'default': dj_database_url.parse(
        os.getenv('DATABASE_URL'),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# Allowed hosts for production
ALLOWED_HOSTS = [
    'beiyangu.up.railway.app',
    os.getenv('ALLOWED_HOST', ''),
]

# Remove empty strings from ALLOWED_HOSTS
ALLOWED_HOSTS = [host for host in ALLOWED_HOSTS if host]

# CORS Settings for production
CORS_ALLOWED_ORIGINS = [
    os.getenv('FRONTEND_URL', 'https://your-frontend-domain.vercel.app'),
]

# Remove empty strings from CORS_ALLOWED_ORIGINS
CORS_ALLOWED_ORIGINS = [origin for origin in CORS_ALLOWED_ORIGINS if origin]

CORS_ALLOW_CREDENTIALS = True

# CSRF trusted origins for production
CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS.copy()

# Security Settings for production
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_PRELOAD = True
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Session and CSRF cookies security
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'None'
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'None'

# JWT Settings for production
SIMPLE_JWT.update({
    'AUTH_COOKIE_SECURE': True,
    'AUTH_COOKIE_SAMESITE': 'None',
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),  # Shorter in production
})

# Static files configuration for production
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static'] if (BASE_DIR / 'static').exists() else []

# Static files storage for production
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = False  # Disable in production for performance

# Media files configuration for production
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Email configuration for production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER)

# Cache configuration for production
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'beiyangu',
        'TIMEOUT': 300,
    }
}

# Session configuration for production
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# Logging configuration for production
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} '
                      '{thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.security': {
            'handlers': ['console', 'file'],
            'level': 'WARNING',
            'propagate': True,
        },
        'beiyangu': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
}

# Create logs directory if it doesn't exist
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

# Additional security headers
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'

# Data upload limits
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB

# Admin security
ADMIN_URL = os.getenv('ADMIN_URL', 'admin/')

