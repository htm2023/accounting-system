from django.contrib import admin
from .models import Party

@admin.register(Party)
class PartyAdmin(admin.ModelAdmin):
    list_display = ['name_ar', 'party_type', 'email', 'phone', 'default_account']
    list_filter = ['party_type']
    search_fields = ['name_ar', 'name_en', 'email', 'tax_number']
