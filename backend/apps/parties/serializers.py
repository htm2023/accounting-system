from rest_framework import serializers
from .models import Party

class PartySerializer(serializers.ModelSerializer):
    class Meta:
        model = Party
        fields = [
            'id', 'party_type', 'name_ar', 'name_en', 'email', 'phone',
            'address', 'tax_number', 'credit_limit', 'opening_balance',
            'opening_balance_date', 'default_account', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
