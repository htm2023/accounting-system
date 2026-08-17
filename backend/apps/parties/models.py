from django.db import models
from apps.common.models import TimeStampedModel

class Party(TimeStampedModel):
    class PartyType(models.TextChoices):
        CUSTOMER = 'Customer', 'Customer'
        SUPPLIER = 'Supplier', 'Supplier'
        BOTH = 'Both', 'Both'

    party_type = models.CharField(max_length=20, choices=PartyType.choices)
    name_ar = models.CharField(max_length=255)
    name_en = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    tax_number = models.CharField(max_length=50, blank=True, null=True)
    credit_limit = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    opening_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    opening_balance_date = models.DateField(null=True, blank=True)
    default_account = models.ForeignKey(
        'chart_of_accounts.Account',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='parties'
    )

    class Meta:
        verbose_name = 'Party'
        verbose_name_plural = 'Parties'
        ordering = ['name_ar']

    def __str__(self):
        return f"{self.name_ar} ({self.party_type})"
