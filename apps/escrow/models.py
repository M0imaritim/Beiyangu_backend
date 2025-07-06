"""
Escrow transaction model for the Beiyangu marketplace.

This module defines the EscrowTransaction model that handles
the simulated escrow system for secure payments.
"""
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone
import uuid

User = get_user_model()


class EscrowTransaction(models.Model):
    """
    Model representing an escrow transaction for a request.
    
    When a bid is accepted, funds are locked in escrow until
    the order is completed and the buyer releases the funds.
    """
    
    STATUS_CHOICES = [
        ('locked', 'Locked'),
        ('released', 'Released'),
        ('held', 'Held for Dispute'),
        ('refunded', 'Refunded'),
    ]
    
    # Valid status transitions
    VALID_STATUS_TRANSITIONS = {
        'locked': ['released', 'held'],
        'held': ['released', 'refunded'],
        'released': [],  # Terminal state
        'refunded': [],  # Terminal state
    }
    
    # Public ID for external references
    public_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        help_text="Public identifier for this escrow transaction"
    )
    request = models.OneToOneField(
        'requests.Request',
        on_delete=models.CASCADE,
        related_name='escrow',
        help_text="The request this escrow is for"
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Amount locked in escrow"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='locked',
        help_text="Current status of the escrow"
    )
    locked_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When funds were locked in escrow"
    )
    released_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When funds were released from escrow"
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional notes about this escrow transaction"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_escrows',
        help_text="User who created this record"
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='updated_escrows',
        help_text="User who last updated this record"
    )
    
    class Meta:
        """Meta options for EscrowTransaction model."""
        
        ordering = ['-locked_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['locked_at']),
            models.Index(fields=['public_id']),
        ]
    
    def __str__(self):
        """Return string representation of the escrow transaction."""
        return f"Escrow ${self.amount} - {self.get_status_display()}"
    
    def clean(self):
        """Validate the escrow data."""
        super().clean()
        
        # Validate amount matches accepted bid
        if self.request.accepted_bid and self.amount != self.request.accepted_bid.amount:
            raise ValidationError("Escrow amount must match accepted bid amount")
    
    def save(self, *args, **kwargs):
        """Override save to set audit fields."""
        # Set created_by on first save
        if not self.pk and hasattr(self, '_current_user'):
            self.created_by = self._current_user
        
        # Always set updated_by
        if hasattr(self, '_current_user'):
            self.updated_by = self._current_user
        
        super().save(*args, **kwargs)
    
    @property
    def is_active(self):
        """Check if escrow is currently active (locked)."""
        return self.status == 'locked'
    
    @property
    def can_be_released(self):
        """Check if escrow can be released."""
        return (
            self.status == 'locked' and
            self.request.status == 'delivered'
        )
    
    def can_transition_to(self, new_status):
        """Check if escrow can transition to the given status."""
        return new_status in self.VALID_STATUS_TRANSITIONS.get(self.status, [])
    
    @transaction.atomic
    def release_funds(self, user=None, notes=None):
        """
        Release funds from escrow.
        
        Args:
            user (User, optional): User releasing the funds
            notes (str, optional): Additional notes for the release
            
        Returns:
            bool: True if funds were successfully released
        """
        if not self.can_be_released():
            return False
        
        if not self.can_transition_to('released'):
            return False
        
        self.status = 'released'
        self.released_at = timezone.now()
        if notes:
            self.notes = notes
        if user:
            self._current_user = user
        self.save()
        
        # Update request status to completed
        self.request.change_status('completed', user)
        
        return True
    
    @transaction.atomic
    def hold_for_dispute(self, user=None, notes=None):
        """
        Hold funds in escrow due to dispute.
        
        Args:
            user (User, optional): User initiating the hold
            notes (str, optional): Reason for holding funds
            
        Returns:
            bool: True if funds were successfully held
        """
        if not self.can_transition_to('held'):
            return False
        
        self.status = 'held'
        if notes:
            self.notes = notes
        if user:
            self._current_user = user
        self.save()
        
        # Update request status to disputed
        self.request.change_status('disputed', user)
        
        return True
    
    @transaction.atomic
    def refund_funds(self, user=None, notes=None):
        """
        Refund funds from escrow.
        
        Args:
            user (User, optional): User processing the refund
            notes (str, optional): Reason for refund
            
        Returns:
            bool: True if funds were successfully refunded
        """
        if not self.can_transition_to('refunded'):
            return False
        
        self.status = 'refunded'
        self.released_at = timezone.now()
        if notes:
            self.notes = notes
        if user:
            self._current_user = user
        self.save()
        
        # Update request status to cancelled
        self.request.change_status('cancelled', user)
        
        return True
    
    @classmethod
    def create_for_request(cls, request, amount, user=None):
        """
        Create an escrow transaction for a request.
        
        Args:
            request: The Request instance
            amount: Amount to lock in escrow
            user: User creating the escrow
            
        Returns:
            EscrowTransaction: The created escrow transaction
        """
        escrow = cls(request=request, amount=amount)
        if user:
            escrow._current_user = user
        escrow.save()
        return escrow
