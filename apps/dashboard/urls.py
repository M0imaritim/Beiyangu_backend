"""
URL configuration for dashboard endpoints.
"""
from django.urls import path
from .views import buyer_dashboard, seller_dashboard

urlpatterns = [
    path('buyer/', buyer_dashboard, name='buyer-dashboard'),
    path('seller/', seller_dashboard, name='seller-dashboard'),
]

