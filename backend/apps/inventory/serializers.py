from rest_framework import serializers
from .models import Product, StockMovement

class ProductSerializer(serializers.ModelSerializer):
    current_stock = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'sku', 'name_ar', 'name_en', 'description', 'unit',
            'valuation_method', 'average_cost', 'selling_price', 'reorder_level',
            'inventory_account', 'cogs_account', 'revenue_account', 'current_stock',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['average_cost', 'created_at', 'updated_at']

    def validate(self, data):
        instance = self.instance or Product()
        for field, value in data.items():
            setattr(instance, field, value)
        instance.clean()
        return data

class StockMovementSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockMovement
        fields = [
            'id', 'product', 'movement_type', 'quantity', 'unit_cost',
            'reference_type', 'reference_id', 'date', 'created_by', 'created_at'
        ]
        read_only_fields = ['created_by', 'created_at']

    def validate(self, data):
        instance = self.instance or StockMovement()
        for field, value in data.items():
            setattr(instance, field, value)
        instance.clean()
        return data
