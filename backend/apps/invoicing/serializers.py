from decimal import Decimal
from django.db import transaction
from rest_framework import serializers
from .models import Invoice, InvoiceItem
from apps.currencies.services import get_exchange_rate

class InvoiceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceItem
        fields = ['id', 'product', 'quantity', 'unit_price', 'unit_cost', 'tax_rate', 'discount', 'total']
        read_only_fields = ['total']

    def validate(self, data):
        instance = InvoiceItem(**data)
        instance.clean()
        return data

class InvoiceSerializer(serializers.ModelSerializer):
    items = InvoiceItemSerializer(many=True, required=True)

    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_type', 'invoice_number', 'fiscal_period', 'date',
            'due_date', 'party', 'currency', 'exchange_rate_used', 'subtotal',
            'tax_amount', 'tax_account', 'discount', 'discount_account',
            'total_amount', 'paid_amount', 'status',
            'journal_entry', 'items', 'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'invoice_number', 'subtotal', 'total_amount', 'paid_amount',
            'status', 'journal_entry', 'created_by', 'created_at', 'updated_at'
        ]

    @staticmethod
    def _resolve_unit_cost(invoice_type, item_data, exchange_rate):
        # unit_cost قيمة محاسبية داخلية (تكلفة البضاعة بالعملة الأساسية)، وليست
        # مُدخلاً حرًا من المستخدم:
        # - عند البيع: تُشتق دائمًا من متوسط تكلفة المنتج الحالي (بالعملة الأساسية أصلًا).
        # - عند الشراء: تساوي سعر الشراء المدفوع (بعملة الفاتورة) مُحوَّلًا للعملة
        #   الأساسية بسعر الصرف، حتى يبقى تقييم المخزون ومتوسط التكلفة موحّدًا
        #   بعملة واحدة بصرف النظر عن عملة فاتورة الشراء.
        if invoice_type == Invoice.InvoiceType.SALE:
            return item_data['product'].average_cost
        if not item_data.get('unit_cost'):
            return Decimal(item_data['unit_price'] * exchange_rate).quantize(Decimal('0.0001'))
        return item_data['unit_cost']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        with transaction.atomic():
            invoice = Invoice.objects.create(**validated_data)
            for item_data in items_data:
                item_data['unit_cost'] = self._resolve_unit_cost(
                    invoice.invoice_type, item_data, invoice.exchange_rate_used
                )
                InvoiceItem.objects.create(invoice=invoice, **item_data)
            invoice.update_totals()
        return invoice

    def update(self, instance, validated_data):
        if instance.status != Invoice.Status.DRAFT:
            raise serializers.ValidationError('Only draft invoices can be modified.')
        items_data = validated_data.pop('items', None)
        with transaction.atomic():
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            if items_data is not None:
                instance.items.all().delete()
                for item_data in items_data:
                    item_data['unit_cost'] = self._resolve_unit_cost(
                        instance.invoice_type, item_data, instance.exchange_rate_used
                    )
                    InvoiceItem.objects.create(invoice=instance, **item_data)
            instance.update_totals()
        return instance

    def validate(self, data):
        fiscal_period = data.get('fiscal_period')
        date = data.get('date') or (self.instance.date if self.instance else None)
        if fiscal_period and data.get('date'):
            if fiscal_period.is_closed:
                raise serializers.ValidationError('Cannot create invoice in closed fiscal period.')
            if data['date'] < fiscal_period.start_date or data['date'] > fiscal_period.end_date:
                raise serializers.ValidationError('Invoice date must be within fiscal period.')
        items = data.get('items')
        if items is not None and not items:
            raise serializers.ValidationError('At least one item is required.')

        # تحديد سعر الصرف الفعلي: إن كانت العملة أساسية أو غير محددة فالسعر
        # دائمًا 1. غير ذلك، إن لم يُرسَل سعر صرف صراحة (أو أُرسل 1 الافتراضي)
        # يُشتق آخر سعر مسجَّل لهذه العملة بتاريخ الفاتورة أو قبله.
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
