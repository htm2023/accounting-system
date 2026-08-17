from django.contrib import admin
from .models import ReceiptPayment, PaymentAllocation

class PaymentAllocationInline(admin.TabularInline):
    # للعرض فقط: allocate_to_invoice() هي المسار الوحيد لإنشاء تخصيص متزامن
    model = PaymentAllocation
    extra = 0

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(ReceiptPayment)
class ReceiptPaymentAdmin(admin.ModelAdmin):
    list_display = ['number', 'document_type', 'party', 'date', 'amount', 'journal_entry']
    list_filter = ['document_type', 'fiscal_period']
    search_fields = ['number', 'party__name_ar']
    inlines = [PaymentAllocationInline]
    readonly_fields = ['number', 'journal_entry']

    def has_change_permission(self, request, obj=None):
        if obj and obj.journal_entry:
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.journal_entry:
            return False
        return super().has_delete_permission(request, obj)

@admin.register(PaymentAllocation)
class PaymentAllocationAdmin(admin.ModelAdmin):
    # لا تعديل ولا حذف مباشر عمدًا: allocate_to_invoice() هي المسار الوحيد
    # الذي يُبقي invoice.paid_amount/status متزامنًا مع سجلات التخصيص
    list_display = ['receipt_payment', 'invoice', 'allocated_amount']
    search_fields = ['receipt_payment__number', 'invoice__invoice_number']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
