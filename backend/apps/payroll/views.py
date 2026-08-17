from django.core.exceptions import ValidationError
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Employee, Payslip
from .serializers import EmployeeSerializer, PayslipSerializer
from apps.common.permissions import IsAccountant, IsAdmin

class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAccountant]
        else:
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

class PayslipViewSet(viewsets.ModelViewSet):
    queryset = Payslip.objects.all()
    serializer_class = PayslipSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAccountant]
        elif self.action == 'post':
            self.permission_classes = [IsAdmin]
        else:
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    def perform_update(self, serializer):
        if serializer.instance.journal_entry:
            from rest_framework.exceptions import ValidationError as DRFValidationError
            raise DRFValidationError('Posted payslips cannot be modified.')
        serializer.save()

    def perform_destroy(self, instance):
        if instance.journal_entry:
            from rest_framework.exceptions import ValidationError as DRFValidationError
            raise DRFValidationError('Posted payslips cannot be deleted.')
        instance.delete()

    @action(detail=True, methods=['post'])
    def post(self, request, pk=None):
        payslip = self.get_object()
        try:
            journal_entry = payslip.post(user=request.user)
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            'message': 'Payslip posted successfully.',
            'journal_entry': journal_entry.entry_number
        })
