"""URL configuration for requests app."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from .views import RequestViewSet, RequestCategoryListView
from apps.bids.views import BidViewSet

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'requests', RequestViewSet)

# Create nested router for bids under requests
requests_router = routers.NestedDefaultRouter(
    router, r'requests', lookup='request'
)
requests_router.register(
    r'bids',
    BidViewSet,
    basename='request-bids'
)

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/', include(requests_router.urls)),
    # Add the categories endpoint
    path(
        'api/categories/',
        RequestCategoryListView.as_view(),
        name='request-categories'),
]
