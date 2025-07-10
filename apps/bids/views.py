"""
Bid views for the Beiyangu marketplace.

This module provides bid management functionality including
creation, updates, and acceptance.
"""
from django.shortcuts import get_object_or_404
from rest_framework import status, generics, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import Bid
from .serializers import BidSerializer, BidCreateUpdateSerializer
from .permissions import IsBidOwnerOrReadOnly
from apps.user_requests.models import Request


class BidViewSet(ModelViewSet):
    """
    ViewSet for managing bids.

    Provides CRUD operations for bids with proper permissions
    and business logic validation.
    """

    serializer_class = BidSerializer
    permission_classes = [permissions.IsAuthenticated, IsBidOwnerOrReadOnly]

    def get_queryset(self):
        """Return user's bids with related data."""
        return Bid.objects.select_related('request', 'seller').filter(
            seller=self.request.user,
            is_deleted=False
        ).order_by('-created_at')

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action in ['create', 'update', 'partial_update']:
            return BidCreateUpdateSerializer
        return BidSerializer

    def create(self, request, *args, **kwargs):
        """Create a new bid (handled by RequestBidView)."""
        return Response({
            'success': False,
            'error': 'Use /api/requests/{id}/bids/ to create bids'
        }, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def update(self, request, *args, **kwargs):
        """Update a bid."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        # Check if bid can be updated
        if not instance.is_editable:
            return Response({
                'success': False,
                'error': 'This bid cannot be edited'
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(
            instance, data=request.data, partial=partial
        )
        if serializer.is_valid():
            bid = serializer.save()
            bid._current_user = request.user
            bid.save()

            return Response({
                'success': True,
                'message': 'Bid updated successfully',
                'data': {
                    'bid': BidSerializer(bid).data
                }
            })

        return Response({
            'success': False,
            'error': 'Bid update failed',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        """Soft delete a bid."""
        instance = self.get_object()

        # Check if bid can be deleted
        if not instance.is_editable:
            return Response({
                'success': False,
                'error': 'This bid cannot be deleted'
            }, status=status.HTTP_400_BAD_REQUEST)

        instance.soft_delete(request.user)

        return Response({
            'success': True,
            'message': 'Bid deleted successfully'
        }, status=status.HTTP_204_NO_CONTENT)


class RequestBidView(generics.ListCreateAPIView):
    """
    Handle bids for a specific request.

    GET /api/requests/{id}/bids/ - List bids for request
    POST /api/requests/{id}/bids/ - Create bid for request
    """

    serializer_class = BidSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return bids for the specified request."""
        request_id = self.kwargs.get('request_id')
        return Bid.objects.select_related('seller').filter(
            request_id=request_id,
            is_deleted=False
        ).order_by('amount', '-created_at')

    def get_request_object(self):
        """Get the request object."""
        request_id = self.kwargs.get('request_id')
        return get_object_or_404(Request, pk=request_id, is_deleted=False)

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.request.method == 'POST':
            return BidCreateUpdateSerializer
        return BidSerializer

    def list(self, request, *args, **kwargs):
        """List all bids for the request."""
        request_obj = self.get_request_object()

        # Only show bids to request owner or if user has bid
        user = request.user
        if (request_obj.buyer != user and
                not self.get_queryset().filter(seller=user).exists()):
            return Response({
                'success': False,
                'error': ('You can only view bids on your own requests or '
                          'requests you have bid on')
            }, status=status.HTTP_403_FORBIDDEN)

        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        return Response({
            'success': True,
            'data': {
                'bids': serializer.data,
                'request': {
                    'id': request_obj.id,
                    'title': request_obj.title,
                    'budget': request_obj.budget,
                    'status': request_obj.status
                }
            }
        })

    def create(self, request, *args, **kwargs):
        """Create a new bid for the request."""
        request_obj = self.get_request_object()

        # Check if request can receive bids
        if not request_obj.can_be_bid_on():
            return Response({
                'success': False,
                'error': 'This request is not open for bidding'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if user already has a bid on this request
        existing_bid = Bid.objects.filter(
            request=request_obj,
            seller=request.user,
            is_deleted=False
        ).first()

        if existing_bid:
            return Response({
                'success': False,
                'error': 'You already have a bid on this request'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Pass request_obj to serializer context
        serializer = self.get_serializer(
            data=request.data,
            context={'request': request, 'request_obj': request_obj}
        )
        if serializer.is_valid():
            bid = serializer.save()
            bid._current_user = request.user
            bid.save()

            return Response({
                'success': True,
                'message': 'Bid submitted successfully',
                'data': {
                    'bid': BidSerializer(bid).data
                }
            }, status=status.HTTP_201_CREATED)

        return Response({
            'success': False,
            'error': 'Bid creation failed',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class BidAcceptView(generics.UpdateAPIView):
    """
    Handle bid acceptance.

    POST /api/bids/{id}/accept/
    """

    queryset = Bid.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """Accept a bid."""
        bid = self.get_object()

        # Check if user is the request owner
        if bid.request.buyer != request.user:
            return Response({
                'success': False,
                'error': 'Only the request owner can accept bids'
            }, status=status.HTTP_403_FORBIDDEN)

        # Check if bid can be accepted
        if not bid.can_be_accepted():
            return Response({
                'success': False,
                'error': 'This bid cannot be accepted'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Accept the bid
        success = bid.request.accept_bid(bid, request.user)
        if success:
            return Response({
                'success': True,
                'message': 'Bid accepted successfully',
                'data': {
                    'bid': BidSerializer(bid).data,
                    'request_status': bid.request.status
                }
            })

        return Response({
            'success': False,
            'error': 'Failed to accept bid'
        }, status=status.HTTP_400_BAD_REQUEST)
