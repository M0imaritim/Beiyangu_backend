"""Development settings for beiyangu project.

This module contains settings specific to the development environment.
It includes debug mode, development database configuration, and 
relaxed security settings suitable for local development.
"""

import os

from .base import * 

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Allowed hosts for development
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '0.0.0.0',
]

# Database configuration for development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'beiyangu_db'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

# CORS Settings for development
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

# Allow all origins in development (less secure but convenient)
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# CSRF trusted origins for development
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

# JWT Settings for development (less secure cookies)
SIMPLE_JWT.update({
    'AUTH_COOKIE_SECURE': False,
    'AUTH_COOKIE_SAMESITE': 'Lax',
})

# Cookie settings for development
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
CSRF_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SAMESITE = 'Lax'

# Email backend for development (prints to console)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Static files configuration for development
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Logging configuration for development
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
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'beiyangu': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

# Development-specific cache (dummy cache for development)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}