from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Sum
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('medicine', 'quantity', 'price', 'item_total')
    
    def item_total(self, obj):
        return f"Rs. {obj.quantity * obj.price:,.2f}"
    item_total.short_description = "Item Total"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'customer_name', 'status_badge', 'status', 'total_price', 'created_date', 'days_since', 'action_buttons')
    list_filter = ('status', 'created_at')
    search_fields = ('user__email', 'user__name', 'id', 'phone')
    list_editable = ('status',)
    inlines = [OrderItemInline]
    readonly_fields = ('created_at', 'updated_at', 'order_summary', 'user_info')
    ordering = ['-created_at']
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_summary', 'user_info', 'status')
        }),
        ('Delivery Details', {
            'fields': ('delivery_address', 'phone')
        }),
        ('Pricing', {
            'fields': ('total_price', 'delivery_fee')
        }),
        ('Notes & Timestamps', {
            'fields': ('notes', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def order_id(self, obj):
        return format_html('<strong>Order #{}</strong>', obj.id)
    order_id.short_description = 'Order ID'
    
    def customer_name(self, obj):
        return f"{obj.user.name or obj.user.email}"
    customer_name.short_description = 'Customer'
    
    def status_badge(self, obj):
        colors = {
            'confirmed': '#007bff',
            'packed': '#ffc107',
            'dispatched': '#17a2b8',
            'delivered': '#28a745',
            'cancelled': '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def created_date(self, obj):
        return obj.created_at.strftime('%d %b %Y, %H:%M')
    created_date.short_description = 'Order Date'
    
    def days_since(self, obj):
        from django.utils import timezone
        days = (timezone.now() - obj.created_at).days
        if days == 0:
            return 'Today'
        elif days == 1:
            return 'Yesterday'
        else:
            return f'{days} days ago'
    days_since.short_description = 'Time'
    
    def action_buttons(self, obj):
        edit_url = reverse('admin:orders_order_change', args=[obj.pk])
        return format_html(
            '<a class="button" href="{}">Edit</a>',
            edit_url
        )
    action_buttons.short_description = 'Actions'
    
    def order_summary(self, obj):
        items = obj.items.all()
        item_details = '<br>'.join([
            f"• {item.medicine.name}: {item.quantity}x Rs. {item.price}" 
            for item in items
        ])
        subtotal = obj.total_price - obj.delivery_fee
        return format_html(
            '<div style="background-color: #f8f9fa; padding: 10px; border-radius: 5px;">'
            '<strong>Order #{}</strong><br>'
            'Items:<br>{}<br>'
            '<hr style="margin: 10px 0;">'
            'Subtotal: Rs. {:,.2f}<br>'
            'Delivery Fee: Rs. {:,.2f}<br>'
            '<strong style="font-size: 1.1em;">Total: Rs. {:,.2f}</strong>'
            '</div>',
            obj.id,
            item_details,
            subtotal,
            obj.delivery_fee,
            obj.total_price
        )
    order_summary.short_description = 'Order Summary'
    
    def user_info(self, obj):
        return format_html(
            '<div style="background-color: #e7f3ff; padding: 10px; border-radius: 5px;">'
            '<strong>Customer:</strong> {}<br>'
            '<strong>Email:</strong> {}<br>'
            '<strong>Phone:</strong> {}<br>'
            '<strong>Address:</strong> {}'
            '</div>',
            obj.user.name or 'N/A',
            obj.user.email,
            obj.phone,
            obj.delivery_address
        )
    user_info.short_description = 'Customer Information'
    
    def get_queryset(self, request):
        # Optimize queries with select_related
        qs = super().get_queryset(request)
        return qs.select_related('user').prefetch_related('items__medicine')


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order_link', 'medicine', 'quantity', 'price', 'item_total')
    list_filter = ('order__created_at', 'order__status')
    search_fields = ('order__id', 'medicine__name')
    readonly_fields = ('order', 'medicine', 'quantity', 'price')
    
    def order_link(self, obj):
        url = reverse('admin:orders_order_change', args=[obj.order.pk])
        return format_html('<a href="{}">Order #{}</a>', url, obj.order.id)
    order_link.short_description = 'Order'
    
    def item_total(self, obj):
        return f"Rs. {obj.quantity * obj.price:,.2f}"
    item_total.short_description = 'Total'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
