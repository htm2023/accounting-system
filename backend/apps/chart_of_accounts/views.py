from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Account
from .serializers import AccountSerializer
from apps.common.permissions import IsAccountant
from apps.audit_logs.services import log_action
from apps.audit_logs.models import AuditLog

class AccountViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAccountant]
        else:
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save()
        log_action(
            user=self.request.user,
            action=AuditLog.Action.UPDATE,
            model_name='Account',
            object_id=serializer.instance.id,
            description=f'Update account {serializer.instance.code}',
            request=self.request
        )

    def perform_destroy(self, instance):
        if instance.children.exists():
            from rest_framework.exceptions import ValidationError
            raise ValidationError('Cannot delete account with child accounts.')
        log_action(
            user=self.request.user,
            action=AuditLog.Action.DELETE,
            model_name='Account',
            object_id=instance.id,
            description=f'Delete account {instance.code}',
            request=self.request
        )
        instance.delete()
