from django.contrib import admin
from .models import Currency, ExchangeRateHistory

@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'is_base_currency']

@admin.register(ExchangeRateHistory)
class ExchangeRateHistoryAdmin(admin.ModelAdmin):
    list_display = ['currency', 'rate', 'date']
    list_filter = ['currency', 'date']
