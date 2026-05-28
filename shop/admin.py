from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Medicine


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'medicine_count', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['name']
    
    def medicine_count(self, obj):
        count = obj.medicines.count()
        return format_html(
            '<span style="background-color: #007bff; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">{}</span>',
            count
        )
    medicine_count.short_description = 'Medicines'


@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ('medicine_name', 'category', 'price', 'stock_badge', 'requires_prescription', 'is_active')
    list_filter = ('category', 'requires_prescription', 'is_active', 'created_at')
    search_fields = ('name', 'description', 'manufacturer')
    list_editable = ('price', 'is_active')
    readonly_fields = ('created_at', 'updated_at', 'medicine_stats')
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'category', 'description')
        }),
        ('Pricing & Inventory', {
            'fields': ('price', 'stock_quantity', 'medicine_stats')
        }),
        ('Medical Information', {
            'fields': ('requires_prescription', 'manufacturer', 'dosage')
        }),
        ('Status & Timestamps', {
            'fields': ('is_active', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Media', {
            'fields': ('image',),
            'classes': ('collapse',)
        }),
    )
    
    def medicine_name(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 30px; height: 30px; margin-right: 10px; border-radius: 3px;"/>'
                '<strong>{}</strong>',
                obj.image.url,
                obj.name
            )
        return format_html('<strong>{}</strong>', obj.name)
    medicine_name.short_description = 'Medicine'
    
    def stock_badge(self, obj):
        if obj.stock_quantity > 100:
            color = '#28a745'
            status = 'In Stock'
        elif obj.stock_quantity > 10:
            color = '#ffc107'
            status = 'Running Low'
        elif obj.stock_quantity > 0:
            color = '#ff6b6b'
            status = 'Critical'
        else:
            color = '#dc3545'
            status = 'Out of Stock'
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 8px; border-radius: 3px; font-weight: bold;">'
            '{} ({} units)'
            '</span>',
            color,
            status,
            obj.stock_quantity
        )
    stock_badge.short_description = 'Stock Status'
    
    def medicine_stats(self, obj):
        from orders.models import OrderItem
        total_sold = OrderItem.objects.filter(medicine=obj).aggregate(
            total=__import__('django.db.models', fromlist=['Sum']).Sum('quantity')
        )['total'] or 0
        
        return format_html(
            '<div style="background-color: #f8f9fa; padding: 10px; border-radius: 5px;">'
            '<strong>Current Stock:</strong> {} units<br>'
            '<strong>Total Sold:</strong> {} units<br>'
            '<strong>Price:</strong> Rs. {:,.2f}<br>'
            '</div>',
            obj.stock_quantity,
            total_sold,
            obj.price
        )
    medicine_stats.short_description = 'Medicine Statistics'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('category')
