from rest_framework import serializers
from .models import Currency, ExchangeRateHistory

class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = ['id', 'code', 'name', 'is_base_currency']

class ExchangeRateHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExchangeRateHistory
        fields = ['id', 'currency', 'rate', 'date']
