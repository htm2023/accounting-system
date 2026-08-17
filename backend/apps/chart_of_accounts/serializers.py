from rest_framework import serializers
from .models import Account

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = [
            'id', 'code', 'name_ar', 'name_en', 'account_type',
            'parent', 'normal_balance', 'is_active', 'allow_posting',
            'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']

    def validate(self, data):
        instance = self.instance or Account()
        for field, value in data.items():
            setattr(instance, field, value)
        instance.clean()
        return data
