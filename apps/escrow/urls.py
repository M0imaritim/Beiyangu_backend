"""
URL configuration for escrow app.
"""
from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import EscrowTransactionViewSet

# Create router and register viewsets
router = DefaultRouter()
router.register(r'escrow-transactions', EscrowTransactionViewSet, basename='escrow-transactions')

app_name = 'escrow'

urlpatterns = [
    path('', include(router.urls)),
    # Additional custom endpoints if needed
]