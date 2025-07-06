"""
Serializers for the escrow app.

This module defines DRF serializers for EscrowTransaction model.
"""
from rest_framework import serializers
from .models import EscrowTransaction


class EscrowTransactionSerializer(serializers.ModelSerializer):
    """
    Serializer for escrow transaction display.
    
    Provides escrow transaction information for API responses.
    """
    
    can_be_released = serializers.BooleanField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    time_locked = serializers.SerializerMethodField()
    
    class Meta:
        """Meta options for EscrowTransactionSerializer."""
        
        model = EscrowTransaction
        fields = [
            'id', 'request', 'amount', 'status', 'can_be_released',
            'is_active', 'time_locked', 'locked_at', 'released_at', 'notes'
        ]
        read_only_fields = [
            'id', 'request', 'amount', 'status', 'can_be_released',
            'is_active', 'time_locked', 'locked_at', 'released_at'
        ]
    
    def get_time_locked(self, obj):
        """Get human-readable time since locking."""
        from django.utils.timesince import timesince
        if obj.status == 'released' and obj.released_at:
            return timesince(obj.locked_at, obj.released_at)
        return timesince(obj.locked_at)
    