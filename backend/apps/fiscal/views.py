from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import FiscalYear, FiscalPeriod
from .serializers import FiscalYearSerializer, FiscalPeriodSerializer
from apps.common.permissions import IsAccountant, IsAdmin

class FiscalYearViewSet(viewsets.ModelViewSet):
    queryset = FiscalYear.objects.all()
    serializer_class = FiscalYearSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdmin]
        else:
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    def perform_destroy(self, instance):
        if instance.periods.exists():
            from rest_framework.exceptions import ValidationError
            raise ValidationError('Cannot delete fiscal year with existing periods.')
        instance.delete()

class FiscalPeriodViewSet(viewsets.ModelViewSet):
    queryset = FiscalPeriod.objects.all()
    serializer_class = FiscalPeriodSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAccountant]
        else:
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    def perform_update(self, serializer):
        instance = serializer.save()
        if instance.is_closed and self.request.user.role not in ['Admin']:
            from rest_framework.exceptions import ValidationError
            raise ValidationError('Closed period cannot be modified.')

    def perform_destroy(self, instance):
        if instance.is_closed:
            from rest_framework.exceptions import ValidationError
            raise ValidationError('Closed period cannot be deleted.')
        instance.delete()
