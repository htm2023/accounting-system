from django.contrib import admin
from .models import DocumentSequence

@admin.register(DocumentSequence)
class DocumentSequenceAdmin(admin.ModelAdmin):
    list_display = ['document_type', 'prefix', 'current_number', 'fiscal_year']
    list_filter = ['document_type', 'fiscal_year']
    search_fields = ['document_type', 'prefix']
