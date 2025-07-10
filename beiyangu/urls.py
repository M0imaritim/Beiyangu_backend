"""
Main URL configuration for Beiyangu project.
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Import app routers
from apps.user_requests.views import RequestViewSet
from apps.bids.views import BidViewSet, RequestBidView, BidAcceptView
from apps.escrow.views import EscrowTransactionViewSet

# Create main router
router = DefaultRouter()
router.register(r'requests', RequestViewSet)
router.register(r'bids', BidViewSet, basename='user-bids')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.users.urls')),
    path('api/', include(router.urls)),

    # Request-specific bid endpoints (using the RequestBidView)
    path(
        'api/requests/<int:request_id>/bids/',
        RequestBidView.as_view(),
        name='request-bids'),
    # Bid acceptance endpoint
    path(
        'api/bids/<int:pk>/accept/',
        BidAcceptView.as_view(),
        name='bid-accept'),
    path('api/dashboard/', include('apps.dashboard.urls')),
    path('api/escrow/', include('apps.escrow.urls')),
    path('', include('apps.user_requests.urls')),
]
