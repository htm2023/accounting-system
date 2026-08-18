from rest_framework import serializers
from .models import FiscalYear, FiscalPeriod
from apps.chart_of_accounts.models import Account

class FiscalYearSerializer(serializers.ModelSerializer):
    retained_earnings_account = serializers.PrimaryKeyRelatedField(
        queryset=Account.objects.filter(account_type=Account.AccountType.EQUITY),
        required=False,
        allow_null=True
    )

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
