from rest_framework import serializers
from .models import AuditLog

class AuditLogSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_full_name = serializers.CharField(source='user.full_name', read_only=True, allow_null=True)

    class Meta:
        model = AuditLog
        fields = ['id', 'user', 'user_username', 'user_full_name', 'action', 'model_name', 'object_id', 'changes', 'description', 'ip_address', 'timestamp']
        read_only_fields = fields
