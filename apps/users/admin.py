"""
Django admin configuration for users app.

This module provides admin interfaces for managing users
in the Beiyangu marketplace.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Q
from django.contrib.admin import SimpleListFilter
from django.utils import timezone
from datetime import timedelta

from .models import User


class UserActivityFilter(SimpleListFilter):
    """Filter users by their activity level."""

    title = 'activity level'
    parameter_name = 'activity'

    def lookups(self, request, model_admin):
        """Return activity filter options."""
        return [
            ('active_week', 'Active this week'),
            ('active_month', 'Active this month'),
            ('inactive_month', 'Inactive 30+ days'),
            ('new_users', 'New users (7 days)'),
        ]

    def queryset(self, request, queryset):
        """Filter by activity level."""
        now = timezone.now()

        if self.value() == 'active_week':
            week_ago = now - timedelta(days=7)
            return queryset.filter(last_login__gte=week_ago)
        elif self.value() == 'active_month':
            month_ago = now - timedelta(days=30)
            return queryset.filter(last_login__gte=month_ago)
        elif self.value() == 'inactive_month':
            month_ago = now - timedelta(days=30)
            return queryset.filter(
                Q(last_login__lt=month_ago) | Q(last_login__isnull=True)
            )
        elif self.value() == 'new_users':
            week_ago = now - timedelta(days=7)
            return queryset.filter(date_joined__gte=week_ago)

        return queryset


class UserRoleFilter(SimpleListFilter):
    """Filter users by their role/permissions."""

    title = 'user role'
    parameter_name = 'role'

    def lookups(self, request, model_admin):
        """Return role filter options."""
        return [
            ('superuser', 'Superusers'),
            ('staff', 'Staff'),
            ('regular', 'Regular users'),
        ]

    def queryset(self, request, queryset):
        """Filter by user role."""
        if self.value() == 'superuser':
            return queryset.filter(is_superuser=True)
        elif self.value() == 'staff':
            return queryset.filter(is_staff=True, is_superuser=False)
        elif self.value() == 'regular':
            return queryset.filter(is_staff=False, is_superuser=False)

        return queryset


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for User model."""

    # List display configuration
    list_display = [
        'username',
        'email',
        'full_name_display',
        'location_display',
        'user_stats',
        'activity_status',
        'permissions_display',
        'date_joined'
    ]

    list_filter = [
        UserActivityFilter,
        UserRoleFilter,
        'is_active',
        'is_staff',
        'is_superuser',
        'date_joined',
        'last_login'
    ]

    search_fields = [
        'username',
        'email',
        'first_name',
        'last_name',
        'location'
    ]

    ordering = ['-date_joined']
    list_per_page = 25
    date_hierarchy = 'date_joined'

    # Fieldsets for the user form
    fieldsets = (
        ('Basic Information', {
            'fields': ('username', 'email', 'password')
        }),
        ('Personal Info', {
            'fields': ('first_name', 'last_name', 'bio', 'location')
        }),
        ('Permissions', {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions'
            )
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    # Fieldsets for adding new users
    add_fieldsets = (
        ('Basic Information', {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2')
        }),
        ('Personal Info', {
            'classes': ('wide',),
            'fields': ('first_name', 'last_name', 'bio', 'location')
        }),
        ('Permissions', {
            'classes': ('wide',),
            'fields': ('is_active', 'is_staff', 'is_superuser')
        }),
    )

    readonly_fields = [
        'created_at',
        'updated_at',
        'last_login',
        'date_joined'
    ]

    filter_horizontal = ['groups', 'user_permissions']

    actions = [
        'activate_users',
        'deactivate_users',
        'make_staff',
        'remove_staff',
        'send_welcome_email'
    ]

    def get_queryset(self, request):
        """Optimize queryset with annotations for statistics."""
        return super().get_queryset(request).annotate(
            request_count=Count(
                'requests', filter=Q(
                    requests__is_deleted=False)), bid_count=Count(
                'bids', filter=Q(
                    bids__is_deleted=False)))

    def full_name_display(self, obj):
        """Return user's full name or username if no full name."""
        full_name = obj.get_full_name()
        if full_name:
            return full_name
        return f"({obj.username})"
    full_name_display.short_description = 'Full Name'
    full_name_display.admin_order_field = 'first_name'

    def location_display(self, obj):
        """Return user's location or dash if empty."""
        return obj.location or '-'
    location_display.short_description = 'Location'
    location_display.admin_order_field = 'location'

    def user_stats(self, obj):
        """Return user's marketplace statistics."""
        request_count = getattr(obj, 'request_count', 0)
        bid_count = getattr(obj, 'bid_count', 0)

        stats = []
        if request_count > 0:
            stats.append(
                f'{request_count} request{"s" if request_count != 1 else ""}')
        if bid_count > 0:
            stats.append(f'{bid_count} bid{"s" if bid_count != 1 else ""}')

        if stats:
            return format_html('<br>'.join(stats))
        return 'No activity'
    user_stats.short_description = 'Marketplace Activity'

    def activity_status(self, obj):
        """Return user's activity status with color coding."""
        if not obj.last_login:
            return format_html(
                '<span style="color: gray;">Never logged in</span>'
            )

        now = timezone.now()
        days_since_login = (now - obj.last_login).days

        if days_since_login <= 7:
            color = 'green'
            status = 'Active'
        elif days_since_login <= 30:
            color = 'orange'
            status = 'Recently active'
        else:
            color = 'red'
            status = 'Inactive'

        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span><br>'
            '<small>Last: {}</small>',
            color, status, obj.last_login.strftime('%Y-%m-%d')
        )
    activity_status.short_description = 'Activity Status'
    activity_status.admin_order_field = 'last_login'

    def permissions_display(self, obj):
        """Return user's permission level with badges."""
        badges = []

        if obj.is_superuser:
            badges.append(
                '<span style="background: red; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px;">SUPER</span>')
        elif obj.is_staff:
            badges.append(
                '<span style="background: blue; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px;">STAFF</span>')

        if not obj.is_active:
            badges.append(
                '<span style="background: gray; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px;">INACTIVE</span>')

        if badges:
            return format_html(' '.join(badges))
        return 'Regular'
    permissions_display.short_description = 'Permissions'

    def activate_users(self, request, queryset):
        """Activate selected users."""
        count = queryset.update(is_active=True)
        self.message_user(
            request,
            f'{count} user(s) activated successfully.'
        )
    activate_users.short_description = 'Activate selected users'

    def deactivate_users(self, request, queryset):
        """Deactivate selected users."""
        count = queryset.update(is_active=False)
        self.message_user(
            request,
            f'{count} user(s) deactivated successfully.'
        )
    deactivate_users.short_description = 'Deactivate selected users'

    def make_staff(self, request, queryset):
        """Give staff permissions to selected users."""
        count = queryset.update(is_staff=True)
        self.message_user(
            request,
            f'{count} user(s) given staff permissions.'
        )
    make_staff.short_description = 'Make selected users staff'

    def remove_staff(self, request, queryset):
        """Remove staff permissions from selected users."""
        count = queryset.filter(is_superuser=False).update(is_staff=False)
        self.message_user(
            request,
            f'{count} user(s) had staff permissions removed.'
        )
    remove_staff.short_description = 'Remove staff permissions'

    def send_welcome_email(self, request, queryset):
        """Send welcome email to selected users."""
        # This is a placeholder - implement actual email sending
        count = queryset.count()
        self.message_user(
            request,
            f'Welcome email queued for {count} user(s).'
        )
    send_welcome_email.short_description = 'Send welcome email'

    def get_readonly_fields(self, request, obj=None):
        """Customize readonly fields based on user permissions."""
        readonly = list(self.readonly_fields)

        # Regular staff can't edit superuser status
        if not request.user.is_superuser:
            readonly.append('is_superuser')

        # Users can't edit their own staff status
        if obj and obj == request.user:
            readonly.extend(['is_staff', 'is_superuser', 'is_active'])

        return readonly

    def has_delete_permission(self, request, obj=None):
        """Prevent users from deleting themselves."""
        if obj and obj == request.user:
            return False
        return super().has_delete_permission(request, obj)

    def save_model(self, request, obj, form, change):
        """Custom save logic."""
        # For new users, set default values
        if not change:
            if not obj.is_active:
                obj.is_active = True

        super().save_model(request, obj, form, change)


# Customize admin site
admin.site.site_header = 'Beiyangu Marketplace Admin'
admin.site.site_title = 'Beiyangu Admin'
admin.site.index_title = 'Welcome to Beiyangu Administration'
