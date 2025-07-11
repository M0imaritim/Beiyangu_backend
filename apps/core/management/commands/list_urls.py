# apps/core/management/commands/list_urls.py
from django.core.management.base import BaseCommand
from django.urls import get_resolver
from django.conf import settings

class Command(BaseCommand):
    help = 'List all available URLs'

    def handle(self, *args, **options):
        urlconf = __import__(settings.ROOT_URLCONF, {}, {}, [''])
        
        def show_urls(urllist, depth=0):
            for entry in urllist:
                print("  " * depth + entry.pattern.regex.pattern)
                if hasattr(entry, 'url_patterns'):
                    show_urls(entry.url_patterns, depth + 1)
        
        show_urls(urlconf.urlpatterns)