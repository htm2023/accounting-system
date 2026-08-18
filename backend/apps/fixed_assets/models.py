from decimal import Decimal
from django.db import models, transaction
from django.core.exceptions import ValidationError
from apps.common.models import TimeStampedModel

class FixedAsset(TimeStampedModel):
    class DepreciationMethod(models.TextChoices):
        STRAIGHT_LINE = 'Straight-line', 'Straight-line'
        DECLINING = 'Declining', 'Declining'

    class Status(models.TextChoices):
        ACTIVE = 'Active', 'Active'
        DISPOSED = 'Disposed', 'Disposed'

    name = models.CharField(max_length=255)
    asset_account = models.ForeignKey(
        'chart_of_accounts.Account',
        on_delete=models.PROTECT,
        related_name='fixed_assets_asset'
    )
    depreciation_account = models.ForeignKey(
        'chart_of_accounts.Account',
        on_delete=models.PROTECT,
        related_name='fixed_assets_depreciation',
        help_text='حساب مجمع الإهلاك (دائن، Contra-Asset)'
    )
    expense_account = models.ForeignKey(
        'chart_of_accounts.Account',
        on_delete=models.PROTECT,
        related_name='fixed_assets_expense',
        help_text='حساب مصروف الإهلاك (مدين)'
    )
    purchase_date = models.DateField()
    cost = models.DecimalField(max_digits=15, decimal_places=2)
    salvage_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    useful_life_years = models.PositiveIntegerField()
    depreciation_method = models.CharField(
        max_length=20,
        choices=DepreciationMethod.choices,
        default=DepreciationMethod.STRAIGHT_LINE
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)

    class Meta:
        verbose_name = 'Fixed Asset'
        verbose_name_plural = 'Fixed Assets'
        ordering = ['name']

    def __str__(self):
        return self.name

    def clean(self):
        if self.cost <= 0:
            raise ValidationError('Cost must be positive.')
        if self.salvage_value < 0 or self.salvage_value >= self.cost:
            raise ValidationError('Salvage value must be non-negative and less than cost.')
        if self.useful_life_years <= 0:
            raise ValidationError('Useful life years must be positive.')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def generate_depreciation_schedule(self):
        """توليد جدول إهلاك مبدئي (يمكن تعديله لاحقًا قبل الترحيل)"""
        if self.status != self.Status.ACTIVE:
            raise ValidationError('Cannot generate schedule for disposed asset.')
        # مسح الجداول السابقة غير المرحّلة
        self.depreciation_schedules.filter(is_posted=False).delete()
        years = self.useful_life_years
        # حساب الإهلاك السنوي (القسط الثابت)
        if self.depreciation_method == self.DepreciationMethod.STRAIGHT_LINE:
            annual_dep = ((self.cost - self.salvage_value) / years).quantize(Decimal('0.01'))
        else:  # Declining (نسبة مئوية ثابتة من القيمة الدفترية)
            # عامل تقريبي: 2 / useful_life
            rate = Decimal(2) / Decimal(years)
            book_value = self.cost
            accumulated = Decimal('0')
            for i in range(years):
                dep = (book_value * rate).quantize(Decimal('0.01'))
                if book_value - dep < self.salvage_value:
                    dep = (book_value - self.salvage_value).quantize(Decimal('0.01'))
                accumulated += dep
                from .models import DepreciationSchedule
                DepreciationSchedule.objects.create(
                    asset=self,
                    fiscal_period=None,
                    depreciation_amount=dep,
                    accumulated_depreciation=accumulated,
                )
                book_value -= dep
            return
        # إنشاء صفوف لكل سنة
        accumulated = 0
        from .models import DepreciationSchedule
        for i in range(1, years + 1):
            accumulated += annual_dep
            DepreciationSchedule.objects.create(
                asset=self,
                fiscal_period=None,  # سيُحدد لاحقًا
                depreciation_amount=annual_dep,
                accumulated_depreciation=accumulated,
            )

class DepreciationSchedule(TimeStampedModel):
    asset = models.ForeignKey(
        FixedAsset,
        on_delete=models.CASCADE,
        related_name='depreciation_schedules'
    )
    fiscal_period = models.ForeignKey(
        'fiscal.FiscalPeriod',
        on_delete=models.PROTECT,
        related_name='depreciation_schedules',
        null=True,
        blank=True,
        help_text='يُترك فارغًا عند التوليد المبدئي، ويجب تحديده قبل الترحيل'
    )
    depreciation_amount = models.DecimalField(max_digits=15, decimal_places=2)
    accumulated_depreciation = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    journal_entry = models.ForeignKey(
        'journal_entries.JournalEntry',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='depreciation_schedules'
    )
    is_posted = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Depreciation Schedule'
        verbose_name_plural = 'Depreciation Schedules'
        ordering = ['fiscal_period__start_date']

    def __str__(self):
        return f"{self.asset.name} - {self.fiscal_period.name if self.fiscal_period else 'No period'}"

    def clean(self):
        if self.fiscal_period and self.fiscal_period.is_closed and self.is_posted:
            raise ValidationError('Cannot post depreciation to closed fiscal period.')
        if self.depreciation_amount <= 0:
            raise ValidationError('Depreciation amount must be positive.')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def post(self, user=None):
        if self.is_posted:
            raise ValidationError('This depreciation is already posted.')
        if not self.fiscal_period or self.fiscal_period.is_closed:
            raise ValidationError('Fiscal period must be set and not closed.')
        # إنشاء القيد المحاسبي
        from apps.journal_entries.services import create_journal_entry
        lines = [
            {
                'account': self.asset.expense_account,   # مدين: مصروف الإهلاك
                'debit': self.depreciation_amount,
                'credit': 0,
                'description': f'Depreciation expense for {self.asset.name}'
            },
            {
                'account': self.asset.depreciation_account,  # دائن: مجمع الإهلاك
                'debit': 0,
                'credit': self.depreciation_amount,
                'description': f'Accumulated depreciation for {self.asset.name}'
            }
        ]
        with transaction.atomic():
            journal_entry = create_journal_entry(
                fiscal_period=self.fiscal_period,
                date=self.fiscal_period.end_date,
                description=f"Depreciation for {self.asset.name}",
                source_type='Asset',
                source_id=str(self.id),
                created_by=user,
                auto_post=True,
                approved_by=user,
                lines_data=lines
            )
            self.journal_entry = journal_entry
            self.is_posted = True
            self.save(update_fields=['journal_entry', 'is_posted', 'updated_at'])
        return journal_entry
