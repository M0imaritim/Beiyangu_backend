"""Django application configuration for the Escrow app."""
from django.apps import AppConfig


class EscrowConfig(AppConfig):
    """Configuration class for the Escrow app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.escrow'
