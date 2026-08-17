from rest_framework import serializers
from .models import FiscalYear, FiscalPeriod

class FiscalYearSerializer(serializers.ModelSerializer):
    class Meta:
        model = FiscalYear
        fields = '__all__'
        read_only_fields = ['is_closed', 'closed_by', 'closed_at']

class FiscalPeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = FiscalPeriod
        fields = '__all__'
        read_only_fields = ['is_closed']

    def validate(self, data):
        instance = FiscalPeriod(**data)
        instance.clean()
        return data
