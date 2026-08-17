from django.contrib import admin
from .models import FixedAsset, DepreciationSchedule

class DepreciationScheduleInline(admin.TabularInline):
    model = DepreciationSchedule
    extra = 0

@admin.register(FixedAsset)
class FixedAssetAdmin(admin.ModelAdmin):
    list_display = ['name', 'purchase_date', 'cost', 'salvage_value', 'depreciation_method', 'status']
    list_filter = ['status', 'depreciation_method']
    search_fields = ['name']
    inlines = [DepreciationScheduleInline]

@admin.register(DepreciationSchedule)
class DepreciationScheduleAdmin(admin.ModelAdmin):
    list_display = ['asset', 'fiscal_period', 'depreciation_amount', 'accumulated_depreciation', 'is_posted']
    list_filter = ['is_posted', 'fiscal_period']
    readonly_fields = ['journal_entry', 'is_posted']

    def has_change_permission(self, request, obj=None):
        if obj and obj.is_posted:
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.is_posted:
            return False
        return super().has_delete_permission(request, obj)
