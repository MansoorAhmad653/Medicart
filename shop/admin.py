from django.contrib import admin
from .models import Category, Medicine


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock_quantity', 'requires_prescription', 'is_active')
    list_filter = ('category', 'requires_prescription', 'is_active')
    search_fields = ('name', 'description')
    list_editable = ('price', 'stock_quantity', 'is_active')
