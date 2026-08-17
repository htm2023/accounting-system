from django.contrib import admin
from .models import CostCenter

@admin.register(CostCenter)
class CostCenterAdmin(admin.ModelAdmin):
    list_display = ['code', 'name_ar', 'name_en', 'is_active']
    search_fields = ['code', 'name_ar', 'name_en']
