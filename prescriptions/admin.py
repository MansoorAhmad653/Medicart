from django.contrib import admin
from .models import Prescription

@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'uploaded_at')
    list_filter = ('status',)
    list_editable = ('status',)
    search_fields = ('user__email',)
    readonly_fields = ('uploaded_at', 'updated_at')
