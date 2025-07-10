"""app configuration for bids app."""
from django.apps import AppConfig


class BidsConfig(AppConfig):
    """Configuration class for the bids app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.bids'
