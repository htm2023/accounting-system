from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Party
from .serializers import PartySerializer
from apps.common.permissions import IsAccountant
from apps.audit_logs.services import log_action
from apps.audit_logs.models import AuditLog

class PartyViewSet(viewsets.ModelViewSet):
    queryset = Party.objects.all()
    serializer_class = PartySerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAccountant]
        else:
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    def perform_update(self, serializer):
        serializer.save()
        log_action(
            user=self.request.user,
            action=AuditLog.Action.UPDATE,
            model_name='Party',
            object_id=serializer.instance.id,
            description=f"Update party {serializer.instance.name_ar or serializer.instance.name_en}",
            request=self.request
        )

    def perform_destroy(self, instance):
        log_action(
            user=self.request.user,
            action=AuditLog.Action.DELETE,
            model_name='Party',
            object_id=instance.id,
            description=f"Delete party {instance.name_ar or instance.name_en}",
            request=self.request
        )
        instance.delete()
