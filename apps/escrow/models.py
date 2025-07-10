"""
Escrow transaction model for the Beiyangu marketplace.

This module defines the EscrowTransaction model that handles
the simulated escrow system for secure payments with proper
bid acceptance workflow.
"""
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone
import uuid
import random
import time

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
        ('apple_pay', 'Apple Pay'),
        ('google_pay', 'Google Pay'),
        ('stripe', 'Stripe'),
    ]
    
    # Valid status transitions
    VALID_STATUS_TRANSITIONS = {
        'pending': ['locked', 'failed'],
        'locked': ['released', 'held', 'refunded'],
        'held': ['released', 'refunded'],
        'released': [],  # Terminal state
        'refunded': [],  # Terminal state
        'failed': ['pending'],    # Allow retry
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
    bid = models.OneToOneField(
        'bids.Bid',
        on_delete=models.CASCADE,
        related_name='escrow',
        null=True,
        blank=True,
        help_text="The accepted bid this escrow is for"
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
        max_length=50,
        choices=PAYMENT_METHOD_CHOICES,
        default='credit_card',
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
    payment_token = models.CharField(
        max_length=100,
        blank=True,
        help_text="Simulated payment token"
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
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When escrow expires if not completed"
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
            models.Index(fields=['payment_method']),
        ]
    
    def __str__(self):
        """Return string representation of the escrow transaction."""
        return f"Escrow ${self.amount} ({self.payment_method}) - {self.get_status_display()}"
    
    def clean(self):
        """Validate the escrow data."""
        super().clean()
        
        # Calculate total amount
        if self.amount and self.escrow_fee:
            calculated_total = self.amount + self.escrow_fee
            if self.total_amount != calculated_total:
                self.total_amount = calculated_total
        
        # Validate bid belongs to request
        if self.bid and self.bid.request != self.request:
            raise ValidationError("Bid must belong to the associated request")
    
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
        
        # Generate payment token if not set
        if not self.payment_token:
            self.payment_token = f"tok_{uuid.uuid4().hex[:16]}"
        
        # Set expiration (30 days from creation)
        if not self.expires_at and not self.pk:
            self.expires_at = timezone.now() + timezone.timedelta(days=30)
        
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
    def is_expired(self):
        """Check if escrow has expired."""
        return self.expires_at and timezone.now() > self.expires_at
    
    @property
    def can_be_released(self):
        """Check if escrow can be released."""
        return (
            self.status == 'locked' and
            hasattr(self.request, 'status') and
            self.request.status in ['delivered', 'completed']
        )
    
    @property
    def can_be_refunded(self):
        """Check if escrow can be refunded."""
        return self.status in ['locked', 'held']
    
    def can_transition_to(self, new_status):
        """Check if escrow can transition to the given status."""
        return new_status in self.VALID_STATUS_TRANSITIONS.get(self.status, [])
    
    def get_payment_processor_details(self):
        """Get simulated payment processor details."""
        processors = {
            'credit_card': 'Stripe Payment Processing',
            'debit_card': 'Stripe Payment Processing',
            'bank_transfer': 'ACH Processing Network',
            'paypal': 'PayPal Payment System',
            'apple_pay': 'Apple Pay via Stripe',
            'google_pay': 'Google Pay via Stripe',
            'stripe': 'Stripe Direct Processing',
        }
        return processors.get(self.payment_method, 'Generic Payment Processor')
    
    @transaction.atomic
    def simulate_payment_processing(self, user=None, payment_details=None):
        """
        Simulate payment processing for escrow.
        
        Args:
            user (User, optional): User processing the payment
            payment_details (dict, optional): Payment method details
            
        Returns:
            dict: Result of payment simulation
        """
        if not self.can_transition_to('locked'):
            return {
                'success': False,
                'error': f'Cannot process payment from {self.status} status'
            }
        
        # Simulate payment processing delay
        processing_time = random.uniform(1, 3)  # 1-3 seconds
        time.sleep(processing_time)
        
        # Different success rates by payment method
        success_rates = {
            'credit_card': 0.95,
            'debit_card': 0.92,
            'bank_transfer': 0.88,
            'paypal': 0.94,
            'apple_pay': 0.97,
            'google_pay': 0.96,
            'stripe': 0.96,
        }
        
        success_rate = success_rates.get(self.payment_method, 0.90)
        
        if random.random() < success_rate:
            self.status = 'locked'
            self.locked_at = timezone.now()
            self.notes = f"Payment processed successfully via {self.get_payment_method_display()}"
            
            # Add payment details to notes if provided
            if payment_details:
                self.notes += f"\nPayment Details: {payment_details}"
            
            if user:
                self._current_user = user
            self.save()
            
            return {
                'success': True,
                'message': 'Funds successfully locked in escrow',
                'payment_reference': self.payment_reference,
                'payment_token': self.payment_token,
                'locked_at': self.locked_at,
                'processor': self.get_payment_processor_details(),
                'processing_time': f"{processing_time:.2f}s"
            }
        else:
            self.status = 'failed'
            error_messages = [
                'Insufficient funds',
                'Payment method declined',
                'Card expired',
                'Invalid payment details',
                'Transaction limit exceeded'
            ]
            error_message = random.choice(error_messages)
            self.notes = f"Payment failed: {error_message}"
            
            if user:
                self._current_user = user
            self.save()
            
            return {
                'success': False,
                'error': f'Payment processing failed: {error_message}',
                'payment_reference': self.payment_reference,
                'processor': self.get_payment_processor_details(),
                'processing_time': f"{processing_time:.2f}s"
            }
    
    @transaction.atomic
    def release_funds(self, user=None, notes=None):
        """
        Release funds from escrow.
        
        Args:
            user (User, optional): User releasing the funds
            notes (str, optional): Additional notes for the release
            
        Returns:
            dict: Result of fund release
        """
        if not self.can_be_released:
            return {
                'success': False,
                'error': f'Cannot release funds. Current status: {self.status}, Request status: {self.request.status}'
            }
        
        if not self.can_transition_to('released'):
            return {
                'success': False,
                'error': f'Cannot transition from {self.status} to released'
            }
        
        self.status = 'released'
        self.released_at = timezone.now()
        
        release_notes = f"Funds released to seller"
        if notes:
            release_notes += f". {notes}"
        
        self.notes = release_notes
        
        if user:
            self._current_user = user
        self.save()
        
        # Update request status to completed
        if hasattr(self.request, 'change_status'):
            self.request.change_status('completed', user)
        
        return {
            'success': True,
            'message': 'Funds successfully released to seller',
            'released_at': self.released_at,
            'amount': self.amount,
            'payment_reference': self.payment_reference
        }
    
    @transaction.atomic
    def hold_for_dispute(self, user=None, notes=None):
        """
        Hold funds in escrow due to dispute.
        
        Args:
            user (User, optional): User initiating the hold
            notes (str, optional): Reason for holding funds
            
        Returns:
            dict: Result of hold action
        """
        if not self.can_transition_to('held'):
            return {
                'success': False,
                'error': f'Cannot hold funds from {self.status} status'
            }
        
        self.status = 'held'
        
        hold_notes = "Funds held due to dispute"
        if notes:
            hold_notes += f". Reason: {notes}"
        
        self.notes = hold_notes
        
        if user:
            self._current_user = user
        self.save()
        
        # Update request status to disputed
        if hasattr(self.request, 'change_status'):
            self.request.change_status('disputed', user)
        
        return {
            'success': True,
            'message': 'Funds held for dispute resolution',
            'held_at': timezone.now(),
            'amount': self.amount,
            'payment_reference': self.payment_reference
        }
    
    @transaction.atomic
    def refund_funds(self, user=None, notes=None):
        """
        Refund funds from escrow.
        
        Args:
            user (User, optional): User processing the refund
            notes (str, optional): Reason for refund
            
        Returns:
            dict: Result of refund
        """
        if not self.can_be_refunded:
            return {
                'success': False,
                'error': f'Cannot refund funds from {self.status} status'
            }
        
        if not self.can_transition_to('refunded'):
            return {
                'success': False,
                'error': f'Cannot transition from {self.status} to refunded'
            }
        
        self.status = 'refunded'
        self.released_at = timezone.now()
        
        refund_notes = f"Funds refunded to buyer"
        if notes:
            refund_notes += f". Reason: {notes}"
        
        self.notes = refund_notes
        
        if user:
            self._current_user = user
        self.save()
        
        # Update request status to cancelled
        if hasattr(self.request, 'change_status'):
            self.request.change_status('cancelled', user)
        
        return {
            'success': True,
            'message': 'Funds successfully refunded to buyer',
            'refunded_at': self.released_at,
            'amount': self.total_amount,  # Include fees in refund
            'payment_reference': self.payment_reference
        }
    
    @classmethod
    def create_for_bid_acceptance(cls, request, bid, payment_method='credit_card', escrow_fee=None, user=None):
        """
        Create an escrow transaction when a bid is accepted.
        
        Args:
            request: The Request instance
            bid: The accepted Bid instance
            payment_method: Payment method for escrow
            escrow_fee: Escrow service fee (calculated if not provided)
            user: User creating the escrow
            
        Returns:
            EscrowTransaction: The created escrow transaction
        """
        # Calculate escrow fee if not provided (2.9% + $0.30)
        if escrow_fee is None:
            escrow_fee = (bid.amount * Decimal('0.029')) + Decimal('0.30')
        
        escrow = cls(
            request=request,
            bid=bid,
            amount=bid.amount,
            payment_method=payment_method,
            escrow_fee=escrow_fee,
            total_amount=bid.amount + escrow_fee
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
            'can_be_refunded': self.can_be_refunded,
            'is_active': self.is_active,
            'is_pending': self.is_pending,
            'is_expired': self.is_expired,
            'payment_method': self.payment_method,
            'payment_method_display': self.get_payment_method_display(),
            'processor': self.get_payment_processor_details(),
            'amount': str(self.amount),
            'escrow_fee': str(self.escrow_fee),
            'total_amount': str(self.total_amount),
            'payment_reference': self.payment_reference,
            'expires_at': self.expires_at,
        }
        
        if self.status == 'locked' and self.locked_at:
            status_info['locked_duration'] = str(timezone.now() - self.locked_at)
        elif self.status == 'released' and self.released_at and self.locked_at:
            status_info['total_duration'] = str(self.released_at - self.locked_at)
        
        return status_info