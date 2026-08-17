from django.db import models
from django.core.exceptions import ValidationError
from apps.common.models import TimeStampedModel

class Account(TimeStampedModel):
    class AccountType(models.TextChoices):
        ASSET = 'Asset', 'Asset'
        LIABILITY = 'Liability', 'Liability'
        EQUITY = 'Equity', 'Equity'
        REVENUE = 'Revenue', 'Revenue'
        EXPENSE = 'Expense', 'Expense'

    class NormalBalance(models.TextChoices):
        DEBIT = 'Debit', 'Debit'
        CREDIT = 'Credit', 'Credit'

    code = models.CharField(max_length=20, unique=True, db_index=True)
    name_ar = models.CharField(max_length=255)
    name_en = models.CharField(max_length=255, blank=True, null=True)
    account_type = models.CharField(max_length=20, choices=AccountType.choices)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )
    normal_balance = models.CharField(
        max_length=10,
        choices=NormalBalance.choices,
        default=NormalBalance.DEBIT
    )
    is_active = models.BooleanField(default=True)
    allow_posting = models.BooleanField(default=True)
    is_cash_account = models.BooleanField(
        default=False,
        help_text='حساب نقدي/بنكي يُستخدم في قائمة التدفقات النقدية'
    )
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_accounts'
    )

    class Meta:
        verbose_name = 'Account'
        verbose_name_plural = 'Accounts'
        ordering = ['code']

    def clean(self):
        # منع الترحيل على الحسابات الرئيسية (التي لديها أبناء)
        if self.pk and self.children.exists():
            self.allow_posting = False
        # لا يمكن أن يكون الحساب والدًا لنفسه
        if self.pk and self.parent_id == self.pk:
            raise ValidationError('Account cannot be its own parent.')
        # نوع الحساب الفرعي يجب أن يطابق نوع الأب
        if self.parent and self.account_type != self.parent.account_type:
            raise ValidationError('Child account type must match parent account type.')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} - {self.name_ar or self.name_en}"
