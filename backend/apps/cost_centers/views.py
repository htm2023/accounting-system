from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import CostCenter
from .serializers import CostCenterSerializer
from apps.common.permissions import IsAccountant

class CostCenterViewSet(viewsets.ModelViewSet):
    queryset = CostCenter.objects.all()
    serializer_class = CostCenterSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAccountant]
        else:
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()
