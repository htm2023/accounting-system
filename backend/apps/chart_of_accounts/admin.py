from django.contrib import admin
from .models import Account

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ['code', 'name_ar', 'name_en', 'account_type', 'parent', 'normal_balance', 'is_active', 'allow_posting']
    list_filter = ['account_type', 'is_active', 'allow_posting']
    search_fields = ['code', 'name_ar', 'name_en']
    ordering = ['code']
