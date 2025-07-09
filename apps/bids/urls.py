"""URL configuration for bids app."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BidViewSet, BidAcceptView, RequestBidView

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'bids', BidViewSet, basename='bids')

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/bids/<int:pk>/accept/', BidAcceptView.as_view(), name='bid-accept'),
    path('api/requests/<int:request_id>/bids/', RequestBidView.as_view(), name='request-bids'),
]