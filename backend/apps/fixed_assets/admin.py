from django import forms
from django.contrib import admin
from .models import FixedAsset, DepreciationSchedule

class DepreciationScheduleInlineForm(forms.ModelForm):
    class Meta:
        model = DepreciationSchedule
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # صف مُرحَّل بالفعل: كل حقوله للقراءة فقط، بغض النظر عن حالة الأصل الأب
        if self.instance and self.instance.pk and self.instance.is_posted:
            for field in self.fields.values():
                field.disabled = True

class DepreciationScheduleInlineFormSet(forms.BaseInlineFormSet):
    def add_fields(self, form, index):
        super().add_fields(form, index)
        # منع حذف صف مُرحَّل عبر خانة الحذف الجماعية في الـ inline
        if form.instance and form.instance.pk and form.instance.is_posted and 'DELETE' in form.fields:
            form.fields['DELETE'].disabled = True

class DepreciationScheduleInline(admin.TabularInline):
    model = DepreciationSchedule
    form = DepreciationScheduleInlineForm
    formset = DepreciationScheduleInlineFormSet
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
