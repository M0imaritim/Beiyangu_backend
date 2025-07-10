"""
Dashboard views for the Beiyangu marketplace.

This module provides aggregated data views for buyer and seller dashboards.
"""
from django.db.models import Count, Q, Sum, Avg
from rest_framework import permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from apps.user_requests.models import Request
from apps.user_requests.serializers import RequestSerializer
from apps.bids.models import Bid
from apps.bids.serializers import BidSerializer


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def buyer_dashboard(request):
    """
    Get buyer dashboard data.

    GET /api/dashboard/buyer/
    """
    user = request.user

    # Get user's requests with related data
    requests = Request.objects.select_related('category').prefetch_related(
        'bids'
    ).filter(
        buyer=user,
        is_deleted=False
    ).annotate(
        total_bids=Count('bids', filter=Q(bids__is_deleted=False))
    ).order_by('-created_at')[:10]

    # Get statistics
    stats = {
        'total_requests': Request.objects.filter(
            buyer=user,
            is_deleted=False).count(),
        'open_requests': Request.objects.filter(
            buyer=user,
            status='open',
            is_deleted=False).count(),
        'completed_requests': Request.objects.filter(
                buyer=user,
                status='completed',
                is_deleted=False).count(),
        'total_spent': Bid.objects.filter(
                    request__buyer=user,
                    request__status='completed',
                    request__is_deleted=False,
                    is_accepted=True,
                    is_deleted=False).aggregate(
                        total=Sum('amount'))['total'] or 0,
    }

    # Get recent bids on user's requests
    recent_bids = Bid.objects.select_related('seller', 'request').filter(
        request__buyer=user,
        is_deleted=False
    ).order_by('-created_at')[:10]

    return Response({
        'success': True,
        'data': {
            'stats': stats,
            'recent_requests': RequestSerializer(requests, many=True).data,
            'recent_bids': BidSerializer(recent_bids, many=True).data
        }
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def seller_dashboard(request):
    """
    Get seller dashboard data.

    GET /api/dashboard/seller/
    """
    user = request.user

    # Get user's bids with related data
    bids = Bid.objects.select_related('request').filter(
        seller=user,
        is_deleted=False
    ).order_by('-created_at')[:10]

    # Get statistics
    stats = {
        'total_bids': Bid.objects.filter(
            seller=user,
            is_deleted=False).count(),
        'accepted_bids': Bid.objects.filter(
            seller=user,
            is_accepted=True,
            is_deleted=False).count(),
        'total_earned': Bid.objects.filter(
                seller=user,
                is_accepted=True,
                is_deleted=False,
                request__status='completed').aggregate(
                    total=Sum('amount'))['total'] or 0,
        'pending_earnings': Bid.objects.filter(
                        seller=user,
                        is_accepted=True,
                        is_deleted=False,
                        request__status__in=[
                            'accepted',
                            'delivered']).aggregate(
                                total=Sum('amount'))['total'] or 0,
    }

    # Get available requests (excluding user's own)
    available_requests = Request.objects.select_related('buyer',
                                                        'category').filter(
        status='open',
        is_active=True,
        is_deleted=False
    ).exclude(
        buyer=user
    ).exclude(
        # Exclude requests user has already bid on
        bids__seller=user,
        bids__is_deleted=False
    ).annotate(
        total_bids=Count('bids', filter=Q(bids__is_deleted=False))
    ).order_by('-created_at')[:10]

    return Response({
        'success': True,
        'data': {
            'stats': stats,
            'my_bids': BidSerializer(bids, many=True).data,
            'available_requests': RequestSerializer(available_requests,
                                                    many=True).data
        }
    })
