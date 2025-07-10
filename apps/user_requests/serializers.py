"""
Serializers for the Beiyangu marketplace request system.

This module provides serializers for Request and RequestCategory models
with appropriate validation and field handling.
"""
from decimal import Decimal
from django.utils import timezone
from rest_framework import serializers
from rest_framework.fields import CharField

from .models import Request, RequestCategory
from apps.escrow.models import EscrowTransaction


class RequestCategorySerializer(serializers.ModelSerializer):
    """Serializer for RequestCategory model."""

    class Meta:
        model = RequestCategory
        fields = [
            'id',
            'name',
            'description',
            'is_active'
        ]
        read_only_fields = ['id']


class RequestSerializer(serializers.ModelSerializer):
    """
    Basic serializer for Request model.

    Used for list views and basic CRUD operations.
    """

    buyer_name = serializers.CharField(
        source='buyer.get_full_name', read_only=True)
    buyer_username = serializers.CharField(
        source='buyer.username', read_only=True)
    category_name = serializers.CharField(
        source='category.name', read_only=True)
    status_display = serializers.CharField(
        source='get_status_display', read_only=True)
    bid_count_ = serializers.IntegerField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    can_be_bid_on = serializers.SerializerMethodField()
    time_until_deadline = serializers.SerializerMethodField()

    class Meta:
        model = Request
        fields = [
            'id',
            'public_id',
            'title',
            'description',
            'budget',
            'buyer',
            'buyer_name',
            'buyer_username',
            'status',
            'status_display',
            'category',
            'category_name',
            'deadline',
            'bid_count_',
            'is_expired',
            'can_be_bid_on',
            'time_until_deadline',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'id',
            'public_id',
            'buyer',
            'buyer_name',
            'buyer_username',
            'status',
            'status_display',
            'category_name',
            'bid_count_',
            'is_expired',
            'can_be_bid_on',
            'time_until_deadline',
            'created_at',
            'updated_at',
            'created_by',
            'updated_by'
        ]

    def get_can_be_bid_on(self, obj):
        """Check if this request can receive bids."""
        return obj.can_be_bid_on()

    def get_time_until_deadline(self, obj):
        """Get human-readable time until deadline."""
        if not obj.deadline:
            return None

        now = timezone.now()
        if obj.deadline <= now:
            return "Expired"

        delta = obj.deadline - now
        days = delta.days
        hours = delta.seconds // 3600

        if days > 0:
            return f"{days} days, {hours} hours"
        elif hours > 0:
            return f"{hours} hours"
        else:
            minutes = delta.seconds // 60
            return f"{minutes} minutes"

    def validate_budget(self, value):
        """Validate budget amount."""
        if value <= Decimal('0.00'):
            raise serializers.ValidationError(
                "Budget must be greater than zero.")

        # Optional: Set maximum budget limit
        if value > Decimal('1000000.00'):
            raise serializers.ValidationError(
                "Budget cannot exceed $1,000,000.")

        return value

    def validate_deadline(self, value):
        """Validate deadline is in the future."""
        if value and value <= timezone.now():
            raise serializers.ValidationError(
                "Deadline must be in the future.")

        # Optional: Validate deadline is not too far in the future
        max_deadline = timezone.now() + timezone.timedelta(days=365)
        if value and value > max_deadline:
            raise serializers.ValidationError(
                "Deadline cannot be more than 1 year in the future.")

        return value

    def validate_title(self, value):
        """Validate title content."""
        if len(value.strip()) < 5:
            raise serializers.ValidationError(
                "Title must be at least 5 characters long.")

        return value.strip()

    def validate_description(self, value):
        """Validate description content."""
        if len(value.strip()) < 20:
            raise serializers.ValidationError(
                "Description must be at least 20 characters long.")

        return value.strip()


