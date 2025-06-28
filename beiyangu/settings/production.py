from .base import *
import dj_database_url

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Parse Railway's DATABASE_URL
DATABASES = {
    'default': dj_database_url.parse(os.getenv('DATABASE_URL'))
}

# Railway deployment settings
ALLOWED_HOSTS = [
    '.railway.app',
    os.getenv('RAILWAY_PUBLIC_DOMAIN', ''),
]

# Add your frontend domain to allowed hosts
CORS_ALLOWED_ORIGINS = [
    os.getenv('FRONTEND_URL', 'https://your-frontend-domain.vercel.app'),
]

CORS_ALLOW_CREDENTIALS = True

# Security Settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_SECONDS = 86400
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# JWT Settings for production
SIMPLE_JWT.update({
    'AUTH_COOKIE_SECURE': True,
    'AUTH_COOKIE_SAMESITE': 'None',
})

# Static files for production
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}