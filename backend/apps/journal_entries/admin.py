from django.contrib import admin
from .models import JournalEntry, JournalEntryLine

class JournalEntryLineInline(admin.TabularInline):
    model = JournalEntryLine
    extra = 1

@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ['entry_number', 'date', 'description', 'source_type', 'is_posted']
    list_filter = ['is_posted', 'source_type', 'fiscal_period']
    search_fields = ['entry_number', 'description', 'reference']
    inlines = [JournalEntryLineInline]
    readonly_fields = ['entry_number', 'is_posted']

    def has_change_permission(self, request, obj=None):
        if obj and obj.is_posted:
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.is_posted:
            return False
        return super().has_delete_permission(request, obj)
