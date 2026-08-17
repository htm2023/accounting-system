from django.contrib import admin
from .models import Product, StockMovement

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['sku', 'name_ar', 'unit', 'valuation_method', 'average_cost', 'selling_price']
    search_fields = ['sku', 'name_ar', 'name_en']

@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ['product', 'movement_type', 'quantity', 'unit_cost', 'date']
    list_filter = ['movement_type', 'date']
    search_fields = ['product__sku', 'reference_type']

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
