from django.db import models
from django.db.models import Sum
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.common.models import TimeStampedModel

class JournalEntry(TimeStampedModel):
    class SourceType(models.TextChoices):
        MANUAL = 'Manual', 'Manual'
        INVOICE = 'Invoice', 'Invoice'
        PAYMENT = 'Payment', 'Payment'
        PAYROLL = 'Payroll', 'Payroll'
        ASSET = 'Asset', 'Asset'
        REVERSAL = 'Reversal', 'Reversal'

    entry_number = models.CharField(max_length=50, unique=True, editable=False)
    fiscal_period = models.ForeignKey(
        'fiscal.FiscalPeriod',
        on_delete=models.PROTECT,
        related_name='journal_entries'
    )
    date = models.DateField()
    description = models.TextField(blank=True, default='')
    reference = models.CharField(max_length=100, blank=True, null=True)
    source_type = models.CharField(
        max_length=20,
        choices=SourceType.choices,
        default=SourceType.MANUAL
    )
    source_id = models.CharField(max_length=50, null=True, blank=True)
    is_posted = models.BooleanField(default=False)
    reversed_entry = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reversal_of'
    )
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='journal_entries_created'
    )
    approved_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='journal_entries_approved'
    )

    class Meta:
        verbose_name = 'Journal Entry'
        verbose_name_plural = 'Journal Entries'
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.entry_number} - {self.date}"

    def clean(self):
        # التحقق من أن الفترة المحاسبية غير مقفولة إذا كان القيد مرحّلًا
        if self.is_posted and self.fiscal_period and self.fiscal_period.is_closed:
            raise ValidationError('Cannot post to a closed fiscal period.')
        # التأكد من أن تاريخ القيد يقع ضمن الفترة
        if self.fiscal_period:
            if self.date < self.fiscal_period.start_date or self.date > self.fiscal_period.end_date:
                raise ValidationError('Entry date must be within the fiscal period.')

    def save(self, *args, **kwargs):
        # توليد رقم القيد تلقائيًا إذا لم يُحدد
        if not self.entry_number:
            from apps.sequences.services import get_next_number
            from apps.sequences.models import DocumentSequence
            self.entry_number = get_next_number(
                DocumentSequence.DocumentType.JOURNAL_ENTRY,
                fiscal_year=self.fiscal_period.fiscal_year if self.fiscal_period else None
            )
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def total_debit(self):
        return self.lines.aggregate(total=Sum('debit'))['total'] or 0

    @property
    def total_credit(self):
        return self.lines.aggregate(total=Sum('credit'))['total'] or 0

    def post(self, user=None):
        if self.is_posted:
            raise ValidationError('Entry is already posted.')
        if not self.lines.exists():
            raise ValidationError('Cannot post an entry with no lines.')
        if self.total_debit != self.total_credit:
            raise ValidationError('Debit and credit totals must match before posting.')
        if self.fiscal_period.is_closed:
            raise ValidationError('Cannot post to a closed fiscal period.')
        self.is_posted = True
        self.approved_by = user
        self.save()

    def create_reversal(self, user=None, date=None):
        if not self.is_posted:
            raise ValidationError('Only posted entries can be reversed.')
        if self.reversed_entry:
            raise ValidationError('This entry is already a reversal or has been reversed.')
        reversal_date = date or timezone.now().date()
        reversal = JournalEntry.objects.create(
            fiscal_period=self.fiscal_period,
            date=reversal_date,
            description=f"Reversal of {self.entry_number}",
            source_type=JournalEntry.SourceType.REVERSAL,
            source_id=self.id,
            reversed_entry=self,
            created_by=user
        )
        for line in self.lines.all():
            JournalEntryLine.objects.create(
                journal_entry=reversal,
                account=line.account,
                debit=line.credit,
                credit=line.debit,
                exchange_rate_used=line.exchange_rate_used,
                currency=line.currency,
                description=f"Reversal of {line.description or ''}",
                cost_center=line.cost_center
            )
        return reversal

class JournalEntryLine(models.Model):
    journal_entry = models.ForeignKey(
        JournalEntry,
        on_delete=models.CASCADE,
        related_name='lines'
    )
    account = models.ForeignKey(
        'chart_of_accounts.Account',
        on_delete=models.PROTECT,
        related_name='journal_entry_lines'
    )
    debit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    exchange_rate_used = models.DecimalField(max_digits=15, decimal_places=6, default=1)
    currency = models.ForeignKey(
        'currencies.Currency',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='journal_entry_lines'
    )
    description = models.CharField(max_length=255, blank=True, null=True)
    cost_center = models.ForeignKey(
        'cost_centers.CostCenter',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='journal_entry_lines'
    )

    class Meta:
        verbose_name = 'Journal Entry Line'
        verbose_name_plural = 'Journal Entry Lines'

    def __str__(self):
        return f"{self.account.code} - Debit: {self.debit}, Credit: {self.credit}"

    def clean(self):
        if self.debit and self.credit:
            raise ValidationError('A line cannot have both debit and credit values.')
        if not self.debit and not self.credit:
            raise ValidationError('Either debit or credit must be specified.')
        if self.account and not self.account.allow_posting:
            raise ValidationError(f'Account {self.account.code} does not allow posting (parent account).')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
