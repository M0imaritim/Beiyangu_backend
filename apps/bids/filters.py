"""Filters for the bids app."""

import django_filters
from .models import Bid


class BidFilter(django_filters.FilterSet):
    """Filter class for Bid model."""

    amount_min = django_filters.NumberFilter(
        field_name='amount', lookup_expr='gte'
    )
    amount_max = django_filters.NumberFilter(
        field_name='amount', lookup_expr='lte'
    )
    is_accepted = django_filters.BooleanFilter()
    my_bids = django_filters.BooleanFilter(method='filter_my_bids')

    class Meta:
        """Meta options for BidFilter."""

        model = Bid
        fields = ['is_accepted', 'amount_min', 'amount_max', 'my_bids']

    def filter_my_bids(self, queryset, name, value):
        """Filter to show only current user's bids."""
        if value and self.request.user.is_authenticated:
            return queryset.filter(seller=self.request.user)
        return queryset
