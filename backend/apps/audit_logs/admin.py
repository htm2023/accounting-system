from django.contrib import admin
from .models import AuditLog

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'user', 'action', 'model_name', 'object_id', 'ip_address']
    list_filter = ['action', 'model_name', 'timestamp']
    search_fields = ['description', 'object_id', 'user__username']
    readonly_fields = ['user', 'action', 'model_name', 'object_id', 'changes', 'description', 'ip_address', 'timestamp']
    date_hierarchy = 'timestamp'
