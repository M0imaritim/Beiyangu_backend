"""
Serializers for the escrow app.
"""
from rest_framework import serializers
from .models import EscrowTransaction


class EscrowTransactionSerializer(serializers.ModelSerializer):
    """
    Serializer for escrow transaction display.
    """
    
    can_be_released = serializers.BooleanField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    is_pending = serializers.BooleanField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    time_locked = serializers.SerializerMethodField()
    status_info = serializers.SerializerMethodField()
    
    class Meta:
        model = EscrowTransaction
        fields = [
            'public_id', 'amount', 'escrow_fee', 'total_amount',
            'payment_method', 'payment_method_display', 'status', 'status_display',
            'payment_reference', 'payment_processor',
            'can_be_released', 'is_active', 'is_pending', 'time_locked',
            'created_at', 'locked_at', 'released_at', 'notes', 'status_info'
        ]
        read_only_fields = [
            'public_id', 'amount', 'escrow_fee', 'total_amount',
            'payment_method', 'status', 'payment_reference', 'payment_processor',
            'can_be_released', 'is_active', 'is_pending', 'time_locked',
            'created_at', 'locked_at', 'released_at', 'status_info'
        ]
    
    def get_time_locked(self, obj):
        """Get human-readable time since locking."""
        from django.utils.timesince import timesince
        if obj.status == 'released' and obj.released_at:
            return timesince(obj.locked_at, obj.released_at)
        elif obj.locked_at:
            return timesince(obj.locked_at)
        return None
    
    def get_status_info(self, obj):
        """Get detailed status information."""
        return obj.get_status_info()


class EscrowActionSerializer(serializers.Serializer):
    """
    Serializer for escrow actions (release, hold, refund).
    """
    
    action = serializers.ChoiceField(
        choices=[
            ('release', 'Release Funds'),
            ('hold', 'Hold for Dispute'),
            ('refund', 'Refund Funds'),
        ]
    )
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_action(self, value):
        """Validate that the action is allowed for current escrow status."""
        escrow = self.context.get('escrow')
        if escrow and not escrow.can_transition_to(value):
            raise serializers.ValidationError(
                f"Cannot {value} from {escrow.status} status"
            )
        return value