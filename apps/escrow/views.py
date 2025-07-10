"""
Escrow views with proper payment method handling and cURL support.
"""
from rest_framework import viewsets, serializers, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import models
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import EscrowTransaction
from .serializers import EscrowTransactionSerializer, EscrowActionSerializer
from apps.user_requests.models import Request
from apps.bids.models import Bid


class EscrowTransactionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for escrow transactions.
    Supports CRUD operations and escrow management.
    """
    queryset = EscrowTransaction.objects.all()
    serializer_class = EscrowTransactionSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'public_id'

    def get_queryset(self):
        """Filter escrow transactions by user."""
        user = self.request.user
        return EscrowTransaction.objects.filter(
            models.Q(request__buyer=user) | 
            models.Q(bid__seller=user)
        ).select_related('request', 'bid', 'request__buyer', 'bid__seller').distinct()

    @action(detail=False, methods=['post'])
    def create_for_bid(self, request):
        """
        Create escrow transaction when accepting a bid.
        
        POST /api/escrow/create_for_bid/
        {
            "bid_id": 123,
            "payment_method": "credit_card",
            "payment_details": {
                "card_number": "****1234",
                "card_type": "visa"
            }
        }
        """
        bid_id = request.data.get('bid_id')
        payment_method = request.data.get('payment_method', 'credit_card')
        payment_details = request.data.get('payment_details', {})
        
        if not bid_id:
            return Response({
                'success': False,
                'error': 'bid_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            bid = Bid.objects.select_related('request').get(id=bid_id)
        except Bid.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Bid not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if user is the request buyer
        if bid.request.buyer != request.user:
            return Response({
                'success': False,
                'error': 'Only the request buyer can create escrow'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Check if bid can be accepted
        if not bid.can_be_accepted():
            return Response({
                'success': False,
                'error': 'Bid cannot be accepted'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if escrow already exists
        if hasattr(bid.request, 'escrow'):
            return Response({
                'success': False,
                'error': 'Escrow already exists for this request'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate payment method
        valid_methods = [choice[0] for choice in EscrowTransaction.PAYMENT_METHOD_CHOICES]
        if payment_method not in valid_methods:
            return Response({
                'success': False,
                'error': f'Invalid payment method. Valid options: {valid_methods}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Create escrow transaction
            escrow = EscrowTransaction.create_for_bid_acceptance(
                request=bid.request,
                bid=bid,
                payment_method=payment_method,
                user=request.user
            )
            
            # Accept the bid
            bid.is_accepted = True
            bid._current_user = request.user
            bid.save()
            
            # Change request status to accepted
            bid.request.change_status('accepted', request.user)
            
            # Process payment
            payment_result = escrow.simulate_payment_processing(
                user=request.user,
                payment_details=payment_details
            )
            
            if payment_result['success']:
                return Response({
                    'success': True,
                    'message': 'Escrow created and payment processed successfully',
                    'data': {
                        'escrow': EscrowTransactionSerializer(escrow).data,
                        'payment_result': payment_result
                    }
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'success': False,
                    'error': 'Escrow created but payment failed',
                    'data': {
                        'escrow': EscrowTransactionSerializer(escrow).data,
                        'payment_result': payment_result
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Failed to create escrow: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def process_payment(self, request, public_id=None):
        """
        Process payment for pending escrow.
        
        POST /api/escrow/{public_id}/process_payment/
        {
            "payment_method": "paypal",
            "payment_details": {
                "paypal_email": "user@example.com"
            }
        }
        """
        escrow = get_object_or_404(EscrowTransaction, public_id=public_id)
        
        # Check permissions
        if request.user != escrow.request.buyer:
            return Response({
                'success': False,
                'error': 'Only the buyer can process payment'
            }, status=status.HTTP_403_FORBIDDEN)
        
        if escrow.status != 'pending' and escrow.status != 'failed':
            return Response({
                'success': False,
                'error': f'Cannot process payment for escrow in {escrow.status} status'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update payment method if provided
        payment_method = request.data.get('payment_method')
        if payment_method:
            valid_methods = [choice[0] for choice in EscrowTransaction.PAYMENT_METHOD_CHOICES]
            if payment_method not in valid_methods:
                return Response({
                    'success': False,
                    'error': f'Invalid payment method. Valid options: {valid_methods}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            escrow.payment_method = payment_method
            escrow.save()
        
        payment_details = request.data.get('payment_details', {})
        
        # Process payment
        payment_result = escrow.simulate_payment_processing(
            user=request.user,
            payment_details=payment_details
        )
        
        if payment_result['success']:
            return Response({
                'success': True,
                'message': 'Payment processed successfully',
                'data': {
                    'escrow': EscrowTransactionSerializer(escrow).data,
                    'payment_result': payment_result
                }
            })
        else:
            return Response({
                'success': False,
                'error': 'Payment processing failed',
                'data': {
                    'escrow': EscrowTransactionSerializer(escrow).data,
                    'payment_result': payment_result
                }
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def perform_action(self, request, public_id=None):
        """
        Perform escrow action (release, hold, refund).
        
        POST /api/escrow/{public_id}/perform_action/
        {
            "action": "release",
            "notes": "Service completed satisfactorily"
        }
        """
        escrow = get_object_or_404(EscrowTransaction, public_id=public_id)
        
        # Check permissions based on action
        action_type = request.data.get('action')
        if action_type == 'release':
            # Only buyer can release funds
            if request.user != escrow.request.buyer:
                return Response({
                    'success': False,
                    'error': 'Only the buyer can release funds'
                }, status=status.HTTP_403_FORBIDDEN)
        elif action_type in ['hold', 'refund']:
            # Both buyer and seller can initiate hold/refund
            if request.user not in [escrow.request.buyer, escrow.bid.seller if escrow.bid else None]:
                return Response({
                    'success': False,
                    'error': 'Permission denied'
                }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = EscrowActionSerializer(
            data=request.data,
            context={'escrow': escrow}
        )
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': 'Invalid action data',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        action_type = serializer.validated_data['action']
        notes = serializer.validated_data.get('notes', '')
        
        # Perform the action
        if action_type == 'release':
            result = escrow.release_funds(request.user, notes)
        elif action_type == 'hold':
            result = escrow.hold_for_dispute(request.user, notes)
        elif action_type == 'refund':
            result = escrow.refund_funds(request.user, notes)
        else:
            return Response({
                'success': False,
                'error': 'Invalid action'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if result['success']:
            return Response({
                'success': True,
                'message': result['message'],
                'data': {
                    'escrow': EscrowTransactionSerializer(escrow).data,
                    'action_result': result
                }
            })
        else:
            return Response({
                'success': False,
                'error': result['error'],
                'data': {
                    'escrow': EscrowTransactionSerializer(escrow).data
                }
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def status(self, request, public_id=None):
        """
        Get detailed status of escrow transaction.
        
        GET /api/escrow/{public_id}/status/
        """
        escrow = get_object_or_404(EscrowTransaction, public_id=public_id)
        
        # Check permissions
        if request.user not in [escrow.request.buyer, escrow.bid.seller if escrow.bid else None]:
            return Response({
                'success': False,
                'error': 'Permission denied'
            }, status=status.HTTP_403_FORBIDDEN)
        
        return Response({
            'success': True,
            'data': {
                'escrow': EscrowTransactionSerializer(escrow).data,
                'status_info': escrow.get_status_info()
            }
        })

    @action(detail=False, methods=['get'])
    def payment_methods(self, request):
        """
        Get available payment methods.
        
        GET /api/escrow/payment_methods/
        """
        payment_methods = []
        
        for method_code, method_label in EscrowTransaction.PAYMENT_METHOD_CHOICES:
            method_info = {
                'value': method_code,
                'label': method_label,
                'processor': self._get_payment_processor(method_code),
                'required_fields': self._get_required_payment_fields(method_code),
                'supported_currencies': self._get_supported_currencies(method_code)
            }
            payment_methods.append(method_info)
        
        return Response({
            'success': True,
            'data': {
                'payment_methods': payment_methods,
                'default_method': 'credit_card'
            }
        })

    def _get_payment_processor(self, method_code):
        """Get the payment processor for a specific method."""
        processor_mapping = {
            'credit_card': 'stripe',
            'debit_card': 'stripe',
            'paypal': 'paypal',
            'bank_transfer': 'stripe_ach',
            'mobile_money': 'mobile_payment_gateway',
            'cryptocurrency': 'crypto_processor'
        }
        return processor_mapping.get(method_code, 'unknown')

    def _get_required_payment_fields(self, method_code):
        """Get required fields for a payment method."""
        field_mapping = {
            'credit_card': ['card_number', 'expiry_date', 'cvv', 'cardholder_name'],
            'debit_card': ['card_number', 'expiry_date', 'cvv', 'cardholder_name'],
            'paypal': ['paypal_email'],
            'bank_transfer': ['account_number', 'routing_number', 'account_holder_name'],
            'mobile_money': ['mobile_number', 'network_provider'],
            'cryptocurrency': ['wallet_address', 'crypto_type']
        }
        return field_mapping.get(method_code, [])

    def _get_supported_currencies(self, method_code):
        """Get supported currencies for a payment method."""
        currency_mapping = {
            'credit_card': ['USD', 'EUR', 'GBP', 'KES', 'UGX', 'TZS'],
            'debit_card': ['USD', 'EUR', 'GBP', 'KES', 'UGX', 'TZS'],
            'paypal': ['USD', 'EUR', 'GBP'],
            'bank_transfer': ['USD', 'EUR', 'GBP', 'KES'],
            'mobile_money': ['KES', 'UGX', 'TZS'],
            'cryptocurrency': ['BTC', 'ETH', 'USDT']
        }
        return currency_mapping.get(method_code, ['USD'])

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get escrow statistics for the current user.
        
        GET /api/escrow/statistics/
        """
        user = request.user
        queryset = self.get_queryset()
        
        # Calculate statistics
        total_escrows = queryset.count()
        pending_escrows = queryset.filter(status='pending').count()
        funded_escrows = queryset.filter(status='funded').count()
        completed_escrows = queryset.filter(status='completed').count()
        disputed_escrows = queryset.filter(status='disputed').count()
        
        # Calculate totals by user role
        buyer_escrows = queryset.filter(request__buyer=user)
        seller_escrows = queryset.filter(bid__seller=user)
        
        # Calculate monetary totals (you may need to adjust based on your currency handling)
        from django.db.models import Sum
        total_amount = queryset.aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        return Response({
            'success': True,
            'data': {
                'overview': {
                    'total_escrows': total_escrows,
                    'pending_escrows': pending_escrows,
                    'funded_escrows': funded_escrows,
                    'completed_escrows': completed_escrows,
                    'disputed_escrows': disputed_escrows,
                    'total_amount': float(total_amount)
                },
                'by_role': {
                    'as_buyer': buyer_escrows.count(),
                    'as_seller': seller_escrows.count()
                },
                'by_status': {
                    'pending': pending_escrows,
                    'funded': funded_escrows,
                    'completed': completed_escrows,
                    'disputed': disputed_escrows,
                    'failed': queryset.filter(status='failed').count(),
                    'refunded': queryset.filter(status='refunded').count()
                }
            }
        })

    @action(detail=True, methods=['get'])
    def history(self, request, public_id=None):
        """
        Get detailed history of escrow transaction.
        
        GET /api/escrow/{public_id}/history/
        """
        escrow = get_object_or_404(EscrowTransaction, public_id=public_id)
        
        # Check permissions
        if request.user not in [escrow.request.buyer, escrow.bid.seller if escrow.bid else None]:
            return Response({
                'success': False,
                'error': 'Permission denied'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get all related history/logs if you have a logging model
        # This is a placeholder - you would implement based on your logging system
        history_entries = []
        
        # Basic history based on escrow model fields
        history_entries.append({
            'event': 'escrow_created',
            'timestamp': escrow.created_at.isoformat(),
            'description': 'Escrow transaction created',
            'details': {
                'amount': float(escrow.amount),
                'payment_method': escrow.payment_method
            }
        })
        
        if escrow.funded_at:
            history_entries.append({
                'event': 'escrow_funded',
                'timestamp': escrow.funded_at.isoformat(),
                'description': 'Escrow funded successfully',
                'details': {}
            })
        
        if escrow.completed_at:
            history_entries.append({
                'event': 'escrow_completed',
                'timestamp': escrow.completed_at.isoformat(),
                'description': 'Escrow completed and funds released',
                'details': {}
            })
        
        return Response({
            'success': True,
            'data': {
                'escrow': EscrowTransactionSerializer(escrow).data,
                'history': sorted(history_entries, key=lambda x: x['timestamp'])
            }
        })

    @action(detail=True, methods=['post'])
    def dispute(self, request, public_id=None):
        """
        Initiate dispute for an escrow transaction.
        
        POST /api/escrow/{public_id}/dispute/
        {
            "reason": "Service not delivered as agreed",
            "evidence": "Description of evidence or links to supporting documents"
        }
        """
        escrow = get_object_or_404(EscrowTransaction, public_id=public_id)
        
        # Check permissions - both buyer and seller can initiate disputes
        if request.user not in [escrow.request.buyer, escrow.bid.seller if escrow.bid else None]:
            return Response({
                'success': False,
                'error': 'Permission denied'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Check if dispute can be initiated
        if escrow.status not in ['funded', 'disputed']:
            return Response({
                'success': False,
                'error': f'Cannot initiate dispute for escrow in {escrow.status} status'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        reason = request.data.get('reason', '')
        evidence = request.data.get('evidence', '')
        
        if not reason:
            return Response({
                'success': False,
                'error': 'Dispute reason is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create dispute (you would implement this based on your dispute model)
        dispute_result = escrow.create_dispute(
            initiated_by=request.user,
            reason=reason,
            evidence=evidence
        )
        
        if dispute_result['success']:
            return Response({
                'success': True,
                'message': 'Dispute initiated successfully',
                'data': {
                    'escrow': EscrowTransactionSerializer(escrow).data,
                    'dispute': dispute_result.get('dispute_data', {})
                }
            })
        else:
            return Response({
                'success': False,
                'error': dispute_result.get('error', 'Failed to initiate dispute')
            }, status=status.HTTP_400_BAD_REQUEST)