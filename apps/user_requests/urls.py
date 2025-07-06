# apps/requests/urls.py
"""
URL configuration for requests app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from .views import RequestViewSet

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'requests', RequestViewSet)

# Create nested router for bids under requests
requests_router = routers.NestedDefaultRouter(
    router, r'requests', lookup='request'
)
requests_router.register(
    r'bids', 
    'apps.bids.views.BidViewSet', 
    basename='request-bids'
)

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/', include(requests_router.urls)),
]