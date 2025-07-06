"""
URL configuration for dashboard endpoints.
"""
from django.urls import path
from .views import BuyerDashboardView, SellerDashboardView

urlpatterns = [
    path('buyer/', BuyerDashboardView.as_view(), name='buyer-dashboard'),
    path('seller/', SellerDashboardView.as_view(), name='seller-dashboard'),
]

