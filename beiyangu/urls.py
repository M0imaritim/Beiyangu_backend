"""
Main URL configuration for Beiyangu project.
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Import app routers
from apps.user_requests.views import RequestViewSet
from apps.bids.views import BidViewSet

# Create main router
router = DefaultRouter()
router.register(r'requests', RequestViewSet)
router.register(r'bids', BidViewSet, basename='user-bids')

# Create nested router for request-specific bids
from rest_framework_nested import routers
requests_router = routers.NestedDefaultRouter(
    router, r'requests', lookup='request'
)
requests_router.register(r'bids', BidViewSet, basename='request-bids')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.users.urls')),  # Auth endpoints
    path('api/', include(router.urls)),
    path('api/', include(requests_router.urls)),
    path('api/dashboard/', include('apps.dashboard.urls')),  # Dashboard endpoints
]
