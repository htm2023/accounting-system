from rest_framework import serializers
from .models import ReceiptPayment, PaymentAllocation

class PaymentAllocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentAllocation
        fields = ['id', 'receipt_payment', 'invoice', 'allocated_amount']

class ReceiptPaymentSerializer(serializers.ModelSerializer):
    payment_allocations = PaymentAllocationSerializer(many=True, read_only=True)
    total_allocated = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    unallocated_amount = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)

    class Meta:
        model = ReceiptPayment
        fields = [
            'id', 'document_type', 'number', 'fiscal_period', 'date', 'party',
            'amount', 'account', 'description', 'journal_entry',
            'payment_allocations', 'total_allocated', 'unallocated_amount',
            'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'number', 'journal_entry', 'total_allocated',
            'unallocated_amount', 'created_by', 'created_at', 'updated_at'
        ]

    def validate(self, data):
        fiscal_period = data.get('fiscal_period')
        date = data.get('date')
        if fiscal_period and date:
            if fiscal_period.is_closed:
                raise serializers.ValidationError('Cannot create in closed fiscal period.')
            if date < fiscal_period.start_date or date > fiscal_period.end_date:
                raise serializers.ValidationError('Document date must be within fiscal period.')
        return data
