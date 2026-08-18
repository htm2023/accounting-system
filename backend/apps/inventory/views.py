from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Product, StockMovement
from .serializers import ProductSerializer, StockMovementSerializer
from apps.common.permissions import IsAccountant
from apps.audit_logs.services import log_action
from apps.audit_logs.models import AuditLog

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

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
            model_name='Product',
            object_id=serializer.instance.id,
            description=f"Update product {serializer.instance.sku}",
            request=self.request
        )

    def perform_destroy(self, instance):
        log_action(
            user=self.request.user,
            action=AuditLog.Action.DELETE,
            model_name='Product',
            object_id=instance.id,
            description=f"Delete product {instance.sku}",
            request=self.request
        )
        instance.delete()

class StockMovementViewSet(mixins.CreateModelMixin,
                            mixins.RetrieveModelMixin,
                            mixins.ListModelMixin,
                            viewsets.GenericViewSet):
    # لا يوجد update/destroy عمدًا: التصحيح يتم عبر حركة Adjustment جديدة فقط
    queryset = StockMovement.objects.all()
    serializer_class = StockMovementSerializer

    def get_permissions(self):
        if self.action == 'create':
            self.permission_classes = [IsAccountant]
        else:
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
