from django.contrib import admin
from .models import Notification


class NotificationAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'sender', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['recipient__email', 'sender__email']

admin.site.register(Notification, NotificationAdmin)
