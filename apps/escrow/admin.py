"""
Admin configuration for escrow app.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import EscrowTransaction


@admin.register(EscrowTransaction)
class EscrowTransactionAdmin(admin.ModelAdmin):
    """Admin interface for EscrowTransaction model."""
    
    list_display = [
        'public_id_short', 'request_title', 'amount', 'escrow_fee', 'total_amount',
        'payment_method', 'status_badge', 'created_at', 'locked_at'
    ]
    list_filter = ['status', 'payment_method', 'created_at', 'locked_at']
    search_fields = ['public_id', 'request__title', 'payment_reference']
    readonly_fields = [
        'public_id', 'payment_reference', 'created_at', 'locked_at', 'released_at',
        'created_by', 'updated_by', 'status_info_display'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('public_id', 'request', 'status', 'status_info_display')
        }),
        ('Payment Details', {
            'fields': ('amount', 'escrow_fee', 'total_amount', 'payment_method', 
                      'payment_reference', 'payment_processor')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'locked_at', 'released_at')
        }),
        ('Notes & Audit', {
            'fields': ('notes', 'created_by', 'updated_by')
        }),
    )
    
    def public_id_short(self, obj):
        """Display shortened public ID."""
        return f"{str(obj.public_id)[:8]}..."
    public_id_short.short_description = 'ID'
    
    def request_title(self, obj):
        """Display request title with link."""
        if obj.request:
            url = reverse('admin:user_requests_request_change', args=[obj.request.pk])
            return format_html('<a href="{}">{}</a>', url, obj.request.title[:50])
        return '-'
    request_title.short_description = 'Request'
    
    def status_badge(self, obj):
        """Display status as colored badge."""
        colors = {
            'pending': '#ffa500',
            'locked': '#28a745',
            'released': '#007bff',
            'held': '#dc3545',
            'refunded': '#6c757d',
            'failed': '#dc3545'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def status_info_display(self, obj):
        """Display detailed status information."""
        info = obj.get_status_info()
        html = f"<strong>Status:</strong> {info['status_display']}<br>"
        html += f"<strong>Can be released:</strong> {info['can_be_released']}<br>"
        html += f"<strong>Is active:</strong> {info['is_active']}<br>"
        html += f"<strong>Is pending:</strong> {info['is_pending']}<br>"
        
        if 'locked_duration' in info:
            html += f"<strong>Locked for:</strong> {info['locked_duration']}<br>"
        elif 'total_duration' in info:
            html += f"<strong>Total duration:</strong> {info['total_duration']}<br>"
        
        return mark_safe(html)
    status_info_display.short_description = 'Status Information'
    
    def has_add_permission(self, request):
        """Disable adding escrow transactions directly."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Disable deleting escrow transactions."""
        return False