from django.db import models
from apps.common.models import TimeStampedModel

class Currency(TimeStampedModel):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    is_base_currency = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Currency'
        verbose_name_plural = 'Currencies'

    def __str__(self):
        return f"{self.code} - {self.name}"

    def clean(self):
        if self.is_base_currency:
            # التأكد من عدم وجود عملة أساسية أخرى
            qs = Currency.objects.filter(is_base_currency=True).exclude(pk=self.pk)
            if qs.exists():
                from django.core.exceptions import ValidationError
                raise ValidationError('There is already a base currency.')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

class ExchangeRateHistory(TimeStampedModel):
    currency = models.ForeignKey(
        Currency,
        on_delete=models.CASCADE,
        related_name='exchange_rates'
    )
    rate = models.DecimalField(max_digits=15, decimal_places=6)
    date = models.DateField()

    class Meta:
        verbose_name = 'Exchange Rate History'
        verbose_name_plural = 'Exchange Rate Histories'
        unique_together = ('currency', 'date')

    def __str__(self):
        return f"{self.currency.code} - {self.rate} ({self.date})"
