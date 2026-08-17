from rest_framework import serializers
from .models import FixedAsset, DepreciationSchedule

class FixedAssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = FixedAsset
        fields = [
            'id', 'name', 'asset_account', 'depreciation_account', 'expense_account',
            'purchase_date', 'cost', 'salvage_value', 'useful_life_years',
            'depreciation_method', 'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class DepreciationScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = DepreciationSchedule
        fields = [
            'id', 'asset', 'fiscal_period', 'depreciation_amount',
            'accumulated_depreciation', 'journal_entry', 'is_posted',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['journal_entry', 'is_posted', 'created_at', 'updated_at']

    def validate(self, data):
        instance = DepreciationSchedule(**data)
        instance.clean()
        return data
