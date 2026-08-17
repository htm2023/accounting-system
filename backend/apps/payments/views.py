from decimal import Decimal, InvalidOperation
from django.core.exceptions import ValidationError
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import ReceiptPayment, PaymentAllocation
from .serializers import ReceiptPaymentSerializer, PaymentAllocationSerializer
from apps.common.permissions import IsAccountant, IsAdmin

class ReceiptPaymentViewSet(viewsets.ModelViewSet):
    queryset = ReceiptPayment.objects.prefetch_related('payment_allocations')
    serializer_class = ReceiptPaymentSerializer

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
        if serializer.instance.journal_entry:
            from rest_framework.exceptions import ValidationError as DRFValidationError
            raise DRFValidationError('Posted documents cannot be modified.')
        serializer.save()

    def perform_destroy(self, instance):
        if instance.journal_entry:
            from rest_framework.exceptions import ValidationError as DRFValidationError
            raise DRFValidationError('Posted documents cannot be deleted.')
        instance.delete()

    @action(detail=True, methods=['post'])
    def post(self, request, pk=None):
        rp = self.get_object()
        try:
            journal_entry = rp.post(user=request.user)
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            'message': 'Document posted successfully.',
            'number': rp.number,
            'journal_entry': journal_entry.entry_number
        })

    @action(detail=True, methods=['post'])
    def allocate(self, request, pk=None):
        rp = self.get_object()
        invoice_id = request.data.get('invoice_id')
        try:
            amount = Decimal(str(request.data.get('amount')))
        except (InvalidOperation, TypeError):
            return Response({'error': 'Invalid amount.'}, status=status.HTTP_400_BAD_REQUEST)

        from apps.invoicing.models import Invoice
        try:
            invoice = Invoice.objects.get(id=invoice_id)
        except Invoice.DoesNotExist:
            return Response({'error': 'Invoice not found.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            rp.allocate_to_invoice(invoice, amount)
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'message': 'Allocation successful.'})

class PaymentAllocationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PaymentAllocation.objects.all()
    serializer_class = PaymentAllocationSerializer
    permission_classes = [IsAuthenticated]
