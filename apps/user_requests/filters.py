"""
Filters for the requests app.
"""
import django_filters
from django.db.models import Q
from .models import Request


class RequestFilter(django_filters.FilterSet):
    """Filter class for Request model."""

    budget_min = django_filters.NumberFilter(
        field_name='budget', lookup_expr='gte'
    )
    budget_max = django_filters.NumberFilter(
        field_name='budget', lookup_expr='lte'
    )
    status = django_filters.ChoiceFilter(choices=Request.STATUS_CHOICES)
    category = django_filters.CharFilter(lookup_expr='icontains')
    has_deadline = django_filters.BooleanFilter(
        method='filter_has_deadline'
    )
    my_requests = django_filters.BooleanFilter(
        method='filter_my_requests'
    )

    class Meta:
        """Meta options for RequestFilter."""

        model = Request
        fields = [
            'status', 'category', 'budget_min', 'budget_max',
            'has_deadline', 'my_requests'
        ]

    def filter_has_deadline(self, queryset, name, value):
        """Filter requests that have a deadline set."""
        if value:
            return queryset.filter(deadline__isnull=False)
        return queryset.filter(deadline__isnull=True)

    def filter_my_requests(self, queryset, name, value):
        """Filter to show only current user's requests."""
        if value and self.request.user.is_authenticated:
            return queryset.filter(buyer=self.request.user)
        return queryset
