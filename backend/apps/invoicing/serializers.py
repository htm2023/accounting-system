from django.db import transaction
from rest_framework import serializers
from .models import Invoice, InvoiceItem

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
            'tax_amount', 'discount', 'total_amount', 'paid_amount', 'status',
            'journal_entry', 'items', 'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'invoice_number', 'subtotal', 'total_amount', 'paid_amount',
            'status', 'journal_entry', 'created_by', 'created_at', 'updated_at'
        ]

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        with transaction.atomic():
            invoice = Invoice.objects.create(**validated_data)
            for item_data in items_data:
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
                    InvoiceItem.objects.create(invoice=instance, **item_data)
            instance.update_totals()
        return instance

    def validate(self, data):
        fiscal_period = data.get('fiscal_period')
        date = data.get('date')
        if fiscal_period and date:
            if fiscal_period.is_closed:
                raise serializers.ValidationError('Cannot create invoice in closed fiscal period.')
            if date < fiscal_period.start_date or date > fiscal_period.end_date:
                raise serializers.ValidationError('Invoice date must be within fiscal period.')
        items = data.get('items')
        if items is not None and not items:
            raise serializers.ValidationError('At least one item is required.')
        return data
