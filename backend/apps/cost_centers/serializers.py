from rest_framework import serializers
from .models import CostCenter

class CostCenterSerializer(serializers.ModelSerializer):
    class Meta:
        model = CostCenter
        fields = ['id', 'code', 'name_ar', 'name_en', 'is_active']
