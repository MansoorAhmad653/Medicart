from django.contrib import admin
from .models import Feedback

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('user', 'rating', 'order', 'medicine', 'created_at')
    list_filter = ('rating',)
    search_fields = ('user__email', 'comment')
