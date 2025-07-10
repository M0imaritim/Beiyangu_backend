"""Utility functions for escrow operations."""
from decimal import Decimal
from .services import EscrowService


def create_escrow_for_request(request, payment_method, user=None):
    """
    Help function to create escrow for a request.

    Args:
        request: Request instance
        payment_method: Payment method string
        user: User creating the escrow

    Returns:
        tuple: (success, escrow_or_error)
    """
    escrow, result = EscrowService.create_escrow_for_request(
        request, payment_method, user
    )

    if result['success']:
        return True, escrow
    else:
        return False, result['error']


def get_escrow_fee_estimate(amount):
    """
    Get estimated escrow fee for an amount.

    Args:
        amount: Amount to calculate fee for

    Returns:
        dict: Fee breakdown
    """
    fee = EscrowService.calculate_escrow_fee(Decimal(str(amount)))
    total = Decimal(str(amount)) + fee

    return {
        'amount': amount,
        'fee': fee,
        'total': total,
        'fee_percentage': '2.9%',
        'fixed_fee': '$0.30'
    }
