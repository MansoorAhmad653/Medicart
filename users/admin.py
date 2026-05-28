from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('user_info', 'role_badge', 'phone', 'total_orders', 'joined_date', 'is_active')
    list_filter = ('role', 'is_active', 'date_joined')
    search_fields = ('email', 'username', 'name', 'phone')
    readonly_fields = ('date_joined', 'last_login', 'user_stats', 'order_info')
    ordering = ['-date_joined']
    
    fieldsets = (
        ('Authentication', {
            'fields': ('email', 'username', 'password')
        }),
        ('Personal Information', {
            'fields': ('name', 'phone', 'address')
        }),
        ('Account Status', {
            'fields': ('role', 'is_active', 'is_staff', 'date_joined', 'last_login')
        }),
        ('Statistics', {
            'fields': ('user_stats', 'order_info'),
            'classes': ('collapse',)
        }),
    )
    
    def user_info(self, obj):
        role_color = '#007bff' if obj.role == 'customer' else '#dc3545'
        return format_html(
            '<strong style="color: #333;">{}</strong><br>'
            '<span style="color: #666; font-size: 0.9em;">Email: {}</span>',
            obj.name or obj.email,
            obj.email
        )
    user_info.short_description = 'User'
    
    def role_badge(self, obj):
        colors = {
            'customer': '#28a745',
            'admin': '#dc3545',
        }
        color = colors.get(obj.role, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_role_display() if hasattr(obj, 'get_role_display') else obj.role.title()
        )
    role_badge.short_description = 'Role'
    
    def joined_date(self, obj):
        return obj.date_joined.strftime('%d %b %Y')
    joined_date.short_description = 'Joined'
    
    def total_orders(self, obj):
        count = obj.orders.count()
        url = reverse('admin:orders_order_changelist') + f'?user__id__exact={obj.id}'
        return format_html(
            '<a href="{}" style="font-weight: bold; color: #007bff;">{} orders</a>',
            url,
            count
        )
    total_orders.short_description = 'Orders'
    
    def user_stats(self, obj):
        total_orders = obj.orders.count()
        total_spent = obj.orders.exclude(status='cancelled').aggregate(
            total=__import__('django.db.models', fromlist=['Sum']).Sum('total_price')
        )['total'] or 0
        
        return format_html(
            '<div style="background-color: #e8f5e9; padding: 10px; border-radius: 5px;">'
            '<strong>Total Orders:</strong> {}<br>'
            '<strong>Total Spent:</strong> Rs. {:,.2f}<br>'
            '<strong>Account Status:</strong> {}'
            '</div>',
            total_orders,
            total_spent,
            'Active' if obj.is_active else 'Inactive'
        )
    user_stats.short_description = 'User Statistics'
    
    def order_info(self, obj):
        from orders.models import Order
        orders = obj.orders.all()[:5]
        if not orders:
            return '<em>No orders yet</em>'
        
        order_list = '<br>'.join([
            f'<a href="{reverse("admin:orders_order_change", args=[o.id])}" style="color: #007bff;">Order #{o.id}</a> - '
            f'{o.get_status_display()} - Rs. {o.total_price:,.2f} ({o.created_at.strftime("%d %b %Y")})'
            for o in orders
        ])
        
        return format_html(
            '<div style="background-color: #f0f7ff; padding: 10px; border-radius: 5px;">'
            '<strong>Recent Orders:</strong><br>{}'
            '</div>',
            order_list
        )
    order_info.short_description = 'Recent Orders'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Optimize with prefetch_related for orders
        from django.db.models import Prefetch
        return qs.prefetch_related('orders')
