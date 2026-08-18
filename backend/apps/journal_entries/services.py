from django.db import transaction
from django.db.models import Sum, Q
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import JournalEntry, JournalEntryLine
from apps.chart_of_accounts.models import Account
from apps.fiscal.models import FiscalPeriod

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

@transaction.atomic
def close_fiscal_period(period_id, user=None):
    """
    إقفال فترة محاسبية: ترحيل صافي الربح/الخسارة إلى حساب الأرباح المحتجزة.
    """
    period = FiscalPeriod.objects.select_for_update().get(id=period_id)
    if period.is_closed:
        raise ValidationError('الفترة مغلقة بالفعل')
    if period.fiscal_year.is_closed:
        raise ValidationError('السنة المالية مغلقة بالفعل')

    retained_account = period.fiscal_year.retained_earnings_account
    if not retained_account:
        raise ValidationError('لم يتم تعيين حساب الأرباح المحتجزة للسنة المالية')

    # التأكد من أن الحساب من نوع حقوق ملكية
    if retained_account.account_type != Account.AccountType.EQUITY:
        raise ValidationError('حساب الأرباح المحتجزة يجب أن يكون من نوع حقوق ملكية')

    # حساب أرصدة حسابات الإيرادات والمصروفات للفترة
    revenue_accounts = Account.objects.filter(
        account_type=Account.AccountType.REVENUE,
        is_active=True
    )
    expense_accounts = Account.objects.filter(
        account_type=Account.AccountType.EXPENSE,
        is_active=True
    )

    lines_data = []
    # إغلاق حسابات الإيرادات (رصيد دائن -> مدين)
    for account in revenue_accounts:
        balance = JournalEntryLine.objects.filter(
            journal_entry__fiscal_period=period,
            journal_entry__is_posted=True,
            account=account
        ).aggregate(
            total_debit=Sum('debit'),
            total_credit=Sum('credit')
        )
        total_debit = balance['total_debit'] or 0
        total_credit = balance['total_credit'] or 0
        net = total_credit - total_debit  # رصيد الإيراد (موجب إذا دائن)
        if net != 0:
            lines_data.append({
                'account': account,
                'debit': abs(net) if net > 0 else 0,
                'credit': 0 if net > 0 else abs(net),
                'description': f'إقفال حساب الإيراد {account.code}'
            })
            lines_data.append({
                'account': retained_account,
                'debit': 0 if net > 0 else abs(net),
                'credit': abs(net) if net > 0 else 0,
                'description': f'إقفال إلى الأرباح المحتجزة'
            })

    # إغلاق حسابات المصروفات (رصيد مدين -> دائن)
    for account in expense_accounts:
        balance = JournalEntryLine.objects.filter(
            journal_entry__fiscal_period=period,
            journal_entry__is_posted=True,
            account=account
        ).aggregate(
            total_debit=Sum('debit'),
            total_credit=Sum('credit')
        )
        total_debit = balance['total_debit'] or 0
        total_credit = balance['total_credit'] or 0
        net = total_debit - total_credit  # رصيد المصروف (موجب إذا مدين)
        if net != 0:
            lines_data.append({
                'account': retained_account,
                'debit': abs(net) if net > 0 else 0,
                'credit': 0 if net > 0 else abs(net),
                'description': f'إقفال المصروف {account.code}'
            })
            lines_data.append({
                'account': account,
                'debit': 0 if net > 0 else abs(net),
                'credit': abs(net) if net > 0 else 0,
                'description': f'إقفال إلى الأرباح المحتجزة'
            })

    if not lines_data:
        # لا توجد أرصدة للإقفال
        raise ValidationError('لا توجد أرصدة في حسابات الإيرادات والمصروفات لهذه الفترة')

    # إنشاء القيد المحاسبي
    entry = create_journal_entry(
        fiscal_period=period,
        date=period.end_date,
        description=f'إقفال فترة {period.name}',
        source_type='Closing',
        source_id=f'close-{period.id}',
        created_by=user,
        auto_post=True,
        approved_by=user,
        lines_data=lines_data
    )

    # تحديث حالة الفترة
    period.is_closed = True
    period.save(update_fields=['is_closed', 'updated_at'])

    # إذا كانت جميع فترات السنة مغلقة، أغلق السنة
    year = period.fiscal_year
    if not year.periods.filter(is_closed=False).exists():
        year.is_closed = True
        year.closed_by = user
        year.closed_at = timezone.now()
        year.save(update_fields=['is_closed', 'closed_by', 'closed_at', 'updated_at'])

    return entry
