from django.contrib import admin
from .models import FiscalYear, FiscalPeriod

@admin.register(FiscalYear)
class FiscalYearAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_date', 'end_date', 'is_closed', 'retained_earnings_account']
    list_filter = ['is_closed']
    search_fields = ['name']
    ordering = ['-start_date']

    def has_change_permission(self, request, obj=None):
        if obj and obj.is_closed:
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.is_closed:
            return False
        return super().has_delete_permission(request, obj)

@admin.register(FiscalPeriod)
class FiscalPeriodAdmin(admin.ModelAdmin):
    list_display = ['name', 'fiscal_year', 'start_date', 'end_date', 'is_closed']
    list_filter = ['is_closed', 'fiscal_year']
    search_fields = ['name']
    ordering = ['-start_date']

    def has_change_permission(self, request, obj=None):
        if obj and obj.is_closed:
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.is_closed:
            return False
        return super().has_delete_permission(request, obj)
