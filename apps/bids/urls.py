"""
URL configuration for bids app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BidViewSet

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'bids', BidViewSet, basename='bids')

urlpatterns = [
    path('api/', include(router.urls)),
]