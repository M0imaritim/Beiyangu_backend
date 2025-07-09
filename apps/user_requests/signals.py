from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.exceptions import ValidationError
from .models import Request

@receiver(post_save, sender=Request)
def handle_request_creation(sender, instance, created, **kwargs):
    """
    Handle post-creation tasks for requests.
    
    Currently disabled - escrow creation should be handled
    when a bid is accepted, not when request is created.
    """
    if created:
        # For now, we don't automatically create escrow on request creation
        # Escrow is created when a bid is accepted
        pass