"""Django admin configuration for bids app."""
from django.contrib import admin
from .models import Bid


@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    """Admin interface for Bid model."""
    
    list_display = [
        'id', 'request', 'seller', 'amount', 'is_accepted', 
        'is_deleted', 'created_at'
    ]
    list_filter = ['is_accepted', 'is_deleted', 'created_at']
    search_fields = ['seller__username', 'request__title', 'message']
    readonly_fields = [
        'public_id', 'created_at', 'updated_at', 'created_by', 'updated_by'
    ]
    raw_id_fields = ['request', 'seller', 'created_by', 'updated_by']
    
    fieldsets = (
        (None, {
            'fields': ('public_id', 'request', 'seller', 'amount', 'message')
        }),
        ('Delivery', {
            'fields': ('delivery_time', 'expires_at')
        }),
        ('Status', {
            'fields': ('is_accepted', 'is_deleted')
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        })
    )
    
    def has_delete_permission(self, request, obj=None):
        """Prevent hard deletion - use soft delete instead."""
        return False