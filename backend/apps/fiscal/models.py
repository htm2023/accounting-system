from django.db import models
from django.core.exceptions import ValidationError
from apps.common.models import TimeStampedModel

class FiscalYear(TimeStampedModel):
    name = models.CharField(max_length=50, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    is_closed = models.BooleanField(default=False)
    closed_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='closed_fiscal_years'
    )
    closed_at = models.DateTimeField(null=True, blank=True)
    retained_earnings_account = models.ForeignKey(
        'chart_of_accounts.Account',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='retained_earnings_years'
    )

    def clean(self):
        if self.start_date >= self.end_date:
            raise ValidationError('End date must be after start date.')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class FiscalPeriod(TimeStampedModel):
    fiscal_year = models.ForeignKey(
        FiscalYear,
        on_delete=models.CASCADE,
        related_name='periods'
    )
    name = models.CharField(max_length=50)
    start_date = models.DateField()
    end_date = models.DateField()
    is_closed = models.BooleanField(default=False)

    class Meta:
        unique_together = ('fiscal_year', 'name')

    def clean(self):
        if self.start_date >= self.end_date:
            raise ValidationError('End date must be after start date.')
        if self.fiscal_year.start_date > self.start_date or self.fiscal_year.end_date < self.end_date:
            raise ValidationError('Period dates must be within fiscal year range.')
        overlapping = FiscalPeriod.objects.filter(
            fiscal_year=self.fiscal_year,
            start_date__lt=self.end_date,
            end_date__gt=self.start_date
        ).exclude(pk=self.pk)
        if overlapping.exists():
            raise ValidationError('Period dates overlap with existing periods.')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.fiscal_year.name})"
