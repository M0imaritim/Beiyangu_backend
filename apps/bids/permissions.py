"""Custom permissions for the bids app."""

from rest_framework import permissions


class IsBidOwnerOrReadOnly(permissions.BasePermission):
    """Custom permission to only allow bid owners to edit their bids."""

    def has_object_permission(self, request, view, obj):
        """Check if user has permission to access the bid."""
        # Read permissions for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions only to the bid owner
        return obj.seller == request.user
