from django.contrib import admin
from .models import Employee, Payslip

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['name', 'position', 'basic_salary', 'status', 'salary_account']
    list_filter = ['status']
    search_fields = ['name', 'position']

@admin.register(Payslip)
class PayslipAdmin(admin.ModelAdmin):
    list_display = ['employee', 'fiscal_period', 'basic_salary', 'net_salary', 'journal_entry']
    list_filter = ['fiscal_period']
    search_fields = ['employee__name']
    readonly_fields = ['net_salary', 'journal_entry']

    def has_change_permission(self, request, obj=None):
        if obj and obj.journal_entry:
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.journal_entry:
            return False
        return super().has_delete_permission(request, obj)
