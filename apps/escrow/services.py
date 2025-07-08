"""
Services for escrow functionality.
"""
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from .models import EscrowTransaction


class EscrowService:
    """Service class for handling escrow operations."""
    
    @staticmethod
    def calculate_escrow_fee(amount):
        """
        Calculate escrow fee based on amount.
        
        Args:
            amount (Decimal): Base amount
            
        Returns:
            Decimal: Calculated escrow fee
        """
        # Standard rate: 2.9% + $0.30
        return (amount * Decimal('0.029')) + Decimal('0.30')
    
    @staticmethod
    @transaction.atomic
    def create_escrow_for_request(request, payment_method, user=None):
        """
        Create escrow transaction for a request.
        
        Args:
            request: Request instance
            payment_method: Payment method string
            user: User creating the escrow
            
        Returns:
            tuple: (EscrowTransaction, dict) - escrow instance and result
        """
        try:
            # Get amount from request budget
            amount = Decimal(str(request.budget))
            
            # Calculate escrow fee
            escrow_fee = EscrowService.calculate_escrow_fee(amount)
            
            # Create escrow transaction
            escrow = EscrowTransaction.create_for_request(
                request=request,
                amount=amount,
                payment_method=payment_method,
                escrow_fee=escrow_fee,
                user=user
            )
            
            # Simulate payment processing
            payment_result = escrow.simulate_payment_processing(user)
            
            return escrow, {
                'success': True,
                'escrow_id': escrow.public_id,
                'payment_result': payment_result,
                'total_amount': escrow.total_amount,
                'escrow_fee': escrow_fee
            }
            
        except Exception as e:
            return None, {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def get_escrow_status(request):
        """
        Get escrow status for a request.
        
        Args:
            request: Request instance
            
        Returns:
            dict: Escrow status information
        """
        try:
            escrow = request.escrow
            return {
                'has_escrow': True,
                'escrow_id': escrow.public_id,
                'status': escrow.status,
                'amount': escrow.amount,
                'fee': escrow.escrow_fee,
                'total': escrow.total_amount,
                'payment_method': escrow.get_payment_method_display(),
                'created_at': escrow.created_at,
                'locked_at': escrow.locked_at,
                'can_be_released': escrow.can_be_released,
                'is_active': escrow.is_active
            }
        except EscrowTransaction.DoesNotExist:
            return {
                'has_escrow': False
            }