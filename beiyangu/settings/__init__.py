import os

# Default to development settings
settings_module = os.getenv('DJANGO_SETTINGS_MODULE', 'beiyangu.settings.development')

if settings_module == 'beiyangu.settings.production':
    from .production import *
else:
    from .development import *