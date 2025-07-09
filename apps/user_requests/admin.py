"""
Django admin configuration for user_requests app.

This module provides admin interfaces for managing requests and categories
in the Beiyangu marketplace.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.db.models import Count, Q
from django.contrib.admin import SimpleListFilter

from .models import Request, RequestCategory


class RequestStatusFilter(SimpleListFilter):
    """Custom filter for request status with counts."""
    
    title = 'status'
    parameter_name = 'status'
    
    def lookups(self, request, model_admin):
        """Return filter options with counts."""
        choices = []
        for status_code, status_name in Request.STATUS_CHOICES:
            count = Request.objects.filter(status=status_code, is_deleted=False).count()
            choices.append((status_code, f"{status_name} ({count})"))
        return choices
    
    def queryset(self, request, queryset):
        """Filter queryset based on selected status."""
        if self.value():
            return queryset.filter(status=self.value())
        return queryset


class RequestCategoryFilter(SimpleListFilter):
    """Custom filter for request categories."""
    
    title = 'category'
    parameter_name = 'category'
    
    def lookups(self, request, model_admin):
        """Return active categories."""
        categories = RequestCategory.objects.filter(is_active=True)
        return [(cat.id, cat.name) for cat in categories]
    
    def queryset(self, request, queryset):
        """Filter by category."""
        if self.value():
            return queryset.filter(category_id=self.value())
        return queryset


class HasDeadlineFilter(SimpleListFilter):
    """Filter requests by deadline presence."""
    
    title = 'deadline'
    parameter_name = 'has_deadline'
    
    def lookups(self, request, model_admin):
        """Return deadline filter options."""
        return [
            ('yes', 'Has deadline'),
            ('no', 'No deadline'),
            ('expired', 'Expired'),
        ]
    
    def queryset(self, request, queryset):
        """Filter by deadline status."""
        if self.value() == 'yes':
            return queryset.filter(deadline__isnull=False)
        elif self.value() == 'no':
            return queryset.filter(deadline__isnull=True)
        elif self.value() == 'expired':
            return queryset.filter(deadline__lt=timezone.now())
        return queryset


@admin.register(RequestCategory)
class RequestCategoryAdmin(admin.ModelAdmin):
    """Admin interface for RequestCategory model."""
    
    list_display = [
        'name',
        'description_short',
        'request_count',
        'is_active',
        'created_at'
    ]
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']
    list_editable = ['is_active']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at']
    
    def description_short(self, obj):
        """Return truncated description."""
        if obj.description:
            return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
        return '-'
    description_short.short_description = 'Description'
    
    def request_count(self, obj):
        """Return count of requests in this category."""
        count = obj.requests.filter(is_deleted=False).count()
        if count > 0:
            url = reverse('admin:user_requests_request_changelist')
            return format_html(
                '<a href="{}?category={}">{} requests</a>',
                url, obj.id, count
            )
        return '0 requests'
    request_count.short_description = 'Requests'
    
    def get_queryset(self, request):
        """Optimize queryset with prefetch."""
        return super().get_queryset(request).annotate(
            request_count=Count('requests', filter=Q(requests__is_deleted=False))
        )


@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    """Admin interface for Request model."""
    
    list_display = [
        'title_short',
        'buyer_link',
        'status_badge',
        'budget_formatted',
        'category_name',
        'bid_count_display',
        'deadline_display',
        'created_at'
    ]
    list_filter = [
        RequestStatusFilter,
        RequestCategoryFilter,
        HasDeadlineFilter,
        'is_active',
        'is_deleted',
        'created_at'
    ]
    search_fields = [
        'title',
        'description',
        'buyer__username',
        'buyer__email',
        'buyer__first_name',
        'buyer__last_name'
    ]
    ordering = ['-created_at']
    list_per_page = 25
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'budget', 'category', 'deadline')
        }),
        ('Ownership & Status', {
            'fields': ('buyer', 'status', 'is_active')
        }),
        ('Audit Information', {
            'fields': (
                'public_id',
                'created_at',
                'updated_at',
                'created_by',
                'updated_by'
            ),
            'classes': ('collapse',)
        }),
        ('System Fields', {
            'fields': ('is_deleted',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = [
        'public_id',
        'created_at',
        'updated_at',
        'created_by',
        'updated_by'
    ]
    
    autocomplete_fields = ['buyer', 'category']
    
    actions = [
        'mark_as_active',
        'mark_as_inactive',
        'soft_delete_selected',
        'restore_selected'
    ]
    
    def get_queryset(self, request):
        """Optimize queryset with select_related and annotations."""
        return super().get_queryset(request).select_related(
            'buyer', 'category', 'created_by', 'updated_by'
        ).annotate(
            annotated_bid_count=Count('bids', filter=Q(bids__is_deleted=False))
        )
    
    def title_short(self, obj):
        """Return truncated title."""
        return obj.title[:50] + '...' if len(obj.title) > 50 else obj.title
    title_short.short_description = 'Title'
    title_short.admin_order_field = 'title'
    
    def buyer_link(self, obj):
        """Return link to buyer's admin page."""
        url = reverse('admin:users_user_change', args=[obj.buyer.pk])
        return format_html('<a href="{}">{}</a>', url, obj.buyer.username)
    buyer_link.short_description = 'Buyer'
    buyer_link.admin_order_field = 'buyer__username'
    
    def status_badge(self, obj):
        """Return colored status badge."""
        colors = {
            'open': 'green',
            'accepted': 'blue',
            'delivered': 'orange',
            'completed': 'purple',
            'disputed': 'red',
            'cancelled': 'gray'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'
    
    def budget_formatted(self, obj):
        """Return formatted budget amount."""
        return f'${obj.budget:,.2f}'
    budget_formatted.short_description = 'Budget'
    budget_formatted.admin_order_field = 'budget'
    
    def category_name(self, obj):
        """Return category name or dash if none."""
        return obj.category.name if obj.category else '-'
    category_name.short_description = 'Category'
    category_name.admin_order_field = 'category__name'
    
    def bid_count_display(self, obj):
        """Return bid count with link to bids."""
        count = getattr(obj, 'annotated_bid_count', 0)
        if count > 0:
            # Assuming you have a bids admin or can create a filtered view
            return format_html(
                '<strong>{}</strong> bid{}',
                count, 's' if count != 1 else ''
            )
        return '0 bids'
    bid_count_display.short_description = 'Bids'
    bid_count_display.admin_order_field = 'annotated_bid_count'
    
    def deadline_display(self, obj):
        """Return formatted deadline with status."""
        if not obj.deadline:
            return '-'
        
        now = timezone.now()
        if obj.deadline <= now:
            return format_html(
                '<span style="color: red; font-weight: bold;">Expired</span><br>'
                '<small>{}</small>',
                obj.deadline.strftime('%Y-%m-%d %H:%M')
            )
        else:
            delta = obj.deadline - now
            days = delta.days
            if days > 0:
                time_left = f'{days} days'
            else:
                hours = delta.seconds // 3600
                time_left = f'{hours} hours'
            
            return format_html(
                '<span style="color: green;">{}</span><br>'
                '<small>{}</small>',
                time_left, obj.deadline.strftime('%Y-%m-%d %H:%M')
            )
    deadline_display.short_description = 'Deadline'
    deadline_display.admin_order_field = 'deadline'
    
    def mark_as_active(self, request, queryset):
        """Mark selected requests as active."""
        count = queryset.update(is_active=True)
        self.message_user(
            request,
            f'{count} request(s) marked as active.'
        )
    mark_as_active.short_description = 'Mark selected requests as active'
    
    def mark_as_inactive(self, request, queryset):
        """Mark selected requests as inactive."""
        count = queryset.update(is_active=False)
        self.message_user(
            request,
            f'{count} request(s) marked as inactive.'
        )
    mark_as_inactive.short_description = 'Mark selected requests as inactive'
    
    def soft_delete_selected(self, request, queryset):
        """Soft delete selected requests."""
        count = queryset.update(is_deleted=True, is_active=False)
        self.message_user(
            request,
            f'{count} request(s) soft deleted.'
        )
    soft_delete_selected.short_description = 'Soft delete selected requests'
    
    def restore_selected(self, request, queryset):
        """Restore soft deleted requests."""
        count = queryset.update(is_deleted=False, is_active=True)
        self.message_user(
            request,
            f'{count} request(s) restored.'
        )
    restore_selected.short_description = 'Restore selected requests'
    
    def get_readonly_fields(self, request, obj=None):
        """Make certain fields readonly for existing objects."""
        readonly = list(self.readonly_fields)
        if obj:  # Editing existing object
            readonly.extend(['buyer', 'public_id'])
        return readonly
    
    def save_model(self, request, obj, form, change):
        """Set audit fields when saving."""
        if not change:  # Creating new object
            obj.created_by = request.user
            obj.buyer = obj.buyer or request.user
        obj.updated_by = request.user
        obj._current_user = request.user
        super().save_model(request, obj, form, change)


# Custom admin site configuration
admin.site.site_header = 'Beiyangu Marketplace Admin'
admin.site.site_title = 'Beiyangu Admin'
admin.site.index_title = 'Welcome to Beiyangu Administration'