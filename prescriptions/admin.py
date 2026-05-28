from django.contrib import admin
from django.utils.html import format_html
from .models import Prescription


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ('prescription_id', 'user_info', 'status_badge', 'medicine_count', 'uploaded_date', 'file_preview')
    list_filter = ('status', 'uploaded_at')
    search_fields = ('user__email', 'user__name')
    filter_horizontal = ('medicines',)
    readonly_fields = ('uploaded_at', 'updated_at', 'file_preview_large', 'user_info_detail')
    ordering = ['-uploaded_at']
    
    fieldsets = (
        ('Patient Information', {
            'fields': ('user', 'user_info_detail')
        }),
        ('Prescription Document', {
            'fields': ('file', 'file_preview_large')
        }),
        ('Approval', {
            'fields': ('status', 'medicines', 'admin_notes')
        }),
        ('Timestamps', {
            'fields': ('uploaded_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Patient Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    def prescription_id(self, obj):
        return format_html('<strong>Rx #{}</strong>', obj.id)
    prescription_id.short_description = 'Prescription'
    
    def user_info(self, obj):
        return format_html(
            '<strong>{}</strong><br><span style="color: #666; font-size: 0.9em;">{}</span>',
            obj.user.name or obj.user.email,
            obj.user.email
        )
    user_info.short_description = 'Patient'
    
    def user_info_detail(self, obj):
        return format_html(
            '<div style="background-color: #e7f3ff; padding: 10px; border-radius: 5px;">'
            '<strong>Name:</strong> {}<br>'
            '<strong>Email:</strong> {}<br>'
            '<strong>Phone:</strong> {}'
            '</div>',
            obj.user.name or 'N/A',
            obj.user.email,
            obj.user.phone or 'N/A'
        )
    user_info_detail.short_description = 'Patient Details'
    
    def status_badge(self, obj):
        colors = {
            'pending': '#ffc107',
            'approved': '#28a745',
            'rejected': '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 8px; border-radius: 3px; font-weight: bold;">'
            '{}'
            '</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def medicine_count(self, obj):
        count = obj.medicines.count()
        if obj.status == 'approved':
            return format_html(
                '<span style="background-color: #007bff; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">'
                '{} medicine{}'
                '</span>',
                count,
                's' if count != 1 else ''
            )
        return format_html(
            '<span style="color: #999;">—</span>'
        )
    medicine_count.short_description = 'Medicines'
    
    def uploaded_date(self, obj):
        return obj.uploaded_at.strftime('%d %b %Y, %H:%M')
    uploaded_date.short_description = 'Uploaded'
    
    def file_preview(self, obj):
        if obj.file:
            file_url = obj.file.url
            if obj.is_image():
                return format_html(
                    '<a href="{}" target="_blank"><img src="{}" style="width: 30px; height: 30px; border-radius: 3px;"/></a>',
                    file_url,
                    file_url
                )
            else:
                return format_html(
                    '<a href="{}" target="_blank" style="color: #007bff;">📄 View File</a>',
                    file_url
                )
        return '—'
    file_preview.short_description = 'File'
    
    def file_preview_large(self, obj):
        if not obj.file:
            return 'No file attached'
        
        file_url = obj.file.url
        if obj.is_image():
            return format_html(
                '<a href="{}" target="_blank">'
                '<img src="{}" style="max-width: 400px; max-height: 500px; border: 1px solid #ddd; border-radius: 5px;"/>'
                '</a>',
                file_url,
                file_url
            )
        else:
            return format_html(
                '<a href="{}" target="_blank" class="button" style="padding: 10px 20px;">'
                '📄 Download File'
                '</a>',
                file_url
            )
    file_preview_large.short_description = 'Document Preview'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user').prefetch_related('medicines')
