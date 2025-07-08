from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Request
from .serializers import RequestCreateSerializer

@receiver(post_save, sender=Request)
def validate_escrow(sender, instance, created, **kwargs):
    if created:
        serializer = RequestCreateSerializer()
        try:
            serializer.validate_escrow(instance)
        except serializer.ValidationError as e:
            # Optionally update Request status or flag
            instance.status = 'pending_escrow'  # Add a custom status to Request model
            instance.save()