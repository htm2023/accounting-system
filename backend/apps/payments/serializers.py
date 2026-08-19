from decimal import Decimal
from rest_framework import serializers
from .models import ReceiptPayment, PaymentAllocation
from apps.currencies.services import get_exchange_rate

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
            'amount', 'account', 'currency', 'exchange_rate_used', 'description', 'journal_entry',
            'payment_allocations', 'total_allocated', 'unallocated_amount',
            'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'number', 'journal_entry', 'total_allocated',
            'unallocated_amount', 'created_by', 'created_at', 'updated_at'
        ]

    def validate(self, data):
        fiscal_period = data.get('fiscal_period')
        date = data.get('date') or (self.instance.date if self.instance else None)
        if fiscal_period and data.get('date'):
            if fiscal_period.is_closed:
                raise serializers.ValidationError('Cannot create in closed fiscal period.')
            if data['date'] < fiscal_period.start_date or data['date'] > fiscal_period.end_date:
                raise serializers.ValidationError('Document date must be within fiscal period.')

        # تحديد سعر الصرف الفعلي، بنفس منطق InvoiceSerializer تمامًا.
        currency = data.get('currency')
        if currency is not None and not currency.is_base_currency:
            provided_rate = data.get('exchange_rate_used')
            if not provided_rate or provided_rate == Decimal('1'):
                rate = get_exchange_rate(currency, date)
                if rate is None:
                    raise serializers.ValidationError(
                        f'لا يوجد سعر صرف مسجَّل للعملة {currency.code} بتاريخ {date} أو قبله. '
                        'أضف سعر صرف أولاً من شاشة العملات.'
                    )
                data['exchange_rate_used'] = rate
        else:
            data['exchange_rate_used'] = Decimal('1')
        return data