class RequestDetailSerializer(RequestSerializer):
    """
    Detailed serializer for Request model.

    Used for retrieve operations and includes additional fields
    and related data.
    """

    category_details = RequestCategorySerializer(
        source='category', read_only=True)
    accepted_bid_id = serializers.IntegerField(
        source='accepted_bid.id', read_only=True)
    accepted_bid_amount = serializers.DecimalField(
        source='accepted_bid.amount',
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    accepted_seller_name = serializers.CharField(
        source='accepted_bid.seller.get_full_name',
        read_only=True
    )
    recent_bids = serializers.SerializerMethodField()
    has_escrow = serializers.SerializerMethodField()

    class Meta(RequestSerializer.Meta):
        fields = RequestSerializer.Meta.fields + [
            'category_details',
            'accepted_bid_id',
            'accepted_bid_amount',
            'accepted_seller_name',
            'recent_bids',
            'has_escrow'
        ]

    def get_recent_bids(self, obj):
        """Get recent bids for this request (limited for performance)."""
        from apps.bids.serializers import BidSerializer

        recent_bids = obj.bids.filter(
            is_deleted=False
        ).select_related('seller').order_by('-created_at')[:5]

        return BidSerializer(recent_bids, many=True).data

    def get_has_escrow(self, obj):
        """Check if request has an associated escrow transaction."""
        return hasattr(obj, 'escrow') and obj.escrow is not None


class RequestCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new requests.

    Includes additional validation for creation-specific requirements.
    """

    class Meta:
        model = Request
        fields = [
            'title',
            'description',
            'budget',
            'category',
            'deadline'
        ]

    def validate(self, attrs):
        """Perform cross-field validation."""
        # Ensure category is active if provided
        category = attrs.get('category')
        if category and not category.is_active:
            raise serializers.ValidationError({
                'category': 'Selected category is not active.'
            })

        return attrs

    def validate_budget(self, value):
        """Validate budget for new requests."""
        if value <= Decimal('0.00'):
            raise serializers.ValidationError(
                "Budget must be greater than zero.")

        # Minimum budget requirement
        if value < Decimal('5.00'):
            raise serializers.ValidationError("Minimum budget is $5.00.")

        # Maximum budget check
        if value > Decimal('1000000.00'):
            raise serializers.ValidationError(
                "Budget cannot exceed $1,000,000.")

        return value

    def validate_deadline(self, value):
        """Validate deadline is in the future."""
        if value and value <= timezone.now():
            raise serializers.ValidationError(
                "Deadline must be in the future.")

        # Validate deadline is not too far in the future
        max_deadline = timezone.now() + timezone.timedelta(days=365)
        if value and value > max_deadline:
            raise serializers.ValidationError(
                "Deadline cannot be more than 1 year in the future.")

        return value

    def validate_title(self, value):
        """Validate title content."""
        if not value or len(value.strip()) < 5:
            raise serializers.ValidationError(
                "Title must be at least 5 characters long.")

        return value.strip()

    def validate_description(self, value):
        """Validate description content."""
        if not value or len(value.strip()) < 20:
            raise serializers.ValidationError(
                "Description must be at least 20 characters long.")

        return value.strip()

    def create(self, validated_data):
        """Create a new request with the authenticated user as buyer."""
        request = self.context['request']
        validated_data['buyer'] = request.user
        return super().create(validated_data)


class RequestUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating existing requests.

    Only allows updating certain fields and includes status-based validation.
    """

    class Meta:
        model = Request
        fields = [
            'title',
            'description',
            'budget',
            'deadline'
        ]

    def validate(self, attrs):
        """Validate update based on current request status."""
        request_obj = self.instance

        # Only allow updates if request is open
        if request_obj.status != 'open':
            raise serializers.ValidationError(
                "Cannot update request that is not in 'open' status."
            )

        # Don't allow budget reduction if there are existing bids
        if 'budget' in attrs and hasattr(
                request_obj,
                'bid_count') and request_obj.bid_count > 0:
            if attrs['budget'] < request_obj.budget:
                raise serializers.ValidationError({
                    'budget': 'Cannot reduce budget\
                        when there are existing bids.'
                })

        return attrs

    def validate_budget(self, value):
        """Validate budget for updates."""
        if value <= Decimal('0.00'):
            raise serializers.ValidationError(
                "Budget must be greater than zero.")

        # Minimum budget requirement
        if value < Decimal('5.00'):
            raise serializers.ValidationError("Minimum budget is $5.00.")

        # Maximum budget check
        if value > Decimal('1000000.00'):
            raise serializers.ValidationError(
                "Budget cannot exceed $1,000,000.")

        return value

    def validate_deadline(self, value):
        """Validate deadline is in the future."""
        if value and value <= timezone.now():
            raise serializers.ValidationError(
                "Deadline must be in the future.")

        # Validate deadline is not too far in the future
        max_deadline = timezone.now() + timezone.timedelta(days=365)
        if value and value > max_deadline:
            raise serializers.ValidationError(
                "Deadline cannot be more than 1 year in the future.")

        return value

    def validate_title(self, value):
        """Validate title content."""
        if not value or len(value.strip()) < 5:
            raise serializers.ValidationError(
                "Title must be at least 5 characters long.")

        return value.strip()

    def validate_description(self, value):
        """Validate description content."""
        if not value or len(value.strip()) < 20:
            raise serializers.ValidationError(
                "Description must be at least 20 characters long.")

        return value.strip()


class RequestStatusSerializer(serializers.Serializer):
    """
    Serializer for status change operations.

    Used for status transition endpoints.
    """

    status = serializers.ChoiceField(choices=Request.STATUS_CHOICES)
    reason = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True)

    def validate_status(self, value):
        """Validate status transition is allowed."""
        request_obj = self.context.get('request_obj')

        if not request_obj:
            raise serializers.ValidationError(
                "Request object not found in context.")

        if hasattr(request_obj, 'can_transition_to') and not\
                request_obj.can_transition_to(value):
            raise serializers.ValidationError(
                f"Cannot transition from '{request_obj.status}' to '{value}'"
            )

        return value
