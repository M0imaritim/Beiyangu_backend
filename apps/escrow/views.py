from rest_framework import viewsets, serializers, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import models
from django.shortcuts import get_object_or_404
from .models import EscrowTransaction
from .serializers import EscrowTransactionSerializer, EscrowActionSerializer
from apps.user_requests.models import Request

class EscrowTransactionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for escrow transactions.
    Supports CRUD operations for escrow transactions.
    """
    queryset = EscrowTransaction.objects.all()
    serializer_class = EscrowTransactionSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'public_id'

    def get_queryset(self):
        """Filter escrow transactions by user."""
        user = self.request.user
        return EscrowTransaction.objects.filter(
            models.Q(request__user=user) | 
            models.Q(request__accepted_bid__user=user)
        ).distinct()

    def perform_create(self, serializer):
        """Validate and create an EscrowTransaction."""
        request_id = self.request.data.get('request')
        try:
            request_obj = Request.objects.get(id=request_id, user=self.request.user)
        except Request.DoesNotExist:
            raise serializers.ValidationError("Invalid request ID or not owned by user.")
        serializer.save(buyer=self.request.user, request=request_obj)

    @action(detail=True, methods=['post'])
    def perform_action(self, request, public_id=None):
        """
        Perform escrow action (release, hold, refund).
        """
        escrow = get_object_or_404(EscrowTransaction, public_id=public_id)
        if not (request.user == escrow.request.user or 
                (hasattr(escrow.request, 'accepted_bid') and 
                 request.user == escrow.request.accepted_bid.user)):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = EscrowActionSerializer(
            data=request.data,
            context={'escrow': escrow}
        )
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        action_type = serializer.validated_data['action']
        notes = serializer.validated_data.get('notes', '')
        if action_type == 'release':
            success = escrow.release_funds(request.user, notes)
        elif action_type == 'hold':
            success = escrow.hold_for_dispute(request.user, notes)
        elif action_type == 'refund':
            success = escrow.refund_funds(request.user, notes)
        else:
            return Response(
                {'error': 'Invalid action'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if success:
            return Response({
                'success': True,
                'message': f'Escrow {action_type} successful',
                'escrow': EscrowTransactionSerializer(escrow).data
            })
        else:
            return Response(
                {'error': f'Failed to {action_type} escrow'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['get'])
    def status(self, request, public_id=None):
        """
        Get detailed status of escrow transaction.
        """
        escrow = get_object_or_404(EscrowTransaction, public_id=public_id)
        return Response({
            'escrow': EscrowTransactionSerializer(escrow).data,
            'status_info': escrow.get_status_info()
        })