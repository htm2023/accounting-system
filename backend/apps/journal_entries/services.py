from django.db import transaction
from django.core.exceptions import ValidationError
from .models import JournalEntry, JournalEntryLine

@transaction.atomic
def create_journal_entry(
    *,
    fiscal_period,
    date,
    description,
    lines_data,
    source_type=JournalEntry.SourceType.MANUAL,
    source_id=None,
    reference=None,
    created_by=None,
    auto_post=False,
    approved_by=None
):
    """
    إنشاء قيد محاسبي جديد مع سطوره.
    lines_data: قائمة من dicts تحتوي على:
        account, debit, credit, exchange_rate_used, currency, description, cost_center
    """
    entry = JournalEntry(
        fiscal_period=fiscal_period,
        date=date,
        description=description,
        reference=reference,
        source_type=source_type,
        source_id=source_id,
        created_by=created_by,
        is_posted=False
    )
    entry.save()
    for line in lines_data:
        JournalEntryLine.objects.create(
            journal_entry=entry,
            account=line['account'],
            debit=line.get('debit', 0),
            credit=line.get('credit', 0),
            exchange_rate_used=line.get('exchange_rate_used', 1),
            currency=line.get('currency'),
            description=line.get('description', ''),
            cost_center=line.get('cost_center')
        )
    if auto_post:
        entry.post(user=approved_by)
    return entry
