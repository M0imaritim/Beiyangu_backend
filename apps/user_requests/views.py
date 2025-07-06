"""
Request views for the Beiyangu marketplace.

This module provides CRUD operations for buyer requests
and related functionality like delivery confirmation.
"""
from django.db.models import Count, Q, Prefetch
from django.shortcuts import get_object_or_404
from rest_framework import status, generics, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.pagination import PageNumberPagination

from .models import Request, RequestCategory
from .serializers import (
    RequestSerializer,
    RequestDetailSerializer,
    RequestCategorySerializer
)
from .permissions import IsOwnerOrReadOnly, IsRequestBuyerOrReadOnly
from apps.bids.models import Bid
from apps.bids.serializers import BidSerializer


class RequestPagination(PageNumberPagination):
    """Custom pagination for requests."""
    
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50


class RequestViewSet(ModelViewSet):
    """
    ViewSet for managing requests.
    
    Provides CRUD operations for requests with proper permissions
    and filtering capabilities.
    """
    
    # Add the queryset attribute that was missing
    queryset = Request.objects.select_related('buyer', 'category').annotate(
        bid_count=Count('bids', filter=Q(bids__is_deleted=False))
    ).filter(is_deleted=False, is_active=True).order_by('-created_at')
    
    serializer_class = RequestSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    pagination_class = RequestPagination
    
    def get_queryset(self):
        """
        Return queryset with appropriate filtering and optimization.
        
        Returns:
            QuerySet: Filtered and optimized request queryset
        """
        # Start with the base queryset
        queryset = self.queryset
        
        # Filter by status
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by category
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category__id=category)
        
        # Filter by budget range
        min_budget = self.request.query_params.get('min_budget', None)
        max_budget = self.request.query_params.get('max_budget', None)
        if min_budget:
            queryset = queryset.filter(budget__gte=min_budget)
        if max_budget:
            queryset = queryset.filter(budget__lte=max_budget)
        
        # Search in title and description
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )
        
        # Filter out user's own requests for regular listing
        if self.action == 'list' and self.request.user.is_authenticated:
            exclude_own = self.request.query_params.get('exclude_own', 'true')
            if exclude_own.lower() == 'true':
                queryset = queryset.exclude(buyer=self.request.user)
        
        return queryset
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'retrieve':
            return RequestDetailSerializer
        return RequestSerializer
    
    def perform_create(self, serializer):
        """Set the buyer to the current user and audit fields."""
        request_obj = serializer.save(buyer=self.request.user)
        request_obj._current_user = self.request.user
        request_obj.save()
    
    def perform_update(self, serializer):
        """Set audit fields on update."""
        request_obj = serializer.save()
        request_obj._current_user = self.request.user
        request_obj.save()
    
    def create(self, request, *args, **kwargs):
        """Create a new request."""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            
            return Response({
                'success': True,
                'message': 'Request created successfully',
                'data': {
                    'request': serializer.data
                }
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'error': 'Request creation failed',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, *args, **kwargs):
        """Update a request."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Check if request can be updated
        if instance.status != 'open':
            return Response({
                'success': False,
                'error': 'Cannot update request that is not open'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            self.perform_update(serializer)
            
            return Response({
                'success': True,
                'message': 'Request updated successfully',
                'data': {
                    'request': serializer.data
                }
            })
        
        return Response({
            'success': False,
            'error': 'Request update failed',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, *args, **kwargs):
        """Soft delete a request."""
        instance = self.get_object()
        
        # Check if request can be deleted
        if instance.bid_count > 0:
            return Response({
                'success': False,
                'error': 'Cannot delete request with existing bids'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        instance.soft_delete(self.request.user)
        
        return Response({
            'success': True,
            'message': 'Request deleted successfully'
        }, status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['post'], permission_classes=[IsRequestBuyerOrReadOnly])
    def deliver(self, request, pk=None):
        """
        Mark request as delivered (for accepted seller).
        
        POST /api/requests/{id}/deliver/
        """
        request_obj = self.get_object()
        
        # Check if user is the accepted seller
        accepted_bid = request_obj.accepted_bid
        if not accepted_bid or accepted_bid.seller != request.user:
            return Response({
                'success': False,
                'error': 'Only the accepted seller can mark as delivered'
            }, status=status.HTTP_403_FORBIDDEN)
        
        if request_obj.status != 'accepted':
            return Response({
                'success': False,
                'error': 'Request must be in accepted status'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        success = request_obj.change_status('delivered', request.user)
        if success:
            return Response({
                'success': True,
                'message': 'Request marked as delivered'
            })
        
        return Response({
            'success': False,
            'error': 'Failed to update request status'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], permission_classes=[IsRequestBuyerOrReadOnly])
    def release_funds(self, request, pk=None):
        """
        Release funds from escrow (buyer only).
        
        POST /api/requests/{id}/release/
        """
        request_obj = self.get_object()
        
        if request_obj.status != 'delivered':
            return Response({
                'success': False,
                'error': 'Request must be delivered before releasing funds'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if escrow exists
        if not hasattr(request_obj, 'escrow'):
            return Response({
                'success': False,
                'error': 'No escrow transaction found'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        success = request_obj.escrow.release_funds(request.user)
        if success:
            return Response({
                'success': True,
                'message': 'Funds released successfully'
            })
        
        return Response({
            'success': False,
            'error': 'Failed to release funds'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def my_requests(self, request):
        """
        Get current user's requests.
        
        GET /api/requests/my_requests/
        """
        queryset = self.get_queryset().filter(buyer=request.user)
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response({
                'success': True,
                'data': {
                    'requests': serializer.data
                }
            })
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'data': {
                'requests': serializer.data
            }
        })


class RequestCategoryListView(generics.ListAPIView):
    """
    List all active request categories.
    
    GET /api/requests/categories/
    """
    
    queryset = RequestCategory.objects.filter(is_active=True).order_by('name')
    serializer_class = RequestCategorySerializer
    permission_classes = [permissions.AllowAny]
    
    def list(self, request, *args, **kwargs):
        """Return list of categories."""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'success': True,
            'data': {
                'categories': serializer.data
            }
        })