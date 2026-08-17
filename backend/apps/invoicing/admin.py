from django.contrib import admin
from .models import Invoice, InvoiceItem

class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'invoice_type', 'party', 'date', 'total_amount', 'status']
    list_filter = ['invoice_type', 'status', 'fiscal_period']
    search_fields = ['invoice_number', 'party__name_ar']
    inlines = [InvoiceItemInline]
    readonly_fields = ['invoice_number', 'subtotal', 'total_amount', 'paid_amount', 'status', 'journal_entry']

    def has_change_permission(self, request, obj=None):
        if obj and obj.status != Invoice.Status.DRAFT:
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.status != Invoice.Status.DRAFT:
            return False
        return super().has_delete_permission(request, obj)
