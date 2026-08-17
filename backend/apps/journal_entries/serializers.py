from django.db import transaction
from rest_framework import serializers
from .models import JournalEntry, JournalEntryLine
from .services import create_journal_entry

class JournalEntryLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = JournalEntryLine
        fields = [
            'id', 'account', 'debit', 'credit', 'exchange_rate_used',
            'currency', 'description', 'cost_center'
        ]

    def validate(self, data):
        instance = JournalEntryLine(**data)
        instance.clean()
        return data

class JournalEntrySerializer(serializers.ModelSerializer):
    lines = JournalEntryLineSerializer(many=True, required=True)

    class Meta:
        model = JournalEntry
        fields = [
            'id', 'entry_number', 'fiscal_period', 'date', 'description',
            'reference', 'source_type', 'source_id', 'is_posted',
            'reversed_entry', 'lines', 'total_debit', 'total_credit',
            'created_by', 'approved_by', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'entry_number', 'source_type', 'source_id', 'is_posted',
            'reversed_entry', 'total_debit', 'total_credit',
            'created_by', 'approved_by', 'created_at', 'updated_at'
        ]

    def create(self, validated_data):
        lines_data = validated_data.pop('lines')
        return create_journal_entry(
            fiscal_period=validated_data['fiscal_period'],
            date=validated_data['date'],
            description=validated_data.get('description', ''),
            lines_data=lines_data,
            reference=validated_data.get('reference'),
            created_by=validated_data.get('created_by'),
        )

    def update(self, instance, validated_data):
        # منع تعديل القيد المرحّل
        if instance.is_posted:
            raise serializers.ValidationError('Posted journal entries cannot be modified.')
        lines_data = validated_data.pop('lines', None)
        with transaction.atomic():
            # تحديث الحقول الأساسية
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            if lines_data is not None:
                instance.lines.all().delete()
                for line_data in lines_data:
                    JournalEntryLine.objects.create(journal_entry=instance, **line_data)
        return instance

    def validate(self, data):
        # التأكد من أن الفترة غير مقفولة
        fiscal_period = data.get('fiscal_period')
        date = data.get('date')
        if fiscal_period and date:
            if fiscal_period.is_closed:
                raise serializers.ValidationError('Cannot create entry in a closed fiscal period.')
            if date < fiscal_period.start_date or date > fiscal_period.end_date:
                raise serializers.ValidationError('Entry date must be within fiscal period.')
        # التأكد من وجود سطور
        lines = data.get('lines')
        if lines is not None and not lines:
            raise serializers.ValidationError('At least one line is required.')
        return data
