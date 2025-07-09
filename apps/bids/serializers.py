# apps/bids/serializers.py
"""
Serializers for the bids app.

This module defines DRF serializers for Bid model
to handle API serialization and validation.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Bid

User = get_user_model()


class SellerSerializer(serializers.ModelSerializer):
    """Serializer for seller information in bids."""
    
    class Meta:
        """Meta options for SellerSerializer."""
        
        model = User
        fields = ['id', 'username', 'first_name', 'last_name']
        read_only_fields = ['id', 'username', 'first_name', 'last_name']


class BidSerializer(serializers.ModelSerializer):
    """
    Serializer for bid display and listing.
    
    Provides all bid information including seller details.
    """
    
    seller = SellerSerializer(read_only=True)
    savings_amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    savings_percentage = serializers.DecimalField(
        max_digits=5, decimal_places=2, read_only=True
    )
    is_editable = serializers.BooleanField(read_only=True)
    can_be_accepted = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()
    time_since_created = serializers.SerializerMethodField()
    
    class Meta:
        """Meta options for BidSerializer."""
        
        model = Bid
        fields = [
            'id', 'request', 'seller', 'amount', 'message',
            'delivery_time', 'is_accepted', 'savings_amount',
            'savings_percentage', 'is_editable', 'can_be_accepted',
            'is_owner', 'time_since_created', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'request', 'seller', 'is_accepted', 'savings_amount',
            'savings_percentage', 'is_editable', 'can_be_accepted',
            'is_owner', 'time_since_created', 'created_at', 'updated_at'
        ]
    
    def get_can_be_accepted(self, obj):
        """Check if this bid can be accepted by current user."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return (
                obj.request.buyer == request.user and
                obj.can_be_accepted()
            )
        return False
    
    def get_is_owner(self, obj):
        """Check if current user is the bid owner."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.seller == request.user
        return False
    
    def get_time_since_created(self, obj):
        """Get human-readable time since creation."""
        from django.utils.timesince import timesince
        return timesince(obj.created_at)


class BidCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating bids.
    
    Handles validation and creation of new bids.
    """
    
    class Meta:
        """Meta options for BidCreateUpdateSerializer."""
        
        model = Bid
        fields = ['amount', 'message', 'delivery_time']
    
    def validate_amount(self, value):
        """Validate bid amount."""
        if value <= 0:
            raise serializers.ValidationError(
                "Bid amount must be greater than zero."
            )
        
        # Check against request budget during creation
        if self.instance is None:  # Creating new bid
            request_obj = self.context.get('request_obj')
            if request_obj and value > request_obj.budget:
                raise serializers.ValidationError(
                    f"Bid amount cannot exceed the budget of ${request_obj.budget}."
                )
        
        return value
    
    def validate_message(self, value):
        """Validate bid message."""
        if len(value.strip()) < 10:
            raise serializers.ValidationError(
                "Message must be at least 10 characters long."
            )
        return value.strip()
    
    def validate_delivery_time(self, value):
        """Validate delivery time."""
        if value is not None and value <= 0:
            raise serializers.ValidationError(
                "Delivery time must be greater than zero days."
            )
        return value
    
    def create(self, validated_data):
        """Create a new bid with the current user as seller."""
        validated_data['seller'] = self.context['request'].user
        validated_data['request'] = self.context['request_obj']
        
        bid = Bid(**validated_data)
        
        bid._current_user = self.context['request'].user
        
        bid.save()
        
        return bid