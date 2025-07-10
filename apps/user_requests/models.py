"""
Request model for the Beiyangu marketplace.

This module defines the core Request model that represents buyer requests
in the reverse marketplace system.
"""
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone
import uuid

User = get_user_model()


class RequestCategory(models.Model):
    """Model for organizing request categories."""

    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Category name"
    )
    description = models.TextField(
        blank=True,
        help_text="Category description"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this category is active"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Meta options for RequestCategory model."""
    
        verbose_name_plural = "Request Categories"
        ordering = ['name']

    def __str__(self):
        """Return string representation of the category."""
        return self.name


class Request(models.Model):
    """
    Model representing a buyer's request in the marketplace.

    Buyers create requests with a description and budget, and sellers
    can bid on these requests. The request progresses through various
    statuses as it moves through the marketplace workflow.
    """

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('accepted', 'Accepted'),
        ('delivered', 'Delivered'),
        ('completed', 'Completed'),
        ('disputed', 'Disputed'),
        ('pending_escrow', 'Pending Escrow'),
        ('cancelled', 'Cancelled'),
    ]

    # Valid status transitions
    VALID_STATUS_TRANSITIONS = {
        'open': ['accepted', 'cancelled'],
        'accepted': ['delivered', 'disputed', 'cancelled'],
        'delivered': ['completed', 'disputed'],
        'disputed': ['completed', 'cancelled'],
        'completed': [],  # Terminal state
        'cancelled': [],  # Terminal state
    }

    # Public ID for external references
    public_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        help_text="Public identifier for this request"
    )
    title = models.CharField(
        max_length=200,
        help_text="Brief title describing what the buyer needs"
    )
    description = models.TextField(
        help_text="Detailed description of the request"
    )
    budget = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Maximum amount buyer is willing to pay"
    )
    buyer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='requests',
        help_text="User who created this request"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='open',
        help_text="Current status of the request"
    )
    category = models.ForeignKey(
        RequestCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='requests',
        help_text="Category of service requested"
    )
    deadline = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the buyer needs this completed"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this request is active and visible"
    )
    is_deleted = models.BooleanField(
        default=False,
        help_text="Soft delete flag"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this request was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When this request was last modified"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_requests',
        help_text="User who created this record"
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='updated_requests',
        help_text="User who last updated this record"
    )

    class Meta:
        """Meta options for Request model."""

        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'is_active', 'is_deleted']),
            models.Index(fields=['buyer', 'status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['public_id']),
            models.Index(fields=['category', 'is_active']),
        ]

    def __str__(self):
        """Return string representation of the request."""
        return f"{self.title} - {self.get_status_display()}"

    def clean(self):
        """Validate the request data."""
        super().clean()

        # Validate deadline is in the future
        if self.deadline and self.deadline <= timezone.now():
            raise ValidationError("Deadline must be in the future")

        # Validate budget is reasonable
        if self.budget <= 0:
            raise ValidationError("Budget must be greater than zero")

    def save(self, *args, **kwargs):
        """Override save to run validation and set audit fields."""
        # Remove any invalid kwargs that might be passed
        kwargs.pop('commit', None)

        # Run model validation (but catch ValidationError to handle it
        # gracefully)
        try:
            self.full_clean()
        except ValidationError as e:
            # Only run full_clean if we're not in a migration or bulk operation
            if not kwargs.get(
                    'force_insert',
                    False) and not kwargs.get(
                    'force_update',
                    False):
                raise e

        # Set created_by on first save
        if not self.pk and hasattr(
                self, '_current_user') and self._current_user:
            self.created_by = self._current_user

        # Always set updated_by if user is available
        if hasattr(self, '_current_user') and self._current_user:
            self.updated_by = self._current_user

        super().save(*args, **kwargs)

    @property
    def is_open(self):
        """Check if request is open for bidding."""
        return self.status == 'open' and self.is_active and not self.is_deleted

    @property
    def bid_count(self):
        """Get the number of bids on this request."""
        return self.bids.filter(is_deleted=False).count()

    @property
    def accepted_bid(self):
        """Get the accepted bid for this request, if any."""
        return self.bids.filter(is_accepted=True, is_deleted=False).first()

    @property
    def is_expired(self):
        """Check if request has passed its deadline."""
        return self.deadline and self.deadline <= timezone.now()

    def can_be_bid_on(self):
        """Check if this request can receive new bids."""
        return (
            self.is_open and
            self.is_active and
            not self.is_deleted and
            not self.is_expired
        )

    def can_transition_to(self, new_status):
        """Check if request can transition to the given status."""
        return new_status in self.VALID_STATUS_TRANSITIONS.get(self.status, [])

    def change_status(self, new_status, user=None):
        """
        Change request status with validation.

        Args:
            new_status (str): New status to transition to
            user (User, optional): User making the change

        Returns:
            bool: True if status was changed successfully
        """
        if not self.can_transition_to(new_status):
            return False

        old_status = self.status
        self.status = new_status

        if user:
            self._current_user = user

        self.save()

        # Log status change (you might want to implement a StatusLog model)
        # StatusLog.objects.create(
        #     request=self,
        #     old_status=old_status,
        #     new_status=new_status,
        #     changed_by=user
        # )

        return True

    @transaction.atomic
    def accept_bid(self, bid, user=None):
        """
        Accept a bid for this request.

        Args:
            bid: The Bid instance to accept
            user: User accepting the bid

        Returns:
            bool: True if bid was successfully accepted
        """
        if not self.can_be_bid_on():
            return False

        if bid.request != self:
            return False

        if not bid.can_be_accepted():
            return False

        # Mark the bid as accepted
        bid.is_accepted = True
        if user:
            bid._current_user = user
        bid.save()

        # Update request status
        if not self.change_status('accepted', user):
            return False

        # Create escrow transaction
        from apps.escrow.models import EscrowTransaction
        EscrowTransaction.create_for_bid_acceptance(
            self, bid, payment_method='credit_card',)

        return True

    def soft_delete(self, user=None):
        """Soft delete the request."""
        self.is_deleted = True
        self.is_active = False
        if user:
            self._current_user = user
        self.save()
