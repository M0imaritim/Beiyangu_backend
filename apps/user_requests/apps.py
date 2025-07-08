from django.apps import AppConfig



class UserRequestsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.user_requests'

    def ready(self):
        import apps.user_requests.signals  # Ensure signals are imported
