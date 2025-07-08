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
    
    When a request is created with escrow enabled, funds are simulated
    to be locked in escrow until the order is completed.
    """
    
    STATUS_CHOICES = [
        ('pending', 'Pending Setup'),
        ('locked', 'Locked'),
        ('released', 'Released'),
        ('held', 'Held for Dispute'),
        ('refunded', 'Refunded'),
        ('failed', 'Failed'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('paypal', 'PayPal'),
    ]
    
    # Valid status transitions
    VALID_STATUS_TRANSITIONS = {
        'pending': ['locked', 'failed'],
        'locked': ['released', 'held'],
        'held': ['released', 'refunded'],
        'released': [],  # Terminal state
        'refunded': [],  # Terminal state
        'failed': [],    # Terminal state
    }
    
    # Public ID for external references
    public_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        help_text="Public identifier for this escrow transaction"
    )
    request = models.OneToOneField(
        'user_requests.Request',
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
    escrow_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Escrow service fee"
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Total amount including fees"
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        help_text="Payment method used for escrow"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="Current status of the escrow"
    )
    
    # Simulated payment details
    payment_reference = models.CharField(
        max_length=100,
        blank=True,
        help_text="Simulated payment reference"
    )
    payment_processor = models.CharField(
        max_length=50,
        default='stripe_simulation',
        help_text="Simulated payment processor"
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When escrow was created"
    )
    locked_at = models.DateTimeField(
        null=True,
        blank=True,
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
    
    # Audit fields
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
        
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['public_id']),
            models.Index(fields=['payment_reference']),
        ]
    
    def __str__(self):
        """Return string representation of the escrow transaction."""
        return f"Escrow ${self.amount} - {self.get_status_display()}"
    
    def clean(self):
        """Validate the escrow data."""
        super().clean()
        
        # Calculate total amount
        if self.amount and self.escrow_fee:
            calculated_total = self.amount + self.escrow_fee
            if self.total_amount != calculated_total:
                self.total_amount = calculated_total
    
    def save(self, *args, **kwargs):
        """Override save to set audit fields and calculate totals."""
        # Set created_by on first save
        if not self.pk and hasattr(self, '_current_user'):
            self.created_by = self._current_user
        
        # Always set updated_by
        if hasattr(self, '_current_user'):
            self.updated_by = self._current_user
        
        # Calculate total amount if not set
        if not self.total_amount:
            self.total_amount = self.amount + self.escrow_fee
        
        # Generate payment reference if not set
        if not self.payment_reference:
            self.payment_reference = f"ESC_{self.public_id.hex[:8].upper()}"
        
        super().save(*args, **kwargs)
    
    @property
    def is_active(self):
        """Check if escrow is currently active (locked)."""
        return self.status == 'locked'
    
    @property
    def is_pending(self):
        """Check if escrow is pending setup."""
        return self.status == 'pending'
    
    @property
    def can_be_released(self):
        """Check if escrow can be released."""
        return (
            self.status == 'locked' and
            hasattr(self.request, 'status') and
            self.request.status in ['delivered', 'completed']
        )
    
    def can_transition_to(self, new_status):
        """Check if escrow can transition to the given status."""
        return new_status in self.VALID_STATUS_TRANSITIONS.get(self.status, [])
    
    @transaction.atomic
    def simulate_payment_processing(self, user=None):
        """
        Simulate payment processing for escrow.
        
        Args:
            user (User, optional): User processing the payment
            
        Returns:
            dict: Result of payment simulation
        """
        if not self.can_transition_to('locked'):
            return {
                'success': False,
                'error': f'Cannot process payment from {self.status} status'
            }
        
        # Simulate payment processing delay
        import time
        import random
        
        # Simulate 90% success rate
        if random.random() < 0.9:
            self.status = 'locked'
            self.locked_at = timezone.now()
            self.notes = f"Payment simulated successfully via {self.get_payment_method_display()}"
            
            if user:
                self._current_user = user
            self.save()
            
            return {
                'success': True,
                'message': 'Funds successfully locked in escrow',
                'payment_reference': self.payment_reference,
                'locked_at': self.locked_at
            }
        else:
            self.status = 'failed'
            self.notes = "Simulated payment failure"
            
            if user:
                self._current_user = user
            self.save()
            
            return {
                'success': False,
                'error': 'Payment processing failed',
                'payment_reference': self.payment_reference
            }
    
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
        
        # Update request status to completed if it has the method
        if hasattr(self.request, 'change_status'):
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
        
        # Update request status to disputed if it has the method
        if hasattr(self.request, 'change_status'):
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
        
        # Update request status to cancelled if it has the method
        if hasattr(self.request, 'change_status'):
            self.request.change_status('cancelled', user)
        
        return True
    
    @classmethod
    def create_for_request(cls, request, amount, payment_method, escrow_fee=None, user=None):
        """
        Create an escrow transaction for a request.
        
        Args:
            request: The Request instance
            amount: Amount to lock in escrow
            payment_method: Payment method for escrow
            escrow_fee: Escrow service fee (calculated if not provided)
            user: User creating the escrow
            
        Returns:
            EscrowTransaction: The created escrow transaction
        """
        # Calculate escrow fee if not provided (2.9% + $0.30)
        if escrow_fee is None:
            escrow_fee = (amount * Decimal('0.029')) + Decimal('0.30')
        
        escrow = cls(
            request=request,
            amount=amount,
            payment_method=payment_method,
            escrow_fee=escrow_fee,
            total_amount=amount + escrow_fee
        )
        
        if user:
            escrow._current_user = user
        
        escrow.save()
        return escrow
    
    def get_status_info(self):
        """Get detailed status information."""
        status_info = {
            'status': self.status,
            'status_display': self.get_status_display(),
            'can_be_released': self.can_be_released,
            'is_active': self.is_active,
            'is_pending': self.is_pending,
        }
        
        if self.status == 'locked':
            status_info['locked_duration'] = timezone.now() - self.locked_at
        elif self.status == 'released':
            status_info['total_duration'] = self.released_at - self.locked_at
        
        return status_info