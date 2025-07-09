"""
Bid model for the Beiyangu marketplace.

This module defines the Bid model that represents seller bids
on buyer requests in the marketplace system.
"""
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
import uuid

User = get_user_model()


class Bid(models.Model):
    """
    Model representing a seller's bid on a buyer's request.
    
    Sellers submit bids with their proposed amount and message
    explaining their approach or qualifications.
    """
    
    # Public ID for external references
    public_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        help_text="Public identifier for this bid"
    )
    request = models.ForeignKey(
        'user_requests.Request',
        on_delete=models.CASCADE,
        related_name='bids',
        help_text="The request this bid is for"
    )
    seller = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='bids',
        help_text="User who submitted this bid"
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Amount the seller is proposing"
    )
    message = models.TextField(
        help_text="Seller's proposal or message to the buyer"
    )
    delivery_time = models.PositiveIntegerField(
        help_text="Estimated delivery time in days",
        null=True,
        blank=True
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this bid expires"
    )
    is_accepted = models.BooleanField(
        default=False,
        help_text="Whether this bid has been accepted by the buyer"
    )
    is_deleted = models.BooleanField(
        default=False,
        help_text="Soft delete flag"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this bid was submitted"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When this bid was last modified"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,  # Add blank=True to allow empty values during validation
        related_name='created_bids',
        help_text="User who created this record"
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,  # Add blank=True to allow empty values during validation
        related_name='updated_bids',
        help_text="User who last updated this record"
    )
    
    class Meta:
        """Meta options for Bid model."""
        
        unique_together = ['request', 'seller']
        ordering = ['amount', '-created_at']
        indexes = [
            models.Index(fields=['request', 'is_accepted', 'is_deleted']),
            models.Index(fields=['seller', 'is_accepted']),
            models.Index(fields=['created_at']),
            models.Index(fields=['public_id']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        """Return string representation of the bid."""
        return f"Bid by {self.seller.username} - ${self.amount}"
    
    def clean(self):
        """Validate the bid data."""
        super().clean()
        
        # Validate bid amount doesn't exceed request budget
        if self.amount > self.request.budget:
            raise ValidationError("Bid amount cannot exceed request budget")
        
        # Validate seller is not the buyer
        if self.seller == self.request.buyer:
            raise ValidationError("Sellers cannot bid on their own requests")
        
        # Validate request is open for bidding
        if not self.request.can_be_bid_on():
            raise ValidationError("This request is not open for bidding")
        
        # Validate expiration date
        if self.expires_at and self.expires_at <= timezone.now():
            raise ValidationError("Expiration date must be in the future")
    
    def save(self, *args, **kwargs):
        """Override save to run validation and set audit fields."""
        # Set audit fields before validation
        if not self.pk and hasattr(self, '_current_user'):
            self.created_by = self._current_user
        
        if hasattr(self, '_current_user'):
            self.updated_by = self._current_user
        
        # Now run validation
        self.full_clean()
        
        super().save(*args, **kwargs)
    
    @property
    def is_editable(self):
        """Check if this bid can be edited."""
        return (
            not self.is_accepted and 
            not self.is_deleted and
            not self.is_expired and
            self.request.can_be_bid_on()
        )
    
    @property
    def is_expired(self):
        """Check if this bid has expired."""
        return self.expires_at and self.expires_at <= timezone.now()
    
    @property
    def savings_amount(self):
        """Calculate how much this bid saves compared to budget."""
        return self.request.budget - self.amount
    
    @property
    def savings_percentage(self):
        """Calculate savings percentage compared to budget."""
        if self.request.budget > 0:
            return (self.savings_amount / self.request.budget) * 100
        return 0
    
    def can_be_accepted(self):
        """Check if this bid can be accepted."""
        return (
            not self.is_accepted and
            not self.is_deleted and
            not self.is_expired and
            self.request.can_be_bid_on() and
            self.amount <= self.request.budget
        )
    
    def soft_delete(self, user=None):
        """Soft delete the bid."""
        self.is_deleted = True
        if user:
            self._current_user = user
        self.save()