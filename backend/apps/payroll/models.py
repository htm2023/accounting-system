from django.db import models, transaction
from django.core.exceptions import ValidationError
from apps.common.models import TimeStampedModel

class Employee(TimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = 'Active', 'Active'
        TERMINATED = 'Terminated', 'Terminated'

    name = models.CharField(max_length=255)
    position = models.CharField(max_length=255, blank=True, null=True)
    basic_salary = models.DecimalField(max_digits=15, decimal_places=2)
    hire_date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    salary_account = models.ForeignKey(
        'chart_of_accounts.Account',
        on_delete=models.PROTECT,
        related_name='employees'
    )
    payment_account = models.ForeignKey(
        'chart_of_accounts.Account',
        on_delete=models.PROTECT,
        related_name='employees_payment',
        help_text='حساب البنك/الخزينة الذي يُصرف منه الراتب'
    )

    class Meta:
        verbose_name = 'Employee'
        verbose_name_plural = 'Employees'
        ordering = ['name']

    def __str__(self):
        return self.name

    def clean(self):
        if self.basic_salary < 0:
            raise ValidationError('Basic salary cannot be negative.')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

class Payslip(TimeStampedModel):
    employee = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name='payslips'
    )
    fiscal_period = models.ForeignKey(
        'fiscal.FiscalPeriod',
        on_delete=models.PROTECT,
        related_name='payslips'
    )
    basic_salary = models.DecimalField(max_digits=15, decimal_places=2)
    allowances = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    deductions = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    net_salary = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    journal_entry = models.ForeignKey(
        'journal_entries.JournalEntry',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payslips'
    )

    class Meta:
        verbose_name = 'Payslip'
        verbose_name_plural = 'Payslips'
        ordering = ['-fiscal_period__start_date']

    def __str__(self):
        return f"{self.employee.name} - {self.fiscal_period.name}"

    def clean(self):
        if self.fiscal_period and self.fiscal_period.is_closed:
            raise ValidationError('Cannot create payslip in a closed fiscal period.')
        if self.basic_salary < 0 or self.allowances < 0 or self.deductions < 0:
            raise ValidationError('Salary values cannot be negative.')

    def save(self, *args, **kwargs):
        self.net_salary = self.basic_salary + self.allowances - self.deductions
        self.full_clean()
        super().save(*args, **kwargs)

    def post(self, user=None):
        if self.journal_entry:
            raise ValidationError('Payslip is already posted.')
        # إنشاء القيد المحاسبي
        from apps.journal_entries.services import create_journal_entry
        lines = [
            {
                'account': self.employee.salary_account,
                'debit': self.net_salary,
                'credit': 0,
                'description': f'Salary for {self.employee.name}'
            },
            {
                'account': self.employee.payment_account,
                'debit': 0,
                'credit': self.net_salary,
                'description': f'Payment of salary for {self.employee.name}'
            }
        ]
        with transaction.atomic():
            journal_entry = create_journal_entry(
                fiscal_period=self.fiscal_period,
                date=self.fiscal_period.end_date,
                description=f"Payroll for {self.employee.name} - {self.fiscal_period.name}",
                source_type='Payroll',
                source_id=str(self.id),
                created_by=user,
                auto_post=True,
                approved_by=user,
                lines_data=lines
            )
            self.journal_entry = journal_entry
            self.save(update_fields=['journal_entry', 'updated_at'])
        return journal_entry
