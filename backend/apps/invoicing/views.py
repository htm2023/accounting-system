from django.core.exceptions import ValidationError
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Invoice
from .serializers import InvoiceSerializer
from apps.common.permissions import IsAccountant, IsAdmin

class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.prefetch_related('items')
    serializer_class = InvoiceSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAccountant]
        elif self.action == 'post':
            self.permission_classes = [IsAdmin]
        else:
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save()

    def perform_destroy(self, instance):
        if instance.status != Invoice.Status.DRAFT:
            from rest_framework.exceptions import ValidationError
            raise ValidationError('Only draft invoices can be deleted.')
        instance.delete()

    @action(detail=True, methods=['post'])
    def post(self, request, pk=None):
        invoice = self.get_object()
        try:
            journal_entry = invoice.post(user=request.user)
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            'message': 'Invoice posted successfully.',
            'invoice_number': invoice.invoice_number,
            'journal_entry': journal_entry.entry_number
        })
