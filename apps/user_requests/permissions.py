"""
Custom permission classes for the Beiyangu marketplace request system.

This module provides permissions for controlling access to request operations
based on user roles and ownership.
"""
from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    
    Assumes the model instance has a `buyer` attribute that represents ownership.
    """
    
    def has_object_permission(self, request, view, obj):
        """
        Check if user has permission to access the object.
        
        Args:
            request: The HTTP request
            view: The view handling the request
            obj: The object being accessed
            
        Returns:
            bool: True if permission is granted
        """
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner of the request.
        # For Request model, the owner is the buyer
        return obj.buyer == request.user


class IsRequestBuyerOrReadOnly(permissions.BasePermission):
    """
    Custom permission that allows request buyers to perform specific actions.
    
    This permission is used for actions like marking delivery or releasing funds
    where only the buyer should have write access.
    """
    
    def has_permission(self, request, view):
        """
        Check view-level permissions.
        
        Args:
            request: The HTTP request
            view: The view handling the request
            
        Returns:
            bool: True if permission is granted
        """
        # Allow read access to authenticated users
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        
        # For write operations, user must be authenticated
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """
        Check object-level permissions.
        
        Args:
            request: The HTTP request
            view: The view handling the request
            obj: The request object being accessed
            
        Returns:
            bool: True if permission is granted
        """
        # Read permissions for authenticated users
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        
        # Write permissions only for the buyer of the request
        return obj.buyer == request.user


class IsRequestSellerOrReadOnly(permissions.BasePermission):
    """
    Custom permission for actions that should be performed by the accepted seller.
    
    This is used for actions like marking a request as delivered.
    """
    
    def has_permission(self, request, view):
        """Check view-level permissions."""
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """
        Check if user is the accepted seller for this request.
        
        Args:
            request: The HTTP request
            view: The view handling the request
            obj: The request object being accessed
            
        Returns:
            bool: True if permission is granted
        """
        # Read permissions for authenticated users
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        
        # Write permissions only for the accepted seller
        accepted_bid = obj.accepted_bid
        if not accepted_bid:
            return False
        
        return accepted_bid.seller == request.user


class IsRequestParticipant(permissions.BasePermission):
    """
    Permission that allows both buyer and accepted seller to access the request.
    
    Useful for actions where both parties need access (like viewing transaction details).
    """
    
    def has_permission(self, request, view):
        """Check view-level permissions."""
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """
        Check if user is either the buyer or accepted seller.
        
        Args:
            request: The HTTP request
            view: The view handling the request
            obj: The request object being accessed
            
        Returns:
            bool: True if permission is granted
        """
        # User must be authenticated
        if not request.user.is_authenticated:
            return False
        
        # Check if user is the buyer
        if obj.buyer == request.user:
            return True
        
        # Check if user is the accepted seller
        accepted_bid = obj.accepted_bid
        if accepted_bid and accepted_bid.seller == request.user:
            return True
        
        return False


class CanBidOnRequest(permissions.BasePermission):
    """
    Permission that determines if a user can bid on a request.
    
    Users cannot bid on their own requests.
    """
    
    def has_permission(self, request, view):
        """Check view-level permissions."""
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """
        Check if user can bid on this request.
        
        Args:
            request: The HTTP request
            view: The view handling the request
            obj: The request object being accessed
            
        Returns:
            bool: True if permission is granted
        """
        # User must be authenticated
        if not request.user.is_authenticated:
            return False
        
        # User cannot bid on their own request
        if obj.buyer == request.user:
            return False
        
        # Request must be open for bidding
        if not obj.can_be_bid_on():
            return False
        
        return True


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permission that allows admin users to perform write operations.
    
    Regular users can only read.
    """
    
    def has_permission(self, request, view):
        """
        Check permissions at the view level.
        
        Args:
            request: The HTTP request
            view: The view handling the request
            
        Returns:
            bool: True if permission is granted
        """
        # Read permissions for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        
        # Write permissions only for admin users
        return request.user.is_authenticated and request.user.is_staff